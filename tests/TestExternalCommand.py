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

import unittest.mock as mock
import os
import sys
import unittest
import time
import types
#import psutil
if 'win32' == sys.platform:
    import winreg
    import win32gui
    from windows.setup_py2exe import SHRED_REGEX_KEY

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib, GObject
    from bleachbit.GUI import Bleachbit
    HAVE_GTK = True
except ImportError:
    HAVE_GTK = False

import bleachbit
from bleachbit import _
from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.Options import options, Options
from bleachbit import Cleaner, CleanerML
from bleachbit.Cleaner import backends
from tests import common

bleachbit.online_update_notification_enabled = False


class ExternalCommandTestCase(common.BleachbitTestCase):
    """Test case for application level functions"""

    @classmethod
    def setUpClass(cls):
        cls.old_language = common.get_env('LANGUAGE')
        common.put_env('LANGUAGE', 'en')
        super(ExternalCommandTestCase, ExternalCommandTestCase).setUpClass()
        options.set('first_start', False)
        options.set('check_online_updates', False)  # avoid pop-up window

    @classmethod
    def tearDownClass(cls):
        super(ExternalCommandTestCase, ExternalCommandTestCase).tearDownClass()
        common.put_env('LANGUAGE', cls.old_language)

    def _context_helper(self, fn_prefix):
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
        shred_command_key = '{}\\command'.format(SHRED_REGEX_KEY)
        shred_command_string = common.get_winregistry_value(
            winreg.HKEY_CLASSES_ROOT,  shred_command_key)

        if shred_command_string is None:
            # Use main .py file when the application is not installed and there is no .exe file
            # and corresponding registry entry.
            shred_command_string = r'{} bleachbit.py --gui --no-uac --shred --exit "{}"'.format(sys.executable,
                                                                                                file_to_shred)
            set_curdir_to_bleachbit()
        else:
            self.assertTrue('"%1"' in shred_command_string)
            shred_command_string = shred_command_string.replace(
                '"%1"', file_to_shred)

        delete_confirmation_saved_state = options.get('delete_confirmation')
        options.set('delete_confirmation', False)
        os.system(shred_command_string)
        options.set('delete_confirmation', delete_confirmation_saved_state)

        self.assertNotExists(file_to_shred)

        opened_windows_titles = common.get_opened_windows_titles()
        # Assert that the Bleachbit window has been closed after the context menu operation had finished.
        self.assertFalse(
            any(['BleachBit' == window_title for window_title in opened_windows_titles]))

    @common.skipUnlessWindows
    def test_windows_explorer_context_menu_command(self):
        for fn_prefix in ('file_to_shred_with_context_menu_command', 'embedded space'):
            self._context_helper(fn_prefix)
