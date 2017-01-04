# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
# http://www.bleachbit.org
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
Test case for Common
"""


import os
import sys
import tempfile
import unittest

import common

sys.path.append('.')
import bleachbit.Common as Common


class CommonTestCase(unittest.TestCase, common.AssertFile):

    """Test case for Common."""

    def test_expandvars(self):
        """Unit test for expandvars."""
        var = Common.expandvars('$HOME')
        self.assertIsInstance(var, unicode)

    def test_expanduser(self):
        """Unit test for expanduser."""
        # Return Unicode when given str.
        var = Common.expanduser('~')
        self.assertIsInstance(var, unicode)
        # Return Unicode when given Unicode.
        var = Common.expanduser(u'~')
        self.assertIsInstance(var, unicode)
        # Blank input should give blank output.
        self.assertEqual(Common.expanduser(''), u'')
        # An absolute path should not be altered.
        if 'posix' == os.name:
            abs_dir = os.path.expandvars('$HOME')
        if 'nt' == os.name:
            abs_dir = os.path.expandvars('%USERPROFILE%')
        self.assertExists(abs_dir)
        self.assertEqual(Common.expanduser(abs_dir), abs_dir)
        # Path with tilde should be expanded
        self.assertTrue(os.path.normpath(Common.expanduser('~')), os.path.normpath(os.path.expanduser('~')))
        # A relative path (without a reference to the home directory)
        # should not be expanded.
        self.assertEqual(Common.expanduser('common'), 'common')

def suite():
    return unittest.makeSuite(CommonTestCase)


if __name__ == '__main__':
    unittest.main()
