# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2011 Andrew Ziem
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
Test case for module Memory
"""



import unittest
import sys

sys.path.append('.')
from bleachbit.Memory import *



class MemoryTestCase(unittest.TestCase):
    """Test case for module Memory"""


    def test_count_linux_swap(self):
        """Test for method count_linux_swap"""
        if 'linux2' != sys.platform:
            return
        n_swaps = count_swap_linux()
        self.assert_(isinstance(n_swaps, (int, long)))
        self.assert_(n_swaps >= 0)
        self.assert_(n_swaps < 10)


    def test_physical_free(self):
        """Test for method physical_free"""
        self.assert_(isinstance(physical_free(), (int, long)))
        self.assert_(physical_free() > 0)
        report_free()


    def test_get_swap_size_linux(self):
        """Test for get_swap_size_linux()"""
        if 'linux2' != sys.platform:
            return
        swapdev = open('/proc/swaps').read().split('\n')[1].split(' ')[0]
        if 0 == len(swapdev):
            print 'no active swap device detected'
            return
        size = get_swap_size_linux(swapdev)
        self.assert_(isinstance(size, (int, long)))
        self.assert_(size > 1024**2)
        print "debug: size of swap '%s': %d B (%d MB)" % \
            (swapdev, size, size / (1024**2))
        proc_swaps = file('/proc/swaps').read()
        size2 = get_swap_size_linux(swapdev, proc_swaps)
        self.assertEqual(size, size2)


    def test_get_swap_uuid(self):
        """Test for method get_swap_uuid"""
        if 'linux2' != sys.platform:
            return
        self.assertEqual(get_swap_uuid('/dev/doesnotexist'), None)



def suite():
    return unittest.makeSuite(MemoryTestCase)


if __name__ == '__main__':
    unittest.main()


