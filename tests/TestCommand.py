# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2024 Andrew Ziem
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
Test case for Command
"""

import errno
import os
import warnings
from unittest import mock

import win32con
import win32file

from tests import common
from bleachbit import FileUtilities
from bleachbit.Command import Delete, Function, Shred


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

    def test_Function(self):
        """Unit test for Function"""
        path = self.write_file('test_Function', b'foo')
        cmd = Function(path, FileUtilities.delete, 'bar')
        self.assertExists(path)
        self.assertGreater(os.path.getsize(path), 0)

        # preview
        ret = next(cmd.execute(False))
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

    def test_Shred(self):
        """Unit test for Shred"""
        self.test_Delete(Shred)

    def test_Delete_not_deleted_reports_zero(self):
        """Do not report file deleted when delete() returns False"""
        dirname = self.mkdir('not_empty_delete')
        self.write_file(os.path.join(dirname, 'a_file'), b'content')
        cmd = Delete(dirname)
        ret = next(cmd.execute(really_delete=True))
        self.assertEqual(0, ret['n_deleted'])
        self.assertEqual(0, ret['size'])
        self.assertExists(dirname)

    def test_shred_access_denied_locked_file(self):
        """Shred on exclusively locked file leaves file intact.

        Non-admin: delete_locked_file fails, OSError (EACCES) is raised.
        Admin: file is marked for deletion on reboot instead.
        """
        path = self.write_file('test_Shred_access_denied', b'secret data')
        handle = win32file.CreateFile(
            path,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        try:
            cmd = Shred(path)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                try:
                    ret = next(cmd.execute(really_delete=True))
                except OSError as e:
                    self.assertEqual(errno.EACCES, e.errno)
                else:
                    self.assertEqual('Mark for deletion', ret['label'])
                    self.assertTrue(caught)
            self.assertExists(path)
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            win32file.CloseHandle(handle)
            if os.path.exists(path):
                FileUtilities.delete(path)

    def test_Delete_locked_file_access_denied_one_line(self):
        """When delete_locked_file fails, log one line without traceback"""
        from pywintypes import error as pywinerror

        from bleachbit import Windows

        path = self.write_file('test_Delete_locked_no_admin', b'locked')
        cmd = Delete(path)
        with mock.patch('bleachbit.FileUtilities.delete') as mock_delete:
            mock_delete.side_effect = PermissionError(
                13, 'Permission denied', path, 32)
            with mock.patch.object(Windows, 'delete_locked_file') as mock_del:
                mock_del.side_effect = pywinerror(
                    5, 'MoveFileExW', 'Access is denied.')
                with mock.patch('bleachbit.Command.logger') as mock_logger:
                    with self.assertRaises(OSError) as cm:
                        next(cmd.execute(really_delete=True))
                    self.assertEqual(errno.EACCES, cm.exception.errno)
                    mock_logger.exception.assert_not_called()
                    mock_logger.error.assert_called()

    def test_Delete_locked_file_shred_fallback(self):
        """Shred on a locked file falls back to mark for deletion"""
        from bleachbit import Windows
        from tests.TestFileUtilities import _open_blocking_handle

        path = self.write_file('test_Delete_locked', b'locked')
        handle = _open_blocking_handle(path, 0)
        cmd = Delete(path)
        cmd.shred = True
        try:
            with mock.patch('win32com.shell.shell.IsUserAnAdmin',
                            return_value=True):
                with mock.patch.object(Windows, 'delete_locked_file') as mock_del:
                    ret = next(cmd.execute(really_delete=True))
                    mock_del.assert_called_once_with(path)
                    self.assertEqual('Mark for deletion', ret['label'])
            self.assertExists(path)
        finally:
            win32file.CloseHandle(handle)
            if os.path.exists(path):
                FileUtilities.delete(path)

    def test_Function_sqlite_error(self):
        """Unit test for Function handling sqlite3 database errors"""
        import sqlite3
        path = self.write_file('test_Function_sqlite_error', b'not a valid sqlite database')

        def raise_database_error(path):
            # This simulates what happens when vacuum is called on a non-database file
            conn = sqlite3.connect(path)
            conn.execute('VACUUM')
            conn.close()

        cmd = Function(path, raise_database_error, 'test')
        # Should not raise an exception, just log and return
        with self.assertRaises(StopIteration):
            next(cmd.execute(True))
