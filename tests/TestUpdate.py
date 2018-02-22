# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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


from __future__ import absolute_import, print_function

from tests import common
import bleachbit
from bleachbit import logger
from bleachbit.Update import check_updates, update_winapp2, user_agent
import bleachbit.Update

import os
import os.path


class UpdateTestCase(common.BleachbitTestCase):
    """Test case for module Update"""

    def test_UpdateCheck_fake(self):
        """Unit tests for class UpdateCheck using fake network"""

        wa = '<winapp2 url="http://katana.oooninja.com/bleachbit/winapp2.ini" sha512="ce9e18252f608c8aff28811e372124d29a86404f328d3cd51f1f220578744bb8b15f55549eabfe8f1a80657fc940f6d6deece28e0532b3b0901a4c74110f7ba7"/>'
        update_tests = [
            ('<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
                           ((u'0.8.4', u'http://084'), (u'0.8.5beta', u'http://085beta'))),
            ('<updates><stable ver="0.8.4">http://084</stable>%s</updates>' % wa,
                           ((u'0.8.4', u'http://084'), )),
            ('<updates><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
                           ((u'0.8.5beta', u'http://085beta'), )),
            ('<updates></updates>', ())]

        # fake network
        original_open = bleachbit.Update.build_opener
        xml = ""

        class FakeOpener:
            def add_headers(self):
                pass

            def read(self):
                return xml

            def open(self, url):
                return self

        # TODO: mock
        bleachbit.Update.build_opener = FakeOpener
        for xml, expected in update_tests:
            updates = check_updates(True, False, None, None)
            self.assertEqual(updates, expected)
        bleachbit.Update.build_opener = original_open

    def test_UpdateCheck_real_network(self):
        """Unit tests for class UpdateCheck using real network"""

        # real network
        for update in check_updates(True, False, None, None):
            if not update:
                continue
            ver = update[0]
            url = update[1]
            self.assertIsInstance(ver, (type(None), unicode))
            self.assertIsInstance(url, (type(None), unicode))

    def test_UpdateCheck_real(self):
        """Unit test for class UpdateCheck with bad network address"""
        # expect connection failure
        preserve_url = bleachbit.update_check_url
        bleachbit.update_check_url = "http://localhost/doesnotexist"
        self.assertEqual(
            check_updates(True, False, None, None),
            ())
        bleachbit.update_check_url = preserve_url

    def test_update_url(self):
        """Check connection to the update URL"""
        from bleachbit.Update import build_opener
        opener = build_opener()
        handle = opener.open(bleachbit.update_check_url)
        doc = handle.read()
        import xml
        xml.dom.minidom.parseString(doc)

    def test_update_winapp2(self):
        from bleachbit import personal_cleaners_dir
        fn = os.path.join(personal_cleaners_dir, 'winapp2.ini')
        if os.path.exists(fn):
            logger.info('deleting %s', fn.encode(bleachbit.FSE))
            os.unlink(fn)

        url = 'http://katana.oooninja.com/bleachbit/winapp2/winapp2-2016-03-14.ini'

        def expect_failure():
            raise AssertionError('Call should have failed')

        def on_success():
            succeeded['r'] = True

        succeeded = {'r': False}  # scope

        # bad hash
        self.assertRaises(RuntimeError, update_winapp2, url, "notahash", print, expect_failure)

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
        import httplib
        self.assertTrue(hasattr(httplib, 'HTTPS'))
        import socket
        self.assertTrue(hasattr(socket, 'ssl'))
