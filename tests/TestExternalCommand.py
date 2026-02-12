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


START_TIMEOUT_SECONDS = 10


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


def is_application_running(require_both=False):
    """Check if the application is running"""
    is_process_running = False
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            name = process.info['name'] or ''
            cmdline = process.info['cmdline'] or []
            if name.lower().startswith('python') and any(arg in ('--context-menu', '--no-load-cleaners') for arg in cmdline):
                is_process_running = True
                continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Second, check using window titles.
    if not os.name == 'nt':
        return is_process_running
    opened_windows_titles = common.get_opened_windows_titles()
    window_open = any(
        ['BleachBit' == window_title for window_title in opened_windows_titles])
    if require_both:
        return is_process_running and window_open
    return is_process_running or window_open


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
        options.set('delete_confirmation', False, commit=True)
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            # Set environment variable for child process.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', cls.tempdir)
            cls.environment_changed = True

    @classmethod
    def tearDownClass(cls):
        """Tear down the test case"""
        super(ExternalCommandTestCase, ExternalCommandTestCase).tearDownClass()
        common.put_env('LANGUAGE', cls.old_language)
        if cls.environment_changed:
            # We don't want to affect other tests, executed after this one.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', None)

    def assertRunning(self, expect_running=True, timeout=START_TIMEOUT_SECONDS):
        """Assert whether BleachBit GUI processes are running or not

        Args:
            expect_running: If True (default), assert that processes ARE running.
                           If False, assert that processes are NOT running.
            timeout: Maximum time to wait for process to be running (only used when expect_running=True)
        """
        if expect_running:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if is_application_running(True):
                    return
                time.sleep(0.1)
            self.fail(
                "Expected BleachBit GUI process to be running, but none found")
        else:
            if is_application_running(True):
                self.fail("BleachBit GUI process is still running")

    def _context_helper(self, fn_prefix, allow_opened_window=False):
        """Unit test for 'Shred with BleachBit' Windows Explorer context menu command"""

        # This test is more likely an integration test as it imitates user behavior.
        # It could be interpreted as TestCLI->test_gui_no-uac_shred_exit
        # but it is more explicit to have it here as a separate case.
        # It covers a single case where one file is shred without delete confirmation dialog.

        file_to_shred = self.mkstemp(prefix=fn_prefix)
        print('file_to_shred = {}'.format(file_to_shred))
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
        self.assertRunning()  # delay until started, within timeout
        try:
            returncode = wait_for_process_tree_windows(process, timeout=60)
        except subprocess.TimeoutExpired:
            self.fail("Shred command timed out")
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
        print(args)
        p = subprocess.Popen(args, shell=False)
        # Let the first process start up before launching the second process.
        time.sleep(START_TIMEOUT_SECONDS)
        self.assertRunning()
        try:
            # Run a second process that will shred a file.
            self._context_helper('while_app_is_running',
                                 allow_opened_window=True)
        finally:
            self.assertRunning()
            # Kill the first process immediately after context menu operation completes
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
            bleachbit.Windows.shell.ShellExecuteEx = original
            rc = shell.ShellExecuteEx(lpVerb=lpVerb,
                                      lpFile=lpFile,
                                      lpParameters=lpParameters,
                                      nShow=nShow,
                                      fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                      )
            hproc = rc['hProcess']
            win32event.WaitForSingleObject(hproc, win32event.INFINITE)
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
