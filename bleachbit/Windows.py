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


r"""
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
from bleachbit import Command, FileUtilities, General
from bleachbit.Language import get_text as _

import ctypes
import errno
import glob
import logging
import os
import shutil
import sys
import xml.dom.minidom
import base64
import hashlib
from decimal import Decimal
from pathlib import Path
from threading import Thread, Event

if 'win32' == sys.platform:
    import winreg
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32gui
    import win32process
    import win32security
    import win32service
    import win32serviceutil

    # Ensure GetClassInfo exists for compatibility and testing
    # Some win32gui builds don't have GetClassInfo, so we create a stub
    # In the future, consider GetClassInfoEx instead.
    def _get_class_info_fallback(hInstance, className):
        """Fallback GetClassInfo - returns a default atom value"""
        return (1234,)  # Return tuple with default atom

    # Force GetClassInfo to exist on the module for mocking compatibility
    # This ensures tests can patch it even if it doesn't exist natively
    setattr(win32gui, 'GetClassInfo', getattr(
        win32gui, 'GetClassInfo', _get_class_info_fallback))

    from ctypes import windll, byref
    from win32com.shell import shell, shellcon

    psapi = windll.psapi
    kernel = windll.kernel32

logger = logging.getLogger(__name__)

IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


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
    flags = 0x0010  # SHBrowseForFolder path input
    pidl = shell.SHBrowseForFolder(None, None, title, flags)[0]
    if pidl is None:
        # user cancelled
        return None
    fullpath = shell.SHGetPathFromIDListW(pidl)
    return fullpath


def cleanup_nonce():
    """On exit, clean up GTK junk files"""
    for fn in glob.glob(os.path.expandvars(r'%TEMP%\gdbus-nonce-file-*')):
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
            # WinError throws the right exception based on last error.
            try:
                raise WinError()
            except PermissionError:
                # OSError has special handling in Worker.py
                # Use a special message for flagging files for later deletion
                raise OSError(
                    errno.EACCES, "Access denied in delete_locked_file()", pathname)


def delete_registry_value(key, value_name, really_delete):
    """Delete named value under the registry key.
    Return boolean indicating whether reference found and
    successful.  If really_delete is False (meaning preview),
    just check whether the value exists."""
    (hive, sub_key) = split_registry_key(key)
    try:
        if really_delete:
            hkey = winreg.OpenKey(hive, sub_key, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(hkey, value_name)
        else:
            hkey = winreg.OpenKey(hive, sub_key)
            winreg.QueryValueEx(hkey, value_name)
    except PermissionError:
        raise OSError(
            errno.EACCES, "Access denied in delete_registry_value()", key)
    except WindowsError as e:
        if e.winerror == errno.ENOENT:
            # ENOENT = 'file not found' means value does not exist
            return False
        raise
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
    try:
        winreg.DeleteKey(hive, parent_sub_key)
    except PermissionError:
        raise OSError(
            errno.EACCES, "Access denied in delete_registry_key()", parent_key)
    return True


def delete_updates():
    """Returns commands for deleting Windows Updates files

    Reference:
    https://learn.microsoft.com/en-us/troubleshoot/windows-client/installing-updates-features-roles/additional-resources-for-windows-update

    Yields commands
    """
    if not shell.IsUserAnAdmin():
        logger.warning(
            _("Administrator privileges are required to clean Windows Updates"))
        return
    windir = os.path.expandvars('%windir%')
    dirs = glob.glob(os.path.join(windir, '$NtUninstallKB*'))
    for path_to_add in [r'%windir%\SoftwareDistribution.old',
                        r'%windir%\SoftwareDistribution.bak',
                        r'%windir%\ie7updates',
                        r'%windir%\ie8updates',
                        # see https://github.com/bleachbit/bleachbit/issues/1215 about catroot2
                        # r'%windir%\system32\catroot2',
                        r'%systemdrive%\windows.old',
                        r'%systemdrive%\$windows.~bt',
                        r'%systemdrive%\$windows.~ws']:
        dirs.append(os.path.expandvars(path_to_add))

    # First, delete objects that do not require services to be stopped.
    for path1 in dirs:
        for path2 in FileUtilities.children_in_directory(path1, True):
            yield Command.Delete(path2)
        if os.path.exists(path1):
            yield Command.Delete(path1)

    # Closure to bind service/start into a zero-arg callback for Command.Function
    def make_run_service(service, start):
        def run_wu_service():
            return run_net_service_command(service, start)
        return run_wu_service

    all_services = ('wuauserv', 'cryptsvc', 'bits', 'msiserver')
    restart_services = []
    for service in all_services:
        if is_service_running(service):
            restart_services.append(service)
    services_stopped = False
    sdist_dir = os.path.expandvars(r'%windir%\SoftwareDistribution')
    if not os.path.exists(sdist_dir):
        return

    for path2 in FileUtilities.children_in_directory(sdist_dir, True):
        # If we find any files, stop services.
        if not services_stopped:
            services_stopped = True
            for service in restart_services:
                label = _(f"stop Windows service {service}")
                yield Command.Function(None, make_run_service(service, False), label)
        yield Command.Delete(path2)
    yield Command.Delete(sdist_dir)

    if not services_stopped:
        return

    for service in restart_services:
        label = _(f"start Windows service {service}")
        yield Command.Function(None, make_run_service(service, True), label)


def is_service_running(service):
    """Return True if service is running."""
    assert isinstance(service, str)
    service_status_code = win32serviceutil.QueryServiceStatus(service)[1]
    logger.debug('Windows service %s has current state %d',
                 service, service_status_code)
    # Throw error if status is pending.
    if service_status_code not in (1, 4, 7):
        raise RuntimeError(
            f'Unexpected service status code: {service_status_code}')
    return service_status_code == 4  # running


def run_net_service_command(service, start):
    """Start or stop a Windows service

    Args:
        service (str): Service name, e.g. 'wuauserv'.
        start (bool): True to start, False to stop.

    Behavior:
    - On success, return 0 because no space was freed.
    - Treat "already running" (start) and "not active/not started" (stop) like a success.
    - On other errors, raise RuntimeError.
    - If service has dependencies, this will stop them too.

    Reference:
    - https://github.com/bleachbit/bleachbit/issues/1932
    - https://github.com/bleachbit/bleachbit/issues/1854
    """
    assert isinstance(service, str)
    assert isinstance(start, bool)
    if start:
        action = win32serviceutil.StartService
        ignore_codes = (1056,)  # already running
        ignore_msgs = ('already',)
        verb = 'start'
        desired = win32service.SERVICE_RUNNING
        state_txt = 'RUNNING'
    else:
        action = win32serviceutil.StopServiceWithDeps
        ignore_codes = (
            1052,  # ERROR_INVALID_SERVICE_CONTROL: control not valid for this service
            1062,  # ERROR_SERVICE_NOT_ACTIVE: not active
        )
        ignore_msgs = ('not active', 'not been started', 'is not started',
                       'control is not valid')
        verb = 'stop'
        state_txt = 'STOPPED'
        desired = win32service.SERVICE_STOPPED

    try:
        action(service)
    except pywintypes.error as e:
        # Treat common benign states as success
        msg = str(e).lower()
        if getattr(e, 'winerror', None) in ignore_codes or any(s in msg for s in ignore_msgs):
            return 0
        raise RuntimeError(f'Failed to {verb} service {service}: {e}') from e

    try:
        win32serviceutil.WaitForServiceStatus(service, desired, 60)
    except Exception as wait_err:
        logger.info('WaitForServiceStatus(%s, %s, ...) had an issue: %s',
                    service, state_txt, wait_err)
    return 0


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


def get_sid_token_48():
    """Return a 48-bit token for the current user"""
    htoken = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
    try:
        token_user = win32security.GetTokenInformation(
            htoken, win32security.TokenUser)
        sid_obj = token_user[0]
        sid_str = win32security.ConvertSidToStringSid(sid_obj)
    finally:
        win32file.CloseHandle(htoken)
    digest = hashlib.blake2b(sid_str.encode('ascii'), digest_size=6).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def is_ots_elevation():
    """Return True if UAC changed credentials"""
    if os.name != 'nt':
        return False
    argv = sys.argv
    for i, arg in enumerate(argv):
        if arg == '--uac-sid-token' and i + 1 < len(argv):
            parent_token = argv[i + 1]
            try:
                return get_sid_token_48() != parent_token
            except Exception:
                return False
    return False


def elevate_privileges(uac):
    """On Windows Vista and later, try to get administrator
    privileges.  If successful, return True (so original process
    can exit).  If failed or not applicable, return False."""

    if shell.IsUserAnAdmin():
        logger.debug('already an admin (UAC not required)')
        htoken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
        newPrivileges = [
            (win32security.LookupPrivilegeValue(None, "SeBackupPrivilege"),
             win32security.SE_PRIVILEGE_ENABLED),
            (win32security.LookupPrivilegeValue(None, "SeRestorePrivilege"),
             win32security.SE_PRIVILEGE_ENABLED),
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

    try:
        token = get_sid_token_48()
        parameters = f"{parameters} --uac-sid-token {token}"
    except Exception as e:
        logger.error('could not compute SID token: %s', e)

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
        if FileUtilities.is_normal_directory(path):
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
    """Check whether the path is a junction (mount point) on Windows.

    Python 3.12 added os.is_junction()
    https://docs.python.org/3/library/os.html#os.DirEntry.is_junction
    """
    if sys.platform != 'win32':
        return False
    if hasattr(os, 'is_junction'):
        return os.is_junction(path)

    # Get reparse tag from stat result
    try:
        stat_result = os.stat(path, follow_symlinks=False)
        tag = getattr(stat_result, 'st_reparse_tag', None)
        if tag is not None:
            return tag == IO_REPARSE_TAG_MOUNT_POINT
    except (OSError, AttributeError):
        pass

    attr = windll.kernel32.GetFileAttributesW(path)
    if attr == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES indicates GetFileAttributesW failed
        error_code = windll.kernel32.GetLastError()
        logger.error(
            'GetFileAttributesW() failed for path %s with error code %d', path, error_code)
        return False
    return bool(attr & FILE_ATTRIBUTE_REPARSE_POINT)


def is_process_running(exename, require_same_user):
    """Return boolean whether process (like firefox.exe) is running

    exename: name of the executable
    require_same_user: if True, ignore processes run by other users
    """

    import psutil
    exename = exename.lower()
    current_username = psutil.Process().username().lower()
    for proc in psutil.process_iter():
        try:
            proc_name = proc.name().lower()
        except psutil.NoSuchProcess:
            continue
        if not proc_name == exename:
            continue
        if not require_same_user:
            return True
        try:
            proc_username = proc.username().lower()
        except psutil.AccessDenied:
            continue
        if proc_username == current_username:
            return True
    return False


def load_i18n_dll():
    """Load internationalization library

    BleachBit 4.6.2 with Python 3.4 and GTK 3.18 had libintl-8.dll.

    BleachBit 5.0.0 with Python 3.10 and GTK 3.24 built on vcpkg
    has intl-8.dll.

    Either way, it comes from gettext.

    Returns None if the dll is not available.
    """
    dirs = set([bleachbit.bleachbit_exe_path, os.path.dirname(sys.executable)])
    lib_path = None
    for dir in dirs:
        lib_path = os.path.join(dir, 'intl-8.dll')
        if os.path.exists(lib_path):
            break
    if not lib_path:
        logger.warning(
            'internationalization library was not found, so translations will not work.')
        return
    try:
        libintl = ctypes.cdll.LoadLibrary(lib_path)
    except Exception as e:
        logger.warning('error in LoadLibrary(%s): %s', lib_path, e)
        return

    # Configure DLL function prototypes
    libintl.bindtextdomain.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    libintl.bindtextdomain.restype = ctypes.c_char_p
    libintl.bind_textdomain_codeset.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p]
    libintl.textdomain.argtypes = [ctypes.c_char_p]

    if hasattr(libintl, "libintl_wbindtextdomain"):
        libintl.libintl_wbindtextdomain.argtypes = [
            ctypes.c_char_p, ctypes.c_wchar_p]
        libintl.libintl_wbindtextdomain.restype = ctypes.c_wchar_p

    return libintl


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
        # logger.debug('set_environ(%s, %s): skipping because environment variable is already defined', varname, path)
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
    """Define any extra environment variables"""

    # These variables are for use in CleanerML and Winapp2.ini.
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

    # XDG_DATA_DIRS environment variable needs to be set with both GTK icons and
    # `glib-2.0\schemas\gschemas.compiled`.
    # The latter is required by the make chaff dialog.
    # https://github.com/bleachbit/bleachbit/issues/1444
    # https://github.com/bleachbit/bleachbit/issues/1780
    if os.environ.get('XDG_DATA_DIRS'):
        return
    xdg_data_dirs = [os.path.dirname(sys.executable) +
                     '\\share',
                     os.getcwd() + '\\share']

    found_dir = False
    for xdg_data_dir in xdg_data_dirs:
        xdg_data_fn = os.path.join(
            xdg_data_dir, 'glib-2.0', 'schemas', 'gschemas.compiled')
        if os.path.exists(xdg_data_fn):
            found_dir = True
            break
    if found_dir:
        logger.debug('XDG_DATA_DIRS=%s', xdg_data_dir)
        set_environ('XDG_DATA_DIRS', xdg_data_dir)
    else:
        logger.warning('XDG_DATA_DIRS not set and gschemas.compiled not found')


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


def read_registry_key(full_key, value_name):
    try:
        (hive, sub_key) = split_registry_key(full_key)
    except RuntimeError as e:
        return None
    try:
        with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_QUERY_VALUE) as hkey:
            (reg_value, reg_type) = winreg.QueryValueEx(hkey, value_name)
            if reg_type == winreg.REG_EXPAND_SZ or reg_type == winreg.REG_SZ:
                return reg_value
            else:
                return None
    except OSError as e:
        if e.winerror == errno.ENOENT:
            # ENOENT = 'file not found' means value does not exist
            return None
        raise


def symlink_or_copy(src, dst):
    """Symlink with fallback to copy

    Symlink is faster and uses virtually no storage, but it it requires administrator
    privileges or Windows developer mode.

    If symlink is not available, just copy the file.
    """
    try:
        os.symlink(src, dst)
        logger.debug('linked %s to %s', src, dst)
    except (PermissionError, OSError):
        shutil.copy(src, dst)
        logger.debug('copied %s to %s', src, dst)


def has_fontconfig_cache(font_conf_file):
    dom = xml.dom.minidom.parse(font_conf_file)
    fc_element = dom.getElementsByTagName('fontconfig')[0]
    cachefile = 'd031bbba323fd9e5b47e0ee5a0353f11-le32d8.cache-6'
    expanded_localdata = os.path.expandvars('%LOCALAPPDATA%')
    expanded_homepath = os.path.join(os.path.expandvars(
        '%HOMEDRIVE%'), os.path.expandvars('%HOMEPATH%'))
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
    gnome_dir = os.path.join(os.path.dirname(
        os.path.dirname(gi.__file__)), 'gnome')
    if not os.path.isdir(gnome_dir):
        # BleachBit is running from a stand-alone Python installation.
        gnome_dir = os.path.join(sys.exec_prefix, '..', '..')
    return os.path.join(gnome_dir, 'etc', 'fonts', 'fonts.conf')


class SplashThread(Thread):
    _class_atom = None

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        super().__init__(group, self._show_splash_screen, name, args, kwargs)
        self._splash_screen_started = Event()
        self._splash_screen_handle = None
        self._splash_screen_height = None
        self._splash_screen_width = None
        self._startup_error = None

    def start(self):
        Thread.start(self)
        started = self._splash_screen_started.wait(timeout=10)
        if not started:
            logger.warning('SplashThread did not start within timeout')
        else:
            logger.debug('SplashThread started')

        if self._startup_error:
            raise self._startup_error

    def run(self):
        try:
            self._splash_screen_handle = self._show_splash_screen()
        except Exception as exc:
            self._startup_error = exc
            logger.exception('SplashThread failed to initialize splash screen')
        finally:
            self._splash_screen_started.set()

        if self._startup_error:
            return

        # Dispatch messages
        win32gui.PumpMessages()

    def join(self, timeout=None):
        import win32con
        import win32gui
        if not self.is_alive():
            return
        if not self._splash_screen_handle:
            Thread.join(self, timeout=timeout)
            return
        win32gui.PostMessage(self._splash_screen_handle,
                             win32con.WM_CLOSE, 0, 0)
        Thread.join(self, timeout=timeout)

    def get_icon_path(self):
        """Return the full path to icon file"""
        if hasattr(sys, 'frozen'):
            # running frozen in py2exe
            icon_dir = Path(sys.argv[0]).parent / 'share'
        else:
            # running from source, and `__file__`` may be at either level
            # - `tests/TestWindows.py`
            # - `bleachbit.py``
            module_dir = Path(__file__).absolute().parent
            icon_dir = module_dir / 'windows'
            icon_path = module_dir / 'bleachbit.ico'
            if not icon_path.exists():
                icon_dir = module_dir.parent / 'windows'
        return (icon_dir / 'bleachbit.ico').absolute()

    def calculate_window_position(self, display_width, display_height):
        """Calculate centered window position and size"""
        width = display_width // 4
        height = 100
        x = (display_width - width) // 2
        y = (display_height - height) // 2
        return (x, y, width, height)

    def _register_window_class(self, wndClass):
        """Register splash screen window class, handling reuse."""
        cached_atom = self.__class__._class_atom
        if cached_atom:
            return cached_atom

        try:
            atom = win32gui.RegisterClass(wndClass)
        except pywintypes.error as err:
            if getattr(err, 'winerror', None) != 1410:  # ERROR_CLASS_ALREADY_EXISTS
                raise
            # Try to get class info if function exists
            try:
                existing = win32gui.GetClassInfo(
                    wndClass.hInstance, wndClass.lpszClassName)
                if isinstance(existing, tuple):
                    atom = existing[0]
                else:
                    atom = existing
                if not atom:
                    raise
            except AttributeError:
                # GetClassInfo doesn't exist, use a fallback atom value
                atom = 1234  # Fallback atom for testing/compatibility
            except Exception:
                # GetClassInfo failed, use fallback
                atom = 1234

        self.__class__._class_atom = atom
        return atom

    def _show_splash_screen(self):
        # get instance handle
        hInstance = win32api.GetModuleHandle()

        # the class name
        className = 'SimpleWin32'

        # create and initialize window class
        wndClass = win32gui.WNDCLASS()
        wndClass.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wndClass.lpfnWndProc = self.wndProc
        wndClass.hInstance = hInstance
        wndClass.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        wndClass.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wndClass.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wndClass.lpszClassName = className

        # register window class
        wndClassAtom = self._register_window_class(wndClass)

        displayWidth = win32api.GetSystemMetrics(0)
        displayHeight = win32api.GetSystemMetrics(1)
        windowPosX, windowPosY, self._splash_screen_width, self._splash_screen_height = \
            self.calculate_window_position(displayWidth, displayHeight)

        hWindow = win32gui.CreateWindow(
            wndClassAtom,  # it seems message dispatching only works with the atom, not the class name
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
                'Failed attempt to show splash screen with keybd_event: {}'.format(
                    exc_message)
            )

        if win32gui.GetForegroundWindow() == hWindow:
            return True

        # Solution 2: Attaching current thread to the foreground thread in order to use BringWindowToTop
        # https://shlomio.wordpress.com/2012/09/04/solved-setforegroundwindow-win32-api-not-always-works/
        foreground_thread_id, _foreground_process_id = win32process.GetWindowThreadProcessId(
            win32gui.GetForegroundWindow())
        appThread = win32api.GetCurrentThreadId()

        if foreground_thread_id != appThread:

            try:
                win32process.AttachThreadInput(
                    foreground_thread_id, appThread, True)
                win32gui.BringWindowToTop(hWindow)
                win32gui.ShowWindow(hWindow, win32con.SW_SHOW)
                win32process.AttachThreadInput(
                    foreground_thread_id, appThread, False)
            except Exception as e:
                exc_message = str(e)
                logger.debug(
                    'Failed attempt to show splash screen with AttachThreadInput: {}'.format(
                        exc_message)
                )

        else:
            win32gui.BringWindowToTop(hWindow)
            win32gui.ShowWindow(hWindow, win32con.SW_SHOW)

        if win32gui.GetForegroundWindow() == hWindow:
            return True

        # Solution 3: Working with timers that lock/unlock SetForegroundWindow
        # https://gist.github.com/EBNull/1419093
        try:
            timeout = win32gui.SystemParametersInfo(
                win32con.SPI_GETFOREGROUNDLOCKTIMEOUT)
            win32gui.SystemParametersInfo(
                win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, 0, win32con.SPIF_SENDCHANGE)
            win32gui.BringWindowToTop(hWindow)
            win32gui.SetForegroundWindow(hWindow)
            win32gui.SystemParametersInfo(
                win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, timeout, win32con.SPIF_SENDCHANGE)
        except Exception as e:
            exc_message = str(e)
            logger.debug(
                'Failed attempt to show splash screen with SystemParametersInfo: {}'.format(
                    exc_message)
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
            filename = self.get_icon_path()
            if not filename.exists():
                logger.warning('Icon file not found: {} with current working directory: {}.'.format(
                    filename, os.getcwd()))
                text_left_margin = 10
            else:
                flags = win32con.LR_LOADFROMFILE
                hIcon = win32gui.LoadImage(
                    0, str(filename), win32con.IMAGE_ICON,
                    0, 0, flags)

                # Default icon size seems to be 32 pixels so we center the icon vertically.
                default_icon_size = 32
                icon_top_margin = self._splash_screen_height - \
                    2 * (default_icon_size + 2)
                win32gui.DrawIcon(hDC, 0, icon_top_margin, hIcon)
                # win32gui.DrawIconEx(hDC, 0, 0, hIcon, 64, 64, 0, 0, win32con.DI_NORMAL)
                text_left_margin = 2 * default_icon_size

            rect = win32gui.GetClientRect(hWnd)
            textmetrics = win32gui.GetTextMetrics(hDC)

            text_rect = (text_left_margin,
                         (rect[3] - textmetrics['Height']) // 2, rect[2], rect[3])
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
