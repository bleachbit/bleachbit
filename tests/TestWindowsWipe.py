# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Test case for module WindowsWipe
"""

import os
import sys
import tempfile
import time
import unittest

from tests import common
from bleachbit.FileUtilities import children_in_directory
from bleachbit.WindowsWipe import (
    check_os,
    determine_win_version,
    open_file,
    close_file,
    get_file_basic_info,
    truncate_file,
    volume_from_file,
    get_volume_information,
    get_extents,
    write_zero_fill,
    file_wipe,
    GENERIC_READ,
    GENERIC_WRITE
)

import win32file
import pywintypes

from win32com.shell import shell


@common.skipUnlessWindows
class WindowsWipeTestCase(common.BleachbitTestCase):
    """Test case for module WindowsWipe"""

    def setUp(self):
        """Set up test environment"""
        super(WindowsWipeTestCase, self).setUp()

    def test_check_os(self):
        """Unit test for check_os()"""
        # This should not raise an exception on Windows
        check_os()

    def test_determine_win_version(self):
        """Unit test for determine_win_version"""
        version, is_win_home = determine_win_version()
        self.assertIsInstance(version, str)
        self.assertIsInstance(is_win_home, bool)

    def test_open_close_file(self):
        """Unit tests for open_file() and close_file"""
        open_path = os.path.join(self.tempdir, 'open')
        self.write_file(open_path, b'test data')
        file_handle = open_file(open_path)
        self.assertIsNotNone(file_handle)
        close_file(file_handle)

    def test_get_extents(self):
        """Unit test for get_extents()"""

        error_count = 0
        zero_extents_count = 0
        nonzero_extents_count = 0
        start_time = time.time()

        for path in children_in_directory(os.path.expandvars(r'%windir%\system32')):
            try:
                file_handle = open_file(path)
            except pywintypes.error as e:
                if e.winerror in (5, 32):
                    error_count += 1
                    continue
                print(f"Error opening {path}: {e}")
                raise e

            ret = get_extents(file_handle, filename=path)
            self.assertIsInstance(ret, list)
            close_file(file_handle)

            if len(ret) == 0:
                zero_extents_count += 1
            else:
                nonzero_extents_count += 1

            # Files with size under ~500 bytes are resident in the MFT,
            # so they have zero clusters.
            fsize = os.path.getsize(path)
            if fsize > 1000:
                self.assertGreater(len(ret), 0)
            elif fsize < 200:
                self.assertEqual(len(ret), 0)
        total_files = zero_extents_count + nonzero_extents_count + error_count
        elapsed_seconds = time.time() - start_time
        if total_files > 0:
            files_per_second = total_files / elapsed_seconds
        else:
            files_per_second = None
        print(f"\ntest_get_extents() stats: {error_count:,} errors; {zero_extents_count:,} files with zero extents; {nonzero_extents_count:,} files with nonzero extents; {int(elapsed_seconds)} seconds; {int(files_per_second) if files_per_second else None} files per second")
        self.assertGreater(zero_extents_count, 10)
        self.assertGreater(nonzero_extents_count, 100)

    def test_get_file_basic_info(self):
        """Unit test for get_file_basic_info()"""
        fd, path = tempfile.mkstemp(prefix='bleachbit-test-windows-wipe')
        os.write(fd, b'test data')
        os.close(fd)

        file_handle = open_file(path)
        file_size, is_special = get_file_basic_info(path, file_handle)
        self.assertEqual(file_size, 9)
        self.assertFalse(is_special)
        close_file(file_handle)

        from bleachbit.General import run_external
        compact_cmd = ["compact", "/c", path]
        (rc, stdout, stderr) = run_external(compact_cmd)
        self.assertEqual(0, rc)

        file_handle = open_file(path)
        _, is_special_after = get_file_basic_info(path, file_handle)
        close_file(file_handle)
        self.assertTrue(is_special_after)

        sparse_path = os.path.join(self.tempdir, 'sparse')
        self.write_file(sparse_path, b'test data')
        fsutil_cmd = ["fsutil", "sparse", "setflag", sparse_path]
        (rc, stdout, stderr) = run_external(fsutil_cmd)
        self.assertEqual(0, rc)

        file_handle = open_file(sparse_path)
        _, is_sparse = get_file_basic_info(sparse_path, file_handle)
        close_file(file_handle)
        self.assertTrue(is_sparse)

    def test_truncate_file(self):
        """Unit test for truncate_file()"""
        truncate_path = os.path.join(self.tempdir, 'truncate')
        self.write_file(truncate_path, b'test data to be truncated')

        self.assertGreater(os.path.getsize(truncate_path), 0)

        file_handle = open_file(truncate_path, GENERIC_READ | GENERIC_WRITE)
        truncate_file(file_handle)
        close_file(file_handle)

        self.assertEqual(os.path.getsize(truncate_path), 0)

    def test_get_volume_information(self):
        """Unit test for get_volume_information"""
        volume = volume_from_file(sys.executable)
        self.assertIsInstance(volume, str)
        self.assertTrue(volume.endswith('\\'))
        self.assertTrue(os.path.exists(volume))
        self.assertEqual(len(volume), 3)

        volume_info = get_volume_information(volume)

        self.assertIsNotNone(volume_info)
        self.assertGreater(volume_info.sectors_per_cluster, 0)
        self.assertGreater(volume_info.bytes_per_sector, 0)
        self.assertGreater(volume_info.total_clusters, 0)

    def test_write_zero_fill(self):
        """Unit test for write_zero_fill"""
        tmp_path = os.path.join(self.tempdir, 'write_zero_fill')
        self.write_file(tmp_path, b'test data')

        file_handle = open_file(tmp_path, GENERIC_READ | GENERIC_WRITE)
        write_length = 1024
        write_zero_fill(file_handle, write_length)
        close_file(file_handle)

        self.assertEqual(os.path.getsize(tmp_path), write_length)

        with open(tmp_path, 'rb') as f:
            data = f.read()
            self.assertEqual(data, b'\x00' * write_length)

    def test_file_wipe_basic(self):
        """Basic unit test for file_wipe"""
        if not shell.IsUserAnAdmin():
            self.skipTest("Test requires administrator privileges")

        tmp_path = os.path.join(self.tempdir, 'file_wipe_basic')
        write_data = b'This is test data that should be wiped'
        self.write_file(tmp_path, write_data)

        file_wipe(tmp_path)

        with open(tmp_path, 'rb') as f:
            data = f.read()
            self.assertEqual(data, b'\x00' * len(write_data))

    def test_file_wipe_locked(self):
        """Test file_wipe() with a locked file"""
        if not shell.IsUserAnAdmin():
            self.skipTest("Test requires administrator privileges")

        tmp_path = os.path.join(self.tempdir, 'file_wipe_locked')
        self.write_file(tmp_path, b'This is test data that should be locked')

        file_handle = None
        try:
            file_handle = win32file.CreateFileW(
                tmp_path,
                win32file.GENERIC_READ,  # Only need read access to lock it
                0,  # No sharing to cause "access denied" error
                None,  # No security attributes
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None
            )

            with self.assertRaises(pywintypes.error) as context:
                file_wipe(tmp_path)

            # error 32: file in use
            # error 5: access denied
            self.assertIn(context.exception.winerror, [5, 32])

        finally:
            # Close the file handle to release the lock
            if file_handle:
                win32file.CloseHandle(file_handle)

    def test_not_included(self):
        """Notify users there are more tests"""
        self.skipTest(
            "More wiping tests available at https://github.com/bleachbit/windows-wipe/blob/master/testwipe.py")


if __name__ == '__main__':
    unittest.main()
