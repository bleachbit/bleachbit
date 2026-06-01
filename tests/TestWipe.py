# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Wipe
"""

import errno
import os
import unittest
from unittest import mock

import bleachbit
from bleachbit.Options import options
from bleachbit import Wipe
from bleachbit.Wipe import (
    detect_orphaned_wipe_files,
    sync,
    wipe_contents,
    wipe_path,
    wipe_name
)
from tests import common


class WipeTestCase(common.BleachbitTestCase):

    def test_detect_orphaned_wipe_files(self):
        """Unit test for detect_orphaned_wipe_files()"""
        # Save original shred_drives
        original_drives = options.get_list('shred_drives')

        # Set shred_drives to include our temp directory
        options.set_list('shred_drives', [self.tempdir])

        try:
            # Test 1: No orphaned files initially
            orphaned = detect_orphaned_wipe_files()
            self.assertEqual(orphaned, [])

            # Test 2: Create a file that matches criteria
            # Must start with 'empty_', >100 chars, no extension, contain null bytes
            long_suffix = 'a' * 120
            orphan_name = 'empty_' + long_suffix
            orphan_path = os.path.join(self.tempdir, orphan_name)
            with open(orphan_path, 'wb') as f:
                f.write(b'\x00' * 1000)

            orphaned = detect_orphaned_wipe_files()
            self.assertEqual(len(orphaned), 1)
            self.assertEqual(orphaned[0], orphan_path)

            # Test 3: File with extension should NOT be detected
            with_ext_path = os.path.join(self.tempdir, orphan_name + '.txt')
            with open(with_ext_path, 'wb') as f:
                f.write(b'\x00' * 1000)

            orphaned = detect_orphaned_wipe_files()
            self.assertEqual(len(orphaned), 1)  # Still just the original

            # Test 4: Short filename should NOT be detected
            short_name = 'empty_short'
            short_path = os.path.join(self.tempdir, short_name)
            with open(short_path, 'wb') as f:
                f.write(b'\x00' * 1000)

            orphaned = detect_orphaned_wipe_files()
            self.assertEqual(len(orphaned), 1)  # Still just the original

            # Test 5: File without null bytes should NOT be detected
            no_null_path = os.path.join(self.tempdir, 'empty_' + 'b' * 120)
            with open(no_null_path, 'wb') as f:
                f.write(b'x' * 1000)

            orphaned = detect_orphaned_wipe_files()
            self.assertEqual(len(orphaned), 1)  # Still just the original

        finally:
            # Restore original shred_drives
            if original_drives:
                options.set_list('shred_drives', original_drives)

    def test_sync(self):
        """Unit test for sync()"""
        sync()

    def test_wipe_contents(self):
        """Unit test for wipe_delete()"""

        # create test file
        filename = self.write_file(
            'bleachbit-test-wipe', b'abcdefghij' * 12345)

        # wipe it
        wipe_contents(filename)

        # check it
        f = open(filename, 'rb')
        while True:
            byte = f.read(1)
            if b"" == byte:
                break
            self.assertEqual(byte, 0)
        f.close()

        # clean up
        os.remove(filename)

    def wipe_name_helper(self, filename):
        """Helper for test_wipe_name()"""

        self.assertExists(filename)

        # test
        newname = wipe_name(filename)
        self.assertEqual(len(filename), len(newname))
        self.assertNotExists(filename)
        self.assertExists(newname)

        # clean
        os.remove(newname)
        self.assertNotExists(newname)

    def test_wipe_name(self):
        """Unit test for wipe_name()"""

        # create test file with moderately long name
        filename = self.write_file('bleachbit-test-wipe' + '0' * 50)
        self.wipe_name_helper(filename)

        # create file with short name in temporary directory with long name
        if 'nt' == os.name:
            # In Windows, the maximum path length is 260 characters
            # http://msdn.microsoft.com/en-us/library/aa365247%28VS.85%29.aspx#maxpath
            dir0len = 100
            dir1len = 5
        else:
            dir0len = 210
            dir1len = 210
        filelen = 10

        dir0 = self.mkdtemp(prefix="0" * dir0len)
        self.assertExists(dir0)

        dir1 = self.mkdtemp(prefix="1" * dir1len, dir=dir0)
        self.assertExists(dir1)

        filename = self.write_file(os.path.join(dir1, '2' * filelen))
        self.wipe_name_helper(filename)
        self.assertExists(dir0)
        self.assertExists(dir1)

        # wipe a directory name
        dir1new = wipe_name(dir1)
        self.assertEqual(len(dir1), len(dir1new))
        self.assertNotExists(dir1)
        self.assertExists(dir1new)
        os.rmdir(dir1new)

        # wipe the directory
        os.rmdir(dir0)
        self.assertNotExists(dir0)

    def test_wipe_name_when_basic_characters_exist(self):
        """Unit test for wipe_name() when basic characters exist"""
        testdir = self.mkdtemp()
        filenames = []
        # This tests that FILENAME_CHARS characters are valid for filenames.
        for char in Wipe.FILENAME_CHARS:
            if char == '.':
                continue
            filename = os.path.join(testdir, char)
            self.write_file(filename)
            self.assertExists(filename)
            filenames.append(filename)

        # Verify that FILENAME_CHARS contains uppercase letters on case-sensitive
        # file systems, and that all test filenames are unique (case-insensitively)
        # on case-insensitive file systems to avoid collisions.
        if bleachbit.FS_CASE_SENSITIVE:
            self.assertTrue(any(char.isupper()
                            for char in Wipe.FILENAME_CHARS))
        else:
            basenames = [os.path.basename(filename) for filename in filenames]
            self.assertEqual(len(basenames), len(
                set(name.lower() for name in basenames)))

        filename = filenames[0]
        newname = wipe_name(filename)
        self.assertEqual(filename, newname)
        self.assertExists(newname)

    def test_wipe_name_rejects_windows_invalid_names(self):
        """Unit test for wipe_name() with Windows-invalid names"""
        filename = self.write_file('orig')
        expected = os.path.join(self.tempdir, 'good')

        bad_list = ['bad.', 'bad ', 'COM1', 'bad?']
        with mock.patch.object(Wipe, 'IS_WINDOWS', True), \
                mock.patch.object(
                    Wipe,
                    '__random_string',
                    side_effect=bad_list + ['good']):
            newname = wipe_name(filename)

        self.assertEqual(expected, newname)
        self.assertNotExists(filename)
        for bad_item in bad_list:
            self.assertNotExists(os.path.join(self.tempdir, bad_item))
        self.assertExists(newname)

    @common.skipIfWindows
    def test_wipe_name_allows_windows_reserved_names_on_linux(self):
        """Unit test for wipe_name() with Windows-reserved names on Linux"""
        filename = self.write_file('abc')
        expected = os.path.join(self.tempdir, 'CON')

        with mock.patch.object(Wipe, '__random_string', return_value='CON'):
            newname = wipe_name(filename)

        self.assertEqual(expected, newname)
        self.assertNotExists(filename)
        self.assertExists(newname)

    def test_wipe_name_non_retryable_error(self):
        """Give up early when rename() fails with non-retryable error"""
        for errnum in (errno.EACCES, errno.EPERM, errno.EROFS):
            with self.subTest(errnum=errnum):
                filename = self.write_file(f'orig{errnum}')
                expected = os.path.join(self.tempdir, f'fail{errnum}')
                rename_error = OSError(errnum, os.strerror(errnum))

                self.assertNotExists(expected)
                with mock.patch.object(
                        Wipe, '__random_string',
                        return_value=f'fail{errnum}'), \
                        mock.patch.object(
                            Wipe.os, 'rename',
                            side_effect=rename_error) as rename_mock:
                    newname = wipe_name(filename)

                self.assertEqual(filename, newname)
                self.assertExists(filename)
                self.assertNotExists(expected)
                self.assertEqual(1, rename_mock.call_count)

    @unittest.skipUnless(os.getenv('ALLTESTS') is not None,
                         'warning: skipping long test test_wipe_path() because'
                         ' environment variable ALLTESTS not set')
    def test_wipe_path(self):
        """Unit test for wipe_path()"""

        for _ret in wipe_path(self.tempdir):
            # no idle handler
            pass

    def test_wipe_path_fast(self):
        """Unit test for wipe_path() with fast mode

        This test runs three iterations of the generator
        and then aborts. Each iteration takes a little more
        than two seconds.
        """
        counter = 0
        for _i in wipe_path(self.tempdir, True):
            counter += 1
            if counter >= 3:
                break
        self.assertGreater(counter, 0)
