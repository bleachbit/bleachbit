# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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

from __future__ import absolute_import, print_function

from bleachbit.FileUtilities import extended_path

import unittest
import shutil
import tempfile
import os
import os.path


class BleachbitTestCase(unittest.TestCase):
    """TestCase class with several convenience methods and asserts"""

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for the testcase"""
        cls.tempdir = tempfile.mkdtemp(prefix=cls.__name__)
        print(cls.tempdir)

    @classmethod
    def tearDownClass(cls):
        """remove the temporary directory"""
        shutil.rmtree(cls.tempdir)

    def setUp(cls):
        """Call before each test method"""
        basedir = os.path.join(os.path.dirname(__file__), '..')
        os.chdir(basedir)

    #
    # type asserts
    #
    def assertIsInteger(self, obj, msg=''):
        self.assertIsInstance(obj, (int, long), msg)

    def assertIsUnicodeString(self, obj, msg=''):
        self.assertIsInstance(obj, unicode, msg)

    def assertIsString(self, obj, msg=''):
        self.assertIsInstance(obj, (unicode, str), msg)

    def assertIsBytes(self, obj, msg=''):
        self.assertIsInstance(obj, bytes, msg)

    #
    # file asserts
    #
    def assertExists(self, path, msg='', func=os.path.exists):
        """File, directory, or any path exists"""
        from bleachbit import expandvars
        path = expandvars(path)
        if not func(getTestPath(path)):
            raise AssertionError('The file %s should exist, but it does not. %s' % (path, msg))

    def assertLExists(self, path, msg=''):
        self.assertExists(path, msg, os.path.lexists)

    def assertNotLExists(self, path, msg=''):
        self.assertNotExists(path, msg, os.path.lexists)

    def assertNotExists(self, path, msg='', func=os.path.exists):
        if func(getTestPath(path)):
            raise AssertionError('The file %s should not exist, but it does. %s' % (path, msg))

    def assertCondExists(self, cond, path, msg=''):
        if cond:
            self.assertExists(path, msg)
        else:
            self.assertNotExists(path, msg)

    #
    # file creation functions
    #
    def write_file(self, filename, contents=''):
        """Create a temporary file, optionally writing contents to it"""
        if not os.path.isabs(filename):
            filename = os.path.join(self.tempdir, filename)
        with open(extended_path(filename), 'wb') as f:
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


def destructive_tests(title):
    """Return true if allowed to run destructive tests.  If false print notice."""
    if os.getenv('DESTRUCTIVE_TESTS') == 'T':
        return True
    print('warning: skipping test(s) for %s because not getenv(DESTRUCTIVE_TESTS)=T' % title)
    return False


def touch_file(filename):
    """Create an empty file"""
    with open(filename, "w") as f:
        pass
    assert(os.path.exists(filename))


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
    self.assertIsInstance(result['size'], (int, long, type(None),), "size is %s" % str(result['size']))
    # path
    filename = result['path']
    if not filename:
        # the process action, for example, does not have a filename
        return
    self.assertIsInstance(filename, (str, unicode, type(None)),
                 "Filename is invalid: '%s' (type %s)" % (filename, type(filename)))
    if isinstance(filename, (str, unicode)) and not filename[0:2] == 'HK':
        if really_delete:
            self.assertNotLExists(filename)
        else:
            self.assertLExists(filename)


