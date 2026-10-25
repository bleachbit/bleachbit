# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Scan directory tree for files to delete
"""

import logging
import os
import re
import subprocess
import time
import unicodedata
from collections import namedtuple
from bleachbit import FS_SCAN_RE_FLAGS, IS_FREEBSD, IS_LINUX, IS_MAC
from . import Command
from .FileUtilities import is_normal_directory, openfiles, whitelisted


def normalized_walk(top, **kwargs):
    """
    macOS uses decomposed UTF-8 to store filenames. This functions
    is like `os.walk` but recomposes those decomposed filenames on
    macOS
    """
    if IS_MAC:
        for dirpath, dirnames, filenames in os.walk(top, **kwargs):
            yield dirpath, dirnames, [
                unicodedata.normalize('NFC', fn)
                for fn in filenames
            ]
    else:
        yield from os.walk(top, **kwargs)


def _is_open(path):
    """Return whether a process holds path open, or True if that is unknown"""
    try:
        return openfiles.is_open(path)
    except (OSError, subprocess.CalledProcessError) as e:
        logging.getLogger(__name__).warning(
            'Keeping %s because open files cannot be listed: %s', path, e)
        return True


Search = namedtuple(
    'Search', ['command', 'regex', 'nregex', 'wholeregex', 'nwholeregex',
               'skip_open'])
Search.__new__.__defaults__ = (None,) * len(Search._fields)


def directory_prefix(dirpath):
    """Return a prefix such that prefix + filename == os.path.join(dirpath, filename).

    Uses os.path.join(dirpath, '') for the common case. Bare UNC roots like
    \\\\server\\share are special: join(dir, '') does not add a separator, but
    join(dir, name) still inserts one.
    """
    prefix = os.path.join(dirpath, '')
    if prefix == dirpath:
        # join was a no-op (e.g. 'C:' or a bare UNC share). Probe whether a
        # real filename would insert a separator that concatenation would miss.
        probe = os.path.join(dirpath, 'a')
        if probe != dirpath + 'a':
            return probe[:-1]
    return prefix


class CompiledSearch:
    """Compiled search condition"""

    def __init__(self, search):
        self.command = search.command

        def re_compile(regex):
            return re.compile(regex, FS_SCAN_RE_FLAGS) if regex else None

        self.regex = re_compile(search.regex)
        self.nregex = re_compile(search.nregex)
        self.wholeregex = re_compile(search.wholeregex)
        self.nwholeregex = re_compile(search.nwholeregex)
        # open_files() supports only these platforms
        self.skip_open = bool(search.skip_open) and (
            IS_LINUX or IS_MAC or IS_FREEBSD)

    def match(self, dirpath, filename, path_prefix=None):
        if self.regex and not self.regex.search(filename):
            return None

        if self.nregex and self.nregex.search(filename):
            return None

        if path_prefix is None:
            full_path = os.path.join(dirpath, filename)
        else:
            full_path = path_prefix + filename

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
        yield_time = time.time()

        for (top, searches) in self.searches.items():
            # This skips top-level directories that are in the keep list
            # to reduce unnecessary work.
            if whitelisted(top):
                continue
            compiled_searches = [CompiledSearch(s) for s in searches]
            for (dirpath, dirnames, filenames) in normalized_walk(top):
                # Prune keep-list dirs, symlinks, and reparse points:
                # os.walk's followlinks=False skips POSIX links but not
                # junctions, which would otherwise redirect the scan.
                kept_dirs = []
                for dirname in dirnames:
                    subdir = os.path.join(dirpath, dirname)
                    if not whitelisted(subdir) and is_normal_directory(subdir):
                        kept_dirs.append(dirname)
                dirnames[:] = kept_dirs
                path_prefix = directory_prefix(dirpath)
                for c in compiled_searches:
                    # fixme, don't match filename twice
                    for filename in filenames:
                        full_name = c.match(dirpath, filename, path_prefix)
                        if full_name is None:
                            continue
                        if c.skip_open and _is_open(full_name):
                            continue
                        # fixme: support other commands
                        if c.command == 'delete':
                            yield Command.Delete(full_name)
                        elif c.command == 'shred':
                            yield Command.Shred(full_name)

                if time.time() - yield_time > 0.25:
                    # allow GTK+ to process the idle loop
                    yield True
                    yield_time = time.time()
