# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module GuiCookie
"""

import json
import os
import types
import unittest
from unittest import mock

from tests import common

from bleachbit import General, IS_WINDOWS
from bleachbit.GtkShim import is_gtk_available

HAVE_GTK = is_gtk_available()
if HAVE_GTK:
    from bleachbit.GuiCookie import CookieManagerPane


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class GuiCookieTestCase(common.BleachbitTestCase):
    """Test case for CookieManagerPane"""

    def _fake_pane(self, keep_list_path, domains):
        """A minimal stand-in for CookieManagerPane, avoiding a real Gtk widget."""
        return types.SimpleNamespace(
            keep_list_path=keep_list_path,
            _iter_selected_domains=lambda: iter(domains))

    def test_save_changes_refuses_symlink(self):
        """save_changes() must not write the keep list through a symlink"""
        filename = self.write_file(
            'cookie_keep_list_target.json', text='["keepme.example"]')
        pane = self._fake_pane(filename, ['evil.example'])
        with mock.patch('bleachbit.FileUtilities.os.path.islink',
                        side_effect=lambda p: p == filename):
            # pylint: disable-next=possibly-used-before-assignment
            result = CookieManagerPane.save_changes(pane)
        self.assertFalse(result)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['keepme.example'])

    @common.also_with_sudo
    def test_save_changes_still_works(self):
        """save_changes() still writes the sorted keep list normally"""
        filename = os.path.join(self.tempdir, 'cookie_keep_list.json')
        pane = self._fake_pane(filename, ['b.example', 'a.example'])
        result = CookieManagerPane.save_changes(pane)
        self.assertTrue(result)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['a.example', 'b.example'])
        self.assertEqual(pane.saved_domains, {'a.example', 'b.example'})
        if not IS_WINDOWS:
            self.assertEqual(os.stat(filename).st_uid,
                             General.get_real_uid())

    @common.skipIfWindows
    def test_save_changes_sudo_chown(self):
        """Creating the keep list in sudo mode chowns it to the user."""
        filename = os.path.join(self.mkdtemp(), 'cookie_keep_list.json')
        pane = self._fake_pane(filename, ['a.example'])
        with mock.patch('bleachbit.General.sudo_mode', return_value=True), \
                mock.patch('bleachbit.General.chownself') as mock_chown:
            self.assertTrue(CookieManagerPane.save_changes(pane))
            mock_chown.assert_called_once_with(filename)
            mock_chown.reset_mock()
            # Overwriting an existing file should not chown again
            self.assertTrue(CookieManagerPane.save_changes(pane))
            mock_chown.assert_not_called()
