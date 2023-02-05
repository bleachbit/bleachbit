# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Test case for module Windows
"""

from tests import common

from bleachbit.FileUtilities import extended_path, extended_path_undo
from bleachbit.Windows import *
from bleachbit import logger

import os
import platform
import shutil
import sys
import tempfile
import unittest
import mock
from decimal import Decimal

if 'win32' == sys.platform:
    import winreg
    from win32com.shell import shell


def put_files_into_recycle_bin():
    """Put a file and a folder into the recycle bin"""
    # make a file and move it to the recycle bin
    tests = ('regular', 'unicode-emdash-u\u2014', 'long' + 'x' * 100)
    for test in tests:
        (fd, filename) = tempfile.mkstemp(
            prefix='bleachbit-recycle-file', suffix=test)
        os.close(fd)
        move_to_recycle_bin(filename)
    # make a folder and move it to the recycle bin
    dirname = tempfile.mkdtemp(prefix='bleachbit-recycle-folder')
    common.touch_file(os.path.join(dirname, 'file'))
    move_to_recycle_bin(dirname)


@common.skipUnlessWindows
class WindowsTestCase(common.BleachbitTestCase):

    """Test case for module Windows"""

    def skipUnlessAdmin(self):
        if not shell.IsUserAnAdmin():
            self.skipTest('requires administrator privileges')

    def test_get_recycle_bin(self):
        """Unit test for get_recycle_bin"""
        for f in get_recycle_bin():
            self.assertExists(extended_path(f))

    @common.skipUnlessDestructive
    def test_get_recycle_bin_destructive(self):
        """Unit test the destructive part of get_recycle_bin"""
        put_files_into_recycle_bin()
        # clear recycle bin
        counter = 0
        for f in get_recycle_bin():
            counter += 1
            FileUtilities.delete(f)
        self.assertGreaterEqual(counter, 3, 'deleted %d' % counter)
        # now it should be empty
        for _f in get_recycle_bin():
            self.fail('recycle bin should be empty, but it is not')

    def _test_link_helper(self, mklink_option, clear_recycle_bin):
        """Helper function for testing for links with is_junction() and
        get_recycle_bin()

        It gets called four times for the combinations of the two
        parameters. It's called by four unit tests for accounting
        purposes. In other words, we don't want to count a test as
        skipped if part of it succeeded.

        mklink /j = directory junction
        directory junction does not require administrator privileges

        mklink /d=directory symbolic link
        requires administrator privileges
        """
        if mklink_option == '/d':
            self.skipUnlessAdmin()
        # make a normal directory with a file in it
        target_dir = os.path.join(self.tempdir, 'target_dir')
        os.mkdir(target_dir)
        self.assertExists(target_dir)
        self.assertFalse(is_junction(target_dir))

        from random import randint
        canary_fn = os.path.join(
            target_dir, 'do_not_delete%d' % randint(1000, 9999))
        common.touch_file(canary_fn)
        self.assertExists(canary_fn)
        self.assertFalse(is_junction(canary_fn))

        # make a normal directory to hold a link
        container_dir = os.path.join(self.tempdir, 'container_dir')
        os.mkdir(container_dir)
        self.assertExists(container_dir)
        self.assertFalse(is_junction(container_dir))

        # create the link
        link_pathname = os.path.join(container_dir, 'link')
        args = ('cmd', '/c', 'mklink', mklink_option,
                link_pathname, target_dir)
        from bleachbit.General import run_external
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(rc, 0, stderr)
        self.assertExists(link_pathname)
        self.assertTrue(is_junction(link_pathname))

        # put the link in the recycle bin
        move_to_recycle_bin(container_dir)

        def cleanup_dirs():
            shutil.rmtree(container_dir, True)
            self.assertNotExists(container_dir)
            shutil.rmtree(target_dir, True)

        if not clear_recycle_bin:
            cleanup_dirs()
            return

        # clear the recycle bin
        for f in get_recycle_bin():
            FileUtilities.delete(f, shred=False)

        # verify the canary is still there
        self.assertExists(canary_fn)

        # clean up
        cleanup_dirs()

    def test_link_junction_no_clear(self):
        """Unit test for directory junctions without clearing recycle bin"""
        self._test_link_helper('/j', False)

    def test_link_junction_clear(self):
        """Unit test for directory junctions with clearing recycle bin"""
        self._test_link_helper('/j', True)

    def test_link_symlink_no_clear(self):
        """Unit test for directory symlink without clearing recycle bin"""
        self._test_link_helper('/d', False)

    def test_link_symlink_clear(self):
        """Unit test for directory symlink with clearing recycle bin"""
        self._test_link_helper('/d', True)

    def test_delete_locked_file(self):
        """Unit test for delete_locked_file"""
        tests = ('regular', 'unicode-emdash-u\u2014', 'long' + 'x' * 100)
        for test in tests:
            f = tempfile.NamedTemporaryFile(
                prefix='bleachbit-delete-locked-file', suffix=test,
                delete=False)
            pathname = f.name
            f.close()
            import time
            time.sleep(5)  # avoid race condition
            self.assertExists(pathname)
            logger.debug('delete_locked_file(%s) ' % pathname)
            if not shell.IsUserAnAdmin():
                with self.assertRaises(WindowsError):
                    delete_locked_file(pathname)
            else:
                try:
                    delete_locked_file(pathname)
                except WindowsError:
                    logger.exception(
                        'delete_locked_file() threw an error, which may be a false positive')
            self.assertExists(pathname)
        logger.info('reboot Windows and check the three files are deleted')

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
        hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)
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
        hkey = winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, key + r'\\AndThisKey-Ö')
        hkey.Close()
        return_value = delete_registry_key('HKCU\\' + key, True)
        self.assertTrue(return_value)
        return_value = delete_registry_key('HKCU\\' + key, True)
        self.assertFalse(return_value)

    def test_delete_registry_value(self):
        """Unit test for delete_registry_value"""

        #
        # test: value does exist
        #

        # create a name-value pair
        key = 'Software\\BleachBit'
        hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key)

        value_name = 'delete_this_value_name'
        winreg.SetValueEx(
            hkey, value_name, 0, winreg.REG_SZ, 'delete this value')
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
        self.assertTrue(detect_registry_key('HKCU\\Software\\Microsoft\\'))
        self.assertTrue(not detect_registry_key(
            'HKCU\\Software\\DoesNotExist'))

    def test_get_clipboard_paths(self):
        """Unit test for get_clipboard_paths"""
        # The clipboard is an unknown state, so check the function does
        # not crash and that it returns the right data type.
        paths = get_clipboard_paths()
        self.assertIsInstance(paths, (type(None), tuple))

        # Set the clipboard to an unsupported type (text), so expect no
        # files are returned
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        fname = r'c:\windows\notepad.exe'
        win32clipboard.SetClipboardText(fname, win32clipboard.CF_TEXT)
        win32clipboard.SetClipboardText(fname, win32clipboard.CF_UNICODETEXT)
        self.assertEqual(win32clipboard.GetClipboardData(
            win32clipboard.CF_TEXT), fname.encode('ascii'))
        self.assertEqual(win32clipboard.GetClipboardData(
            win32clipboard.CF_UNICODETEXT), fname)
        win32clipboard.CloseClipboard()

        paths = get_clipboard_paths()
        self.assertIsInstance(paths, (type(None), tuple))
        self.assertEqual(paths, ())

        # Put files in the clipboard in supported format
        args = ('powershell.exe', 'Set-Clipboard',
                '-Path', r'c:\windows\*.exe')
        (ext_rc, _stdout, _stderr) = General.run_external(args)
        self.assertEqual(ext_rc, 0)
        paths = get_clipboard_paths()
        self.assertIsInstance(paths, (type(None), tuple))
        self.assertGreater(len(paths), 1)
        for path in paths:
            self.assertExists(path)

    def test_get_font_conf_file(self):
        """Unit test for get_font_conf_file"""
        # This tests only one of three situations.
        font_fn = get_font_conf_file()
        self.assertExists(font_fn)

    def test_get_known_folder_path(self):
        """Unit test for get_known_folder_path"""
        ret = get_known_folder_path('LocalAppDataLow')
        self.assertNotEqual(ret, '')
        self.assertNotEqual(ret, None)
        self.assertExists(ret)

    def test_get_fixed_drives(self):
        """Unit test for get_fixed_drives"""
        drives = []
        for drive in get_fixed_drives():
            drives.append(drive)
            self.assertEqual(drive, drive.upper())
        self.assertIn("C:\\", drives)

    def test_get_windows_version(self):
        """Unit test for get_windows_version"""
        v = get_windows_version()
        self.assertGreaterEqual(v, 5.1)
        self.assertGreater(v, 5)
        self.assertIsInstance(v, Decimal)

    def test_empty_recycle_bin(self):
        """Unit test for empty_recycle_bin"""
        # check the function basically works
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=False)
            self.assertIsInteger(ret)

    @common.skipUnlessDestructive
    def test_empty_recycle_bin_destructive(self):
        """Unit test the destructive part of empty_recycle_bin()"""
        # check it deletes files for fixed drives
        put_files_into_recycle_bin()
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=True)
            self.assertIsInteger(ret)
        # check it deletes files for all drives
        put_files_into_recycle_bin()
        ret = empty_recycle_bin(None, really_delete=True)
        self.assertIsInteger(ret)
        # Repeat two for reasons.
        # 1. Trying to empty an empty recycling bin can cause
        #    a 'catastrophic failure' error (handled in the function)
        # 2. It should show zero bytes were deleted
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete=True)
            self.assertEqual(ret, 0)

    def test_file_wipe(self):
        """Unit test for file_wipe

        There are more tests in testwipe.py
        """

        from bleachbit.WindowsWipe import file_wipe, open_file, close_file, file_make_sparse
        from bleachbit.Windows import elevate_privileges
        from win32con import GENERIC_WRITE, WRITE_DAC

        dirname = tempfile.mkdtemp(prefix='bleachbit-file-wipe')

        filenames = ('short', 'long' + 'x' * 250, 'utf8-ɡælɪk')
        for filename in filenames:
            longname = os.path.join(dirname, filename)
            logger.debug('file_wipe(%s)', longname)

            def _write_file(longname, contents):
                self.write_file(longname, contents)
                import win32api
                shortname = extended_path_undo(
                    win32api.GetShortPathName(extended_path(longname)))
                self.assertExists(shortname)
                return shortname

            def _deny_access(fh):
                import win32security
                import ntsecuritycon as con

                user, _, _ = win32security.LookupAccountName(
                    "", win32api.GetUserName())
                dacl = win32security.ACL()
                dacl.AddAccessDeniedAce(
                    win32security.ACL_REVISION, con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE, user)
                win32security.SetSecurityInfo(fh, win32security.SE_FILE_OBJECT, win32security.DACL_SECURITY_INFORMATION,
                                              None, None, dacl, None)

            def _test_wipe(contents, deny_access=False, is_sparse=False):
                shortname = _write_file(longname, contents)
                if deny_access or is_sparse:
                    fh = open_file(extended_path(longname),
                                   mode=GENERIC_WRITE | WRITE_DAC)
                    if is_sparse:
                        file_make_sparse(fh)
                    if deny_access:
                        _deny_access(fh)
                    close_file(fh)
                logger.debug('test_file_wipe(): filename length={}, shortname length ={}, contents length={}, is_sparse={}'.format(
                    len(longname), len(shortname), len(contents), is_sparse))
                if shell.IsUserAnAdmin():
                    # wiping requires admin privileges
                    file_wipe(shortname)
                    file_wipe(longname)
                else:
                    with self.assertRaises(pywintypes.error):
                        file_wipe(shortname)
                        file_wipe(longname)
                self.assertExists(shortname)
                os.remove(extended_path(shortname))
                self.assertNotExists(shortname)

            # A small file that fits in MFT
            _test_wipe(b'')

            # requires wiping of extents
            _test_wipe(b'secret' * 100000)

            # requires wiping of extents: special file case
            elevate_privileges(False)
            _test_wipe(b'secret' * 100000, deny_access=True, is_sparse=True)

        shutil.rmtree(dirname, True)

        if shell.IsUserAnAdmin():
            logger.warning(
                'You should also run test_file_wipe() without admin privileges.')
        else:
            logger.warning(
                'You should also run test_file_wipe() with admin privileges.')

    def test_is_process_running(self):
        # winlogon.exe runs on Windows XP and Windows 7
        # explorer.exe does not run on Appveyor
        tests = ((True, 'winlogon.exe'),
                 (True, 'WinLogOn.exe'),
                 (False, 'doesnotexist.exe'))
        for test in tests:
            self.assertEqual(test[0],
                             is_process_running(test[1]),
                             'Expecting is_process_running(%s) = %s' %
                             (test[1], test[0]))

    def test_setup_environment(self):
        """Unit test for setup_environment"""
        setup_environment()
        envs = ['commonappdata', 'documents', 'music', 'pictures', 'video',
                'localappdata', 'localappdatalow']
        for env in envs:
            self.assertExists(os.environ[env])

    def test_split_registry_key(self):
        """Unit test for split_registry_key"""
        tests = (('HKCU\\Software', winreg.HKEY_CURRENT_USER, 'Software'),
                 ('HKLM\\SOFTWARE', winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE'),
                 ('HKU\\.DEFAULT', winreg.HKEY_USERS, '.DEFAULT'))
        for (input_key, expected_hive, expected_key) in tests:
            (hive, key) = split_registry_key(input_key)
            self.assertEqual(expected_hive, hive)
            self.assertEqual(expected_key, key)

    def test_parse_windows_build(self):
        """Unit test for parse_windows_build"""
        tests = (('5.1.2600', Decimal('5.1')),
                 ('5.1', Decimal('5.1')),
                 ('10.0.10240', 10),
                 ('10.0', 10))
        for test in tests:
            self.assertEqual(parse_windows_build(test[0]), test[1])

        # test for crash
        parse_windows_build()
        parse_windows_build(platform.version())
        parse_windows_build(platform.uname()[3])

    def test_path_on_network(self):
        """Unit test for path_on_network"""
        self.assertFalse(path_on_network('c:\\bleachbit.exe'))
        self.assertFalse(path_on_network('a:\\bleachbit.exe'))
        self.assertTrue(path_on_network('\\\\Server\\Folder\\bleachbit.exe'))

    def test_shell_change_notify(self):
        """Unit test for shell_change_notify"""
        ret = shell_change_notify()
        self.assertEqual(ret, 0)

    def test_set_environ(self):
        for folder in ['folderäö', 'folder']:
            test_dir = os.path.join(self.tempdir, folder)
            os.mkdir(test_dir)
            self.assertExists(test_dir)
            set_environ('cd_test', test_dir)
            self.assertEqual(os.environ['cd_test'], test_dir)
            os.environ.pop('cd_test')
