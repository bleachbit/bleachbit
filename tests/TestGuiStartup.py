# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module GuiStartup
"""

import sys
import unittest
from unittest import mock

from bleachbit import GuiStartup
from bleachbit.GuiStartup import _is_version_upgrade


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

    def get_old_version(self):
        """Return old version to check for upgrades."""
        return self._old_version


class GuiStartupTestCase(unittest.TestCase):
    """Tests for GuiStartup helper logic."""

    def test_is_version_upgrade(self):
        """Test version comparison logic."""
        # (old_version, target_version, expected_result)
        cases = [
            # Upgrades that should be detected
            ("5.0.0", "5.1.0", True),
            ("5.0.2", "5.1.0", True),
            ("4.9.9", "5.0.0", True),
            ("5.0", "5.1.0", True),
            # Not upgrades (same or newer version)
            ("5.1.0", "5.1.0", False),
            ("5.2.0", "5.1.0", False),
            ("6.0.0", "5.1.0", False),
            # Invalid inputs should return False
            (None, "5.1.0", False),
            ("", "5.1.0", False),
            ("invalid", "5.1.0", False),
            ("5.0.0", None, False),
            ("", None, False),
        ]
        for old, target, expected in cases:
            with self.subTest(old=old, target=target):
                self.assertEqual(_is_version_upgrade(old, target), expected)

    def test_first_start_message_clears_flag(self):
        """Ensure first-start hint is emitted and flag gets cleared."""
        stub_options = StubOptions()

        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False):
            messages = GuiStartup.get_startup_messages(auto_exit=False)

        self.assertTrue(
            any('Access the application menu' in msg for msg, _ in messages))
        self.assertFalse(stub_options.get('first_start'))

    def test_upgrade_message_shown_for_pre_510(self):
        """Users upgrading from <5.1.0 should see expert-mode reminder."""
        stub_options = StubOptions(first_start=False, old_version="5.0.2")

        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False):
            messages = GuiStartup.get_startup_messages(auto_exit=False)

        self.assertTrue(any('require expert mode' in msg
                            for msg, _ in messages))

    def test_missing_requests(self):
        """Missing requests should be reported but not crash GuiStartup."""
        saved = {}
        for mod in list(sys.modules.keys()):
            if any(mod.startswith(p) for p in ['requests', 'urllib3',
                                                'bleachbit.Network',
                                                'bleachbit.Update',
                                                'bleachbit.GuiStartup']):
                saved[mod] = sys.modules.pop(mod)

        try:
            with mock.patch.dict('sys.modules', {'requests': None}):
                import bleachbit.GuiStartup as GuiStartup
                missing = GuiStartup._get_missing_dependencies()
                self.assertIn('requests', missing)
        finally:
            for mod, mod_obj in saved.items():
                sys.modules[mod] = mod_obj
