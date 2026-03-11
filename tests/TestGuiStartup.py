# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from bleachbit import GuiStartup


class GuiStartupTestCase(unittest.TestCase):
    """Tests for GuiStartup helper logic."""

    def test_first_start_message_clears_flag(self):
        """Ensure first-start hint is emitted and flag gets cleared."""
        class DummyOptions:
            def __init__(self):
                self.values = {'first_start': True, 'shred': False}

            def get(self, key):
                return self.values.get(key)

            def set(self, key, value):
                self.values[key] = value

        dummy_options = DummyOptions()

        with mock.patch.object(GuiStartup, 'options', dummy_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False):
            messages = GuiStartup.get_startup_messages(auto_exit=False)

        self.assertTrue(any('Access the application menu' in msg for msg, _ in messages))
        self.assertFalse(dummy_options.get('first_start'))
