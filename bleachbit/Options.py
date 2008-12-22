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


import gettext
gettext.install("bleachbit")
import os
import ConfigParser

from globals import *

boolean_keys = ['check_online_updates', 'first_start']

class Options:
    def __init__(self):
        self.options = {}

        # defaults
        self.add("first_start", True, False)
        self.add("check_online_updates", True, False)
        self.add("version", APP_VERSION, False)

        # restore non-volatile options
        self.config = ConfigParser.RawConfigParser()
        self.config.read(options_file)
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
            return
        for option in self.config.options("bleachbit"):
            print "debug: __init__ option = '%s'" % (option)
            self.options[option] = (self.get_config(option), False)
        print self.options

    def get(self, key):
        return self.options[key][0]

    def get_config(self, option):
        if option in boolean_keys:
            return self.config.getboolean('bleachbit', option)
        return self.config.get('bleachbit', option)

    def set(self, key, value):
        self.options[key] = (value, self.options[key][1])
        if not self.options[key][1]:
            self.config.set('bleachbit', key, value)
            if not os.path.exists(options_dir):
                os.mkdir(options_dir)
            f = open(options_file, 'wb')
            self.config.write(f)

    def add(self, key, value, volatile = False):
        self.options[key] = (value, volatile)


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

