# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2012 Andrew Ziem
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
Test case for module Options
"""



import sys
import unittest

sys.path.append('.')
from bleachbit.Options import boolean_keys, options



class OptionsTestCase(unittest.TestCase):
    """Test case for class Options"""

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

        # test auto commit
        shred = o.get("shred")
        o.set("shred", False)
        self.assertEqual(o.get("shred"), False)
        o.set("shred", True, commit = False)
        self.assertEqual(o.get("shred"), True)
        o.restore()
        self.assertEqual(o.get("shred"), False)
        o.set("shred", shred)
        self.assertEqual(o.get("shred"), shred)

        # try a list
        list_values = ['a', 'b', 'c']
        o.set_list("list_test", list_values)
        self.assertEqual(list_values, o.get_list("list_test"))

        # whitelist
        self.assert_(type(o.get_whitelist_paths() is list))
        whitelist = [ ('file', '/home/foo'), ('folder', '/home') ]
        old_whitelist = o.get_whitelist_paths()
        options.config.remove_section('whitelist/paths')
        self.assert_(type(o.get_whitelist_paths() is list))
        self.assertEqual(o.get_whitelist_paths(), [])
        o.set_whitelist_paths(whitelist)
        self.assert_(type(o.get_whitelist_paths() is list))
        self.assertEqual(set(whitelist), set(o.get_whitelist_paths()))
        o.set_whitelist_paths(old_whitelist)
        self.assertEqual(set(old_whitelist), set(o.get_whitelist_paths()))

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



def suite():
    return unittest.makeSuite(OptionsTestCase)


if __name__ == '__main__':
    unittest.main()

