# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module FileUtilities
"""

# standard library
import codecs
import contextlib
import ctypes
import errno
import itertools
import json
import locale
import mmap
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
import unittest.mock
import urllib.parse
import warnings

# third-party import
import psutil

from tests import common
from tests.common import pytest

# local import
from bleachbit.FileUtilities import (
    _mount_points_below,
    _posix_keep_list_spelling,
    _remove_windows_readonly,
    _truncate_locked_file,
    bytes_to_human,
    children_below,
    children_in_directory,
    clear_path_spellings,
    clean_ini,
    clean_json,
    delete_file,
    delete,
    detect_encoding,
    exe_exists,
    execute_sqlite3,
    exists_in_path,
    expand_glob_join,
    extended_path_undo,
    extended_path,
    FilesystemInfo,
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
    open_files_linux,
    open_files_lsof,
    open_files_psutil,
    open_files_freebsd,
    OpenFiles,
    same_partition,
    truncate_file,
    uris_to_paths,
    vacuum_sqlite3,
    whitelisted
)
from bleachbit.General import gc_collect, run_external
from bleachbit.Options import init_configuration, options
from bleachbit import logger, FS_CASE_SENSITIVE, IS_FREEBSD, IS_LINUX, IS_MAC, IS_POSIX, IS_WINDOWS


if IS_WINDOWS:
    from bleachbit import Windows
    # pylint: disable=import-error
    import pywintypes
    import win32api
    import win32com.shell
    import win32con
    import win32file

    # pylint: disable-next=ungrouped-imports
    from tests.TestWindows import WindowsLinksMixIn
else:
    WindowsLinksMixIn = object
    # WindowsError is a builtin only on Windows
    # pylint: disable-next=redefined-builtin, ungrouped-imports
    from bleachbit.General import WindowsError


def ini_helper(self, execute):
    """Used to test .ini cleaning in TestAction and in TestFileUtilities"""

    teststr = '#Test\n[RecentsMRL]\nlist=C:\\Users\\me\\Videos\\movie.mpg,C:\\Users\\me\\movie2.mpg\n'
    for encoding in ['utf-8', 'utf-8-sig']:
        with self.subTest(encoding=encoding):
            bom_size = 3 if 'utf-8-sig' == encoding else 0
            extra_size = bom_size
            if IS_WINDOWS:
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
            # Comments are not preserved, so only "[RecentsMRL]\n" (14
            # bytes) remains. The BOM is preserved, so utf-8-sig files
            # are 17 bytes and plain utf-8 files are 14 bytes. clean_ini
            # writes with newline='' so there is no \r\n expansion.
            execute(filename, 'RecentsMRL', 'list')
            self.assertEqual(14 + bom_size, os.path.getsize(filename))

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
    # pylint: disable-next=possibly-used-before-assignment
    return win32file.CreateFile(
        path,
        # pylint: disable-next=possibly-used-before-assignment
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
        super().tearDown()
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

        Example: 1,175,818 -> 1.2MB -> 1,200,000 is 2.06% different,
        but only 24,182 bytes, within half of the displayed 0.1MB step.
        """
        old_iec = options.get('units_iec')
        for units_iec in (False, True):
            options.set('units_iec', units_iec)
            base = 1024 if units_iec else 1000
            for k in range(0, 6):
                step = base ** k
                decimals = 2 if k >= 3 else (1 if k >= 1 else 0)
                half_step = 0.5 * 10 ** -decimals * step
                for frac in (1.0, 1.049, 1.05, 2.5, 7.5, 9.994, 9.995):
                    for delta in (-1, 0, 1):
                        bytes1 = int(frac * step) + delta
                        if bytes1 <= 0:
                            continue
                        human = bytes_to_human(bytes1)
                        if units_iec:
                            bytes2 = human_to_bytes(
                                human.replace('i', ''), 'du')
                        else:
                            bytes2 = human_to_bytes(human)
                        self.assertLessEqual(
                            abs(bytes2 - bytes1), half_step + 1,
                            f"{bytes1:,} -> {human} -> {bytes2:,} exceeds "
                            f"half a display unit ({half_step:,.0f})")
        options.set('units_iec', old_iec)

    def test_bytes_to_human_localization(self):
        """Test localization of bytes_to_human()"""
        if not hasattr(locale, 'format_string'):
            self.skipTest('Locale module does not support format_string')
        old_locale = locale.setlocale(locale.LC_NUMERIC, None)
        try:
            locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
        except locale.Error as e:
            logger.warning('exception when setlocale to de_DE.utf8: %s', e)
        else:
            try:
                self.assertEqual("1,01GB", bytes_to_human(1000 ** 3 + 5812389))
            finally:
                locale.setlocale(locale.LC_NUMERIC, old_locale)

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

    def test_children_in_directory_ordering(self):
        """Verify children_in_directory yields files before their parent directories.

        Regression test: with sibling directories, a dir could appear in the
        output before files contained inside it, causing rmdir to fail on a
        non-empty directory.

        Tree:
          root/
            file_root.txt
            sub1/
              file1.txt
              nested/
                file_nested.txt
            sub2/
              file2.txt
        """
        root = self.mkdir('directory-order-root')  # relative to self.tempdir
        sub1 = self.mkdir(os.path.join(root, 'sub1'))
        nested = self.mkdir(os.path.join(sub1, 'nested'))
        sub2 = self.mkdir(os.path.join(root, 'sub2'))

        file_root = self.mkstemp(prefix='file_root', dir=root)
        file1 = self.mkstemp(prefix='file1', dir=sub1)
        file_nested = self.mkstemp(prefix='file_nested', dir=nested)
        file2 = self.mkstemp(prefix='file2', dir=sub2)

        children = list(children_in_directory(root, list_directories=True))
        expected = [file_root, file1, file_nested, file2, sub1, nested, sub2]
        self.assertCountEqual(children, expected)

        idx = {p: children.index(p)
               for p in expected}

        self.assertLess(idx[file1], idx[sub1],
                        'file1 must appear before sub1')
        self.assertLess(idx[file_nested], idx[nested],
                        'file_nested must appear before nested')
        self.assertLess(idx[nested], idx[sub1],
                        'nested must appear before sub1')
        self.assertLess(idx[file2], idx[sub2],
                        'file2 must appear before sub2')
        for child in children:
            if os.path.isdir(child):
                self.assertTrue(is_dir_empty(child),
                                f'{child} must be empty before deletion')
            self.assertTrue(delete(child))
        self.assertTrue(delete(root))
        self.assertNotExists(root)

    def test_children_in_directory_scandir_unreadable_mid_iteration(self):
        """Regression test: a directory becoming unreadable mid-iteration
        must not abort the whole cleanup.

        os.walk silently skips directories that turn unreadable while being
        listed; _scan_children must do the same instead of propagating the
        OSError/PermissionError from the scandir iterator.
        """
        root = self.mkdir('scandir-unreadable-root')
        self.mkstemp(prefix='file_before', dir=root)

        class _FakeEntry:
            def __init__(self, path, is_dir=False):
                self.path = path
                self._is_dir = is_dir

            def is_dir(self):
                return self._is_dir

            def is_symlink(self):
                return False

        class _RaisingScandir:
            """Yields one file entry, then raises PermissionError mid-iteration."""

            def __init__(self, first_entry):
                self._first = first_entry

            def __iter__(self):
                return self

            def __next__(self):
                if self._first is None:
                    raise PermissionError('simulated mid-iteration failure')
                entry = self._first
                self._first = None
                return entry

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        first_entry = _FakeEntry(os.path.join(
            root, 'file_before'), is_dir=False)
        with unittest.mock.patch(
                'bleachbit.FileUtilities.os.scandir',
                return_value=_RaisingScandir(first_entry)):
            # Must not raise; entries yielded before the failure are kept.
            results = list(children_in_directory(root, list_directories=False))
        self.assertEqual(results, [os.path.join(root, 'file_before')])

    def test_children_in_directory_deep_tree(self):
        """Regression test: a deeply nested tree must not exhaust the
        recursion limit.

        A recursive walk raises RecursionError past about 1000 levels, which
        would abort the cleanup and leave the remaining files behind. os.scandir
        is faked so the depth is not capped by the platform's maximum path
        length.
        """
        depth = 5000

        class _FakeEntry:
            def __init__(self, path, is_dir):
                self.path = path
                self._is_dir = is_dir

            def is_dir(self):
                return self._is_dir

            def is_symlink(self):
                return False

            def is_junction(self):
                return False

        class _FakeScandir:
            def __init__(self, entries):
                self._entries = entries

            def __iter__(self):
                return iter(self._entries)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        # One subdirectory per level, with a single file at the bottom
        root = 'deep-tree-root'
        tree = {}
        path = root
        for _ in range(depth):
            child = os.path.join(path, 'a')
            tree[path] = [_FakeEntry(child, True)]
            path = child
        deep_file = os.path.join(path, 'deepfile')
        tree[path] = [_FakeEntry(deep_file, False)]

        with unittest.mock.patch('bleachbit.FileUtilities.os.scandir',
                                 side_effect=lambda p: _FakeScandir(tree[p])):
            results = list(children_in_directory(root, list_directories=True))

        self.assertEqual(len(results), depth + 1)
        # The file comes first, then the directories, deepest first
        self.assertEqual(results[0], deep_file)
        self.assertEqual(results[1], path)
        self.assertEqual(results[-1], os.path.join(root, 'a'))

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

    @common.skipIfWindows
    def test_children_below_path_max(self):
        """children_below() skips paths as long as PC_PATH_MAX"""
        top = self.mkdir('children-below-path-max')
        sub = self.mkdir(os.path.join(top, 'd'))
        kept = [self.write_file(os.path.join(top, 'f')),
                self.write_file(os.path.join(sub, 'f'))]
        long_dir = self.mkdir(os.path.join(top, 'long-dir'))
        skipped = [self.write_file(os.path.join(sub, 'ff')),
                   self.write_file(os.path.join(long_dir, 'f'))]

        path_max = len(os.fsencode(os.path.join(sub, 'ff')))
        with unittest.mock.patch('os.pathconf', return_value=path_max):
            self.assertCountEqual(dict(children_below(top)), kept)
        for fallback in ({'return_value': -1}, {'side_effect': OSError}):
            with unittest.mock.patch('os.pathconf', **fallback):
                self.assertCountEqual(dict(children_below(top)),
                                      kept + skipped)

    @common.skipIfWindows
    def test_children_below(self):
        """children_below() lists non-directories and never enters a link"""
        top = self.mkdtemp()
        real_file = self.write_file(os.path.join(top, 'file'), b'abc')
        nested = self.mkdir(os.path.join(top, 'sub', 'nested'))
        nested_file = self.write_file(os.path.join(nested, 'nested-file'))
        outside = self.mkdtemp()
        self.write_file(os.path.join(outside, 'outside-file'))
        dir_link = os.path.join(top, 'dir-link')
        os.symlink(outside, dir_link)

        found = dict(children_below(top))
        self.assertCountEqual(found, [real_file, nested_file, dir_link])
        self.assertTrue(stat.S_ISREG(found[real_file].st_mode))
        self.assertEqual(found[real_file].st_size, 3)
        self.assertTrue(stat.S_ISLNK(found[dir_link].st_mode))

    @common.skipIfWindows
    def test_children_below_deep(self):
        """children_below() holds no descriptor per directory level"""
        top = self.mkdir('children-below-deep')
        deep = self.mkdir(os.path.join(top, *['d'] * 20))
        path = self.write_file(os.path.join(deep, 'f'))
        real_open, real_close = os.open, os.close
        open_fds = set()
        peak = 0

        def counting_open(*args, **kwargs):
            nonlocal peak
            fd = real_open(*args, **kwargs)
            open_fds.add(fd)
            peak = max(peak, len(open_fds))
            return fd

        def counting_close(fd):
            open_fds.discard(fd)
            real_close(fd)

        with unittest.mock.patch('os.open', side_effect=counting_open), \
                unittest.mock.patch('os.close', side_effect=counting_close):
            self.assertEqual(list(dict(children_below(top))), [path])
        self.assertEqual(open_fds, set())
        self.assertLessEqual(peak, 2)

    @common.skipIfWindows
    def test_mount_points_below(self):
        """_mount_points_below() reads mounts below dirname from mountinfo"""
        top = self.mkdir('mount-points-below')
        real = os.path.realpath(top)
        mountinfo = ('22 1 8:1 / / rw - ext4 /dev/sda1 rw\n'
                     f'30 22 0:40 / {real} rw - tmpfs tmpfs rw\n'
                     f'31 30 8:1 /srv {real}/bind rw - ext4 /dev/sda1 rw\n'
                     f'32 30 0:41 / {real}/a\\040b rw - tmpfs tmpfs rw\n'
                     f'33 22 0:42 / {real}-sibling rw - tmpfs tmpfs rw\n')
        with unittest.mock.patch('bleachbit.FileUtilities.IS_LINUX', True):
            with unittest.mock.patch(
                    'bleachbit.FileUtilities.open', create=True,
                    new=unittest.mock.mock_open(read_data=mountinfo.encode())):
                self.assertEqual(_mount_points_below(top),
                                 {os.path.join(top, 'bind'),
                                  os.path.join(top, 'a b')})
            with unittest.mock.patch('bleachbit.FileUtilities.open',
                                     create=True, side_effect=OSError):
                self.assertEqual(_mount_points_below(top), set())
        with unittest.mock.patch('bleachbit.FileUtilities.IS_LINUX', False):
            self.assertEqual(_mount_points_below(top), set())

    @common.skipIfWindows
    def test_children_same_device_mount_table(self):
        """same_device also skips a bind mount, which keeps st_dev"""
        top = self.mkdir('children-mount-table')
        top_file = self.write_file(os.path.join(top, 'file'))
        bind = self.mkdir(os.path.join(top, 'bind'))
        bind_file = self.write_file(os.path.join(bind, 'file'))
        # A file can be bind-mounted onto another file
        file_bind = self.write_file(os.path.join(top, 'file-bind'))

        with unittest.mock.patch('bleachbit.FileUtilities._mount_points_below',
                                 return_value={bind, file_bind}):
            self.assertEqual(list(dict(children_below(top, same_device=True))),
                             [top_file])
            self.assertEqual(list(dict(children_below(
                top, list_directories=True, same_device=True))), [top_file])
            self.assertEqual(
                list(children_in_directory(top, True, same_device=True)),
                [top_file])
            self.assertCountEqual(children_in_directory(top, True),
                                  [top_file, bind_file, bind, file_bind])

    @common.skipIfWindows
    def test_children_in_directory_same_device(self):
        """children_in_directory(same_device=True) skips other filesystems"""
        top = self.mkdir('children-in-directory-device')
        top_file = self.write_file(os.path.join(top, 'file'))
        sub = self.mkdir(os.path.join(top, 'mounted'))
        sub_file = self.write_file(os.path.join(sub, 'file'))

        self.assertCountEqual(
            children_in_directory(top, True, same_device=True),
            [top_file, sub, sub_file])
        other_dev = unittest.mock.Mock(st_dev=os.stat(top).st_dev + 1)
        with unittest.mock.patch('os.stat', return_value=other_dev):
            self.assertEqual(
                list(children_in_directory(top, True, same_device=True)),
                [top_file])

    @common.skipIfWindows
    def test_children_below_same_device(self):
        """children_below(same_device=True) stays off other filesystems"""
        top = self.mkdir('children-below-device')
        top_file = self.write_file(os.path.join(top, 'file'))
        sub = self.mkdir(os.path.join(top, 'mounted'))
        sub_file = self.write_file(os.path.join(sub, 'file'))

        self.assertCountEqual(dict(children_below(top, same_device=True)),
                              [top_file, sub_file])
        # Mounting needs root, so top reports another device than its subdirs
        other_dev = unittest.mock.Mock(st_dev=os.stat(top).st_dev + 1)
        with unittest.mock.patch('os.fstat', return_value=other_dev):
            self.assertEqual(list(dict(children_below(top, same_device=True))),
                             [top_file])
            self.assertCountEqual(dict(children_below(top)),
                                  [top_file, sub_file])

    @common.skipIfWindows
    def test_children_below_search_only(self):
        """children_below() and delete() need only search permission above"""
        if not hasattr(os, 'O_PATH'):
            self.skipTest('O_PATH is not available')
        if os.geteuid() == 0:
            self.skipTest('root can read any directory')
        top = self.mkdir('children-below-search-only')
        middle = self.mkdir(os.path.join(top, 'middle'))
        sub = self.mkdir(os.path.join(middle, 'dir', 'sub'))
        path = self.write_file(os.path.join(sub, 'file'))
        os.chmod(top, 0o100)
        os.chmod(middle, 0o100)
        try:
            found = [p for p, _st in children_below(
                os.path.dirname(sub), list_directories=True, top=top)]
            self.assertEqual(found, [path, sub])
            for p in found:
                self.assertTrue(delete(p, shred=False, top=top))
        finally:
            os.chmod(middle, 0o700)
            os.chmod(top, 0o700)
        self.assertNotExists(sub)

    @common.skipIfWindows
    def test_children_below_log_root(self):
        """children_below() logs a directory it cannot open"""
        missing = os.path.join(self.tempdir, 'children-below-missing')
        with self.assertLogs('bleachbit.FileUtilities', level='DEBUG') as cm:
            self.assertEqual(list(children_below(missing)), [])
        self.assertIn(missing, cm.output[0])

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

    def test_clean_ini_refuses_symlink(self):
        """clean_ini() must not write through a symlink to another file

        With shred disabled, the original file is never deleted, so a
        (simulated) symlink at its path must block the write and leave
        the original content in place. With shred enabled, the original
        is deleted first as usual, and a symlink planted after that must
        still block the path from being recreated.
        """
        content = '[Section]\nkey=value\n'

        options.set('shred', False)
        filename = self.write_file('clean_ini_target_noshred', text=content)
        with unittest.mock.patch(
                'bleachbit.FileUtilities.os.path.islink',
                side_effect=lambda p: p == filename):
            with self.assertRaises(OSError):
                clean_ini(filename, 'Section', None)
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

        options.set('shred', True)
        filename = self.write_file('clean_ini_target_shred', text=content)
        with unittest.mock.patch(
                'bleachbit.FileUtilities.os.path.islink',
                side_effect=lambda p: p == filename and not os.path.lexists(p)):
            with self.assertRaises(OSError):
                clean_ini(filename, 'Section', None)
        self.assertNotExists(filename)

    def test_clean_json_refuses_symlink(self):
        """clean_json() must not write through a symlink to another file

        See test_clean_ini_refuses_symlink for why shred=True and
        shred=False need different post-conditions.
        """
        content = '{"deleteme": 1, "keep": 2}'

        options.set('shred', False)
        filename = self.write_file('clean_json_target_noshred', text=content)
        with unittest.mock.patch(
                'bleachbit.FileUtilities.os.path.islink',
                side_effect=lambda p: p == filename):
            with self.assertRaises(OSError):
                clean_json(filename, 'deleteme')
        with open(filename, encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

        options.set('shred', True)
        filename = self.write_file('clean_json_target_shred', text=content)
        with unittest.mock.patch(
                'bleachbit.FileUtilities.os.path.islink',
                side_effect=lambda p: p == filename and not os.path.lexists(p)):
            with self.assertRaises(OSError):
                clean_json(filename, 'deleteme')
        self.assertNotExists(filename)

    @common.skipIfWindows
    def test_clean_ini_json_symlink_with_shred(self):
        """A symlinked config is refused with shred as it is without"""
        cases = (('ini', '[Section]\nkey=value\n',
                  lambda path: clean_ini(path, 'Section', None)),
                 ('json', '{"deleteme": 1, "keep": 2}',
                  lambda path: clean_json(path, 'deleteme')))
        for shred in (False, True):
            options.set('shred', shred)
            for ext, content, clean in cases:
                with self.subTest(ext=ext, shred=shred):
                    config_dir = self.mkdtemp()
                    target = self.write_file(
                        os.path.join(config_dir, 'target.' + ext),
                        text=content)
                    link = os.path.join(config_dir, 'link.' + ext)
                    os.symlink(target, link)
                    with self.assertRaises(OSError):
                        clean(link)
                    self.assertTrue(os.path.islink(link))
                    with open(target, encoding='utf-8') as f:
                        self.assertEqual(f.read(), content)

    @pytest.mark.no_xdist
    def test_delete(self):
        """Unit test for method delete()"""
        for shred in (False, True):
            for delete_func in (delete, delete_file):
                with self.subTest(delete_func=delete_func.__name__, shred=shred):
                    self.delete_helper(delete_func, shred=shred)

    def test_delete_ignore_missing(self):
        """Unit test for delete() with ignore_missing=True"""
        self.assertFalse(delete('does-not-exist', ignore_missing=True))
        self.assertRaises(OSError, delete, 'does-not-exist')

    def test_delete_access_denied(self):
        """delete() raises PermissionError on access denied"""
        path = self.write_file('test_delete_access_denied', b'secret')
        e = PermissionError(13, 'Access is denied', path)
        if IS_WINDOWS:
            e.winerror = 5
        with unittest.mock.patch('os.remove', side_effect=e):
            with self.assertRaises(PermissionError):
                delete(path, shred=False)
        self.assertExists(path)

    @common.skipIfWindows
    def test_delete_top_refuses_link(self):
        """delete() with top does not go through a symlinked directory"""
        top = self.mkdtemp()
        outside = self.mkdtemp()
        secret = self.write_file(os.path.join(outside, 'secret'), b'secret')
        # Stands in for a directory swapped for a link after it was listed
        os.symlink(outside, os.path.join(top, 'link'))
        for shred in (False, True):
            with self.subTest(shred=shred):
                with self.assertRaises(OSError):
                    delete(os.path.join(top, 'link', 'secret'),
                           shred=shred, top=top)
                with open(secret, 'rb') as f:
                    self.assertEqual(f.read(), b'secret')

                sub = self.mkdir(os.path.join(top, 'sub'))
                inside = self.write_file(os.path.join(sub, 'inside'), b'abc')
                self.assertTrue(delete(inside, shred=shred, top=top))
                self.assertNotExists(inside)
                self.assertTrue(delete(sub + os.sep, shred=shred, top=top))
                self.assertNotExists(sub)

    @common.skipIfWindows
    def test_delete_top_error_filename(self):
        """An error from delete() with top names the whole path"""
        top = self.mkdir('delete-top-error')
        path = self.write_file(os.path.join(top, 'file'))

        for err_filename in (os.path.basename(path), None, 3):
            with self.subTest(err_filename=err_filename):
                err = PermissionError(
                    errno.EACCES, 'Permission denied', err_filename)
                with unittest.mock.patch('os.remove', side_effect=err):
                    with self.assertRaises(PermissionError) as cm:
                        delete(path, shred=False, top=top)
                self.assertEqual(cm.exception.errno, errno.EACCES)
                self.assertEqual(cm.exception.filename, path)
        self.assertExists(path)

        for bad_path in (os.path.join(self.tempdir, 'outside'), 'relative',
                         os.sep):
            with self.subTest(bad_path=bad_path):
                with self.assertRaises(OSError) as cm:
                    delete(bad_path, top=top)
                self.assertEqual(cm.exception.errno, errno.EINVAL)
                self.assertEqual(cm.exception.filename, bad_path)
        self.assertEqual(list(children_below(self.tempdir, top=top)), [])

    def test_delete_shred_overwrite_fails(self):
        """delete() warns when shredding cannot overwrite the contents"""
        path = self.write_file('test_delete_shred_overwrite_fails', b'secret')
        e = PermissionError(errno.EPERM, 'Operation not permitted', path)
        with unittest.mock.patch('bleachbit.FileUtilities.wipe_contents', side_effect=e):
            with self.assertLogs('bleachbit.FileUtilities', level='WARNING') as cm:
                self.assertTrue(delete(path, shred=True))
        self.assertIn('Could not overwrite', cm.output[0])
        # Without the \\?\ prefix on Windows
        self.assertIn(f'of {path}:', cm.output[0])
        self.assertNotExists(path)

        # When os.remove() also fails (e.g. a locked file), do not emit a
        # duplicate overwrite warning before raising the removal error.
        path2 = self.write_file('test_delete_shred_both_fail', b'secret')
        with unittest.mock.patch('bleachbit.FileUtilities.wipe_contents', side_effect=e), \
                unittest.mock.patch('os.remove', side_effect=e), \
                unittest.mock.patch('bleachbit.FileUtilities.logger.warning') as mock_warn:
            with self.assertRaises(PermissionError):
                delete(path2, shred=True)
            mock_warn.assert_not_called()

    def test_delete_shred_overwrite_fails_below_top(self):
        """The overwrite warning names the whole path of a file under top"""
        top = self.mkdtemp()
        sub = self.mkdir(os.path.join(top, 'sub'))
        path = self.write_file(os.path.join(sub, 'secret'), b'secret')
        e = PermissionError(errno.EPERM, 'Operation not permitted', path)
        with unittest.mock.patch('bleachbit.FileUtilities.wipe_contents', side_effect=e), \
                self.assertLogs('bleachbit.FileUtilities', level='WARNING') as cm:
            self.assertTrue(delete(path, shred=True, top=top))
        self.assertIn(f'of {path}:', cm.output[0])
        self.assertNotExists(path)

    def test_delete_windows_lstat_denied(self):
        """delete() on Windows still works where os.lstat() is denied

        Some Windows files give Access Denied to os.lstat() but not to the
        native os.path checks. There is no reliable way to create one in a
        test, so both are mocked.
        """
        denied = PermissionError(13, 'Access is denied')
        for isdir in (False, True):
            with self.subTest(isdir=isdir):
                mock_delete_file = unittest.mock.Mock()
                mock_delete_path = unittest.mock.Mock()
                with unittest.mock.patch.multiple(
                        'bleachbit.FileUtilities', IS_POSIX=False,
                        IS_WINDOWS=True, delete_file=mock_delete_file,
                        _delete_path=mock_delete_path), \
                        unittest.mock.patch('os.lstat', side_effect=denied), \
                        unittest.mock.patch('os.path.lexists', return_value=True), \
                        unittest.mock.patch('os.path.isdir', return_value=isdir), \
                        unittest.mock.patch('os.path.isfile', return_value=not isdir):
                    self.assertTrue(delete('C:\\locked'))
                if isdir:
                    mock_delete_file.assert_not_called()
                    self.assertIs(mock_delete_path.call_args.args[1], os.rmdir)
                else:
                    mock_delete_file.assert_called_once()
                    mock_delete_path.assert_not_called()

    def test_delete_windows_non_link_reparse_point(self):
        """delete() treats only links and unopenable reparse points as links"""
        cloud_tag = 0x9000601A
        junction_tag = 0xA0000003
        symlink_tag = 0xA000000C
        af_unix_tag = 0x80000023
        app_exec_link_tag = 0x8000001B
        # (reparse tag, isdir, _delete_path func, or None for delete_file)
        cases = ((0, True, os.rmdir),
                 (cloud_tag, True, os.rmdir),
                 (0, False, None),
                 (cloud_tag, False, None),
                 (junction_tag, True, os.remove),
                 (symlink_tag, False, os.remove),
                 (af_unix_tag, False, os.remove),
                 (app_exec_link_tag, False, os.remove))
        for tag, isdir, expected in cases:
            with self.subTest(tag=hex(tag), isdir=isdir):
                st = unittest.mock.Mock(
                    st_reparse_tag=tag,
                    st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
                mock_delete_file = unittest.mock.Mock()
                mock_delete_path = unittest.mock.Mock()
                with unittest.mock.patch.multiple(
                        'bleachbit.FileUtilities', IS_POSIX=False,
                        IS_WINDOWS=True, delete_file=mock_delete_file,
                        _delete_path=mock_delete_path), \
                        unittest.mock.patch('os.lstat', return_value=st), \
                        unittest.mock.patch('os.path.lexists', return_value=True), \
                        unittest.mock.patch('os.path.isdir', return_value=isdir), \
                        unittest.mock.patch('os.path.isfile', return_value=not isdir):
                    self.assertTrue(delete('C:\\placeholder', shred=not isdir))
                if expected is None:
                    mock_delete_file.assert_called_once()
                    self.assertTrue(mock_delete_file.call_args.args[1])
                    mock_delete_path.assert_not_called()
                else:
                    mock_delete_file.assert_not_called()
                    self.assertIs(mock_delete_path.call_args.args[1], expected)

    def delete_helper(self, delete_func, shred):
        """Called by test_delete() with shred = False and = True"""

        # test deleting with various kinds of filenames
        tests = common.SPECIAL_TEST_STRINGS.copy()
        if IS_POSIX:
            # Windows doesn't allow these characters but Unix systems do
            tests += common.POSIX_SPECIAL_TEST_STRINGS
        for test in tests:
            # create the file
            filename = self.write_file(test, b"top secret")
            # delete the file
            self.assertTrue(delete_func(filename, shred))
            self.assertNotExists(filename)

            # delete an empty directory
            dirname = self.mkdtemp(prefix=test)
            self.assertExists(dirname)
            # delete_file() doesn't delete directories, so do not use delete_func.
            self.assertTrue(delete(dirname, shred))
            self.assertNotExists(dirname)

        def symlink_helper(link_fn):
            if IS_WINDOWS:
                # pylint: disable=no-member
                if not win32com.shell.shell.IsUserAnAdmin():
                    self.skipTest(
                        'skipping symlink test because of insufficient privileges')

            # make regular file
            srcname = self.mkstemp(prefix='bleachbit-test-delete-regular')

            # make symlink
            self.assertExists(srcname)
            linkname = os.path.join(self.tempdir, 'bblink')
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

        if IS_WINDOWS:
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

        # test file with mode 0400/-r--------
        filename = self.write_file('bleachbit-test-0400')
        os.chmod(filename, 0o400)
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
            # pylint: disable=c-extension-no-member
            # pylint: disable-next=possibly-used-before-assignment
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
            filename = self.write_file('locked.txt', text='123')
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
                    self.assertTrue(delete_file(filename, shred))
                else:
                    # Delete expected to fail.
                    # WindowsError is a builtin on Windows and imported above otherwise.
                    # pylint: disable-next=undefined-variable, possibly-used-before-assignment
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
        try:
            self.assertTrue(os.path.isdir(to_dir))
            to_file = os.path.join(to_dir, 'normal-file')
            all_objs = (to_file, from_file, to_dir, from_dir)
            # os.path.isjunction() was added in Python 3.12, but BleachBit
            # supports older versions. Junctions are a Windows-only concept,
            # so on Linux the fallback always returns False.
            isjunction = getattr(os.path, 'isjunction', lambda _p: False)
            for func in (os.path.islink, isjunction, os.path.ismount, is_hard_link):
                for pathname in all_objs:
                    self.assertFalse(func(pathname))
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
        for top in (None, self.tempdir):
            for allow_shred in (False, True):
                with self.subTest(top=top, allow_shred=allow_shred):
                    self.assertFalse(delete(
                        dirname, shred=True, allow_shred=allow_shred, top=top))
                    self.assertExists(fn)
                    self.assertExists(dirname)
        os.remove(fn)
        self.assertTrue(is_dir_empty(dirname))

    def test_delete_shred_dir_filled_after_check(self):
        """A shredded directory that gains an entry keeps its name"""
        dirname = self.mkdir('filled_dir')
        fn = self.write_file(os.path.join(dirname, 'a_file'), b'content')
        # As if the entry was created after the emptiness check
        with unittest.mock.patch('bleachbit.FileUtilities.is_dir_empty',
                                 return_value=True):
            self.assertFalse(delete(dirname, shred=True))
        self.assertExists(fn)

    def test_delete_shred_dir_left_renamed(self):
        """The error names where a shredded directory is left renamed"""
        real_rename = os.rename

        def rename(src, dst, **kwargs):
            if os.path.basename(dst) == 'renamed_dir':
                raise PermissionError(errno.EACCES, 'Permission denied', src)
            return real_rename(src, dst, **kwargs)

        for top in (None, self.tempdir):
            with self.subTest(top=top):
                dirname = self.mkdir('renamed_dir')
                self.write_file(os.path.join(dirname, 'a_file'), b'content')
                with unittest.mock.patch(
                        'bleachbit.FileUtilities.is_dir_empty',
                        return_value=True), \
                        unittest.mock.patch('os.rename', side_effect=rename):
                    with self.assertRaises(OSError) as cm:
                        delete(dirname, shred=True, top=top)
                left = cm.exception.filename
                self.assertEqual(cm.exception.filename2, dirname)
                self.assertEqual(os.path.dirname(left), self.tempdir)
                self.assertNotEqual(os.path.basename(left), 'renamed_dir')
                self.assertExists(os.path.join(left, 'a_file'))
                self.assertNotExists(dirname)

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
        """Unit test for delete() with hard link

        - Tests both shredding and unlink.
        - Target is a file (not a directory).
        - Test is cross platform.
        """
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
                if IS_WINDOWS:
                    self.assertFalse(Windows.is_junction(link))
                self.assertDirectoryCount(tmp_dir, 2)
                self.assertTrue(is_hard_link(link))
                self.assertTrue(is_hard_link(target))
                if IS_POSIX:
                    symlink = os.path.join(tmp_dir, f'symlink-{shred}')
                    os.symlink(link, symlink)
                    dir_fd = os.open(tmp_dir, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        self.assertTrue(
                            is_hard_link(os.path.basename(link), dir_fd))
                        self.assertFalse(
                            is_hard_link(os.path.basename(symlink), dir_fd))
                    finally:
                        os.close(dir_fd)
                    os.unlink(symlink)

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
    def test_truncate_file_refuses_reparse_point(self):
        """truncate_file() refuses a junction or symlink target"""
        target_dir = self.mkdtemp(prefix='truncate-target')
        junction = os.path.join(self.mkdtemp(prefix='truncate'), 'link')
        self._create_win_junction(target_dir, junction)
        with self.assertRaises(OSError):
            truncate_file(junction)

    @common.skipIfWindows
    def test_truncate_file_refuses_symlink(self):
        """truncate_file() must not truncate a symlink's target"""
        target = self.write_file('truncate_target', b'keepme')
        link = os.path.join(self.tempdir, 'truncate_link')
        os.symlink(target, link)
        with self.assertRaises(OSError):
            truncate_file(link)
        self.assertEqual(os.path.getsize(target), len(b'keepme'))

    @common.skipIfWindows
    def test_truncate_locked_file_refuses_symlink(self):
        """_truncate_locked_file() must not truncate a symlink's target"""
        target = self.write_file('locked_truncate_target', b'keepme')
        link = os.path.join(self.tempdir, 'locked_truncate_link')
        os.symlink(target, link)
        self.assertFalse(_truncate_locked_file(link))
        self.assertEqual(os.path.getsize(target), len(b'keepme'))

    @common.skipUnlessWindows
    def test_delete_junction(self):
        """Unit test for delete() with Windows junction

        - Tests both shredding and unlink.
        - Tests junction (not directory symlink).
        - Target is a directory (not a file).
        - Target exists (not broken).
        - Test is Windows only.
        """
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
    def test_delete_junction_nonempty_target(self):
        """Unit test for delete() with a junction whose target is not empty

        Unlike test_delete_junction, the target here is non-empty. The
        junction itself should still be removed regardless.
        """
        for shred in (False, True):
            with self.subTest(shred=shred):
                tmp_dir = self.mkdtemp(prefix=f'delete_junction_ne_{shred}')
                target_dir = self.mkdtemp(
                    prefix=f'junction-target-ne-{shred}', dir=tmp_dir)
                target_file = self.mkstemp(
                    prefix='keep-me-', dir=target_dir)

                junction = os.path.join(tmp_dir, f'junction-ne-{shred}')
                self._create_win_junction(target_dir, junction)
                self.assertExists(junction)
                self.assertTrue(Windows.is_junction(junction))

                self.assertTrue(delete(junction, shred=shred))
                self.assertNotExists(junction)
                # The junction is gone, but its target and target's
                # contents must be completely untouched.
                self.assertExists(target_dir)
                self.assertExists(target_file)

    @common.skipUnlessWindows
    def test_delete_read_only_directory(self):
        """Unit test for delete() with read-only directory on Windows

        - Expects directory to be removed.
        - Tets both shred=True and False.
        """
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

    def test_clean_ini_non_utf8(self):
        """clean_ini() leaves a non-UTF-8 file untouched and logs an error"""
        # Latin-1 bytes that are invalid as UTF-8 (0xe9 = 'é' in Latin-1).
        content = b'[RecentsMRL]\nlist=\xe9\xe9\n'
        filename = self.write_file('bleachbit-test-ini-latin1', content)
        with open(filename, 'rb') as f:
            original = f.read()
        with self.assertLogs('bleachbit.FileUtilities', level='ERROR') as cm:
            clean_ini(filename, 'RecentsMRL', None)
        self.assertIn('not valid UTF-8', cm.output[0])
        # The file must not have been modified.
        with open(filename, 'rb') as f:
            self.assertEqual(original, f.read())
        delete(filename)
        self.assertNotExists(filename)

    @common.skipUnlessWindows
    def test_detect_encoding(self):
        """Unit test for detect_encoding

        The detect_encoding function is used only on Windows.

        Old Linux distributions (e.g., openSUSE 15.6) charset_normalizer <= 3.4.1
        misclassifies EUC-KR as big5hkscs. This was fixed in 3.4.2, but it's moot
        because detect_encoding is not used on Linux. Also, the standard winapp2.ini
        is ASCII as of September 2026.

        311e49c: added use of detect_encoding for Winapp

        498abfb: removed use of detect_encoding for cleaning .ini files, so
        detect_encoding is no longer needed on Linux.
        """
        eat_glass = '나는 유리를 먹을 수 있어요. 그래도 아프지 않아요'
        bom = '\ufeff' + eat_glass  # Add BOM for utf-8-sig
        # ASCII is valid UTF-8, so either answer reads the file correctly
        tests = (('This is just an ASCII file', ['ascii', 'utf-8']),
                 (eat_glass, ['utf-8']),
                 # Accept both EUC-KR and CP949 for Korean
                 (eat_glass, ['EUC-KR', 'CP949']),
                 (bom, ['UTF-8-SIG']))
        for file_contents, expected_encodings in tests:
            with self.subTest(encoding=expected_encodings):
                # Use first encoding for writing
                write_encoding = expected_encodings[0]

                with tempfile.NamedTemporaryFile(mode='w', delete=False,
                                                 dir=self.tempdir,
                                                 encoding=write_encoding) as temp:
                    temp.write(file_contents)
                    temp.flush()
                det = detect_encoding(temp.name)

                # Detectors spell codec names differently, so compare
                # the canonical names
                expected_names = [codecs.lookup(e).name
                                  for e in expected_encodings]
                self.assertIn(
                    codecs.lookup(det).name, expected_names,
                    f"{file_contents} -> {det}, expected one of {expected_encodings}")

    def test_detect_encoding_missing_charset_normalizer(self):
        """detect_encoding should log a warning when charset_normalizer is missing."""
        with common.mock_missing_package('charset_normalizer'):
            # Latin-1 is not valid UTF-8, so a detector is needed
            with tempfile.NamedTemporaryFile(mode='w', delete=False,
                                             dir=self.tempdir,
                                             encoding='latin-1') as temp:
                temp.write('café')
                temp.flush()
            with self.assertLogs('bleachbit.FileUtilities', level='WARNING') as cm:
                self.assertIsNone(detect_encoding(temp.name))
            self.assertIn(
                'charset_normalizer module is not available', cm.output[0])
            os.unlink(temp.name)

    def test_execute_sqlite3(self):
        """Unit test for execute_sqlite3()"""
        db_path = self.mkstemp(suffix='.sqlite')

        cmds = ['CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)',
                "INSERT INTO test (name) VALUES ('A'), ('B')",
                "UPDATE test SET name = 'C' WHERE name = 'B'",
                "DELETE FROM test WHERE name = 'C'"]

        execute_sqlite3(db_path, ';'.join(cmds))
        execute_sqlite3(db_path, 'vacuum')

        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            res = conn.execute("select 1 from test where name = 'A'")
            row = res.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)

        gc_collect()
        os.unlink(db_path)
        self.assertNotExists(db_path)

    def test_execute_sqlite3_semicolon_in_literal(self):
        """execute_sqlite3() keeps a ';' inside a literal, such as a path"""
        db_path = self.mkstemp(suffix='.sqlite')
        attach_path = os.path.join(self.mkdtemp(), 'a;b.sqlite')

        execute_sqlite3(
            db_path,
            "CREATE TABLE test (name TEXT);"
            "INSERT INTO test (name) VALUES ('x;y');"
            f"ATTACH DATABASE '{attach_path}' AS other;"
            "CREATE TABLE other.test (name TEXT)")

        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            rows = conn.execute('SELECT name FROM test').fetchall()
        self.assertEqual(rows, [('x;y',)])
        self.assertExists(attach_path)

        with self.assertRaises(sqlite3.OperationalError):
            execute_sqlite3(db_path, "INSERT INTO test (name) VALUES ('x")

    def test_execute_sqlite3_locked(self):
        """execute_sqlite3() fails fast on a locked database"""
        db_path = os.path.join(self.mkdtemp(), 'locked.sqlite')
        execute_sqlite3(db_path, 'CREATE TABLE test (id int)')
        holder = sqlite3.connect(db_path, isolation_level=None)
        try:
            holder.execute('PRAGMA locking_mode=EXCLUSIVE')
            holder.execute('BEGIN EXCLUSIVE')
            for cmd in ('DELETE FROM test', 'vacuum'):
                start = time.monotonic()
                with self.assertRaisesRegex(sqlite3.OperationalError,
                                            'database is locked'):
                    execute_sqlite3(db_path, cmd)
                self.assertLess(time.monotonic() - start, 3)
        finally:
            holder.close()

    def test_execute_sqlite3_open_error_translation(self):
        """Unit test for execute_sqlite3() open-error translation

        A cryptic sqlite3 "unable to open database file" must be translated
        into OSError(EACCES) (or FileNotFoundError if the path is gone) so the
        Worker can surface the same "Access denied" summary users see for
        locked files.
        """
        # Path whose parent directory does not exist: sqlite cannot create
        # it and raises "unable to open database file"; the path itself is
        # gone -> FileNotFoundError.
        gone_path = os.path.join(self.tempdir, 'no_such_subdir', 'gone.sqlite')
        self.assertNotExists(gone_path)
        with self.assertRaises(FileNotFoundError) as ctx:
            execute_sqlite3(gone_path, 'vacuum')
        self.assertEqual(ctx.exception.errno, errno.ENOENT)
        self.assertEqual(ctx.exception.filename, gone_path)

        # Path that exists but is a directory: sqlite cannot open a directory
        # as a database and raises "unable to open database file"; the path
        # is present -> OSError(EACCES) "Access denied".
        present_path = self.tempdir
        self.assertExists(present_path)
        with self.assertRaises(OSError) as ctx:
            execute_sqlite3(present_path, 'vacuum')
        self.assertEqual(ctx.exception.errno, errno.EACCES)
        self.assertEqual(ctx.exception.filename, present_path)
        self.assertIn('Access denied', ctx.exception.strerror)

    def test_exe_exists(self):
        """Unit test for exe_exists()"""
        tests = [("/bin/sh", True),
                 ("sh", True),
                 ("doesnotexist", False),
                 ("/bin/doesnotexist", False)]
        if IS_WINDOWS:
            tests = [('c:\\windows\\system32\\cmd.exe', True),
                     ('cmd.exe', True),
                     ('doesnotexist', False),
                     ('c:\\windows\\doesnotexist.exe', False)]
        for exe, expected in tests:
            with self.subTest(exe=exe, expected=expected):
                if IS_POSIX and not os.getenv('PATH') and not os.path.isabs(exe):
                    self.skipTest('PATH not set')
                self.assertEqual(exe_exists(exe), expected,
                                 f"{exe} -> {expected}")

    def test_exists_in_path(self):
        """Unit test for exists_in_path()"""
        filename = 'ls'
        if IS_WINDOWS:
            filename = 'cmd.exe'
        if IS_POSIX and not os.getenv('PATH'):
            self.assertFalse(exists_in_path(filename))
        else:
            self.assertTrue(exists_in_path(filename))
        self.assertFalse(exists_in_path('doesnotexist'))
        if IS_POSIX:
            with self.assertRaises(AssertionError):
                exists_in_path('/usr/bin/doesnotexist')
        if IS_WINDOWS:
            with self.assertRaises(AssertionError):
                exists_in_path('c:\\does\\not\\exist.exe')

    def test_expand_glob_join(self):
        """Unit test for expand_glob_join()"""
        if IS_POSIX:
            expand_glob_join('/bin', '*sh')
        if IS_WINDOWS:
            expand_glob_join(r'c:\windows', '*.exe')

    def test_expand_vars_user(self):
        """Unit test for expandvars() and expanduser()

        We had custom implementations of expandvars() and expanduser()
        until commit 3a3913 that switched to Python 3.
        """

        if IS_WINDOWS:
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
        if IS_WINDOWS:
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

    @common.skipUnlessWindows
    def test_extended_path_undo_unc_case(self):
        """Extended UNC prefixes are case insensitive."""
        path = r'\\server\share\folder\file.txt'
        for prefix in ('unc', 'UNC', 'Unc'):
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    path, extended_path_undo(fr'\\?\{prefix}\{path[2:]}'))

    def test_free_space(self):
        """Unit test for free_space()"""

        partitions = []
        os_paths = []
        if IS_WINDOWS:
            # Allow CD-ROM, network drive, etc.
            partitions = psutil.disk_partitions(all=True)
            os_paths = (r'%windir%', r'%userprofile%', r'%temp%')
        elif IS_POSIX:
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
                if IS_WINDOWS and not os.path.exists(path):
                    # e.g., disconnected network drive or empty CD-ROM
                    continue
                test_counter += 1
                try:
                    free = free_space(path)
                except OSError:
                    # e.g., disconnected network drive
                    continue
                self.assertIsInstance(
                    free, int, f"free_space({path}) should return int")
                self.assertGreaterEqual(
                    free, 0, f"free_space({path}) should be non-negative")
        self.assertGreater(test_counter, 0)

    def test_free_space_sub_dir(self):
        """Unit test for free_space() with subdirectories"""
        subdir = self.mkdtemp()
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
        if IS_WINDOWS:
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
        elif IS_POSIX:
            for check_path in (home, '/'):
                detected_fs = get_filesystem_type(check_path)[0]
                self.assertIn(detected_fs, [
                    'apfs', 'btrfs', 'ext4', 'ext3', 'ext2', 'xfs',
                    'hfs', 'squashfs', 'ufs', 'zfs', 'tmpfs', 'ffs',
                    'unknown'],
                    f"Unexpected file system type for {check_path}: {detected_fs}")

    def test_get_filesystem_type_cdrom(self):
        """Unit test for get_filesystem_type() on a CD-ROM drive"""
        cdrom_mounts = common.cdrom_mountpoints()
        if 'GITHUB_ACTIONS' in os.environ and (IS_LINUX or IS_WINDOWS):
            self.assertTrue(
                cdrom_mounts, 'Expected a mounted CD-ROM drive in CI')
        # Scan all partitions: cdrom_mountpoints() already filters on
        # is_cdrom and is_readonly, so asserting on its output cannot fail.
        for part in psutil.disk_partitions(all=False):
            fs_info = get_filesystem_type(part.mountpoint)
            # UDF is excluded: it can be writable (e.g., DVD-RAM).
            if fs_info.is_cdrom and fs_info.fstype.lower() != 'udf':
                self.assertTrue(fs_info.is_readonly, part)

    @common.skipUnlessMac
    def test_get_filesystem_type_macos(self):
        """get_filesystem_type handles firmlinks on macOS"""
        # The sealed system volume is read-only.
        root_fs_info = get_filesystem_type('/')
        self.assertTrue(root_fs_info.is_readonly)
        self.assertFalse(root_fs_info.is_cdrom)

        # Because of firmlinks, read-write paths like ~ resolve to the
        # root partition, which is a secured sealed volume, but
        # os.statvfs() sees through the firmlink to the read-write
        # data volume.
        for pathname in ('/tmp', os.path.expanduser('~')):
            fs_info = get_filesystem_type(pathname)
            self.assertFalse(fs_info.is_readonly)
            self.assertFalse(fs_info.is_cdrom)
            self.assertEqual(fs_info.fstype, root_fs_info.fstype)

    def test_get_filesystem_type_missing_psutil(self):
        """get_filesystem_type should return unknown when psutil is missing."""
        with common.mock_missing_package('psutil'):
            with self.assertLogs('bleachbit.FileUtilities', level='WARNING') as cm:
                result = get_filesystem_type('/')
            self.assertEqual(result, FilesystemInfo("unknown", "none", False))
            self.assertIn('psutil', cm.output[0])

    def test_getsize(self):
        """Unit test for method getsize()"""
        dirname = self.mkdtemp(prefix='bleachbit-test-getsize')

        def test_getsize_helper(fname):
            filename = self.write_file(os.path.join(
                dirname, fname), b"abcdefghij" * 12345)

            if IS_WINDOWS:
                self.assertEqual(getsize(filename), 10 * 12345)
                # Expand the directory names, which are in the short format,
                # to test the case where the full path (including the directory)
                # is longer than 255 characters.
                # pylint: disable=c-extension-no-member
                lname = win32api.GetLongPathNameW(extended_path(filename))
                self.assertEqual(getsize(lname), 10 * 12345)
                # this function returns a byte string instead of Unicode
                counter = 0
                for child in children_in_directory(dirname, False):
                    self.assertEqual(getsize(child), 10 * 12345)
                    counter += 1
                self.assertEqual(counter, 1)
            if IS_POSIX:
                encoding = sys.getdefaultencoding()
                output = str(subprocess.run(
                    ["du", "-h", filename], stdout=subprocess.PIPE,
                    check=False).stdout, encoding=encoding)
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

        if IS_WINDOWS:
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

    @common.skipIfWindows
    def test_getsize_sparse(self):
        """Test getsize() with a sparse file"""
        # macOS HFS+ did not support sparse files, but APFS does.
        logical_size = 1000 ** 2
        (handle, filename) = tempfile.mkstemp(
            prefix="bleachbit-test-sparse-", dir=self.tempdir)
        os.ftruncate(handle, logical_size)
        os.close(handle)
        allocated = getsize(filename)
        if IS_FREEBSD:
            # UFS still allocates a small amount of metadata (often 64KiB).
            self.assertEqual(os.lstat(filename).st_size, logical_size)
            self.assertLess(allocated, logical_size // 10,
                            f"sparse file allocated {allocated} bytes "
                            f"for logical size {logical_size}")
        else:
            self.assertEqual(allocated, 0)

    def test_getsizedir(self):
        """Unit test for getsizedir()"""
        path = '/bin'
        if IS_WINDOWS:
            path = 'c:\\windows\\system32'
        self.assertGreater(getsizedir(path), 0)

    def test_getsizedir_vanished(self):
        """getsizedir() skips a file that vanishes between the walk and the stat"""
        dirname = self.mkdtemp(prefix='bleachbit-test-getsizedir-vanished')
        real_fn = os.path.join(dirname, 'real')
        self.write_file(real_fn, contents=b'0123456789')
        expected = getsize(real_fn)
        self.assertGreater(expected, 0)

        ghost_fn = os.path.join(dirname, 'ghost')
        with unittest.mock.patch('bleachbit.FileUtilities.children_in_directory',
                                 return_value=iter([real_fn, ghost_fn])):
            self.assertEqual(getsizedir(dirname), expected)

        # Other errors must still propagate
        with unittest.mock.patch('bleachbit.FileUtilities.getsize',
                                 side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                getsizedir(dirname)

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
        if IS_POSIX:
            dir1 = '/bin'
            dir2 = os.path.expanduser('/sbin')
        elif IS_WINDOWS:
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
        self.assertLess(paths1, paths12)
        self.assertLess(paths2, paths12)
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
        if IS_WINDOWS:
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
        # FreeBSD lsof appends the mount device to NAME.
        with unittest.mock.patch('bleachbit.FileUtilities.IS_FREEBSD', True):
            self.assertEqual(list(open_files_lsof(
                lambda: 'n/tmp/foo (/dev/gpt/rootfs)\nn/bar/baz\nnoise')),
                ['/tmp/foo', '/bar/baz'])
        # Other lsof (e.g., macOS) does not append the device, so a real
        # file whose name ends in ' (/dev/x)' must not be mangled.
        with unittest.mock.patch('bleachbit.FileUtilities.IS_FREEBSD', False):
            self.assertEqual(list(open_files_lsof(
                lambda: 'n/tmp/foo (/dev/sr0)')),
                ['/tmp/foo (/dev/sr0)'])

    def test_open_files_psutil(self):
        """Unit test for open_files_psutil()"""
        fake_file = unittest.mock.Mock(path='/tmp/opened')
        proc = unittest.mock.Mock()
        proc.open_files.return_value = [fake_file]
        proc.memory_maps.return_value = []
        denied = unittest.mock.Mock()
        denied.open_files.side_effect = OSError('denied')
        empty = unittest.mock.Mock(path='')
        proc_empty = unittest.mock.Mock()
        proc_empty.open_files.return_value = [empty]
        proc_empty.memory_maps.return_value = []
        with unittest.mock.patch('psutil.process_iter', return_value=[proc, denied, proc_empty]):
            self.assertEqual(list(open_files_psutil()), ['/tmp/opened'])

    def test_open_files_psutil_mapped(self):
        """open_files_psutil() yields a file that is mapped but not open"""
        proc = unittest.mock.Mock()
        proc.open_files.return_value = []
        proc.memory_maps.return_value = [
            unittest.mock.Mock(path='/tmp/mapped'),
            unittest.mock.Mock(path='[anon]')]
        no_maps = unittest.mock.Mock()
        no_maps.open_files.return_value = []
        no_maps.memory_maps.side_effect = psutil.AccessDenied()
        with unittest.mock.patch('psutil.process_iter', return_value=[proc, no_maps]):
            self.assertEqual(list(open_files_psutil()), ['/tmp/mapped'])

    def test_open_files_freebsd_without_psutil(self):
        """open_files_freebsd() falls back to lsof when psutil is missing"""
        with unittest.mock.patch('bleachbit.FileUtilities.open_files_psutil',
                                 side_effect=ImportError('no psutil')), \
                unittest.mock.patch('bleachbit.FileUtilities.open_files_lsof',
                                    return_value=iter(['/tmp/via-lsof'])):
            self.assertEqual(list(open_files_freebsd()), ['/tmp/via-lsof'])

    @common.skipIfWindows
    def test_open_files(self):
        """Unit test for class OpenFiles"""

        filename = os.path.join(self.tempdir, 'bleachbit-test-open-files')
        # FreeBSD kinfo_getfile leaves kf_path empty for a newly created
        # O_WRONLY file (Python's 'wb'). Open an existing file for reading
        # so the kernel reports the path.
        self.write_file(filename, b'x')
        with open(filename, 'rb'):
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

    def test_open_files_linux_maps_unescape(self):
        """open_files_linux() decodes octal escapes in /proc/*/maps"""
        maps_data = (
            b'7f0000-7f1000 r--s 00000000 08:01 123 /tmp/a\\040b\\012c\n'
            b'7f1000-7f2000 rw-p 00000000 00:00 0 [heap]\n'
        )
        with unittest.mock.patch(
                'bleachbit.FileUtilities.glob.iglob',
                side_effect=[iter(['/proc/1/fd/3']), iter(['/proc/1/maps'])]), \
                unittest.mock.patch(
                    'bleachbit.FileUtilities.open', create=True,
                    new=unittest.mock.mock_open(read_data=maps_data)):
            self.assertEqual(list(open_files_linux()),
                             ['/proc/1/fd/3', '/tmp/a b\nc'])

    @common.skipUnlessLinux
    def test_open_files_mapped(self):
        """OpenFiles counts a file that is mapped but no longer open"""
        if sys.version_info < (3, 13):
            self.skipTest('mmap needs trackfd=False to not keep a descriptor')
        # The kernel escapes a newline in /proc/*/maps as \012
        filename = self.write_file(
            'bleachbit-test-open-files-mapped a\nb', b'x' * 4096)
        with open(filename, 'rb') as f:
            mapped = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ,
                               trackfd=False)
        try:
            self.assertTrue(OpenFiles().is_open(filename))
        finally:
            mapped.close()
        self.assertFalse(OpenFiles().is_open(filename))

    def test_same_partition(self):
        """Unit test for same_partition()"""
        home = os.path.expanduser('~')
        self.assertTrue(same_partition(home, home))
        if IS_POSIX:
            self.assertFalse(same_partition(home, '/dev'))
            if os.path.isdir('/proc') and os.path.isdir('/sys'):
                self.assertFalse(same_partition('/proc', '/sys'))
        elif IS_WINDOWS:
            home_drive = os.path.splitdrive(home)[0]
            from bleachbit.Windows import get_fixed_drives
            for drive in get_fixed_drives():
                this_drive = os.path.splitdrive(drive)[0]
                self.assertTrue(same_partition(drive, drive))
                self.assertEqual(same_partition(home, drive),
                                 home_drive == this_drive)

    def test_same_partition_device(self):
        """same_partition() compares devices, not only sizes or free space"""
        devices = {'/a': 1, '/b': 2, '/c': 3, '/d': 4, '/proc': 5, '/sys': 6}
        blocks = {'/a': (1000, 500), '/b': (1000, 400), '/c': (1000, 500),
                  '/d': (1000, 499), '/proc': (0, 0), '/sys': (0, 0)}

        def fake_stat(path):
            return unittest.mock.Mock(st_dev=devices[path])

        def fake_statvfs(path):
            f_blocks, f_bfree = blocks[path]
            return unittest.mock.Mock(f_blocks=f_blocks, f_bfree=f_bfree)

        with unittest.mock.patch('bleachbit.FileUtilities.IS_WINDOWS', False), \
                unittest.mock.patch('os.stat', side_effect=fake_stat), \
                unittest.mock.patch('os.statvfs', side_effect=fake_statvfs, create=True):
            self.assertTrue(same_partition('/a', '/a'))
            # different file systems of the same size
            self.assertFalse(same_partition('/a', '/b'))
            # btrfs subvolumes of one file system
            self.assertTrue(same_partition('/a', '/c'))
            # and one whose free space changed between the calls
            self.assertTrue(same_partition('/a', '/d'))
            # pseudo-filesystems with f_blocks == 0
            self.assertTrue(same_partition('/proc', '/proc'))
            self.assertFalse(same_partition('/proc', '/sys'))

        # Free space on C: changes between the two lookups
        changing_free_space = unittest.mock.Mock(side_effect=[1000, 996])
        with unittest.mock.patch('bleachbit.FileUtilities.IS_WINDOWS', True), \
                unittest.mock.patch('bleachbit.FileUtilities.free_space', changing_free_space), \
                unittest.mock.patch('os.stat', return_value=unittest.mock.Mock(st_dev=7)):
            self.assertTrue(same_partition('C:\\Temp', 'C:\\'))

        # Volumes with st_dev == 0 (such as zero-serial RAM disks) fall back
        # to comparing drive roots instead of colliding at 0 == 0.
        with unittest.mock.patch('bleachbit.FileUtilities.IS_WINDOWS', True), \
                unittest.mock.patch('os.stat', return_value=unittest.mock.Mock(st_dev=0)):
            self.assertTrue(same_partition('Z:\\Temp', 'z:\\'))
            self.assertFalse(same_partition('Y:\\Temp', 'Z:\\'))

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

        # Malformed file URIs must not yield an empty path, which previously
        # resolved to CWD in create_simple_cleaner.
        self.assertEqual(uris_to_paths(['file:']), [])
        self.assertEqual(uris_to_paths(['file://']), [])
        self.assertEqual(uris_to_paths(['file:///']), [os.path.normpath('/')])

    @common.skipIfWindows
    def test_uris_to_paths_undecodable(self):
        """A file URI for a name that is not valid UTF-8 gives the name on disk"""
        path = os.path.join(os.fsencode(self.tempdir), b'caf\xe9.txt')
        uri = 'file://' + urllib.parse.quote(path)
        # url2pathname() before Python 3.14
        with unittest.mock.patch('urllib.request.url2pathname', urllib.parse.unquote):
            self.assertEqual(uris_to_paths([uri]), [os.fsdecode(path)])

    def test_vacuum_sqlite3(self):
        """Unit test for method vacuum_sqlite3()"""
        path = os.path.join(self.tempdir, 'bleachbit_test_vacuum.sqlite3')
        conn = sqlite3.connect(path)
        # Use in-memory journal to avoid creating a transient
        # file that could trigger TOCTOU error in parallel tests.
        # (This prevents writing the `-journal` file, but the `.sqlite3`
        # database is still written.)
        conn.execute('PRAGMA journal_mode=memory')
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
        for _ in range(5):
            self.test_execute_sqlite3()
            self.test_vacuum_sqlite3()
            # Slow on OpenSUSE Build Service
            if time.time() - start_time > 30:
                logger.info(
                    "SQLite loop tests stopped early after %d seconds", time.time() - start_time)
                break
        logger.info(
            "SQLite loop tests fully completed after %d seconds", time.time() - start_time)

    def assert_is_whitelisted(self, path, allow_swapcase=True):
        """Helper to assert a path is whitelisted"""
        self.assertTrue(whitelisted(path),
                        f"Path {path} should be whitelisted")
        if allow_swapcase and not FS_CASE_SENSITIVE:
            self.assertTrue(whitelisted(path.swapcase()),
                            f"Path {path.swapcase()} should be whitelisted")

    def test_whitelisted(self):
        """Unit test for whitelisted()"""
        # FIXME: finish renaming whitelist to keep list
        # setup
        keep_list = [('file', '/home/foo'), ('folder', '/home/folder')]
        options.set_whitelist_paths(keep_list)
        self.assertEqual(set(keep_list), set(options.get_whitelist_paths()))

        # test
        # '/' is system-critical and always kept, so it is excluded here
        tests = ('', '/home/foo2', '/home/fo', '/home/', '/home')
        for path in tests:
            self.assertFalse(whitelisted(
                path), f"{path} should not be whitelisted")

        with self.assertRaises(TypeError):
            whitelisted(None)

        # Verbatim of whitelisted.
        self.assert_is_whitelisted('/home/foo')
        self.assert_is_whitelisted('/home/folder')
        if IS_POSIX:
            # Whitelisted + path separator.
            self.assert_is_whitelisted('/home/folder/')
            # File under whitelisted directory.
            self.assert_is_whitelisted('/home/folder/file')
        # Same as explicit whitelisted, minus one character.
        self.assertFalse(whitelisted('/home/folde'))
        # Same as explicit whitelisted, plus one character.
        self.assertFalse(whitelisted('/home/folder2'))

        # Test a blank whitelist.
        options.set_whitelist_paths([])
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

        # Remove the whitelist section from  the configuration.
        options.config.remove_section('whitelist/paths')
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

    def test_whitelisted_posix_system_critical(self):
        """System-critical POSIX paths are kept even with an empty keep list."""
        if not IS_POSIX:
            self.skipTest('POSIX only')
        options.set_whitelist_paths([])
        for path in ('/', '//', '/proc', '/proc/cpuinfo', '/sys/',
                     '/sys/kernel', '/run', '/run/user/0'):
            self.assertTrue(whitelisted(path),
                            f"{path} should be protected")
        # Real cleaners legitimately act under /var, /dev/shm, /etc
        for path in ('/home/user/file', '/tmp/scratch', '/opt/data/x',
                     '/etc/passwd', '/var/log/syslog', '/dev/shm/x',
                     '/procfile', '/sysfs2/x', ''):
            self.assertFalse(whitelisted(path),
                             f"{path} should not be protected")

    @common.skipIfWindows
    def test_whitelisted_posix_root_folder(self):
        """Keeping the filesystem root also keeps its descendants."""
        path = self.write_file('root_keep_test')
        link = os.path.join(self.tempdir, 'root_keep_link')
        os.symlink(path, link)
        for root in ('/', '/./', '///'):
            with self.subTest(root=root):
                options.set_whitelist_paths([('folder', root)])
                self.assertTrue(whitelisted(self.tempdir))
                self.assertTrue(whitelisted(path))
                self.assertTrue(whitelisted(link))
                self.assertFalse(whitelisted('relative/path'))
        options.set_whitelist_paths([('file', '/')])
        self.assertFalse(whitelisted(path))

    @common.skipIfWindows
    def test_whitelisted_posix_spelling_cache(self):
        """Normalize keep entries once, and refresh after edits or a new run."""
        clear_path_spellings()
        self.addCleanup(clear_path_spellings)
        keep = '/home/keep//folder/'
        options.set_whitelist_paths([('folder', keep)])
        with unittest.mock.patch(
                'bleachbit.FileUtilities._posix_keep_list_spelling',
                wraps=_posix_keep_list_spelling) as spelling:
            for _ in range(3):
                self.assertTrue(whitelisted('/home/keep/folder/child'))
            self.assertEqual(
                1, spelling.call_args_list.count(unittest.mock.call(keep)))
            options.set_whitelist_paths([('file', keep)])
            self.assertFalse(whitelisted('/home/keep/folder/child'))
            self.assertEqual(
                2, spelling.call_args_list.count(unittest.mock.call(keep)))
            options.set_whitelist_paths([('folder', '')])
            self.assertTrue(whitelisted('/home/elsewhere'))
            self.assertFalse(whitelisted('relative/path'))
            options.set_whitelist_paths([])
            self.assertFalse(whitelisted('/home/keep/folder'))
            options.set_whitelist_paths([('folder', '/home/other/')])
            self.assertFalse(whitelisted('/home/keep/folder/child'))
            self.assertTrue(whitelisted('/home/other/child'))
            clear_path_spellings()
            self.assertTrue(whitelisted('/home/other/child'))
            self.assertEqual(
                2, spelling.call_args_list.count(unittest.mock.call('/home/other/')))

    @common.skipIfWindows
    def test_whitelisted_posix_symlink_retarget(self):
        """Cached keep spellings must not freeze symlink targets."""
        first = self.write_file('first')
        second = self.write_file('second')
        kept_link = os.path.join(self.tempdir, 'kept_link')
        other_link = os.path.join(self.tempdir, 'other_link')
        os.symlink(first, kept_link)
        os.symlink(first, other_link)
        options.set_whitelist_paths([('file', kept_link)])
        self.assertTrue(whitelisted(other_link))
        os.unlink(kept_link)
        os.symlink(second, kept_link)
        self.assertFalse(whitelisted(other_link))
        self.assertTrue(whitelisted(kept_link))

    @unittest.skipUnless(IS_MAC, 'Requires native macOS Unicode path handling')
    def test_whitelisted_macos_decomposed_symlink(self):
        """Normalize resolved file and folder keeps, including descendants."""
        self.addCleanup(clear_path_spellings)
        root = self.mkdtemp()
        for kind in ('file', 'folder'):
            target = os.path.join(root, unicodedata.normalize(
                'NFD', kind + '-r\u00e9sum\u00e9'))
            if kind == 'folder':
                self.mkdir(target)
                child = self.write_file(os.path.join(
                    target, unicodedata.normalize('NFD', 'caf\u00e9')))
            else:
                self.write_file(target)
                child = target
            kept = os.path.join(root, unicodedata.normalize(
                'NFD', kind + '-gard\u00e9'))
            candidate = os.path.join(root, kind + '-candidate')
            descendant = os.path.join(root, kind + '-descendant')
            outside = os.path.join(root, kind + '-outside')
            os.symlink(target, kept)
            os.symlink(target, candidate)
            os.symlink(child, descendant)
            os.symlink(self.write_file(target + '2'), outside)
            self.assertTrue(os.path.samefile(
                target, unicodedata.normalize('NFC', target)))
            self.assertNotEqual(os.path.realpath(kept), unicodedata.normalize(
                'NFC', os.path.realpath(kept)))
            for keep_path in (target, kept):
                for form in ('NFD', 'NFC'):
                    with self.subTest(kind=kind, keep=keep_path, form=form):
                        options.set_whitelist_paths([
                            (kind, unicodedata.normalize(form, keep_path))])
                        for path in (keep_path, candidate, descendant):
                            with self.subTest(path=path):
                                self.assertTrue(whitelisted(path), path)
                        self.assertFalse(whitelisted(root))
                        self.assertFalse(whitelisted(target + '2'))
                        self.assertFalse(whitelisted(outside))

    @unittest.skipUnless(IS_MAC, 'Requires native macOS Unicode path handling')
    def test_whitelisted_macos_decomposed_symlink_retarget(self):
        """Neither keep-link nor candidate-link targets are cached in a run."""
        self.addCleanup(clear_path_spellings)
        root = self.mkdtemp()
        for kind in ('file', 'folder'):
            with self.subTest(kind=kind):
                targets = []
                candidates = []
                for index in range(2):
                    target = os.path.join(root, unicodedata.normalize(
                        'NFD', f'{kind}-{index}-r\u00e9sum\u00e9'))
                    if kind == 'folder':
                        self.mkdir(target)
                        child = self.write_file(os.path.join(
                            target, unicodedata.normalize('NFD', 'caf\u00e9')))
                    else:
                        self.write_file(target)
                        child = target
                    candidate = os.path.join(root, f'{kind}-candidate-{index}')
                    os.symlink(child, candidate)
                    targets.append(target)
                    candidates.append(candidate)
                kept = os.path.join(root, kind + '-kept')
                os.symlink(targets[0], kept)
                options.set_whitelist_paths([(kind, kept)])
                self.assertTrue(whitelisted(candidates[0]))
                self.assertFalse(whitelisted(candidates[1]))
                os.unlink(kept)
                os.symlink(targets[1], kept)
                self.assertFalse(whitelisted(candidates[0]))
                self.assertTrue(whitelisted(candidates[1]))
                os.unlink(candidates[0])
                os.symlink(os.readlink(candidates[1]), candidates[0])
                self.assertTrue(whitelisted(candidates[0]))
                os.unlink(candidates[1])
                os.symlink(targets[0], candidates[1])
                self.assertFalse(whitelisted(candidates[1]))

    @unittest.skipUnless(IS_MAC, 'Requires native macOS Unicode path handling')
    def test_whitelisted_macos_decomposed_spelling_cache(self):
        """Cached NFD keep spellings match both native NFD and NFC paths."""
        clear_path_spellings()
        self.addCleanup(clear_path_spellings)
        keep = self.mkdir(unicodedata.normalize('NFD', 'gard\u00e9'))
        child = self.write_file(os.path.join(keep, 'child'))
        options.set_whitelist_paths([('folder', keep)])
        with unittest.mock.patch(
                'bleachbit.FileUtilities._posix_keep_list_spelling',
                wraps=_posix_keep_list_spelling) as spelling:
            for _ in range(3):
                for form in ('NFD', 'NFC'):
                    self.assertTrue(whitelisted(
                        unicodedata.normalize(form, child)))
            self.assertEqual(
                1, spelling.call_args_list.count(unittest.mock.call(keep)))
            options.set_whitelist_paths([('file', keep)])
            self.assertFalse(whitelisted(child))
            self.assertEqual(
                2, spelling.call_args_list.count(unittest.mock.call(keep)))
            clear_path_spellings()
            self.assertTrue(whitelisted(unicodedata.normalize('NFC', keep)))
            self.assertEqual(
                3, spelling.call_args_list.count(unittest.mock.call(keep)))

    @common.skipIfWindows
    def test_whitelisted_posix_normpath(self):
        """Keep list matches paths spelled with '//' or a trailing '/'"""
        options.set_whitelist_paths(
            [('file', '/home/foo/cookies.sqlite'), ('folder', '/home/folder/')])
        self.assert_is_whitelisted('/home/foo//cookies.sqlite')
        self.assert_is_whitelisted('/home/folder')
        self.assert_is_whitelisted('/home//folder/model.bin')
        self.assertFalse(whitelisted('/home//folder2/model.bin'))

    @common.skipUnlessWindows
    def test_whitelisted_windows(self):
        """Test whitelisted() on Windows"""
        keep_list = [('folder', 'D:\\'),
                     ('file', 'c:\\windows\\foo.log'),
                     ('file', 'c:\\de\\straße.txt'),
                     ('folder', 'e:\\users')
                     ]
        options.set_whitelist_paths(keep_list)
        # verbatim paths
        self.assert_is_whitelisted('d:\\')
        self.assert_is_whitelisted('c:\\windows\\foo.log')
        self.assert_is_whitelisted('c:\\de\\straße.txt', False)
        self.assert_is_whitelisted('e:\\users')
        # explicit folder plus trailing slash
        self.assert_is_whitelisted('e:\\users\\')
        # file in explicit folder
        self.assert_is_whitelisted('e:\\users\\foo.log')
        self.assert_is_whitelisted('d:\\folder\\foo.log')
        # file in folder not in keep list
        self.assertFalse(whitelisted('e:\\windows\\foo.log'))
        # Same as whitelisted minus one character.
        self.assertFalse(whitelisted('e:\\user'))
        # Same as whitelisted plus a character.
        self.assertFalse(whitelisted('e:\\users2'))
        # Bare root of whitelisted folder
        self.assertFalse(whitelisted('e:\\'))
        self.assertFalse(whitelisted('e:'))
        # German Eszett
        # Windows treats 'ß' and 'ss' as separate filenames.
        self.assertEqual('ß'.lower(), 'ß')
        self.assertEqual('ß'.swapcase(), 'SS')
        self.assertNotEqual('ß'.swapcase().swapcase(), 'ß')
        self.assert_is_whitelisted('c:\\de\\STRAßE.TXT', False)
        self.assertFalse(whitelisted('c:\\de\\strasse.txt'))
        self.assertFalse(whitelisted('c:\\de\\straSSe.txt'))

    @common.skipUnlessWindows
    def test_whitelisted_windows_temp_roots(self):
        """Windows temp roots are preserved, but their contents are not."""
        options.set_whitelist_paths([])
        temp_roots = [
            r'C:\Windows\Temp',
            r'C:\WINDOWS\ServiceProfiles\MariaDB\AppData\Local\Temp',
            r'C:\Windows\ServiceProfiles\LocalService\AppData\Local\Temp',
            r'C:\Users\example\AppData\Local\Temp',
            r'C:\Documents and Settings\example\Local Settings\Temp',
        ]

        for temp_root in temp_roots:
            with self.subTest(temp_root=temp_root):
                self.assert_is_whitelisted(temp_root)
                self.assert_is_whitelisted(temp_root + '\\')
                self.assertFalse(whitelisted(temp_root + r'\bleachbit.tmp'))
                self.assertFalse(whitelisted(temp_root + r'\subdir'))

    @common.skipUnlessWindows
    def test_whitelisted_windows_aliases(self):
        """Keep list matches the Sysnative and 8.3 spellings of a kept path"""
        windir = os.path.expandvars('%windir%')
        options.set_whitelist_paths(
            [('folder', os.path.join(windir, 'System32', 'LogFiles'))])
        self.assert_is_whitelisted(
            os.path.join(windir, 'Sysnative', 'LogFiles', 'foo.log'))
        self.assertFalse(whitelisted(
            os.path.join(windir, 'SysWOW64', 'LogFiles', 'foo.log')))

        # pylint: disable=c-extension-no-member
        long_dir = win32api.GetLongPathName(
            self.mkdir(os.path.join(self.mkdtemp(), 'long directory name')))
        short_dir = win32api.GetShortPathName(long_dir)
        if short_dir == long_dir:
            self.skipTest('8.3 names are disabled on this volume')
        short_file = self.write_file(os.path.join(short_dir, 'foo.log'))
        options.set_whitelist_paths([('folder', long_dir)])
        self.assert_is_whitelisted(short_dir)
        self.assert_is_whitelisted(short_file)
        self.assert_is_whitelisted(extended_path(short_file))

    @common.skipUnlessWindows
    def test_whitelisted_windows_extended_paths(self):
        """Extended and ordinary paths honor the same keep entries."""
        folder = self.mkdir('extended keep folder')
        kept_file = self.write_file(os.path.join(folder, 'kept.txt'))
        other_file = self.write_file('not kept.txt')
        for kind, keep_path, candidate in (
                ('file', kept_file, kept_file),
                ('folder', folder, kept_file),
                ('folder', os.path.splitdrive(folder)[0] + os.sep, kept_file),
                ('file', r'\\server\share\kept.txt', r'\\server\share\kept.txt'),
                ('folder', r'\\server\share\kept', r'\\server\share\kept\file.txt')):
            spellings = [candidate, extended_path(candidate)]
            keep_spellings = [keep_path, extended_path(keep_path)]
            if candidate.startswith('\\\\'):
                spellings.append(extended_path(candidate).replace(
                    '\\unc\\', '\\UNC\\', 1))
                keep_spellings.append(extended_path(keep_path).replace(
                    '\\unc\\', '\\UNC\\', 1))
            for entry, path in itertools.product(keep_spellings, spellings):
                with self.subTest(kind=kind, entry=entry, path=path):
                    options.set_whitelist_paths([(kind, entry)])
                    self.assert_is_whitelisted(path)
                    if kind == 'file':
                        self.assertFalse(whitelisted(
                            extended_path(other_file)))
                    elif keep_path == folder:
                        self.assertFalse(whitelisted(
                            extended_path(folder + '2\\file.txt')))

    @common.skipUnlessWindows
    def test_whitelisted_windows_directory_cache_case(self):
        """Case variants share the native long-directory lookup."""
        # pylint: disable=c-extension-no-member
        long_dir = win32api.GetLongPathName(
            self.mkdir('long directory cache name'))
        short_dir = win32api.GetShortPathName(long_dir)
        if short_dir == long_dir:
            self.skipTest('8.3 names are disabled on this volume')
        short_file = self.write_file(os.path.join(short_dir, 'kept.txt'))
        options.set_whitelist_paths([('folder', long_dir)])
        with unittest.mock.patch.dict(
                'bleachbit.FileUtilities._long_dir_names', clear=True), \
                unittest.mock.patch(
                    'bleachbit.FileUtilities.win32file.GetLongPathName',
                    wraps=win32file.GetLongPathName) as native_long:
            self.assert_is_whitelisted(short_file)
            self.assertEqual(1, native_long.call_count)

    @common.skipUnlessWindows
    def test_whitelisted_windows_unsettled_entry_appears(self):
        """A missing 8.3 entry is retried when its directory reappears."""
        # pylint: disable=c-extension-no-member
        long_dir = win32api.GetLongPathName(
            self.mkdir('future keep directory'))
        short_dir = win32api.GetShortPathName(long_dir)
        if short_dir == long_dir:
            self.skipTest('8.3 names are disabled on this volume')
        os.rmdir(long_dir)
        clear_path_spellings()
        self.addCleanup(clear_path_spellings)
        options.set_whitelist_paths([('folder', short_dir)])
        candidate = os.path.join(long_dir, 'kept.txt')
        self.assertFalse(whitelisted(candidate))
        os.mkdir(long_dir)
        self.assertEqual(short_dir, win32api.GetShortPathName(long_dir))
        self.write_file(candidate)
        self.assert_is_whitelisted(candidate)

    @common.skipUnlessWindows
    def test_whitelisted_windows_spelling_cache(self):
        """Windows is asked for a long name once per directory and entry"""
        temp = r'C:\Users\JOHNSM~1\AppData\Local\Temp'
        keep_file = r'C:\Users\JOHNSM~1\Desktop\NEWFOL~1\keep.txt'
        created = []

        def long_name(path):
            if 'newfol~1' in path.lower() and not created:
                # pylint: disable-next=c-extension-no-member,possibly-used-before-assignment
                raise pywintypes.error(2, 'GetLongPathName', 'not found')
            return path.replace('JOHNSM~1', 'John Smith').replace(
                'NEWFOL~1', 'New folder')

        caches = (
            unittest.mock.patch.dict(
                'bleachbit.FileUtilities._long_dir_names', clear=True),
            unittest.mock.patch.dict(
                'bleachbit.FileUtilities._keep_list_cache',
                {'entries': (), 'spellings': {}}, clear=True))
        for cache in caches:
            cache.start()
            self.addCleanup(cache.stop)
        options.set_whitelist_paths(
            [('folder', temp + r'\keep'), ('file', keep_file)])
        with unittest.mock.patch(
                'bleachbit.FileUtilities.win32file.GetLongPathName',
                side_effect=long_name) as mock_long:
            for i in range(50):
                self.assertTrue(whitelisted(fr'{temp}\keep\file{i}.txt'))
                self.assertFalse(whitelisted(fr'{temp}\other\file{i}.txt'))
            temp_calls = [call.args[0] for call in mock_long.call_args_list
                          if 'appdata' in call.args[0].lower()]
            self.assertEqual(3, len(temp_calls), temp_calls)
            # the entry for a folder not created yet is spelled again later
            long_keep_file = r'C:\Users\John Smith\Desktop\New folder\keep.txt'
            self.assertFalse(whitelisted(long_keep_file))
            created.append(True)
            self.assertTrue(whitelisted(long_keep_file))
            # the next run asks again, for the entry and the directory
            clear_path_spellings()
            self.assertTrue(whitelisted(fr'{temp}\keep\file0.txt'))
            temp_calls = [call.args[0] for call in mock_long.call_args_list
                          if 'appdata' in call.args[0].lower()]
            self.assertEqual(5, len(temp_calls), temp_calls)

    @common.skipIfWindows
    def test_whitelisted_posix_symlink(self):
        """Symlink test for whitelisted_posix()"""
        # setup
        # reminder: unit tests run with a fresh config file each time,
        # so we do not need to keep the old settings.
        realpath = self.write_file('real')
        linkpath = os.path.join(self.tempdir, 'link')
        os.symlink(realpath, linkpath)
        self.assertExists(realpath)
        self.assertFalse(os.path.islink(realpath))
        self.assertExists(linkpath)
        self.assertTrue(os.path.islink(linkpath))

        # test 1: the real path is whitelisted
        keep_list1 = [('file', realpath)]
        options.set_whitelist_paths(keep_list1)
        self.assertFalse(whitelisted(self.tempdir))
        self.assertTrue(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        # test 2: the link is whitelisted
        keep_list2 = [('file', linkpath)]
        options.set_whitelist_paths(keep_list2)
        self.assertFalse(whitelisted(self.tempdir))
        self.assertFalse(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        # test 3: folder symlinks
        realfolder = self.mkdir('realfolder')
        linkfolder = os.path.join(self.tempdir, 'linkfolder')
        os.symlink(realfolder, linkfolder)

        keep_list3 = [('folder', realfolder)]
        options.set_whitelist_paths(keep_list3)
        self.assertTrue(whitelisted(realfolder))
        self.assertTrue(whitelisted(linkfolder))

    def test_whitelisted_speed(self):
        """Benchmark the speed of whitelisted()

        It is called frequently, so the speed is important."""
        d = '/usr/bin'
        # Not under /home: macOS automounts it, which makes realpath() of
        # the keep list slow
        keep_list = [('file', os.path.join(self.tempdir, 'foo')),
                     ('folder', os.path.join(self.tempdir, 'folder'))]
        if IS_WINDOWS:
            d = os.path.expandvars(r'%windir%\system32')
            keep_list = [('file', r'c:\filename'), ('folder', r'c:\\folder')]
        reps = 20
        paths = list(children_in_directory(d, True))
        paths = paths[:1000]  # truncate
        self.assertGreater(len(paths), 10)
        old_keep_list = options.get_whitelist_paths()
        options.set_whitelist_paths(keep_list)

        t0 = time.time()
        for _i in range(0, reps):
            for p in paths:
                _ = whitelisted(p)
        t1 = time.time()
        logger.info('whitelisted() with %d repetitions and %d paths took %g seconds',
                    reps, len(paths), t1 - t0)

        options.set_whitelist_paths(old_keep_list)
