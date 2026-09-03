# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Mac
"""

import subprocess
import unittest
from unittest import mock

from tests import common
from bleachbit import IS_MAC
if IS_MAC:
    from bleachbit.Mac import (
        get_macos_locale,
        macos_version_name,
        notify_macos,
    )


class MacTestCase(common.BleachbitTestCase):
    """Test case for bleachbit.Mac"""

    @common.skipUnlessMac
    def test_notify_macos_calls_osascript(self):
        """notify_macos() invokes osascript with a display notification script."""
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
        malicious = 'x" with title "Hacked" -- do shell script "echo pwned'
        with mock.patch('subprocess.run') as mock_run:
            notify_macos(malicious)

        script = mock_run.call_args[0][0][2]
        self.assertIn('\\"', script)
        self.assertEqual(script.count('display notification'), 1)

    @common.skipUnlessMac
    def test_notify_macos_survives_missing_osascript(self):
        """A missing/failing osascript must not raise out of notify_macos()."""
        with mock.patch('subprocess.run', side_effect=FileNotFoundError('no osascript')):
            notify_macos('should not raise')

    @common.skipUnlessMac
    def test_notify_macos_raises_on_non_mac(self):
        """notify_macos() raises RuntimeError when not running on macOS."""
        with mock.patch('bleachbit.Mac.IS_MAC', False):
            with self.assertRaises(RuntimeError):
                notify_macos('test')

    @common.skipUnlessMac
    def test_get_macos_locale(self):
        """get_macos_locale() returns system locale preference or None."""
        ret = get_macos_locale()
        if ret is not None:
            self.assertIsInstance(ret, str)
            self.assertNotIn('@', ret)

    @common.skipUnlessMac
    def test_get_macos_locale_mocked(self):
        """get_macos_locale() parses AppleLocale output and strips variants."""
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        proc_mock.stdout = 'es_ES@currency=EUR\n'
        with mock.patch('subprocess.run', return_value=proc_mock):
            self.assertEqual(get_macos_locale(), 'es_ES')

        proc_mock.stdout = ''
        with mock.patch('subprocess.run', return_value=proc_mock):
            self.assertIsNone(get_macos_locale())

        with mock.patch('subprocess.run', side_effect=subprocess.SubprocessError):
            self.assertIsNone(get_macos_locale())

    def test_macos_version_name(self):
        """macos_version_name() returns correct marketing name for macOS versions."""
        # Imported inline so this test runs on non-Mac platforms
        from bleachbit.Mac import macos_version_name  # pylint: disable=import-outside-toplevel
        cases = {
            '26.6.2': 'Tahoe',
            '15.1.0': 'Sequoia',
            '14.0': 'Sonoma',
            '13.5': 'Ventura',
            '12.3': 'Monterey',
            '11.0': 'Big Sur',
            # A version newer than this dictionary must return None, not a
            # wrong name.
            '27.0': None,
            '9.0': None,
            '': None,
        }
        for version, expected in cases.items():
            self.assertEqual(macos_version_name(version), expected,
                             f"Version {version} should map to {expected}")

    @common.skipUnlessMac
    def test_macos_version_name_no_arg(self):
        """macos_version_name() with no argument names the running macOS."""
        from bleachbit.Mac import macos_version_name, MACOSX_DICT_LEGACY, MACOSX_DICT_MODERN
        name = macos_version_name()
        self.assertIn(name, {**MACOSX_DICT_LEGACY, **MACOSX_DICT_MODERN}.values())

    def test_macos_version_name_empty_mac_ver(self):
        """An empty platform.mac_ver() string yields None, not an exception."""
        # Imported inline so this test runs on non-Mac platforms
        from bleachbit.Mac import macos_version_name  # pylint: disable=import-outside-toplevel
        with mock.patch('platform.mac_ver', return_value=('', ('', '', ''), '')):
            self.assertIsNone(macos_version_name())
