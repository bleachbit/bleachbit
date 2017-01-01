# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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


from __future__ import print_function

"""
Test case for module Update
"""


import os
import os.path
import sys
import unittest

sys.path.append('.')
from bleachbit import Common
from bleachbit.Common import logger
from bleachbit.Update import check_updates, update_winapp2, user_agent
import bleachbit.Update

class UpdateTestCase(unittest.TestCase):

    """Test case for module Update"""

    def test_UpdateCheck_fake(self):
        """Unit tests for class UpdateCheck using fake network"""

        update_tests = []
        wa = '<winapp2 url="http://katana.oooninja.com/bleachbit/winapp2.ini" sha512="ce9e18252f608c8aff28811e372124d29a86404f328d3cd51f1f220578744bb8b15f55549eabfe8f1a80657fc940f6d6deece28e0532b3b0901a4c74110f7ba7"/>'
        update_tests.append(
            ('<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
                           ((u'0.8.4', u'http://084'), (u'0.8.5beta', u'http://085beta'))))
        update_tests.append(
            ('<updates><stable ver="0.8.4">http://084</stable>%s</updates>' % wa,
                           ((u'0.8.4', u'http://084'), )))
        update_tests.append(
            ('<updates><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa,
                           ((u'0.8.5beta', u'http://085beta'), )))
        update_tests.append(('<updates></updates>', ()))

        # fake network
        original_open = bleachbit.Update.build_opener
        xml = ""

        class fake_opener:

            def add_headers(self):
                pass

            def read(self):
                return xml

            def open(self, url):
                return self

        bleachbit.Update.build_opener = fake_opener
        for update_test in update_tests:
            xml = update_test[0]
            updates = check_updates(True, False, None, None)
            self.assertEqual(updates, update_test[1])
        bleachbit.Update.build_opener = original_open


    def test_UpdateCheck_real(self):
        """Unit tests for class UpdateCheck using real network"""

        # real network
        for update in check_updates(True, False, None, None):
            if not update:
                continue
            ver = update[0]
            url = update[1]
            self.assert_(isinstance(ver, (type(None), unicode)))
            self.assert_(isinstance(url, (type(None), unicode)))

    def test_UpdateCheck_real(self):
        """Unit test for class UpdateCheck with bad network address"""
        # expect connection failure
        Common.update_check_url = "http://localhost/doesnotexist"
        self.assertEqual(
            check_updates(True, False, None, None),
            ())

    def test_update_winapp2(self):
        from bleachbit.Common import personal_cleaners_dir
        fn = os.path.join(personal_cleaners_dir, 'winapp2.ini')
        if os.path.exists(fn):
            logger.info('deleting %s', fn.encode(Common.FSE))
            os.unlink(fn)

        url = 'http://katana.oooninja.com/bleachbit/winapp2/winapp2-2016-03-14.ini'

        def append_text(s):
            print(s)

        succeeded = {'r': False}  # scope

        def on_success():
            succeeded['r'] = True

        # bad hash
        succeeded['r'] = False
        self.assertRaises(RuntimeError, update_winapp2, url, "notahash",
                          append_text, on_success)
        self.assert_(not succeeded['r'])

        # blank hash, download file
        succeeded['r'] = False
        update_winapp2(url, None, append_text, on_success)
        self.assert_(succeeded['r'])

        # blank hash, do not download again
        update_winapp2(url, None, append_text, on_success)
        succeeded['r'] = False
        update_winapp2(url, None, append_text, on_success)
        self.assert_(not succeeded['r'])

    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        logger.debug("user agent = '%s'", agent)
        self.assert_(isinstance(agent, str))

    def test_environment(self):
        """"Check the sanity of the environment"""
        import httplib
        self.assertTrue(hasattr(httplib, 'HTTPS'))
        import socket
        self.assertTrue(hasattr(socket, 'ssl'))
        import _ssl


def suite():
    return unittest.makeSuite(UpdateTestCase)


if __name__ == '__main__':
    unittest.main()
