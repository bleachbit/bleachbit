# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module FileUtilities
"""

# standard library
import contextlib
import ctypes
import itertools
import unittest.mock
import json
import locale
import os
import random
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import warnings

# third-party import
import psutil

# local import
from bleachbit.FileUtilities import (
    _remove_windows_readonly,
    bytes_to_human,
    children_in_directory,
    clean_ini,
    clean_json,
    delete_file,
    delete,
    detect_encoding,
    ego_owner,
    exe_exists,
    execute_sqlite3,
    exists_in_path,
    expand_glob_join,
    extended_path_undo,
    extended_path,
    free_space,
    get_filesystem_type,
    getsize,
    getsizedir,
    globex,
    guess_overwrite_paths,
    human_to_bytes,
    is_dir_empty,
    is_hard_link,
    is_normal_directory,
    listdir,
    open_files_lsof,
    OpenFiles,
    same_partition,
    uris_to_paths,
    vacuum_sqlite3,
    whitelisted
)
from bleachbit.General import gc_collect, run_external
from bleachbit.Options import init_configuration, options
from bleachbit import logger
from tests import common


if 'nt' == os.name:
    # pylint: disable=import-error
    import win32api
    import win32com.shell
    import win32con
    import win32file

    from bleachbit import Windows
    from tests.TestWindows import WindowsLinksMixIn
else:
    WindowsLinksMixIn = object


def ini_helper(self, execute):
    """Used to test .ini cleaning in TestAction and in TestFileUtilities"""

    teststr = '#Test\n[RecentsMRL]\nlist=C:\\Users\\me\\Videos\\movie.mpg,C:\\Users\\me\\movie2.mpg\n'
    for encoding in ['utf-8', 'utf-8-sig']:
        with self.subTest(encoding=encoding):
            extra_size = 0
            if 'utf-8-sig' == encoding:
                extra_size = 3
            if 'nt' == os.name:
                extra_size += teststr.count('\n')

            # create test file
            filename = self.write_file(
                'bleachbit-test-ini', teststr, mode='w', encoding=encoding)
            self.assertExists(filename)
            size = os.path.getsize(filename)
            self.assertEqual(len(teststr) + extra_size, size)

            # The section does not exist, so no change.
            execute(filename, 'Recents', None)
            self.assertEqual(len(teststr) + extra_size,
                             os.path.getsize(filename))

            # The parameter does not exist, so no change.
            execute(filename, 'RecentsMRL', 'files')
            self.assertEqual(len(teststr) + extra_size,
                             os.path.getsize(filename))

            # The parameter does exist, so the file shrinks.
            # The file will be size 14 if chardet is available.
            # Otherwise, size will be 17 with BOM.
            execute(filename, 'RecentsMRL', 'list')
            self.assertIn(os.path.getsize(filename), (14, 17))

            # The section does exist, so the file shrinks.
            execute(filename, 'RecentsMRL', None)
            self.assertEqual(0, os.path.getsize(filename))

            # clean up
            delete(filename)
            self.assertNotExists(filename)


def json_helper(self, execute):
    """Used to test JSON cleaning in TestAction and in TestFileUtilities"""

    def load_js(js_fn):
        with open(js_fn, 'r', encoding='utf-8') as js_fd:
            return json.load(js_fd)

    expected = {'deleteme': 1, 'spareme': {'deletemetoo': 1}}

    # create test file
    (fd, filename) = tempfile.mkstemp(
        prefix='bleachbit-test-json', dir=self.tempdir)
    os.write(fd, b'{ "deleteme" : 1, "spareme" : { "deletemetoo" : 1 } }')
    os.close(fd)
    self.assertExists(filename)
    self.assertEqual(load_js(filename), expected)

    # invalid key
    execute(filename, 'doesnotexist')
    self.assertEqual(load_js(filename), expected)

    # invalid key
    execute(filename, 'deleteme/doesnotexist')
    self.assertEqual(load_js(filename), expected)

    # valid key
    execute(filename, 'deleteme')
    self.assertEqual(load_js(filename), {'spareme': {'deletemetoo': 1}})

    # valid key
    execute(filename, 'spareme/deletemetoo')
    self.assertEqual(load_js(filename), {'spareme': {}})

    # valid key
    execute(filename, 'spareme')
    self.assertEqual(load_js(filename), {})

    # clean up
    delete(filename)
    self.assertNotExists(filename)


def _is_child_path(parent_path, child_path):
    """Check whether child_path is a child of parent_path."""
    parent = os.path.abspath(parent_path)
    child = os.path.abspath(child_path)
    return os.path.commonpath([parent]) == os.path.commonpath([parent, child])


def _open_blocking_handle(path, share_mode):
    """Open a file handle with the given share mode to block other processes.

    Args:
        path: Path to the file to open
        share_mode: Windows share mode (e.g., win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE)
    Returns:
        File handle that blocks other processes from accessing the file
    """
    return win32file.CreateFile(
        path,
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        share_mode,
        None,
        win32con.OPEN_ALWAYS,
        win32con.FILE_ATTRIBUTE_NORMAL,
        None,
    )


class FileUtilitiesTestCase(common.BleachbitTestCase, WindowsLinksMixIn):
    """Test case for module FileUtilities"""

    def setUp(self):
        """Call before each test method"""
        super().setUp()
        self.old_locale_tuple = locale.getlocale(locale.LC_NUMERIC)
        self.old_locale_str = locale.setlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        init_configuration(log=False)

    def tearDown(self):
        """Call after each test method"""
        if self.old_locale_tuple == (None, None):
            locale.setlocale(locale.LC_NUMERIC, 'C')
            return
        try:
            try:
                locale.setlocale(locale.LC_NUMERIC, self.old_locale_str)
            except locale.Error:
                if self.old_locale_tuple[0] is None:
                    locale.setlocale(locale.LC_NUMERIC, None)
                else:
                    try:
                        # First try with the full locale string
                        locale.setlocale(locale.LC_NUMERIC, '.'.join(
                            filter(None, self.old_locale_tuple)))
                    except locale.Error:
                        # If that fails, try just the language code part
                        try:
                            locale.setlocale(
                                locale.LC_NUMERIC, self.old_locale_tuple[0])
                        except locale.Error as e:
                            print(
                                "Failed to restore locale with just language code "
                                f"{self.old_locale_tuple[0]}: {e}")
        except locale.Error as e:
            print(f"Failed to restore locale {self.old_locale_tuple}: {e}")
        # Check that running getlocale again does not raise an exception.
        # For me, getlocale() fails after successful setlocale(..., 'en_MX') on Windows.
        locale.getlocale(locale.LC_NUMERIC)
        self.assertEqual(locale.setlocale(
            locale.LC_NUMERIC), self.old_locale_str)

    def test_bytes_to_human_one_way(self):
        """Test one-way conversion of bytes_to_human()"""

        # Test one-way conversion for predefined values
        # Each test is a tuple in the format: (bytes, SI, EIC)
        tests = ((-1, '-1B', '-1B'),
                 (0, '0B', '0B'),
                 (1, '1B', '1B'),
                 (1000, '1kB', '1000B'),
                 (1024, '1kB', '1KiB'),
                 (1110, '1.1kB', '1.1KiB'),
                 (1000**2, '1MB', '976.6KiB'),
                 (1024**2, '1MB', '1MiB'),
                 (1289748, '1.3MB', '1.2MiB'),
                 (1000**3, '1GB', '953.7MiB'),
                 (1024**3, '1.07GB', '1GiB'),
                 (1320702444, '1.32GB', '1.23GiB'),
                 (1000**4, '1TB', '931.32GiB'),
                 (1024**4, '1.1TB', '1TiB'),
                 (1000**5, '1PB', '909.49TiB'),
                 (1024**5, '1.13PB', '1PiB'))

        options.set('units_iec', True)
        for test in tests:
            iec = bytes_to_human(test[0])
            self.assertEqual(test[2], iec,
                             f"bytes_to_human({test[0]}) IEC = {iec}"
                             f" but expected {test[2]}")

        options.set('units_iec', False)
        for test in tests:
            si = bytes_to_human(test[0])
            self.assertEqual(test[1], si,
                             f"bytes_to_human({test[0]}) SI = {si}"
                             f" but expected {test[1]}")

    def test_bytes_to_human_roundtrip(self):
        """Test roundtrip conversion of bytes_to_human()

        Example: 1,964,950 -> 2MB -> 2,000,000 with difference of 1.78% (0.0178).
        """

        for _n in range(0, 1000):
            bytes1 = random.randrange(0, 1000 ** 4)
            human = bytes_to_human(bytes1)
            bytes2 = human_to_bytes(human)
            error = abs(float(bytes2 - bytes1) / bytes1)
            self.assertLess(abs(
                error), 0.02, f"{bytes1:,} ({human}) is "
                f"{error * 100:.2f}% different than {bytes2:,}")

    def test_bytes_to_human_localization(self):
        """Test localization of bytes_to_human()"""
        if not hasattr(locale, 'format_string'):
            self.skipTest('Locale module does not support format_string')
        try:
            locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
        except locale.Error as e:
            logger.warning('exception when setlocale to de_DE.utf8: %s', e)
        else:
            self.assertEqual("1,01GB", bytes_to_human(1000 ** 3 + 5812389))

    def test_children_in_directory(self):
        """Unit test for function children_in_directory()"""

        # test an existing directory that usually exists
        dirname = os.path.expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assertTrue(os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assertTrue(os.path.isabs(filename))
            self.assertFalse(os.path.isdir(filename))
            self.assertFalse(is_normal_directory(filename))

        # test a constructed file in a constructed directory
        dirname = self.mkdtemp(prefix='bleachbit-test-children')
        filename = self.mkstemp(prefix="somefile", dir=dirname)
        for loopfilename in children_in_directory(dirname, True):
            self.assertEqual(loopfilename, filename)
        for loopfilename in children_in_directory(dirname, False):
            self.assertEqual(loopfilename, filename)
        os.remove(filename)

        # test subdirectory
        subdirname = os.path.join(dirname, "subdir")
        self.mkdir(subdirname)
        for filename in children_in_directory(dirname, True):
            self.assertEqual(filename, subdirname)
        for filename in children_in_directory(dirname, False):
            raise AssertionError(
                'Found a file that shouldn\'t have been found: ' + filename)
        os.rmdir(subdirname)

        os.rmdir(dirname)

    @common.skipIfWindows
    def test_children_in_directory_posix_symlink(self):
        """POSIX: ensure directory symlinks are not followed"""

        base_dir = self.mkdir('children-symlink-primary')

        # Real directory inside base for normal traversal
        real_dir = os.path.join(base_dir, 'real-dir')
        self.mkdir(real_dir)
        real_file = self.mkstemp(prefix='real-file-', dir=real_dir)

        # Symlink inside base pointing outside of base_dir
        external_target = self.mkdir('children-symlink-external')
        external_file = self.mkstemp(
            prefix='external-file-', dir=external_target)
        self.assertExists(external_target)
        self.assertExists(external_file)
        link_dir = os.path.join(base_dir, 'linked-dir')
        os.symlink(external_target, link_dir)
        self.assertExists(link_dir)
        self.assertFalse(is_normal_directory(link_dir))

        # list_directories=True should yield the link itself but not descend
        entries_with_dirs = list(children_in_directory(base_dir, True))
        self.assertIn(link_dir, entries_with_dirs)
        self.assertIn(real_file, entries_with_dirs)
        self.assertIn(real_dir, entries_with_dirs)
        self.assertEqual(len(entries_with_dirs), 3)

        # list_directories=False should only yield the real file
        entries_files_only = list(children_in_directory(base_dir, False))
        self.assertEqual(entries_files_only, [real_file])
        self.assertEqual(len(entries_files_only), 1)

    @common.skipIfWindows
    def test_children_in_directory_posix_circular_symlink(self):
        """POSIX: ensure circular directory symlinks are not followed"""

        base_dir = self.mkdir('children-circular-')

        # Create a normal directory and file inside the base directory
        real_dir = os.path.join(base_dir, 'real-dir')
        self.mkdir(real_dir)
        real_file = self.mkstemp(prefix='real-file-', dir=real_dir)

        # Symlink inside base pointing back to base_dir to create circular reference
        loop_link = os.path.join(base_dir, 'loop-link')
        os.symlink(base_dir, loop_link)
        self.assertExists(loop_link)
        self.assertFalse(is_normal_directory(loop_link))

        entries_with_dirs = list(children_in_directory(base_dir, True))
        self.assertIn(loop_link, entries_with_dirs)
        self.assertIn(real_file, entries_with_dirs)
        self.assertIn(real_dir, entries_with_dirs)
        self.assertEqual(len(entries_with_dirs), 3)

        entries_files_only = list(children_in_directory(base_dir, False))
        self.assertEqual(entries_files_only, [real_file])
        self.assertEqual(len(entries_files_only), 1)

    @common.skipUnlessWindows
    def test_children_in_directory_windows_links(self):
        """Windows: ensure symlinked dirs and junctions are not followed"""

        base_dir = self.mkdir('children-links')

        # Regular directory to confirm normal traversal still works
        normal_dir = os.path.join(base_dir, 'normal-dir')
        self.mkdir(normal_dir)
        normal_file = os.path.join(normal_dir, 'normal-file')
        common.touch_file(normal_file)
        self.assertExists(normal_file)

        # Symlink target lives outside base_dir
        symlink_target = self.mkdir('children-symlink-target')
        symlink_target_file = self.mkstemp(
            prefix='symlink-target-file-', dir=symlink_target)
        symlink_path = os.path.join(base_dir, 'symlinked-dir')
        try:
            self._create_win_dir_symlink(symlink_target, symlink_path)
        except OSError as exc:
            self.skipTest(f'Cannot create Windows directory symlink: {exc}')
        self.assertFalse(is_hard_link(symlink_target))
        self.assertFalse(is_hard_link(symlink_path))
        self.assertFalse(is_normal_directory(symlink_path))
        self.assertTrue(is_normal_directory(symlink_target))

        # Junction target lives outside base_dir
        junction_target = self.mkdir('children-junction-target')
        junction_target_file = self.mkstemp(
            prefix='junction-target-file-', dir=junction_target)
        junction_path = os.path.join(base_dir, 'junction-dir')
        try:
            self._create_win_junction(junction_target, junction_path)
        except (OSError, subprocess.CalledProcessError) as exc:
            self.skipTest(f'Cannot create Windows junction: {exc}')
        self.assertFalse(is_hard_link(junction_target))
        self.assertFalse(is_hard_link(junction_path))
        self.assertFalse(is_normal_directory(junction_path))
        self.assertTrue(is_normal_directory(junction_target))

        entries_with_dirs = list(children_in_directory(base_dir, True))
        entries_files_only = list(children_in_directory(base_dir, False))

        self.assertIn(normal_file, entries_files_only)
        for link_dir in (symlink_path, junction_path):
            self.assertIn(link_dir, entries_with_dirs)
            # There must be no children of the linked directories.
            offending_paths = [
                path for path in entries_with_dirs + entries_files_only
                if _is_child_path(link_dir, path) and path != link_dir
            ]
            self.assertEqual(
                offending_paths,
                [],
                f"Traversal into {link_dir} detected in children_in_directory results",
            )

        # Files living only behind the link targets should never appear
        for hidden_file in (symlink_target_file, junction_target_file):
            self.assertNotIn(hidden_file, entries_with_dirs)
            self.assertNotIn(hidden_file, entries_files_only)

        self.assertEqual(len(entries_with_dirs), 4)
        self.assertEqual(len(entries_files_only), 1)

    def test_clean_ini(self):
        """Unit test for clean_ini()"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                options.set('shred', shred)
                ini_helper(self, clean_ini)

    def test_clean_ini_kde(self):
        """Unit test for clean_ini() with KDE ini file

        It was reading the colon as a delimiter, but now delimiters are limited to equals sign.
        See https://github.com/bleachbit/bleachbit/issues/1902
        """

        ini_content_kfile = """
[KFileDialog Settings]
Recent Files[$e]=file:///run/media/AAA1/BBBBB/cccc_ddddddd.zip
Recent URLs[$e]=file:///run/media/AAA1/BBBBB/
""".lstrip()

        ini_content_mainwindow = """
[MainWindow]
1680x1050 screen: Height=600
1680x1050 screen: Width=990
State=AAAA/wA...
""".lstrip()

        path = os.path.join(self.tempdir, "arkstaterc")

        tests = [
            ("KFileDialog Settings", ini_content_mainwindow),
            ("MainWindow", ini_content_kfile),
        ]
        for section, content in tests:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ini_content_kfile + "\n" + ini_content_mainwindow)

            clean_ini(path, section=section, parameter=None)

            with open(path, "r", encoding="utf-8") as f:
                cleaned_content = f.read()

            self.assertEqual(
                content.strip(), cleaned_content.strip().replace(" = ", "="))

    def test_clean_json(self):
        """Unit test for clean_json()"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                options.set('shred', shred)
                json_helper(self, clean_json)

    def test_delete(self):
        """Unit test for method delete()"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                self.delete_helper(shred=shred)

    def test_delete_ignore_missing(self):
        """Unit test for delete() with ignore_missing=True"""
        self.assertFalse(delete('does-not-exist', ignore_missing=True))
        self.assertRaises(OSError, delete, 'does-not-exist')

    def test_delete_access_denied(self):
        """delete() raises PermissionError on access denied"""
        path = self.write_file('test_delete_access_denied', b'secret')
        e = PermissionError(13, 'Access is denied', path)
        if os.name == 'nt':
            e.winerror = 5
        with unittest.mock.patch('os.remove', side_effect=e):
            with self.assertRaises(PermissionError):
                delete(path, shred=False)
        self.assertExists(path)

    def delete_helper(self, shred):
        """Called by test_delete() with shred = False and = True"""

        # test deleting with various kinds of filenames
        hebrew = "עִבְרִית"
        katanana = "アメリカ"
        umlauts = "ÄäǞǟËëḦḧÏïḮḯÖöȪȫṎṏT̈ẗÜüǕǖǗǘǙǚǛǜṲṳṺṻẄẅẌẍŸÿ"

        tests = ['.prefixandsuffix',  # simple
                 "x".zfill(150),  # long
                 ' begins_with_space',
                 "''",  # quotation mark
                 "~`!@#$%^&()-_+=x",  # non-alphanumeric characters
                 "[]{};'.,x",  # non-alphanumeric characters
                 'abcdefgh',  # simple Unicode
                 'J\xf8rgen Scandinavian',
                 '\u2014em-dash',  # LP#1454030
                 hebrew,
                 katanana,
                 umlauts,
                 'sigil-should$not-change']
        if 'posix' == os.name:
            # Windows doesn't allow these characters but Unix systems do
            tests += ['"*', '\t\\', ':?<>|',
                      ' ', '.file.']  # Windows filenames cannot end with space or period
        for test in tests:
            # create the file
            filename = self.write_file(test, b"top secret")
            # delete the file
            self.assertTrue(delete(filename, shred))
            self.assertNotExists(filename)

            # delete an empty directory
            dirname = self.mkdtemp(prefix=test)
            self.assertExists(dirname)
            self.assertTrue(delete(dirname, shred))
            self.assertNotExists(dirname)

        def symlink_helper(link_fn):
            if 'nt' == os.name:
                # pylint: disable=no-member
                if not win32com.shell.shell.IsUserAnAdmin():
                    self.skipTest(
                        'skipping symlink test because of insufficient privileges')

            # make regular file
            srcname = self.mkstemp(prefix='bleachbit-test-delete-regular')

            # make symlink
            self.assertExists(srcname)
            linkname = tempfile.mktemp('bblink')
            self.assertNotExists(linkname)
            link_fn(srcname, linkname)
            self.assertExists(linkname)
            self.assertLExists(linkname)

            # delete symlink
            self.assertTrue(delete(linkname, shred))
            self.assertExists(srcname)
            self.assertNotLExists(linkname)

            # delete regular file
            self.assertTrue(delete(srcname, shred))
            self.assertNotExists(srcname)

            #
            # test broken symlink
            #
            srcname = self.mkstemp(prefix='bleachbit-test-delete-sym')
            self.assertLExists(srcname)
            link_fn(srcname, linkname)
            self.assertLExists(linkname)
            self.assertExists(linkname)

            # delete regular file first
            self.assertTrue(delete(srcname, shred))
            self.assertNotExists(srcname)
            self.assertLExists(linkname)

            # clean up
            self.assertTrue(delete(linkname, shred))
            self.assertNotExists(linkname)
            self.assertNotLExists(linkname)

        if 'nt' == os.name:
            logger.debug('testing symbolic link')
            kern = ctypes.windll.LoadLibrary("kernel32.dll")

            def win_symlink(src, linkname):
                rc = kern.CreateSymbolicLinkW(linkname, src, 0)
                if rc == 0:
                    print(f'CreateSymbolicLinkW({linkname}, {src})')
                    print(
                        f'CreateSymbolicLinkW() failed, error = {ctypes.FormatError()}')
                    self.assertNotEqual(rc, 0)
            symlink_helper(win_symlink)

            # test empty directory on Windows
            path = self.mkdtemp(prefix='bleachbit-test-delete-dir')
            self.assertExists(path)
            self.assertTrue(delete(path, shred))
            self.assertNotExists(path)

            return

        # below this point, only posix

        # test file with mode 0444/-r--r--r--
        filename = self.write_file('bleachbit-test-0444')
        os.chmod(filename, 0o444)
        self.assertTrue(delete(filename, shred))
        self.assertNotExists(filename)

        # test symlink
        symlink_helper(os.symlink)

        # test FIFO
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assertExists(filename)
        self.assertTrue(delete(filename, shred))
        self.assertNotExists(filename)

        # test directory
        path = self.mkdtemp(prefix='bleachbit-test-delete-dir')
        self.assertExists(path)
        self.assertTrue(delete(path, shred))
        self.assertNotExists(path)

    @common.skipUnlessWindows
    def test_delete_hidden(self):
        """Unit test for delete() with hidden file"""
        for shred in (False, True):
            fn = os.path.join(self.tempdir, 'hidden')
            common.touch_file(fn)
            # pylint: disable=possibly-used-before-assignment, c-extension-no-member
            win32api.SetFileAttributes(fn, win32con.FILE_ATTRIBUTE_HIDDEN)
            self.assertExists(fn)
            self.assertFalse(is_hard_link(fn))
            self.assertFalse(is_normal_directory(fn))
            self.assertTrue(delete(fn, shred=shred))
            self.assertNotExists(fn)

    @common.skipUnlessWindows
    def test_delete_locked_file(self):
        """Unit test for delete() with locked file"""
        # set up
        def test_delete_locked_setup(share_mode):
            (fd, filename) = tempfile.mkstemp(
                prefix='bleachbit-test-fileutilities')
            os.write(fd, b'123')
            os.close(fd)
            self.assertExists(filename)
            self.assertEqual(3, getsize(filename))
            handle = _open_blocking_handle(filename, share_mode)
            self.assertFalse(is_hard_link(filename))
            return filename, handle

        # Each test is:
        #   (share_mode, delete_expected, truncate_expected)
        # The overall outcomes in matrix:
        #  - file deleted (True, None)
        #  - file truncated but not deleted (False, True)
        #  - file not deleted and not truncated (False, False)
        tests = [


            (0, False, False),  # exclusive

            (win32con.FILE_SHARE_READ, False, False),  # read-only sharing

            (
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                False,
                True,
            ),

            (
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_DELETE,
                True,
                None,  # truncate not attempted
            ),

            (
                win32con.FILE_SHARE_READ
                | win32con.FILE_SHARE_WRITE
                | win32con.FILE_SHARE_DELETE,
                True,
                None,  # truncate not attempted
            ),
        ]

        for (share_mode, delete_expected, truncate_expected), shred in itertools.product(tests, (False, True)):
            with self.subTest(share_mode=share_mode, shred=shred):
                filename, handle = test_delete_locked_setup(share_mode)

                if delete_expected:
                    # Delete expected to suceed.
                    delete_file(filename, shred)
                else:
                    # Delete expected to fail.
                    # pylint: disable=undefined-variable
                    with self.assertRaises(WindowsError):
                        delete_file(filename, shred)
                win32file.CloseHandle(handle)
                if delete_expected:
                    self.assertNotExists(filename)
                else:
                    self.assertExists(filename)
                    self.assertIsNotNone(truncate_expected)
                    expected_size = 0 if truncate_expected else 3
                    self.assertEqual(expected_size, getsize(filename))
                    delete(filename)
                    self.assertNotExists(filename)

    @common.skipIfWindows
    @common.also_with_sudo
    def test_delete_mount_point(self):
        """Unit test for deleting a mount point in use"""
        if not common.have_root():
            self.skipTest('not enough privileges')
        from_dir = self.mkdir('mount_from')
        from_file = os.path.join(from_dir, 'normal-file')
        common.touch_file(from_file)
        to_dir = self.mkdir('mount_to')
        args = ['mount', '--bind', from_dir, to_dir]
        (rc, _, stderr) = run_external(args)
        self.assertEqual(
            rc, 0, f'error calling mount\nargs={args}\nstderr={stderr}')
        self.assertTrue(os.path.isdir(to_dir))
        to_file = os.path.join(to_dir, 'normal-file')
        all_objs = (to_file, from_file, to_dir, from_dir)
        for func in (os.path.islink, os.path.isjunction, os.path.ismount, is_hard_link):
            for pathname in all_objs:
                self.assertFalse(func(pathname))
        try:
            # delete() should return False for a busy mount point
            ret = delete(to_dir)
            self.assertFalse(ret)
            # The mount point and its contents should still exist.
            for pathname in all_objs:
                self.assertExists(pathname)
        finally:
            args = ['umount', to_dir]
            (rc, _, stderr) = run_external(args)
            self.assertEqual(
                rc, 0, f'error calling umount\nargs={args}\nstderr={stderr}')
            self.assertNotExists(to_file)

    def test_delete_not_empty(self):
        """Test for scenario directory is not empty"""
        # common.py puts bleachbit.ini in self.tempdir, but it may
        # not be flushed
        dirname = self.mkdir('a_dir')
        self.assertFalse(is_dir_empty(self.tempdir))
        self.assertTrue(is_dir_empty(dirname))
        fn = self.write_file(os.path.join(dirname, 'a_file'), b'content')
        self.assertFalse(is_dir_empty(dirname))

        for path in (fn, dirname, self.tempdir):
            self.assertExists(path)
            self.assertFalse(is_hard_link(path))

        # Make sure shredding does not leave a renamed directory like
        # in https://github.com/bleachbit/bleachbit/issues/783
        for allow_shred in (False, True):
            self.assertFalse(delete(dirname, allow_shred=allow_shred))
            self.assertExists(fn)
            self.assertExists(dirname)
        os.remove(fn)
        self.assertTrue(is_dir_empty(dirname))

    def test_delete_read_only_file(self):
        """Unit test for delete() with read-only file"""
        for option_shred, parameter_shred, delete_func in itertools.product(
            [False, True], [False, True], [delete, delete_file]
        ):
            with self.subTest(option_shred=option_shred, parameter_shred=parameter_shred, delete_func=delete_func.__name__):
                shred = parameter_shred
                variation_dir = f"{option_shred}-{parameter_shred}-{delete_func.__name__}"
                options.set('shred', option_shred)
                # The directory is not read-only, but it used for the read-only test.
                tmp_dir = self.mkdtemp(prefix=f'read-only-dir_{variation_dir}')
                self.assertDirectoryCount(tmp_dir, 0)

                fn = self.write_file(
                    os.path.join(tmp_dir, f'read-only-file_{variation_dir}'),
                    b'read-only content',
                )
                os.chmod(fn, stat.S_IREAD)
                self.assertExists(fn)
                self.assertFalse(is_hard_link(fn))
                self.assertDirectoryCount(tmp_dir, 1)
                try:
                    delete_func(fn, shred=shred)
                except PermissionError as e:
                    _remove_windows_readonly(fn)
                    raise e
                self.assertNotExists(fn)
                self.assertDirectoryCount(tmp_dir, 0)

    def test_delete_hard_link(self):
        """Unit test for delete() with hard link"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                tmp_dir = self.mkdtemp(prefix=f'delete_hard_{shred}')
                target = self.write_file(
                    os.path.join(tmp_dir, f'hardlink-target-{shred}-'),
                    b'canary data',
                )
                self.assertDirectoryCount(tmp_dir, 1)

                link = os.path.join(tmp_dir, f'hardlink-{shred}')
                os.link(target, link)
                self.assertExists(link)
                self.assertFalse(os.path.islink(link))
                self.assertTrue(os.path.isfile(link))
                if os.name == 'nt':
                    self.assertFalse(Windows.is_junction(link))
                self.assertDirectoryCount(tmp_dir, 2)
                self.assertTrue(is_hard_link(link))
                self.assertTrue(is_hard_link(target))

                self.assertTrue(delete(link, shred=shred))
                self.assertNotExists(link)
                self.assertExists(target)
                # Regardless of shred setting, original should have canary data
                with open(target, 'rb') as f:
                    self.assertEqual(f.read(), b'canary data')
                self.assertDirectoryCount(tmp_dir, 1)

                delete(target, shred=False)
                self.assertDirectoryCount(tmp_dir, 0)

    @common.skipUnlessWindows
    def test_delete_junction(self):
        """Unit test for delete() with Windows junction"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                tmp_dir = self.mkdtemp(prefix=f'delete_junction_{shred}')
                # Use empty target: with shred=True, non-empty dirs trigger early return
                target_dir = self.mkdtemp(
                    prefix=f'junction-target-{shred}', dir=tmp_dir)
                self.assertDirectoryCount(tmp_dir, 1)

                junction = os.path.join(tmp_dir, f'junction-{shred}')
                self._create_win_junction(target_dir, junction)
                self.assertExists(junction)
                self.assertTrue(Windows.is_junction(junction))
                self.assertFalse(Windows.is_junction(target_dir))
                self.assertFalse(is_hard_link(junction))
                self.assertFalse(is_hard_link(target_dir))
                self.assertDirectoryCount(tmp_dir, 2)

                delete(junction, shred=shred)
                self.assertNotExists(junction)
                self.assertExists(target_dir)
                self.assertDirectoryCount(tmp_dir, 1)

                delete(target_dir, shred=False)
                self.assertDirectoryCount(tmp_dir, 0)

    @common.skipUnlessWindows
    def test_delete_read_only_directory(self):
        """Unit test for delete() with read-only directory on Windows"""
        kernel32 = ctypes.windll.kernel32
        FILE_ATTRIBUTE_READONLY = 0x1
        for shred in (False, True):
            with self.subTest(shred=shred):
                container = self.mkdtemp(prefix=f'ro-container-{shred}')
                self.assertTrue(is_dir_empty(container))
                self.assertDirectoryCount(container, 0)

                ro_dir = os.path.join(container, f'readonly-{shred}')
                self.mkdir(ro_dir)
                kernel32.SetFileAttributesW(ro_dir, FILE_ATTRIBUTE_READONLY)
                self.assertExists(ro_dir)
                self.assertDirectoryCount(container, 1)

                try:
                    delete(ro_dir, shred=shred)

                    self.assertNotExists(ro_dir)
                    self.assertDirectoryCount(container, 0)
                except Exception:
                    # Cleanup: clear read-only attribute so tearDown can remove it
                    for item in os.listdir(container):
                        item_path = os.path.join(container, item)
                        _remove_windows_readonly(item_path)
                    raise

    @common.skipUnlessWindows
    def test_delete_extended_path(self):
        """Unit test for delete() with extended Windows path (>260 chars)"""
        for shred in (False, True):
            with self.subTest(shred=shred):
                long_name = 'x' * 200
                long_dir = self.mkdir(f'{long_name}-dir-{shred}')

                long_file = self.write_file(
                    extended_path(os.path.join(
                        long_dir, f'{long_name}-file-{shred}.txt')),
                    b'canary data',
                )

                delete(long_file, shred=shred)
                self.assertNotExists(extended_path(long_file))

                delete(long_dir, shred=shred)
                self.assertNotExists(extended_path(long_dir))

    def test_detect_encoding(self):
        """Unit test for detect_encoding"""
        eat_glass = '나는 유리를 먹을 수 있어요. 그래도 아프지 않아요'
        bom = '\ufeff' + eat_glass  # Add BOM for utf-8-sig
        tests = (('This is just an ASCII file', 'ascii'),
                 (eat_glass, 'utf-8'),
                 (eat_glass, 'EUC-KR'),
                 (bom, 'UTF-8-SIG'))
        for file_contents, expected_encoding in tests:
            with self.subTest(encoding=expected_encoding):
                with tempfile.NamedTemporaryFile(mode='w', delete=False,
                                                 encoding=expected_encoding) as temp:
                    temp.write(file_contents)
                    temp.flush()
                det = detect_encoding(temp.name)
                self.assertEqual(
                    det, expected_encoding,
                    f"{file_contents} -> {det}, check that chardet is available")

    @common.skipIfWindows
    def test_ego_owner(self):
        """Unit test for ego_owner()"""
        # pylint: disable=no-member
        self.assertEqual(ego_owner('/bin/ls'), os.getuid() == 0)

    def test_execute_sqlite3(self):
        """Unit test for execute_sqlite3()"""
        db_path = self.mkstemp(prefix='bleachbit-test-file', suffix='.sqlite')

        cmds = ['CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)',
                "INSERT INTO test (name) VALUES ('A'), ('B')",
                "UPDATE test SET name = 'C' WHERE name = 'B'",
                "DELETE FROM test WHERE name = 'C'"]

        execute_sqlite3(db_path, ';'.join(cmds))
        execute_sqlite3(db_path, 'vacuum')

        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            res = conn.execute('select 1 from test where name = "A"')
            row = res.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)

        gc_collect()
        os.unlink(db_path)
        self.assertNotExists(db_path)

    def test_exe_exists(self):
        """Unit test for exe_exists()"""
        tests = [("/bin/sh", True),
                 ("sh", True),
                 ("doesnotexist", False),
                 ("/bin/doesnotexist", False)]
        if 'nt' == os.name:
            tests = [('c:\\windows\\system32\\cmd.exe', True),
                     ('cmd.exe', True),
                     ('doesnotexist', False),
                     ('c:\\windows\\doesnotexist.exe', False)]
        for exe, expected in tests:
            with self.subTest(exe=exe, expected=expected):
                if os.name == 'posix' and not os.getenv('PATH') and not os.path.isabs(exe):
                    self.skipTest('PATH not set')
                self.assertEqual(exe_exists(exe), expected,
                                 f"{exe} -> {expected}")

    def test_exists_in_path(self):
        """Unit test for exists_in_path()"""
        filename = 'ls'
        if 'nt' == os.name:
            filename = 'cmd.exe'
        if 'posix' == os.name and not os.getenv('PATH'):
            self.assertFalse(exists_in_path(filename))
        else:
            self.assertTrue(exists_in_path(filename))
        self.assertFalse(exists_in_path('doesnotexist'))
        if 'posix' == os.name:
            with self.assertRaises(AssertionError):
                exists_in_path('/usr/bin/doesnotexist')
        if 'nt' == os.name:
            with self.assertRaises(AssertionError):
                exists_in_path('c:\\does\\not\\exist.exe')

    def test_expand_glob_join(self):
        """Unit test for expand_glob_join()"""
        if 'posix' == os.name:
            expand_glob_join('/bin', '*sh')
        if 'nt' == os.name:
            expand_glob_join(r'c:\windows', '*.exe')

    def test_expand_vars_user(self):
        """Unit test for expandvars() and expanduser()

        We had custom implementations of expandvars() and expanduser()
        until commit 3a3913 that switched to Python 3.
        """

        if 'nt' == os.name:
            home_vars = ('%USERPROFILE%', '$userprofile', '${USERprofile}')
        else:
            home_vars = ['$HOME', '${HOME}']
        for var in home_vars:
            var_stripped = var.strip('%${}')
            if not os.getenv(var_stripped):
                self.skipTest(f'Environment variable {var_stripped} not set')
            expanded = os.path.expandvars(var)
            self.assertIsString(expanded)
            self.assertNotEqual(
                expanded, var, 'Environment variable was not expanded')
            self.assertEqual(expanded, os.path.expanduser('~'))
            self.assertExists(expanded)
            # An absolute path should not be altered.
            self.assertEqual(expanded, os.path.expandvars(expanded))
            self.assertEqual(expanded, os.path.expanduser(expanded))

    def test_expand_vars_no_change(self):
        """Unit test for expandvars() and expanduser()

        These expect no change.
        """
        # An empty string should not be altered.
        self.assertEqual(os.path.expandvars(''), '')

        # Non-existent variables should not be altered.
        self.assertEqual(os.path.expandvars('$nonexistent'), '$nonexistent')

        # A relative path should not be expanded.
        for p in ('common', 'common/', 'common', 'home', 'userprofile'):
            self.assertEqual(os.path.expanduser(p), p)

    def test_extended_path(self):
        """Unit test for extended_path() and extended_path_undo()"""
        if 'nt' == os.name:
            tests = [
                (r'c:\windows\notepad.exe', r'\\?\c:\windows\notepad.exe'),
                (r'\\server\share\windows\notepad.exe',
                 r'\\?\unc\server\share\windows\notepad.exe'),
            ]
        else:
            # unchanged
            tests = (('/home/foo', '/home/foo'),)
        for short, extended in tests:
            # already extended path shouldn't be changed
            self.assertEqual(extended_path(extended), extended)
            # does the conversion work both ways?
            self.assertEqual(extended_path(short), extended)
            self.assertEqual(extended_path_undo(extended), short)
            # unextended paths shouldn't be shortened any more
            self.assertEqual(extended_path_undo(short), short)

    def test_free_space(self):
        """Unit test for free_space()"""

        partitions = []
        os_paths = []
        if os.name == 'nt':
            # Allow CD-ROM, network drive, etc.
            partitions = psutil.disk_partitions(all=True)
            os_paths = (r'%windir%', r'%userprofile%', r'%temp%')
        elif os.name == 'posix':
            # Do not allow proc, sysfs, udev, etc.
            partitions_original = psutil.disk_partitions(all=False)
            # Allow ext4, vfat, etc. but not squashfs
            partitions = [
                p for p in partitions_original if p.fstype != 'squashfs']
            os_paths = ("/home", "/var", "/tmp", "$home", "$temp", "/dev/shm")
        self.assertGreater(len(partitions), 0, "No disk partitions found")

        test_counter = 0
        test_paths = set()
        for partition in partitions:
            test_paths.add(partition.mountpoint)
        for os_path in os_paths:
            expanded = os.path.expandvars(os_path)
            if os.path.exists(expanded):
                test_paths.add(expanded)
        test_paths.add(os.getcwd())

        for path in test_paths:
            with self.subTest(path=path):
                test_counter += 1
                free = free_space(path)
                self.assertIsInstance(
                    free, int, f"free_space({path}) should return int")
                self.assertGreaterEqual(
                    free, 0, f"free_space({path}) should be non-negative")
        self.assertGreater(test_counter, 0)

    def test_free_space_sub_dir(self):
        """Unit test for free_space() with subdirectories"""
        subdir = self.mkdtemp(prefix='free_space')
        passed = False
        for _ in range(5):
            diff = abs(free_space(subdir) - free_space(self.tempdir))
            if diff <= 1024 * 1024:  # 1MB
                passed = True
                break
        self.assertTrue(
            passed, "free_space() for subdir should be within 1MB of parent dir at least once")

    def test_free_space_invalid(self):
        """Check invalid inputs to free_space()"""
        # Test with invalid paths
        for path in ("invalid", "", None):
            with self.assertRaises((TypeError, FileNotFoundError)):
                free_space(path)

    def test_get_filesystem_type(self):
        """Unit test for get_filesystem_type()"""
        home = os.path.expanduser('~')
        if os.name == 'nt':
            path = self.tempdir
            fs_type = get_filesystem_type(path)[0]
            while path:
                print(path)
                self.assertEqual(get_filesystem_type(path)[0], fs_type)
                self.assertEqual(get_filesystem_type(path.lower())[0], fs_type)
                self.assertEqual(get_filesystem_type(path.upper())[0], fs_type)
                if path == os.path.dirname(path):
                    break
                path = os.path.dirname(path)
            self.assertNotEqual(fs_type, 'unknown')
            self.assertEqual(get_filesystem_type(r'a:\\')[0], 'unknown')
            self.assertEqual(get_filesystem_type(r'Z:\\')[0], 'unknown')
            for check_path in (home, r'c:\\', r'c:'):
                self.assertEqual(get_filesystem_type(
                    check_path)[0], 'NTFS', check_path)
                self.assertEqual(get_filesystem_type(
                    check_path.lower())[0], 'NTFS')
                self.assertEqual(get_filesystem_type(
                    check_path.upper())[0], 'NTFS')
        elif os.name == 'posix':
            for check_path in (home, '/'):
                detected_fs = get_filesystem_type(check_path)[0]
                self.assertIn(detected_fs, ['btrfs', 'ext4', 'ext3', 'squashfs', 'unknown'],
                              f"Unexpected file system type for {check_path}: {detected_fs}")

    def test_getsize(self):
        """Unit test for method getsize()"""
        dirname = self.mkdtemp(prefix='bleachbit-test-getsize')

        def test_getsize_helper(fname):
            filename = self.write_file(os.path.join(
                dirname, fname), b"abcdefghij" * 12345)

            if 'nt' == os.name:
                self.assertEqual(getsize(filename), 10 * 12345)
                # Expand the directory names, which are in the short format,
                # to test the case where the full path (including the directory)
                # is longer than 255 characters.
                # pylint: disable=possibly-used-before-assignment, c-extension-no-member
                lname = win32api.GetLongPathNameW(extended_path(filename))
                self.assertEqual(getsize(lname), 10 * 12345)
                # this function returns a byte string instead of Unicode
                counter = 0
                for child in children_in_directory(dirname, False):
                    self.assertEqual(getsize(child), 10 * 12345)
                    counter += 1
                self.assertEqual(counter, 1)
            if 'posix' == os.name:
                encoding = sys.getdefaultencoding()
                output = str(subprocess.Popen(
                    ["du", "-h", filename],
                    stdout=subprocess.PIPE).communicate()[0], encoding=encoding)
                output = output.replace("\n", "")
                du_size = output.split('\t', maxsplit=1)[0] + "B"
                print(f"output = '{output}', size='{du_size}'")
                du_bytes = human_to_bytes(du_size, 'du')
                print(output, du_size, du_bytes)
                self.assertEqual(getsize(filename), du_bytes)
            delete(filename)
            self.assertNotExists(filename)

        # create regular file
        test_getsize_helper('bleachbit-test-regular')

        # special characters
        test_getsize_helper('bleachbit-test-special-characters-∺ ∯')

        # em-dash (LP1454030)
        test_getsize_helper('bleachbit-test-em-dash-\u2014')

        # long
        test_getsize_helper('bleachbit-test-long' + 'x' * 200)

        # delete the empty directory
        delete(dirname)

        if 'nt' == os.name:
            # the following tests do not apply to Windows
            return

        # create a symlink
        filename = self.write_file(
            'bleachbit-test-symlink', b'abcdefghij' * 12345)
        linkname = os.path.join(self.tempdir, 'bleachbitsymlinktest')
        if os.path.lexists(linkname):
            delete(linkname)
        os.symlink(filename, linkname)
        self.assertLess(getsize(linkname), 8192,
                        f"Symlink size is {getsize(filename)}")
        delete(filename)

        if 'darwin' == sys.platform:
            # MacOS's HFS+ filesystem doesn't support sparse files
            return

        # create sparse file
        (handle, filename) = tempfile.mkstemp(prefix="bleachbit-test-sparse")
        os.ftruncate(handle, 1000 ** 2)
        os.close(handle)
        self.assertEqual(getsize(filename), 0)
        delete(filename)

    def test_getsizedir(self):
        """Unit test for getsizedir()"""
        path = '/bin'
        if 'nt' == os.name:
            path = 'c:\\windows\\system32'
        self.assertGreater(getsizedir(path), 0)

    def test_globex(self):
        """Unit test for method globex()"""
        for path in globex('/bin/*', '/ls$'):
            self.assertEqual(path, '/bin/ls')

    def test_guess_overwrite_paths(self):
        """Unit test for guess_overwrite_paths()"""
        for path in guess_overwrite_paths():
            self.assertTrue(os.path.isdir(path),
                            f'{path} is not a directory')

    def test_human_to_bytes(self):
        """Unit test for human_to_bytes()"""
        self.assertRaises(ValueError, human_to_bytes, '', hformat='invalid')

        for test in ['Bazillion kB', '120XB', '.12MB']:
            self.assertRaises(ValueError, human_to_bytes, test)

        valid = {'1kB': 1000,
                 '1.1MB': 1100000,
                 '12B': 12,
                 '1.0M': 1000 * 1000,
                 '1TB': 1000**4,
                 '1000': 1000}
        for test, result in valid.items():
            self.assertEqual(human_to_bytes(test), result)

        self.assertEqual(human_to_bytes('1 MB', 'du'), 1024 * 1024)

    def test_listdir(self):
        """Unit test for listdir()"""
        if 'posix' == os.name:
            dir1 = '/bin'
            dir2 = os.path.expanduser('/sbin')
        elif 'nt' == os.name:
            dir1 = os.path.expandvars(r'%windir%\fonts')
            dir2 = os.path.expandvars(r'%windir%\logs')
        else:
            raise NotImplementedError()
        # If these directories do not exist, the test results are not valid.
        self.assertExists(dir1)
        self.assertExists(dir2)
        # Every path found in dir1 and dir2 should be found in (dir1, dir2).
        paths1 = set(listdir(dir1))
        paths2 = set(listdir(dir2))
        self.assertGreater(len(paths1), 4)
        self.assertGreater(len(paths2), 4)
        paths12 = set(listdir((dir1, dir2)))
        self.assertTrue(paths1 < paths12)
        self.assertTrue(paths2 < paths12)
        # The individual calls should be equivalent to a combined call.
        self.assertSetEqual(paths1.union(paths2), paths12)
        # The directories should not be empty.
        self.assertGreater(len(paths1), 0)
        self.assertGreater(len(paths2), 0)
        # Every path found should exist.
        for pathname in paths12:
            self.assertLExists(pathname)

    def test_is_normal_directory_real(self):
        """Unit test for is_normal_directory() with real files"""
        # Test with a real directory.
        self.assertTrue(is_normal_directory(self.tempdir))

        # Test with a normal file.
        self.assertFalse(is_normal_directory(__file__))

        # Test with a non-existent path.
        self.assertFalse(is_normal_directory(
            os.path.join(self.tempdir, 'doesnotexist')))

        # Check common junctions on Windows
        if 'nt' == os.name:
            user_docs = os.path.expandvars(r'%userprofile%\My Documents')
            prog_docs = os.path.expandvars(r'%ProgramData%\Documents')
            for junction_path in (user_docs, prog_docs):
                if os.path.exists(junction_path):
                    self.assertTrue(Windows.is_junction(junction_path),
                                    f"{junction_path} should be a junction")
                    self.assertFalse(is_normal_directory(junction_path),
                                     f"{junction_path} should not be a normal directory")
                else:
                    logger.warning("junction not found: %s", junction_path)

    def test_open_files_lsof(self):
        """Unit test for open_files_lsof()"""
        self.assertEqual(list(open_files_lsof(
            lambda: 'n/bar/foo\nn/foo/bar\nnoise')), ['/bar/foo', '/foo/bar'])

    @common.skipIfWindows
    def test_open_files(self):
        """Unit test for class OpenFiles"""

        filename = os.path.join(self.tempdir, 'bleachbit-test-open-files')
        with open(filename, 'wb'):
            openfiles = OpenFiles()
            ago = None
            if openfiles.last_scan_time:
                ago = time.time() - openfiles.last_scan_time
            self.assertTrue(openfiles.is_open(filename),
                            f"Expected is_open({filename}) to return True)\n"
                            f"openfiles.last_scan_time (ago)={ago}\n"
                            f"openfiles.files={openfiles.files}")

        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

        os.unlink(filename)
        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

    def test_same_partition(self):
        """Unit test for same_partition()"""
        home = os.path.expanduser('~')
        self.assertTrue(same_partition(home, home))
        if 'posix' == os.name:
            self.assertFalse(same_partition(home, '/dev'))
        elif 'nt' == os.name:
            home_drive = os.path.splitdrive(home)[0]
            # pylint: disable=import-outside-toplevel
            from bleachbit.Windows import get_fixed_drives
            for drive in get_fixed_drives():
                this_drive = os.path.splitdrive(drive)[0]
                self.assertEqual(same_partition(home, drive),
                                 home_drive == this_drive)

    def test_uris_to_paths(self):
        """Unit test for uris_to_paths()"""
        self.assertEqual(uris_to_paths(['']), [])

        # Unix-style
        uri_u = ['file:///usr/bin/bleachbit']
        path_u = [os.path.normpath('/usr/bin/bleachbit'), ]
        self.assertEqual(uris_to_paths(uri_u), path_u)

        # Windows
        uri_w = [r'file:///C:/program%20files/bleachbit.exe']
        path_w = [os.path.normpath(r'C:/program files/bleachbit.exe'), ]
        self.assertEqual(uris_to_paths(uri_w), path_w)

        # Multiple
        self.assertEqual(uris_to_paths(uri_u + uri_w), path_u + path_w)

        # Unsupported scheme
        uri_s = ['foo://bar']
        self.assertEqual(uris_to_paths(uri_u + uri_w + uri_s), path_u + path_w)

    def test_vacuum_sqlite3(self):
        """Unit test for method vacuum_sqlite3()"""
        path = os.path.join(self.tempdir, 'bleachbit.tmp.sqlite3')
        conn = sqlite3.connect(path)
        conn.execute('create table numbers (number)')
        conn.commit()
        empty_size = getsize(path)

        def number_generator():
            for x in range(1, 10000):
                yield (x, )
        conn.executemany(
            'insert into numbers (number) values ( ? ) ', number_generator())
        conn.commit()
        self.assertLess(empty_size, getsize(path))
        conn.execute('delete from numbers')
        conn.commit()
        conn.close()

        vacuum_sqlite3(path)
        self.assertEqual(empty_size, getsize(path))

        gc_collect()
        delete(path)
        self.assertNotExists(path)

    def test_sqlite_loop(self):
        """Repeat SQLite tests

        This may raise ResourceWarning on Python 3.13.
        """
        warnings.simplefilter("error")
        start_time = time.time()
        for _ in range(50):
            self.test_execute_sqlite3()
            self.test_vacuum_sqlite3()
            # Slow on OpenSUSE Build Service
            if time.time() - start_time > 30:
                logger.info(
                    "SQLite loop tests stopped early after %d seconds", time.time() - start_time)
                break
        logger.info(
            "SQLite loop tests fully completed after %d seconds", time.time() - start_time)

    def test_whitelisted(self):
        """Unit test for whitelisted()"""
        # setup
        old_whitelist = options.get_whitelist_paths()
        whitelist = [('file', '/home/foo'), ('folder', '/home/folder')]
        options.set_whitelist_paths(whitelist)
        self.assertEqual(set(whitelist), set(options.get_whitelist_paths()))

        # test
        self.assertFalse(whitelisted(''))
        self.assertFalse(whitelisted('/'))

        self.assertFalse(whitelisted('/home/foo2'))
        self.assertFalse(whitelisted('/home/fo'))
        self.assertTrue(whitelisted('/home/foo'))

        self.assertTrue(whitelisted('/home/folder'))
        if 'posix' == os.name:
            self.assertTrue(whitelisted('/home/folder/'))
            self.assertTrue(whitelisted('/home/folder/file'))
        self.assertFalse(whitelisted('/home/fold'))
        self.assertFalse(whitelisted('/home/folder2'))

        if 'nt' == os.name:
            whitelist = [('folder', 'D:\\'), (
                'file', 'c:\\windows\\foo.log'), ('folder', 'e:\\users')]
            options.set_whitelist_paths(whitelist)
            self.assertTrue(whitelisted('e:\\users'))
            self.assertTrue(whitelisted('e:\\users\\'))
            self.assertTrue(whitelisted('e:\\users\\foo.log'))
            self.assertFalse(whitelisted('e:\\users2'))
            # case insensitivity
            self.assertTrue(whitelisted('C:\\WINDOWS\\FOO.LOG'))
            self.assertTrue(whitelisted('D:\\USERS'))

            # drives letters have the separator at the end while most paths
            # don't
            self.assertTrue(whitelisted('D:\\FOLDER\\FOO.LOG'))

        # test blank
        options.set_whitelist_paths([])
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

        options.config.remove_section('whitelist/paths')
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

        # clean up
        options.set_whitelist_paths(old_whitelist)
        self.assertEqual(
            set(old_whitelist), set(options.get_whitelist_paths()))

    @common.skipIfWindows
    def test_whitelisted_posix_symlink(self):
        """Symlink test for whitelisted_posix()"""
        # setup
        old_whitelist = options.get_whitelist_paths()
        tmpdir = self.mkdir('bleachbit-whitelist')
        realpath = self.write_file('real')
        linkpath = os.path.join(tmpdir, 'link')
        os.symlink(realpath, linkpath)
        self.assertExists(realpath)
        self.assertExists(linkpath)

        # test 1: the real path is whitelisted
        whitelist = [('file', realpath)]
        options.set_whitelist_paths(whitelist)
        self.assertFalse(whitelisted(tmpdir))
        self.assertTrue(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        # test 2: the link is whitelisted
        whitelist = [('file', linkpath)]
        options.set_whitelist_paths(whitelist)
        self.assertFalse(whitelisted(tmpdir))
        self.assertFalse(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        options.set_whitelist_paths(old_whitelist)

    def test_whitelisted_speed(self):
        """Benchmark the speed of whitelisted()

        It is called frequently, so the speed is important."""
        d = '/usr/bin'
        whitelist = [('file', '/home/foo'), ('folder', '/home/folder')]
        if 'nt' == os.name:
            d = os.path.expandvars(r'%windir%\system32')
            whitelist = [('file', r'c:\filename'), ('folder', r'c:\\folder')]
        reps = 20
        paths = [p for p in children_in_directory(d, True)]
        paths = paths[:1000]  # truncate
        self.assertGreater(len(paths), 10)
        old_whitelist = options.get_whitelist_paths()
        options.set_whitelist_paths(whitelist)

        t0 = time.time()
        for _i in range(0, reps):
            for p in paths:
                _ = whitelisted(p)
        t1 = time.time()
        logger.info('whitelisted() with %d repetitions and %d paths took %g seconds',
                    reps, len(paths), t1 - t0)

        options.set_whitelist_paths(old_whitelist)
