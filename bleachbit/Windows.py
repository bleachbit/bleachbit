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
Functionality specific to Microsoft Windows

The Windows Registry terminology can be confusing. Take for example 
the reference
* HKCU\\Software\\BleachBit
* CurrentVersion

These are the terms:
* 'HKCU' is an abbreviation for the hive HKEY_CURRENT_USER.
* 'HKCU\Software\BleachBit' is the key name.
* 'Software' is a sub-key of HCKU.
* 'BleachBit' is a sub-key of 'Software.'
* 'CurrentVersion' is the value name.
* '0.5.1' is the value data.


"""


import sys
if 'win32' == sys.platform:
    import _winreg


def delete_registry_value(key, value_name, really_delete):
    """Delete named value under the registry key.
    Return boolean indicating whether reference found and
    successful.  If really_delete is False (meaning preview),
    just check whether the value exists."""
    (hive, sub_key) = split_registry_key(key)
    if really_delete:
        try:
            hkey = _winreg.OpenKey(hive, sub_key, 0, _winreg.KEY_SET_VALUE)
            _winreg.DeleteValue(hkey, value_name)
        except WindowsError, e:
            if e.winerror == 2:
                # 2 = 'file not found' means value does not exist
                return False
            raise
        else:
            return True
    try:
        hkey = _winreg.OpenKey(hive, sub_key)
        _winreg.QueryValueEx(hkey, value_name)
    except WindowsError, e:
        if e.winerror == 2:
            return False
        raise
    else:
        return True
    raise RuntimeError ('Unknown error in delete_registry_value')


def delete_registry_key(parent_key, really_delete):
    """Delete registry key including any values and sub-keys.
    Return boolean whether found and success.  If really
    delete is False (meaning preview), just check whether
    the key exists."""
    (hive, parent_sub_key) = split_registry_key(parent_key)
    hkey = None
    try:
        hkey = _winreg.OpenKey(hive, parent_sub_key)
    except WindowsError, e:
        if e.winerror == 2:
            # 2 = 'file not found' happens when key does not exist
            return False
    if not really_delete:
        return True
    keys_size = _winreg.QueryInfoKey(hkey)[0]
    child_keys = []
    for i in range(keys_size):
        child_keys.append(parent_key + '\\' + _winreg.EnumKey(hkey, i))
    for child_key in child_keys:
        delete_registry_key(child_key, True)
    _winreg.DeleteKey(hive, parent_sub_key)
    return True


def split_registry_key(full_key):
    """Given a key like HKLM\Software split into tuple (hive, key).
    Used internally."""
    assert ( len (full_key) > 6 )
    hive_str = full_key[0:4]
    hive_map = { 'HKCU' : _winreg.HKEY_CURRENT_USER,
        'HKLM' : _winreg.HKEY_LOCAL_MACHINE }
    if hive_str not in hive_map:
        raise RuntimeError("Invalid Windows registry hive '%s'" % hive_str)
    return ( hive_map[hive_str], full_key[5:] )



import unittest

class TestWindows(unittest.TestCase):
    """Unit tests for module Windows"""


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



    def test_split_registry_key(self):
        """Unit test for split_registry_key"""
        tests = ( ('HKCU\\Software', _winreg.HKEY_CURRENT_USER, 'Software'),
            ('HKLM\\SOFTWARE', _winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE') )
        for (input_key, expected_hive, expected_key) in tests:
            (hive, key) = split_registry_key(input_key)
            self.assertEqual(expected_hive, hive)
            self.assertEqual(expected_key, key)


if __name__ == '__main__' and sys.platform == 'win32':
    unittest.main()

