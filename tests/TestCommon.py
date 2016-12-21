# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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


import sys
import unittest
import tempfile

sys.path.append('.')
import bleachbit.Common as Common


class CommonTestCase(unittest.TestCase):

    """Test case for Common."""

    def test_expandvars(self):
        """Unit test for expandvars."""
        var = Common.expandvars('$HOME')
        self.assertTrue(isinstance(var, unicode))

    def test_expanduser(self):
        """Unit test for expanduser."""
        var = Common.expanduser('~')
        self.assertTrue(isinstance(var, unicode))
        var = Common.expanduser(u'~')
        self.assertTrue(isinstance(var, unicode))

def suite():
    return unittest.makeSuite(CommonTestCase)


if __name__ == '__main__':
    unittest.main()
