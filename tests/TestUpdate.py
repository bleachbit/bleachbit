# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
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


import socket
import sys
import types
import unittest
import urllib2

sys.path.append('.')
from bleachbit import Common
from bleachbit.Update import check_updates, user_agent



class UpdateTestCase(unittest.TestCase):
    """Test case for module Update"""


    def test_UpdateCheck(self):
        """Unit tests for class UpdateCheck"""

        update_tests = []
        update_tests.append( ( '<updates><stable ver="0.8.4">http://084</stable><beta ver="0.8.5beta">http://085beta</beta></updates>', \
            ( (u'0.8.4', u'http://084') , (u'0.8.5beta', u'http://085beta'))) )
        update_tests.append( ('<updates><stable ver="0.8.4">http://084</stable></updates>', \
            ( (u'0.8.4', u'http://084') , ) ) )
        update_tests.append( ('<updates><beta ver="0.8.5beta">http://085beta</beta></updates>', \
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
            updates = check_updates(True)
            self.assertEqual(updates, update_test[1])
        urllib2.build_opener = original_open

        # real network
        for update in check_updates(True):
            if not update:
                continue
            ver = update[0]
            url = update[1]
            self.assert_(isinstance(ver, (types.NoneType, unicode)))
            self.assert_(isinstance(url, (types.NoneType, unicode)))

        # test failure
        Common.update_check_url = "http://localhost/doesnotexist"
        self.assertRaises(urllib2.URLError, check_updates, True)


    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        print "debug: user agent = '%s'" % (agent, )
        self.assert_ (type(agent) is str)



def suite():
    return unittest.makeSuite(UpdateTestCase)


if __name__ == '__main__':
    unittest.main()

