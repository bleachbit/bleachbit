# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://www.bleachbit.org
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
import sys
import types

sys.path.append('.')
from bleachbit.FileUtilities import extended_path


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
    print 'warning: skipping test(s) for %s because not getenv(DESTRUCTIVE_TESTS)=T' % title
    return False


def touch_file(filename):
    """Create an empty file"""
    f = open(filename, "w")
    f.close()
    import os.path
    assert(os.path.exists(filename))


def validate_result(self, result, really_delete=False):
    """Validate the command returned valid results"""
    self.assert_(isinstance(result, dict), "result is a %s" % type(result))
    # label
    self.assert_(isinstance(result['label'], (str, unicode)))
    self.assert_(len(result['label'].strip()) > 0)
    # n_*
    self.assert_(isinstance(result['n_deleted'], (int, long)))
    self.assert_(result['n_deleted'] >= 0)
    self.assert_(result['n_deleted'] <= 1)
    self.assertEqual(result['n_special'] + result['n_deleted'], 1)
    # size
    self.assert_(isinstance(result['size'], (int, long, type(None))),
                 "size is %s" % str(result['size']))
    # path
    filename = result['path']
    if not filename:
        # the process action, for example, does not have a filename
        return
    from bleachbit.Common import encoding
    self.assert_(isinstance(filename, (str, unicode, type(None))),
                 "Filename is invalid: '%s' (type %s)" % (filename, type(filename)))
    if isinstance(filename, (str, unicode)) and \
            not filename[0:2] == 'HK':
        if really_delete:
            self.assertNotLExists(filename)
        else:
            self.assertLExists(filename)
