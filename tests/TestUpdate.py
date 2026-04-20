# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module Update
"""


from tests import common
import bleachbit
from bleachbit import logger
from bleachbit.Update import check_updates, update_winapp2, user_agent

import mock
import threading
import os
import os.path
import requests


class UpdateTestCase(common.BleachbitTestCase):
    """Test case for module Update"""

    def test_UpdateCheck_fake(self):
        """Unit tests for class UpdateCheck using fake network"""

        wa = '<winapp2 url="http://katana.oooninja.com/bleachbit/winapp2.ini" sha512="ce9e18252f608c8aff28811e372124d29a86404f328d3cd51f1f220578744bb8b15f55549eabfe8f1a80657fc940f6d6deece28e0532b3b0901a4c74110f7ba7"/>'
        update_tests = [
            ('<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
             (('0.8.4', 'http://084'), ('0.8.5beta', 'http://085beta'))),
            ('<updates><stable ver="0.8.4">http://084</stable>%s</updates>' % wa,
             (('0.8.4', 'http://084'), )),
            ('<updates><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
             (('0.8.5beta', 'http://085beta'), )),
            ('<updates></updates>', ())]

        for xml_text, expected in update_tests:
            fake_response = mock.Mock()
            fake_response.text = xml_text
            fake_response.status_code = 200
            with mock.patch('bleachbit.Update.fetch_url', return_value=fake_response):
                updates = check_updates(True, False, None, None)
                self.assertEqual(updates, expected)

    def test_UpdateCheck_real_network(self):
        """Unit tests for class UpdateCheck using real network"""

        # real network
        for update in check_updates(True, False, None, None):
            if not update:
                continue
            ver = update[0]
            url = update[1]
            self.assertIsInstance(ver, (type(None), str))
            self.assertIsInstance(url, (type(None), str))

    def test_check_updates_threaded(self):
        """Test check_update() in thread

        https://github.com/bleachbit/bleachbit/issues/2095"""
        thread = threading.Thread(
            target=check_updates, args=(True, False, None, None))
        thread.start()
        thread.join()

    def test_UpdateCheck_real(self):
        """Unit test for class UpdateCheck with bad network address"""
        # expect connection failure
        preserve_url = bleachbit.update_check_url
        for url in ('http://localhost/doesnotexist',):
            bleachbit.update_check_url = url
            self.assertEqual(
                check_updates(True, False, None, None),
                ())
        bleachbit.update_check_url = preserve_url

    def test_update_url(self):
        """Check connection to the update URL"""
        from bleachbit.Network import fetch_url
        try:
            response = fetch_url(bleachbit.update_check_url)
        except requests.RequestException as e:
            logger.exception('Request error, url: %s', bleachbit.update_check_url)
            raise e
        import xml.dom.minidom
        xml.dom.minidom.parseString(response.text)

    def test_import_requests(self):
        """Test import requests

        https://github.com/bleachbit/bleachbit/issues/2095"""
        import requests

    def test_import_urllib3(self):
        """Import urllib3

        https://github.com/bleachbit/bleachbit/issues/2095"""
        import urllib3

    def test_import_queue(self):
        """Import queue

        https://github.com/bleachbit/bleachbit/issues/2095"""
        import queue

    def test_update_winapp2(self):
        fn = os.path.join(bleachbit.personal_cleaners_dir, 'winapp2.ini')
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

    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        logger.debug("user agent = '%s'", agent)
        self.assertIsString(agent)

    def test_environment(self):
        """Check the sanity of the environment"""
        import http.client
        self.assertTrue(hasattr(http.client, 'HTTPSConnection'))
