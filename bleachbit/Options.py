# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Store and retreieve user preferences
"""


import os
import traceback
import ConfigParser

import Common
import General


boolean_keys = ('auto_hide', 'auto_start', 'check_online_updates', 'first_start', 'shred')



class Options:
    """Store and retrieve user preferences"""


    def __init__(self):
        self.restore()


    def __flush(self):
        """Write information to disk"""
        if not os.path.exists(Common.options_dir):
            General.makedirs(Common.options_dir)
        mkfile = not os.path.exists(Common.options_file)
        _file = open(Common.options_file, 'wb')
        try:
            self.config.write(_file)
        except IOError, e:
            print e
            if 28 == e.errno:
                print "Error: disk is full writing configuration '%s'" % Common.options_file
            else:
                raise
        if mkfile and General.sudo_mode():
            General.chownself(Common.options_file)


    def __set_default(self, key, value):
        """Set the default value"""
        if not self.config.has_option('bleachbit', key):
            self.set(key, value)


    def get(self, option, section = 'bleachbit'):
        """Retrieve a general option"""
        if section == 'hashpath' and option[1] == ':':
            option = option[0] + option[2:]
        if option in boolean_keys:
            return self.config.getboolean(section, option)
        return self.config.get(section, option)


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

    def get_whitelist_paths(self):
        """Return the whitelist of paths"""
        section = "whitelist/paths"
        if not self.config.has_section(section):
            return []
        options = []
        for option in sorted(self.config.options(section)):
            pos = option.find('_')
            if -1 == pos:
                continue
            options.append(option[0:pos])
        values = []
        for option in set(options):
            type = self.config.get(section, option + '_type')
            path = self.config.get(section, option + '_path')
            values.append( ( type, path ) )
        return values


    def get_tree(self, parent, child):
        """Retrieve an option for the tree view.  The child may be None."""
        option = parent
        if None != child:
            option += "." + child
        if not self.config.has_option('tree', option):
            return False
        return self.config.getboolean('tree', option)


    def restore(self):
        """Restore saved options from disk"""
        self.config = ConfigParser.SafeConfigParser()
        try:
            self.config.read(Common.options_file)
        except:
            traceback.print_exc()
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
        if not self.config.has_section("hashpath"):
            self.config.add_section("hashpath")
        if not self.config.has_section("list/shred_drives"):
            if 'nt' == os.name:
                import Windows
                self.set_list('shred_drives', Windows.get_fixed_drives())
            if 'posix' == os.name:
                import Unix
                self.set_list('shred_drives', Unix.guess_overwrite_paths())

        # set defaults
        self.__set_default("auto_hide", True)
        self.__set_default("auto_start", False)
        self.__set_default("check_online_updates", True)
        self.__set_default("shred", False)

        if not self.config.has_section('preserve_languages'):
            lang = Common.user_locale
            pos = lang.find('_')
            if -1 != pos:
                lang = lang [0 : pos]
            for _lang in set([lang, 'en']):
                print "info: automatically preserving language '%s'" % lang
                self.set_language(_lang, True)

        # BleachBit upgrade or first start ever
        if not self.config.has_option('bleachbit', 'version') or \
            self.get('version') != Common.APP_VERSION:
            self.set('first_start', True)

        # set version
        self.set("version", Common.APP_VERSION)


    def set(self, key, value, section = 'bleachbit', commit = True):
        """Set a general option"""
        if section == 'hashpath' and key[1] == ':':
            key = key[0] + key[2:]
        self.config.set(section, key, str(value))
        if commit:
            self.__flush()


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
        """Save thee whitelist"""
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


