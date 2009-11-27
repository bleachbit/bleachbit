# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Common code for unit tests
"""



import os
import types



def destructive_tests(title):
    """Return true if allowed to run destructive tests.  If false print notice."""
    if os.getenv('DESTRUCTIVE_TESTS') == 'T':
        return True
    print 'warning: skipping test(s) for %s because env. var. DESTRUCTIVE_TESTS not set' % title
    return False


def validate_result(self, result):
    """Validate the command returned valid results"""
    self.assert_(type(result) is dict, "result is a %s" % type(result))
    # label
    self.assert_(isinstance(result['label'], (str, unicode)))
    self.assert_(len(result['label'].strip()) > 0)
    # n_*
    self.assert_(isinstance(result['n_deleted'], (int, long)))
    self.assert_(result['n_deleted'] >= 0)
    self.assert_(result['n_deleted'] <= 1)
    self.assertEqual(result['n_special'] + result['n_deleted'], 1)
    # size
    self.assert_(isinstance(result['size'], (int, long, types.NoneType)), \
        "size is %s" % str(result['size']))
    # path
    filename = result['path']
    self.assert_(isinstance(filename, (str, unicode, types.NoneType)), \
        "Filename is invalid: '%s' (type %s)" % (str(filename), type(filename)))
    if isinstance(filename, (str, unicode)) and \
        not filename[0:2] == 'HK':
        self.assert_ (os.path.lexists(filename), \
            "Path does not exist: '%s'" % (filename))

