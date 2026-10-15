# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module GuiCookie
"""

# These tests reach into internals on purpose.
# pylint: disable=protected-access

import json
import os
import types
import unittest
from unittest import mock

from tests import common

import bleachbit
from bleachbit.Cookie import COOKIE_KEEP_LIST_FILENAME
from bleachbit.GtkShim import is_gtk_available

HAVE_GTK = is_gtk_available()
if HAVE_GTK:
    from bleachbit.GtkShim import Gtk
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

    def test_save_changes_still_works(self):
        """save_changes() still writes the sorted keep list normally"""
        filename = os.path.join(self.tempdir, 'cookie_keep_list.json')
        pane = self._fake_pane(filename, ['b.example', 'a.example'])
        result = CookieManagerPane.save_changes(pane)
        self.assertTrue(result)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['a.example', 'b.example'])
        self.assertEqual(pane.saved_domains, {'a.example', 'b.example'})

    def test_activate_link_stops_default_handler(self):
        """The 'Learn more' link must not also be opened by GTK"""
        with mock.patch('bleachbit.GuiCookie.open_url') as open_url:
            # pylint: disable-next=possibly-used-before-assignment
            handled = CookieManagerPane.on_activate_link(
                None, None, 'https://docs.bleachbit.org/')
        self.assertTrue(handled)
        open_url.assert_called_once()

    def test_unreadable_keep_list(self):
        """A corrupt keep list leaves the page usable, and a save replaces it"""
        keep_path = os.path.join(
            bleachbit.options_dir, COOKIE_KEEP_LIST_FILENAME)
        os.makedirs(bleachbit.options_dir, exist_ok=True)
        self.addCleanup(lambda: os.path.exists(
            keep_path) and os.remove(keep_path))
        self.write_file(keep_path, text='["a.example",]')

        with mock.patch('bleachbit.GuiCookie.threading.Thread'), \
                self.assertLogs('bleachbit.GuiCookie', level='ERROR'):
            pane = CookieManagerPane()
        self.assertEqual(pane.saved_domains, set())

        pane._finish_populate(['b.example'])
        pane.on_select_all_clicked(None)
        with open(keep_path, encoding='utf-8') as f:
            self.assertEqual(json.load(f), ['b.example'])
        pane.destroy()

    def test_columns_do_not_sort_filter_model(self):
        """A sortable column needs a sortable model, which a filter is not"""
        with mock.patch('bleachbit.GuiCookie.threading.Thread'):
            pane = CookieManagerPane()
        # pylint: disable-next=possibly-used-before-assignment
        if not isinstance(pane.treeview.get_model(), Gtk.TreeSortable):
            for column in pane.treeview.get_columns():
                self.assertEqual(column.get_sort_column_id(), -1)
        pane.destroy()

    def test_discovery_failure_finishes_loading(self):
        """Any error during cookie discovery still ends the loading state"""
        class SyncThread:
            def __init__(self, target=None, daemon=None):
                self.target = target
                self.daemon = daemon

            def start(self):
                self.target()

        with mock.patch('bleachbit.GuiCookie.threading.Thread', SyncThread), \
                mock.patch('bleachbit.GuiCookie.list_unique_cookies',
                           side_effect=ModuleNotFoundError('sqlite3')), \
                mock.patch('bleachbit.GuiCookie.GLib.idle_add') as idle_add, \
                self.assertLogs('bleachbit.GuiCookie', level='ERROR'):
            pane = CookieManagerPane()
        idle_add.assert_called_once_with(pane._finish_populate, [])
        pane.destroy()

    def test_saved_dotted_host_stays_checked(self):
        """A saved '.example.com' shows as one checked row after reopening"""
        keep_path = os.path.join(
            bleachbit.options_dir, COOKIE_KEEP_LIST_FILENAME)
        os.makedirs(bleachbit.options_dir, exist_ok=True)
        self.addCleanup(lambda: os.path.exists(
            keep_path) and os.remove(keep_path))
        self.write_file(keep_path, text='[".google.com"]')

        with mock.patch('bleachbit.GuiCookie.threading.Thread'):
            pane = CookieManagerPane()
        pane._finish_populate(['.google.com', 'accounts.google.com'])
        self.assertEqual([tuple(row) for row in pane.cookie_store],
                         [(False, 'accounts.google.com'), (True, 'google.com')])
        pane.destroy()
