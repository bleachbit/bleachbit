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
Test case for module Update
"""


from tests import common
import bleachbit
from bleachbit import logger
from bleachbit.Update import check_updates, update_winapp2
import bleachbit.Update

import os
import os.path


class UpdateTestCase(common.BleachbitTestCase):
    """Test case for module Update"""

    def test_check_updates_mock(self):
        """Unit test for function check_updates() using mock"""
        from unittest.mock import Mock, patch
        from bleachbit.Update import check_updates

        wa = '<winapp2 url="http://katana.oooninja.com/bleachbit/winapp2.ini" sha512="ce9e18252f608c8aff28811e372124d29a86404f328d3cd51f1f220578744bb8b15f55549eabfe8f1a80657fc940f6d6deece28e0532b3b0901a4c74110f7ba7"/>'
        update_tests = [
            ('<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
             (('0.8.4', 'http://084'), ('0.8.5beta', 'http://085beta'))),
            ('<updates><stable ver="0.8.4">http://084</stable>%s</updates>' % wa,
             (('0.8.4', 'http://084'), )),
            ('<updates><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
             (('0.8.5beta', 'http://085beta'), )),
            ('<updates></updates>', ())]

        with patch('bleachbit.Update.fetch_url') as mock_fetch:
            # Configure mock responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b''

            for xml, expected in update_tests:
                # Set up mock response content
                mock_response.text = xml
                mock_response.content = xml.encode()
                mock_fetch.return_value = mock_response

                # Run test
                updates = check_updates(True, False, None, None)
                self.assertEqual(updates, expected)

    def test_check_updates_real_network(self):
        """Unit test for function check_updates() using real network"""
        for update in check_updates(True, False, None, None):
            if not update:
                continue
            ver, url = update
            self.assertIsInstance(ver, (type(None), str))
            self.assertIsInstance(url, (type(None), str))

    def test_check_updates_bad_url(self):
        """Unit test for function check_updates() with bad network address"""
        # expect connection failure
        preserve_url = bleachbit.update_check_url
        for url in ('http://localhost/doesnotexist', 'https://httpstat.us/500'):
            bleachbit.update_check_url = url
            self.assertEqual(
                check_updates(True, False, None, None),
                ())
        bleachbit.update_check_url = preserve_url

    def test_update_url(self):
        """Check that the real update URL returns XML"""
        from bleachbit.Network import fetch_url
        response = fetch_url(bleachbit.update_check_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.text.startswith('<?xml version='))
        import xml
        xml.dom.minidom.parseString(response.text)

    def test_update_winapp2(self):
        from bleachbit import personal_cleaners_dir
        fn = os.path.join(personal_cleaners_dir, 'winapp2.ini')
        if os.path.exists(fn):
            logger.info('deleting %s', fn)
            os.unlink(fn)

        url = 'https://download.bleachbit.org/winapp2/winapp2-2021-11-22.ini'

        def expect_failure():
            raise AssertionError('Call should have failed')

        def on_success():
            succeeded['r'] = True

        succeeded = {'r': False}  # scope

        # bad hash
        self.assertRaises(RuntimeError, update_winapp2, url,
                          "notahash", print, expect_failure)

        # blank hash, download file
        update_winapp2(url, None, print, on_success)
        self.assertTrue(succeeded['r'])

        # blank hash, do not download again
        update_winapp2(url, None, print, on_success)
        update_winapp2(url, None, print, expect_failure)

    def test_environment(self):
        """Check the sanity of the environment"""
        import http.client
        self.assertTrue(hasattr(http.client, 'HTTPSConnection'))
