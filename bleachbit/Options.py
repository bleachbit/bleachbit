# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
import sys
from globals import APP_VERSION, options_dir, options_file


boolean_keys = ('auto_hide', 'check_online_updates', 'first_start', 'shred')



class Options:
    """Store and retrieve user preferences"""
    def __init__(self):
        # restore options from disk
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(options_file)
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
        if not self.config.has_section("hashpath"):
            self.config.add_section("hashpath")

        # set defaults
        self.__set_default("auto_hide", True)
        self.__set_default("check_online_updates", True)
        self.__set_default("shred", False)

        if not self.config.has_section('preserve_languages'):
            import locale
            lang = locale.getdefaultlocale()[0]
            if None == lang:
                lang = 'en'
                print "warning: No default language found.  Assuming '%s'" % lang
            else:
                pos = lang.find('_')
                if -1 != pos:
                    lang = lang [0 : pos]
            print "info: automatically preserving language '%s'" % lang
            self.set_language(lang, True)

        # BleachBit upgrade or first start ever
        if not self.config.has_option('bleachbit', 'version') or \
            self.get('version') != APP_VERSION:
            self.set('first_start', True)

        # set version
        self.set("version", APP_VERSION)


    def __flush(self):
        """Write information to disk"""
        mkdir = False
        if not os.path.exists(options_dir):
            os.makedirs(options_dir, 0700)
            mkdir = True
        mkfile = not os.path.exists(options_file)
        _file = open(options_file, 'wb')
        self.config.write(_file)
        # If using sudo, avoid creating a directory that the
        # original account cannot read.
        if sys.platform == 'linux2' and sudo_mode():
            import pwd
            try:
                uid = pwd.getpwnam(os.getlogin())[3]
                if mkfile:
                   os.chown(options_file, uid, -1)
                if mkdir:
                   os.chown(options_dir, uid, -1)
            except:
                print 'Failed fixing permissions created by sudo'
                traceback.print_exc()


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


    def get_tree(self, parent, child):
        """Retrieve an option for the tree view.  The child may be None."""
        option = parent
        if None != child:
            option += "." + child
        if not self.config.has_option('tree', option):
            return False
        return self.config.getboolean('tree', option)


    def set(self, key, value, section = 'bleachbit'):
        """Set a general option"""
        if section == 'hashpath' and key[1] == ':':
            key = key[0] + key[2:]
        self.config.set(section, key, str(value))
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


def sudo_mode():
    """Return whether running in sudo mode"""
    try:
        login1 = os.getlogin()
    except:
        login1 = os.getenv('LOGNAME')

    try:
        import pwd
        login2 = pwd.getpwuid(os.getuid())[0]
        return login1 != login2
    except:
        import traceback
        traceback.print_exc()
        return False




options = Options()

import unittest

class TestOptions(unittest.TestCase):
    """Unit tests for class Options"""

    def test_Options(self):
        """Unit test for class Options"""
        o = options
        value = o.get("check_online_updates")

        # toggle a boolean
        o.toggle('check_online_updates')
        self.assertEqual(not value, o.get("check_online_updates"))

        # restore original boolean
        o.set("check_online_updates", value)
        self.assertEqual(value, o.get("check_online_updates"))

        # these should always be set
        for bkey in boolean_keys:
            self.assert_(type(o.get(bkey)) is bool)

        # ConfigParser naturally treats colons as delimiters
        value = 'abc'
        key = 'c:\\test\\foo.xml'
        o.set(key, value, 'hashpath')
        self.assertEqual(value, o.get(key, 'hashpath'))
        
        # language
        value = o.get_language('en')
        self.assert_(type(value) is bool)
        o.set_language('en', True)
        self.assertEqual(o.get_language('en'), True)
        o.set_language('en', False)
        self.assertEqual(o.get_language('en'), False)
        o.set_language('en', value)

        # tree
        o.set_tree("parent", "child", True)
        self.assertEqual(o.get_tree("parent", "child"), True)
        o.set_tree("parent", "child", False)
        self.assertEqual(o.get_tree("parent", "child"), False)
        o.config.remove_option("tree", "parent.child")
        self.assertEqual(o.get_tree("parent", "child"), False)


    def test_sudo_mode(self):
        """Unit test for sudo_mode()"""
        if not sys.platform == 'linux2':
            return
        self.assert_(type(sudo_mode()) is bool)


if __name__ == '__main__':
    unittest.main()

