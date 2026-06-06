# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import os
import time
import unittest

from bleachbit import IS_WINDOWS
from bleachbit.GtkShim import HAVE_GTK
from tests import common

if HAVE_GTK:
    from bleachbit.GtkShim import Gdk, Gtk
    from bleachbit.GuiUtil import clear_clipboard, get_clipboard_paths


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class GUIUtilTestCase(common.BleachbitTestCase):
    """Test case for module GUI Util"""

    def _wait_for_clipboard_text(self, clipboard, text):
        """Wait for GTK to publish clipboard text."""
        deadline = time.time() + 5
        while time.time() < deadline:
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            if clipboard.wait_for_text() == text:
                return True
            time.sleep(0.05)
        return False

    def test_get_clipboard_paths(self):
        """Get paths from the real clipboard"""
        paths = [
            self.write_file('clipboard-path-1'),
            self.write_file('clipboard-path-2'),
        ]
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        if IS_WINDOWS:
            from bleachbit import General
            args = ('powershell.exe', 'Set-Clipboard', '-Path',
                    os.path.join(self.tempdir, 'clipboard-path-*'))
            rc, _stdout, stderr = General.run_external(args)
            self.assertEqual(0, rc, stderr)
            targets = [Gdk.atom_intern_static_string('FileNameW')]
        else:
            clipboard_text = '\n'.join([f'  {paths[0]}  ', paths[1], ''])
            clipboard.set_text(clipboard_text, -1)
            if not self._wait_for_clipboard_text(clipboard, clipboard_text):
                self.skipTest('clipboard text is unavailable')
            targets = [Gdk.atom_intern_static_string('text/plain')]

        # Getting should not effect the clipboard state.
        get1 = list(get_clipboard_paths(clipboard, targets))
        get2 = list(get_clipboard_paths(clipboard, targets))
        self.assertEqual(get1, get2)
        self.assertEqual(paths, get1)

        # Verify that clearing the clipboard works.
        clear_clipboard()
        self.assertEqual([], list(get_clipboard_paths(clipboard, targets)))
