# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for the context menu command
"""


import os
import sys
import subprocess
import time
from unittest import mock

import psutil

import bleachbit
from bleachbit.GtkShim import HAVE_GTK
from bleachbit.Options import options
from tests import common

if HAVE_GTK:
    from bleachbit.GuiApplication import Bleachbit


START_TIMEOUT_SECONDS = 20
MAX_PATH_DISPLAY = 200


def is_bleachbit_running_process(process_name, cmdline):
    """Return whether process_name/cmdline represent a running BleachBit GUI/context process."""
    assert isinstance(process_name, str)
    assert isinstance(cmdline, list)
    name_lower = (process_name or '').lower()
    normalized_cmdline = [str(arg).lower() for arg in (cmdline or [])]
    cmdline_str = ' '.join(normalized_cmdline)

    image_is_python = name_lower.startswith('python')
    # With subprocess shell=True, process image is cmd.exe instead of python.
    image_is_cmd = name_lower in ('cmd.exe', 'cmd')
    launches_python = 'python.exe' in cmdline_str or 'python3' in cmdline_str
    if not (image_is_python or (image_is_cmd and launches_python)):
        return False

    has_bleachbit_entrypoint = any(
        'bleachbit.py' in arg
        for arg in normalized_cmdline
    )
    has_context_arg = any(
        '--context-menu' in arg or '--gui' in arg for arg in normalized_cmdline)
    return has_bleachbit_entrypoint and has_context_arg


def wait_for_process_tree_windows(process, timeout=60, poll_interval=0.1):
    """Wait for a process and its grandchildren to complete on Windows.

    This function handles the case where a child process spawns a grandchild
    and then exits. It monitors the process tree to ensure all descendants
    have completed before returning.

    Args:
        process: subprocess.Popen object for the child process
        timeout: Maximum time to wait in seconds (default: 60)
        poll_interval: How often to check process status in seconds (default: 0.1)

    Returns:
        The return code of the child process

    Raises:
        subprocess.TimeoutExpired: If the process tree doesn't complete within timeout
    """

    start_time = time.time()
    child_pid = process.pid
    grandchild_pids = set()
    child_exited = False

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            process.kill()
            process.wait()
            raise subprocess.TimeoutExpired(process.args, timeout)

        # Add absolute safety timeout to prevent hanging
        if elapsed > timeout + 30:  # Extra 30 seconds safety margin
            # Force kill everything and exit
            try:
                process.kill()
                process.wait()
                # Try to kill any remaining grandchildren
                for pid in grandchild_pids:
                    try:
                        if psutil.pid_exists(pid):
                            proc = psutil.Process(pid)
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except:
                pass
            raise subprocess.TimeoutExpired(process.args, elapsed)

        if not child_exited:
            child_status = process.poll()
            if child_status is not None:
                child_exited = True
            else:
                try:
                    parent_process = psutil.Process(child_pid)
                    current_children = {
                        child.pid for child in parent_process.children(recursive=True)}
                    grandchild_pids.update(current_children)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        if child_exited:
            if not grandchild_pids:
                return process.returncode

            still_running = set()
            for pid in grandchild_pids:
                try:
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                            still_running.add(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            grandchild_pids = still_running
            if not grandchild_pids:
                return process.returncode

        time.sleep(poll_interval)


class ApplicationRunningTracker:
    """Tracks processes and window titles during application run detection"""

    def __init__(self, check_window_title=False, timeout=0):
        self.check_window_title = check_window_title
        self.timeout = timeout
        self.seen_processes = set()
        self.seen_window_titles = set()
        self.elapsed_time = None
        # This search is more broader than criteria for whether application
        # is running, in case the other criteria is too strict.
        self.candidate_search = ['bleach', 'python']

    def _check_application_state(self):
        """Check current application state without timeout logic.

        Returns tuple (is_running, window_open) where:
        - is_running: True if bleachbit process found
        - window_open: True if bleachbit window found (Windows only)
        """
        is_process_running = False
        window_open = False

        for process in psutil.process_iter(['name', 'cmdline']):
            try:
                name = process.info['name'] or ''
                cmdline = process.info['cmdline'] or []
                name_and_cmdline = f"{name}: {' '.join(cmdline)[:MAX_PATH_DISPLAY]}"

                # Track all interesting processes
                for candidate in self.candidate_search:
                    if candidate in name_and_cmdline.lower():
                        self.seen_processes.add(name_and_cmdline)

                if is_bleachbit_running_process(name, cmdline):
                    is_process_running = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Check window titles on Windows
        if os.name == 'nt' and self.check_window_title:
            opened_windows_titles = common.get_opened_windows_titles()
            window_open = any(
                'BleachBit' == window_title for window_title in opened_windows_titles)

            for window_title in opened_windows_titles:
                for candidate in self.candidate_search:
                    if candidate in window_title.lower():
                        self.seen_window_titles.add(window_title)
                        break

        return is_process_running, window_open

    def _is_running_based_on_checks(self, is_process_running, window_open):
        """Determine if application is running based on check_window_title setting."""
        if self.check_window_title and os.name == 'nt':
            return is_process_running and window_open
        return is_process_running or window_open

    def is_application_running(self, expect_running=True):
        """Check if the application is running with optional timeout polling.

        Args:
            expect_running: If True, poll until timeout waiting for app to start.
                           If False, return immediately.

        Returns:
            bool: True if application is running, False otherwise
        """
        if expect_running and self.timeout > 0:
            start_time = time.time()
            while True:
                is_process_running, window_open = self._check_application_state()
                if self._is_running_based_on_checks(is_process_running, window_open):
                    return True
                self.elapsed_time = time.time() - start_time
                if self.elapsed_time >= self.timeout:
                    return False
                # Add safety check to prevent infinite loops
                if self.elapsed_time > self.timeout + 5:  # Extra safety margin
                    return False
                time.sleep(0.1)
        else:
            is_process_running, window_open = self._check_application_state()
            return self._is_running_based_on_checks(is_process_running, window_open)

    def not_running_msg(self):
        """Returns a string with diagnostic information

        Returns
        - count of window titles
        - list of potential matches for window titles (including those seen earlier)
        - count of processes running
        - list of potential matches for processes (including those seen earlier)
        - check_window_title
        - timeout limit
        - time elapsed waiting
        """
        window_title_str = ""
        if os.name == 'nt' and self.check_window_title:
            opened_window_titles = common.get_opened_windows_titles()
            window_title_count = len(opened_window_titles)
            interesting_window_titles = []

            # Include currently seen interesting titles
            for window_title in opened_window_titles:
                for candidate in self.candidate_search:
                    if candidate in window_title.lower():
                        interesting_window_titles.append(window_title)
                        break

            # Also include titles we saw earlier but don't see now
            missing_titles = self.seen_window_titles - \
                set(opened_window_titles)
            if missing_titles:
                interesting_window_titles.extend(
                    [f"[PREVIOUSLY SEEN] {title}" for title in missing_titles])

            window_title_str = f"currently {window_title_count} window titles, interesting:\n" + \
                "\n".join(
                    f"  - {title}" for title in interesting_window_titles)

        interesting_processes = []
        process_count = 0
        current_processes = set()

        for process in psutil.process_iter(['name', 'cmdline']):
            process_count += 1
            name = process.info['name'] or ''
            cmdline = process.info['cmdline'] or []
            name_and_cmdline = f"{name}: {' '.join(cmdline)[:MAX_PATH_DISPLAY]}"
            current_processes.add(name_and_cmdline)

            for candidate in self.candidate_search:
                if candidate in name_and_cmdline.lower():
                    interesting_processes.append(name_and_cmdline)
                    break

        # Also include processes we saw earlier but don't see now
        missing_processes = self.seen_processes - current_processes
        if missing_processes:
            interesting_processes.extend(
                [f"[PREVIOUSLY SEEN] {proc}" for proc in missing_processes])

        process_str = f"currently {process_count} processes, interesting:\n" + \
            "\n".join(f"  - {proc}" for proc in interesting_processes)

        return f"{window_title_str}\n{process_str}" \
            f"\ncheck_window_title: {self.check_window_title}" \
            f"\ntimeout: {self.timeout}" \
            f"\ntime elapsed: {round(self.elapsed_time, 2)}"


class ExternalCommandTestCase(common.BleachbitTestCase):
    """Test case for the context menu command"""

    @classmethod
    def setUpClass(cls):
        """Set up the test case"""
        cls.old_language = common.get_env('LANGUAGE')
        common.put_env('LANGUAGE', 'en')
        super(ExternalCommandTestCase, ExternalCommandTestCase).setUpClass()
        cls.environment_changed = False
        # This should not be needed because of using CLI arg --no-delete-confirmation.
        options.set('delete_confirmation', False)
        options.commit()
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            # Set environment variable for child process.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', cls.tempdir)
            cls.environment_changed = True

    @classmethod
    def tearDownClass(cls):
        """Tear down the test case"""
        common.put_env('LANGUAGE', cls.old_language)
        if cls.environment_changed:
            # We don't want to affect other tests, executed after this one.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', None)
        super(ExternalCommandTestCase, ExternalCommandTestCase).tearDownClass()

    def assertRunning(self, expect_running=True, check_window_title=True, timeout=START_TIMEOUT_SECONDS):
        """Assert whether BleachBit GUI processes are running or not

        Args:
            expect_running: If True (default), assert that processes ARE running.
                           If False, assert that processes are NOT running.
            check_window_title: Whether to also check for window title (Windows only)
            timeout: Maximum time to wait for process to be running (only used when expect_running=True)
        """
        tracker = ApplicationRunningTracker(
            check_window_title=check_window_title,
            timeout=timeout if expect_running else 0
        )
        is_running = tracker.is_application_running(
            expect_running=expect_running)

        if expect_running and not is_running:
            self.fail(
                f"Expected BleachBit GUI process to be running, but none found\n{tracker.not_running_msg()}")
        elif not expect_running and is_running:
            self.fail("BleachBit GUI process is still running")

    def _context_helper(self, fn_prefix, allow_opened_window=False):
        """Unit test for 'Shred with BleachBit' Windows Explorer context menu command

        Called from
        - test_windows_explorer_context_menu_natural
        - test_context_menu_command_while_the_app_is_running

        This test is more likely an integration test as it imitates user behavior.
        It could be interpreted as TestCLI->test_gui_no-uac_shred_exit
        but it is more explicit to have it here as a separate case.
        It covers a single case where one file is shred without delete confirmation dialog.
        """

        file_to_shred = self.mkstemp(prefix=fn_prefix)
        self.assertExists(file_to_shred)
        if not allow_opened_window:
            self.assertRunning(False)
        shred_command_string = self._get_shred_command_string(file_to_shred)
        self._run_shred_command(shred_command_string,
                                cwd=bleachbit.bleachbit_exe_path)
        self.assertNotExists(file_to_shred)

        if not allow_opened_window:
            self.assertRunning(False)

    def _get_shred_command_string(self, file_to_shred):
        """Build the command string like the context menu command"""
        shred_command_string = (
            # Disable confirmation for automated tests.
            f'{sys.executable} bleachbit.py --no-delete-confirmation --no-first-start '
            f'--context-menu "{file_to_shred}"'  # The pathname must be last.
        )
        return shred_command_string

    def _run_shred_command(self, shred_command_string, cwd=None):
        """Run the shred command

        In case of privilege escalation, the child process
        will launch an elevated process, so the child will exit.
        We must wait for the grandchild to finish.
        """
        process = subprocess.Popen(shred_command_string,
                                   shell=True, cwd=cwd)
        try:
            # It may close too quickly to detect the window title.
            self.assertRunning(check_window_title=False)
            returncode = wait_for_process_tree_windows(process, timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            self.fail("Shred command timed out")
        finally:
            # Ensure process is cleaned up to avoid ResourceWarning
            if process.poll() is None:
                process.kill()
                process.wait()
        self.assertEqual(
            returncode, 0, f"Shred command failed with return code {returncode}")

    def test_windows_explorer_context_menu_natural(self):
        """Test shredding a file with the context menu command in a natural way"""
        # First, test the simple case of a pathname without embedded spaces.
        # Then, test a pathname with a space.
        self.assertRunning(False)
        if not HAVE_GTK:
            self.skipTest('GTK is not available')
        for fn_prefix in ('shred_target_no_spaces', 'shred target with spaces'):
            self._context_helper(fn_prefix)
        self.assertRunning(False)

    @common.skipUnlessWindows
    def test_windows_explorer_context_menu_privilege_escalation(self):
        """Test shredding a file with the context menu command with privilege escalation"""
        if bleachbit.Windows.path_on_network(bleachbit.bleachbit_exe_path):
            self.skipTest('Escalation is not attempted on network paths.')
        if not HAVE_GTK:
            self.skipTest('GTK is not available')
        self.assertRunning(False)
        for fn_prefix in ('shred_target_no_spaces', 'shred target with spaces'):
            self._test_as_non_admin_with_context_menu_path(fn_prefix)
        self.assertRunning(False)

    @common.skipUnlessWindows
    def test_context_menu_command_while_the_app_is_running(self):
        """Test the context menu command while the application is running"""
        self.assertRunning(False)
        if not HAVE_GTK:
            self.skipTest('GTK is not available')
        # Start an idle process that will keep running.
        # The --no-uac flag prevents launching grandchild process.
        # The --no-load-cleaners makes it faster.
        args = [sys.executable, 'bleachbit.py',
                '--gui', '--no-load-cleaners', '--no-check-online-updates', '--no-uac']
        p = subprocess.Popen(args, shell=False)
        try:
            # Let the first process start up before launching the second process.
            self.assertRunning(check_window_title=True)
            try:
                # Run a second process that will shred a file.
                self._context_helper('while_app_is_running',
                                     allow_opened_window=True)
            finally:
                self.assertRunning()
        finally:
            # Ensure the process is always killed, even if assertions fail
            if p.poll() is None:  # Check if process is still running
                p.kill()
                p.wait()
        self.assertRunning(False)

    def _test_as_non_admin_with_context_menu_path(self, fn_prefix):
        """
        This tests covers elevate_privileges in the case where we pretend that we are not admin.
        """
        self.assertTrue(os.name == 'nt')
        file_to_shred = self.mkstemp(prefix=fn_prefix)
        self.assertExists(file_to_shred)

        original = bleachbit.Windows.shell.ShellExecuteEx

        def shell_execute_synchronous(lpVerb='', lpFile='', lpParameters='', nShow=''):
            """
            We need a synchronous call the ShellExecuteEx, so we can assert after it finishes.
            """
            from win32com.shell import shell, shellcon
            import win32event
            import win32file
            bleachbit.Windows.shell.ShellExecuteEx = original
            rc = shell.ShellExecuteEx(lpVerb=lpVerb,
                                      lpFile=lpFile,
                                      lpParameters=lpParameters,
                                      nShow=nShow,
                                      fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                      )
            hproc = rc['hProcess']
            win32event.WaitForSingleObject(hproc, win32event.INFINITE)
            # Close the process handle to prevent ResourceWarning
            win32file.CloseHandle(hproc)
            return rc

        # We redirect the ShellExecuteEx call like this because if we do it in a mock we enter recursion
        # because we call ShellExecuteEx in shell_execute_synchronous
        bleachbit.Windows.shell.ShellExecuteEx = shell_execute_synchronous
        with mock.patch('bleachbit.Windows.shell.IsUserAnAdmin', return_value=False):
            # Do not actually exit the process during the test.
            with mock.patch('bleachbit.GuiApplication.sys.exit'):
                # Mock the command line arguments to be inherited to the child process.
                custom_argv = [
                    'dummy-arg',
                    '--no-delete-confirmation',
                    '--context-menu',
                    file_to_shred,  # The pathname must be last
                ]
                with mock.patch('bleachbit.Windows.sys.argv', custom_argv):
                    Bleachbit(auto_exit=True, shred_paths=[
                              file_to_shred], uac=True)

        self.assertNotExists(file_to_shred)

    def test_is_bleachbit_running_process(self):
        """Test process-matching helper without depending on live processes."""
        # Path as seen on AppVeyor
        py_dir = r'C:\\projects\\bleachbit\\vcpkg_installed\\x86-windows\\tools\\python3\\'
        py_exe = os.path.join(py_dir, 'python.exe')
        tests = (
            # Test runner.
            (False, 'python.exe',
                [
                    py_exe,
                    os.path.join(py_dir, 'coverage.exe'),
                    'run',
                    '--include=bleachbit/*',
                    'tests/TestAll.py',
                ]
             ),
            # D-Bus session bus.
            (False, 'gdbus.exe',
                [os.path.join(py_dir, 'gdbus.exe'), '_win32_run_session_bus']
             ),
            # This is the cleaning process.
            (True, 'cmd.exe',
                [
                    'C:\\Windows\\system32\\cmd.exe',
                    '/c',
                    py_exe,
                    'bleachbit.py',
                    '--no-delete-confirmation',
                    '--no-first-start',
                    '--context-menu'  # followed by a pathname to delete
                ]
             ),
            # This is the cleaning process as seen on AppVeyor with shell=True where arguments are grouped.
            (True, 'cmd.exe',
                [
                    'C:\\Windows\\system32\\cmd.exe',
                    '/c',
                    f'{py_exe} bleachbit.py --no-delete-confirmation --no-first-start --context-menu C:\\Users\\appveyor\\AppData'
                ]
             ),
            # This is the idle process.
            (True, 'python.exe',
                [py_exe, 'bleachbit.py', '--gui', '--no-load-cleaners',
                    '--no-check-online-updates', '--no-uac']
             ),
        )
        for expected, process_name, cmdline in tests:
            self.assertEqual(
                expected,
                is_bleachbit_running_process(process_name, cmdline)
            )

    def test_wait_for_grandchild_process(self):
        """Test that wait_for_process_tree_windows waits for grandchild processes"""
        marker_file = self.mkstemp(prefix='grandchild_marker_')
        os.remove(marker_file)
        self.assertNotExists(marker_file)

        grandchild_script = os.path.join(self.tempdir, 'grandchild.py')
        with open(grandchild_script, 'w', encoding='utf-8') as f:
            f.write(f'''import time
import sys
time.sleep(2)
with open({repr(marker_file)}, "w") as f:
    f.write("grandchild completed")
sys.exit(0)
''')

        child_script = os.path.join(self.tempdir, 'child.py')
        with open(child_script, 'w', encoding='utf-8') as f:
            f.write(f'''import subprocess
import sys
import time
p = subprocess.Popen([sys.executable, {repr(grandchild_script)}])
time.sleep(0.5)
p.wait()
sys.exit(0)
''')

        process = subprocess.Popen([sys.executable, child_script])

        start_time = time.time()
        returncode = wait_for_process_tree_windows(process, timeout=10)
        elapsed = time.time() - start_time

        self.assertEqual(returncode, 0)
        self.assertExists(marker_file)
        self.assertGreater(elapsed, 1.5)
