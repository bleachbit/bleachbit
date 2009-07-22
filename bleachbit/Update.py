# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
Check for updates via the Internet
"""

import platform
import socket
import sys
import urllib2
import xml.dom.minidom

import Common


def user_agent():
    """Return the user agent string"""
    __platform = platform.system() # Linux or Windows
    __os = platform.uname()[2] # e.g., 2.6.28-12-generic or XP
    if sys.platform == "win32":
        # Python 2.5.4 shows uname()[2) as Vista on Windows 7
        __os = platform.uname()[3][0:3] # 5.1 = Windows XP, 6.0 = Vista, 6.1 = 7
    if sys.platform == 'linux2':
        dist = platform.dist()
        __os = dist[0] + '/' + dist[1] + '-' + dist[2]
    import locale
    __locale = locale.getdefaultlocale()[0] # e.g., en_US

    agent = "BleachBit/%s (%s; %s; %s)" % (Common.APP_VERSION, \
        __platform, __os, __locale)
    return agent


class Update:
    """Check for updates via the Internet"""

    def __init__(self):
        self.update_available = None
        self.update_info_url = None


    def get_update_info_url(self):
        """Return the URL with information about the update.
        If no update is available, URL may be none."""
        return self.update_info_url


    def is_update_available(self):
        """Return boolean whether update is available"""
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', user_agent())]
        socket.setdefaulttimeout(Common.socket_timeout)
        try:
            handle = opener.open(Common.update_check_url)
            dom = xml.dom.minidom.parse(handle)
        except:
            print _("Error when checking for updates: "), str(sys.exc_info()[1])
            return False
        elements = dom.getElementsByTagName("url")
        if 0 == len(elements):
            self.update_available = False
        else:
            self.update_info_url = elements[0].firstChild.data
            self.update_available = True
        dom.unlink()
        return self.update_available

import unittest

class TestUpdate(unittest.TestCase):
    """Unit tests for module Update"""


    def test_Update(self):
        """Unit tests for class Update"""
        update = Update()
        available = update.is_update_available()
        print "Update available = ", available
        self.assert_ (type(available) is bool)

        # test failure
        Common.update_check_url = "http://www.surelydoesnotexist.com/foo"
        self.assertEqual(update.is_update_available(), False)


    def test_user_agent(self):
        """Unit test for method user_agent()"""
        agent = user_agent()
        print "debug: user agent = '%s'" % (agent, )
        self.assert_ (type(agent) is str)


if __name__ == '__main__':
    unittest.main()

