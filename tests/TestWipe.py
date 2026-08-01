# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Wipe
"""

import errno
import itertools
import os
import unittest
from contextlib import ExitStack
from unittest import mock

import bleachbit
from bleachbit.Options import options
from bleachbit import Wipe
from bleachbit.Wipe import (
    detect_orphaned_wipe_files,
    sync,
    wipe_contents,
    wipe_path,
    wipe_name,
    wipe_write
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

    def test_wipe_write(self):
        """Unit test for wipe_write()"""

        original = b'abcdefghij' * 12345

        # overwrites the contents with zeros without truncating
        filename = self.write_file('wipe_write', original)
        wipe_write(filename).close()
        with open(filename, 'rb') as f:
            contents = f.read()
        self.assertEqual(contents, b'\x00' * len(contents))
        self.assertGreaterEqual(len(contents), len(original))

    def test_wipe_contents(self):
        """Unit test for wipe_contents()"""

        original = b'abcdefghij' * 12345

        # truncates the file to zero bytes
        filename = self.write_file('wipe_contents_truncate', original)
        wipe_contents(filename)
        self.assertEqual(os.path.getsize(filename), 0)

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
        if bleachbit.IS_WINDOWS:
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

        This test runs three iterations of the generator and then
        aborts. The idle clock is mocked forward on every check so
        this doesn't depend on how fast the real disk/quota fills,
        which varies a lot between CI runners.
        """
        counter = 0
        with mock.patch('bleachbit.Wipe.time.time', side_effect=itertools.count(0, 3)):
            for _i in wipe_path(self.tempdir, True):
                counter += 1
                if counter >= 3:
                    break
        self.assertGreater(counter, 0)

    def _make_mock_file(self, name='/tmp/empty_abc123'):
        """Return a mock file object for wipe_path tests"""
        mock_file = mock.Mock()
        mock_file.name = name
        mock_file.tell.return_value = 0
        mock_file.fileno.return_value = -1
        mock_file.write.return_value = 65536
        mock_file.flush.return_value = None
        mock_file.close.return_value = None
        return mock_file

    def _wipe_path_common_mocks(self, fs_type='ntfs'):
        """Return an ExitStack with the common wipe_path mocks applied.

        Each test can extend the returned stack with additional patches
        via ``stack.enter_context(...)``.
        """
        stack = ExitStack()
        stack.enter_context(mock.patch(
            'bleachbit.Wipe.os.path.isdir', return_value=True))
        stack.enter_context(mock.patch(
            'bleachbit.FileUtilities.get_filesystem_type', return_value=(fs_type,)))
        stack.enter_context(mock.patch(
            'bleachbit.FileUtilities.free_space', return_value=0))
        stack.enter_context(mock.patch('bleachbit.Wipe.sync'))
        # There is no statvfs on Windows, so create it.
        stack.enter_context(mock.patch(
            'bleachbit.Wipe.os.statvfs', create=True))
        stack.enter_context(mock.patch('bleachbit.Wipe.os.fsync'))
        stack.delete_mock = stack.enter_context(
            mock.patch('bleachbit.FileUtilities.delete'))
        return stack

    def test_wipe_path_not_directory(self):
        """Non-directory path should return early"""
        with mock.patch('bleachbit.FileUtilities.get_filesystem_type', return_value=('ntfs',)), \
                mock.patch('bleachbit.Wipe.os.path.isdir', return_value=False):
            results = list(wipe_path('/not-a-directory'))
        self.assertEqual(results, [])

    def test_wipe_path_fitrim(self):
        """Test fitrim is called for ext4/btrfs but not other filesystems"""
        for fs_type, should_call_fitrim in [('ext4', True), ('btrfs', True), ('ntfs', False)]:
            with self.subTest(fs_type=fs_type):
                mock_file = self._make_mock_file()
                mock_file.write.side_effect = IOError(
                    errno.EFBIG, 'File too large')
                with self._wipe_path_common_mocks(fs_type=fs_type) as stack:
                    mock_fitrim = stack.enter_context(
                        mock.patch('bleachbit.Wipe.fitrim'))
                    stack.enter_context(mock.patch(
                        'bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file))
                    list(wipe_path(self.tempdir))
                if should_call_fitrim:
                    mock_fitrim.assert_called_once()
                else:
                    mock_fitrim.assert_not_called()

    def test_wipe_path_tempfile_enametoolong_retry(self):
        """Temporary file creation retries with shorter name on ENAMETOOLONG"""
        mock_file = self._make_mock_file()
        mock_file.write.side_effect = IOError(errno.EFBIG, 'File too large')
        ntf_mock = mock.Mock()
        ntf_mock.side_effect = [
            OSError(errno.ENAMETOOLONG, 'File name too long'),
            mock_file
        ]
        with self._wipe_path_common_mocks() as stack:
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.tempfile.NamedTemporaryFile', ntf_mock))
            list(wipe_path(self.tempdir))
        self.assertEqual(ntf_mock.call_count, 2)
        first_suffix = ntf_mock.call_args_list[0][1]['suffix']
        second_suffix = ntf_mock.call_args_list[1][1]['suffix']
        self.assertEqual(len(first_suffix), 185)
        self.assertEqual(len(second_suffix), 180)

    def test_wipe_path_write_enospc(self):
        """Write loop handles ENOSPC by reducing block size"""
        mock_file = self._make_mock_file()
        call_count = 0

        def side_effect(data):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and len(data) == 65536:
                raise IOError(errno.ENOSPC, 'No space left on device')
            if call_count == 2:
                return len(data)
            raise IOError(errno.EFBIG, 'File too large')
        mock_file.write.side_effect = side_effect
        with self._wipe_path_common_mocks(), \
                mock.patch('bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file):
            list(wipe_path(self.tempdir))
        self.assertGreaterEqual(mock_file.write.call_count, 2)
        first_call_len = len(mock_file.write.call_args_list[0][0][0])
        second_call_len = len(mock_file.write.call_args_list[1][0][0])
        self.assertEqual(first_call_len, 65536)
        self.assertEqual(second_call_len, 32768)

    def test_wipe_path_write_persistent_edquot(self):
        """Persistent EDQUOT (even at 1-byte blocks) stops the outer loop.

        When every write fails with EDQUOT (errno 122, "Disk quota
        exceeded"), the inner loop halves the block down to 1 byte and
        then sets ``disk_full`` so the outer loop breaks instead of
        spinning forever creating empty temp files.

        This reproduces a scenario seen on on Linux with /tmp on a small tmpfs
        using usrquota with a significant gap between available space and the
        quota. Other processes (like other tests running in parallel with
        pytest-xdist) failed when not being able to write to /tmp.

        In this test, ``NamedTemporaryFile`` is allowed to create one file and
        then raises EDQUOT. With the fix, ``disk_full`` breaks the outer loop
        after the first file, so ``NamedTemporaryFile`` is called exactly once.
        Without the fix, the outer loop would call it again.
        """
        mock_file = self._make_mock_file()
        mock_file.write.side_effect = IOError(
            errno.EDQUOT, 'Disk quota exceeded')
        mock_file.tell.return_value = 0
        ntf_calls = [0]

        # ntf=NamedTemporaryFile
        def ntf_side_effect(*_args, **_kwargs):
            ntf_calls[0] += 1
            if ntf_calls[0] == 1:
                return mock_file
            raise OSError(errno.EDQUOT, 'Disk quota exceeded')
        with self._wipe_path_common_mocks() as stack:
            # Simulate EDQUOT despite adequete free space
            stack.enter_context(mock.patch(
                'bleachbit.FileUtilities.free_space', return_value=196 * 1024 * 1024))
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.tempfile.NamedTemporaryFile', side_effect=ntf_side_effect))
            list(wipe_path(self.tempdir))
        # With the fix, disk_full breaks the outer loop after the first file.
        self.assertEqual(ntf_calls[0], 1)
        # Block was halved down to 1 byte before giving up.
        last_call_len = len(mock_file.write.call_args_list[-1][0][0])
        self.assertEqual(last_call_len, 1)

    def test_wipe_path_fsync_edquot(self):
        """EDQUOT from fsync stops the outer loop."""
        mock_file = self._make_mock_file()
        mock_file.write.side_effect = IOError(errno.EFBIG, 'File too large')
        ntf_mock = mock.Mock(side_effect=[
            mock_file,
            AssertionError('wipe_path created another temporary file')
        ])
        with self._wipe_path_common_mocks() as stack:
            stack.enter_context(mock.patch(
                'bleachbit.FileUtilities.free_space', return_value=196 * 1024 * 1024))
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.tempfile.NamedTemporaryFile', ntf_mock))
            fsync_mock = stack.enter_context(mock.patch(
                'bleachbit.Wipe.os.fsync', side_effect=[
                    OSError(errno.EDQUOT, 'Disk quota exceeded'), None]))
            list(wipe_path(self.tempdir))
        self.assertEqual(fsync_mock.call_count, 2)
        self.assertEqual(ntf_mock.call_count, 1)

    def test_wipe_path_write_efbig(self):
        """Write loop handles EFBIG by breaking"""
        mock_file = self._make_mock_file()
        mock_file.write.side_effect = IOError(errno.EFBIG, 'File too large')
        with self._wipe_path_common_mocks(), \
                mock.patch('bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file):
            list(wipe_path(self.tempdir))
        mock_file.write.assert_called_once()

    def test_wipe_path_flush_enospc(self):
        """Flush handles ENOSPC without error"""
        mock_file = self._make_mock_file()
        write_call_count = 0

        def write_side_effect(data):
            nonlocal write_call_count
            write_call_count += 1
            if write_call_count == 1:
                return len(data)
            raise IOError(errno.EFBIG, 'File too large')
        mock_file.write.side_effect = write_side_effect
        mock_file.flush.side_effect = IOError(
            errno.ENOSPC, 'No space left on device')
        with self._wipe_path_common_mocks(), \
                mock.patch('bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file):
            list(wipe_path(self.tempdir))
        self.assertGreaterEqual(mock_file.flush.call_count, 1)

    def test_wipe_path_idle_yields_eta(self):
        """idle=True yields estimate completion tuples"""
        mock_file = self._make_mock_file()
        write_call_count = 0

        def write_side_effect(data):
            nonlocal write_call_count
            write_call_count += 1
            if write_call_count == 1:
                return len(data)
            raise IOError(errno.EFBIG, 'File too large')
        mock_file.write.side_effect = write_side_effect

        def time_side_effect():
            if write_call_count == 0:
                return 0.0
            if write_call_count == 1:
                return 3.0
            return 4.0
        with self._wipe_path_common_mocks() as stack:
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file))
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.time.time', side_effect=time_side_effect))
            results = list(wipe_path(self.tempdir, idle=True))
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 3)

    def test_wipe_path_cleanup_finally(self):
        """Cleanup runs in finally even when truncate_f fails"""
        mock_file = self._make_mock_file()
        mock_file.write.side_effect = IOError(errno.EFBIG, 'File too large')
        with self._wipe_path_common_mocks() as stack:
            stack.enter_context(mock.patch(
                'bleachbit.Wipe.tempfile.NamedTemporaryFile', return_value=mock_file))
            stack.enter_context(mock.patch(
                'bleachbit.FileUtilities.truncate_f', side_effect=RuntimeError('boom')))
            list(wipe_path(self.tempdir))
        mock_file.close.assert_called_once()
        stack.delete_mock.assert_called_once_with(
            mock_file.name, ignore_missing=True)
