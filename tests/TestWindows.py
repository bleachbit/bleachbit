# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module Windows
"""


import sys
import tempfile
import unittest
import platform

import common

if 'win32' == sys.platform:
    import _winreg
    from win32com.shell import shell

sys.path.append('.')
from bleachbit.Windows import *


def put_files_into_recycle_bin():
    """Put a file and a folder into the recycle bin"""
    # make a file and move it to the recycle bin
    import tempfile
    (fd, filename) = tempfile.mkstemp('bleachbit-recycle-file')
    os.close(fd)
    move_to_recycle_bin(filename)
    # make a folder and move it to the recycle bin
    dirname = tempfile.mkdtemp('bleachbit-recycle-folder')
    open(os.path.join(dirname, 'file'), 'a').close()
    move_to_recycle_bin(dirname)


class WindowsTestCase(unittest.TestCase):

    """Test case for module Windows"""

    def test_get_recycle_bin(self):
        """Unit test for get_recycle_bin"""
        for f in get_recycle_bin():
            self.assert_(os.path.exists(f))
        if not common.destructive_tests('get_recycle_bin'):
            return
        put_files_into_recycle_bin()
        # clear recycle bin
        counter = 0
        for f in get_recycle_bin():
            counter += 1
            FileUtilities.delete(f)
        self.assert_(counter >= 3, 'deleted %d' % counter)
        # now it should be empty
        for f in get_recycle_bin():
            self.fail('recycle bin should be empty, but it is not')

    def test_delete_locked_file(self):
        """Unit test for delete_locked_file"""
        tests = (('regular', u'unicode-emdash-u\u2014', 'long'+'x'*100))
        for test in tests:
            (fd, pathname) = tempfile.mkstemp(
                prefix='bleachbit-delete-locked-file',suffix=test)
            os.close(fd)
            self.assert_(os.path.exists(pathname))
            try:
                delete_locked_file(pathname)
            except pywintypes.error, e:
                if 5 == e.winerror and not shell.IsUserAnAdmin():
                    pass
                else:
                    raise
            self.assert_(os.path.exists(pathname))
        print 'NOTE: reboot Windows and check the three files are deleted'

    def test_delete_registry_key(self):
        """Unit test for delete_registry_key"""
        # (return value, key, really_delete)
        tests = ((False, 'HKCU\\Software\\BleachBit\\DoesNotExist', False, ),
                 (False, 'HKCU\\Software\\BleachBit\\DoesNotExist', True, ),
                 (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', False, ),
                 (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', True, ), )

        # create a nested key
        key = 'Software\\BleachBit\\DeleteThisKey'
        subkey = key + '\\AndThisKey'
        hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, subkey)
        hkey.Close()

        # test
        for test in tests:
            rc = test[0]
            key = test[1]
            really_delete = test[2]
            return_value = delete_registry_key(key, really_delete)
            self.assertEqual(rc, return_value)
            if really_delete:
                self.assertFalse(detect_registry_key(key))

        # Test Unicode key.  In BleachBit 0.7.3 this scenario would lead to
        # the error (bug 537109)
        # UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position
        # 11: ordinal not in range(128)
        key = r'Software\\BleachBit\\DeleteThisKey'
        hkey = _winreg.CreateKey(
            _winreg.HKEY_CURRENT_USER, key + r'\\AndThisKey-Ö')
        hkey.Close()
        return_value = delete_registry_key(u'HKCU\\' + key, True)
        self.assertTrue(return_value)
        return_value = delete_registry_key(u'HKCU\\' + key, True)
        self.assertFalse(return_value)

    def test_delete_registry_value(self):
        """Unit test for delete_registry_value"""

        #
        # test: value does exist
        #

        # create a name-value pair
        key = 'Software\\BleachBit'
        hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, key)

        value_name = 'delete_this_value_name'
        _winreg.SetValueEx(
            hkey, value_name, 0, _winreg.REG_SZ, 'delete this value')
        hkey.Close()

        # delete and confirm
        self.assertTrue(
            delete_registry_value('HKCU\\' + key, value_name, False))
        self.assertTrue(
            delete_registry_value('HKCU\\' + key, value_name, True))
        self.assertFalse(
            delete_registry_value('HKCU\\' + key, value_name, False))
        self.assertFalse(
            delete_registry_value('HKCU\\' + key, value_name, True))

        #
        # test: value does not exist
        #
        self.assertFalse(delete_registry_value(
            'HKCU\\' + key, 'doesnotexist', False))
        self.assertFalse(delete_registry_value(
            'HKCU\\' + key, 'doesnotexist', True))
        self.assertFalse(delete_registry_value(
            'HKCU\\doesnotexist', value_name, False))
        self.assertFalse(delete_registry_value(
            'HKCU\\doesnotexist', value_name, True))

    def test_detect_registry_key(self):
        """Test for detect_registry_key()"""
        self.assert_(detect_registry_key('HKCU\\Software\\Microsoft\\'))
        self.assert_(not detect_registry_key('HKCU\\Software\\DoesNotExist'))

    def test_get_autostart_path(self):
        """Unit test for get_autostart_path"""
        pathname = get_autostart_path()
        dirname = os.path.dirname(pathname)
        self.assert_(os.path.exists(dirname),
                     'startup directory does not exist: %s' % dirname)

    def test_get_known_folder_path(self):
        """Unit test for get_known_folder_path"""
        version = platform.uname()[3][0:3]
        ret = get_known_folder_path('LocalAppDataLow')
        self.assertNotEqual(ret, '')
        if version <= '6.0':
            # Before Vista
            self.assertEqual(ret, None)
            return
        # Vista or later
        self.assertNotEqual(ret, None)
        self.assert_(os.path.exists(ret))

    def test_get_fixed_drives(self):
        """Unit test for get_fixed_drives"""
        drives = []
        for drive in get_fixed_drives():
            drives.append(drive)
            self.assertEqual(drive, drive.upper())
        self.assert_("C:\\" in drives)

    def test_empty_recycle_bin(self):
        """Unit test for empty_recycle_bin"""
        # check the function basically works
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=False)
            self.assert_(isinstance(ret, (int, long)))
        if not common.destructive_tests('recycle bin'):
            return
        # check it deletes files for fixed drives
        put_files_into_recycle_bin()
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=True)
            self.assert_(isinstance(ret, (int, long)))
        # check it deletes files for all drives
        put_files_into_recycle_bin()
        ret = empty_recycle_bin(None, really_delete=True)
        self.assert_(isinstance(ret, (int, long)))
        # Repeat two for reasons.
        # 1. Trying to empty an empty recycling bin can cause
        #    a 'catastrophic failure' error (handled in the function)
        # 2. It should show zero bytes were deleted
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=True)
            self.assertEqual(ret, 0)

    def test_is_process_running(self):
        tests = ((True, 'explorer.exe'),
                 (True, 'ExPlOrEr.exe'),
                 (False, 'doesnotexist.exe'))
        for test in tests:
            self.assertEqual(test[0], is_process_running(
                test[1]), 'is_process_running(%s) != %s' % (test[1], test[0]))
            self.assertEqual(test[0], is_process_running_win32(test[1]))
            self.assertEqual(test[0], is_process_running_wmic(test[1]))

    def test_setup_environment(self):
        """Unit test for setup_environment"""
        setup_environment()
        envs = ['commonappdata', 'documents',
                'localappdata', 'music', 'pictures', 'video']
        version = platform.uname()[3][0:3]
        if version >= '6.0':
            envs.append('localappdatalow')
        for env in envs:
            self.assert_(os.path.exists(os.environ[env]))

    def test_split_registry_key(self):
        """Unit test for split_registry_key"""
        tests = (('HKCU\\Software', _winreg.HKEY_CURRENT_USER, 'Software'),
                 ('HKLM\\SOFTWARE', _winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE'),
                 ('HKU\\.DEFAULT', _winreg.HKEY_USERS, '.DEFAULT'))
        for (input_key, expected_hive, expected_key) in tests:
            (hive, key) = split_registry_key(input_key)
            self.assertEqual(expected_hive, hive)
            self.assertEqual(expected_key, key)

    def test_start_with_computer(self):
            """Unit test for start_with_computer*"""
            b = start_with_computer_check()
            self.assert_(isinstance(b, bool))
            # opposite setting
            start_with_computer(not b)
            two_b = start_with_computer_check()
            self.assert_(isinstance(two_b, bool))
            self.assertEqual(b, not two_b)
            # original setting
            start_with_computer(b)
            three_b = start_with_computer_check()
            self.assert_(isinstance(b, bool))
            self.assertEqual(b, three_b)

    def test_path_on_network(self):
        """Unit test for path_on_network"""
        self.assertFalse(path_on_network('c:\\bleachbit.exe'))
        self.assertFalse(path_on_network('a:\\bleachbit.exe'))
        self.assertTrue(path_on_network('\\\\Server\\Folder\\bleachbit.exe'))


def suite():
    return unittest.makeSuite(WindowsTestCase)


if __name__ == '__main__' and sys.platform == 'win32':
    unittest.main()
