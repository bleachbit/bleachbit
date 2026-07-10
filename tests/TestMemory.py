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
from contextlib import contextmanager
from unittest import mock

from tests import common
from bleachbit import logger
from bleachbit.FileUtilities import exe_exists
from bleachbit.Memory import (
    _memory_child_script,
    _run_memory_child_fork,
    _run_memory_child_systemd_scope,
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

    @staticmethod
    @contextmanager
    def _mock_systemd_scope_common():
        """Common mocks for _run_memory_child_systemd_scope(): systemd-run
        is present and the real UID is 1000."""
        with mock.patch('bleachbit.FileUtilities.exe_exists',
                        return_value=True):
            with mock.patch('bleachbit.Memory.General.get_real_uid',
                            return_value=1000):
                yield

    def _assert_fork_exit_status(self, waitpid_status, expected):
        """Run _run_memory_child_fork() under the standard parent-path mocks
        and assert it returns ``expected`` for the given waitpid status."""
        # Mock _() to avoid lazy translation setup, which calls
        # subprocess.Popen and would break under mocked os.fork/os.waitpid.
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.Memory.General.get_real_uid',
                            return_value=1000):
                with mock.patch('os.fork', return_value=1234):
                    with mock.patch('os.waitpid',
                                    return_value=(1234, waitpid_status)):
                        self.assertEqual(_run_memory_child_fork(), expected)

    def _assert_wipe_memory_happy_path(self, scope_return, fork_return,
                                       fork_called):
        """Exercise wipe_memory() through its mocked happy path and verify
        the generator yields two progress values then 0, with swap
        re-enabled. ``scope_return`` and ``fork_return`` select which child
        runner is used; ``fork_called`` asserts whether the fork fallback
        is expected to run."""
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.FileUtilities.exe_exists',
                            return_value=True):
                with mock.patch('bleachbit.Memory.get_proc_swaps',
                                return_value=''):
                    with mock.patch('bleachbit.Memory.disable_swap_linux',
                                    return_value=['/dev/sda1']):
                        with mock.patch('bleachbit.Memory.wipe_swap_linux'):
                            with mock.patch(
                                    'bleachbit.Memory._run_memory_child_systemd_scope',
                                    return_value=scope_return):
                                with mock.patch(
                                        'bleachbit.Memory._run_memory_child_fork',
                                        return_value=fork_return) as mock_fork:
                                    with mock.patch(
                                            'bleachbit.Memory.enable_swap_linux') as mock_enable:
                                        gen = wipe_memory()
                                        self.assertTrue(next(gen))
                                        self.assertTrue(next(gen))
                                        self.assertEqual(next(gen), 0)
                                        self.assertTrue(mock_enable.called)
                                        self.assertEqual(mock_fork.called,
                                                         fork_called)

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
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.Memory.General.run_external', return_value=(0, '', '')) as mock_run:
                enable_swap_linux()
                self.assertEqual(mock_run.call_args.args[0], ['swapon', '-a'])

        # Failure
        with mock.patch('bleachbit.Memory._', side_effect=lambda s: s):
            with mock.patch('bleachbit.Memory.General.run_external', return_value=(1, '', 'swapon failed')):
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

        # Happy path via the fork fallback (systemd-run path disabled)
        self._assert_wipe_memory_happy_path(
            scope_return=None, fork_return=0, fork_called=True)

        # Happy path via the systemd scope (fork fallback not used)
        self._assert_wipe_memory_happy_path(
            scope_return=0, fork_return=None, fork_called=False)

    @common.skipIfWindows
    def test_memory_child_script(self):
        """Test for _memory_child_script()"""
        script = _memory_child_script(1000)
        self.assertIn('make_self_oom_target_linux(1000)', script)
        self.assertIn('fill_memory_linux()', script)
        # None uid renders as the literal None
        script_none = _memory_child_script(None)
        self.assertIn('make_self_oom_target_linux(None)', script_none)

    @common.skipIfWindows
    def test_run_memory_child_systemd_scope_missing(self):
        """_run_memory_child_systemd_scope() returns None without systemd-run"""
        with mock.patch('bleachbit.FileUtilities.exe_exists', return_value=False):
            self.assertIsNone(_run_memory_child_systemd_scope())

    @common.skipIfWindows
    def test_run_memory_child_systemd_scope_unique_unit(self):
        """_run_memory_child_systemd_scope() uses a PID-suffixed unit name"""
        captured = {}

        def fake_run(args, env=None, **kwargs):
            captured['args'] = args
            captured['kwargs'] = kwargs
            proc = mock.Mock()
            proc.returncode = 0
            proc.stderr = ''
            return proc

        with self._mock_systemd_scope_common():
            with mock.patch('bleachbit.Memory.subprocess.run', side_effect=fake_run):
                _run_memory_child_systemd_scope()
        unit_args = [a for a in captured['args'] if a.startswith('--unit=')]
        self.assertEqual(len(unit_args), 1)
        self.assertIn(f'bleachbit-wipe-memory-{os.getpid()}', unit_args[0])

    @common.skipIfWindows
    def test_run_memory_child_systemd_scope_signal(self):
        """_run_memory_child_systemd_scope() normalizes signal exit codes"""
        # subprocess.run reports -N when its direct child is killed by signal N.
        # A shell instead exposes this as status 128+N (for SIGKILL, 137), so
        # do not model a shell-observed 137 as subprocess signal termination.
        mock_proc = mock.Mock()
        mock_proc.returncode = -9
        mock_proc.stderr = ''
        with self._mock_systemd_scope_common():
            with mock.patch('bleachbit.Memory.subprocess.run', return_value=mock_proc):
                self.assertEqual(_run_memory_child_systemd_scope(), 9)
        # Normal exit
        mock_proc.returncode = 0
        with self._mock_systemd_scope_common():
            with mock.patch('bleachbit.Memory.subprocess.run', return_value=mock_proc):
                self.assertEqual(_run_memory_child_systemd_scope(), 0)

    @common.skipIfWindows
    def test_run_memory_child_systemd_scope_without_oom_policy(self):
        """Retry without OOMPolicy when scope units do not support it"""
        unsupported_proc = mock.Mock()
        unsupported_proc.returncode = 1
        unsupported_proc.stderr = 'Unknown property OOMPolicy\n'
        success_proc = mock.Mock()
        success_proc.returncode = 0
        success_proc.stderr = ''
        with self._mock_systemd_scope_common():
            with mock.patch(
                    'bleachbit.Memory.subprocess.run',
                    side_effect=(unsupported_proc, success_proc)) as mock_run:
                self.assertEqual(_run_memory_child_systemd_scope(), 0)
        self.assertEqual(mock_run.call_count, 2)
        self.assertIn('--property=OOMPolicy=kill', mock_run.call_args_list[0].args[0])
        self.assertNotIn('--property=OOMPolicy=kill', mock_run.call_args_list[1].args[0])

    @common.skipIfWindows
    def test_run_memory_child_systemd_scope_runtime_failure(self):
        """_run_memory_child_systemd_scope() falls back when systemd-run fails

        A non-zero, non-signal exit code means systemd-run itself failed
        (e.g. no systemd as PID 1, no D-Bus session) and the child never
        ran -- the function returns None so the caller can fall back to
        fork().
        """
        mock_proc = mock.Mock()
        mock_proc.returncode = 1
        mock_proc.stderr = 'Failed to start transient scope unit: Access denied\n'
        with self._mock_systemd_scope_common():
            with mock.patch('bleachbit.Memory.subprocess.run', return_value=mock_proc) as mock_run:
                with mock.patch('bleachbit.Memory.logger') as mock_logger:
                    self.assertIsNone(_run_memory_child_systemd_scope())
                    mock_run.assert_called_once()
                    self.assertTrue(
                        mock_run.call_args.kwargs.get('capture_output'))
                    debug_msgs = [
                        call.args[0] % call.args[1:]
                        if call.args else ''
                        for call in mock_logger.debug.call_args_list
                    ]
                    self.assertTrue(
                        any('Access denied' in msg for msg in debug_msgs),
                        debug_msgs)
        # A high exit code (e.g. 137) is treated as a plain failure, not a
        # signal, since subprocess.run already reports signals as -N.
        mock_proc.returncode = 137
        mock_proc.stderr = ''
        with self._mock_systemd_scope_common():
            with mock.patch('bleachbit.Memory.subprocess.run', return_value=mock_proc):
                self.assertIsNone(_run_memory_child_systemd_scope())

    @common.skipIfWindows
    def test_run_memory_child_fork_child_path(self):
        """_run_memory_child_fork() child path calls the right functions and exits"""
        with mock.patch('bleachbit.Memory.General.get_real_uid', return_value=1000):
            with mock.patch('bleachbit.Memory.make_self_oom_target_linux') as mock_oom:
                with mock.patch('bleachbit.Memory.fill_memory_linux') as mock_fill:
                    with mock.patch('os.fork', return_value=0):
                        with mock.patch('os._exit') as mock_exit:
                            _run_memory_child_fork()
                            mock_oom.assert_called_once_with(1000)
                            mock_fill.assert_called_once()
                            mock_exit.assert_called_once_with(0)

    @common.skipIfWindows
    def test_run_memory_child_fork_normal_exit(self):
        """_run_memory_child_fork() returns 0 when child exits normally"""
        self._assert_fork_exit_status(0, 0)

    @common.skipIfWindows
    def test_run_memory_child_fork_signal(self):
        """_run_memory_child_fork() returns signal number when child is killed"""
        self._assert_fork_exit_status(9, 9)

    @common.skipIfWindows
    def test_run_memory_child_fork_nonzero_exit(self):
        """_run_memory_child_fork() returns a non-zero exit code"""
        self._assert_fork_exit_status(1 << 8, 1)

    @common.skipIfWindows
    def test_run_memory_child_fork_uid_exception(self):
        """_run_memory_child_fork() falls back to None when get_real_uid fails"""
        with mock.patch('bleachbit.Memory.General.get_real_uid', side_effect=Exception('boom')):
            with mock.patch('bleachbit.Memory.make_self_oom_target_linux') as mock_oom:
                with mock.patch('bleachbit.Memory.fill_memory_linux'):
                    with mock.patch('os.fork', return_value=0):
                        with mock.patch('os._exit'):
                            _run_memory_child_fork()
                            mock_oom.assert_called_once_with(None)

    @common.skipIfWindows
    def test_swap_off_swap_on(self):
        """Test for disabling and enabling swap"""
        if not common.have_root():
            self.skipTest('not enough privileges')
        disable_swap_linux()
        enable_swap_linux()
