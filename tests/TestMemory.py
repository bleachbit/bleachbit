# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module Memory
"""

from __future__ import absolute_import, print_function

from tests import common
from bleachbit.Memory import *

import unittest
import sys

running_linux = sys.platform.startswith('linux')


class MemoryTestCase(common.BleachbitTestCase):
    """Test case for module Memory"""

    @unittest.skipUnless(running_linux, 'not running linux')
    def test_get_proc_swaps(self):
        """Test for method get_proc_swaps"""
        ret = get_proc_swaps()
        self.assertGreater(len(ret), 10)
        if not re.search('Filename\s+Type\s+Size', ret):
            raise RuntimeError("Unexpected first line in swap summary '%s'" % ret)

    @unittest.skipUnless(running_linux, 'not running linux')
    def test_make_self_oom_target_linux(self):
        """Test for method make_self_oom_target_linux"""

        # preserve
        euid = os.geteuid()

        # Minimally test there is no traceback
        make_self_oom_target_linux()

        # restore
        os.seteuid(euid)

    @unittest.skipUnless(running_linux, 'not running linux')
    def test_count_linux_swap(self):
        """Test for method count_linux_swap"""
        n_swaps = count_swap_linux()
        self.assertIsInteger(n_swaps)
        self.assertTrue(0 <= n_swaps < 10)

    def test_physical_free_darwin(self):
        # TODO: use mock
        self.assertEqual(physical_free_darwin(lambda:
"""Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                              836891.
Pages active:                            588004.
Pages inactive:                           16985.
Pages speculative:                        89776.
Pages throttled:                              0.
Pages wired down:                        468097.
Pages purgeable:                          58313.
"Translation faults":                3109985921.
Pages copy-on-write:                   25209334.
Pages zero filled:                    537180873.
Pages reactivated:                    132264973.
Pages purged:                          11567935.
File-backed pages:                       184609.
Anonymous pages:                         510156.
Pages stored in compressor:              784977.
Pages occupied by compressor:             96724.
Decompressions:                        66048421.
Compressions:                          90076786.
Pageins:                              758631430.
Pageouts:                              30477017.
Swapins:                               19424481.
Swapouts:                              20258188.
"""), 3427905536)
        self.assertRaises(RuntimeError, physical_free_darwin, lambda: "Invalid header")

    def test_physical_free(self):
        """Test for method physical_free"""
        ret = physical_free()
        self.assertIsInteger(ret, 'physical_free() returns variable type %s' % type(ret))
        self.assertGreater(physical_free(), 0)
        report_free()

    @unittest.skipUnless(running_linux, 'not running linux')
    def test_get_swap_size_linux(self):
        """Test for get_swap_size_linux()"""
        with open('/proc/swaps') as f:
            swapdev = f.read().split('\n')[1].split(' ')[0]
        if 0 == len(swapdev):
            self.skipTest('no active swap device detected')
        size = get_swap_size_linux(swapdev)
        self.assertIsInteger(size)
        self.assertGreater(size, 1024 ** 2)
        logger.debug("size of swap '%s': %d B (%d MB)", swapdev, size, size / (1024 ** 2))
        with open('/proc/swaps') as f:
            proc_swaps = f.read()
        size2 = get_swap_size_linux(swapdev, proc_swaps)
        self.assertEqual(size, size2)

    @unittest.skipUnless(running_linux, 'not running linux')
    def test_get_swap_uuid(self):
        """Test for method get_swap_uuid"""
        self.assertEqual(get_swap_uuid('/dev/doesnotexist'), None)

    def test_parse_swapoff(self):
        """Test for method parse_swapoff"""
        tests = (
            # Ubuntu 15.10 has format "swapoff /dev/sda3"
            ('swapoff /dev/sda3', '/dev/sda3'),
            ('swapoff for /dev/sda6', '/dev/sda6'),
            ('swapoff on /dev/mapper/lubuntu-swap_1', '/dev/mapper/lubuntu-swap_1'))

        for test in tests:
            self.assertEqual(parse_swapoff(test[0]), test[1])

    @unittest.skipUnless(running_linux, 'skipping test on non-linux')
    def test_swap_off_swap_on(self):
        """Test for disabling and enabling swap"""
        if not General.sudo_mode() or os.getuid() > 0:
            self.skipTest('not enough privileges')
        disable_swap_linux()
        enable_swap_linux()
