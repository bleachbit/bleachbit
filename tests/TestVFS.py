# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for VFS
"""

import os

from tests import common

from bleachbit import IS_POSIX, IS_WINDOWS
from bleachbit.VFS import ListVFS, RealVFS, VFS


class VFSTestCase(common.BleachbitTestCase):
    """Test case for VFS."""

    def test_VFS_abstract(self):
        """Test VFS base class is abstract"""
        vfs = VFS()
        with self.assertRaises(NotImplementedError):
            vfs.listdir('/')
        with self.assertRaises(NotImplementedError):
            vfs.isdir('/')

    def test_RealVFS(self):
        """Test RealVFS against the real filesystem"""
        vfs = RealVFS()
        # Test against the actual root
        self.assertTrue(vfs.isdir('/'))
        root_children = vfs.listdir('/' if IS_POSIX else 'C:\\')
        self.assertIsInstance(root_children, list)
        self.assertGreater(len(root_children), 0)
        self.assertTrue(all(isinstance(child, str) for child in root_children))
        if IS_POSIX:
            self.assertIn('tmp', root_children)
        if IS_WINDOWS:
            self.assertIn('Users', root_children)

        # Test against the temporary directory
        self.assertTrue(vfs.isdir(self.tempdir))
        self.assertFalse(vfs.isdir(os.path.join(self.tempdir, 'nonexistent')))

    def test_ListVFS_basic(self):
        """Test ListVFS with a basic path list"""
        vfs = ListVFS(['/foo/bar', '/foo/baz'])

        self.assertTrue(vfs.isdir('/'))
        self.assertTrue(vfs.isdir('/foo'))
        self.assertFalse(vfs.isdir('/foo/bar'))
        self.assertFalse(vfs.isdir('/foo/baz'))
        self.assertFalse(vfs.isdir('/foo/qux'))

        self.assertEqual(vfs.listdir('/'), ['foo'])
        self.assertEqual(vfs.listdir('/foo'), ['bar', 'baz'])
        with self.assertRaises(NotADirectoryError):
            vfs.listdir('/foo/bar')

    def test_ListVFS_comments_and_blanks(self):
        """Test ListVFS ignores comments and blank lines"""
        vfs = ListVFS(['', '# comment', '/file1'])
        self.assertEqual(vfs.listdir('/'), ['file1'])
        self.assertFalse(vfs.isdir('/file1'))
        self.assertFalse(vfs.isdir('# comment'))

    def test_ListVFS_no_leading_slash(self):
        """Test ListVFS adds leading slash if missing"""
        vfs = ListVFS(['foo/bar'])
        self.assertTrue(vfs.isdir('/foo'))
        self.assertFalse(vfs.isdir('/foo/bar'))

    def test_ListVFS_trailing_slash(self):
        """Test ListVFS handles trailing slashes"""
        vfs = ListVFS(['/foo/bar/'])
        self.assertTrue(vfs.isdir('/foo'))
        self.assertTrue(vfs.isdir('/foo/bar'))
        self.assertEqual(vfs.listdir('/foo'), ['bar'])

    def test_ListVFS_empty_path(self):
        """Test ListVFS with an empty path list"""
        vfs = ListVFS([])
        self.assertTrue(vfs.isdir('/'))
        self.assertEqual(vfs.listdir('/'), [])

    def test_ListVFS_listdir_non_directory(self):
        """Test ListVFS raises for files and non-existent directories"""
        vfs = ListVFS(['/foo/bar'])
        with self.assertRaises(NotADirectoryError):
            vfs.listdir('/foo/bar')
        with self.assertRaises(FileNotFoundError):
            vfs.listdir('/foo/qux')

    def test_ListVFS_isdir_false(self):
        """Test ListVFS.isdir returns False for files and non-existent paths"""
        vfs = ListVFS(['/foo/bar'])
        self.assertFalse(vfs.isdir('/foo/bar'))
        self.assertFalse(vfs.isdir('/foo/qux'))
        self.assertFalse(vfs.isdir('/baz'))
