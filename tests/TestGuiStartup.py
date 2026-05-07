# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module GuiStartup
"""

import os
import stat
import sys
import unittest
import tempfile
from unittest import mock

from bleachbit import IS_WINDOWS
import bleachbit
from bleachbit import GuiStartup
from bleachbit.Cleaner import register_cleaners
from bleachbit.GuiStartup import _has_selected_warning_option, _get_posix_permission_issues, _get_windows_permission_issues
from bleachbit.Options import options
from tests import common


class StubOptions:
    """Minimal stand-in for bleachbit.Options for testing."""

    def __init__(self, *, first_start=True, shred=False, old_version=None):
        """Seed stub with values."""
        self.values = {'first_start': first_start, 'shred': shred}
        self._old_version = old_version

    def get(self, key):
        """Return stored option value."""
        return self.values.get(key)

    def set(self, key, value):
        """Set a option value."""
        self.values[key] = value


class GuiStartupTestCase(common.BleachbitTestCase):
    """Tests for GuiStartup helper logic."""

    def test_first_start_message_clears_flag(self):
        """Ensure first-start hint is emitted and flag gets cleared."""
        stub_options = StubOptions()

        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False):
            messages = GuiStartup.get_startup_messages(auto_exit=False)

        self.assertTrue(
            any('Access the application menu' in msg for msg, _ in messages))
        self.assertFalse(stub_options.get('first_start'))

    def test_has_selected_warning_option(self):
        """Test the function _has_selected_warning_option()"""
        # Register cleaners to populate backends
        list(register_cleaners())
        # Each test case starts with fresh options, so with
        # nothing selected, it should return False.
        self.assertFalse(_has_selected_warning_option())
        # Enable a safe option.
        options.set_tree('system', 'tmp', True)
        self.assertFalse(_has_selected_warning_option())
        # Enable an option with a warning.
        options.set_tree('system', 'empty_space', True)
        self.assertTrue(_has_selected_warning_option())
        # Clean up
        options.set_tree('system', 'tmp', False)
        options.set_tree('system', 'empty_space', False)

    def test_missing_requests(self):
        """Missing requests should be reported but not crash GuiStartup."""
        with common.mock_missing_package(
                'requests',
                clear_prefixes=('bleachbit.Network', 'bleachbit.Update', 'bleachbit.GuiStartup')):
            import bleachbit.GuiStartup as GuiStartup
            missing = GuiStartup._get_missing_dependencies()
            self.assertIn('requests', missing)

    @common.skipIfWindows
    def test_is_config_writable(self):
        """Test read-only configuration file"""
        o = bleachbit.Options.Options()
        o.close()
        os.chmod(bleachbit.options_file, stat.S_IRUSR |
                 stat.S_IRGRP | stat.S_IROTH)
        self.assertExists(bleachbit.options_file)
        issues = GuiStartup._get_config_permission_issues()
        os.unlink(bleachbit.options_file)
        self.assertNotExists(bleachbit.options_file)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('Write error' in issue for issue in issues),
                        f"Expected 'Write error' in issues: {issues}")

    def test_config_permission_issues_normal(self):
        """Test that a normal writable config file reports no issues."""
        o = bleachbit.Options.Options()
        o.close()
        self.assertExists(bleachbit.options_file)
        issues = GuiStartup._get_config_permission_issues()
        os.unlink(bleachbit.options_file)
        self.assertNotExists(bleachbit.options_file)
        self.assertFalse(issues)

    def test_permission_issues_normal_file(self):
        """Test  ownership check on a normal file owned by the user."""
        path = self.write_file('check_me')
        fstat = os.stat(path)
        if IS_WINDOWS:
            has_error, lines = _get_windows_permission_issues(path)
        else:
            has_error, lines = _get_posix_permission_issues(fstat, path)
        self.assertFalse(has_error)
        self.assertTrue(any('File owner:' in line for line in lines))
        self.assertTrue(any('Current user:' in line for line in lines))

    @common.skipUnlessWindows
    def test_get_windows_user_info(self):
        """Test _get_windows_user_info function."""
        current_sid, current_name, group_sids = GuiStartup._get_windows_user_info()
        self.assertIsNotNone(current_sid)
        self.assertIsNotNone(current_name)
        self.assertIsNotNone(group_sids)
        self.assertIsInstance(current_sid, str)
        self.assertIsInstance(current_name, str)
        self.assertIsInstance(group_sids, set)
        self.assertEqual(current_name, os.environ.get('USERNAME', ''))

    @common.skipUnlessWindows
    def test_get_windows_file_owner(self):
        """Test _get_windows_file_owner function."""
        owner_sid_str, owner_name = GuiStartup._get_windows_file_owner(
            self.tempdir)
        self.assertIsNotNone(owner_sid_str)
        self.assertIsNotNone(owner_name)
        self.assertIsInstance(owner_sid_str, str)
        self.assertIsInstance(owner_name, str)
        if 'APPVEYOR' in os.environ:
            expected_owner = 'Administrators'
        else:
            expected_owner = os.environ.get('USERNAME', '')
        self.assertEqual(owner_name, expected_owner)
