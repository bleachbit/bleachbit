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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Test case for Command
"""

import errno
import os
import sqlite3
import warnings
from unittest import mock

from tests import common
import bleachbit.Command
from bleachbit import FileUtilities, IS_WINDOWS
from bleachbit.Command import Delete, Function, Shred, Truncate
from bleachbit.Language import get_text as _
from bleachbit.Options import options

if not IS_WINDOWS:
    # pylint: disable-next=redefined-builtin
    from bleachbit.General import WindowsError


class CommandTestCase(common.BleachbitTestCase):
    """Test case for Command"""

    def test_Delete(self, cls=Delete):
        """Unit test for Delete"""
        path = self.write_file('test_Delete', b'foo')
        cmd = cls(path)
        self.assertExists(path)

        # preview
        ret = next(cmd.execute(really_delete=False))
        self.assertGreater(ret['size'], 0)
        self.assertEqual(ret['path'], path)
        self.assertExists(path)

        # delete
        ret = next(cmd.execute(really_delete=True))
        self.assertGreater(ret['size'], 0)
        self.assertEqual(ret['path'], path)
        self.assertNotExists(path)

    def test_delete_permission(self):
        """Test delete with permission denied for getsize()"""
        path = self.write_file('test_delete_permission', b'foo')
        cmd = Delete(path)
        self.assertExists(path)

        with mock.patch('bleachbit.FileUtilities.getsize') as mock_getsize:
            mock_getsize.side_effect = PermissionError('Permission denied')

            # preview
            ret = next(cmd.execute(really_delete=False))
            self.assertIsNone(ret['size'])
            self.assertEqual(ret['path'], path)
            self.assertExists(path)

    def test_Delete_locked_with_shred_option(self):
        """A locked file is reported as not overwritten when the global
        shred option is on, as with the Shred command"""
        path = self.write_file('test_Delete_locked', b'foo')
        # The overwrite and the delete both failed on a sharing violation
        if IS_WINDOWS:
            locked = PermissionError(errno.EACCES, 'locked', path)
            locked.winerror = 32
        else:
            # pylint: disable-next=possibly-used-before-assignment
            locked = WindowsError(32, 'locked')
        options.set('shred', True)
        with mock.patch('bleachbit.FileUtilities.delete', side_effect=locked), \
                mock.patch.object(bleachbit.Command, 'bleachbit', mock.Mock(),
                                  create=True) as fake_bleachbit, \
                warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            ret = next(Delete(path).execute(really_delete=True))
        fake_bleachbit.Windows.delete_locked_file.assert_called_once_with(
            FileUtilities.extended_path(path))
        self.assertEqual(ret['label'], _('Mark for deletion'))
        self.assertIn(UserWarning, [w.category for w in caught])

    def test_Delete_locked_extended_path(self):
        """A locked file is flagged for deletion by the same extended
        path that delete() uses, so a long path is found"""
        path = self.write_file('test_Delete_locked_extended', b'foo')
        if IS_WINDOWS:
            locked = PermissionError(errno.EACCES, 'locked', path)
            locked.winerror = 32
        else:
            # pylint: disable-next=possibly-used-before-assignment
            locked = WindowsError(32, 'locked')
        with mock.patch('bleachbit.FileUtilities.delete', side_effect=locked), \
                mock.patch('bleachbit.FileUtilities.extended_path',
                           side_effect=lambda p: '\\\\?\\' + p), \
                mock.patch.object(bleachbit.Command, 'bleachbit', mock.Mock(),
                                  create=True) as fake_bleachbit:
            next(Delete(path).execute(really_delete=True))
        fake_bleachbit.Windows.delete_locked_file.assert_called_once_with(
            '\\\\?\\' + path)

    def test_Function(self):
        """Unit test for Function"""
        path = self.write_file('test_Function', b'foo')
        cmd = Function(path, FileUtilities.delete, 'bar')
        self.assertExists(path)
        self.assertGreater(os.path.getsize(path), 0)

        # preview
        next(cmd.execute(False))
        self.assertExists(path)
        self.assertGreater(os.path.getsize(path), 0)

        # delete
        ret = next(cmd.execute(True))
        self.assertGreater(ret['size'], 0)
        self.assertEqual(ret['path'], path)
        self.assertNotExists(path)

    def test_Function_no_collation(self):
        """Unit test for Function with no collation

        See https://github.com/bleachbit/bleachbit/issues/1866
        """
        path = self.write_file('test_Function_no_collation', b'')
        cmd = Function(path,
                       lambda p: FileUtilities.execute_sqlite3(
                           p, 'CREATE TABLE test (name TEXT COLLATE foo);'),
                       'test_no_collation')

        with mock.patch('bleachbit.Command.logger.debug') as mock_debug:
            with self.assertRaises(StopIteration):
                next(cmd.execute(True))
            mock_debug.assert_called_with(mock.ANY)

    def test_Function_sqlite_error_propagates(self):
        """Unit test for Function with sqlite error that is not collation

        Non-collation sqlite errors must propagate to the Worker instead of
        being silently swallowed by Command.execute().
        """
        path = self.write_file('test_Function_sqlite_error', b'')
        cmd = Function(path,
                       lambda p: FileUtilities.execute_sqlite3(
                           p, 'SELECT * FROM nonexistent_table;'),
                       'test_sqlite_error')

        with self.assertRaises(sqlite3.OperationalError):
            next(cmd.execute(True))

    def test_Shred(self):
        """Unit test for Shred"""
        self.test_Delete(Shred)

    def test_Truncate(self):
        """Unit test for Truncate"""
        path = self.write_file('test_Truncate', b'foo')
        cmd = Truncate(path)

        # preview leaves the file intact
        ret = next(cmd.execute(really_delete=False))
        self.assertEqual(ret['path'], path)
        self.assertGreater(os.path.getsize(path), 0)

        # truncate empties the file but keeps it
        ret = next(cmd.execute(really_delete=True))
        self.assertEqual(ret['path'], path)
        self.assertExists(path)
        self.assertEqual(os.path.getsize(path), 0)
