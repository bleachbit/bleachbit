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


import platform
import socket
import sys
import urllib2
import xml.dom.minidom

from globals import *

def user_agent():
    """Return the user agent string"""
    ver = APP_VERSION
    __platform = platform.system()
    __os = platform.uname()[2]
    cpu = platform.machine()
    lang = 'en-US'
    agent = "BleachBit/%s (%s; %s, %s; %s)" % (ver, __platform, __os, cpu, lang)
    return agent


class Update:
    """Check for updates via the Internet"""

    def __init__(self):
        self.update_available = None
        self.update_url = None


    def get_update_url(self):
        """Return the URL with information about the update.  
        If no update is available, URL may be none."""
        return self.update_url


    def is_update_available(self):
        """Return boolean whether update is available"""
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', user_agent())]
        socket.setdefaulttimeout(socket_timeout)
        try:
            handle = opener.open(update_url)
            dom = xml.dom.minidom.parse(handle)
        except:
            print _("Error when checking for updates: "), str(sys.exc_info()[1])
            return False
        elements = dom.getElementsByTagName("url")
        if 0 == len(elements):
            self.update_available = False
        else:
            self.update_url = elements[0].firstChild.data
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

if __name__ == '__main__':
    unittest.main()

