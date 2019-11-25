# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2019 Andrew Ziem
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

from __future__ import absolute_import

import os
import time
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

from bleachbit import _
from bleachbit.GuiPreferences import PreferencesDialog
from tests import common

@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
class GUITestCase(common.BleachbitTestCase):
    app = Bleachbit(auto_exit=True, uac=False)

    """Test case for module GUI"""
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for the testcase"""
        super(GUITestCase, GUITestCase).setUpClass()
        cls.app.run()

    @classmethod
    def refresh_gui(cls, delay=0):
        while Gtk.events_pending():
            Gtk.main_iteration_do(blocking=False)
        time.sleep(delay)

    @classmethod
    def print_children(cls, widget, indent=0):
        print('{}{}'.format(' ' * indent, c))
        if isinstance(widget, Gtk.Container):
            for c in widget.get_children():
                cls.print_children(c, indent + 2)

    @classmethod
    def find_button(cls, widget, text):
        if isinstance(widget, Gtk.Button):
            if widget.get_label() == text:
                return widget
        if isinstance(widget, Gtk.Container):
            for c in widget.get_children():
                b = cls.find_button(c, text)
                if b is not None:
                    return b
        return None

    def click_button(self, dialog, text):
        b = self.find_button(dialog, text)
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

    def test_shred(self):
        """
        - Create a named temporary file
        - Do the equivalent of opening the menu and clicking "Shred Files"
        - Find the named temporary files
        - Shred it
        - Verify it is gone
        """

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
        dialog = self.app.get_diagnostics_dialog()
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

    def test_clean_chrome_cookies(self):
        """
        - Select Google Chrome/Cookies checkbox option
        - Click preview button
        """
