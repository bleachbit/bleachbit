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

from tests.common import pytest

from bleachbit import General, logger
from bleachbit.GtkShim import is_gtk_available

from tests import common

HAVE_GTK = is_gtk_available()
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

    @pytest.mark.xdist_group('gui')
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

        targets = [Gdk.Atom.intern('text/uri-list', False)]

        get1 = get_clipboard_paths(Clipboard(), targets)
        get2 = get_clipboard_paths(Clipboard(), targets)
        self.assertIsInstance(get1, list)
        self.assertIsInstance(get2, list)
        self.assertEqual(get1, get2)
        self.assertEqual(self.paths, get1)

    @common.skipIfWindows
    def test_get_clipboard_paths_matches_target_names(self):
        """Match targets by name because Gdk.Atom objects may not compare equal"""
        uris = [Path(path).as_uri() for path in self.paths]
        text = '\n'.join(self.paths)

        class Target:
            """Stand-in for a Gdk.Atom that only exposes its name"""

            def __init__(self, name):
                self._name = name

            def name(self):
                """Return the target name"""
                return self._name

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

            def wait_for_text(self):
                """Return the paths as plain text"""
                return text

        for target_name in ('text/uri-list', 'text/plain', 'UTF8_STRING'):
            with self.subTest(target=target_name):
                self.assertEqual(self.paths, get_clipboard_paths(
                    Clipboard(), [Target(target_name)]))

    @common.skipIfWindows
    def test_get_clipboard_paths_unusable_target_name(self):
        """Fall back to a fresh atom when a target's name cannot be decoded.

        Regression test for a real-world bug where Gdk.atom_intern_static_string()
        returned an atom whose name() raised UnicodeDecodeError.
        """
        uris = [Path(path).as_uri() for path in self.paths]

        class UnusableTarget:
            """Stand-in for a Gdk.Atom with a corrupted, undecodable name"""

            def name(self):
                """Simulate a corrupted atom name"""
                raise UnicodeDecodeError(
                    'utf-8', b'\xff', 0, 1, 'invalid start byte')

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

        result = get_clipboard_paths(Clipboard(), [UnusableTarget()])
        self.assertEqual(self.paths, result)

    def test_get_clipboard_paths_none_target(self):
        """Fall back to a fresh atom when a target is None.

        Regression test for a real-world crash on macOS/Quartz where a
        clipboard target whose NSPasteboard type could not be mapped to
        a Gdk.Atom appeared as None in the target list (alongside a
        'gdk_atom_intern: assertion atom_name != NULL failed' GDK
        warning) instead of a valid atom object, crashing on
        target.name() with AttributeError.
        """
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

        result = get_clipboard_paths(Clipboard(), [None])
        self.assertEqual(self.paths, result)

    @common.skipUnlessWindows
    @pytest.mark.xdist_group('gui')
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


class GUIUtilNotifyMacTestCase(common.BleachbitTestCase):
    """Test case for notify_macos() in module GuiUtil"""

    @common.skipUnlessMac
    def test_notify_macos_calls_osascript(self):
        """notify_macos() invokes osascript with a display notification script."""
        from unittest import mock
        from bleachbit.GuiUtil import notify_macos

        with mock.patch('subprocess.run') as mock_run:
            notify_macos('hello world')

        self.assertEqual(mock_run.call_count, 1)
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], 'osascript')
        self.assertEqual(args[1], '-e')
        self.assertIn('display notification', args[2])
        self.assertIn('hello world', args[2])

    @common.skipUnlessMac
    def test_notify_macos_escapes_quotes_and_backslashes(self):
        """Quotes and backslashes in the message cannot break out of the
        AppleScript string literal or inject additional script."""
        from unittest import mock
        from bleachbit.GuiUtil import notify_macos

        malicious = 'x" with title "Hacked" -- do shell script "echo pwned'
        with mock.patch('subprocess.run') as mock_run:
            notify_macos(malicious)

        script = mock_run.call_args[0][0][2]
        # The malicious quote must be escaped, not left as a live delimiter.
        self.assertIn('\\"', script)
        # Exactly one real AppleScript command, not two -- confirming
        # the attacker payload never broke out to start a second one.
        self.assertEqual(script.count('display notification'), 1)

    @common.skipUnlessMac
    def test_notify_macos_survives_missing_osascript(self):
        """A missing/failing osascript must not raise out of notify_macos()."""
        from unittest import mock
        from bleachbit.GuiUtil import notify_macos

        with mock.patch('subprocess.run', side_effect=FileNotFoundError('no osascript')):
            notify_macos('should not raise')  # must not raise
