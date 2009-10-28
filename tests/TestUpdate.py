# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
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


import sys
import unittest
import urllib2

sys.path.append('.')
from bleachbit import Common
from bleachbit.Update import Update, user_agent



class UpdateTestCase(unittest.TestCase):
    """Test case for module Update"""


    def test_Update(self):
        """Unit tests for class Update"""
        update = Update()
        available = update.is_update_available()
        print "Update available = ", available
        self.assert_ (type(available) is bool)

        # test failure
        Common.update_check_url = "http://www.surelydoesnotexist.com/foo"
        self.assertRaises(urllib2.URLError, update.is_update_available)


    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        print "debug: user agent = '%s'" % (agent, )
        self.assert_ (type(agent) is str)



def suite():
    return unittest.makeSuite(UpdateTestCase)


if __name__ == '__main__':
    unittest.main()

