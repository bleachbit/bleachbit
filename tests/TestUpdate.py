# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2013 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Test case for module Update
"""


import os
import os.path
import socket
import sys
import types
import unittest
import urllib2

sys.path.append('.')
from bleachbit import Common
from bleachbit.Update import check_updates, update_winapp2, user_agent



class UpdateTestCase(unittest.TestCase):
    """Test case for module Update"""


    def test_UpdateCheck(self):
        """Unit tests for class UpdateCheck"""

        update_tests = []
        wa = '<winapp2 url="http://katana.oooninja.com/bleachbit/winapp2.ini" sha512="ce9e18252f608c8aff28811e372124d29a86404f328d3cd51f1f220578744bb8b15f55549eabfe8f1a80657fc940f6d6deece28e0532b3b0901a4c74110f7ba7"/>'
        update_tests.append( ( '<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa, \
            ( (u'0.8.4', u'http://084') , (u'0.8.5beta', u'http://085beta'))) )
        update_tests.append( ('<updates><stable ver="0.8.4">http://084</stable>%s</updates>' % wa, \
            ( (u'0.8.4', u'http://084') , ) ) )
        update_tests.append( ('<updates><beta ver="0.8.5beta">http://085beta</beta>%s</updates>' % wa, \
            ( (u'0.8.5beta', u'http://085beta') , ) ) )
        update_tests.append( ('<updates></updates>', ()) )

        # fake network
        original_open = urllib2.build_opener
        xml = ""
        class fake_opener:

            def add_headers(self):
                pass

            def read(self):
                return xml

            def open(self, url):
                return self

        urllib2.build_opener = fake_opener
        for update_test in update_tests:
            xml = update_test[0]
            updates = check_updates(True, False, None)
            self.assertEqual(updates, update_test[1])
        urllib2.build_opener = original_open

        # real network
        for update in check_updates(True, False, None):
            if not update:
                continue
            ver = update[0]
            url = update[1]
            self.assert_(isinstance(ver, (types.NoneType, unicode)))
            self.assert_(isinstance(url, (types.NoneType, unicode)))

        # test failure
        Common.update_check_url = "http://localhost/doesnotexist"
        self.assertRaises(urllib2.URLError, check_updates, True, False, None)


    def test_update_winapp2(self):
        from bleachbit.Common import personal_cleaners_dir
        fn = os.path.join(personal_cleaners_dir, 'winapp2.ini')
        if os.path.exists(fn):
            print 'note: deleting %s' % fn
            os.unlink(fn)

        url = 'http://www.winapp2.com/Winapp2.ini'

        def append_text(s):
            print s

        # bad hash
        self.assertRaises(RuntimeError, update_winapp2, url, "notahash", append_text)

        # blank hash, download file
        update_winapp2(url, None, append_text)

        # blank hash, overwrite file
        update_winapp2(url, None, append_text)


    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        print "debug: user agent = '%s'" % (agent, )
        self.assert_ (type(agent) is str)



def suite():
    return unittest.makeSuite(UpdateTestCase)


if __name__ == '__main__':
    unittest.main()

