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

# standard library
import os
import sys
import tempfile
import time
import unittest

# third party
if os.name == 'nt':
    import win32file
    import pywintypes
    from win32com.shell import shell

# local
from tests import common
from bleachbit.FileUtilities import children_in_directory

if os.name == 'nt':
    # importing WindowsWipe fails on non-Windows
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
        wipe_file_direct,
        GENERIC_READ,
        GENERIC_WRITE,
        SetFilePointer,
        FILE_BEGIN,
        FlushFileBuffers
    )


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

    def test_get_extents_system32(self):
        """Unit test for get_extents() with system32 files"""

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
                self.assertGreater(len(ret), 0, f"File {path} has size {fsize:,} but no extents")
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

        cases = [
            {
                "name": "file_wipe_basic_small",
                "data": b'This is test data that should be wiped',
                "expect_zero_extents": True,
            },
            {
                "name": "file_wipe_basic_large",
                "data": os.urandom(4 * 1024 * 1024),
                "expect_zero_extents": False,
            },
        ]

        for case in cases:
            tmp_path = os.path.join(self.tempdir, case["name"])
            write_data = case["data"]
            self.write_file(tmp_path, write_data)

            file_handle = open_file(tmp_path)
            try:
                extents = get_extents(file_handle, filename=tmp_path)
            finally:
                close_file(file_handle)

            if case["expect_zero_extents"]:
                self.assertEqual(extents, [])
            else:
                self.assertIsInstance(extents, list)
                self.assertGreater(len(extents), 0)

            total_clusters = sum((end - start + 1) for start, end in extents)
            if total_clusters > 0:
                volume = volume_from_file(tmp_path)
                volume_info = get_volume_information(volume)
                cluster_size = (volume_info.sectors_per_cluster *
                                volume_info.bytes_per_sector)
                self.assertGreaterEqual(total_clusters * cluster_size, len(write_data))

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

    def test_file_wipe_swapped_handles(self):
        """Test file_wipe() with swapped handles and extents"""
        if not shell.IsUserAnAdmin():
            self.skipTest("Test requires administrator privileges")

        volume = volume_from_file(self.tempdir)
        volume_info = get_volume_information(volume)
        cluster_size = (volume_info.sectors_per_cluster *
                        volume_info.bytes_per_sector)

        file_configs = [
            {"path": os.path.join(self.tempdir, 'file_wipe_swap_1'),
             "content": b'1',
             "clusters": 1,
             "handle": None},
            {"path": os.path.join(self.tempdir, 'file_wipe_swap_2'),
             "content": b'2',
             "clusters": 2,
             "handle": None}
        ]

        try:
            for config in file_configs:
                with open(config["path"], 'wb') as f:
                    f.write(config["content"] *
                            (cluster_size * config["clusters"]))

                with open(config["path"], 'rb') as f:
                    content = f.read()
                    config["content_before"] = content
                    expected_size = cluster_size * config["clusters"]
                    self.assertEqual(len(content), expected_size,
                                     f"File should be exactly {config['clusters']} cluster(s) ({expected_size} bytes)")
                    self.assertEqual(
                        content, config["content"] * expected_size)

                config["handle"] = open_file(
                    config["path"], GENERIC_READ | GENERIC_WRITE)
                config["extents"] = get_extents(
                    config["handle"], filename=config["path"])

                total_clusters = sum([(end - start + 1)
                                     for start, end in config["extents"]])
                self.assertEqual(total_clusters, config["clusters"],
                                 f"File should have exactly {config['clusters']} cluster(s)")

                config["size"], _ = get_file_basic_info(
                    config["path"], config["handle"])

                # SetFilePointer(config["handle"], 0, FILE_BEGIN)

            # Wipe files with swapped handles and extents
            # Wipe file1 using file2's handle and extents
            wipe_file_direct(file_configs[1]["handle"], file_configs[0]["extents"],
                             cluster_size, file_configs[0]["size"])
            # Wipe file2 using file1's handle and extents
            wipe_file_direct(file_configs[0]["handle"], file_configs[1]["extents"],
                             cluster_size, file_configs[1]["size"])

            for config in file_configs:
                if config["handle"]:
                    # FlushFileBuffers(config["handle"])
                    close_file(config["handle"])
                    config["handle"] = None

            for config in file_configs:
                with open(config["path"], 'rb') as f:
                    config["content_after"] = f.read()

            # Verify results
            # File 1 (originally 1 cluster) wiped with File 2's extents (2 clusters)
            self.assertNotEqual(file_configs[0]["content_after"], file_configs[0]["content_before"],
                                "File 1 still contains original content after wiping")
            self.assertTrue(all(byte == 0 for byte in file_configs[0]["content_after"][:cluster_size]),
                            "First cluster of file 1 was not properly zeroed out")
            # File 1 should grow to match file 2's size (2 clusters)
            self.assertEqual(len(file_configs[0]["content_after"]), cluster_size * 2,
                             f"File 1 size should grow to 2 clusters ({cluster_size * 2} bytes)")

            # File 2 (originally 2 clusters) wiped with File 1's extents (1 cluster)
            self.assertNotEqual(file_configs[1]["content_after"], file_configs[1]["content_before"],
                                "File 2 still contains all original content after wiping")
            # First cluster should be zeroed out
            first_cluster = file_configs[1]["content_after"][:cluster_size]
            self.assertTrue(all(byte == 0 for byte in first_cluster),
                            "First cluster of file 2 was not properly zeroed out")
            # Second cluster should still have original data
            second_cluster = file_configs[1]["content_after"][cluster_size:cluster_size * 2]
            self.assertEqual(second_cluster, file_configs[1]["content"] * cluster_size,
                             "Second cluster of file 2 should still contain original data")
            # File 2 size should remain the same (2 clusters)
            self.assertEqual(len(file_configs[1]["content_after"]), cluster_size * 2,
                             f"File 2 size should remain 2 clusters ({cluster_size * 2} bytes)")

        finally:
            for config in file_configs:
                if config.get("handle"):
                    try:
                        close_file(config["handle"])
                    except:
                        pass

    def test_not_included(self):
        """Notify users there are more tests"""
        self.skipTest(
            "More wiping tests available at https://github.com/bleachbit/windows-wipe/blob/master/testwipe.py")


if __name__ == '__main__':
    unittest.main()
