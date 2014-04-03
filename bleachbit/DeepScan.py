# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Scan directory tree for files to delete
"""


import os
import re


class DeepScan:

    """Advanced directory tree scan"""

    def __init__(self):
        self.roots = []
        self.searches = {}

    def add_search(self, dirname, regex):
        """Starting in dirname, look for files matching regex"""
        if not self.searches.has_key(dirname):
            self.searches[dirname] = [regex]
        else:
            self.searches[dirname].append(regex)

    def scan(self):
        """Perform requested searches and yield each match"""
        print 'debug: DeepScan.scan: searches=', self.searches
        import time
        yield_time = time.time()

        for (top, regexes) in self.searches.iteritems():
            for (dirpath, dirnames, filenames) in os.walk(top):
                for regex in regexes:
                    # fixme, don't match filename twice
                    r = re.compile(regex)
                    for filename in filenames:
                        if r.search(filename):
                            yield os.path.join(dirpath, filename)
                if time.time() - yield_time > 0.25:
                    # allow GTK+ to process the idle loop
                    yield True
                    yield_time = time.time()
