# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
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

import os
import time
import types
import unittest

os.environ['LANGUAGE'] = 'en'

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
from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.Options import options, Options
from tests import common

bleachbit.online_update_notification_enabled = False

@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
class GUITestCase(common.BleachbitTestCase):
    app = Bleachbit(auto_exit=False, uac=False)
    options_get_tree = options.get_tree

    """Test case for module GUI"""
    @classmethod
    def setUpClass(cls):
        super(GUITestCase, GUITestCase).setUpClass()
        options.set('first_start', False)
        options.set('check_online_updates', False) # avoid pop-up window
        options.get_tree = types.MethodType(lambda self, parent, child: False, options)
        cls.app.register()
        cls.app.activate()
        cls.refresh_gui()

    @classmethod
    def tearDownClass(cls):
        super(GUITestCase, GUITestCase).tearDownClass()
        options.get_tree = cls.options_get_tree

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

    def test_diagnostics(self):
        """Opens the diagnostics dialog and closes it"""
        dialog, txt = self.app.get_diagnostics_dialog()
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
        model = gui.view.get_model()
        tree = self.find_widget(gui, Gtk.TreeView)
        self.assertIsNotNone(tree)

        def get_iter(model, cleaner):
            it = model.get_iter(Gtk.TreePath(0))
            while it:
                if model[it][2] == cleaner:
                    return model.iter_children(it)
                it = model.iter_next(it)
            return None

        def find_option(model, cleaner, option):
            it = get_iter(model, cleaner)
            self.assertIsNotNone(it)
            while it:
                if model[it][2] == option:
                    return it
                it = model.iter_next(it)
            return None

        it = find_option(model, 'system', 'tmp')
        self.assertIsNotNone(it)

        tree.scroll_to_cell(model.get_path(it), None, False, 0, 0)
        self.refresh_gui()
        model[model.iter_parent(it)][1] = True
        model[it][1] = True
        self.refresh_gui()

        b = self.click_button(gui, _("Preview"))
        self.refresh_gui()

    @unittest.skipIf(os.getenv('TRAVIS', 'f') == 'true', 'Not supported on Travis CI')
    def test_notify(self):
        """Test a pop-up notification"""
        from bleachbit.GUI import notify
        notify('This is a test notification')
        import time
        time.sleep(1)
