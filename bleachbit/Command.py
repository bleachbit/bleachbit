# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Command design pattern implementation for cleaning
"""


import os
import types
import FileUtilities

from sqlite3 import DatabaseError
from Common import _

if 'nt' == os.name:
    import Windows
else:
    from General import WindowsError


def whitelist(path):
    """Return information that this file was whitelisted"""
    ret = {
        # TRANSLATORS: This is the label in the log indicating was
        # skipped because it matches the whitelist
        'label': _('Skip'),
        'n_deleted': 0,
        'n_special': 0,
        'path': path,
        'size': 0}
    return ret


class Delete:

    """Delete a single file or directory.  Obey the user
    preference regarding shredding."""

    def __init__(self, path):
        """Create a Delete instance to delete 'path'"""
        self.path = path
        self.shred = False

    def execute(self, really_delete):
        """Make changes and return results"""
        if FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return
        ret = {
            # TRANSLATORS: This is the label in the log indicating will be
            # deleted (for previews) or was actually deleted
            'label': _('Delete'),
            'n_deleted': 1,
            'n_special': 0,
            'path': self.path,
            'size': FileUtilities.getsize(self.path)}
        if really_delete:
            try:
                FileUtilities.delete(self.path, self.shred)
            except WindowsError, e:
                # WindowsError: [Error 32] The process cannot access the file because it is being
                # used by another process: u'C:\\Documents and
                # Settings\\username\\Cookies\\index.dat'
                if 32 != e.winerror and 5 != e.winerror:
                    raise
                try:
                    Windows.delete_locked_file(self.path)
                except:
                    raise
                else:
                    # TRANSLATORS: The file will be deleted when the
                    # system reboots
                    ret['label'] = _('Mark for deletion')
        yield ret


class Function:

    """Execute a simple Python function"""

    def __init__(self, path, func, label):
        """Path is a pathname that exists or None.  If
        it exists, func takes the pathname.  Otherwise,
        function returns the size."""
        self.path = path
        self.func = func
        self.label = label
        try:
            assert(isinstance(func, types.FunctionType))
        except AssertionError:
            raise AssertionError('Expected MethodType but got %s' % type(func))

    def execute(self, really_delete):

        if None != self.path and FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return

        ret = {
            'label': self.label,
            'n_deleted': 0,
            'n_special': 1,
            'path': self.path,
            'size': None}

        if really_delete:
            if None == self.path:
                # Function takes no path.  It returns the size.
                func_ret = self.func()
                if isinstance(func_ret, types.GeneratorType):
                    # function returned generator
                    for func_ret in self.func():
                        if True == func_ret or isinstance(func_ret, tuple):
                            # Return control to GTK idle loop.
                            # If tuple, then display progress.
                            yield func_ret
                # either way, func_ret should be an integer
                assert(isinstance(func_ret, (int, long)))
                ret['size'] = func_ret
            else:
                # Function takes a path.  We check the size.
                oldsize = FileUtilities.getsize(self.path)
                try:
                    self.func(self.path)
                except DatabaseError, e:
                    if -1 == e.message.find('file is encrypted or is not a database') and \
                       -1 == e.message.find('or missing database'):
                        raise
                    print 'Warning:', e.message
                    return
                try:
                    newsize = FileUtilities.getsize(self.path)
                except OSError, e:
                    from errno import ENOENT
                    if e.errno == ENOENT:
                        # file does not exist
                        newsize = 0
                    else:
                        raise
                ret['size'] = oldsize - newsize
        yield ret


class Ini:

    """Remove sections or parameters from a .ini file"""

    def __init__(self, path, section, parameter):
        """Create the instance"""
        self.path = path
        self.section = section
        self.parameter = parameter

    def execute(self, really_delete):
        """Make changes and return results"""

        if FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return

        ret = {
            # TRANSLATORS: Parts of this file will be deleted
            'label': _('Clean file'),
            'n_deleted': 0,
            'n_special': 1,
            'path': self.path,
            'size': None}
        if really_delete:
            oldsize = FileUtilities.getsize(self.path)
            FileUtilities.clean_ini(self.path, self.section, self.parameter)
            newsize = FileUtilities.getsize(self.path)
            ret['size'] = oldsize - newsize
        yield ret


class Json:

    """Remove a key from a JSON configuration file"""

    def __init__(self, path, address):
        """Create the instance"""
        self.path = path
        self.address = address

    def execute(self, really_delete):
        """Make changes and return results"""

        if FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return

        ret = {
            'label': _('Clean file'),
            'n_deleted': 0,
            'n_special': 1,
            'path': self.path,
            'size': None}
        if really_delete:
            oldsize = FileUtilities.getsize(self.path)
            FileUtilities.clean_json(self.path, self.address)
            newsize = FileUtilities.getsize(self.path)
            ret['size'] = oldsize - newsize
        yield ret


class Shred(Delete):

    """Shred a single file"""

    def __init__(self, path):
        """Create an instance to shred 'path'"""
        Delete.__init__(self, path)
        self.shred = True


class Truncate(Delete):

    """Truncate a single file"""

    def execute(self, really_delete):
        """Make changes and return results"""

        if FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return

        ret = {
            # TRANSLATORS: The file will be truncated to 0 bytes in length
            'label': _('Truncate'),
            'n_deleted': 1,
            'n_special': 0,
            'path': self.path,
            'size': FileUtilities.getsize(self.path)}
        if really_delete:
            f = open(self.path, 'wb')
            f.truncate(0)
        yield ret


class Winreg:

    """Clean Windows registry"""

    def __init__(self, keyname, valuename):
        """Create the Windows registry cleaner"""
        self.keyname = keyname
        self.valuename = valuename

    def execute(self, really_delete):
        """Execute the Windows registry cleaner"""
        if 'nt' != os.name:
            raise StopIteration
        _str = None  # string representation
        ret = None  # return value meaning 'deleted' or 'delete-able'
        if self.valuename:
            _str = '%s<%s>' % (self.keyname, self.valuename)
            ret = Windows.delete_registry_value(self.keyname,
                                                self.valuename, really_delete)
        else:
            ret = Windows.delete_registry_key(self.keyname, really_delete)
            _str = self.keyname
        if not ret:
            # Nothing to delete or nothing was deleted.  This return
            # makes the auto-hide feature work nicely.
            raise StopIteration

        ret = {
            'label': _('Delete registry key'),
            'n_deleted': 0,
            'n_special': 1,
            'path': _str,
            'size': 0}

        yield ret
