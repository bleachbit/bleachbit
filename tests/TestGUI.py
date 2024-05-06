# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2023 Andrew Ziem
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
Test case for module GUI
"""

import mock
import os
import unittest
import time
import types

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from bleachbit.GUI import Bleachbit
    HAVE_GTK = True
except ImportError:
    HAVE_GTK = False

import bleachbit
from bleachbit import _
from bleachbit.Options import options

from tests import common

bleachbit.online_update_notification_enabled = False


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
class GUITestCase(common.BleachbitTestCase):
    app = Bleachbit(auto_exit=False, uac=False)
    options_get_tree = options.get_tree

    """Test case for module GUI"""
    @classmethod
    def setUpClass(cls):
        cls.old_language = common.get_env('LANGUAGE')
        common.put_env('LANGUAGE', 'en')
        super(GUITestCase, GUITestCase).setUpClass()
        options.set('first_start', False)
        options.set('check_online_updates', False)  # avoid pop-up window
        options.get_tree = types.MethodType(
            lambda self, parent, child: False, options)
        cls.app.register()
        cls.app.activate()
        cls.refresh_gui()

    @classmethod
    def tearDownClass(cls):
        super(GUITestCase, GUITestCase).tearDownClass()
        options.get_tree = cls.options_get_tree
        common.put_env('LANGUAGE', cls.old_language)
        
    def setUp(self):
        self._gui = self.app._window
        self._cleaner_id, self._option_id = 'cleaner', 'option'
        self._cleaner_id_2, self._option_id_2 = 'cleaner2', 'option2'
        self._dirname = self.mkdtemp()

    @classmethod
    def refresh_gui(cls, delay=0):
        while Gtk.events_pending():
            Gtk.main_iteration_do(blocking=False)
        time.sleep(delay)

    @classmethod
    def print_widget(cls, widget, indent=0):
        print('{}{}'.format(' ' * indent, widget))
        if isinstance(widget, Gtk.Container):
            for c in widget.get_children():
                cls.print_children(c, indent + 2)

    @classmethod
    def find_widget(cls, widget, widget_class, widget_label=None):
        if isinstance(widget, widget_class):
            if widget_label is None or widget.get_label() == widget_label:
                return widget
        if isinstance(widget, Gtk.Container):
            for c in widget.get_children():
                b = cls.find_widget(c, widget_class, widget_label)
                if b is not None:
                    return b
        return None

    @classmethod
    def get_iter(cls, model, cleaner):
        it = model.get_iter(Gtk.TreePath(0))
        while it:
            if model[it][2] == cleaner:
                return model.iter_children(it)
            it = model.iter_next(it)
        return None

    @classmethod
    def find_option(cls, model, cleaner, option):
        it = cls.get_iter(model, cleaner)
        #cls.assertIsNotNone(cls, it)
        while it:
            if model[it][2] == option:
                return it
            it = model.iter_next(it)
        return None

    def _put_checkmark_on_cleaner(self, cleaner_id, option_id):
        it = self._cleaner_in_tree(cleaner_id, option_id)
        model = self._gui.view.get_model()
        model[model.iter_parent(it)][1] = True
        model[it][1] = True
        self.refresh_gui()
        
    def _get_checkmark_state_for_cleaner(self, cleaner_id, option_id):
        it = self._cleaner_in_tree(cleaner_id, option_id)
        model = self._gui.view.get_model()
        parent_check_mark_state = model[model.iter_parent(it)][1]
        checkmark_state = model[it][1]
        return parent_check_mark_state, checkmark_state

    def _cleaner_in_tree(self, cleaner_id, option_id):
        model = self._gui.view.get_model()
        tree = self.find_widget(self._gui, Gtk.TreeView)
        self.assertIsNotNone(tree)
        it = self.find_option(model, cleaner_id, option_id)
        self.assertIsNotNone(it)
        tree.scroll_to_cell(model.get_path(it), None, False, 0, 0)
        return it

    def click_button(self, dialog, label):
        b = self.find_widget(dialog, Gtk.Button, label)
        self.assertIsNotNone(b)
        b.clicked()
        self.refresh_gui()

    def test_GUI(self):
        """Unit test for class GUI"""
        # there should be no crashes
        # app.do_startup()
        # pp.do_activate()                            Build a unit test that that does this
        gui = self.app._window
        gui.update_progress_bar(0.0)
        gui.update_progress_bar(1.0)
        gui.update_progress_bar("status")

    def test_preferences(self):
        """Opens the preferences dialog and closes it"""

        # show preferences dialog
        pref = self.app.get_preferences_dialog()
        pref.dialog.show_all()
        self.refresh_gui()

        # click close button
        self.click_button(pref.dialog, Gtk.STOCK_CLOSE)

        # destroy
        pref.dialog.destroy()

    def test_system_information(self):
        """Opens the system information dialog and closes it"""
        dialog, txt = self.app.get_system_information_dialog()
        dialog.show_all()
        self.refresh_gui()

        # click close button
        self.click_button(dialog, Gtk.STOCK_CLOSE)

        # destroy
        dialog.destroy()

    def test_about(self):
        """Opens the about dialog and closes it"""
        about = self.app.get_about_dialog()
        about.show_all()
        self.refresh_gui()

        # destroy
        about.destroy()

    def test_preview(self):
        """Select cleaner option and clicks preview button"""
        gui = self.app._window
        self.refresh_gui()
        self._put_checkmark_on_cleaner('system', 'tmp')
        self.refresh_gui()
        b = self.click_button(gui, _("Preview"))
        self.refresh_gui()

    @unittest.skipIf(os.getenv('TRAVIS', 'f') == 'true', 'Not supported on Travis CI')
    def test_notify(self):
        """Test a pop-up notification"""
        from bleachbit.GUI import notify
        notify('This is a test notification')
        import time
        time.sleep

    @mock.patch('bleachbit.GuiBasic.delete_confirmation_dialog')
    def test_confirm_delete(self, mock_delete_confirmation_dialog):
        gui = self.app._window
        for new_delete_confirmation in [True, False]:
            options.set('delete_confirmation',
                        new_delete_confirmation, commit=False)
            gui._confirm_delete(False, False)

        # We should have a single call to delete_confirmation_dialog
        # only when delete_confirmation option is True.
        mock_delete_confirmation_dialog.assert_called_once()

    def test_shred_paths(self):
        dirname = self.mkdtemp(prefix='bleachbit-test-shred_paths')
        test_files_dirs = [
            self.mkstemp(prefix="somefile", dir=dirname),
            dirname,
            self.mkstemp(prefix="somefile")
        ]

        for obj in test_files_dirs:
            self.assertExists(obj)

        gui = self.app._window
        self.refresh_gui()

        with mock.patch('bleachbit.GUI.GUI._confirm_delete', return_value=True):
            self.assertTrue(gui._confirm_delete(False, False))
            gui.shred_paths(test_files_dirs)

        self.refresh_gui()

        for obj in test_files_dirs:
            self.assertNotExists(obj)

    @mock.patch('bleachbit.RecognizeCleanerML.cleaner_change_dialog')
    def _setup_new_cleaner(self, dirname, cleaner_id, option_id, mock_cleaner_change_dialog):#, mock_list_cleanerml_files):
        def _create_cleaner_file_in_directory(cleaner_id, option_id, dirname):
            cleaner_content = ('<?xml version="1.0" encoding="UTF-8"?>'
                               '<cleaner id="{0}">'
                               '<label>{0}_label</label>'
                               '<option id="{1}">'
                               '<label>{1}_label</label>'
                               '<description>Delete files in a test directory</description>'
                               '<action command="delete" search="walk.all" path="{2}"/>'
                               '</option>'
                               '</cleaner>'.format(cleaner_id, option_id, dirname))
            cleaner_filename = os.path.join(
                dirname, 'test_gui_cleaner_{}.xml'.format(cleaner_id))
            self.write_file(cleaner_filename, cleaner_content, 'w')
            return cleaner_filename

        def _set_mocks_return_values(mock_cleaner_change_dialog):
            mock_cleaner_change_dialog.return_value = None

        def _load_new_cleaner_in_gui():
            # to load the new test cleaner
            self._gui.cb_refresh_operations()
            self.refresh_gui()

        cleaner_filename = _create_cleaner_file_in_directory(cleaner_id, option_id, dirname)
        self.assertExists(cleaner_filename)
        _set_mocks_return_values(mock_cleaner_change_dialog)
        _load_new_cleaner_in_gui()
        file_to_clean = self.mkstemp(prefix="somefile", dir=dirname)
        self.assertExists(file_to_clean)
        return file_to_clean

    def test_run_operations(self):
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            file_to_clean = self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)
            self._put_checkmark_on_cleaner(self._cleaner_id, self._option_id)

            with mock.patch('bleachbit.GUI.GUI._confirm_delete', return_value=True):
                self.assertTrue(self._gui._confirm_delete(False, False))
                # same as b = self.click_button(gui, _("Clean"))
                self._gui.run_operations(None)

            self.refresh_gui()
            self.assertNotExists(file_to_clean)

    def test_cb_run_option(self):
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            file_to_clean = self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)

            for really_delete, assert_method in [(False, self.assertExists), (True, self.assertNotExists)]:
                with mock.patch('bleachbit.GUI.GUI._confirm_delete', return_value=True):
                    self.assertTrue(self._gui._confirm_delete(False, False))
                    self._gui.cb_run_option(
                        None, really_delete, self._cleaner_id, self._option_id
                    )  # activated from context menu

                self.refresh_gui()
                assert_method(file_to_clean)
    
    def _assert_checkmark_active(self, cleaner_id, option_id, is_checkmark_active):
        assert_function = self.assertTrue if is_checkmark_active else self.assertFalse
        parent_check_mark_state, checkmark_state = self._get_checkmark_state_for_cleaner(cleaner_id, option_id)
        assert_function(parent_check_mark_state)
        assert_function(checkmark_state)
    
    def test_deselect_all_based_on_clean_selection(self):
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)
            
            self._assert_checkmark_active(self._cleaner_id, self._option_id, False)
            
            self._gui._deselect_all_button.emit("pressed")
            self.refresh_gui()
            
            self._assert_checkmark_active(self._cleaner_id, self._option_id, False)

    def test_select_all_deselect_all_based_on_clean_selection(self):
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)
            self._gui._select_all_button.emit("pressed")
            self.refresh_gui()
            
            self._assert_checkmark_active(self._cleaner_id, self._option_id, True)
            
            self._gui._deselect_all_button.emit("pressed")
            
            self._assert_checkmark_active(self._cleaner_id, self._option_id, False)
    
    def test_select_all_based_on_existing_selection(self):
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            from bleachbit.Cleaner import backends
            self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)
            self._setup_new_cleaner(self._dirname, self._cleaner_id_2, self._option_id_2)
            
            self._put_checkmark_on_cleaner(self._cleaner_id, self._option_id)
            self._assert_checkmark_active(self._cleaner_id, self._option_id, True)
            self._assert_checkmark_active(self._cleaner_id_2, self._option_id_2, False)
            
            self._gui._select_all_button.emit("pressed")
            self.refresh_gui()
            self._assert_checkmark_active(self._cleaner_id, self._option_id, True)
            self._assert_checkmark_active(self._cleaner_id_2, self._option_id_2, True)
       
    def test_deselect_all_based_on_existing_selection(self):    
        with mock.patch('bleachbit.system_cleaners_dir', self._dirname):
            from bleachbit.Cleaner import backends
            self._setup_new_cleaner(self._dirname, self._cleaner_id, self._option_id)
            self._setup_new_cleaner(self._dirname, self._cleaner_id_2, self._option_id_2)
            
            self._put_checkmark_on_cleaner(self._cleaner_id, self._option_id)
            self._assert_checkmark_active(self._cleaner_id, self._option_id, True)
            self._assert_checkmark_active(self._cleaner_id_2, self._option_id_2, False)
            
            self._gui._deselect_all_button.emit("pressed")
            self.refresh_gui()
            
            self._assert_checkmark_active(self._cleaner_id, self._option_id, False)
            self._assert_checkmark_active(self._cleaner_id_2, self._option_id_2, False)
