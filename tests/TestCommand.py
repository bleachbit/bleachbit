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

import os
from unittest import mock

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

    def test_Delete_locked_file_shred_fallback(self):
        """Shred on a locked file falls back to mark for deletion"""
        from pywintypes import error as pywinerror

        from bleachbit import Windows

        path = self.write_file('test_Delete_locked', b'locked')
        cmd = Delete(path)
        cmd.shred = True
        with mock.patch('win32com.shell.shell.IsUserAnAdmin',
                        return_value=True):
            with mock.patch('bleachbit.WindowsWipe.file_wipe') as mock_wipe:
                mock_wipe.side_effect = pywinerror(
                    32, 'CreateFileW',
                    'The process cannot access the file because it is '
                    'being used by another process.')
                with mock.patch.object(Windows, 'delete_locked_file') as mock_del:
                    ret = next(cmd.execute(really_delete=True))
                    mock_del.assert_called_once_with(path)
                    self.assertEqual('Mark for deletion', ret['label'])
        self.assertExists(path)

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
