# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module GuiChaff
"""


import sys
import tempfile
import threading
import time
import unittest
import warnings
from unittest.mock import patch

from tests import common

from bleachbit.GtkShim import HAVE_GTK, Gtk, GLib, Gio

if HAVE_GTK:
    from bleachbit.GuiApplication import Bleachbit
    from bleachbit.GuiChaff import (STOP_MODE_FILE_COUNT,
                                    STOP_MODE_TOTAL_SIZE,
                                    STOP_MODE_FREE_SPACE,
                                    MAX_FILE_COUNT,
                                    _make_should_stop,
                                    _make_progress_cb)


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
class GuiChaffTestCase(common.BleachbitTestCase):
    """Test case for module GuiChaff"""
    app = Bleachbit(auto_exit=False, uac=False) if HAVE_GTK else None

    @classmethod
    def setUpClass(cls):
        super(GuiChaffTestCase, cls).setUpClass()

        # Try to register the application, catch the error if already registered
        try:
            cls.app.register()
            cls.app.hold()  # Keep application alive during tests
            cls.app.activate()
        except GLib.GError as e:
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
            if sys.version_info >= (3, 14):
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    warnings.filterwarnings(
                        "ignore",
                        message=".*asyncio.AbstractEventLoopPolicy.*",
                        category=DeprecationWarning
                    )
                    warnings.filterwarnings(
                        "ignore",
                        message=".*asyncio.get_event_loop_policy.*",
                        category=DeprecationWarning
                    )
                    Gtk.main_iteration_do(blocking=False)
            else:
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
        # Test stop mode combo
        self.assertIsNotNone(self.dialog.stop_mode_combo)
        self.assertEqual(self.dialog.stop_mode_combo.get_active(), 0)
        # Test stop value spinner
        self.assertIsNotNone(self.dialog.stop_value_spin)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 100)
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

    def test_stop_value_spinner_file_count(self):
        """Test stop value spinner limits for file count mode"""
        self.dialog.stop_mode_combo.set_active(STOP_MODE_FILE_COUNT)
        self.dialog.stop_value_spin.set_value(1)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 1)
        self.dialog.stop_value_spin.set_value(MAX_FILE_COUNT)
        self.assertEqual(
            self.dialog.stop_value_spin.get_value_as_int(), MAX_FILE_COUNT)
        # Test out of bounds values
        self.dialog.stop_value_spin.set_value(0)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 1)
        self.dialog.stop_value_spin.set_value(MAX_FILE_COUNT + 1)
        self.assertEqual(
            self.dialog.stop_value_spin.get_value_as_int(), MAX_FILE_COUNT)

    def test_stop_value_spinner_total_size(self):
        """Test stop value spinner limits for total size mode"""
        self.dialog.stop_mode_combo.set_active(STOP_MODE_TOTAL_SIZE)
        self.dialog.stop_value_spin.set_value(1)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 1)
        self.dialog.stop_value_spin.set_value(999999)
        self.assertEqual(
            self.dialog.stop_value_spin.get_value_as_int(), 999999)

    def test_stop_value_spinner_free_space(self):
        """Test stop value spinner limits for free space mode"""
        self.dialog.stop_mode_combo.set_active(STOP_MODE_FREE_SPACE)
        self.dialog.stop_value_spin.set_value(1)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 1)
        self.dialog.stop_value_spin.set_value(99)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 99)
        # Test out of bounds
        self.dialog.stop_value_spin.set_value(0)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 1)
        self.dialog.stop_value_spin.set_value(100)
        self.assertEqual(self.dialog.stop_value_spin.get_value_as_int(), 99)

    def test_stop_mode_changed(self):
        """Test that changing stop mode updates the label and adjustment"""
        self.dialog.stop_mode_combo.set_active(STOP_MODE_TOTAL_SIZE)
        self.refresh_gui()
        self.assertIn('MB', self.dialog.stop_value_label.get_text())

        self.dialog.stop_mode_combo.set_active(STOP_MODE_FREE_SPACE)
        self.refresh_gui()
        self.assertIn('%', self.dialog.stop_value_label.get_text())

        self.dialog.stop_mode_combo.set_active(STOP_MODE_FILE_COUNT)
        self.refresh_gui()
        self.assertIn('files', self.dialog.stop_value_label.get_text().lower())

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.download_models')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files(self, mock_have_models, mock_download_models, mock_make_files):
        """Test make files functionality with automatic download"""
        # Set up mocks
        mock_have_models.return_value = False  # Need to download models
        mock_download_models.return_value = True

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.stop_value_spin.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Simulate clicking make button
        self.dialog.make_button.clicked()
        self.refresh_gui(0.1)

        # Verify models were downloaded
        mock_download_models.assert_called_once()

        # Verify make_files_thread was called with correct arguments
        mock_make_files.assert_called_once()
        args = mock_make_files.call_args[0]
        self.assertEqual(args[0], 0)   # stop_mode (file count)
        self.assertEqual(args[1], 10)  # stop_value
        self.assertEqual(args[2], 0)   # inspiration (2600)
        self.assertEqual(args[3], self.tempdir)  # output_folder
        self.assertIsInstance(args[6], threading.Event)  # abort_event

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.download_models')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files_download_fails(self, mock_have_models, mock_download_models, mock_make_files):
        """Test handling when download fails"""
        mock_have_models.return_value = False  # Need to download models
        mock_download_models.return_value = False  # Download fails

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.stop_value_spin.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Simulate clicking make button
        self.dialog.make_button.clicked()
        self.refresh_gui(0.1)

        # Verify models download was attempted
        mock_download_models.assert_called_once()

        # Verify make_files_thread was NOT called because download failed
        mock_make_files.assert_not_called()

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.have_models')
    def test_make_files_models_exist(self, mock_have_models, mock_make_files):
        """Test making files when models already exist"""
        mock_have_models.return_value = True  # Models already exist

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.stop_value_spin.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Simulate clicking make button
        self.dialog.make_button.clicked()
        self.refresh_gui(0.1)

        # Verify make_files_thread was called with correct arguments
        mock_make_files.assert_called_once()
        self.assertIsInstance(mock_make_files.call_args, tuple)
        args = mock_make_files.call_args[0]
        self.assertEqual(args[0], 0)   # stop_mode (file count)
        self.assertEqual(args[1], 10)  # stop_value
        self.assertEqual(args[2], 0)   # inspiration (2600)
        self.assertEqual(args[3], self.tempdir)  # output_folder
        self.assertIsInstance(args[6], threading.Event)  # abort_event

    def test_progress_cb_keyword_args(self):
        """Regression test: _make_progress_cb must accept keyword args from Chaff.py

        Chaff.py calls on_progress(fraction, generated_file_names=..., cumulative_size=...)
        so the callbacks must accept those keyword names.
        """

        collected = []

        def on_progress(fraction):
            collected.append(fraction)

        for stop_mode in (STOP_MODE_FILE_COUNT, STOP_MODE_TOTAL_SIZE, STOP_MODE_FREE_SPACE):
            cb = _make_progress_cb(stop_mode, 100, self.tempdir, on_progress)
            # Must accept keyword arguments as Chaff.py passes them
            cb(0.5, generated_file_names=['/tmp/fake'], cumulative_size=12345)
            self.assertEqual(len(collected), 1, f'stop_mode={stop_mode}')
            collected.clear()

    def test_should_stop_keyword_args(self):
        """Regression test: _make_should_stop must accept keyword args from Chaff.py

        Chaff.py calls should_stop(generated_file_names, cumulative_size=...)
        so the callbacks must accept those parameter names.
        """


        abort_event = threading.Event()

        for stop_mode in (STOP_MODE_FILE_COUNT, STOP_MODE_TOTAL_SIZE, STOP_MODE_FREE_SPACE):
            should_stop, _file_count = _make_should_stop(
                stop_mode, 100, self.tempdir, abort_event)
            # Must accept keyword argument as Chaff.py passes it
            result = should_stop(['/tmp/fake'], cumulative_size=12345)
            self.assertIsInstance(result, bool)

    @patch('bleachbit.GuiChaff.make_files_thread')
    @patch('bleachbit.Chaff.have_models')
    def test_abort_button(self, mock_have_models, mock_make_files):
        """Test that abort button sets the abort event"""
        mock_have_models.return_value = True

        self.dialog.choose_folder_button.set_filename(self.tempdir)
        self.dialog.stop_value_spin.set_value(10)
        self.dialog.inspiration_combo.set_active(0)

        # Initially, the abort button should be disabled.
        self.assertFalse(self.dialog.abort_button.get_sensitive())

        # Start generation
        self.dialog.make_button.clicked()
        self.refresh_gui(0.1)

        # The abort button should now be enabled.
        self.assertTrue(self.dialog.abort_button.get_sensitive())

        # Click abort.
        self.dialog.abort_button.clicked()
        self.refresh_gui()

        # Verify that the abort event was set.
        abort_event = mock_make_files.call_args[0][6]
        self.assertIsInstance(abort_event, threading.Event)
        self.assertTrue(abort_event.is_set())
