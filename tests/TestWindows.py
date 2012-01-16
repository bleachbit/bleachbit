# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2011 Andrew Ziem
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
Test case for module Windows
"""



import sys
import tempfile
import unittest

import common

if 'win32' == sys.platform:
    import _winreg
    from win32com.shell import shell

sys.path.append('.')
from bleachbit.Windows import *



class WindowsTestCase(unittest.TestCase):
    """Test case for module Windows"""


    def test_delete_locked_file(self):
        """Unit test for delete_locked_file"""
        (fd, pathname) = tempfile.mkstemp('bbregular')
        os.close(fd)
        self.assert_(os.path.exists(pathname))
        try:
            delete_locked_file(pathname)
        except pywintypes.error, e:
            if 5 == e.winerror and not shell.IsUserAnAdmin():
                pass
            else:
                raise


    def test_delete_registry_key(self):
        """Unit test for delete_registry_key"""
        # (return value, key, really_delete)
        tests = ( (False, 'HKCU\\Software\\BleachBit\\DoesNotExist', False, ) ,
            (False, 'HKCU\\Software\\BleachBit\\DoesNotExist', True, ) ,
            (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', False, ) ,
            (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', True, ) , )


        # create a nested key
        key = 'Software\\BleachBit\\DeleteThisKey'
        subkey = key + '\\AndThisKey'
        hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, subkey )
        hkey.Close()

        # test
        for test in tests:
            return_value = delete_registry_key(test[1], test[2])
            self.assertEqual(test[0], return_value)

        # Test Unicode key.  In BleachBit 0.7.3 this scenario would lead to
        # the error (bug 537109)
        # UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 11: ordinal not in range(128)
        key = r'Software\\BleachBit\\DeleteThisKey'
        hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, key + r'\\AndThisKey-Ö')
        hkey.Close()
        return_value = delete_registry_key(u'HKCU\\' + key, True)
        self.assertEqual(return_value, True)
        return_value = delete_registry_key(u'HKCU\\' + key, True)
        self.assertEqual(return_value, False)


    def test_delete_registry_value(self):
        """Unit test for delete_registry_value"""

        ##
        ## test: value does exist
        ##

        # create a name-value pair
        key = 'Software\\BleachBit'
        hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, key )

        value_name = 'delete_this_value_name'
        _winreg.SetValueEx( hkey, value_name , 0, _winreg.REG_SZ, 'delete this value')
        hkey.Close()

        # delete and confirm
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, False), True)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, True), True)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, False), False)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, True), False)


        ##
        ## test: value does not exist
        ##
        self.assertEqual(delete_registry_value('HKCU\\' + key, 'doesnotexist', False), False)
        self.assertEqual(delete_registry_value('HKCU\\' + key, 'doesnotexist', True), False)
        self.assertEqual(delete_registry_value('HKCU\\doesnotexist', value_name, False), False)
        self.assertEqual(delete_registry_value('HKCU\\doesnotexist', value_name, True), False)


    def test_detect_registry_key(self):
        """Test for detect_registry_key()"""
        self.assert_(detect_registry_key('HKCU\\Software\\Microsoft\\'))
        self.assert_(not detect_registry_key('HKCU\\Software\\DoesNotExist'))


    def test_get_autostart_path(self):
        """Unit test for get_autostart_path"""
        pathname = get_autostart_path()
        dirname = os.path.dirname(pathname)
        self.assert_(os.path.exists(dirname), 'startup directory does not exist: %s' % dirname)


    def test_get_fixed_drives(self):
        """Unit test for get_fixed_drives"""
        drives = []
        for drive in get_fixed_drives():
            drives.append(drive)
            self.assertEqual(drive, drive.upper())
        self.assert_("C:\\" in drives)


    def test_is_process_running(self):
        tests = ((True, 'explorer.exe'), \
            (True, 'ExPlOrEr.exe'), \
            (False, 'doesnotexist.exe'))
        for test in tests:
            self.assertEqual(test[0], is_process_running(test[1]), 'is_process_running(%s) != %s' % (test[1], test[0]))
            self.assertEqual(test[0], is_process_running_win32(test[1]))
            self.assertEqual(test[0], is_process_running_wmic(test[1]))


    def test_empty_recycle_bin(self):
        """Unit test for empty_recycle_bin"""
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete = False)
            self.assert_ (isinstance(ret, (int, long)))
        if not common.destructive_tests('recycle bin'):
            return
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete = True)
            self.assert_ (isinstance(ret, (int, long)))
            # repeat because emptying empty recycle bin can cause
            # 'catastrophic failure' error



    def test_split_registry_key(self):
        """Unit test for split_registry_key"""
        tests = ( ('HKCU\\Software', _winreg.HKEY_CURRENT_USER, 'Software'),
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
        self.assertEqual(path_on_network('c:\\bleachbit.exe'), False)
        self.assertEqual(path_on_network('a:\\bleachbit.exe'), False)
        self.assertEqual(path_on_network('\\\\Server\\Folder\\bleachbit.exe'), True)


def suite():
    return unittest.makeSuite(WindowsTestCase)


if __name__ == '__main__' and sys.platform == 'win32':
    unittest.main()

