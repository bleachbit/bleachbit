# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
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
Test case for Command
"""



import sys
import unittest
import tempfile

sys.path.append('.')
from bleachbit.Command import *



class TestCommand(unittest.TestCase):
    """Test cases for commands"""


    def test_Delete(self, cls = Delete):
        """Unit test for Delete"""
        (fd, path) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, "foo")
        os.close(fd)
        cmd = cls(path)
        self.assert_(os.path.exists(path))

        # preview
        ret = cmd.execute(really_delete = False).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(os.path.exists(path))

        # delete
        ret = cmd.execute(really_delete = True).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(not os.path.exists(path))


    def test_Function(self):
        """Unit test for Function"""
        (fd, path) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, "foo")
        os.close(fd)
        cmd = Function(path, FileUtilities.delete, 'bar')
        self.assert_(os.path.exists(path))

        # preview
        ret = cmd.execute(False).next()
        self.assert_(os.path.exists(path))

        # delete
        ret = cmd.execute(True).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(not os.path.exists(path))


    def test_Shred(self):
        """Unit test for Shred"""
        self.test_Delete(Shred)


if __name__ == '__main__':
    unittest.main()

