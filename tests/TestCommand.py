# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
Test case for Command
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from bleachbit.Command import *
from tests import common

import unittest


class CommandTestCase(unittest.TestCase, common.AssertFile):

    """Test case for Command"""

    def test_Delete(self, cls=Delete):
        """Unit test for Delete"""
        path = common.touch_temp_file(b'foo', prefix='bleachbit-test-command')
        cmd = cls(path)
        self.assertExists(path)

        # preview
        ret = cmd.execute(really_delete=False).next()
        s = str(cmd)
        self.assertGreater(ret['size'], 0)
        self.assertEqual(ret['path'], path)
        self.assertExists(path)

        # delete
        ret = cmd.execute(really_delete=True).next()
        self.assertGreater(ret['size'], 0)
        self.assertEqual(ret['path'], path)
        self.assertNotExists(path)

    def test_Function(self):
        """Unit test for Function"""
        path = common.touch_temp_file(b'foo', prefix='bleachbit-test-command')
        cmd = Function(path, FileUtilities.delete, 'bar')
        self.assertExists(path)
        self.assertGreater(os.path.getsize(path), 0)

        # preview
        ret = cmd.execute(False).next()
        self.assertExists(path)
        self.assertGreater(os.path.getsize(path), 0)

        # delete
        ret = cmd.execute(True).next()
        self.assert_(ret['size'] > 0, 'Size is %d' % ret['size'])
        self.assertEqual(ret['path'], path)
        self.assertNotExists(path)

    def test_Shred(self):
        """Unit test for Shred"""
        self.test_Delete(Shred)


def suite():
    return unittest.makeSuite(CommandTestCase)


if __name__ == '__main__':
    unittest.main()
