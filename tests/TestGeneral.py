# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
Test case for module General
"""

# standard library
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from unittest import mock

# local
from bleachbit import logger
from bleachbit.FileUtilities import exe_exists, exists_in_path
from bleachbit.General import (
    boolstr_to_bool,
    get_executable,
    get_real_uid,
    get_real_username,
    makedirs,
    run_external,
    shell_split,
    sudo_mode)
from tests import common
from tests.common import also_with_sudo


class GeneralTestCase(common.BleachbitTestCase):
    """Test case for module General"""

    def test_boolstr_to_bool(self):
        """Test case for method boolstr_to_bool"""
        tests = (('True', True),
                 ('true', True),
                 ('False', False),
                 ('false', False))

        for test in tests:
            self.assertEqual(boolstr_to_bool(test[0]), test[1])

    def test_get_executable(self):
        """Test for get_executable()"""
        exe = get_executable()
        self.assertIsInstance(exe, str)
        self.assertGreater(len(exe), 0)
        self.assertEqual(exe, exe.strip())
        self.assertTrue(exe_exists(exe))
        if sys.executable:
            self.assertEqual(exe, sys.executable)

    @also_with_sudo
    def test_get_real_uid(self):
        """Test for get_real_uid()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, get_real_uid)
            return

        # Basic functionality test
        uid = get_real_uid()
        self.assertIsInstance(uid, int)
        self.assertTrue(0 <= uid <= 65535)

        # Multiple calls should return same value
        uid2 = get_real_uid()
        self.assertEqual(uid, uid2)

        # Test relationship with sudo_mode()
        if sudo_mode():
            self.assertGreater(uid, 0)
            self.assertNotEqual(uid, os.geteuid())
        else:
            self.assertEqual(uid, os.getuid())

        # Test that UID is exists in passwd
        # Import pwd here because it would fail on Windows.
        import pwd  # pylint: disable=import-outside-toplevel
        try:
            pwd_entry = pwd.getpwuid(uid)
            self.assertIsInstance(pwd_entry.pw_name, str)
            self.assertGreater(len(pwd_entry.pw_name), 0)
        except KeyError:
            # UID might not be in passwd database in some test environments
            pass

        # Test environment variable consistency
        sudo_uid_env = os.getenv('SUDO_UID')
        if sudo_uid_env:
            self.assertEqual(uid, int(sudo_uid_env))

        # Test with empty LOGNAME (if not in sudo mode)
        original_logname = os.getenv('LOGNAME')
        if not sudo_mode():
            try:
                if 'LOGNAME' in os.environ:
                    del os.environ['LOGNAME']
                uid_no_logname = get_real_uid()
                self.assertIsInstance(uid_no_logname, int)
                self.assertTrue(0 <= uid_no_logname <= 65535)
            finally:
                # Restore original environment
                if original_logname is not None:
                    os.environ['LOGNAME'] = original_logname
                elif 'LOGNAME' in os.environ:
                    del os.environ['LOGNAME']

        # Debug logging for troubleshooting
        logger.debug("os.getenv('LOGNAME') = %s", os.getenv('LOGNAME'))
        logger.debug("os.getenv('SUDO_UID') = %s", os.getenv('SUDO_UID'))
        logger.debug('os.geteuid() = %d', os.geteuid())
        logger.debug('os.getuid() = %d', os.getuid())
        logger.debug('get_real_uid() = %d', uid)
        logger.debug('sudo_mode() = %s', sudo_mode())

        try:
            logger.debug('os.getlogin() = %s', os.getlogin())
        except:
            logger.exception('os.getlogin() raised exception')

        # Test that function doesn't modify global state
        uid_after = get_real_uid()
        self.assertEqual(uid, uid_after)

    def test_get_real_uid_numeric_login_without_passwd_entry(self):
        """Docker containers may advertise UID as username without /etc/passwd."""
        if 'posix' != os.name:
            self.skipTest('POSIX-only behavior')

        # Ensure the code path executes past the SUDO_UID shortcut.
        env_overrides = {'SUDO_UID': ''}
        with mock.patch.dict(os.environ, env_overrides, clear=False):
            with mock.patch('os.getlogin', return_value='1000'):
                with mock.patch('pwd.getpwnam', side_effect=KeyError):
                    uid = get_real_uid()
        self.assertEqual(uid, 1000)

    @also_with_sudo
    def test_get_real_username(self):
        """Test for get_real_username()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, get_real_username)
            return
        username = get_real_username()
        self.assertIsInstance(username, str)
        self.assertGreater(len(username), 0)
        if sudo_mode():
            self.assertNotEqual(username, 'root')

    def test_get_real_username_container_env_fallback(self):
        """Ensure container fallback uses LOGNAME when getpass fails."""
        if 'posix' != os.name:
            self.skipTest('POSIX-only behavior')

        env = {'LOGNAME': 'containeruser'}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch('os.getlogin', side_effect=OSError('no tty')):
                with mock.patch('getpass.getuser', side_effect=KeyError):
                    username = get_real_username()
        self.assertEqual(username, 'containeruser')

    def test_get_real_username_container_uid_fallback(self):
        """Ensure fallback returns UID string when everything else fails."""
        if 'posix' != os.name:
            self.skipTest('POSIX-only behavior')

        env = {}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch('os.getlogin', side_effect=OSError('no tty')):
                with mock.patch('getpass.getuser', side_effect=OSError('no user')):
                    with mock.patch('os.getuid', return_value=4242):
                        username = get_real_username()
        self.assertEqual(username, '4242')

    @also_with_sudo
    def test_makedirs(self):
        """Unit test for makedirs"""

        dir = os.path.join(self.tempdir, 'just', 'a', 'directory', 'adventure')
        # directory does not exist
        makedirs(dir)
        self.assertLExists(dir)
        # directory already exists
        makedirs(dir)
        self.assertLExists(dir)
        # clean up
        shutil.rmtree(os.path.join(self.tempdir, 'just'))

    def test_run_external(self):
        """Unit test for run_external"""
        args = {'nt': ['cmd.exe', '/c', 'dir', r'%windir%\system32', '/s', '/b'],
                'posix': ['find', '/usr/bin']}
        (rc, _stdout, stderr) = run_external(args[os.name])
        self.assertEqual(0, rc)
        self.assertEqual(0, len(stderr))

    @common.skipUnlessWindows
    def test_run_external_quote(self):
        """Unit test for run_external() with quoted command"""
        tests = [
            (('cmd.exe', '/c', 'echo "hello world"'), 'hello world'),
            ((os.path.expandvars('%windir%\\system32\\ping.exe'), '/?'), 'Usage: ping')
        ]
        for args, expected in tests:
            (rc, stdout, stderr) = run_external(args)
            self.assertEqual(0, rc)
            self.assertIn(expected, stdout.strip())
            self.assertEqual(0, len(stderr))

    def test_run_external_does_not_exist(self):
        """Unit test for run_external() with non-existent command"""
        self.assertRaises(OSError, run_external, ['cmddoesnotexist'])
        args = {'nt': ['cmd.exe', '/c', 'dir', r'c:\doesnotexist'],
                'posix': ['ls', '/doesnotexist']}
        (rc, _stdout, _stderr) = run_external(args[os.name])
        self.assertNotEqual(0, rc)

    def test_run_external_nowait(self):
        """Unit test for run_external() with wait=False"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")

            args = {'nt': ['cmd.exe', '/c', 'dir', r'%windir%\system32', '/s', '/b'],
                    'posix': ['find', '/usr/bin']}
            (rc, stdout, stderr) = run_external(args[os.name], wait=False)
            self.assertEqual(0, rc)
            self.assertEqual(0, len(stdout))
            self.assertEqual(0, len(stderr))

    def test_run_external_command_completion(self):
        """Test that run_external() commands complete successfully"""
        with warnings.catch_warnings(record=True) as w:
            # Any warning is an error.
            warnings.simplefilter("error")
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = os.path.join(temp_dir, 'test_file.txt')

                if os.name == 'posix':
                    cmd = ['touch', test_file]
                    expected_stdout = ''
                else:
                    cmd = ['cmd.exe', '/c', 'copy', 'nul', test_file]
                    expected_stdout = '1 file(s) copied.'

                # Wait for the command to complete.
                (rc, stdout, stderr) = run_external(cmd, timeout=5)
                self.assertEqual(0, rc, stderr)
                self.assertEqual('', stderr)
                self.assertEqual(expected_stdout, stdout.strip())
                self.assertExists(test_file)

                os.unlink(test_file)
                self.assertNotExists(test_file)

                # Test with wait=False
                (rc, stdout, stderr) = run_external(cmd, wait=False, timeout=5)

                self.assertEqual(0, rc)
                self.assertEqual('', stdout)
                self.assertEqual('', stderr)
                # Poll for file creation. Touch normally completes in milliseconds,
                # so one second is plenty.
                for _ in range(100):
                    if os.path.exists(test_file):
                        break
                    time.sleep(0.01)
                self.assertExists(test_file)

    def test_run_external_with_timeout_failure(self):
        """Test run_external() with timeout value that is too short"""
        if os.name == 'posix':
            args = ['sleep', '5']
        else:
            args = ['ping', '-n', '10', '127.0.0.1']
        with self.assertRaises(subprocess.TimeoutExpired):
            run_external(args, timeout=1)

    def test_run_external_stdout(self):
        """Test that run_external properly captures stdout"""
        if os.name == 'posix':
            args = ['echo', 'test output']
        else:
            args = ['cmd.exe', '/c', 'echo test output']
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(0, rc)
        self.assertIn('test output', stdout)
        self.assertEqual('', stderr)

    def test_run_external_stderr(self):
        """Test that run_external properly captures stderr"""
        if os.name == 'posix':
            args = ['sh', '-c', 'echo "error message" >&2']
        else:
            args = ['cmd.exe', '/c', 'echo error message 1>&2']
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(0, rc)
        self.assertEqual('', stdout)
        self.assertIn('error message', stderr)

    def test_run_external_return_codes(self):
        """Test that run_external() properly returns non-zero exit codes"""
        if os.name == 'posix':
            args = ['false']
        else:
            args = ['cmd.exe', '/c', 'exit 1']
        (rc, _, _) = run_external(args)
        self.assertEqual(1, rc)

    @common.skipIfWindows
    def test_run_external_clean_env(self):
        """Unit test for clean_env parameter to run_external()"""

        def run(args, clean_env):
            (rc, stdout, _stderr) = run_external(args, clean_env=clean_env)
            self.assertEqual(rc, 0)
            return stdout.rstrip('\n')

        # clean_env should set language to C
        run(['sh', '-c', '[ "x$LANG" = "xC" ]'], clean_env=True)
        run(['sh', '-c', '[ "x$LC_ALL" = "xC" ]'], clean_env=True)

        # clean_env parameter should not alter the PATH, and the PATH
        # should not be empty
        path_clean = run(['bash', '-c', 'echo $PATH'], clean_env=True)
        if os.getenv('PATH'):
            self.assertEqual(common.get_env('PATH'), path_clean)
        self.assertGreater(len(path_clean), 10)

        path_unclean = run(['bash', '-c', 'echo $PATH'], clean_env=False)
        self.assertEqual(path_clean, path_unclean)

        # With parent environment set to English and parameter clean_env=False,
        # expect English

        old_environ = copy.deepcopy(os.environ)

        lc_all_old = common.get_env('LC_ALL')
        lang_old = common.get_env('LANG')
        common.put_env('LC_ALL', 'C')
        (rc, _, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        self.assertIn('No such file', stderr)

        # Set parent environment to Spanish.
        common.put_env('LC_ALL', 'es_MX.UTF-8')
        (rc, _, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        if os.path.exists('/usr/share/locale-langpack/es/LC_MESSAGES/coreutils.mo'):
            # Spanish language pack is installed.
            self.assertIn('No existe el archivo', stderr)

        # Here the parent environment has Spanish, but the child process
        # should use English.
        (rc, _, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=True)
        self.assertEqual(rc, 2)
        self.assertIn('No such file', stderr)

        # Reset environment
        self.assertNotEqual(old_environ, copy.deepcopy(os.environ))
        common.put_env('LC_ALL', lc_all_old)
        common.put_env('LANG', lang_old)
        self.assertEqual(old_environ, copy.deepcopy(os.environ))

    def test_run_external_invalid(self):
        """Unit test for run_external() with invalid arguments"""
        with self.assertRaises(AssertionError):
            run_external(None)
        with self.assertRaises(AssertionError):
            run_external('foo')
        with self.assertRaises(ValueError):
            run_external([None, 'foo'])
        with self.assertRaises(ValueError):
            run_external(['hello', None])
        with self.assertRaises(ValueError):
            run_external([''])
        with self.assertRaises(AssertionError):
            run_external([])

    def test_run_external_timeout(self):
        """Unit test for run_external() with timeout"""
        if os.name == 'posix':
            args = ['sleep', '10']
        if os.name == 'nt':
            args = ['ping', '-n', '10', '127.0.0.1']
        start_time = time.time()
        with self.assertRaises(subprocess.TimeoutExpired):
            run_external(args, timeout=1)
        elapsed_time = time.time() - start_time
        self.assertLess(elapsed_time, 2)

    @common.skipIfWindows
    def test_dconf(self):
        """Unit test for dconf"""
        if not exists_in_path('dconf'):
            self.skipTest('dconf not found')
        if sudo_mode():
            self.skipTest('dconf not supported in sudo mode')
        # pylint: disable=import-outside-toplevel
        from bleachbit.GtkShim import HAVE_GTK
        if not HAVE_GTK:
            self.skipTest('dconf not supported without GUI')
        args = ['dconf', 'write',
                '/apps/bleachbit/test', 'true']
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(0, rc, stderr)
        self.assertEqual('', stderr)
        self.assertEqual('', stdout)

    def test_shell_split(self):
        """Unit test for shell_split()"""
        tests = [('', []),
                 ('a', ['a']),
                 ('a b', ['a', 'b'])
                 ]
        if os.name == 'nt':
            tests.append(('"a b"', ['a b']))
            tests.append(('"a b" c', ['a b', 'c']))
            tests.append(("echo 'a b'", ['echo', "'a b'"]))
            tests.append(('echo a\\ b', ['echo', 'a\\', 'b']))
        elif os.name == 'posix':
            tests.append(("echo 'a b'", ['echo', 'a b']))
            tests.append(("echo 'a b' c", ['echo', 'a b', 'c']))
            tests.append(('echo a\\ b', ['echo', 'a b']))
        for test in tests:
            self.assertEqual(test[1], shell_split(test[0]))

    @common.skipIfWindows
    @also_with_sudo
    def test_sudo_mode(self):
        """Unit test for sudo_mode"""
        self.assertIsInstance(sudo_mode(), bool)
