# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
Scan directory tree for files to delete
"""

from __future__ import absolute_import, print_function

import bleachbit

import logging
import os
import platform
import re
import unicodedata


UTF8 = 'utf-8'


def to_unicode(s):
    """
    Converts non-unicode UTF-8 string to unicode obj. Does nothing if
    string is already unicode.
    """
    return s if isinstance(s, unicode) else unicode(s, UTF8)


def normalized_walk(top, **kwargs):
    """
    macOS uses decomposed UTF-8 to store filenames. This functions
    is like `os.walk` but recomposes those decomposed filenames on
    macOS
    """
    if 'Darwin' == platform.system():
        for dirpath, dirnames, filenames in os.walk(top, **kwargs):
            yield dirpath, dirnames, [
                unicodedata.normalize('NFC', to_unicode(fn)).encode(UTF8)
                for fn in filenames
            ]
    else:
        for result in os.walk(top, **kwargs):
            yield result


class DeepScan:

    """Advanced directory tree scan"""

    def __init__(self):
        self.roots = []
        self.searches = {}

    def add_search(self, dirname, regex):
        """Starting in dirname, look for files matching regex"""
        if dirname not in self.searches:
            self.searches[dirname] = [regex]
        else:
            self.searches[dirname].append(regex)

    def scan(self):
        """Perform requested searches and yield each match"""
        logging.getLogger(__name__).debug('DeepScan.scan: searches=%s', str(self.searches))
        import time
        yield_time = time.time()

        for (top, regexes) in self.searches.items():
            for (dirpath, dirnames, filenames) in normalized_walk(top):
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
