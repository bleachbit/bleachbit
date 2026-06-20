# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Memory
"""

import os
import re
from unittest import mock

from tests import common
from bleachbit import logger
from bleachbit.FileUtilities import exe_exists
from bleachbit.Memory import (
    count_swap_linux,
    disable_swap_linux,
    enable_swap_linux,
    get_proc_swaps,
    get_swap_size_linux,
    get_swap_uuid,
    make_self_oom_target_linux,
    parse_swapoff,
    physical_free, physical_free_darwin,
    report_free,
    wipe_memory,
    wipe_swap_linux)


class MemoryTestCase(common.BleachbitTestCase):
    """Test case for module Memory"""

    @common.skipIfWindows
    def test_get_proc_swaps(self):
        """Test for method get_proc_swaps"""
        if not exe_exists('swapon'):
            self.skipTest('swapon not found')
        ret = get_proc_swaps()
        self.assertGreater(len(ret), 10)
        if not re.search(r'Filename\s+Type\s+Size', ret):
            raise RuntimeError(
                "Unexpected first line in swap summary '%s'" % ret)

    @common.skipIfWindows
    def test_make_self_oom_target_linux(self):
        """Test for method make_self_oom_target_linux"""

        # preserve
        euid = os.geteuid()

        # Minimally test there is no traceback
        make_self_oom_target_linux()

        # restore
        os.seteuid(euid)

    @common.skipIfWindows
    def test_count_linux_swap(self):
        """Test for method count_linux_swap"""
        n_swaps = count_swap_linux()
        self.assertIsInteger(n_swaps)
        self.assertTrue(0 <= n_swaps < 10)

    @common.skipIfWindows
    def test_physical_free_darwin(self):
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
        self.assertRaises(RuntimeError, physical_free_darwin,
                          lambda: "Invalid header")

    @common.skipIfWindows
    def test_physical_free(self):
        """Test for method physical_free"""
        ret = physical_free()
        self.assertIsInteger(
            ret, 'physical_free() returns variable type %s' % type(ret))
        self.assertGreater(physical_free(), 0)
        report_free()

    @common.skipIfWindows
    def test_get_swap_size_linux(self):
        """Test for get_swap_size_linux()"""
        if not exe_exists('swapon'):
            self.skipTest('swapon not found')
        with open('/proc/swaps', encoding='utf-8') as f:
            swapdev = f.read().split('\n')[1].split(' ')[0]
        if 0 == len(swapdev):
            self.skipTest('no active swap device detected')
        size = get_swap_size_linux(swapdev)
        self.assertIsInteger(size)
        self.assertGreater(size, 1024 ** 2)
        logger.debug("size of swap '%s': %d B (%d MB)",
                     swapdev, size, size / (1024 ** 2))
        with open('/proc/swaps', encoding='utf-8') as f:
            proc_swaps = f.read()
        size2 = get_swap_size_linux(swapdev, proc_swaps)
        self.assertEqual(size, size2)

    @common.skipIfWindows
    def test_get_swap_uuid(self):
        """Test for method get_swap_uuid"""
        if not exe_exists('blkid'):
            self.skipTest('blkid not found')
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

    @common.skipIfWindows
    def test_disable_swap_linux(self):
        """Test for disable_swap_linux() with mocks"""
        # No swap active - early return
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=0):
            self.assertIsNone(disable_swap_linux())

        # Command failure
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=1):
            with mock.patch('bleachbit.Memory.General.run_external', return_value=(1, '', 'swapoff failed')):
                self.assertRaisesRegex(
                    RuntimeError, 'swapoff failed', disable_swap_linux)

        # Unexpected output
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=1):
            with mock.patch('bleachbit.Memory.General.run_external', return_value=(0, 'unexpected\n', '')):
                self.assertRaisesRegex(
                    RuntimeError, 'Unexpected output', disable_swap_linux)

        # Parse success
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=1):
            with mock.patch('bleachbit.Memory.General.run_external', return_value=(0, 'swapoff /dev/sda3\n', '')):
                devices = disable_swap_linux()
                self.assertEqual(devices, ['/dev/sda3'])

    @common.skipIfWindows
    def test_enable_swap_linux(self):
        """Test for enable_swap_linux() with mocks"""
        # Success
        mock_proc = mock.Mock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ('', '')
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.Memory.subprocess.Popen', return_value=mock_proc) as mock_popen:
                enable_swap_linux()
                self.assertTrue(mock_popen.call_args.kwargs['text'])

        # Failure
        mock_proc = mock.Mock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = ('', 'swapon failed')
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.Memory.subprocess.Popen', return_value=mock_proc):
                self.assertRaisesRegex(
                    RuntimeError, 'swapon failed', enable_swap_linux)

    @common.skipIfWindows
    def test_get_swap_size_linux_errors(self):
        """Test for get_swap_size_linux() error paths"""
        # Malformed header
        self.assertRaisesRegex(
            RuntimeError, 'Unexpected first line',
            get_swap_size_linux, '/dev/sda1', 'bad header\n')

        # Missing device
        proc_swaps = 'Filename\tType\tSize\tUsed\tPriority\n/dev/sda2\tpartition\t123\t0\t-2\n'
        self.assertRaisesRegex(
            RuntimeError, 'cannot find size of swap device',
            get_swap_size_linux, '/dev/sda1', proc_swaps)

    @common.skipIfWindows
    def test_wipe_swap_linux(self):
        """Test for wipe_swap_linux() with mocks"""
        # devices is None - early return
        wipe_swap_linux(None, '')

        # Swap still in use
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=1):
            self.assertRaisesRegex(
                RuntimeError, 'Cannot wipe swap while it is in use',
                wipe_swap_linux, ['/dev/sda1'], '')

        # Safety limit exceeded
        safety_limit = 29 * 1024 ** 3
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=0):
            with mock.patch('bleachbit.Memory.get_swap_size_linux', return_value=safety_limit + 1):
                self.assertRaisesRegex(
                    RuntimeError, 'larger .* than expected',
                    wipe_swap_linux, ['/dev/sda1'], '')

        # UUID preservation
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=0):
            with mock.patch('bleachbit.Memory.get_swap_size_linux', return_value=1024 ** 2):
                with mock.patch('bleachbit.Memory.get_swap_uuid', return_value='abc-123'):
                    with mock.patch('bleachbit.Memory.wipe_contents'):
                        with mock.patch('bleachbit.Memory.General.run_external', return_value=(0, '', '')) as mock_run:
                            wipe_swap_linux(['/dev/sda1'], '')
                            args = mock_run.call_args[0][0]
                            self.assertIn('-U', args)
                            self.assertIn('abc-123', args)

        # mkswap failure
        with mock.patch('bleachbit.Memory.count_swap_linux', return_value=0):
            with mock.patch('bleachbit.Memory.get_swap_size_linux', return_value=1024 ** 2):
                with mock.patch('bleachbit.Memory.get_swap_uuid', return_value=None):
                    with mock.patch('bleachbit.Memory.wipe_contents'):
                        with mock.patch('bleachbit.Memory.General.run_external', return_value=(1, '', 'mkswap failed')):
                            self.assertRaisesRegex(
                                RuntimeError, 'mkswap failed',
                                wipe_swap_linux, ['/dev/sda1'], '')

    @common.skipIfWindows
    def test_wipe_memory(self):
        """Test for wipe_memory() with mocks"""
        # Command missing
        with mock.patch('bleachbit.FileUtilities.exe_exists', return_value=False):
            gen = wipe_memory()
            self.assertRaisesRegex(
                RuntimeError, 'Command swapon not found', next, gen)

        # Happy path
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.FileUtilities.exe_exists', return_value=True):
                with mock.patch('bleachbit.Memory.get_proc_swaps', return_value=''):
                    with mock.patch('bleachbit.Memory.disable_swap_linux', return_value=['/dev/sda1']):
                        with mock.patch('bleachbit.Memory.wipe_swap_linux'):
                            with mock.patch('os.fork', return_value=1):
                                with mock.patch('os.waitpid', return_value=(1, 0)):
                                    with mock.patch('bleachbit.Memory.enable_swap_linux'):
                                        gen = wipe_memory()
                                        self.assertTrue(next(gen))
                                        self.assertTrue(next(gen))
                                        self.assertEqual(next(gen), 0)

    @common.skipIfWindows
    def test_swap_off_swap_on(self):
        """Test for disabling and enabling swap"""
        if not common.have_root():
            self.skipTest('not enough privileges')
        disable_swap_linux()
        enable_swap_linux()
