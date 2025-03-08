# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
Test case for module GuiChaff
"""


import os
import unittest
import tempfile
import time
from unittest.mock import patch, MagicMock

from tests import common

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio
    HAVE_GTK = True
    from bleachbit.GUI import Bleachbit
except ImportError:
    HAVE_GTK = False


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
class GuiChaffTestCase(common.BleachbitTestCase):
    """Test case for module GuiChaff"""
    app = Bleachbit(auto_exit=False, uac=False)

    @classmethod
    def setUpClass(cls):
        if os.name == 'nt':
            from bleachbit.Windows import setup_environment
        super(GuiChaffTestCase, cls).setUpClass()

        # Try to register the application, catch the error if already registered
        try:
            cls.app.register()
            cls.app.hold()  # Keep application alive during tests
            cls.app.activate()
        except gi.repository.GLib.GError as e:
            if not "already exported" in str(e):
                raise
            # Application already registered, just hold it
            cls.app.hold()
            # Try to get the default application and activate it
            default_app = Gio.Application.get_default()
            if default_app:
                default_app.activate()
        cls.refresh_gui()

    @classmethod
    def refresh_gui(cls, delay=0):
        while Gtk.events_pending():
            Gtk.main_iteration_do(blocking=False)
        time.sleep(delay)

    def setUp(self):
        from bleachbit.GuiChaff import ChaffDialog
        # Pass the GtkWindow object
        self.dialog = ChaffDialog(parent=self.app._window)

    def tearDown(self):
        self.dialog.destroy()

    def test_dialog_creation(self):
        """Test that dialog is created with expected widgets"""
        self.assertIsNotNone(self.dialog)
        # Test combo box
        self.assertIsNotNone(self.dialog.inspiration_combo)
        self.assertEqual(self.dialog.inspiration_combo.get_active(), 0)
        # Test file count spinner
        self.assertIsNotNone(self.dialog.file_count)
        self.assertEqual(self.dialog.file_count.get_value_as_int(), 100)
        # Test folder chooser
        self.assertIsNotNone(self.dialog.choose_folder_button)
        self.assertEqual(
            self.dialog.choose_folder_button.get_filename(),
            tempfile.gettempdir())

    def test_combo_options(self):
        """Test that combo box has correct options"""
        expected_options = ('2600 Magazine', "Hillary Clinton's emails")
        self.assertEqual(
            self.dialog.inspiration_combo_options, expected_options)
        for i, option in enumerate(expected_options):
            self.dialog.inspiration_combo.set_active(i)
            self.assertEqual(
                self.dialog.inspiration_combo.get_active_text(),
                option)

    def test_file_count_spinner(self):
        """Test file count spinner limits and adjustment"""
        self.dialog.file_count.set_value(1)
        self.assertEqual(self.dialog.file_count.get_value_as_int(), 1)
        self.dialog.file_count.set_value(99999)
        self.assertEqual(self.dialog.file_count.get_value_as_int(), 99999)
        # Test out of bounds values
        self.dialog.file_count.set_value(0)
        self.assertEqual(self.dialog.file_count.get_value_as_int(), 1)
        self.dialog.file_count.set_value(100000)
        self.assertEqual(self.dialog.file_count.get_value_as_int(), 99999)

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.download_models')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files(self, mock_have_models, mock_download_models, mock_make_files):
        """Test make files functionality"""
        # Set up mocks
        mock_have_models.return_value = False  # Need to download models
        mock_download_models.return_value = True

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.file_count.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Mock the dialog response
        def mock_dialog_run(parent, *args, **kwargs):
            dialog = MagicMock()
            dialog.run = lambda: Gtk.ResponseType.OK
            dialog.destroy = lambda: None
            return dialog

        # Patch Gtk.MessageDialog during the test
        with patch('gi.repository.Gtk.MessageDialog', side_effect=mock_dialog_run):
            # Simulate clicking make button
            self.dialog.make_button.clicked()

            # Verify models were downloaded
            mock_download_models.assert_called_once()

            # Verify make_files_thread was called with correct arguments
            mock_make_files.assert_called_once()
            args = mock_make_files.call_args[0]
            self.assertEqual(args[0], 10)  # file_count
            self.assertEqual(args[1], 0)   # inspiration (2600)
            self.assertEqual(args[2], self.tempdir)  # output_folder

    @patch('bleachbit.Chaff.download_models')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files_cancel_download(self, mock_have_models, mock_download_models):
        """Test canceling the download models dialog"""
        mock_have_models.return_value = False  # Need to download models

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.file_count.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Mock the dialog response
        def mock_dialog_run(parent, *args, **kwargs):
            dialog = MagicMock()
            dialog.run = lambda: Gtk.ResponseType.CANCEL
            dialog.destroy = lambda: None
            return dialog

        # Patch Gtk.MessageDialog during the test
        with patch('gi.repository.Gtk.MessageDialog', side_effect=mock_dialog_run):
            # Simulate clicking make button
            self.dialog.make_button.clicked()

            # Verify models were not downloaded
            mock_download_models.assert_not_called()

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files_models_exist(self, mock_have_models, mock_make_files):
        """Test making files when models already exist"""
        mock_have_models.return_value = True  # Models already exist

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.file_count.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Simulate clicking make button
        self.dialog.make_button.clicked()

        # Verify make_files_thread was called with correct arguments
        mock_make_files.assert_called_once()
        args = mock_make_files.call_args[0]
        self.assertEqual(args[0], 10)  # file_count
        self.assertEqual(args[1], 0)   # inspiration (2600)
        self.assertEqual(args[2], self.tempdir)  # output_folder
