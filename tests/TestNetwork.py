# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module Network
"""

# standard library
import ipaddress
import logging
import os
import random

# third party
import mock
import requests

# first party imports
import bleachbit
from tests import common
from bleachbit.FileUtilities import delete
from bleachbit.Network import (download_url_to_fn, fetch_url, get_gtk_version,
                               get_ip_for_url, get_user_agent, unset_sslkeylogfile)

logger = logging.getLogger(__name__)


def response_to_error_msg(response):
    """Convert response to error message"""
    return "URL: {url}\n" + \
           "Status: %s %s\n" % (response.status_code, response.reason) + \
           "Response headers: %s\n" % dict(response.headers) + \
           "Response content: %s" % response.text


class NetworkTestCase(common.BleachbitTestCase):
    """Test case for module Network"""
    status_generators = [
        'https://httpbin.org/status/{}',
        'https://httpbingo.org/status/{}',
        'https://mock.httpstatus.io/{}',
        'https://postman-echo.com/status/{}',
        'https://the-internet.herokuapp.com/status_codes/{}'
    ]
    status_generator_url = None

    @classmethod
    def setUpClass(cls):
        super(NetworkTestCase, cls).setUpClass()
        status_generators = list(cls.status_generators)
        random.shuffle(status_generators)
        for generator in status_generators:
            url = generator.format(200)
            try:
                response = fetch_url(url, timeout=5, max_retries=0)
                if response.status_code == 200:
                    cls.status_generator_url = generator
                    logger.info('Using status generator: %s',
                                cls.status_generator_url)
                    return
                else:
                    logger.warning('Status generator %s returned %s',
                                   generator, response.status_code)
            except requests.exceptions.RequestException as e:
                logger.warning('Status generator failed: %s (%s)',
                               generator.format('...'), e)
        if not cls.status_generator_url:
            raise RuntimeError('No working HTTP status code generator found.')

    def setUp(self):
        """Set up the test environment before each test method."""
        super(NetworkTestCase, self).setUp()
        os.environ['SSLKEYLOGFILE'] = 'ssl.log'

    def test_unset_sslkeylogfile(self):
        """Test the function unset_sslkeylogfile()."""
        # SSLKEYLOGFILE is set in setUp().
        self.assertEqual(unset_sslkeylogfile(True), os.name == 'nt')
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
            print('test on_error: %s error for %s' %
                  (error_type, msg1.split(':')[-1].strip()))
            on_error_called[0] = True
        for (url, expected_rc) in tests:
            with self.subTest(url=url, expected_rc=expected_rc):
                self.assertNotExists(fn)
                on_error_called = [False]
                rc = download_url_to_fn(url, fn, None,
                                        on_error=on_error, timeout=20)
                err_msg = 'test_download_url_to_fn(%s) returned %s instead of %s' % (
                    url, rc, expected_rc)
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
            ipaddress.ip_address(ip_str)
        for bad_url in (None, '', 'https://test.invalid'):
            ret = get_ip_for_url(bad_url)
            self.assertEqual(ret[0], '(',
                             'get_ip_for_url(%s)=%s' % (bad_url, ret))

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
        with mock.patch('bleachbit.Network.requests.Session') as mock_session:
            session_instance = mock.MagicMock()
            session_instance.get.return_value = mock.Mock()
            mock_session.return_value.__enter__ = mock.Mock(
                return_value=session_instance)
            mock_session.return_value.__exit__ = mock.Mock(
                return_value=False)

            tests = [
                # (custom_headers, expected_custom_key)
                (None, None),
                ({'X-BleachBit-Version': '5.1.0'}, 'X-BleachBit-Version'),
            ]
            for custom_headers, expected_custom_key in tests:
                with self.subTest(custom_headers=custom_headers):
                    response = fetch_url('https://example.com', max_retries=0, timeout=5,
                                         headers=custom_headers)
                    # Python 3.4: use call_args[1] instead of call_args.kwargs
                    kwargs = session_instance.get.call_args[1]
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
        try:
            fetch_url(url, max_retries=1, timeout=5)
        except requests.exceptions.RetryError:
            return
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as exc:
            self.skipTest("Status generator unavailable (%s)" % exc)
        self.fail('fetch_url() did not raise RetryError for HTTP 500 response')

    def test_fetch_url_invalid(self):
        """Unit test for fetch_url() with invalid URL"""
        url = 'https://test.invalid'
        with self.assertRaises(requests.exceptions.RequestException):
            fetch_url(url)
