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
Test case for module FileUtilities
"""

# standard library
import contextlib
import ctypes
import json
import locale
import os
import random
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import warnings

# local import
from bleachbit.FileUtilities import (
    bytes_to_human,
    children_in_directory,
    clean_ini,
    clean_json,
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
    listdir,
    open_files_lsof,
    OpenFiles,
    same_partition,
    sync,
    uris_to_paths,
    vacuum_sqlite3,
    whitelisted,
    wipe_contents,
    wipe_name,
    wipe_path
)
from bleachbit.General import gc_collect, run_external
from bleachbit.Options import options
from bleachbit import logger
from tests import common

if 'nt' == os.name:
    # pylint: disable=import-error
    import win32api
    import win32com.shell
    import win32con


def test_ini_helper(self, execute):
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


def test_json_helper(self, execute):
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


class FileUtilitiesTestCase(common.BleachbitTestCase):
    """Test case for module FileUtilities"""

    def setUp(self):
        """Call before each test method"""
        super().setUp()
        self.old_locale = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')

    def tearDown(self):
        """Call after each test method"""
        if self.old_locale == (None, None):
            locale.setlocale(locale.LC_NUMERIC, 'C')
            return
        try:
            if self.old_locale[0] is None:
                locale.setlocale(locale.LC_NUMERIC, None)
            else:
                try:
                    # First try with the full locale string
                    locale.setlocale(locale.LC_NUMERIC, '.'.join(
                        filter(None, self.old_locale)))
                except locale.Error:
                    # If that fails, try just the language code part
                    try:
                        locale.setlocale(locale.LC_NUMERIC, self.old_locale[0])
                    except locale.Error as e:
                        print(
                            "Failed to restore locale with just language code "
                            f"{self.old_locale[0]}: {e}")
        except locale.Error as e:
            print(f"Failed to restore locale {self.old_locale}: {e}")
        # Check that running getlocale again does not raise an exception.
        # For me, getlocale() fails after successful setlocale(..., 'en_MX') on Windows.
        locale.getlocale(locale.LC_NUMERIC)
        self.assertEqual(locale.getlocale(locale.LC_NUMERIC), self.old_locale)

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
        os.mkdir(subdirname)
        for filename in children_in_directory(dirname, True):
            self.assertEqual(filename, subdirname)
        for filename in children_in_directory(dirname, False):
            raise AssertionError(
                'Found a file that shouldn\'t have been found: ' + filename)
        os.rmdir(subdirname)

        os.rmdir(dirname)

    def test_clean_ini(self):
        """Unit test for clean_ini()"""
        print("testing test_clean_ini() with shred = False")
        options.set('shred', False, commit=False)
        test_ini_helper(self, clean_ini)

        print("testing test_clean_ini() with shred = True")
        options.set('shred', True, commit=False)
        test_ini_helper(self, clean_ini)

    def test_clean_json(self):
        """Unit test for clean_json()"""
        print("testing test_clean_json() with shred = False")
        options.set('shred', False, commit=False)
        test_json_helper(self, clean_json)

        print("testing test_clean_json() with shred = True")
        options.set('shred', True, commit=False)
        test_json_helper(self, clean_json)

    def test_delete(self):
        """Unit test for method delete()"""
        print("testing delete() with shred = False")
        self.delete_helper(shred=False)
        print("testing delete() with shred = True")
        self.delete_helper(shred=True)
        # exercise ignore_missing
        delete('does-not-exist', ignore_missing=True)
        self.assertRaises(OSError, delete, 'does-not-exist')

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
            delete(filename, shred)
            self.assertNotExists(filename)

            # delete an empty directory
            dirname = self.mkdtemp(prefix=test)
            self.assertExists(dirname)
            delete(dirname, shred)
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
            delete(linkname, shred)
            self.assertExists(srcname)
            self.assertNotLExists(linkname)

            # delete regular file
            delete(srcname, shred)
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
            delete(srcname, shred)
            self.assertNotExists(srcname)
            self.assertLExists(linkname)

            # clean up
            delete(linkname, shred)
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
                        f'CreateSymolicLinkW() failed, error = {ctypes.FormatError()}')
                    self.assertNotEqual(rc, 0)
            symlink_helper(win_symlink)

            return

        # below this point, only posix

        # test file with mode 0444/-r--r--r--
        filename = self.write_file('bleachbit-test-0444')
        os.chmod(filename, 0o444)
        delete(filename, shred)
        self.assertNotExists(filename)

        # test symlink
        symlink_helper(os.symlink)

        # test FIFO
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assertExists(filename)
        delete(filename, shred)
        self.assertNotExists(filename)

        # test directory
        path = self.mkdtemp(prefix='bleachbit-test-delete-dir')
        self.assertExists(path)
        delete(path, shred)
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
            delete(fn, shred=shred)
            self.assertNotExists(fn)

    @common.skipUnlessWindows
    def test_delete_locked(self):
        """Unit test for delete() with locked file"""
        # set up
        def test_delete_locked_setup():
            (fd, filename) = tempfile.mkstemp(
                prefix='bleachbit-test-fileutilities')
            os.write(fd, b'123')
            os.close(fd)
            self.assertExists(filename)
            self.assertEqual(3, getsize(filename))
            return filename

        # File is open but not opened exclusive, so expect that the
        # file is truncated but not deleted.
        # O_EXCL = fail if file exists (i.e., not an exclusive lock)
        filename = test_delete_locked_setup()
        f = os.open(filename, os.O_WRONLY | os.O_EXCL)
        self.assertExists(filename)
        self.assertEqual(3, getsize(filename))
        # pylint: disable=undefined-variable
        with self.assertRaises(WindowsError):
            delete(filename)
        os.close(f)
        self.assertExists(filename)
        self.assertEqual(0, getsize(filename))
        delete(filename)
        self.assertNotExists(filename)

        # File is open with exclusive lock, so expect the file is neither
        # deleted nor truncated.
        for allow_shred in (False, True):
            filename = test_delete_locked_setup()
            self.assertEqual(3, getsize(filename))
            fd = os.open(filename, os.O_APPEND | os.O_EXCL)
            self.assertExists(filename)
            self.assertEqual(3, getsize(filename))
            # pylint: disable=undefined-variable
            with self.assertRaises(WindowsError):
                delete(filename, shred=allow_shred, allow_shred=allow_shred)
            os.close(fd)
            self.assertExists(filename)
            if not allow_shred:
                # A shredding attempt truncates the file.
                self.assertEqual(3, getsize(filename))
            delete(filename)
            self.assertNotExists(filename)

    @common.skipIfWindows
    def test_delete_mount_point(self):
        """Unit test for deleting a mount point in use"""
        if not common.have_root():
            self.skipTest('not enough privileges')
        from_dir = os.path.join(self.tempdir, 'mount_from')
        to_dir = os.path.join(self.tempdir, 'mount_to')
        os.mkdir(from_dir)
        os.mkdir(to_dir)
        args = ['mount', '--bind', from_dir, to_dir]
        (rc, _, stderr) = run_external(args)
        self.assertEqual(
            rc, 0, f'error calling mount\nargs={args}\nstderr={stderr}')

        delete(to_dir)

        args = ['umount', to_dir]
        (rc, _, stderr) = run_external(args)
        self.assertEqual(
            rc, 0, f'error calling umount\nargs={args}\nstderr={stderr}')

    def test_delete_not_empty(self):
        """Test for scenario directory is not empty"""
        # common.py puts bleachbit.ini in self.tempdir, but it may
        # not be flushed
        dirname = os.path.join(self.tempdir, 'a_dir')
        os.mkdir(dirname)
        self.assertFalse(is_dir_empty(self.tempdir))
        self.assertTrue(is_dir_empty(dirname))
        fn = os.path.join(dirname, 'a_file')
        common.touch_file(fn)
        self.assertFalse(is_dir_empty(dirname))
        self.assertExists(fn)
        self.assertExists(dirname)
        self.assertExists(self.tempdir)

        # Make sure shredding does not leave a renamed directory like
        # in https://github.com/bleachbit/bleachbit/issues/783
        for allow_shred in (False, True):
            delete(dirname, allow_shred=allow_shred)
            self.assertExists(fn)
            self.assertExists(dirname)
        os.remove(fn)
        self.assertTrue(is_dir_empty(dirname))

    def test_delete_read_only(self):
        """Unit test for delete() with read-only file"""
        for shred in (False, True):
            fn = os.path.join(self.tempdir, 'read-only')
            common.touch_file(fn)
            os.chmod(fn, stat.S_IREAD)
            self.assertExists(fn)
            delete(fn, shred=shred)
            self.assertNotExists(fn)

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
            if not os.getenv(var):
                self.skipTest(f'Environment variable {var} not set')
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
        home = os.path.expanduser('~')
        result = free_space(home)
        self.assertNotEqual(result, None)
        self.assertGreater(result, -1)
        self.assertIsInteger(result)

    @common.skipUnlessWindows
    def test_free_space_windows(self):
        """Unit test for free_space() on Windows

        Repeat because of possible race condition.
        """
        args = ['wmic', 'LogicalDisk', 'get', 'DeviceID,', 'FreeSpace']
        max_attempts = 3

        def compare_free_space():
            """Returns whether all drives have equal free space"""
            (rc, stdout, stderr) = run_external(args)
            self.assertEqual(
                rc, 0, f'error calling WMIC\nargs={args}\nstderr={stderr}')
            lines = stdout.splitlines()
            self.assertGreater(len(lines), 0)
            for line in lines:
                line = line.strip()
                if not re.match(r'([A-Z]):\s+(\d+)', line):
                    continue
                drive, bytes_free = re.split(r'\s+', line)
                bytes_free = int(bytes_free)
                free = free_space(drive)
                if free != bytes_free:
                    logger.debug(
                        'Free space mismatch for drive %s: %s != %s', drive, free, bytes_free)
                    return False
            return True

        for attempt in range(max_attempts):
            if attempt > 0:
                time.sleep(0.5)
            if compare_free_space():
                return
            if attempt == max_attempts - 1:
                self.fail(
                    f'Failed to find equal free space after {max_attempts} attempts')

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

    def test_sync(self):
        """Unit test for sync()"""
        sync()

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
        for _ in range(50):
            self.test_execute_sqlite3()
            self.test_vacuum_sqlite3()

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
        tmpdir = os.path.join(self.tempdir, 'bleachbit-whitelist')
        os.mkdir(tmpdir)
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
        self.assertGreater(len(filename), len(newname))
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
        self.assertGreater(len(dir1), len(dir1new))
        self.assertNotExists(dir1)
        self.assertExists(dir1new)
        os.rmdir(dir1new)

        # wipe the directory
        os.rmdir(dir0)
        self.assertNotExists(dir0)

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
