# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Mac
"""

import errno
import glob
import os
import struct
import subprocess
from unittest import mock

from tests import common
from bleachbit import IS_MAC
if IS_MAC:
    from bleachbit.Mac import (
        delete_safari_cookies,
        get_macos_locale,
        is_full_disk_access_enabled,
        is_safari_binarycookies,
        list_safari_cookies,
        notify_macos,
        _read_safari_cookie_records,
        _serialize_safari_cookie_records,
        _write_safari_cookie_records,
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

    def test_is_full_disk_access_enabled_non_mac(self):
        """is_full_disk_access_enabled() returns True on non-macOS."""
        if IS_MAC:
            self.skipTest('This test is only for non-macOS')
        from bleachbit.Mac import is_full_disk_access_enabled
        self.assertTrue(is_full_disk_access_enabled())

    @common.skipUnlessMac
    def test_is_full_disk_access_enabled_no_probe_exists(self):
        """When no probe path exists, the function returns True (assume enabled)."""
        fake_probes = ('~/nonexistent_fda_probe_1/',
                       '~/nonexistent_fda_probe_2/')
        with mock.patch('bleachbit.Mac._FDA_PROBE_PATHS', fake_probes):
            self.assertTrue(is_full_disk_access_enabled())

    @common.skipUnlessMac
    def test_is_full_disk_access_enabled_eperm_detected(self):
        """EPERM on an existing probe path is detected as FDA not enabled."""

        fake_probes = ('~/Library/Safari/',)
        real_exists = os.path.exists

        def fake_scandir(path):
            # Simulate TCC blocking the directory with EPERM.
            raise OSError(errno.EPERM, 'Operation not permitted', path)

        with mock.patch('bleachbit.Mac._FDA_PROBE_PATHS', fake_probes), \
                mock.patch('os.scandir', side_effect=fake_scandir), \
                mock.patch('os.path.exists', side_effect=real_exists):
            self.assertFalse(is_full_disk_access_enabled())

    @common.skipUnlessMac
    def test_is_full_disk_access_enabled_eacces_not_fda(self):
        """EACCES (Unix mode) is not mistaken for a TCC/FDA denial."""
        fake_probes = ('~/Library/Safari/',)
        real_exists = os.path.exists

        def fake_scandir(path):
            raise OSError(errno.EACCES, 'Permission denied', path)

        with mock.patch('bleachbit.Mac._FDA_PROBE_PATHS', fake_probes), \
                mock.patch('os.scandir', side_effect=fake_scandir), \
                mock.patch('os.path.exists', side_effect=real_exists):
            self.assertTrue(is_full_disk_access_enabled())

    @common.skipUnlessMac
    def test_is_full_disk_access_enabled_accessible(self):
        """When probe paths are accessible, FDA is reported as enabled."""
        # Use a path that exists and is accessible (not TCC-protected).
        fake_probes = (self.tempdir + '/',)
        with mock.patch('bleachbit.Mac._FDA_PROBE_PATHS', fake_probes):
            self.assertTrue(is_full_disk_access_enabled())

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
        self.assertIn(name, {**MACOSX_DICT_LEGACY, **
                      MACOSX_DICT_MODERN}.values())

    def test_macos_version_name_empty_mac_ver(self):
        """An empty platform.mac_ver() string yields None, not an exception."""
        # Imported inline so this test runs on non-Mac platforms
        from bleachbit.Mac import macos_version_name  # pylint: disable=import-outside-toplevel
        with mock.patch('platform.mac_ver', return_value=('', ('', '', ''), '')):
            self.assertIsNone(macos_version_name())

    @staticmethod
    def _make_cookie_record(domain, name='cookie_name', path='/', value='cookie_val'):
        """Build a raw binary Safari cookie record."""
        header_size = 32
        d_bytes = domain.encode('utf-8') + b'\x00'
        n_bytes = name.encode('utf-8') + b'\x00'
        p_bytes = path.encode('utf-8') + b'\x00'
        v_bytes = value.encode('utf-8') + b'\x00'
        d_off = header_size
        n_off = d_off + len(d_bytes)
        p_off = n_off + len(n_bytes)
        v_off = p_off + len(p_bytes)
        total_size = v_off + len(v_bytes)
        return (
            struct.pack('<IIIIIIII', total_size, 0, 0,
                        0, d_off, n_off, p_off, v_off)
            + d_bytes + n_bytes + p_bytes + v_bytes
        )

    def _create_binarycookies_file(self, domain_records):
        """Create a temporary binarycookies file"""
        pages = [{'records': domain_records}]
        data = _serialize_safari_cookie_records(pages)
        temp_path = self.mkstemp(suffix='.binarycookies')
        with open(temp_path, 'wb') as f:
            f.write(data)
        return temp_path

    @common.skipUnlessMac
    def test_is_safari_binarycookies(self):
        """is_safari_binarycookies correctly identifies binarycookies files."""
        rec = self._make_cookie_record('webkit.org')
        path = self._create_binarycookies_file([('webkit.org', rec)])
        self.assertTrue(is_safari_binarycookies(path))

        # Non-binarycookies file
        not_cookie = self.mkstemp()
        with open(not_cookie, 'wb') as f:
            f.write(b'SQLite format 3\x00')
        self.assertFalse(is_safari_binarycookies(not_cookie))

        # Nonexistent file
        self.assertFalse(is_safari_binarycookies(
            '/nonexistent/path/cookies.binarycookies'))

    @common.skipUnlessMac
    def test_read_safari_cookies_rejects_bad_page_marker(self):
        """Regression test: _read_safari_cookie_records() must reject a
        page whose marker doesn't match what real Safari (and this
        module's own writer) always emits, rather than trusting
        cookie_count blindly. Confirmed against a real, unmodified
        Safari Cookies.binarycookies file that this exact marker value
        (b'\\x00\\x00\\x01\\x00') is what real Safari writes.

        File layout for a single-page, single-record file: 'cook'(4) +
        page_count(4) + page_size_table(4x1) = 12 bytes of file header,
        then the page itself starts at file offset 12 (the page marker
        is its first 4 bytes).
        """
        rec = self._make_cookie_record('webkit.org')
        temp_path = self._create_binarycookies_file([('webkit.org', rec)])

        with open(temp_path, 'r+b') as f:
            f.seek(12)
            f.write(b'\xff')

        with self.assertRaises(ValueError):
            list(_read_safari_cookie_records(temp_path))

    @common.skipUnlessMac
    def test_read_safari_cookies_rejects_bad_end_of_table_marker(self):
        """Regression test: _read_safari_cookie_records() must reject a
        page whose end-of-table marker (right after the offset table)
        doesn't match what real Safari (and this module's own writer)
        always emits.

        For a single-record page, the offset table is 4 bytes (one
        entry), so the end-of-table marker sits at page offset
        8 + 1*4 = 12, i.e. file offset 12 (page start) + 12 = 24.
        """
        rec = self._make_cookie_record('webkit.org')
        temp_path = self._create_binarycookies_file([('webkit.org', rec)])

        with open(temp_path, 'r+b') as f:
            f.seek(24)
            f.write(b'\xff')

        with self.assertRaises(ValueError):
            list(_read_safari_cookie_records(temp_path))

    @common.skipUnlessMac
    def test_safari_binarycookies_roundtrip(self):
        """Roundtrip serialize, write, read, and list Safari binary cookies."""
        rec1 = self._make_cookie_record('webkit.org')
        rec2 = self._make_cookie_record('.sub.domain.org')
        path = self._create_binarycookies_file([
            ('webkit.org', rec1),
            ('sub.domain.org', rec2),
        ])

        domains = list_safari_cookies(path)
        self.assertEqual(domains, ['sub.domain.org', 'webkit.org'])

        pages = _read_safari_cookie_records(path)
        self.assertEqual(len(pages), 1)
        self.assertEqual(len(pages[0]['records']), 2)
        self.assertEqual(pages[0]['records'][0][0], 'webkit.org')
        self.assertEqual(pages[0]['records'][1][0], 'sub.domain.org')

        # Test writing via _write_safari_cookie_records
        write_path = os.path.join(self.tempdir, 'rewritten.binarycookies')
        _write_safari_cookie_records(write_path, pages)
        self.assertEqual(list_safari_cookies(write_path),
                         ['sub.domain.org', 'webkit.org'])

    @common.skipUnlessMac
    def test_delete_safari_cookies_preview(self):
        """Preview deletion of Safari cookies computes deletion stats without modifying file."""
        rec1 = self._make_cookie_record('bugs.webkit.org')
        rec2 = self._make_cookie_record('github.com')
        path = self._create_binarycookies_file([
            ('bugs.webkit.org', rec1),
            ('github.com', rec2),
        ])

        res = delete_safari_cookies(path, {'github.com'}, really_delete=False)
        self.assertEqual(res['total_deleted'], 1)
        self.assertEqual(res['total_kept'], 1)
        self.assertFalse(res['skipped'])
        self.assertFalse(res['whole_file_deleted'])
        self.assertEqual(res['file_size_estimation_method'], 'ratio')
        # File should remain unmodified
        self.assertEqual(list_safari_cookies(path), [
                         'bugs.webkit.org', 'github.com'])

    @common.skipUnlessMac
    def test_delete_safari_cookies_selective(self):
        """Selective deletion removes unkept domains and rewrites the file."""
        rec1 = self._make_cookie_record('git.webkit.org')
        rec2 = self._make_cookie_record('github.com')
        path = self._create_binarycookies_file([
            ('git.webkit.org', rec1),
            ('github.com', rec2),
        ])

        res = delete_safari_cookies(path, {'github.com'}, really_delete=True)
        self.assertEqual(res['total_deleted'], 1)
        self.assertEqual(res['total_kept'], 1)
        self.assertFalse(res['skipped'])
        self.assertFalse(res['whole_file_deleted'])
        self.assertEqual(list_safari_cookies(path), ['github.com'])

    @common.skipUnlessMac
    def test_delete_safari_cookies_delete_all(self):
        """When no cookies match keep list, the whole file is removed."""
        rec1 = self._make_cookie_record('build.webkit.org')
        path = self._create_binarycookies_file([('build.webkit.org', rec1)])

        res = delete_safari_cookies(path, {'other.org'}, really_delete=True)
        self.assertEqual(res['total_deleted'], 1)
        self.assertEqual(res['total_kept'], 0)
        self.assertTrue(res['whole_file_deleted'])
        self.assertFalse(os.path.exists(path))

    @common.skipUnlessMac
    def test_delete_safari_cookies_empty_keep_list_raises(self):
        """Empty keep list raises ValueError."""
        rec1 = self._make_cookie_record('lists.webkit.org')
        path = self._create_binarycookies_file([('lists.webkit.org', rec1)])

        with self.assertRaises(ValueError):
            delete_safari_cookies(path, set(), really_delete=False)

    @common.skipUnlessMac
    def test_cookie_module_delegates_safari(self):
        """bleachbit.Cookie delegator functions invoke Mac Safari implementations."""
        from bleachbit import Cookie
        rec1 = self._make_cookie_record('webkit.org')
        rec2 = self._make_cookie_record('bleachbit.org')
        path = self._create_binarycookies_file([
            ('webkit.org', rec1),
            ('bleachbit.org', rec2),
        ])

        # list_cookies
        cookie_list = Cookie.list_cookies(path)
        self.assertEqual(cookie_list, [('bleachbit.org',), ('webkit.org',)])

        # delete_cookies preview
        preview = Cookie.delete_cookies(
            path, {'bleachbit.org'}, really_delete=False)
        self.assertEqual(preview['total_deleted'], 1)
        self.assertEqual(preview['total_kept'], 1)

        # delete_cookies execute
        result = Cookie.delete_cookies(
            path, {'bleachbit.org'}, really_delete=True)
        self.assertEqual(result['total_deleted'], 1)
        self.assertEqual(result['total_kept'], 1)
        self.assertEqual(Cookie.list_cookies(path), [('bleachbit.org',)])

    @common.skipUnlessMac
    def test_real_safari_cookies_read_sanity(self):
        """Reading real Safari cookie files must not crash or yield garbage."""
        from bleachbit import Cookie

        patterns = (
            '~/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies',
            '~/Library/HTTPStorages/*.binarycookies',
        )
        paths = [
            path
            for pattern in patterns
            for path in glob.glob(os.path.expanduser(pattern))
        ]
        if not paths:
            self.skipTest('no real Safari cookie files present on this system')

        if not is_full_disk_access_enabled():
            self.skipTest('Full Disk Access is not enabled')

        for path in paths:
            self.assertTrue(is_safari_binarycookies(path))

            domains = list_safari_cookies(path)
            self.assertIsInstance(domains, list)
            self.assertEqual(Cookie.list_cookies(
                path), [(d,) for d in domains])

            for domain in domains:
                self.assertIsInstance(domain, str)
                self.assertTrue(domain)
                self.assertNotIn('\x00', domain)
