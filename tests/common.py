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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Common code for unit tests
"""

import os
import shutil
import sys
import tempfile
import time
import unittest
import warnings
from pathlib import Path
from unittest import mock

if 'win32' == sys.platform:
    import winreg
    import win32gui
    from bleachbit import Windows

import bleachbit
import bleachbit.Options
from bleachbit.FileUtilities import (
    children_in_directory,
    extended_path,
    is_hard_link,
    is_normal_directory,
)
from bleachbit.General import gc_collect, sudo_mode


def _supports_stdout_char(char: str) -> bool:
    """Return True if sys.stdout can encode the given character."""
    encoding = (
        getattr(bleachbit, 'stdout_encoding', None)
        or getattr(sys.stdout, 'encoding', None)
        or sys.getdefaultencoding()
    )
    try:
        char.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


class BleachbitTestCase(unittest.TestCase):
    """TestCase class with several convenience methods and asserts"""
    _patchers = []

    @classmethod
    def setUpClass(cls):
        """Do common setup for the test case

        * Create a temporary directory for the testcase.
        * Treat warnings as errors.
        This is also set by environment variable in `Makefile` and
        `appveyor.yml`.
        * Patch options paths.
        """
        warnings.simplefilter("error")
        cls.tempdir = tempfile.mkdtemp(prefix=cls.__name__)
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            cls._patch_options_paths()
        bleachbit.Options.options.reset_overrides()
        bleachbit.Options.options.set_override("first_start", False)

    @classmethod
    def _patch_options_paths(cls):
        to_patch = [('bleachbit.options_dir', cls.tempdir),
                    ('bleachbit.options_file', os.path.join(
                        cls.tempdir, "bleachbit.ini")),
                    ('bleachbit.personal_cleaners_dir', os.path.join(cls.tempdir, "cleaners"))]
        for target, source in to_patch:
            patcher = mock.patch(target, source)
            patcher.start()
            cls._patchers.append(patcher)

        bleachbit.Options.options.restore()

    @classmethod
    def tearDownClass(cls):
        """Do common teardown for the test case

        * Collect garbage.
        * Remove the temporary directory.
        * Restore options paths.
        """
        bleachbit.Options.options.reset_overrides()
        gc_collect()
        # On Windows, a file may be temporarily locked, so retry.
        for attempt in range(5):
            try:
                if os.path.exists(cls.tempdir):
                    shutil.rmtree(cls.tempdir)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(1)
                else:
                    raise
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            cls._stop_patch_options_paths()

    @classmethod
    def _stop_patch_options_paths(cls):
        for patcher in cls._patchers:
            patcher.stop()

    def run(self, result=None):
        """Run the test case with conditional timer message"""
        start = time.perf_counter()
        outcome = super().run(result)
        duration = time.perf_counter() - start
        threshold = os.getenv('BLEACHBIT_SLOW_TEST_THRESHOLD')  # in seconds
        if threshold:
            threshold = float(threshold)
        if not threshold or threshold < 0:
            threshold = 30.0
        if duration >= threshold:
            test_id = f"{self.__class__.__name__}.{self._testMethodName}"
            prefix = "🐌 " if _supports_stdout_char("🐌") else ""
            print(f"{prefix}SLOW TEST: {test_id} ({duration:.1f}s)", flush=True)
        return outcome

    def setUp(cls):
        """Call before each test method"""
        basedir = os.path.join(os.path.dirname(__file__), '..')
        os.chdir(basedir)

    #
    # type asserts
    #

    def assertIsInteger(self, obj, msg=''):
        self.assertIsInstance(obj, int, msg)

    def assertIsString(self, obj, msg=''):
        self.assertIsInstance(obj, str, msg)

    def assertIsBytes(self, obj, msg=''):
        self.assertIsInstance(obj, bytes, msg)

    def assertIsLanguageCode(self, lang_id, msg=''):
        self.assertIsInstance(lang_id, str)
        if lang_id in ('C', 'C.UTF-8', 'C.utf8', 'POSIX'):
            return
        self.assertTrue(len(lang_id) >= 2)
        import re
        pattern = r'^[a-z]{2,3}([_-][A-Z][A-Za-z]{1,3})?(@\w+)?(\.[a-zA-Z][a-zA-Z0-9-]+)?$'
        self.assertTrue(re.match(pattern, lang_id),
                        f'Invalid language code format: {lang_id}')

    @staticmethod
    def check_exists(func, path):
        try:
            func(path)
            return True
        except PermissionError:
            # Python 3.4: on Windows os.path.[l]exists may return False when access is denied:
            # https://bugs.python.org/issue28075
            return True
        except:
            return False

    #
    # file asserts
    #
    def assertExists(self, path, msg='', func=os.stat):
        """File, directory, or any path exists"""
        if isinstance(path, Path):
            path = str(path)
        assert isinstance(
            path, str), f'path must be a string, not {type(path)}'
        path = os.path.expandvars(path)
        if not self.check_exists(func, getTestPath(path)):
            raise AssertionError(
                'The file %s should exist, but it does not. %s' % (path, msg))

    def assertNotExists(self, path, msg='', func=os.stat):
        if self.check_exists(func, getTestPath(path)):
            raise AssertionError(
                'The file %s should not exist, but it does. %s' % (path, msg))

    def assertLExists(self, path, msg=''):
        self.assertExists(path, msg, os.lstat)

    def assertNotLExists(self, path, msg=''):
        self.assertNotExists(path, msg, os.lstat)

    def assertCondExists(self, cond, path, msg=''):
        if cond:
            self.assertExists(path, msg)
        else:
            self.assertNotExists(path, msg)

    def assertDirectoryCount(self, path, count, list_directories=True):
        """Assert that a directory has a specific number of files

        - Counts recursively
        - Counts links
        - Does not recurse links

        """
        object_list = list(children_in_directory(path, list_directories))
        self.assertEqual(len(object_list), count, f"contains {len(object_list)} objects "
                         f"such as {object_list[:2]}, expected {count}")

    #
    # file creation functions
    #
    def write_file(self, filename, contents=b'', mode='wb', encoding=None):
        """Create a temporary file, optionally writing contents to it"""
        if not encoding and mode == 'w':
            encoding = 'utf-8'
        if not os.path.isabs(filename):
            filename = os.path.join(self.tempdir, filename)
        with open(extended_path(filename), mode, encoding=encoding) as f:
            f.write(contents)
        assert (os.path.exists(extended_path(filename)))
        with open(extended_path(filename), 'rb' if 'b' in mode else 'r', encoding=encoding if 'b' not in mode else None) as f:
            written_contents = f.read()
        expected = contents if 'b' in mode else contents.encode(
            encoding) if encoding else contents
        actual = written_contents if 'b' in mode else written_contents.encode(
            encoding) if encoding else written_contents
        assert actual == expected, f"File contents mismatch: expected {expected!r}, got {actual!r}"
        return filename

    def mkdir(self, dirname):
        """Create a directory with a given name

        If dirname is not absolute, it will be created in self.tempdir.

        Returns the path to the created directory.
        """
        assert isinstance(dirname, str)
        if not os.path.isabs(dirname):
            dirname = os.path.join(self.tempdir, dirname)
        ext_dirname = extended_path(dirname)
        os.makedirs(ext_dirname, exist_ok=True)
        self.assertExists(ext_dirname)
        self.assertTrue(os.path.isdir(ext_dirname))
        self.assertFalse(is_hard_link(ext_dirname))
        self.assertTrue(is_normal_directory(ext_dirname))
        self.assertFalse(os.path.isfile(ext_dirname))
        if os.name == 'nt':
            self.assertFalse(Windows.is_junction(ext_dirname))
        return dirname

    def mkstemp(self, **kwargs):
        if 'dir' not in kwargs:
            kwargs['dir'] = self.tempdir
        (fd, filename) = tempfile.mkstemp(**kwargs)
        os.close(fd)
        return filename

    def mkdtemp(self, **kwargs):
        """Create a temporary directory

        Objects under self.tempdir are automatically removed after testing.
        """
        if 'dir' not in kwargs:
            kwargs['dir'] = self.tempdir
        return tempfile.mkdtemp(**kwargs)


def getTestPath(path):
    if 'nt' == os.name:
        return extended_path(os.path.normpath(path))
    return path


def get_env(key):
    """Get an environment variable. If not set, returns None instead of KeyError."""
    if not key in os.environ:
        return None
    return os.environ[key]


def have_root():
    """Return true if we have root privileges on POSIX systems"""
    return sudo_mode() or os.getuid() == 0


def put_env(key, val):
    """Put an environment variable. None removes the key

    Returns None
    """
    if not val:
        if key in os.environ:
            del os.environ[key]
    else:
        os.environ[key] = val


def skipIfWindows(f):
    """Skip unit test if running on Windows"""
    return unittest.skipIf('win32' == sys.platform, 'running on Windows')(f)


def skipUnlessDestructive(f):
    """Skip unless destructive tests are allowed"""
    return unittest.skipUnless(os.getenv('DESTRUCTIVE_TESTS') == 'T', 'environment variable DESTRUCTIVE_TESTS not set to T')(f)


def skipUnlessWindows(f):
    """Skip unit test unless running on Windows"""
    return unittest.skipUnless('win32' == sys.platform, 'not running on Windows')(f)


def also_with_sudo(test_func):
    """
    Decorator to mark test methods that should be run both normally and with sudo.

    See also `tests/test_with_sudo.py`.
    """
    test_func._also_with_sudo = True
    return test_func


def touch_file(filename):
    """Create an empty file"""
    dname = os.path.dirname(filename)
    if not os.path.exists(dname):
        # Make the directory, if it does not exist.
        os.makedirs(dname)
    import pathlib
    pathlib.Path(filename).touch()
    assert (os.path.exists(filename))
    assert not is_normal_directory(filename)


def validate_result(self, result, really_delete=False):
    """Validate the command returned valid results"""
    self.assertIsInstance(result, dict, "result is a %s" % type(result))
    # label
    self.assertIsString(result['label'])
    self.assertGreater(len(result['label'].strip()), 0)
    # n_*
    self.assertIsInteger(result['n_deleted'])
    self.assertGreaterEqual(result['n_deleted'], 0)
    self.assertLessEqual(result['n_deleted'], 1)
    self.assertEqual(result['n_special'] + result['n_deleted'], 1)
    # size
    self.assertIsInstance(result['size'], (int, type(
        None),), "size is %s" % str(result['size']))
    # path
    filename = result['path']
    if not filename:
        # the process action, for example, does not have a filename
        return
    self.assertIsInstance(filename, (str, type(None)),
                          "Filename is invalid: '%s' (type %s)" % (filename, type(filename)))
    if isinstance(filename, str) and not filename[0:2] == 'HK':
        if really_delete:
            self.assertNotLExists(filename)
        else:
            self.assertLExists(filename)


def get_winregistry_value(key, subkey):
    try:
        with winreg.OpenKey(key, subkey) as hkey:
            return winreg.QueryValue(hkey, None)
    except FileNotFoundError:
        return None


def get_opened_windows_titles():
    """
    Get the titles of all opened windows.

    Returns:
        list: A list of window titles.
    """
    opened_windows_titles = []

    def enumerate_opened_windows_titles(hwnd, ctx):
        text = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowVisible(hwnd) and text:
            opened_windows_titles.append(text)

    win32gui.EnumWindows(enumerate_opened_windows_titles, None)
    return opened_windows_titles
