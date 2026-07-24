# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Network
"""

# standard imports
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
import requests

# first party imports
import bleachbit
from tests import common
from bleachbit import IS_WINDOWS
from bleachbit.FileUtilities import delete
from bleachbit.Network import (download_url_to_fn, fetch_url, get_gtk_version,
                               get_ip_for_url, get_user_agent, unset_sslkeylogfile)

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
            import bleachbit.Network as Network
            self.assertFalse(Network.HAVE_REQUESTS)
            with self.assertRaises(Network.RequestException):
                Network.fetch_url('https://example.com')

    def test_missing_urllib3(self):
        """Missing urllib3 should set HAVE_URLLIB3 to False."""
        with common.mock_missing_package(
                'urllib3',
                clear_prefixes=('bleachbit.Network',)):
            import bleachbit.Network as Network
            self.assertFalse(Network.HAVE_URLLIB3)
