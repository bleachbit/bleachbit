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
Command design pattern implementation for cleaning

Standard clean up commands are Delete, Truncate and Shred. Everything
else is counted as special commands: run any external process, edit
JSON or INI file, delete registry key, edit SQLite3 database, etc.
"""

from bleachbit.Language import get_text as _
from bleachbit import FileUtilities

import logging
import os
import types
import warnings

if 'nt' == os.name:
    import bleachbit.Windows
else:
    from bleachbit.General import WindowsError

logger = logging.getLogger(__name__)


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

    def __str__(self):
        return 'Command to %s %s' % \
            ('shred' if self.shred else 'delete', self.path)

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
            except WindowsError as e:
                # WindowsError: [Error 32] The process cannot access the file because it is being
                # used by another process: 'C:\\Documents and
                # Settings\\username\\Cookies\\index.dat'
                if e.winerror not in (5, 32):
                    raise

                bleachbit.Windows.delete_locked_file(self.path)

                if self.shred:

                    warnings.warn(
                        _('At least one file was locked by another process, so its contents could not be overwritten. It will be marked for deletion upon system reboot.'))
                    # TRANSLATORS: The file will be deleted when the
                    # system reboots
                    ret['label'] = _('Mark for deletion')
        yield ret


class Function:

    """Execute a simple Python function"""

    def __init__(self, path, func, label, preview_func=None):
        """Initialize a Function command

        Parameters:
            path (str or None): Path to file or None if function doesn't operate on a file
            func (function): Function to execute that takes path or returns size
            label (str): Label for display in the UI
            preview_func (function, optional): Function to call in preview mode

        func and preview_func take no arguments and return an integer.
        """
        self.path = path
        self.func = func
        self.label = label
        self.preview_func = preview_func
        assert isinstance(path, (str, type(None)))
        if not isinstance(func, types.FunctionType):
            raise TypeError(
                f'Expected FunctionType for func but got {type(func)}')
        assert isinstance(label, str)
        if not isinstance(preview_func, (types.FunctionType, type(None))):
            raise TypeError(
                f'Expected FunctionType or None for preview_func but got {type(preview_func)}')

    def __str__(self):
        if self.path:
            return 'Function: %s: %s' % (self.label, self.path)
        return 'Function: %s' % (self.label)

    def execute(self, really_delete):
        """Execute the function and return results"""

        if self.path is not None and FileUtilities.whitelisted(self.path):
            yield whitelist(self.path)
            return

        ret = {
            'label': self.label,
            'n_deleted': 0,
            'n_special': 1,
            'path': self.path,
            'size': None}

        if not really_delete and self.preview_func is not None:
            # Preview mode: call preview function to get list of items that would be deleted
            try:
                preview_items = self.preview_func()
                if isinstance(preview_items, int):
                    ret['size'] = preview_items
            except Exception as e:
                logger.warning(f'Preview function failed: {e}')
                ret['size'] = 0
        elif really_delete:
            if self.path is None:
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
                assert isinstance(func_ret, int)
                ret['size'] = func_ret
            else:
                if os.path.isdir(self.path):
                    raise RuntimeError('Attempting to run file function %s on directory %s' %
                                       (self.func.__name__, self.path))
                # Function takes a path.  We check the size.
                oldsize = FileUtilities.getsize(self.path)

                from sqlite3 import DatabaseError
                try:
                    self.func(self.path)
                except DatabaseError as e:
                    # Firefox version 140 added a collation sequence that
                    # cannot be vacuumed.
                    # https://github.com/bleachbit/bleachbit/issues/1866
                    if 'no such collation sequence' in str(e):
                        logger.debug(str(e))
                        return
                    logger.exception(e)
                    return
                try:
                    newsize = FileUtilities.getsize(self.path)
                except OSError as e:
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

    def __str__(self):
        return 'Command to clean .ini path=%s, section=%s, parameter=%s ' % \
            (self.path, self.section, self.parameter)

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

    def __str__(self):
        return 'Command to clean JSON file, path=%s, address=%s ' % \
            (self.path, self.address)

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

    def __str__(self):
        return 'Command to shred %s' % self.path


class Truncate(Delete):

    """Truncate a single file"""

    def __str__(self):
        return 'Command to truncate %s' % self.path

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
            with open(self.path, 'w', encoding='ascii') as f:
                f.truncate(0)
        yield ret


class Winreg:

    """Clean Windows registry"""

    def __init__(self, keyname, valuename):
        """Create the Windows registry cleaner"""
        self.keyname = keyname
        self.valuename = valuename

    def __str__(self):
        return 'Command to clean registry, key=%s, value=%s ' % (self.keyname, self.valuename)

    def execute(self, really_delete):
        """Execute the Windows registry cleaner"""
        if 'nt' != os.name:
            return
        _str = None  # string representation
        ret = None  # return value meaning 'deleted' or 'delete-able'
        if self.valuename:
            _str = '%s<%s>' % (self.keyname, self.valuename)
            ret = bleachbit.Windows.delete_registry_value(self.keyname,
                                                          self.valuename, really_delete)
        else:
            ret = bleachbit.Windows.delete_registry_key(
                self.keyname, really_delete)
            _str = self.keyname
        if not ret:
            # Nothing to delete or nothing was deleted.  This return
            # makes the auto-hide feature work nicely.
            return

        ret = {
            'label': _('Delete registry key'),
            'n_deleted': 0,
            'n_special': 1,
            'path': _str,
            'size': 0}

        yield ret
