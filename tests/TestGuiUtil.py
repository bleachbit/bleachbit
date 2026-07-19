# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for GuiUtil module.
"""


import os
import time
import unittest
from pathlib import Path

from bleachbit import General, logger
from bleachbit.GtkShim import HAVE_GTK

from tests import common

if HAVE_GTK:
    from bleachbit.GtkShim import Gdk, Gtk  # pylint: disable=ungrouped-imports
    from bleachbit.GuiUtil import (clear_clipboard, flush_gtk_events,
                                   get_clipboard_paths, get_font_size_from_name)

CLIPBOARD_TIMEOUT_SECONDS = 5
CLIPBOARD_SLEEP_SECONDS = 0.05


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class GUIUtilClipboardTestCase(common.BleachbitTestCase):
    """Test case for module GUI Util"""

    def setUp(self):
        """Set up before each test method."""
        super().setUp()
        self.paths = [
            self.write_file('clipboard-path-1'),
            self.write_file('clipboard-path-2'),
        ]

    def tearDown(self):
        """Clean up after each test method."""
        super().tearDown()
        # Verify that clearing the clipboard works.
        clear_clipboard()
        self.assertEqual([], list(get_clipboard_paths()))

    def _wait_for_clipboard_text(self, clipboard, text):
        """Wait for GTK to publish clipboard text."""
        start_time = time.time()
        deadline = start_time + CLIPBOARD_TIMEOUT_SECONDS
        if clipboard.wait_for_text() == text:
            logger.debug(
                'clipboard text available after first wait attempt at %.1fs', time.time() - start_time)
            return True
        while time.time() < deadline:
            flush_gtk_events()
            if clipboard.wait_for_text() == text:
                elapsed = time.time() - start_time
                logger.info(
                    "clipboard text became available after %.1fs", elapsed)
                return True
            time.sleep(CLIPBOARD_SLEEP_SECONDS)
        elapsed = time.time() - start_time
        logger.warning(
            "clipboard text was still not available after %.1fs", elapsed)
        return False

    def _copy_paths_to_windows_clipboard(self):
        """Copy test paths using the shell clipboard, like Explorer."""
        pattern = os.path.join(self.tempdir, 'clipboard-path-*')
        args = ('powershell.exe', 'Set-Clipboard', '-Path', pattern)
        rc, _stdout, stderr = General.run_external(args)
        self.assertEqual(0, rc, stderr)

    def _wait_for_windows_clipboard_paths(self, clipboard, paths):
        """Wait for the production clipboard path to return file paths."""
        expected = sorted(paths)
        start_time = time.time()
        deadline = start_time + CLIPBOARD_TIMEOUT_SECONDS
        while time.time() < deadline:
            flush_gtk_events()
            got = sorted(get_clipboard_paths())
            if got == expected:
                elapsed = time.time() - start_time
                logger.info(
                    "clipboard paths became available after %.1fs", elapsed)
                return
            time.sleep(CLIPBOARD_SLEEP_SECONDS)
        got = sorted(get_clipboard_paths())
        _has_targets, targets = clipboard.wait_for_targets()
        target_names = [target.name() for target in targets] if targets else []
        elapsed = time.time() - start_time
        self.fail(
            'clipboard file paths were still not available after '
            f'{elapsed:.1f}s: expected {expected}, got {got}, '
            f'targets={target_names}')

    def test_get_clipboard_paths_text_plain(self):
        """Get text/plain paths from the real clipboard."""

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard_text = '\n'.join([f'  {self.paths[0]}  ', self.paths[1], ''])
        clipboard.set_text(clipboard_text, -1)
        if not self._wait_for_clipboard_text(clipboard, clipboard_text):
            self.skipTest('clipboard text is unavailable')

        # Getting should not affect the clipboard state.
        get1 = get_clipboard_paths()
        get2 = get_clipboard_paths()
        self.assertIsInstance(get1, list)
        self.assertIsInstance(get2, list)
        self.assertEqual(get1, get2)
        self.assertEqual(self.paths, get1)

    @common.skipIfWindows
    def test_get_clipboard_paths_uri_list(self):
        """Get text/uri-list paths like those copied from a file manager."""
        uris = [Path(path).as_uri() for path in self.paths]

        class ClipboardContents:
            """Mock clipboard contents for testing"""

            def get_uris(self):
                """Return the URIs"""
                return uris

        class Clipboard:
            """Mock clipboard for testing"""

            def wait_for_contents(self, _target):
                """Return mock clipboard contents"""
                return ClipboardContents()

        targets = [Gdk.atom_intern_static_string('text/uri-list')]

        get1 = get_clipboard_paths(Clipboard(), targets)
        get2 = get_clipboard_paths(Clipboard(), targets)
        self.assertIsInstance(get1, list)
        self.assertIsInstance(get2, list)
        self.assertEqual(get1, get2)
        self.assertEqual(self.paths, get1)

    @common.skipUnlessWindows
    def test_get_clipboard_paths_windows(self):
        """Get file paths from the clipboard on Windows."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._copy_paths_to_windows_clipboard()
        self._wait_for_windows_clipboard_paths(clipboard, self.paths)

        # Getting should not affect the clipboard state.
        get1 = get_clipboard_paths()
        get2 = get_clipboard_paths()
        self.assertIsInstance(get1, list)
        self.assertIsInstance(get2, list)
        self.assertEqual(get1, get2)
        self.assertEqual(sorted(self.paths), sorted(get1))


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class GUIUtilFontTestCase(common.BleachbitTestCase):
    """Test case for font size utility"""

    def test_get_font_size_from_name_valid(self):
        """Extract font size from valid font names."""
        tests = (
            ('Sans 12', 12),
            ('Monospace Bold 14', 14),
            ('12', 12),
            ('Arial 10.5', 10),
        )
        for font_name, expected in tests:
            self.assertEqual(get_font_size_from_name(font_name), expected,
                             f"Font name '{font_name}' should return {expected}")

    def test_get_font_size_from_name_invalid(self):
        """Return None for invalid inputs."""
        tests = (
            None,
            123,
            '',
            'Sans',
            'Sans abc',
            'Sans 0',
            'Sans -1',
        )
        for font_name in tests:
            self.assertIsNone(get_font_size_from_name(font_name),
                              f"Font name '{font_name}' should return None")
