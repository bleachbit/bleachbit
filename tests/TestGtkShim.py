# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module GtkShim
"""

import ctypes
import os
import unittest
from unittest import mock

from tests import common
from bleachbit.GtkShim import (
    _build_error_html,
    _handle_gtk_import_error,
    _show_windows_error_dialog,
    path_has_lib_or_bin,
)


class PathHasLibOrBinTestCase(unittest.TestCase):
    """Test path_has_lib_or_bin() detection logic."""

    def test_path_has_lib_or_bin(self):
        """Test path_has_lib_or_bin() with various paths."""
        tests = [
            # (path, expected_result)
            # Standalone 'bin' directory triggers detection
            (r'C:\bin', 'bin'),
            (r'C:\bin\xlib', 'bin'),
            (r'C:\libx\bin', 'bin'),
            (r'C:\bin\bin', 'bin'),
            (r'C:\Users\username\Downloads\bin\BleachBit-Portable', 'bin'),
            # Standalone 'lib' directory triggers detection
            (r'C:\lib', 'lib'),
            (r'C:\lib\xbin', 'lib'),
            (r'C:\binx\lib', 'lib'),
            (r'C:\lib\lib', 'lib'),
            (r'C:\Users\username\Downloads\lib\BleachBit-Portable', 'lib'),
            (r'C:\ProgramData\chocolatey\lib\bleachbit.portable\BleachBit-Portable', 'lib'),
            # Detection is case-insensitive
            (r'C:\Users\BIN\app', 'bin'),
            (r'C:\Users\Lib\app', 'lib'),
            # 'binx' is not 'bin'
            (r'C:\Users\username\Downloads\binx\BleachBit-Portable', None),
            # 'xbin' is not 'bin'
            (r'C:\Users\username\Downloads\xbin\BleachBit-Portable', None),
            # 'libfoo' is not 'lib'
            (r'C:\ProgramData\libfoo\app', None),
            # Normal portable path without lib or bin
            (r'C:\Users\username\Downloads\BleachBit-5.0.0-portable\BleachBit-Portable', None),
            # Empty path returns None
            ('', None),
            # 'lib' or 'bin' embedded in longer names should not match
            (r'C:\calibre\library\app', None),
            (r'C:\cabinet\app', None),
        ]
        case_functions = (
            lambda x: x.lower(),
            lambda x: x.upper(),
            lambda x: x.title(),
            lambda x: x.title().swapcase(),
        )
        for path, expected in tests:
            with self.subTest(path=path, expected=expected):
                joined = os.path.join(path, 'bleachbit.exe')
                for func in case_functions:
                    self.assertEqual(path_has_lib_or_bin(
                        func(joined)), expected)


class BuildErrorHtmlTestCase(unittest.TestCase):
    """Tests for _build_error_html()."""

    def test_lib_bin_bug_omits_traceback_and_sysinfo(self):
        """lib/bin HTML must not include traceback or system information."""
        html = _build_error_html(
            ValueError('Namespace Gtk not available'),
            is_lib_bin_bug=True,
            exe_path=r'C:\Users\user\bin\BleachBit',
        )
        self.assertIn('bin', html)
        self.assertIn('pygobject-lib-bin-error', html)
        self.assertNotIn('Traceback', html)
        self.assertNotIn('System information', html)
        self.assertNotIn('<textarea', html)

    def test_lib_bin_bug_html_has_fix_advice(self):
        """lib/bin HTML must mention moving BleachBit."""
        html = _build_error_html(
            ValueError('Namespace Gtk not available'),
            is_lib_bin_bug=True,
            exe_path=r'C:\Users\user\lib\BleachBit',
        )
        self.assertIn('lib', html)
        self.assertIn('Move BleachBit', html)

    def test_unknown_error_includes_traceback_and_sysinfo(self):
        """Unknown-error HTML must include traceback and system information."""
        html = _build_error_html(
            RuntimeError('something broke'),
            is_lib_bin_bug=False,
            traceback_text='Traceback (most recent call last):...',
        )
        self.assertIn('Error: something broke', html)
        self.assertIn(
            'Traceback:\nTraceback (most recent call last):...', html)
        self.assertIn('System information:\n', html)
        self.assertIn('textarea', html)
        self.assertIn('Copy to clipboard', html)
        self.assertIn("function copyBugReport()", html)
        self.assertIn('get-help', html)
        self.assertEqual(html.count('<textarea'), 1)
        self.assertEqual(html.count('<pre>'), 0)

    def test_unknown_error_escapes_html_in_error_message(self):
        """Error message containing HTML special chars must be escaped."""
        html = _build_error_html(
            RuntimeError('<script>alert(1)</script>'),
            is_lib_bin_bug=False,
        )
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_html_structure(self):
        """Output must be valid minimal HTML with required elements."""
        for is_lib_bin in (True, False):
            html = _build_error_html(
                Exception('test'),
                is_lib_bin_bug=is_lib_bin,
                exe_path=r'C:\app\bin\BleachBit',
            )
            self.assertIn('<!DOCTYPE html>', html)
            self.assertIn('<html', html)
            self.assertIn('BleachBit cannot start', html)


class ShowWindowsErrorDialogTestCase(unittest.TestCase):
    """Tests for _show_windows_error_dialog() (non-Windows stubs)."""

    @common.skipUnlessWindows
    def test_yes_writes_html_file(self):
        """Selecting Yes must write the HTML file and open the browser."""
        with mock.patch.object(
            ctypes.windll.user32, 'MessageBoxW', return_value=6
        ), mock.patch('webbrowser.open') as mock_open:
            _show_windows_error_dialog('BleachBit', 'msg', '<html>test</html>')
            mock_open.assert_called_once()
            html_path = mock_open.call_args[0][0].replace('file:///', '')
            with open(html_path, encoding='utf-8') as f:
                self.assertIn('test', f.read())

    @common.skipUnlessWindows
    def test_no_does_not_write_file(self):
        """Selecting No must not open the browser."""
        with mock.patch.object(
            ctypes.windll.user32, 'MessageBoxW', return_value=7
        ), mock.patch('webbrowser.open') as mock_open:
            _show_windows_error_dialog('BleachBit', 'msg', '<html/>')
            mock_open.assert_not_called()


class HandleGtkImportErrorTestCase(unittest.TestCase):
    """Tests for _handle_gtk_import_error()."""

    @common.skipIfWindows
    def test_noop_on_non_windows(self):
        """Must do nothing on non-Windows platforms."""
        with mock.patch('bleachbit.GtkShim._show_windows_error_dialog') as m:
            _handle_gtk_import_error(ValueError('test'))
            m.assert_not_called()

    @common.skipUnlessWindows
    def test_lib_bin_path_calls_dialog(self):
        """lib/bin path must trigger dialog with correct short_message."""
        with mock.patch('bleachbit.GtkShim._show_windows_error_dialog') as m, \
                mock.patch('sys.frozen', True, create=True), \
                mock.patch('sys.executable', r'C:\Users\user\bin\BleachBit\bleachbit.exe'):
            _handle_gtk_import_error(ValueError('Namespace Gtk not available'))
            m.assert_called_once()
            _title, short_msg, html = m.call_args[0]
            self.assertIn('bin', short_msg)
            self.assertNotIn('Traceback', html)

    @common.skipUnlessWindows
    def test_unknown_error_includes_traceback_in_html(self):
        """Unknown errors must produce HTML with traceback section."""
        with mock.patch('bleachbit.GtkShim._show_windows_error_dialog') as m, \
                mock.patch('sys.frozen', True, create=True), \
                mock.patch('sys.executable', r'C:\Users\user\Apps\BleachBit\bleachbit.exe'):
            _handle_gtk_import_error(RuntimeError('something broke'))
            m.assert_called_once()
            _title, _short_msg, html = m.call_args[0]
            self.assertIn('Traceback', html)
            self.assertIn('System information', html)


if __name__ == '__main__':
    unittest.main()
