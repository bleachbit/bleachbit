# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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

import functools
import os
import shutil
import sys
import tempfile
import unittest

import mock

if 'win32' == sys.platform:
    import winreg
    import win32gui

import bleachbit
import bleachbit.Options
from bleachbit.FileUtilities import extended_path
from bleachbit.General import sudo_mode


class BleachbitTestCase(unittest.TestCase):
    """TestCase class with several convenience methods and asserts"""
    _patchers = []

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for the testcase"""
        cls.tempdir = tempfile.mkdtemp(prefix=cls.__name__)
        print(cls.tempdir)
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            cls._patch_options_paths()

    @classmethod
    def _patch_options_paths(cls):
        to_patch = [('bleachbit.options_dir', cls.tempdir),
                    ('bleachbit.options_file', os.path.join(cls.tempdir, "bleachbit.ini")),
                    ('bleachbit.personal_cleaners_dir', os.path.join(cls.tempdir, "cleaners"))]
        for target, source in to_patch:
            patcher = mock.patch(target, source)
            patcher.start()
            cls._patchers.append(patcher)

        bleachbit.Options.options.restore()

    @classmethod
    def tearDownClass(cls):
        """remove the temporary directory"""
        if os.path.exists(cls.tempdir):
            shutil.rmtree(cls.tempdir)
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            cls._stop_patch_options_paths()

    @classmethod
    def _stop_patch_options_paths(cls):
        for patcher in cls._patchers:
            patcher.stop()

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
        path = os.path.expandvars(path)
        if not self.check_exists(func, getTestPath(path)):
            raise AssertionError(
                f'The file {path} should exist, but it does not. {msg}')

    def assertNotExists(self, path, msg='', func=os.stat):
        if self.check_exists(func, getTestPath(path)):
            raise AssertionError(
                f'The file {path} should not exist, but it does. {msg}')

    def assertLExists(self, path, msg=''):
        self.assertExists(path, msg, os.lstat)

    def assertNotLExists(self, path, msg=''):
        self.assertNotExists(path, msg, os.lstat)

    def assertCondExists(self, cond, path, msg=''):
        if cond:
            self.assertExists(path, msg)
        else:
            self.assertNotExists(path, msg)

    #
    # file creation functions
    #
    def write_file(self, filename, contents=b'', mode='wb'):
        """Create a temporary file, optionally writing contents to it"""
        if not os.path.isabs(filename):
            filename = os.path.join(self.tempdir, filename)
        with open(extended_path(filename), mode) as f:
            f.write(contents)
        assert (os.path.exists(extended_path(filename)))
        return filename

    def mkstemp(self, **kwargs):
        if 'dir' not in kwargs:
            kwargs['dir'] = self.tempdir
        (fd, filename) = tempfile.mkstemp(**kwargs)
        os.close(fd)
        return filename

    def mkdtemp(self, **kwargs):
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
    """Put an environment variable. None removes the key"""
    if not val:
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


def touch_file(filename):
    """Create an empty file"""
    dname = os.path.dirname(filename)
    if not os.path.exists(dname):
        # Make the directory, if it does not exist.
        os.makedirs(dname)
    import pathlib
    pathlib.Path(filename).touch()
    assert os.path.exists(filename)


def validate_result(self, result, really_delete=False):
    """Validate the command returned valid results"""
    self.assertIsInstance(result, dict, f"result is a {type(result)}")
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
        None)), f"size is {str(result['size'])}")
    # path
    filename = result['path']
    if not filename:
        # the process action, for example, does not have a filename
        return
    self.assertIsInstance(filename, (str, type(None)),
                          f"Filename is invalid: '{filename}' (type {type(filename)})")
    if isinstance(filename, str) and not filename[0:2] == 'HK':
        if really_delete:
            self.assertNotLExists(filename)
        else:
            self.assertLExists(filename)


def get_winregistry_value(key, subkey):
    try:
        with winreg.OpenKey(key,  subkey) as hkey:
            return winreg.QueryValue(hkey, None)
    except FileNotFoundError:
        return None


def get_opened_windows_titles():
    opened_windows_titles = []

    def enumerate_opened_windows_titles(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            opened_windows_titles.append(win32gui.GetWindowText(hwnd))

    win32gui.EnumWindows(enumerate_opened_windows_titles, None)
    return opened_windows_titles
