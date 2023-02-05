# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Test case for application level functions
"""


import os
import sys
import subprocess
from unittest import mock, SkipTest

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib, GObject
    from bleachbit.GUI import Bleachbit
    HAVE_GTK = True
except ImportError:
    HAVE_GTK = False

import bleachbit
from bleachbit.Options import options
from tests import common


@common.skipUnlessWindows
class ExternalCommandTestCase(common.BleachbitTestCase):
    """Test case for application level functions"""

    @classmethod
    def setUpClass(cls):
        bleachbit.online_update_notification_enabled = False
        cls.old_language = common.get_env('LANGUAGE')
        common.put_env('LANGUAGE', 'en')
        super(ExternalCommandTestCase, ExternalCommandTestCase).setUpClass()
        options.set('first_start', False)
        options.set('check_online_updates', False)  # avoid pop-up window

    @classmethod
    def tearDownClass(cls):
        super(ExternalCommandTestCase, ExternalCommandTestCase).tearDownClass()
        common.put_env('LANGUAGE', cls.old_language)

    def _context_helper(self, fn_prefix, allow_opened_window=False):
        """Unit test for 'Shred with BleachBit' Windows Explorer context menu command"""

        # This test is more likely an integration test as it imitates user behavior.
        # It could be interpreted as TestCLI->test_gui_no-uac_shred_exit
        # but it is more explicit to have it here as a separate case.
        # It covers a single case where one file is shred without delete confirmation dialog.

        def set_curdir_to_bleachbit():
            os.curdir = os.path.split(__file__)[0]
            os.curdir = os.path.split(os.curdir)[0]

        file_to_shred = self.mkstemp(prefix=fn_prefix)
        print('file_to_shred = {}'.format(file_to_shred))
        self.assertExists(file_to_shred)
        set_curdir_to_bleachbit()
        shred_command_string = self._get_shred_command_string(file_to_shred)
        self._run_shred_command(shred_command_string)
        self.assertNotExists(file_to_shred)

        if not allow_opened_window:
            opened_windows_titles = common.get_opened_windows_titles()
            # Assert that the Bleachbit window has been closed after the context menu operation had finished.
            # If any windows is titled BleachBit the test will fail.
            # This could happen with Windows Explorer opened with folder BleachBit for example.
            self.assertFalse(
                any(['BleachBit' == window_title for window_title in opened_windows_titles]))

    def _get_shred_command_string(self, file_to_shred):
        shred_command_string = r'{} bleachbit.py --context-menu "{}"'.format(sys.executable,
                                                                                            file_to_shred)
        return shred_command_string

    def _run_shred_command(self, shred_command_string):
        environment_changed = False
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            # We need to set env var because of the new process that executes the context menu command string
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', self.tempdir)
            environment_changed = True

        options.set('delete_confirmation', False)
        os.system(shred_command_string)

        if environment_changed:
            # We don't want to affect other tests, executed after this one.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', None)

    def test_windows_explorer_context_menu_command(self):
        for fn_prefix in ('file_to_shred_with_context_menu_command', 'embedded space'):
            self._context_helper(fn_prefix)
            self._test_as_non_admin_with_context_menu_path(fn_prefix)

    def test_context_menu_command_while_the_app_is_running(self):
        p = subprocess.Popen([sys.executable, 'bleachbit.py'], shell=False)
        self._context_helper('while_app_is_running', allow_opened_window=True)
        subprocess.Popen.kill(p)

    def _test_as_non_admin_with_context_menu_path(self, fn_prefix):
        """
        This tests covers elevate_privileges in the case where we pretend that we are not admin.
        """
        from bleachbit.Options import options

        file_to_shred = self.mkstemp(prefix=fn_prefix)
        self.assertExists(file_to_shred)

        original = bleachbit.Windows.shell.ShellExecuteEx
        def shell_execute_synchronous(lpVerb='', lpFile='', lpParameters='', nShow=''):
            """
            We need a synchronous call the ShellExecuteEx so we can assert after it finishes.
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

        environment_changed = False
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            # We need to set env var because of the new process that executes the context menu command string
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', self.tempdir)
            environment_changed = True
        options.set('delete_confirmation', False)

        # We redirect the ShellExecuteEx call like this because if we do it in a mock we enter recursion
        # because we call ShellExecuteEx in shell_execute_synchronous
        bleachbit.Windows.shell.ShellExecuteEx = shell_execute_synchronous
        with mock.patch('bleachbit.Windows.shell.IsUserAnAdmin', return_value=False):
            with mock.patch('bleachbit.GUI.sys.exit'):
                with mock.patch('bleachbit.Windows.sys.argv', ['dummy-arg', '--context-menu', file_to_shred]):
                    Bleachbit(auto_exit=True, shred_paths=[file_to_shred], uac=True)

        self.assertNotExists(file_to_shred)

        if environment_changed:
            # We don't want to affect other tests, executed after this one.
            common.put_env('BLEACHBIT_TEST_OPTIONS_DIR', None)