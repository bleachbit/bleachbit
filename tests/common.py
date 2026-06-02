# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Common code for unit tests
"""

import mock
import os
import pathlib
import shutil
import tempfile
import unittest

import winreg
import win32gui

import bleachbit
import bleachbit.Options
from bleachbit.FileUtilities import extended_path, is_normal_directory
from bleachbit.Windows import is_junction, setup_environment


class BleachbitTestCase(unittest.TestCase):
    """TestCase class with several convenience methods and asserts"""
    _patchers = []

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for the testcase"""
        cls.tempdir = tempfile.mkdtemp(prefix=cls.__name__)
        print(cls.tempdir)
        setup_environment()
        if 'BLEACHBIT_TEST_OPTIONS_DIR' not in os.environ:
            cls._patch_options_paths()

    @classmethod
    def _patch_options_paths(cls):
        to_patch = [('bleachbit.OPTIONS_DIR', cls.tempdir),
                    ('bleachbit.OPTIONS_FILE', os.path.join(
                        cls.tempdir, "bleachbit.ini")),
                    ('bleachbit.PERSONAL_CLEANERS_DIR', os.path.join(cls.tempdir, "cleaners"))]
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
    @staticmethod
    def _assert_path(path):
        """Normalize a path for existence checks in unit tests."""
        # TestMakefile.py uses relative path without an environment variable.
        # TestWinapp.py uses variable "$bbtestdir"
        # However, do not expand paths that are already absolute.
        if not os.path.isabs(path):
            path = os.path.expandvars(path)
        return path

    def assertExists(self, path, msg='', func=os.stat):
        """File, directory, or any path exists"""
        path = self._assert_path(path)
        if not self.check_exists(func, getTestPath(path)):
            raise AssertionError(
                'The file %s should exist, but it does not. %s' % (path, msg))

    def assertNotExists(self, path, msg='', func=os.stat):
        path = self._assert_path(path)
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

    def mkdir(self, dirname):
        """Create a directory, checking it is a normal directory"""
        assert isinstance(dirname, str)
        if not os.path.isabs(dirname):
            dirname = os.path.join(self.tempdir, dirname)
        ext_dirname = extended_path(dirname)
        os.makedirs(ext_dirname, exist_ok=True)
        self.assertExists(ext_dirname)
        self.assertTrue(os.path.isdir(ext_dirname))
        self.assertTrue(is_normal_directory(ext_dirname))
        self.assertFalse(os.path.isfile(ext_dirname))
        self.assertFalse(is_junction(ext_dirname))
        return dirname

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
    return extended_path(os.path.abspath(os.path.normpath(path)))


def get_env(key):
    """Get an environment variable. If not set, returns None instead of KeyError."""
    if not key in os.environ:
        return None
    return os.environ[key]



def put_env(key, val):
    """Put an environment variable. None removes the key"""
    if not val:
        del os.environ[key]
    else:
        os.environ[key] = val

def skipUnlessDestructive(f):
    """Skip unless destructive tests are allowed"""
    return unittest.skipUnless(os.getenv('DESTRUCTIVE_TESTS') == 'T', 'environment variable DESTRUCTIVE_TESTS not set to T')(f)


def touch_file(filename):
    """Create an empty file"""
    dname = os.path.dirname(filename)
    if not os.path.exists(dname):
        # Make the directory, if it does not exist.
        os.makedirs(dname)
    pathlib.Path(filename).touch()
    assert(os.path.exists(filename))
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
