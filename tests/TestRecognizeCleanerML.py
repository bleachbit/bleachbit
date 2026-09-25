# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for RecognizeCleanerML
"""

import os
import unittest
from unittest import mock

import bleachbit
from tests import common
from bleachbit.GtkShim import is_gtk_available
from bleachbit.Options import options, path_to_option
from bleachbit.RecognizeCleanerML import (NEW, cleaner_change_dialog, hashdigest,
                                          RecognizeCleanerML)


class RecognizeCleanerMLTestCase(common.BleachbitTestCase):
    """Test case for RecognizeCleanerML"""

    def test_hash(self):
        """Unit test for hash()"""
        digest = hashdigest('bleachbit')
        self.assertEqual(len(digest), 128)
        self.assertEqual(digest[1:10], '6382c203e')

    def test_init_without_salt(self):
        """Unit test for __init__ when hashsalt is not set in options"""
        self.assertFalse(options.has_option('hashsalt'))
        # Create a CleanerML file so list_cleanerml_files() returns a file,
        # which exercises __recognized().
        cleaner_dir = bleachbit.personal_cleaners_dir
        os.makedirs(cleaner_dir, exist_ok=True)
        cleaner_file = os.path.join(cleaner_dir, 'test_recognize.xml')
        try:
            with open(cleaner_file, 'w', encoding='utf-8') as f:
                f.write(
                    '<?xml version="1.0"?><cleaner id="test"><label>Test</label></cleaner>')
            with mock.patch('bleachbit.RecognizeCleanerML.cleaner_change_dialog'):
                rcm = RecognizeCleanerML(parent_window=None)
            self.assertIsNotNone(rcm.salt)
            self.assertIsInstance(rcm.salt, str)
            self.assertEqual(len(rcm.salt), 128)
            # Verify __recognized() was exercised by checking the hash was stored.
            self.assertTrue(options.has_option(
                path_to_option(cleaner_file), 'hashpath'))
        finally:
            if os.path.exists(cleaner_file):
                os.remove(cleaner_file)

    @unittest.skipUnless(is_gtk_available(), 'requires GTK+ module and a display environment')
    def test_cleaner_change_dialog_remove_error(self):
        """The dialog closes whether or not deleting a file works"""

        class TickedStore(list):
            """ListStore with every row ticked for deletion"""

            def append(self, row):
                super().append([True, row[1]])

        # Portable mode lists a file twice, so the second delete misses it
        changes = [['a.xml', NEW, ''], ['a.xml', NEW, '']]
        for remove_error in (FileNotFoundError, PermissionError):
            fake_gtk = mock.MagicMock()
            dialog = fake_gtk.Dialog.return_value
            dialog.run.return_value = fake_gtk.ResponseType.ACCEPT
            fake_gtk.ListStore.return_value = TickedStore()
            with mock.patch('bleachbit.GtkShim.Gtk', fake_gtk, create=True), \
                    mock.patch('bleachbit.GtkShim.GObject', mock.MagicMock(), create=True), \
                    mock.patch('bleachbit.GuiUtil.load_icon_or_fallback'), \
                    mock.patch('bleachbit.GuiBasic.delete_confirmation_dialog',
                               return_value=True), \
                    mock.patch('bleachbit.RecognizeCleanerML.os.remove',
                               side_effect=[None, remove_error]):
                if remove_error is FileNotFoundError:
                    cleaner_change_dialog(changes, None)
                else:
                    with self.assertRaises(PermissionError):
                        cleaner_change_dialog(changes, None)
            dialog.destroy.assert_called_once()
