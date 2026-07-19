# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Virtual File System abstraction for testing filesystem traversal
without requiring real files and directories.
"""

import os


class VFS:
    """Abstract base class for virtual file systems"""

    def listdir(self, path):
        """Return a list of the entries in the directory given by path"""
        raise NotImplementedError

    def isdir(self, path):
        """Return True if path is an existing directory"""
        raise NotImplementedError


class RealVFS(VFS):
    """Pass-through to the real filesystem"""

    def listdir(self, path):
        return os.listdir(path)

    def isdir(self, path):
        return os.path.isdir(path)


class ListVFS(VFS):
    """Virtual filesystem built from a flat list of full paths.

    Derives directory structure automatically.  Any path prefix that
    appears as a parent of another path is treated as a directory.
    Leaf paths (with no children in the list) are treated as files,
    unless they end with a slash.
    """

    def __init__(self, paths):
        self._dirs = {'/'}
        self._files = set()
        self._children = {}  # parent_dir -> set of child names

        for path in paths:
            path = path.strip()
            if not path or path.startswith('#'):
                continue
            is_dir = path.endswith('/')
            path = path.rstrip('/')
            if not path:
                continue
            if not path.startswith('/'):
                path = '/' + path

            parts = path.split('/')
            # parts[0] is '' because path starts with '/'
            for i in range(2, len(parts) + 1):
                current = '/'.join(parts[:i])
                parent = '/'.join(parts[:i - 1]) or '/'
                child_name = parts[i - 1]
                self._children.setdefault(parent, set()).add(child_name)
                if i < len(parts) or is_dir:
                    self._dirs.add(current)
                    self._files.discard(current)
                elif current not in self._dirs:
                    self._files.add(current)

    def listdir(self, path):
        path = path.rstrip('/')
        if path == '':
            path = '/'
        if path in self._files:
            raise NotADirectoryError(f"Not a directory: {path}")
        if path not in self._dirs:
            raise FileNotFoundError(f"No such directory: {path}")
        return sorted(self._children.get(path, set()))

    def isdir(self, path):
        path = path.rstrip('/')
        if path == '':
            path = '/'
        return path in self._dirs
