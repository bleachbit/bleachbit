# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2010 Andrew Ziem
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
Test case for module DeepScan
"""



import os
import sys
import tempfile
import unittest

sys.path.append('.')
from bleachbit.DeepScan import DeepScan



class DeepScanTestCase(unittest.TestCase):
    """Test Case for module DeepScan"""


    def _touch(self, fn):
        """Create an empty file"""
        open(fn, 'w')


    def _test_encoding(self, fn):
        """Test encoding"""

        tempd = tempfile.mkdtemp('bleachbit-deepscan')
        self.assert_(os.path.exists(tempd))

        fullpath = os.path.join(tempd, fn)
        self._touch(fullpath)
        self.assert_(os.path.exists(fullpath))

        ds = DeepScan()
        ds.add_search(tempd, '^%s$' % fn)
        found = False
        for ret in ds.scan():
            if True == ret:
                continue
            self.assert_(ret == fullpath)
            found = True
        self.assert_(found, "Did not find '%s'" % fullpath)

        os.unlink(fullpath)
        self.assert_(not os.path.exists(fullpath))
        os.rmdir(tempd)
        self.assert_(not os.path.exists(tempd))


    def test_encoding(self):
        """Test encoding"""
        tests = ('äöüßÄÖÜ', \
            "עִבְרִית")

        for test in tests:
            self._test_encoding(test)


    def test_DeepScan(self):
        """Unit test for class DeepScan"""
        ds = DeepScan()
        path = os.path.expanduser('~')
        ds.add_search(path, '^Makefile$')
        ds.add_search(path, '~$')
        ds.add_search(path, 'bak$')
        ds.add_search(path, '^Thumbs.db$')
        ds.add_search(path, '^Thumbs.db:encryptable$')
        for ret in ds.scan():
            if True == ret:
                # it's yielding control to the GTK idle loop
                continue
            self.assert_(isinstance(ret, (str, unicode)), \
                "Expecting string but got '%s' (%s)" % \
                 (ret, str(type(ret))))
            self.assert_(os.path.lexists(ret))


def suite():
    return unittest.makeSuite(DeepScanTestCase)


if __name__ == '__main__':
    unittest.main()

