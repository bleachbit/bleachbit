# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for the module Process
"""

# These tests reach into internals on purpose.
# pylint: disable=protected-access
import os
import subprocess
import sys
from unittest import mock

# While POSIX systems may not always have psutil,
# the test environment (and Windows) always should have it.
import psutil

from bleachbit import IS_LINUX, IS_WINDOWS
from bleachbit.General import (get_real_uid, get_real_username, resolve_exe,
                               sudo_mode)
from bleachbit.Process import (
    _enumerate_proc_fs,
    _enumerate_ps_aux,
    enumerate_processes,
    is_pid_running,
    is_process_running,
    ProcessInfo,
)
from tests import common


class ProcessTestCase(common.BleachbitTestCase):

    def test_enumerate_processes(self):
        """Test enumerate_processes()"""
        funcs = [enumerate_processes]
        if IS_LINUX:
            funcs.append(_enumerate_proc_fs)
        for func in funcs:
            with self.subTest(func=func.__name__):
                processes = list(func())
                self.assertGreater(len(processes), 0)

                for proc in processes:
                    self.assertIsInstance(proc, ProcessInfo)
                    self.assertIsInstance(proc.pid, int)
                    self.assertGreaterEqual(proc.pid, 0, proc)
                    self.assertIsInstance(proc.name, str)
                    self.assertGreater(len(proc.name), 0)
                    self.assertIsInstance(proc.same_user, bool)

    @mock.patch('subprocess.check_output')
    @common.skipIfWindows
    @common.also_with_sudo
    def test_enumerate_ps_aux(self, mock_check_output):
        username = get_real_username()
        ps_out = f"""USER               PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
root               703   0.0  0.0  2471428   2792   ??  Ss   20May16   0:01.30 SubmitDiagInfo
alocaluseraccount   681   0.0  0.0  2471568    856   ??  S    20May16   0:00.81 DiskUnmountWatcher
alocaluseraccount   666   0.0  0.0  2507092   3488   ??  S    20May16   0:17.47 SpotlightNetHelper
root               665   0.0  0.0  2497508    512   ??  Ss   20May16   0:11.30 check_afp
alocaluseraccount   646   0.0  0.1  2502484   5656   ??  S    20May16   0:03.62 DataDetectorsDynamicData
alocaluseraccount   632   0.0  0.0  2471288    320   ??  S    20May16   0:02.79 mdflagwriter
alocaluseraccount   616   0.0  0.0  2497596    520   ??  S    20May16   0:00.41 familycircled
alocaluseraccount   573   0.0  0.0  3602328   2440   ??  S    20May16   0:39.64 storedownloadd
alocaluseraccount   572   0.0  0.0  2531184   3116   ??  S    20May16   0:02.93 LaterAgent
{username}   561   0.0  0.0  2471492    584   ??  S    20May16   0:00.21 USBAgent
alocaluseraccount   535   0.0  0.0  2496656    524   ??  S    20May16   0:00.33 storelegacy
root               531   0.0  0.0  2501712    588   ??  Ss   20May16   0:02.40 suhelperd
alocaluseraccount   530   0.0  0.0  2496700    530   ??  S    20May16   0:04.44 Google Chrome Helper
"""
        mock_check_output.return_value = ps_out

        result = list(_enumerate_ps_aux())
        expected = [
            ProcessInfo(703, 'SubmitDiagInfo', False),
            ProcessInfo(681, 'DiskUnmountWatcher', False),
            ProcessInfo(666, 'SpotlightNetHelper', False),
            ProcessInfo(665, 'check_afp', False),
            ProcessInfo(646, 'DataDetectorsDynamicData', False),
            ProcessInfo(632, 'mdflagwriter', False),
            ProcessInfo(616, 'familycircled', False),
            ProcessInfo(573, 'storedownloadd', False),
            ProcessInfo(572, 'LaterAgent', False),
            ProcessInfo(561, 'USBAgent', True),
            ProcessInfo(535, 'storelegacy', False),
            ProcessInfo(531, 'suhelperd', False),
            ProcessInfo(530, 'Google Chrome Helper', False),
        ]
        self.assertEqual(result, expected)
        mock_check_output.assert_called_once()
        call = mock_check_output.call_args
        self.assertEqual(call.args[0], [resolve_exe('ps'), 'aux', '-c'])
        self.assertTrue(call.kwargs.get('universal_newlines'))
        # the child's env is sanitized (LD_*/DYLD_* dropped when root)
        self.assertIn('env', call.kwargs)

        mock_check_output.return_value = 'invalid-input'
        with self.assertRaises(RuntimeError):
            list(_enumerate_ps_aux())

    @common.skipIfWindows
    def test_enumerate_proc_fs_comm_with_spaces(self):
        """/proc fallback keeps a comm field with spaces intact"""
        pid_dir = self.mkdir('1234')
        # Regular file, not a symlink, so os.readlink raises OSError
        self.write_file(os.path.join(pid_dir, 'exe'))
        self.write_file(
            os.path.join(pid_dir, 'stat'),
            text="1234 (Web Content) S 1 1234 1234 0 -1 4194304 0 0 0 0")

        result = list(_enumerate_proc_fs(self.tempdir))
        self.assertEqual(
            result, [ProcessInfo(1234, 'Web Content', not sudo_mode())])

    @common.skipUnlessLinux
    def test_enumerate_proc_fs_script_comm(self):
        """/proc fallback yields comm even when exe and argv[0] differ (e.g. scripts)"""
        if not sys.executable:
            self.skipTest('sys.executable is empty')
        # 15 = PR_SET_NAME: change the name of the current process.
        code = ("import ctypes, time\n"
                "# PR_SET_NAME = 15\n"
                "ctypes.CDLL(None).prctl(15, b'bb-test-comm', 0, 0, 0)\n"
                "print('ready', flush=True)\n"
                "time.sleep(60)\n")
        with subprocess.Popen([sys.executable, '-c', code],
                              stdout=subprocess.PIPE, text=True) as proc:
            try:
                # wait until the child has renamed itself
                self.assertEqual(proc.stdout.readline().strip(), 'ready')
                names = {p.name for p in _enumerate_proc_fs()
                         if p.pid == proc.pid}
            finally:
                proc.terminate()
        self.assertIn('bb-test-comm', names)

    @common.also_with_sudo
    def test_is_process_running_self(self):
        """Test that this process is running"""
        exe_names = [psutil.Process().name()]
        parent = psutil.Process().parent()
        if parent:
            exe_names.append(parent.name())

        if IS_WINDOWS:
            exe_names.extend([e.swapcase() for e in exe_names])

        # Under sudo the test process (and its parent) run as root, while
        # 'same_user' intentionally compares against the real (non-root)
        # user, so the current process is not considered 'same_user'.
        # The require_same_user=True assertion is only valid when the
        # current process actually runs as the real user.
        check_same_user = not sudo_mode()

        for exe_name in exe_names:
            self.assertTrue(is_process_running(exe_name, False))
            if check_same_user:
                self.assertTrue(is_process_running(exe_name, True))

    @common.also_with_sudo
    def test_is_process_running_does_not_exist(self):
        """Test is_process_running() with processes that do not exist"""
        this_proc_name = psutil.Process().name()
        tests = [
            'does_not_exist',
            '',
            '*',
            this_proc_name + 'x',
            'x' + this_proc_name,
            this_proc_name[1:]
        ]
        # if current process is 'python3', then not unlikely 'python' could
        # be running too, so omit: this test `psutil.Process().name()[:-1]`
        if not this_proc_name == 'python3':
            tests.append(this_proc_name[:-1])
        if not IS_WINDOWS:
            tests.append(this_proc_name.swapcase())
        for exename in tests:
            for require_same_user in (False, True):
                with self.subTest(exename=exename, require_same_user=require_same_user):
                    self.assertFalse(is_process_running(exename, require_same_user),
                                     f'is_running({exename}, {require_same_user})')

    @common.skipUnlessLinux
    @common.also_with_sudo
    def test_is_process_running_linux(self):
        """Unit test for method is_process_running()"""
        # Do not use get_executable() here because of how it
        # handles symlinks.
        # sys.executable may look like /usr/bin/python3
        # When running under `env -i`, then sys.executable is empty.
        exe = None
        if sys.executable:
            exe = os.path.basename(os.path.realpath(sys.executable))
        else:
            try:
                with open('/proc/self/stat', 'r', encoding='utf-8') as f:
                    exe = f.read().split()[1].strip('()')
            except (IOError, IndexError):
                self.skipTest(
                    "Could not determine current process name from /proc/self/stat")
        tests = [
            # (expected, exe, require_same_user)
            (True, exe, False),  # Check the actual process name
            (True, exe, True),  # Check the actual process name
        ]
        # These do not exist.
        tests += [
            (False, 'does-not-exist', True),
            (False, 'does-not-exist', False),
        ]
        for expected, exename, require_same_user in tests:
            with self.subTest(exename=exename, require_same_user=require_same_user):
                self.assertEqual(is_process_running(exename, require_same_user), expected,
                                 f'is_running({exename}, {require_same_user})')
        # PID 1 belongs to root, or to this user inside a container. By PID,
        # since its name is shared with the user's own systemd instance
        init_same_user = os.stat('/proc/1').st_uid == get_real_uid()
        self.assertTrue(is_pid_running(1, False))
        self.assertEqual(is_pid_running(1, True), init_same_user)

    @common.skipUnlessMac
    @common.also_with_sudo
    def test_is_process_running_macos(self):
        """Unit test for is_process_running() on macOS.

        On macOS, psutil reports the process name as the app-bundle
        executable name (truncated to 15 chars, like 'comm'), while
        the 'exe' basename may give the full name.  Both are yielded by
        _enumerate_psutil_posix, so is_process_running should find the
        process by either name.
        """
        proc = psutil.Process()
        psutil_name = proc.name()  # 'Process'
        exe = proc.exe()  # '/Library/Developer/.../Python' (long string)
        exe_basename = os.path.basename(exe) if exe else psutil_name
        self.assertTrue(psutil_name, 'psutil did not return a process name')

        # Names by which the current process should be detectable.
        detectable_names = {psutil_name}
        if exe_basename != psutil_name:
            detectable_names.add(exe_basename)

        check_same_user = not sudo_mode()
        for name in detectable_names:
            self.assertTrue(is_process_running(name, False),
                            f'is_running({name}, False)')
            if check_same_user:
                self.assertTrue(is_process_running(name, True),
                                f'is_running({name}, True)')

        # macOS system daemons that run as root, so they should be
        # running but not as the same (real) user.
        non_user_exes = ('bluetoothd', 'logd', 'launchd')
        for name in non_user_exes:
            with self.subTest(exename=name, require_same_user=True):
                self.assertTrue(is_process_running(name, False),
                                f'expected {name} to be running on macOS')
                self.assertFalse(is_process_running(name, True),
                                 f'{name} should not be same_user')

        # These do not exist.
        for exename in ('sol.exe', 'systemd', 'kthreadd', ''):
            for require_same_user in (False, True):
                with self.subTest(exename=exename,
                                  require_same_user=require_same_user):
                    self.assertFalse(is_process_running(exename, require_same_user),
                                     f'is_running({exename}, {require_same_user})')

    def test_psutil_not_imported_at_module_load(self):
        """psutil stays off the import path until something needs it"""
        code = ('import sys, bleachbit.Process; '
                'print("psutil" in sys.modules)')
        proc = subprocess.run([sys.executable, '-c', code],
                              capture_output=True, text=True, check=True, timeout=60,
                              cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(proc.stdout.strip(), 'False', proc.stderr)

    def test_missing_psutil(self):
        """Process imports without psutil and remembers it is missing"""
        with common.mock_missing_package(
                'psutil',
                clear_prefixes=('bleachbit.Process',)):
            # `import x.y as Y` is deliberate: mock_missing_package drops the
            # submodule from sys.modules but leaves the parent attribute, so
            # `from x import Y` would hand back the stale module.
            # pylint: disable=consider-using-from-import
            import bleachbit.Process as Process
            # force the lazy detection
            self.assertIsNone(Process._import_psutil())
            # assertIs, not assertFalse: the un-probed state is None.
            self.assertIs(Process._has_psutil, False)

    @common.skipUnlessWindows
    def test_is_process_running_windows(self):
        """Test is_process_running() on Windows"""
        # winlogon.exe runs on Windows XP and Windows 7
        # explorer.exe did not run in CI, but it does as of 2025-01-25.
        # svchost.exe runs both as system and current user on Windows 11
        # svchost.exe does not always run as the same user in CI.
        tests = ((True, 'winlogon.exe', False),
                 (True, 'WinLogOn.exe', False),
                 (False, 'doesnotexist.exe', False),
                 (True, 'explorer.exe', True),
                 (True, 'svchost.exe', False),
                 (True, 'services.exe', False),
                 (False, 'services.exe', True),
                 (True, 'wininit.exe', False),
                 (False, 'wininit.exe', True))

        for expected, exename, require_same_user in tests:
            with self.subTest(exename=exename, require_same_user=require_same_user):
                result = is_process_running(exename, require_same_user)
                self.assertEqual(
                    expected, result, f'Expecting is_process_running({exename}, {require_same_user}) = {expected}, got {result}')

    def test_missing_psutil_import(self):
        """Process imports without psutil and remembers it is missing"""
        with common.mock_missing_package(
                'psutil',
                clear_prefixes=('bleachbit.Process',)):
            # `import x.y as Y` is deliberate: mock_missing_package drops the
            # submodule from sys.modules but leaves the parent attribute, so
            # `from x import Y` would hand back the stale module.
            # pylint: disable=consider-using-from-import
            import bleachbit.Process as Process
            # force the lazy detection
            self.assertIsNone(Process._import_psutil())
            # assertIs, not assertFalse: the un-probed state is None.
            self.assertIs(Process._has_psutil, False)
            if IS_WINDOWS:
                with self.assertRaises(RuntimeError):
                    list(Process.enumerate_processes())
