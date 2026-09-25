# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Network
"""

# standard imports
import errno
import http.server
import ipaddress
import logging
import os
import threading
import unittest
import warnings
from unittest.mock import MagicMock, Mock, patch

# Suppress urllib3's NotOpenSSLWarning (raised when the ssl module is
# not OpenSSL, e.g. macOS LibreSSL) before importing requests, which
# would otherwise become an error under PYTHONWARNINGS=error.
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

# third party imports
# pylint: disable-next=wrong-import-position
import requests

# first party imports
# pylint: disable-next=wrong-import-position
import bleachbit
# pylint: disable-next=wrong-import-position
from tests import common
# pylint: disable-next=wrong-import-position
from bleachbit import IS_WINDOWS
# pylint: disable-next=wrong-import-position
from bleachbit.FileUtilities import delete
# pylint: disable-next=wrong-import-position
from bleachbit.Network import (download_url_to_fn, fetch_url, get_gtk_version,
                               get_ip_for_url, get_user_agent,
                               unset_sslkeylogfile, _coarsen_os_version,
                               _coarsen_windows_build, _version_major_minor)

logger = logging.getLogger(__name__)


def response_to_error_msg(response):
    """Convert response to error message"""
    return "URL: {url}\n" + \
           f"Status: {response.status_code} {response.reason}\n" + \
           f"Response headers: {dict(response.headers)}\n" + \
           f"Response content: {response.text}"


class _StatusCodeHandler(http.server.BaseHTTPRequestHandler):
    """Reply with the HTTP status code named in the request path.

    A request for /status/404 responds with 404. Serving the codes
    locally keeps the tests off external services.
    """

    # do_GET is the handler name required by http.server
    # pylint: disable-next=invalid-name
    def do_GET(self):
        try:
            status_code = int(self.path.rsplit('/', 1)[-1])
        except ValueError:
            status_code = 400
        body = b'BleachBit test server\n'
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """Silence the default per-request logging to stderr."""


class NetworkTestCase(common.BleachbitTestCase):
    """Test case for module Network"""
    status_generator_url = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._httpd = http.server.ThreadingHTTPServer(
            ('127.0.0.1', 0), _StatusCodeHandler)
        cls._server_thread = threading.Thread(
            target=cls._httpd.serve_forever, daemon=True)
        cls._server_thread.start()
        host, port = cls._httpd.server_address
        cls.status_generator_url = f'http://{host}:{port}/status/{{}}'
        logger.info('Local status server: %s', cls.status_generator_url)

    @classmethod
    def tearDownClass(cls):
        cls._httpd.shutdown()
        cls._server_thread.join(timeout=5)
        cls._httpd.server_close()
        super().tearDownClass()

    def test_unset_sslkeylogfile(self):
        """Test the function unset_sslkeylogfile()."""
        with common.set_temporary_env('SSLKEYLOGFILE', 'ssl.log'):
            self.assertEqual(unset_sslkeylogfile(True), IS_WINDOWS)
            self.assertFalse(unset_sslkeylogfile(True))

    def test_download_url_to_fn(self):
        """Unit test for function download_url_to_fn()"""
        # Test different HTTP status codes
        # 200: success
        # 404: not found (non-retryable error)
        # 500: server error (retryable error)
        tests = ((self.status_generator_url.format(200), True),
                 (self.status_generator_url.format(404), False),
                 (self.status_generator_url.format(500), False))
        fn = os.path.join(self.tempdir, 'download')
        on_error_called = [False]

        def on_error(msg1, msg2):
            # Only print a simplified error message to avoid excessive output
            error_type = 'HTTP status' if 'HTTP status code' in str(
                msg2) else 'Connection'
            print(
                f'test on_error: {error_type} error for {msg1.split(":")[-1].strip()}')
            on_error_called[0] = True
        for (url, expected_rc) in tests:
            with self.subTest(url=url, expected_rc=expected_rc):
                self.assertNotExists(fn)
                on_error_called = [False]
                rc = download_url_to_fn(url, fn, None,
                                        on_error=on_error, timeout=20)
                err_msg = f'test_download_url_to_fn({url}) returned {rc} instead of {expected_rc}'
                self.assertEqual(rc, expected_rc, err_msg)
                if expected_rc:
                    self.assertExists(fn)
                self.assertNotEqual(rc, on_error_called[0])
                # minimal parameters
                rc = download_url_to_fn(url, fn)
                self.assertEqual(rc, expected_rc, err_msg)
                delete(fn, ignore_missing=True)

    @common.skipIfWindows
    def test_download_url_to_fn_creates_private_dir(self):
        """download_url_to_fn() must create missing directories mode 0o700"""
        new_dir = os.path.join(self.tempdir, 'not', 'yet', 'created')
        fn = os.path.join(new_dir, 'download')
        self.assertNotExists(new_dir)

        rc = download_url_to_fn(self.status_generator_url.format(200), fn)
        self.assertTrue(rc)
        self.assertExists(fn)
        for created_dir in (new_dir, os.path.dirname(new_dir),
                            os.path.dirname(os.path.dirname(new_dir))):
            mode = os.stat(created_dir).st_mode & 0o777
            self.assertEqual(mode, 0o700,
                             f'{created_dir} has mode {oct(mode)}, expected 0o700')

    def test_download_url_to_fn_refuses_symlink(self):
        """download_url_to_fn() must not write the download through a symlink"""
        filename = self.write_file('download_target', text='keepme')
        fake_response = Mock()
        fake_response.status_code = 200
        fake_response.content = b'attacker payload'
        on_error = Mock()
        # The link is simulated, so delete() would remove the real file
        with patch('bleachbit.Network.fetch_url', return_value=fake_response), \
                patch('bleachbit.FileUtilities.os.path.islink',
                      side_effect=lambda p: p == filename), \
                patch('bleachbit.Network.delete'):
            self.assertFalse(download_url_to_fn(
                'https://example.invalid/x', filename, on_error=on_error))
        on_error.assert_called_once()
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(f.read(), 'keepme')

    def test_download_url_to_fn_write_error(self):
        """A failed write returns False and leaves no partial file"""
        fn = os.path.join(self.tempdir, 'partial')
        fake_response = Mock()
        fake_response.status_code = 200
        fake_response.content = b'complete'
        on_error = Mock()

        def disk_full(path, mode):
            with open(path, mode) as f:
                f.write(b'part')
            raise OSError(errno.ENOSPC, 'No space left on device')

        with patch('bleachbit.Network.fetch_url', return_value=fake_response), \
                patch('bleachbit.Network.open_for_overwrite', side_effect=disk_full):
            self.assertFalse(download_url_to_fn(
                'https://example.invalid/x', fn, on_error=on_error))
        on_error.assert_called_once()
        self.assertNotExists(fn)

    def test_get_gtk_version(self):
        """Unit test for get_gtk_version()"""
        gtk_ver = get_gtk_version()
        if gtk_ver is None:
            self.skipTest("GTK is not installed")
        self.assertIsInstance(gtk_ver, str)
        self.assertRegex(gtk_ver, r"^\d+\.\d+\.\d+$")

    def test_get_ip_for_url(self):
        """Unit test for get_ip_for_url()"""
        for good_url in ('https://www.example.com', bleachbit.update_check_url):
            ip_str = get_ip_for_url(good_url)
            _ = ipaddress.ip_address(ip_str)
        for bad_url in (None, '', 'https://test.invalid'):
            ret = get_ip_for_url(bad_url)
            self.assertEqual(ret[0], '(',
                             f'get_ip_for_url({bad_url})={ret}')

    def test_get_user_agent(self):
        """Unit test for method get_user_agent()"""
        agent = get_user_agent()
        logger.debug("user agent = '%s'", agent)
        self.assertIsString(agent)

    def test_version_major_minor(self):
        """Unit test for _version_major_minor()"""
        cases = (
            ('6.18.50_1', '6.18'),
            ('7.0.12+deb14.1', '7.0'),
            ('6.12.3-061203-generic', '6.12'),
            ('15.1-STABLE', '15.1'),
            ('2026-05-16', '2026-05'),
            ('2026-05', '2026-05'),
            ('20260402', '202604'),
            ('20250302.0.316047', '202503'),
            ('24.10', '24.10'),
            ('6.12', '6.12'),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                self.assertEqual(expected, _version_major_minor(version))

    def test_coarsen_os_version(self):
        """Unit test for _coarsen_os_version()"""
        cases = (
            ('arch 20081221.0.316047', 'arch 200812'),
            ('artix 20081221', 'artix 200812'),
            ('biglinux 2008-12-21', 'biglinux 2008-12'),
            ('endeavouros 2008.12.21', 'endeavouros 2008.12'),
            ('omarchy 4.0.0.r1854.g06e32d2', 'omarchy 4.0'),
            ('opensuse-slowroll 20081221', 'opensuse-slowroll 200812'),
            ('opensuse-tumbleweed 20081221', 'opensuse-tumbleweed 200812'),
            ('ubuntu 24.10', 'ubuntu 24.10'),
            ('Linux 7.0.12+deb14.1 (unknown distribution)', 'Linux 7.0'),
            ('Linux 6.18.50_1 (unknown distribution)', 'Linux 6.18'),
            ('Linux', 'Linux'),
            ('FreeBSD 15.1-STABLE stable/15-n284829-192a5eeab8d1', 'FreeBSD 15.1'),
            ('', ''),
        )
        for os_version, expected in cases:
            with self.subTest(os_version=os_version):
                self.assertEqual(expected,
                                 _coarsen_os_version(os_version))

    def test_coarsen_windows_build(self):
        """Unit test for _coarsen_windows_build()"""
        cases = (
            ('10.0.27999', '10.0.26300'),
            ('10.0.26461', '10.0.26300'),
            ('10.0.22625', '10.0.22621'),
            ('10.0.28000', '10.0.28000'),
            ('10.0.22000', '10.0.22000'),
            ('10.0.19045', '10.0.19045'),
            ('10.0.10240', '10.0.10240'),
            # Future builds beyond the newest known release keep two
            # significant digits
            ('10.0.28001', '10.0.28000'),
            ('10.0.99999', '10.0.99000'),
            ('11.0.100000', '11.0.100000'),
            # Builds below the first known release are unchanged
            ('6.1.7601', '6.1.7601'),
            ('10.0.9', '10.0.9'),
            ('10.0.2660', '10.0.2660'),
            ('10.0', '10.0'),
            ('10.0.26461.foo', '10.0.26461.foo'),
            ('', ''),
        )
        for os_version, expected in cases:
            with self.subTest(os_version=os_version):
                self.assertEqual(expected,
                                 _coarsen_windows_build(os_version))

    def test_fetch_url_nonretry(self):
        """Unit test for fetch_url() without retry"""
        status_codes = (200, 404)
        for status_code in status_codes:
            url = self.status_generator_url.format(status_code)
            with self.subTest(status_code=status_code):
                response = fetch_url(url, max_retries=0, timeout=5)
                error_msg = response_to_error_msg(response)
                self.assertEqual(response.status_code, status_code,
                                 error_msg)

    def test_fetch_url_headers(self):
        """Unit test for fetch_url() header handling"""
        with patch('bleachbit.Network.requests.Session') as mock_session:
            session_instance = MagicMock()
            session_instance.get.return_value = Mock()
            mock_session.return_value.__enter__.return_value = session_instance

            tests = [
                # (custom_headers, expected_custom_key)
                (None, None),
                ({'X-BleachBit-Version': '5.1.0'}, 'X-BleachBit-Version'),
            ]
            for custom_headers, expected_custom_key in tests:
                with self.subTest(custom_headers=custom_headers):
                    response = fetch_url('https://example.com', max_retries=0, timeout=5,
                                         headers=custom_headers)
                    kwargs = session_instance.get.call_args.kwargs
                    headers = kwargs['headers']
                    self.assertEqual(
                        response, session_instance.get.return_value)
                    self.assertIsInstance(headers, dict)
                    self.assertIn('User-Agent', headers)
                    self.assertEqual(headers['User-Agent'], get_user_agent())
                    self.assertNotIn('X-OS-Type', headers)
                    if expected_custom_key:
                        self.assertIn(expected_custom_key, headers)
                        self.assertEqual(headers[expected_custom_key],
                                         custom_headers[expected_custom_key])
                    else:
                        self.assertNotIn('X-BleachBit-Version', headers)

    def test_fetch_url_retry(self):
        """Unit test for fetch_url() with retry"""
        url = self.status_generator_url.format(500)
        with self.assertRaises(requests.exceptions.RetryError):
            fetch_url(url, max_retries=1, timeout=5)

    def test_fetch_url_invalid(self):
        """Unit test for fetch_url() with invalid URL"""
        url = 'https://test.invalid'
        with self.assertRaises(requests.exceptions.RequestException):
            fetch_url(url)


class MissingPackagesTestCase(unittest.TestCase):
    """Test behavior when optional third-party packages are missing."""

    def test_missing_requests(self):
        """Network should be importable without requests."""
        with common.mock_missing_package(
                'requests', 'urllib3',
                clear_prefixes=('bleachbit.Network', 'bleachbit.Update')):
            # `import x.y as Y` is deliberate: mock_missing_package drops the
            # submodule from sys.modules but leaves the parent attribute, so
            # `from x import Y` would hand back the stale module.
            # pylint: disable=consider-using-from-import
            import bleachbit.Network as Network
            self.assertFalse(Network.HAVE_REQUESTS)
            with self.assertRaises(Network.RequestException):
                Network.fetch_url('https://example.com')

    def test_missing_urllib3(self):
        """Missing urllib3 should set HAVE_URLLIB3 to False."""
        with common.mock_missing_package(
                'urllib3',
                clear_prefixes=('bleachbit.Network',)):
            # `import x.y as Y` is deliberate: mock_missing_package drops the
            # submodule from sys.modules but leaves the parent attribute, so
            # `from x import Y` would hand back the stale module.
            # pylint: disable=consider-using-from-import
            import bleachbit.Network as Network
            self.assertFalse(Network.HAVE_URLLIB3)
