# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2008 Andrew Ziem
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

import os
import ConfigParser

from globals import *

boolean_keys = ['check_online_updates', 'first_start']

class Options:
    """A class for storing and retrieving user options preferences from
    volatile and non-volatile memory."""
    def __init__(self):
        self.options = {}

        # defaults
        self.add("first_start", True, False)
        self.add("check_online_updates", True, False)
        self.add("version", APP_VERSION, False)

        # restore non-volatile options
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(options_file)
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
            return
        for option in self.config.options("bleachbit"):
            self.options[option] = (self.get_config(option), False)

    def flush(self):
        """Write non-volatile information to disk"""
        if not os.path.exists(options_dir):
            os.mkdir(options_dir)
        f = open(options_file, 'wb')
        self.config.write(f)

    def get(self, key):
        """Retrieve  a general option from memory"""
        return self.options[key][0]

    def get_config(self, option):
        """Retrieve a general option"""
        if option in boolean_keys:
            return self.config.getboolean('bleachbit', option)
        return self.config.get('bleachbit', option)

    def set(self, key, value):
        """Set a general option"""
        self.options[key] = (value, self.options[key][1])
        if not self.options[key][1]:
            self.config.set('bleachbit', key, str(value))
            self.flush()

    def add(self, key, value, volatile = False):
        """Add a default value for a general option"""
        self.options[key] = (value, volatile)

    def set_tree(self, parent, child, value):
        """Set an option for the tree view.  The child may be None."""
        if not self.config.has_section("tree"):
            self.config.add_section("tree")
        id = parent
        if None != child:
            id = id + "." + child
        self.config.set('tree', id, str(value))
        self.flush()

    def get_tree(self, parent, child):
        """Retrieve an option for the tree view.  The child may be None."""
        id = parent
        if None != child:
            id = id + "." + child
        if not self.config.has_option('tree', id):
            return None
        return self.config.getboolean('tree', id)



options = Options()

import unittest

class TestOptions(unittest.TestCase):
    def test_Options(self):
        o = options
        v = o.get("check_online_updates")
        o.set("check_online_updates", not v)
        self.assertEqual(not v, o.get("check_online_updates"))
        o.set("check_online_updates", v)
        self.assertEqual(v, o.get("check_online_updates"))


if __name__ == '__main__':
        unittest.main()

