# vim: ts=4:sw=4:expandtab
# coding=utf-8

# BleachBit
# Copyright (C) 2008-2023 Andrew Ziem
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
Test cases for __init__
"""

from tests import common

import os


class InitTestCase(common.BleachbitTestCase):

    """Test cases for __init__"""

    def test_expanduser(self):
        """Unit test for function expanduser()"""
        # already absolute
        test_input = '/home/user/foo'
        test_output = os.path.expanduser(test_input)
        self.assertEqual(test_input, test_output)

        # tilde not at beginning
        test_input = '/home/user/~'
        test_output = os.path.expanduser(test_input)
        self.assertEqual(test_input, test_output)

        # should be expanded
        if os.name == 'nt':
            test_inputs = ('~', r'~\ntuser.dat')
        elif os.name == 'posix':
            test_inputs = ('~', '~/.profile')
        for test_input in test_inputs:
            test_output = os.path.expanduser(test_input)
            self.assertNotEqual(test_input, test_output)
            self.assertExists(test_output)
            if os.name == 'posix':
                self.assertTrue(os.path.samefile(
                    test_output, os.path.expanduser(test_input)))


def suite():
    return unittest.makeSuite(InitTestCase)
