# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
# https://www.bleachbit.org
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
Test case for module Options
"""
from __future__ import absolute_import, print_function

from tests import common
import bleachbit.Options
from bleachbit import NoOptionError

import os


class OptionsTestCase(common.BleachbitTestCase):
    """Test case for class Options"""

    def test_Options(self):
        """Unit test for class Options"""
        o = bleachbit.Options.options
        value = o.get("check_online_updates")

        # toggle a boolean
        o.toggle('check_online_updates')
        self.assertEqual(not value, o.get("check_online_updates"))

        # restore original boolean
        o.set("check_online_updates", value)
        self.assertEqual(value, o.get("check_online_updates"))

        # test auto commit
        shred = o.get("shred")
        o.set("shred", False)
        self.assertFalse(o.get("shred"))
        o.set("shred", True, commit=False)
        self.assertTrue(o.get("shred"))
        o.restore()
        self.assertFalse(o.get("shred"))
        o.set("shred", shred)
        self.assertEqual(o.get("shred"), shred)

        # try a list
        list_values = ['a', 'b', 'c']
        o.set_list("list_test", list_values)
        self.assertEqual(list_values, o.get_list("list_test"))

        # whitelist
        self.assertIsInstance(o.get_whitelist_paths(), list)
        whitelist = [('file', '/home/foo'), ('folder', '/home')]
        old_whitelist = o.get_whitelist_paths()
        o.config.remove_section('whitelist/paths')
        self.assertIsInstance(o.get_whitelist_paths(), list)
        self.assertEqual(o.get_whitelist_paths(), [])
        o.set_whitelist_paths(whitelist)
        self.assertIsInstance(o.get_whitelist_paths(), list)
        self.assertEqual(set(whitelist), set(o.get_whitelist_paths()))
        o.set_whitelist_paths(old_whitelist)
        self.assertEqual(set(old_whitelist), set(o.get_whitelist_paths()))

        # these should always be set
        for bkey in bleachbit.Options.boolean_keys:
            self.assertIsInstance(o.get(bkey), bool)

        # language
        value = o.get_language('en')
        self.assertIsInstance(value, bool)
        o.set_language('en', True)
        self.assertTrue(o.get_language('en'))
        o.set_language('en', False)
        self.assertFalse(o.get_language('en'))
        o.set_language('en', value)

        # tree
        o.set_tree("parent", "child", True)
        self.assertTrue(o.get_tree("parent", "child"))
        o.set_tree("parent", "child", False)
        self.assertFalse(o.get_tree("parent", "child"))
        o.config.remove_option("tree", "parent.child")
        self.assertFalse(o.get_tree("parent", "child"))

        # clean up
        del o

    def test_purge(self):
        """Test purging"""
        # By default ConfigParser stores keys (the filenames) as lowercase.
        # This needs special consideration when combined with purging.
        o1 = bleachbit.Options.Options()
        pathname = self.write_file('foo.xml')
        myhash = '0ABCD'
        o1.set_hashpath(pathname, myhash)
        self.assertEqual(myhash, o1.get_hashpath(pathname))
        if 'nt' == os.name:
            # check case sensitivity
            self.assertEqual(myhash, o1.get_hashpath(pathname.upper()))
        del o1

        # reopen
        o2 = bleachbit.Options.Options()
        # write something, which triggers the purge
        o2.set('dummypath', 'dummyvalue', 'hashpath')
        # verify the path was not purged
        self.assertTrue(os.path.exists(pathname))
        self.assertEqual(myhash, o2.get_hashpath(pathname))

        # delete the path
        os.remove(pathname)
        # close and reopen
        del o2
        o3 = bleachbit.Options.Options()
        # write something, which triggers the purge
        o3.set('dummypath', 'dummyvalue', 'hashpath')
        # verify the path was purged
        self.assertRaises(NoOptionError, lambda: o3.get_hashpath(pathname))

    def test_abbreviations(self):
        """Test non-standard, abbreviated booleans T and F"""

        # set values
        o = bleachbit.Options.options
        if not o.config.has_section('test'):
            o.config.add_section('test')
        o.config.set('test', 'test_t_upper', 'T')
        o.config.set('test', 'test_f_upper', 'F')
        o.config.set('test', 'test_t_lower', 't')
        o.config.set('test', 'test_f_lower', 'f')

        # read
        self.assertEqual(o.config.getboolean('test', 'test_t_upper'), True)
        self.assertEqual(o.config.getboolean('test', 'test_t_lower'), True)
        self.assertEqual(o.config.getboolean('test', 'test_f_upper'), False)
        self.assertEqual(o.config.getboolean('test', 'test_f_lower'), False)

        # clean up
        del o
