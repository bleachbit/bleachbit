# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Store and retrieve user preferences
"""


import os
import re
import traceback
import ConfigParser

import Common
import General

if 'nt' == os.name:
    from win32file import GetLongPathName


boolean_keys = ['auto_start', 'check_beta',
                'check_online_updates', 'first_start', 'shred']
if 'nt' == os.name:
    boolean_keys.append('update_winapp2')


def path_to_option(pathname):
    """Change a pathname to a .ini option name (a key)"""
    # On Windows change to lowercase and use backwards slashes.
    pathname = os.path.normcase(pathname)
    # On Windows expand DOS-8.3-style pathnames.
    if 'nt' == os.name and os.path.exists(pathname):
        pathname = GetLongPathName(pathname)
    if ':' == pathname[1]:
        # ConfigParser treats colons in a special way
        pathname = pathname[0] + pathname[2:]
    return pathname


class Options:

    """Store and retrieve user preferences"""

    def __init__(self):
        self.purged = False
        self.config = ConfigParser.SafeConfigParser()
        self.config.optionxform = str  # make keys case sensitive for hashpath purging
        self.restore()

    def __flush(self):
        """Write information to disk"""
        if not self.purged:
            self.__purge()
        if not os.path.exists(Common.options_dir):
            General.makedirs(Common.options_dir)
        mkfile = not os.path.exists(Common.options_file)
        _file = open(Common.options_file, 'wb')
        try:
            self.config.write(_file)
        except IOError, e:
            print e
            from errno import ENOSPC
            if e.errno == ENOSPC:
                print "Error: disk is full writing configuration '%s'" % Common.options_file
            else:
                raise
        if mkfile and General.sudo_mode():
            General.chownself(Common.options_file)

    def __purge(self):
        """Clear out obsolete data"""
        self.purged = True
        if not self.config.has_section('hashpath'):
            return
        for option in self.config.options('hashpath'):
            pathname = option
            if 'nt' == os.name and re.search('^[a-z]\\\\', option):
                # restore colon lost because ConfigParser treats colon special
                # in keys
                pathname = pathname[0] + ':' + pathname[1:]
            if not os.path.lexists(pathname):
                # the file does not on exist, so forget it
                self.config.remove_option('hashpath', option)

    def __set_default(self, key, value):
        """Set the default value"""
        if not self.config.has_option('bleachbit', key):
            self.set(key, value)

    def get(self, option, section='bleachbit'):
        """Retrieve a general option"""
        if not 'nt' == os.name and 'update_winapp2' == option:
            return False
        if section == 'hashpath' and option[1] == ':':
            option = option[0] + option[2:]
        if option in boolean_keys:
            return self.config.getboolean(section, option)
        return self.config.get(section, option)

    def get_hashpath(self, pathname):
        """Recall the hash for a file"""
        return self.get(path_to_option(pathname), 'hashpath')

    def get_language(self, langid):
        """Retrieve value for whether to preserve the language"""
        if not self.config.has_option('preserve_languages', langid):
            return False
        return self.config.getboolean('preserve_languages', langid)

    def get_languages(self):
        """Return a list of all selected languages"""
        if not self.config.has_section('preserve_languages'):
            return None
        return self.config.options('preserve_languages')

    def get_list(self, option):
        """Return an option which is a list data type"""
        section = "list/%s" % option
        if not self.config.has_section(section):
            return None
        values = []
        for option in sorted(self.config.options(section)):
            values.append(self.config.get(section, option))
        return values

    def get_paths(self, section):
        """Abstracts get_whitelist_paths and get_custom_paths"""
        if not self.config.has_section(section):
            return []
        myoptions = []
        for option in sorted(self.config.options(section)):
            pos = option.find('_')
            if -1 == pos:
                continue
            myoptions.append(option[0:pos])
        values = []
        for option in set(myoptions):
            p_type = self.config.get(section, option + '_type')
            p_path = self.config.get(section, option + '_path')
            values.append((p_type, p_path))
        return values

    def get_whitelist_paths(self):
        """Return the whitelist of paths"""
        return self.get_paths("whitelist/paths")

    def get_custom_paths(self):
        """Return list of custom paths"""
        return self.get_paths("custom/paths")

    def get_tree(self, parent, child):
        """Retrieve an option for the tree view.  The child may be None."""
        option = parent
        if None != child:
            option += "." + child
        if not self.config.has_option('tree', option):
            return False
        try:
            return self.config.getboolean('tree', option)
        except:
            # in case of corrupt configuration (Launchpad #799130)
            traceback.print_exc()
            return False

    def restore(self):
        """Restore saved options from disk"""
        try:
            self.config.read(Common.options_file)
        except:
            traceback.print_exc()
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
        if not self.config.has_section("hashpath"):
            self.config.add_section("hashpath")
        if not self.config.has_section("list/shred_drives"):
            from FileUtilities import guess_overwrite_paths
            self.set_list('shred_drives', guess_overwrite_paths())

        # set defaults
        self.__set_default("auto_start", False)
        self.__set_default("check_beta", False)
        self.__set_default("check_online_updates", True)
        self.__set_default("shred", False)
        if 'nt' == os.name:
            self.__set_default("update_winapp2", False)

        if not self.config.has_section('preserve_languages'):
            lang = Common.user_locale
            pos = lang.find('_')
            if -1 != pos:
                lang = lang[0: pos]
            for _lang in set([lang, 'en']):
                print "info: automatically preserving language '%s'" % lang
                self.set_language(_lang, True)

        # BleachBit upgrade or first start ever
        if not self.config.has_option('bleachbit', 'version') or \
                self.get('version') != Common.APP_VERSION:
            self.set('first_start', True)

        # set version
        self.set("version", Common.APP_VERSION)

    def set(self, key, value, section='bleachbit', commit=True):
        """Set a general option"""
        self.config.set(section, key, str(value))
        if commit:
            self.__flush()

    def set_hashpath(self, pathname, hashvalue):
        """Remember the hash of a path"""
        self.set(path_to_option(pathname), hashvalue, 'hashpath')

    def set_list(self, key, values):
        """Set a value which is a list data type"""
        section = "list/%s" % key
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter), value)
            counter += 1
        self.__flush()

    def set_whitelist_paths(self, values):
        """Save the whitelist"""
        section = "whitelist/paths"
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter) + '_type', value[0])
            self.config.set(section, str(counter) + '_path', value[1])
            counter += 1
        self.__flush()

    def set_custom_paths(self, values):
        """Save the customlist"""
        section = "custom/paths"
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter) + '_type', value[0])
            self.config.set(section, str(counter) + '_path', value[1])
            counter += 1
        self.__flush()

    def set_language(self, langid, value):
        """Set the value for a locale (whether to preserve it)"""
        if not self.config.has_section('preserve_languages'):
            self.config.add_section('preserve_languages')
        if self.config.has_option('preserve_languages', langid) and not value:
            self.config.remove_option('preserve_languages', langid)
        else:
            self.config.set('preserve_languages', langid, str(value))
        self.__flush()

    def set_tree(self, parent, child, value):
        """Set an option for the tree view.  The child may be None."""
        if not self.config.has_section("tree"):
            self.config.add_section("tree")
        option = parent
        if None != child:
            option = option + "." + child
        if self.config.has_option('tree', option) and not value:
            self.config.remove_option('tree', option)
        else:
            self.config.set('tree', option, str(value))
        self.__flush()

    def toggle(self, key):
        """Toggle a boolean key"""
        self.set(key, not self.get(key))


options = Options()
