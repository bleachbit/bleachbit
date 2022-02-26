# vim: ts=4:sw=4:expandtab

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

import bleachbit
from bleachbit import _, Command, FileUtilities, General

import glob
import logging
import os
import sys
import shutil
from threading import Thread, Event
import xml.dom.minidom

from decimal import Decimal

if 'win32' == sys.platform:
    import winreg
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32gui
    import win32process
    import win32security

    from ctypes import windll, c_ulong, c_buffer, byref, sizeof
    from win32com.shell import shell, shellcon

    psapi = windll.psapi
    kernel = windll.kernel32

logger = logging.getLogger(__name__)


def browse_file(_, title):
    """Ask the user to select a single file.  Return full path"""
    try:
        ret = win32gui.GetOpenFileNameW(None,
                                        Flags=win32con.OFN_EXPLORER
                                        | win32con.OFN_FILEMUSTEXIST
                                        | win32con.OFN_HIDEREADONLY,
                                        Title=title)
    except pywintypes.error as e:
        logger = logging.getLogger(__name__)
        if 0 == e.winerror:
            logger.debug('browse_file(): user cancelled')
        else:
            logger.exception('exception in browse_file()')
        return None
    return ret[0]


def browse_files(_, title):
    """Ask the user to select files.  Return full paths"""
    try:
        # The File parameter is a hack to increase the buffer length.
        ret = win32gui.GetOpenFileNameW(None,
                                        File='\x00' * 10240,
                                        Flags=win32con.OFN_ALLOWMULTISELECT
                                        | win32con.OFN_EXPLORER
                                        | win32con.OFN_FILEMUSTEXIST
                                        | win32con.OFN_HIDEREADONLY,
                                        Title=title)
    except pywintypes.error as e:
        if 0 == e.winerror:
            logger.debug('browse_files(): user cancelled')
        else:
            logger.exception('exception in browse_files()')
        return None
    _split = ret[0].split('\x00')
    if 1 == len(_split):
        # only one filename
        return _split
    dirname = _split[0]
    pathnames = [os.path.join(dirname, fname) for fname in _split[1:]]
    return pathnames


def browse_folder(_, title):
    """Ask the user to select a folder.  Return full path."""
    flags = 0x0010 #SHBrowseForFolder path input
    pidl = shell.SHBrowseForFolder(None, None, title, flags)[0]
    if pidl is None:
        # user cancelled
        return None
    fullpath = shell.SHGetPathFromIDListW(pidl)
    return fullpath


def cleanup_nonce():
    """On exit, clean up GTK junk files"""
    for fn in glob.glob(os.path.expandvars('%TEMP%\gdbus-nonce-file-*')):
        logger.debug('cleaning GTK nonce file: %s', fn)
        FileUtilities.delete(fn)


def csidl_to_environ(varname, csidl):
    """Define an environment variable from a CSIDL for use in CleanerML and Winapp2.ini"""
    try:
        sppath = shell.SHGetSpecialFolderPath(None, csidl)
    except:
        logger.info(
            'exception when getting special folder path for %s', varname)
        return
    # there is exception handling in set_environ()
    set_environ(varname, sppath)


def delete_locked_file(pathname):
    """Delete a file that is currently in use"""
    if os.path.exists(pathname):
        MOVEFILE_DELAY_UNTIL_REBOOT = 4
        if 0 == windll.kernel32.MoveFileExW(pathname, None, MOVEFILE_DELAY_UNTIL_REBOOT):
            from ctypes import WinError
            raise WinError()


def delete_registry_value(key, value_name, really_delete):
    """Delete named value under the registry key.
    Return boolean indicating whether reference found and
    successful.  If really_delete is False (meaning preview),
    just check whether the value exists."""
    (hive, sub_key) = split_registry_key(key)
    if really_delete:
        try:
            hkey = winreg.OpenKey(hive, sub_key, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(hkey, value_name)
        except WindowsError as e:
            if e.winerror == 2:
                # 2 = 'file not found' means value does not exist
                return False
            raise
        else:
            return True
    try:
        hkey = winreg.OpenKey(hive, sub_key)
        winreg.QueryValueEx(hkey, value_name)
    except WindowsError as e:
        if e.winerror == 2:
            return False
        raise
    else:
        return True


def delete_registry_key(parent_key, really_delete):
    """Delete registry key including any values and sub-keys.
    Return boolean whether found and success.  If really
    delete is False (meaning preview), just check whether
    the key exists."""
    parent_key = str(parent_key)  # Unicode to byte string
    (hive, parent_sub_key) = split_registry_key(parent_key)
    hkey = None
    try:
        hkey = winreg.OpenKey(hive, parent_sub_key)
    except WindowsError as e:
        if e.winerror == 2:
            # 2 = 'file not found' happens when key does not exist
            return False
    if not really_delete:
        return True
    if not hkey:
        # key not found
        return False
    keys_size = winreg.QueryInfoKey(hkey)[0]
    child_keys = [
        parent_key + '\\' + winreg.EnumKey(hkey, i) for i in range(keys_size)
    ]
    for child_key in child_keys:
        delete_registry_key(child_key, True)
    winreg.DeleteKey(hive, parent_sub_key)
    return True


def delete_updates():
    """Returns commands for deleting Windows Updates files"""
    windir = os.path.expandvars('%windir%')
    dirs = glob.glob(os.path.join(windir, '$NtUninstallKB*'))
    dirs += [os.path.expandvars(r'%windir%\SoftwareDistribution')]
    dirs += [os.path.expandvars(r'%windir%\SoftwareDistribution.old')]
    dirs += [os.path.expandvars(r'%windir%\SoftwareDistribution.bak')]
    dirs += [os.path.expandvars(r'%windir%\ie7updates')]
    dirs += [os.path.expandvars(r'%windir%\ie8updates')]
    dirs += [os.path.expandvars(r'%windir%\system32\catroot2')]
    if not dirs:
        # if nothing to delete, then also do not restart service
        return

    args = []

    def run_wu_service():
        General.run_external(args)
        return 0

    services = {}
    all_services = ('wuauserv', 'cryptsvc', 'bits', 'msiserver')
    for service in all_services:
        import win32serviceutil
        services[service] = win32serviceutil.QueryServiceStatus(service)[
            1] == 4
        logger.debug('Windows service {} has current state: {}'.format(
            service, services[service]))

        if services[service]:
            args = ['net', 'stop', service]
            yield Command.Function(None, run_wu_service, " ".join(args))

    for path1 in dirs:
        for path2 in FileUtilities.children_in_directory(path1, True):
            yield Command.Delete(path2)
        if os.path.exists(path1):
            yield Command.Delete(path1)

    for this_service in all_services:
        if services[this_service]:
            args = ['net', 'start', this_service]
            yield Command.Function(None, run_wu_service, " ".join(args))


def detect_registry_key(parent_key):
    """Detect whether registry key exists"""
    try:
        parent_key = str(parent_key)  # Unicode to byte string
    except UnicodeEncodeError:
        return False
    (hive, parent_sub_key) = split_registry_key(parent_key)
    hkey = None
    try:
        hkey = winreg.OpenKey(hive, parent_sub_key)
    except WindowsError as e:
        if e.winerror == 2:
            # 2 = 'file not found' happens when key does not exist
            return False
    if not hkey:
        # key not found
        return False
    return True


def elevate_privileges(uac):
    """On Windows Vista and later, try to get administrator
    privileges.  If successful, return True (so original process
    can exit).  If failed or not applicable, return False."""

    if shell.IsUserAnAdmin():
        logger.debug('already an admin (UAC not required)')
        htoken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
        newPrivileges = [
            (win32security.LookupPrivilegeValue(None, "SeBackupPrivilege"), win32security.SE_PRIVILEGE_ENABLED),
            (win32security.LookupPrivilegeValue(None, "SeRestorePrivilege"), win32security.SE_PRIVILEGE_ENABLED),
        ]
        win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)
        win32file.CloseHandle(htoken)
        return False
    elif not uac:
        return False

    if hasattr(sys, 'frozen'):
        # running frozen in py2exe
        exe = sys.executable
        parameters = "--gui --no-uac"
    else:
        pyfile = os.path.join(bleachbit.bleachbit_exe_path, 'bleachbit.py')
        # If the Python file is on a network drive, do not offer the UAC because
        # the administrator may not have privileges and user will not be
        # prompted.
        if len(pyfile) > 0 and path_on_network(pyfile):
            logger.debug(
                "debug: skipping UAC because '%s' is on network", pyfile)
            return False
        parameters = '"%s" --gui --no-uac' % pyfile
        exe = sys.executable


    parameters = _add_command_line_parameters(parameters)

    logger.debug('elevate_privileges() exe=%s, parameters=%s', exe, parameters)

    rc = None
    try:
        rc = shell.ShellExecuteEx(lpVerb='runas',
                                  lpFile=exe,
                                  lpParameters=parameters,
                                  nShow=win32con.SW_SHOW)
    except pywintypes.error as e:
        if 1223 == e.winerror:
            logger.debug('user denied the UAC dialog')
            return False
        raise

    logger.debug('ShellExecuteEx=%s', rc)

    if isinstance(rc, dict):
        return True

    return False


def _add_command_line_parameters(parameters):
    """
    Add any command line parameters such as --debug-log.
    """
    if '--context-menu' in sys.argv:
        return '{} {} "{}"'.format(parameters, ' '.join(sys.argv[1:-1]), sys.argv[-1])

    return '{} {}'.format(parameters, ' '.join(sys.argv[1:]))


def empty_recycle_bin(path, really_delete):
    """Empty the recycle bin or preview its size.

    If the recycle bin is empty, it is not emptied again to avoid an error.

    Keyword arguments:
    path          -- A drive, folder or None.  None refers to all recycle bins.
    really_delete -- If True, then delete.  If False, then just preview.
    """
    (bytes_used, num_files) = shell.SHQueryRecycleBin(path)
    if really_delete and num_files > 0:
        # Trying to delete an empty Recycle Bin on Vista/7 causes a
        # 'catastrophic failure'
        flags = shellcon.SHERB_NOSOUND | shellcon.SHERB_NOCONFIRMATION | shellcon.SHERB_NOPROGRESSUI
        shell.SHEmptyRecycleBin(None, path, flags)
    return bytes_used


def get_clipboard_paths():
    """Return a tuple of Unicode pathnames from the clipboard"""
    import win32clipboard
    win32clipboard.OpenClipboard()
    path_list = ()
    try:
        path_list = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
    except TypeError:
        pass
    finally:
        win32clipboard.CloseClipboard()
    return path_list


def get_fixed_drives():
    """Yield each fixed drive"""
    for drive in win32api.GetLogicalDriveStrings().split('\x00'):
        if win32file.GetDriveType(drive) == win32file.DRIVE_FIXED:
            # Microsoft Office 2010 Starter creates a virtual drive that
            # looks much like a fixed disk but isdir() returns false
            # and free_space() returns access denied.
            # https://bugs.launchpad.net/bleachbit/+bug/1474848
            if os.path.isdir(drive):
                yield drive


def get_known_folder_path(folder_name):
    """Return the path of a folder by its Folder ID

    Requires Windows Vista, Server 2008, or later

    Based on the code Michael Kropat (mkropat) from
    <https://gist.github.com/mkropat/7550097>
    licensed  under the GNU GPL"""
    import ctypes
    from ctypes import wintypes
    from uuid import UUID

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8)
        ]

        def __init__(self, uuid_):
            ctypes.Structure.__init__(self)
            self.Data1, self.Data2, self.Data3, self.Data4[
                0], self.Data4[1], rest = uuid_.fields
            for i in range(2, 8):
                self.Data4[i] = rest >> (8 - i - 1) * 8 & 0xff

    class FOLDERID:
        LocalAppDataLow = UUID(
            '{A520A1A4-1780-4FF6-BD18-167343C5AF16}')
        Fonts = UUID('{FD228CB7-AE11-4AE3-864C-16F3910AB8FE}')

    class UserHandle:
        current = wintypes.HANDLE(0)

    _CoTaskMemFree = windll.ole32.CoTaskMemFree
    _CoTaskMemFree.restype = None
    _CoTaskMemFree.argtypes = [ctypes.c_void_p]

    try:
        _SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    except AttributeError:
        # Not supported on Windows XP
        return None
    _SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(
            ctypes.c_wchar_p)
    ]

    class PathNotFoundException(Exception):
        pass

    folderid = getattr(FOLDERID, folder_name)
    fid = GUID(folderid)
    pPath = ctypes.c_wchar_p()
    S_OK = 0
    if _SHGetKnownFolderPath(ctypes.byref(fid), 0, UserHandle.current, ctypes.byref(pPath)) != S_OK:
        raise PathNotFoundException(folder_name)
    path = pPath.value
    _CoTaskMemFree(pPath)
    return path


def get_recycle_bin():
    """Yield a list of files in the recycle bin"""
    pidl = shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_BITBUCKET)
    desktop = shell.SHGetDesktopFolder()
    h = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)
    for item in h:
        path = h.GetDisplayNameOf(item, shellcon.SHGDN_FORPARSING)
        if os.path.isdir(path):
            # Return the contents of a normal directory, but do
            # not recurse Windows symlinks in the Recycle Bin.
            yield from FileUtilities.children_in_directory(path, True)
        yield path


def get_windows_version():
    """Get the Windows major and minor version in a decimal like 10.0"""
    v = win32api.GetVersionEx(0)
    vstr = '%d.%d' % (v[0], v[1])
    return Decimal(vstr)


def is_junction(path):
    """Check whether the path is a link

    On Python 2.7 the function os.path.islink() always returns False,
    so this is needed
    """
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    attr = windll.kernel32.GetFileAttributesW(path)
    return bool(attr & FILE_ATTRIBUTE_REPARSE_POINT)


def is_process_running(name):
    """Return boolean whether process (like firefox.exe) is running

    Works on Windows Vista or later, but on Windows XP gives an ImportError
    """

    import psutil
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                return True
        except psutil.NoSuchProcess:
            pass
    return False


def move_to_recycle_bin(path):
    """Move 'path' into recycle bin"""
    shell.SHFileOperation(
        (0, shellcon.FO_DELETE, path, None, shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION))


def parse_windows_build(build=None):
    """
    Parse build string like 1.2.3 or 1.2 to numeric,
    ignoring the third part, if present.
    """
    if not build:
        # If not given, default to current system's version
        return get_windows_version()
    return Decimal('.'.join(build.split('.')[0:2]))


def path_on_network(path):
    """Check whether 'path' is on a network drive"""
    drive = os.path.splitdrive(path)[0]
    if drive.startswith(r'\\'):
        return True
    return win32file.GetDriveType(drive) == win32file.DRIVE_REMOTE


def shell_change_notify():
    """Notify the Windows shell of update.

    Used in windows_explorer.xml."""
    shell.SHChangeNotify(shellcon.SHCNE_ASSOCCHANGED, shellcon.SHCNF_IDLIST,
                         None, None)
    return 0


def set_environ(varname, path):
    """Define an environment variable for use in CleanerML and Winapp2.ini"""
    if not path:
        return
    if varname in os.environ:
        #logger.debug('set_environ(%s, %s): skipping because environment variable is already defined', varname, path)
        if 'nt' == os.name:
            os.environ[varname] = os.path.expandvars('%%%s%%' % varname)
        # Do not redefine the environment variable when it already exists
        # But re-encode them with utf-8 instead of mbcs
        return
    try:
        if not os.path.exists(path):
            raise RuntimeError(
                'Variable %s points to a non-existent path %s' % (varname, path))
        os.environ[varname] = path
    except:
        logger.exception(
            'set_environ(%s, %s): exception when setting environment variable', varname, path)


def setup_environment():
    """Define any extra environment variables for use in CleanerML and Winapp2.ini"""
    csidl_to_environ('commonappdata', shellcon.CSIDL_COMMON_APPDATA)
    csidl_to_environ('documents', shellcon.CSIDL_PERSONAL)
    # Windows XP does not define localappdata, but Windows Vista and 7 do
    csidl_to_environ('localappdata', shellcon.CSIDL_LOCAL_APPDATA)
    csidl_to_environ('music', shellcon.CSIDL_MYMUSIC)
    csidl_to_environ('pictures', shellcon.CSIDL_MYPICTURES)
    csidl_to_environ('video', shellcon.CSIDL_MYVIDEO)
    # LocalLowAppData does not have a CSIDL for use with
    # SHGetSpecialFolderPath. Instead, it is identified using
    # SHGetKnownFolderPath in Windows Vista and later
    try:
        path = get_known_folder_path('LocalAppDataLow')
    except:
        logger.exception('exception identifying LocalAppDataLow')
    else:
        set_environ('LocalAppDataLow', path)
    # %cd% can be helpful for cleaning portable applications when
    # BleachBit is portable. It is the same variable name as defined by
    # cmd.exe .
    set_environ('cd', os.getcwd())


def split_registry_key(full_key):
    r"""Given a key like HKLM\Software split into tuple (hive, key).
    Used internally."""
    assert len(full_key) >= 6
    [k1, k2] = full_key.split("\\", 1)
    hive_map = {
        'HKCR': winreg.HKEY_CLASSES_ROOT,
        'HKCU': winreg.HKEY_CURRENT_USER,
        'HKLM': winreg.HKEY_LOCAL_MACHINE,
        'HKU': winreg.HKEY_USERS}
    if k1 not in hive_map:
        raise RuntimeError("Invalid Windows registry hive '%s'" % k1)
    return hive_map[k1], k2


def symlink_or_copy(src, dst):
    """Symlink with fallback to copy

    Symlink is faster and uses virtually no storage, but it it requires administrator
    privileges or Windows developer mode.

    If symlink is not available, just copy the file.
    """
    try:
        os.symlink(src, dst)
        logger.debug('linked %s to %s', src, dst)
    except (PermissionError, OSError) as e:
        shutil.copy(src, dst)
        logger.debug('copied %s to %s', src, dst)


def has_fontconfig_cache(font_conf_file):
    dom = xml.dom.minidom.parse(font_conf_file)
    fc_element = dom.getElementsByTagName('fontconfig')[0]
    cachefile = 'd031bbba323fd9e5b47e0ee5a0353f11-le32d8.cache-6'
    expanded_localdata = os.path.expandvars('%LOCALAPPDATA%')
    expanded_homepath = os.path.join(os.path.expandvars('%HOMEDRIVE%'), os.path.expandvars('%HOMEPATH%'))
    for dir_element in fc_element.getElementsByTagName('cachedir'):

        if dir_element.firstChild.nodeValue == 'LOCAL_APPDATA_FONTCONFIG_CACHE':
            dirpath = os.path.join(expanded_localdata, 'fontconfig', 'cache')
        elif dir_element.firstChild.nodeValue == 'fontconfig' and dir_element.getAttribute('prefix') == 'xdg':
            dirpath = os.path.join(expanded_homepath, '.cache', 'fontconfig')
        elif dir_element.firstChild.nodeValue == '~/.fontconfig':
            dirpath = os.path.join(expanded_homepath, '.fontconfig')
        else:
            # user has entered a custom directory
            dirpath = dir_element.firstChild.nodeValue

        if dirpath and os.path.exists(os.path.join(dirpath, cachefile)):
            return True

    return False


def get_font_conf_file():
    """Return the full path to fonts.conf"""
    if hasattr(sys, 'frozen'):
        # running inside py2exe
        return os.path.join(bleachbit.bleachbit_exe_path, 'etc', 'fonts', 'fonts.conf')

    import gi
    gnome_dir = os.path.join(os.path.dirname(os.path.dirname(gi.__file__)), 'gnome')
    if not os.path.isdir(gnome_dir):
        # BleachBit is running from a stand-alone Python installation.
        gnome_dir = os.path.join(sys.exec_prefix, '..', '..')
    return os.path.join(gnome_dir, 'etc', 'fonts', 'fonts.conf')


class SplashThread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        super().__init__(group, self._show_splash_screen, name, args, kwargs)
        self._splash_screen_started = Event()
        self._splash_screen_handle = None
        self._splash_screen_height = None
        self._splash_screen_width = None

    def start(self):
        Thread.start(self)
        self._splash_screen_started.wait()
        logger.debug('SplashThread started')

    def run(self):
        self._splash_screen_handle = self._target()
        self._splash_screen_started.set()

        # Dispatch messages
        win32gui.PumpMessages()

    def join(self, *args):
        import win32con, win32gui
        win32gui.PostMessage(self._splash_screen_handle, win32con.WM_CLOSE, 0, 0)
        Thread.join(self, *args)

    def _show_splash_screen(self):
        #get instance handle
        hInstance = win32api.GetModuleHandle()

        # the class name
        className = 'SimpleWin32'

        # create and initialize window class
        wndClass                = win32gui.WNDCLASS()
        wndClass.style          = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wndClass.lpfnWndProc    = self.wndProc
        wndClass.hInstance      = hInstance
        wndClass.hIcon          = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        wndClass.hCursor        = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wndClass.hbrBackground  = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wndClass.lpszClassName  = className

        # register window class
        wndClassAtom = None
        try:
            wndClassAtom = win32gui.RegisterClass(wndClass)
        except Exception as e:
            raise e

        displayWidth = win32api.GetSystemMetrics(0)
        displayHeigh = win32api.GetSystemMetrics(1)
        self._splash_screen_height = 100
        self._splash_screen_width = displayWidth // 4
        windowPosX = (displayWidth - self._splash_screen_width) // 2
        windowPosY = (displayHeigh - self._splash_screen_height) // 2

        hWindow = win32gui.CreateWindow(
            wndClassAtom,                   #it seems message dispatching only works with the atom, not the class name
            'Bleachbit splash screen',
            win32con.WS_POPUPWINDOW |
            win32con.WS_VISIBLE,
            windowPosX,
            windowPosY,
            self._splash_screen_width,
            self._splash_screen_height,
            0,
            0,
            hInstance,
            None)

        is_splash_screen_on_top = self._force_set_foreground_window(hWindow)
        logger.debug(
            'Is splash screen on top: {}'.format(is_splash_screen_on_top)
        )

        return hWindow

    def _force_set_foreground_window(self, hWindow):
        # As there are some restrictions about which processes can call SetForegroundWindow as described here:
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
        # we try consecutively three different ways to show the splash screen on top of all other windows.

        # Solution 1: Pressing alt key unlocks SetForegroundWindow
        # https://stackoverflow.com/questions/14295337/win32gui-setactivewindow-error-the-specified-procedure-could-not-be-found
        # Not using win32com.client.Dispatch like in the link because there are problems when building with py2exe.
        ALT_KEY = win32con.VK_MENU
        RIGHT_ALT = 0xb8
        win32api.keybd_event(ALT_KEY, RIGHT_ALT, 0, 0)
        win32api.keybd_event(ALT_KEY, RIGHT_ALT, win32con.KEYEVENTF_KEYUP, 0)
        win32gui.ShowWindow(hWindow, win32con.SW_SHOW)
        try:
            win32gui.SetForegroundWindow(hWindow)
        except Exception as e:
            exc_message = str(e)
            logger.debug(
                'Failed attempt to show splash screen with keybd_event: {}'.format(exc_message)
            )

        if win32gui.GetForegroundWindow() == hWindow:
            return True

        # Solution 2: Attaching current thread to the foreground thread in order to use BringWindowToTop
        # https://shlomio.wordpress.com/2012/09/04/solved-setforegroundwindow-win32-api-not-always-works/
        foreground_thread_id, foreground_process_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        appThread = win32api.GetCurrentThreadId()

        if foreground_thread_id != appThread:

            try:
                win32process.AttachThreadInput(foreground_thread_id, appThread, True)
                win32gui.BringWindowToTop(hWindow)
                win32gui.ShowWindow(hWindow, win32con.SW_SHOW)
                win32process.AttachThreadInput(foreground_thread_id, appThread, False)
            except Exception as e:
                exc_message = str(e)
                logger.debug(
                    'Failed attempt to show splash screen with AttachThreadInput: {}'.format(exc_message)
                )

        else:
            win32gui.BringWindowToTop(hWindow)
            win32gui.ShowWindow(hWindow, win32con.SW_SHOW)

        if win32gui.GetForegroundWindow() == hWindow:
            return True

        # Solution 3: Working with timers that lock/unlock SetForegroundWindow
        #https://gist.github.com/EBNull/1419093
        try:
            timeout = win32gui.SystemParametersInfo(win32con.SPI_GETFOREGROUNDLOCKTIMEOUT)
            win32gui.SystemParametersInfo(win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, 0, win32con.SPIF_SENDCHANGE)
            win32gui.BringWindowToTop(hWindow)
            win32gui.SetForegroundWindow(hWindow)
            win32gui.SystemParametersInfo(win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, timeout, win32con.SPIF_SENDCHANGE)
        except Exception as e:
            exc_message = str(e)
            logger.debug(
                'Failed attempt to show splash screen with SystemParametersInfo: {}'.format(exc_message)
            )

        if win32gui.GetForegroundWindow() == hWindow:
            return True

        # Solution 4: If on some machines the splash screen still doesn't come on top, we can try
        # the following solution that combines attaching to a thread and timers:
        # https://www.codeproject.com/Tips/76427/How-to-Bring-Window-to-Top-with-SetForegroundWindo

        return False

    def wndProc(self, hWnd, message, wParam, lParam):

        if message == win32con.WM_PAINT:
            hDC, paintStruct = win32gui.BeginPaint(hWnd)
            folder_with_ico_file = 'share' if hasattr(sys, 'frozen') else 'windows'
            filename = os.path.join(os.path.dirname(sys.argv[0]), folder_with_ico_file, 'bleachbit.ico')
            flags = win32con.LR_LOADFROMFILE
            hIcon = win32gui.LoadImage(
                0, filename, win32con.IMAGE_ICON,
                0, 0, flags)

            # Default icon size seems to be 32 pixels so we center the icon vertically.
            default_icon_size = 32
            icon_top_margin = self._splash_screen_height - 2 * (default_icon_size + 2)
            win32gui.DrawIcon(hDC, 0, icon_top_margin, hIcon)
            # win32gui.DrawIconEx(hDC, 0, 0, hIcon, 64, 64, 0, 0, win32con.DI_NORMAL)

            rect = win32gui.GetClientRect(hWnd)
            textmetrics = win32gui.GetTextMetrics(hDC)
            text_left_margin = 2 * default_icon_size
            text_rect = (text_left_margin, (rect[3]-textmetrics['Height'])//2, rect[2], rect[3])
            win32gui.DrawText(
                hDC,
                _("BleachBit is starting...\n"),
                -1,
                text_rect,
                win32con.DT_WORDBREAK)
            win32gui.EndPaint(hWnd, paintStruct)
            return 0

        elif message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0

        else:
            return win32gui.DefWindowProc(hWnd, message, wParam, lParam)

splash_thread = SplashThread()
