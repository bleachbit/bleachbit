# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module Windows
"""


from tests import common

from bleachbit import FileUtilities, General
from bleachbit.Command import Delete, Function
from bleachbit.FileUtilities import extended_path, extended_path_undo
from bleachbit.Windows import (
    delete_locked_file,
    delete_registry_key,
    delete_registry_value,
    delete_updates,
    is_service_running,
    run_net_service_command,
    detect_registry_key,
    empty_recycle_bin,
    get_clipboard_paths,
    get_fixed_drives,
    get_font_conf_file,
    get_known_folder_path,
    get_recycle_bin,
    get_windows_version,
    is_junction,
    is_process_running,
    move_to_recycle_bin,
    parse_windows_build,
    path_on_network,
    set_environ,
    setup_environment,
    shell_change_notify,
    split_registry_key,
    read_registry_key,
    get_sid_token_48,
    is_ots_elevation,
    SplashThread,
)
from bleachbit import logger

import ctypes
import os
import itertools
import platform
import shutil
import subprocess
import sys
import time
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest import mock
from random import randint


if 'win32' == sys.platform:
    import pywintypes
    import win32api
    import win32service
    import winreg
    from win32com.shell import shell

    from bleachbit import Windows


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


class WindowsLinksMixIn():
    """Mixin class for Windows link creation methods."""

    def _create_win_dir_symlink(self, target, linkname):
        """Create a directory symlink"""

        self.assertFalse(os.path.lexists(linkname),
                         f'Link must not exist: {linkname}')
        self.assertTrue(os.path.isabs(target),
                        f'Target must be absolute path: {target}')
        self.assertTrue(os.path.isabs(linkname),
                        f'Link must be absolute path: {linkname}')
        self.assertExists(target)
        target_path = Path(target)
        self.assertTrue(target_path.is_dir(),
                        f'Target must be an existing directory: {target}')

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateSymbolicLinkW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
        ]
        kernel32.CreateSymbolicLinkW.restype = ctypes.c_ubyte
        result = kernel32.CreateSymbolicLinkW(
            linkname, target, 1)  # SYMBOLIC_LINK_FLAG_DIRECTORY
        if result == 0:
            err = ctypes.GetLastError()
            raise OSError(err, ctypes.FormatError(err))
        self.assertExists(linkname)
        link_path = Path(linkname)
        self.assertTrue(link_path.is_symlink())
        self.assertTrue(link_path.is_dir())
        self.assertFalse(Windows.is_junction(linkname))
        self.assertFalse(FileUtilities.is_normal_directory(linkname))

    def _create_win_hard_link(self, target, linkname):
        """Create a hard link to a file"""

        self.assertFalse(os.path.lexists(linkname),
                         f'Link must not exist: {linkname}')
        self.assertTrue(os.path.isabs(target),
                        f'Target must be absolute path: {target}')
        self.assertTrue(os.path.isabs(linkname),
                        f'Link must be absolute path: {linkname}')
        self.assertExists(target)
        target_path = Path(target)
        self.assertTrue(target_path.is_file(),
                        f'Target must be an existing file: {target}')
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateHardLinkW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_void_p,
        ]
        kernel32.CreateHardLinkW.restype = ctypes.c_bool
        result = kernel32.CreateHardLinkW(linkname, target, None)
        if not result:
            err = ctypes.GetLastError()
            raise OSError(err, ctypes.FormatError(err))
        self.assertExists(linkname)
        link_path = Path(linkname)
        self.assertTrue(link_path.is_file())
        self.assertFalse(link_path.is_symlink())
        self.assertFalse(Windows.is_junction(linkname))
        self.assertTrue(os.path.samefile(target, linkname))
        self.assertFalse(FileUtilities.is_normal_directory(linkname))

    def _create_win_junction(self, target, linkname):
        """Create a directory junction using mklink /J."""

        if os.path.lexists(linkname):
            raise OSError(f'Link already exists: {linkname}')
        self.assertTrue(os.path.isabs(target),
                        f'Target must be absolute path: {target}')
        self.assertTrue(os.path.isabs(linkname),
                        f'Link must be absolute path: {linkname}')
        self.assertExists(target)
        target_path = Path(target)
        self.assertTrue(target_path.is_dir(),
                        f'Target must be an existing directory: {target}')
        cmd = ['cmd', '/c', 'mklink', '/J',
               extended_path(linkname), extended_path(target)]
        subprocess.check_call(cmd)
        self.assertExists(linkname)
        self.assertTrue(Windows.is_junction(linkname))
        path = Path(linkname)
        self.assertTrue(path.is_dir())
        self.assertFalse(path.is_symlink())


@common.skipUnlessWindows
class WindowsTestCase(common.BleachbitTestCase, WindowsLinksMixIn):

    """Test case for module Windows"""

    def skipUnlessAdmin(self):
        if not shell.IsUserAnAdmin():
            self.skipTest('requires administrator privileges')

    def test_get_recycle_bin(self):
        """Unit test for get_recycle_bin"""
        for f in get_recycle_bin():
            self.assertLExists(extended_path(f))

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

    def _test_link_helper(self, mklink_option, recycle_container, clear_recycle_bin):
        """Helper function for testing directory junctions and symlinks in the recycle bin.

        Tests that get_recycle_bin() correctly handles Windows directory links
        when they are placed in the recycle bin, and verifies that the original
        target directory and its contents are preserved after clearing the bin.

        Args:
            mklink_option: Link type to create. '/j' for directory junction,
                '/d' for directory symbolic link.
            recycle_container: If True, move the container directory to the
                recycle bin. If False, move only the link itself.
            clear_recycle_bin: If True, clear the recycle bin after moving
                the link. If False, manually delete items from get_recycle_bin().

        Note:
            Directory symbolic links (/d) require administrator privileges.
        """
        assert mklink_option in ('/j', '/d')
        if mklink_option == '/d':
            self.skipUnlessAdmin()
        # make a normal directory with a file in it
        target_dir = self.mkdir('target_dir')

        canary_base = f'do_not_delete{randint(10000, 9999999)}'
        canary_fn = os.path.join(target_dir, canary_base)
        common.touch_file(canary_fn)
        self.assertFalse(is_junction(canary_fn))

        # make a normal directory to hold a link
        container_dir = self.mkdir('container_dir')

        # create the link
        link_pathname = os.path.join(container_dir, 'link')
        if mklink_option == '/j':
            self._create_win_junction(target_dir, link_pathname)
        else:
            self._create_win_dir_symlink(target_dir, link_pathname)

        # put the link in the recycle bin
        move_to_recycle_bin(
            container_dir if recycle_container else link_pathname)

        def cleanup_dirs():
            shutil.rmtree(container_dir, True)
            self.assertNotExists(container_dir)
            shutil.rmtree(target_dir, True)

        if not clear_recycle_bin:
            cleanup_dirs()
            return

        # clear the recycle bin
        for f in get_recycle_bin():
            if canary_base in f:
                logger.error('get_recycle_bin() returned canary: %s', f)
            FileUtilities.delete(f, shred=False)

        # verify the canary is still there
        self.assertExists(canary_fn)

        # clean up
        cleanup_dirs()

    def test_link_types(self):
        """Unit test for directory junctions and symlinks with recycle bin"""
        for mklink_option, recycle_container, clear_recycle_bin in itertools.product(
            ('/j', '/d'), (False, True), (False, True)
        ):
            with self.subTest(mklink_option=mklink_option,
                              recycle_container=recycle_container,
                              clear_recycle_bin=clear_recycle_bin):
                self._test_link_helper(
                    mklink_option, recycle_container, clear_recycle_bin)

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

    def test_delete_updates(self):
        """Unit test for delete_updates

        As a preview, this does not modify services or delete files.
        """
        if not shell.IsUserAnAdmin():
            # It should return None without doing any work.
            for _ in delete_updates():
                pass
            return

        counter = 0
        for cmd in delete_updates():
            counter += 1
            self.assertIsInstance(cmd, (Delete, Function))
        logger.debug('delete_updates() returned %s commands', f'{counter:,}')

    def test_is_service_running(self):
        """Unit test for is_service_running()"""
        # RPC is always running.
        self.assertTrue(is_service_running('rpcss'))
        # Windows Update is sometimes running.
        self.assertIsInstance(is_service_running('wuauserv'), bool)
        # Non-existent service should raise an error.
        with self.assertRaises(pywintypes.error):
            is_service_running('does_not_exist')
        # None should raise an error.
        with self.assertRaises(AssertionError):
            is_service_running(None)

    def test_is_ots_elevation_without_flag_returns_false(self):
        """Without --uac-sid-token, is_ots_elevation() returns False"""
        argv = ['bleachbit.exe', '--gui']
        with mock.patch('bleachbit.Windows.sys.argv', argv):
            self.assertFalse(is_ots_elevation())

    def test_is_ots_elevation_false_when_tokens_match(self):
        """If current token matches parent token, there is no elevation"""
        parent_token = 'ABCDEFGH'
        argv = ['bleachbit.exe', '--gui', '--uac-sid-token', parent_token]
        with mock.patch('bleachbit.Windows.sys.argv', argv):
            with mock.patch('bleachbit.Windows.get_sid_token_48', return_value=parent_token):
                self.assertFalse(is_ots_elevation())

    def test_is_ots_elevation_true_when_tokens_differ(self):
        """If current token differs from parent token, elevation is detected"""
        parent_token = 'ABCDEFGH'
        argv = ['bleachbit.exe', '--gui', '--uac-sid-token', parent_token]
        with mock.patch('bleachbit.Windows.sys.argv', argv):
            with mock.patch('bleachbit.Windows.get_sid_token_48', return_value='DIFFERNT'):
                self.assertTrue(is_ots_elevation())

    def test_is_ots_elevation_ignores_flag_without_value(self):
        """A trailing --uac-sid-token without value should not crash and returns False"""
        argv = ['bleachbit.exe', '--gui', '--uac-sid-token']
        with mock.patch('bleachbit.Windows.sys.argv', argv):
            self.assertFalse(is_ots_elevation())

    def test_is_ots_elevation_returns_false_on_get_sid_error(self):
        """If get_sid_token_48() raises, is_ots_elevation() falls back to False"""
        parent_token = 'ABCDEFGH'
        argv = ['bleachbit.exe', '--gui', '--uac-sid-token', parent_token]
        with mock.patch('bleachbit.Windows.sys.argv', argv):
            with mock.patch('bleachbit.Windows.get_sid_token_48', side_effect=RuntimeError('error')):
                self.assertFalse(is_ots_elevation())

    def test_splash_thread_reuses_cached_class_atom(self):
        """_register_window_class skips RegisterClass when cached."""
        splash = SplashThread()
        self.addCleanup(lambda: setattr(SplashThread, '_class_atom', None))
        SplashThread._class_atom = 9876
        with mock.patch('bleachbit.Windows.win32gui.RegisterClass') as mock_register:
            atom = splash._register_window_class(mock.Mock())
        self.assertEqual(atom, 9876)
        mock_register.assert_not_called()

    def test_splash_thread_recovers_when_class_exists(self):
        """_register_window_class handles ERROR_CLASS_ALREADY_EXISTS."""
        splash = SplashThread()
        self.addCleanup(lambda: setattr(SplashThread, '_class_atom', None))
        SplashThread._class_atom = None
        wnd_class = mock.Mock()
        wnd_class.hInstance = mock.sentinel.instance
        wnd_class.lpszClassName = 'SimpleWin32'
        register_error = pywintypes.error(1410, 'RegisterClass', 'Class already exists.')
        with mock.patch('bleachbit.Windows.win32gui.RegisterClass', side_effect=register_error) as mock_register, \
                mock.patch('bleachbit.Windows.win32gui.GetClassInfo', return_value=(4321,)) as mock_get_class_info:
            atom = splash._register_window_class(wnd_class)
        self.assertEqual(atom, 4321)
        self.assertEqual(SplashThread._class_atom, 4321)
        mock_register.assert_called_once_with(wnd_class)
        mock_get_class_info.assert_called_once_with(wnd_class.hInstance, wnd_class.lpszClassName)

    def test_splash_thread_propagates_startup_error(self):
        """start() raises if splash initialization fails."""
        splash = SplashThread()
        with mock.patch.object(splash, '_show_splash_screen', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                splash.start()
        self.assertIsNotNone(splash._startup_error)

    def test_splash_thread_join_handles_missing_window(self):
        """join() succeeds even when window handle was never created."""
        splash = SplashThread()
        splash._startup_error = RuntimeError('boom')
        splash._splash_screen_started.set()
        splash.start = lambda: None  # prevent thread start
        # Directly call join; should not raise even though handle is None
        splash.join(timeout=0)

    @common.skipUnlessDestructive
    def test_run_net_service_command(self):
        """Integration test for run_net_service_command().

        Actually stop/start Windows Update service.

        spooler (Print Spooler) is often on by default and has no dependencies.

        Windows Audio Endpoint Builder (AudioEndpointBuilder) is often on
        by default and depends on audiosrv (Windows Audio).

        Requires admin.
        """
        if not shell.IsUserAnAdmin():
            self.skipTest('requires administrator privileges')
        def _service_exists_and_enabled(svc):
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            try:
                hs = win32service.OpenService(scm, svc, win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_QUERY_CONFIG)
                try:
                    cfg = win32service.QueryServiceConfig(hs)
                    return True if cfg[1] != win32service.SERVICE_DISABLED else False
                finally:
                    win32service.CloseServiceHandle(hs)
            except pywintypes.error:
                return False
            finally:
                win32service.CloseServiceHandle(scm)

        def _can_open_all_access(svc):
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            try:
                try:
                    hs = win32service.OpenService(scm, svc, win32service.SERVICE_ALL_ACCESS)
                except pywintypes.error:
                    return False
                else:
                    win32service.CloseServiceHandle(hs)
                    return True
            finally:
                win32service.CloseServiceHandle(scm)

        is_ci = os.environ.get('APPVEYOR') == 'True'
        if is_ci:
            candidates = ('bits', 'wuauserv', 'AudioEndpointBuilder', 'spooler')
            service = None
            # Prefer already-running to avoid state changes
            for s in candidates:
                if _service_exists_and_enabled(s) and _can_open_all_access(s) and is_service_running(s):
                    service = s
                    break
            # If none are running, pick any we can open with required access
            if not service:
                for s in candidates:
                    if _service_exists_and_enabled(s) and _can_open_all_access(s):
                        service = s
                        break
        else:
            candidates = ('AudioEndpointBuilder', 'spooler', 'bits', 'wuauserv')
            service = None
            for s in candidates:
                if _service_exists_and_enabled(s):
                    service = s
                    break
        if not service:
            self.skipTest('no suitable startable service on this machine')

        initial_running = is_service_running(service)

        try:
            if is_ci:
                ret = run_net_service_command(service, True)
                self.assertEqual(ret, 0)
                ret = run_net_service_command(service, True)
                self.assertEqual(ret, 0)
            else:
                ret = run_net_service_command(service, False)
                self.assertEqual(ret, 0)
                self.assertFalse(is_service_running(service))
                if service == 'AudioEndpointBuilder':
                    self.assertFalse(is_service_running('audiosrv'))
                ret = run_net_service_command(service, False)
                self.assertEqual(ret, 0)
                self.assertFalse(is_service_running(service))
                ret = run_net_service_command(service, True)
                self.assertEqual(ret, 0)
                self.assertTrue(is_service_running(service))
                ret = run_net_service_command(service, True)
                self.assertEqual(ret, 0)
                self.assertTrue(is_service_running(service))
        finally:
            if not is_ci:
                run_net_service_command(service, initial_running)
                self.assertEqual(initial_running, is_service_running(service))

    def test_run_net_service_command_not_admin(self):
        """Test as run_net_service_command() as not admin user"""
        if shell.IsUserAnAdmin():
            self.skipTest('requires non-admin user')
        service = 'wuauserv'
        initial_running = is_service_running(service)
        for start in (True, False):
            with self.assertRaises(RuntimeError):
                run_net_service_command(service, start)
            self.assertEqual(is_service_running(service), initial_running)

    def test_run_net_service_command_invalid_service(self):
        """Test as run_net_service_command() with invalid service"""
        for service in ('does_not_exist', None):
            for start in (True, False):
                with self.subTest(service=service, start=start):
                    with self.assertRaises((AssertionError, RuntimeError)):
                        run_net_service_command(service, start)

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

    def test_get_sid_token_48_basic_properties(self):
        """get_sid_token_48() returns an 8-char, URL-safe ASCII string"""
        token = get_sid_token_48()
        self.assertIsString(token)
        # 6 bytes (48 bits) become 8 base64-url characters without padding
        self.assertEqual(len(token), 8)
        for ch in token:
            self.assertLess(ord(ch), 128)
        # urlsafe_b64encode must not use '+', '/', or '='
        self.assertNotIn('+', token)
        self.assertNotIn('/', token)
        self.assertNotIn('=', token)

    def test_get_sid_token_48_is_deterministic_for_current_process(self):
        """Multiple calls for the same process should yield the same token"""
        t1 = get_sid_token_48()
        t2 = get_sid_token_48()
        self.assertEqual(t1, t2)

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
        # explorer.exe did not run Appveyor, but it does as of 2025-01-25.
        # svchost.exe runs both as system and current user on Windows 11
        # svchost.exe does not run as same user on AppVeyor and Windows Server 2012.
        tests = ((True, 'winlogon.exe', False),
                 (True, 'WinLogOn.exe', False),
                 (False, 'doesnotexist.exe', False),
                 (True, 'explorer.exe', True),
                 (True, 'svchost.exe', False),
                 (True, 'services.exe', False),
                 (False, 'services.exe', True),
                 (True, 'wininit.exe', False),
                 (False, 'wininit.exe', True))

        for expected, exename, require_same_user in tests:
            with self.subTest(exename=exename, require_same_user=require_same_user):
                result = is_process_running(exename, require_same_user)
                self.assertEqual(
                    expected, result, f'Expecting is_process_running({exename}, {require_same_user}) = {expected}, got {result}')

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

    def test_read_registry_key(self):
        """Unit test for read_registry_key"""
        tests = (('HKCR\\.bmp', 'PerceivedType', 'image'),
                 ('HKCU\\Software\\BleachBit\\DoesNotExist', 'DoesNotExist', None))
        for (input_key, input_value, expected_value) in tests:
            value = read_registry_key(input_key, input_value)
            if value != None:
                value = value.lower() # AppVeyor: image, Windows 11: Image
            self.assertEqual(expected_value, value)

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

    def test_splash_screen(self):
        """Unit test for splash screen"""
        splash_thread = SplashThread()
        icon_path = splash_thread.get_icon_path()
        self.assertTrue(icon_path.is_absolute())
        self.assertExists(icon_path)
        splash_thread.start()
        timeout = 5.0  # seconds
        start_time = time.time()
        time.sleep(1)
        while not splash_thread.is_alive() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        self.assertTrue(splash_thread.is_alive(),
                        'Splash thread did not start within timeout')
        splash_thread.join()

        # Originally, running twice in same process caused indefinite hang,
        # so run it twice.
        repeat = SplashThread()
        repeat.start()
        repeat.join()

    def test_splash_screen_window_pos(self):
        """Unit test for calculate_window_position()"""
        splash_thread = SplashThread()

        # Test with a typical 1080p display
        display_width = 1920
        display_height = 1080
        x, y, width, height = splash_thread.calculate_window_position(
            display_width, display_height)

        # The window should have positive dimensions
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

        # The window position should be positive (on screen)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

        # The window should fit within the display
        self.assertLessEqual(x + width, display_width)
        self.assertLessEqual(y + height, display_height)

        # The window should be roughly centered
        # x should be approximately (display_width - width) / 2
        expected_x = (display_width - width) // 2
        self.assertEqual(x, expected_x)
        # y should be approximately (display_height - height) / 2
        expected_y = (display_height - height) // 2
        self.assertEqual(y, expected_y)

        # Width should be 1/4 of display width (480 for 1920)
        self.assertEqual(width, display_width // 4)
        # Height should be 100
        self.assertEqual(height, 100)

    def test_set_environ(self):
        for folder in ['folderäö', 'folder']:
            test_dir = os.path.join(self.tempdir, folder)
            os.mkdir(test_dir)
            self.assertExists(test_dir)
            set_environ('cd_test', test_dir)
            self.assertEqual(os.environ['cd_test'], test_dir)
            os.environ.pop('cd_test')
