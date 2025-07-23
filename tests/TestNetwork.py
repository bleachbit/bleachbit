# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Test case for module Network
"""

import ipaddress
import logging
import os
import random
import requests

import bleachbit
from tests import common
from bleachbit.FileUtilities import delete
from bleachbit.Network import (download_url_to_fn, fetch_url, get_gtk_version,
                               get_ip_for_url, get_user_agent)

logger = logging.getLogger(__name__)


def response_to_error_msg(response):
    """Convert response to error message"""
    return "URL: {url}\n" + \
           f"Status: {response.status_code} {response.reason}\n" + \
           f"Response headers: {dict(response.headers)}\n" + \
           f"Response content: {response.text}"


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

    def test_fetch_url_retry(self):
        """Unit test for fetch_url() with retry"""
        url = self.status_generator_url.format(500)
        with self.assertRaises(requests.exceptions.RetryError):
            fetch_url(url, max_retries=1, timeout=2)

    def test_fetch_url_invalid(self):
        """Unit test for fetch_url() with invalid URL"""
        url = 'https://test.invalid'
        with self.assertRaises(requests.exceptions.RequestException):
            fetch_url(url)
