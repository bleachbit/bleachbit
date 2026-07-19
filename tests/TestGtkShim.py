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
import subprocess
import sys
import unittest
from unittest import mock

from tests import common
from bleachbit import IS_WINDOWS
from bleachbit.General import get_executable
from bleachbit.GtkShim import (
    _build_error_html,
    _fix_arg,
    _handle_gtk_import_error,
    _patched_argv,
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

    def test_unknown_error_includes_traceback_and_sysinfo(self):
        """Unknown-error HTML must include traceback and system information."""
        html = _build_error_html(
            RuntimeError('something broke'),
            traceback_text='Traceback (most recent call last):...',
        )
        self.assertIn('Error: something broke', html)
        self.assertIn('Traceback (most recent call last):...', html)
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
        )
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_html_structure(self):
        """Output must be valid minimal HTML with required elements."""
        html = _build_error_html(
            Exception('test'),
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
            _show_windows_error_dialog('BleachBit', '<html>test</html>')
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
            _show_windows_error_dialog('BleachBit', '<html/>')
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
    def test_unknown_error_includes_traceback_in_html(self):
        """Unknown errors must produce HTML with traceback section."""
        with mock.patch('bleachbit.GtkShim._show_windows_error_dialog') as m, \
                mock.patch('sys.frozen', True, create=True), \
                mock.patch('sys.executable', r'C:\Users\user\Apps\BleachBit\bleachbit.exe'):
            try:
                raise RuntimeError('something broke')
            except RuntimeError as e:
                _handle_gtk_import_error(e)
            m.assert_called_once()
            _title, html = m.call_args[0]
            self.assertIn('Traceback', html)
            self.assertIn('System information', html)


class FixArgTestCase(unittest.TestCase):
    """Tests for _fix_arg()."""

    def test_ascii_unchanged(self):
        """ASCII strings must pass through unchanged."""
        self.assertEqual(_fix_arg('hello'), 'hello')

    def test_surrogate_replaced(self):
        """Unpaired surrogates must be replaced with the replacement character."""
        arg = 'prefix' + chr(0xD800) + 'suffix'
        fixed = _fix_arg(arg)
        self.assertNotIn(chr(0xD800), fixed)
        self.assertIn('\ufffd', fixed)

    def test_valid_unicode_unchanged(self):
        """Valid Unicode characters must pass through unchanged."""
        self.assertEqual(_fix_arg('\u2014em-dash'), '\u2014em-dash')
        self.assertEqual(_fix_arg('\U0001F525'), '\U0001F525')


class PatchedArgvTestCase(unittest.TestCase):
    """Tests for _patched_argv()."""

    def test_transform_applied(self):
        """Transform function must be applied to all argv elements."""
        original = sys.argv[:]
        with _patched_argv(lambda a: a.swapcase()):
            self.assertEqual(sys.argv, [a.swapcase() for a in original])
        self.assertEqual(sys.argv, original)

    def test_restored_on_exception(self):
        """sys.argv must be restored even when exception occurs."""
        original = sys.argv[:]

        def boom():
            with _patched_argv(lambda a: 'x'):
                raise RuntimeError('boom')
        self.assertRaises(RuntimeError, boom)
        self.assertEqual(sys.argv, original)

    def test_restores_reference_identity(self):
        """sys.argv must be restored to the exact same object reference."""
        original = sys.argv
        with _patched_argv(lambda a: a):
            pass
        self.assertIs(sys.argv, original)


class TryImportGtkTestCase(unittest.TestCase):
    """Test GTK import flow with surrogate paths in argv."""

    def test_surrogate_in_argv(self):
        """Must not crash for surrogates in sys.argv."""
        bad_path = os.path.join(
            'c:\\', 'temp', 'surrogate') + chr(0xD800) + 'beta_test0'

        if IS_WINDOWS:
            script = f'''
import ctypes
import sys
from unittest import mock
sys.argv = ['bleachbit.py', {bad_path!r}]
with mock.patch.object(ctypes.windll.user32, 'MessageBoxW', return_value=7):
    from bleachbit.GtkShim import is_gtk_available
    success = is_gtk_available()
print(f"OK success={{success}}")
'''
        else:
            script = f'''
import sys
sys.argv = ['bleachbit.py', {bad_path!r}]
from bleachbit.GtkShim import is_gtk_available
success = is_gtk_available()
print(f"OK success={{success}}")
'''

        result = subprocess.run(
            [get_executable(), '-c', script],
            capture_output=True, text=True,
            timeout=30, check=False,
        )

        self.assertEqual(result.returncode, 0,
                         f'stderr: {result.stderr}')
        self.assertIn('OK success=', result.stdout,
                      'surrogate argv caused GTK import to crash')

    @common.skipIfWindows
    def test_no_display_does_not_import_gtk_libraries(self):
        """A failed display precondition must not import gi.repository."""
        script = '''
import sys
import bleachbit.GtkShim as shim
assert not shim.is_gtk_available()
assert not shim.gtk_may_be_available()
from bleachbit.GtkShim import Gtk
assert Gtk is None
assert not any(name.startswith('gi.repository') for name in sys.modules)
'''
        env = os.environ.copy()
        env.pop('DISPLAY', None)
        env.pop('WAYLAND_DISPLAY', None)
        env.pop('XDG_RUNTIME_DIR', None)
        result = subprocess.run(
            [get_executable(), '-c', script],
            capture_output=True, text=True, env=env, timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0,
                         f'stderr: {result.stderr}')


class GtkAvailabilityTestCase(unittest.TestCase):
    """Test actual and preflight GTK availability states."""

    def test_require_gtk_reports_deferred_import_failure(self):
        """A deferred import failure raises RuntimeError and reports the reason."""
        import bleachbit.GtkShim as shim  # pylint: disable=import-outside-toplevel

        with mock.patch.multiple(
            shim,
            _gtk_preconditions_met=True,
            _gtk_libraries_imported=False,
            _gtk_libraries_available=False,
            _gtk_unavailable_reason=None,
        ), mock.patch.object(
            shim, '_import_gtk_libraries',
            return_value=(False, 'simulated GTK import failure'),
        ):
            self.assertTrue(shim.gtk_may_be_available())
            self.assertFalse(shim.is_gtk_available())
            with self.assertRaisesRegex(
                RuntimeError, 'simulated GTK import failure',
            ):
                shim.require_gtk()


if __name__ == '__main__':
    unittest.main()
