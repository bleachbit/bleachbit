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

from bleachbit.GtkShim import is_gtk_available

from tests import common

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
            result = CookieManagerPane.save_changes(pane)
        self.assertFalse(result)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['keepme.example'])

    def test_save_changes_still_works(self):
        """save_changes() still writes the sorted keep list normally"""
        filename = os.path.join(self.tempdir, 'cookie_keep_list.json')
        pane = self._fake_pane(filename, ['b.example', 'a.example'])
        result = CookieManagerPane.save_changes(pane)
        self.assertTrue(result)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['a.example', 'b.example'])
        self.assertEqual(pane.saved_domains, {'a.example', 'b.example'})
