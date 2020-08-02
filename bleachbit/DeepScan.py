# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
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

import logging
import os
import platform
import re
import unicodedata
from collections import namedtuple
from bleachbit import fs_scan_re_flags
from . import Command

def normalized_walk(top, **kwargs):
    """
    macOS uses decomposed UTF-8 to store filenames. This functions
    is like `os.walk` but recomposes those decomposed filenames on
    macOS
    """
    try:
        from scandir import walk
    except:
        # there is a warning in FileUtilities, so don't warn again here
        from os import walk
    if 'Darwin' == platform.system():
        for dirpath, dirnames, filenames in walk(top, **kwargs):
            yield dirpath, dirnames, [
                unicodedata.normalize('NFC', fn)
                for fn in filenames
            ]
    else:
        for result in walk(top, **kwargs):
            yield result


Search = namedtuple('Search', ['command', 'regex', 'nregex', 'wholeregex', 'nwholeregex'])
Search.__new__.__defaults__ = (None,) * len(Search._fields)

class CompiledSearch:
    """Compiled search condition"""
    def __init__(self, search):
        self.command = search.command

        def re_compile(regex):
            return re.compile(regex, fs_scan_re_flags) if regex else None

        self.regex = re_compile(search.regex)
        self.nregex = re_compile(search.nregex)
        self.wholeregex = re_compile(search.wholeregex)
        self.nwholeregex = re_compile(search.nwholeregex)

    def match(self, dirpath, filename):
        full_path = os.path.join(dirpath, filename)

        if self.regex and not self.regex.search(filename):
            return None

        if self.nregex and self.nregex.search(filename):
            return None

        if self.wholeregex and not self.wholeregex.search(full_path):
            return None

        if self.nwholeregex and self.nwholeregex.search(full_path):
            return None

        return full_path

class DeepScan:

    """Advanced directory tree scan"""

    def __init__(self, searches):
        self.roots = []
        self.searches = searches

    def scan(self):
        """Perform requested searches and yield each match"""
        logging.getLogger(__name__).debug(
            'DeepScan.scan: searches=%s', str(self.searches))
        import time
        yield_time = time.time()

        for (top, searches) in self.searches.items():
            compiled_searches = []
            for s in searches:
                compiled_searches.append(CompiledSearch(s))

            for (dirpath, dirnames, filenames) in normalized_walk(top):
                for c in compiled_searches:
                    # fixme, don't match filename twice
                    for filename in filenames:
                        full_name = c.match(dirpath, filename)
                        if full_name is not None:
                            # fixme: support other commands
                            if c.command == 'delete':
                                yield Command.Delete(full_name)
                            elif c.command == 'shred':
                                yield Command.Shred(full_name)

                if time.time() - yield_time > 0.25:
                    # allow GTK+ to process the idle loop
                    yield True
                    yield_time = time.time()
