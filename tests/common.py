# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
from __future__ import absolute_import, division, print_function, unicode_literals

from bleachbit.FileUtilities import extended_path
from bleachbit.Common import ensure_unicode

import tempfile
import os
import six


class TypeAsserts():
    def assertIsInteger(self, obj, msg=''):
        self.assertIsInstance(obj, six.integer_types, msg)

    def assertIsString(self, obj, msg=''):
        if not isinstance(obj, six.text_type):
            raise AssertionError('Expected: string, found: %s (%s)' % (type(obj), obj))

    def assertIsBytes(self, obj, msg=''):
        self.assertIsInstance(obj, six.binary_type, msg)


class AssertFile:

    def getTestPath(self, path):
        if 'nt' == os.name:
            return extended_path(os.path.normpath(path))
        return path

    def assertExists(self, path, msg='', func=os.path.exists):
        """File, directory, or any path exists"""
        from bleachbit.Common import expandvars
        path = expandvars(path)
        if not func(self.getTestPath(path)):
            raise AssertionError(
                'The file %s should exist, but it does not. %s' % (path, msg))

    def assertLExists(self, path, msg=''):
        self.assertExists(path, msg, os.path.lexists)

    def assertNotLExists(self, path, msg=''):
        self.assertNotExists(path, msg, os.path.lexists)

    def assertNotExists(self, path, msg='', func=os.path.exists):
        if func(self.getTestPath(path)):
            raise AssertionError(
                'The file %s should not exist, but it does. %s' % (path, msg))

    def assertCondExists(self, cond, path, msg=''):
        if cond:
            self.assertExists(path, msg)
        else:
            self.assertNotExists(path, msg)


def destructive_tests(title):
    """Return true if allowed to run destructive tests.  If false print notice."""
    if os.getenv('DESTRUCTIVE_TESTS') == 'T':
        return True
    print('warning: skipping test(s) for %s because not getenv(DESTRUCTIVE_TESTS)=T' % title)
    return False


def touch_file(filename):
    """Create an empty file"""
    f = open(filename, "w")
    f.close()
    import os.path
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
    self.assertIsInstance(result['size'], six.integer_types + (type(None),), "size is %s" % str(result['size']))
    # path
    filename = result['path']
    if not filename:
        # the process action, for example, does not have a filename
        return
    from bleachbit.Common import encoding
    self.assertIsInstance(filename, (six.text_type, type(None)))
    if isinstance(filename, six.text_type) and not filename[0:2] == 'HK':
        if really_delete:
            self.assertNotLExists(filename)
        else:
            self.assertLExists(filename)


def write_file(filename, contents):
    """Write contents to file"""
    ensure_unicode(filename)
    with open(extended_path(filename), 'wb') as f:
        f.write(contents)


def touch_temp_file(contents=b'', **kwargs):
    """Creates a temporary file (same args as tempfile.mkstemp, optionally writes contents
    to it and returns the filename including the path"""
    (fd, filename) = tempfile.mkstemp(**kwargs)
    if contents:
        os.write(fd, contents)
    os.close(fd)
    return filename
