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
File-related utilities
"""

# standard imports
import atexit
import contextlib
import ctypes
import errno
import glob
import json
import locale
import logging
import os
import os.path
import random
import re
import sqlite3
import stat
import string
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import warnings
from pathlib import Path

# local imports
import bleachbit
from bleachbit.Language import get_text as _


logger = logging.getLogger(__name__)

if 'nt' == os.name:
    # pylint: disable=import-error, no-name-in-module
    from pywintypes import error as pywinerror
    import win32file
    # pylint: disable=import-error
    from win32com.shell.shell import IsUserAnAdmin
    # pylint: disable=ungrouped-imports
    import bleachbit.Windows
    os_path_islink = os.path.islink
    os.path.islink = lambda path: os_path_islink(
        path) or bleachbit.Windows.is_junction(path)

if 'posix' == os.name:
    # pylint: disable=redefined-builtin
    from bleachbit.General import WindowsError
    # pylint: disable=invalid-name
    pywinerror = WindowsError

try:
    # FIXME: replace scandir.walk() with os.scandir()
    # Preserve behavior added in 25e694.
    # Test that os.walk() behaves the same on Windows.
    from scandir import walk
    if 'nt' == os.name:
        import scandir

        class _Win32DirEntryPython(scandir.Win32DirEntryPython):
            def is_symlink(self):
                """internal use"""
                return super(_Win32DirEntryPython, self).is_symlink() or \
                    bleachbit.Windows.is_junction(self.path)

        scandir.scandir = scandir.scandir_python
        scandir.DirEntry = scandir.Win32DirEntryPython = _Win32DirEntryPython
except ImportError:
    # Since Python 3.5, os.walk() calls os.scandir().
    from os import walk


def open_files_linux():
    """Return iterator of open files on Linux"""
    return glob.iglob("/proc/*/fd/*")


def get_filesystem_type(path):
    """Get file system type from the given path

    path: directory path

    Return value:
    A tuple of (file_system_type, device_name)
    file_system_type: vfat, ntfs, etc.
    device_name: C:, D:, etc.

    File system types seen
    * On Linux: btrfs,ext4, vfat, squashfs
    * On Windows: NTFS, FAT32, CDFS
    """
    try:
        # pylint: disable=import-outside-toplevel
        import psutil
    except ImportError:
        logger.warning(
            'To get the file system type from the given path, you need to install psutil package')
        return ("unknown", "none")

    path_obj = Path(path)
    if os.name == 'nt':
        if len(path) == 2 and path[1] == ':':
            path_obj = Path(path + '\\')

    # Get all partitions with Path objects as keys
    partitions = {}
    for partition in psutil.disk_partitions():
        mount_path = Path(partition.mountpoint)
        partitions[mount_path] = (partition.fstype, partition.device)

    # Exact match
    for mount_path, fs_info in partitions.items():
        if path_obj == mount_path:
            return fs_info

    # Try parent paths
    current = path_obj
    while current.parent != current:  # Stop at root
        current = current.parent
        for mount_path, fs_info in partitions.items():
            if current == mount_path:
                return fs_info

    return ("unknown", "none")


def open_files_lsof(run_lsof=None):
    """Return iterator of open files using lsof"""
    if run_lsof is None:
        def run_lsof():
            return subprocess.check_output(["lsof", "-Fn", "-n"])
    for f in run_lsof().split("\n"):
        if f.startswith("n/"):
            yield f[1:]  # Drop lsof's "n"


def open_files():
    """Return iterator of open files"""
    if sys.platform == 'linux':
        files = open_files_linux()
    elif 'darwin' == sys.platform or sys.platform.startswith('freebsd'):
        files = open_files_lsof()
    else:
        raise RuntimeError('unsupported platform for open_files()')
    for filename in files:
        try:
            target = os.path.realpath(filename)
        except TypeError:
            # happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            continue
        except PermissionError:
            # /proc/###/fd/0 with systemd
            # https://github.com/bleachbit/bleachbit/issues/1515
            continue
        else:
            yield target


class OpenFiles:

    """Cached way to determine whether a file is open by active process"""

    def __init__(self):
        self.last_scan_time = None
        self.files = []

    def file_qualifies(self, filename):
        """Return boolean whether filename qualifies to enter cache (check \
        against blacklist)"""
        return not filename.startswith("/dev") and \
            not filename.startswith("/proc")

    def scan(self):
        """Update cache"""
        self.last_scan_time = time.time()
        self.files = []
        for filename in open_files():
            if self.file_qualifies(filename):
                self.files.append(filename)

    def is_open(self, filename):
        """Return boolean whether filename is open by running process"""
        if self.last_scan_time is None or (time.time() - self.last_scan_time) > 10:
            self.scan()
        return os.path.realpath(filename) in self.files


def __random_string(length):
    """Return random alphanumeric characters of given length"""
    return ''.join(random.choice(string.ascii_letters + '0123456789_.-')
                   for i in range(length))


def bytes_to_human(bytes_i):
    # type: (int) -> str
    """Display a file size in human terms (megabytes, etc.) using preferred standard (SI or IEC)"""

    if bytes_i < 0:
        return '-' + bytes_to_human(-bytes_i)

    from bleachbit.Options import options
    if options.get('units_iec'):
        prefixes = ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi']
        base = 1024.0
    else:
        prefixes = ['', 'k', 'M', 'G', 'T', 'P']
        base = 1000.0

    assert isinstance(bytes_i, int)

    if 0 == bytes_i:
        return '0B'

    if bytes_i >= base ** 3:
        decimals = 2
    elif bytes_i >= base:
        decimals = 1
    else:
        decimals = 0

    for _exponent, prefix in enumerate(prefixes):
        if bytes_i < base:
            abbrev = round(bytes_i, decimals)
            suf = prefix
            return locale.str(abbrev) + suf + 'B'
        bytes_i /= base
    return 'A lot.'


def children_in_directory(top, list_directories=False):
    """Iterate files and, optionally, subdirectories in directory"""
    if isinstance(top, tuple):
        for top_ in top:
            yield from children_in_directory(top_, list_directories)
        return
    for (dirpath, dirnames, filenames) in walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def clean_ini(path, section, parameter):
    """Delete sections and parameters (aka option) in the file

    Comments are not preserved.
    """

    def write(parser, ini_file):
        """
        Reimplementation of the original RowConfigParser write function.

        This function is 99% same as its origin. The only change is
        removing a cast to str. This is needed to handle unicode chars.
        """
        if parser._defaults:
            ini_file.write("[DEFAULT]\n")
            for (key, value) in parser._defaults.items():
                value_str = str(value).replace('\n', '\n\t')
                ini_file.write(f"{key} = {value_str}\n")
            ini_file.write("\n")
        for section in parser._sections:
            ini_file.write(f"[{section}]\n")
            for (key, value) in parser._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (parser._optcre == parser.OPTCRE):
                    # The line below is the only changed line of the original function.
                    # This is the original line for reference:
                    # key = " = ".join((key, str(value).replace('\n', '\n\t')))
                    key = " = ".join((key, value.replace('\n', '\n\t')))
                ini_file.write(f"{key}\n")
            ini_file.write("\n")

    encoding = detect_encoding(path) or 'utf_8_sig'

    # read file to parser
    config = bleachbit.RawConfigParser(delimiters='=')
    config.optionxform = lambda option: option
    config.write = write
    with open(path, 'r', encoding=encoding) as fp:
        config.read_file(fp)

    # change file
    changed = False
    if config.has_section(section):
        if parameter is None:
            changed = True
            config.remove_section(section)
        elif config.has_option(section, parameter):
            changed = True
            config.remove_option(section, parameter)

    # write file
    if changed:
        from bleachbit.Options import options
        fp.close()
        if options.get('shred'):
            delete(path, True)
        with open(path, 'w', encoding=encoding, newline='') as fp:
            config.write(config, fp)


def clean_json(path, target):
    """Delete key in the JSON file"""
    changed = False
    targets = target.split('/')

    # read file to parser
    with open(path, 'r', encoding='utf-8-sig') as f:
        js = json.load(f)

    # change file
    pos = js
    while True:
        new_target = targets.pop(0)
        if not isinstance(pos, dict):
            break
        if new_target in pos and len(targets) > 0:
            # descend
            pos = pos[new_target]
        elif new_target in pos:
            # delete terminal target
            changed = True
            del pos[new_target]
        else:
            # target not found
            break
        if 0 == len(targets):
            # target not found
            break

    if changed:
        from bleachbit.Options import options
        if options.get('shred'):
            delete(path, True)
        # write file
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(js, f)


def delete(path, shred=False, ignore_missing=False, allow_shred=True):
    """Delete path that is either file, directory, link or FIFO.

       If shred is enabled as a function parameter or the BleachBit global
       parameter, the path will be shredded unless allow_shred = False.

       All links are removed without following the link. This includes:
       * Linux symlink
       * Windows symlink (soft link)
       * Windows hard link
       * Windows junction
       * Windows .lnk files
    """
    from bleachbit.Options import options
    is_special = False
    path = extended_path(path)
    do_shred = allow_shred and (shred or options.get('shred'))
    if not os.path.lexists(path):
        if ignore_missing:
            return
        raise OSError(2, 'No such file or directory', path)
    if 'posix' == os.name:
        # With certain (relatively rare) files on Windows os.lstat()
        # may return Access Denied
        mode = os.lstat(path)[stat.ST_MODE]
        is_special = stat.S_ISFIFO(mode) or stat.S_ISLNK(mode)
    if is_special:
        os.remove(path)
    elif os.path.isdir(path):
        delpath = path
        if do_shred:
            if not is_dir_empty(path):
                # Avoid renaming non-empty directory like
                # https://github.com/bleachbit/bleachbit/issues/783
                logger.info(_("Directory is not empty: %s"), path)
                return
            delpath = wipe_name(path)
        try:
            os.rmdir(delpath)
        except OSError as e:
            # [Errno 39] Directory not empty
            # https://bugs.launchpad.net/bleachbit/+bug/1012930
            if errno.ENOTEMPTY == e.errno:
                logger.info(_("Directory is not empty: %s"), path)
            elif errno.EBUSY == e.errno:
                if os.name == 'posix' and os.path.ismount(path):
                    logger.info(_("Skipping mount point: %s"), path)
                else:
                    logger.info(_("Device or resource is busy: %s"), path)
            else:
                raise
        except WindowsError as e:
            # WindowsError: [Error 145] The directory is not empty:
            # 'C:\\Documents and Settings\\username\\Local Settings\\Temp\\NAILogs'
            # Error 145 may happen if the files are scheduled for deletion
            # during reboot.
            if 145 == e.winerror:
                logger.info(_("Directory is not empty: %s"), path)
            else:
                raise
    elif os.path.isfile(path):
        # wipe contents
        if do_shred:
            try:
                wipe_contents(path)
            except pywinerror as e:  # pylint: disable=possibly-used-before-assignment
                # 2 = The system cannot find the file specified.
                # This can happen with a broken symlink
                # https://github.com/bleachbit/bleachbit/issues/195
                if 2 != e.winerror:
                    raise
                # If a broken symlink, try os.remove() below.
            except IOError as e:
                # permission denied (13) happens shredding MSIE 8 on Windows 7
                logger.debug("IOError #%s shredding '%s'",
                             e.errno, path, exc_info=True)
            # wipe name
            os.remove(wipe_name(path))
        else:
            # unlink
            os.remove(path)
    elif os.path.islink(path):
        os.remove(path)
    else:
        logger.info(_("Special file type cannot be deleted: %s"), path)


def detect_encoding(fn):
    """Detect the encoding of the file"""
    try:
        # pylint: disable=import-outside-toplevel
        import chardet
    except ImportError:
        logger.warning(
            'chardet module is not available to detect character encoding')
        return None

    with open(fn, 'rb') as f:
        detector = chardet.universaldetector.UniversalDetector()
        for line in f.readlines():
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result['encoding']


def ego_owner(filename):
    """Return whether current user owns the file

    POSIX only"""
    assert 'posix' == os.name
    # pylint: disable=no-member
    return os.lstat(filename).st_uid == os.getuid()


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    delimiter = ':'
    if 'nt' == os.name:
        delimiter = ';'
    path_env = os.getenv('PATH')
    if not path_env:
        return False
    assert not os.path.isabs(filename)
    for dirname in path_env.split(delimiter):
        if os.path.exists(os.path.join(dirname, filename)):
            return True
    return False


def exe_exists(pathname):
    """Returns boolean whether executable exists"""
    if os.path.isabs(pathname):
        return os.path.exists(pathname)
    else:
        return exists_in_path(pathname)


def execute_sqlite3(path, cmds):
    """Execute SQL commands on SQLite database

    Args:
        path (str): Path to the SQLite database file
        cmds (str): SQL commands to execute, separated by semicolons

    Raises:
        sqlite3.OperationalError: If there's an error executing the SQL commands
        sqlite3.DatabaseError: If there's a database-related error

    Returns:
        None
    """
    from bleachbit.Options import options
    assert isinstance(path, str)
    assert isinstance(cmds, str)
    with contextlib.closing(sqlite3.connect(path)) as conn:
        # overwrites deleted content with zeros
        # https://www.sqlite.org/pragma.html#pragma_secure_delete
        if options.get('shred'):
            conn.execute('PRAGMA secure_delete=ON')
            assert conn.execute('PRAGMA secure_delete').fetchone()[0] == 1

        for cmd in cmds.split(';'):
            try:
                conn.execute(cmd)
            except sqlite3.OperationalError as exc:
                if str(exc).find('no such function: ') >= 0:
                    # fixme: determine why randomblob and zeroblob are not
                    # available
                    logger.exception(exc.message)
                else:
                    raise sqlite3.OperationalError(f'{exc}: {path}')
            except sqlite3.DatabaseError as exc:
                raise sqlite3.DatabaseError(f'{exc}: {path}')

        conn.commit()

    bleachbit.General.gc_collect()


def expand_glob_join(pathname1, pathname2):
    """Join pathname1 and pathname1, expand pathname, glob, and return as list"""
    pathname3 = os.path.expanduser(os.path.expandvars(
        os.path.join(pathname1, pathname2)))
    ret = [pathname4 for pathname4 in glob.iglob(pathname3)]
    return ret


def extended_path(path):
    r"""Return the extended Windows pathname

    example: c:\foo\bar.txt to \\?\c:\foo\bar.txt

    The path is returned unchanged if:
    * Path was already extended
    * Path is a sysnative path
    * System is not Windows
    """
    # Do not extend the Sysnative paths because on some systems there are
    # problems with path resolution. For example:
    # https://github.com/bleachbit/bleachbit/issues/1574.
    if 'nt' == os.name and 'Sysnative' not in path.split(os.sep):
        if path.startswith(r'\\?'):
            return path
        if path.startswith(r'\\'):
            return '\\\\?\\unc\\' + path[2:]
        return '\\\\?\\' + path
    return path


def extended_path_undo(path):
    r"""Undo extended path

    For example: \\c:\foo\bar.txt -> c:\foo\bar.txt
    """
    if 'nt' == os.name:
        if path.startswith(r'\\?\unc'):
            return '\\' + path[7:]
        if path.startswith(r'\\?'):
            return path[4:]
    return path


def free_space(pathname):
    """Return free space in bytes"""
    if 'nt' == os.name:
        # pylint: disable=import-error,import-outside-toplevel
        import psutil
        return psutil.disk_usage(pathname).free
    assert 'posix' == os.name
    # pylint: disable=no-member
    mystat = os.statvfs(pathname)
    return mystat.f_bfree * mystat.f_bsize


def getsize(path):
    """Return the actual file size considering spare files
       and symlinks"""
    if 'posix' == os.name:
        try:
            __stat = os.lstat(path)
        except OSError as e:
            # OSError: [Errno 13] Permission denied
            # can happen when a regular user is trying to find the size of /var/log/hp/tmp
            # where /var/log/hp is 0774 and /var/log/hp/tmp is 1774
            if errno.EACCES == e.errno:
                return 0
            raise
        return __stat.st_blocks * 512
    if 'nt' == os.name:
        # On rare files os.path.getsize() returns access denied, so first
        # try FindFilesW.
        # Also, apply prefix to use extended-length paths to support longer
        # filenames.
        try:
            # pylint: disable=c-extension-no-member
            finddata = win32file.FindFilesW(extended_path(path))
        except pywinerror as e:
            if e.winerror == 3:  # 3 = The system cannot find the path specified.
                raise OSError(errno.ENOENT, e.strerror, path)
            raise e
        if not finddata:
            # FindFilesW does not work for directories, so fall back to
            # getsize()
            return os.path.getsize(path)
        else:
            size = (finddata[0][4] * (0xffffffff + 1)) + finddata[0][5]
            return size
    return os.path.getsize(path)


def getsizedir(path):
    """Return the size of the contents of a directory"""
    total_bytes = sum(
        getsize(node)
        for node in children_in_directory(path, list_directories=False)
    )
    return total_bytes


def globex(pathname, regex):
    """Yield a list of files with pathname and filter by regex"""
    if isinstance(pathname, tuple):
        for singleglob in pathname:
            yield from globex(singleglob, regex)
    else:
        for path in glob.iglob(pathname):
            if re.search(regex, path):
                yield path


def guess_overwrite_paths():
    """Guess which partitions to overwrite (to hide deleted files)"""
    # In case overwriting leaves large files, placing them in
    # ~/.config makes it easy to find them and clean them.
    ret = []
    if 'posix' == os.name:
        home = os.path.expanduser('~/.cache')
        if not os.path.exists(home):
            home = os.path.expanduser("~")
        ret.append(home)
        if not same_partition(home, '/tmp/'):
            ret.append('/tmp')
    elif 'nt' == os.name:
        localtmp = os.path.expandvars('$TMP')
        if not os.path.exists(localtmp):
            logger.warning(
                _("The environment variable TMP refers to a directory that does not exist: %s"), localtmp)
            localtmp = None
        for drive in bleachbit.Windows.get_fixed_drives():
            if localtmp and same_partition(localtmp, drive):
                ret.append(localtmp)
            else:
                ret.append(drive)
    else:
        raise NotImplementedError('Unsupported OS in guess_overwrite_paths')
    return ret


def human_to_bytes(human, hformat='si'):
    """Convert a string like 10.2GB into bytes.  By
    default use SI standard (base 10).  The format of the
    GNU command 'du' (base 2) also supported."""

    if 'si' == hformat:
        base = 1000
        suffixes = 'kMGTE'
    elif 'du' == hformat:
        base = 1024
        suffixes = 'KMGTE'
    else:
        raise ValueError(f"Invalid format: '{hformat}'")
    matches = re.match(r'^(\d+(?:\.\d+)?) ?([' + suffixes + ']?)B?$', human)
    if matches is None:
        raise ValueError(f"Invalid input for '{human}' (hformat='{hformat}')")
    (amount, suffix) = matches.groups()

    if '' == suffix:
        exponent = 0
    else:
        exponent = suffixes.find(suffix) + 1
    return int(float(amount) * base**exponent)


def is_dir_empty(dirname):
    """Returns boolean whether directory is empty.

    It assumes the path exists and is a directory.
    """
    with os.scandir(dirname) as it:
        for _entry in it:
            return False
    return True


def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if isinstance(directory, tuple):
        for dirname in directory:
            yield from listdir(dirname)
        return
    dirname = os.path.expanduser(directory)
    if not os.path.lexists(dirname):
        return
    for filename in os.listdir(dirname):
        yield os.path.join(dirname, filename)


def same_partition(dir1, dir2):
    """Are both directories on the same partition?"""
    if 'nt' == os.name:
        try:
            return free_space(dir1) == free_space(dir2)
        except pywinerror as e:
            if 5 == e.winerror:
                # Microsoft Office 2010 Starter Edition has a virtual
                # drive that gives access denied
                # https://bugs.launchpad.net/bleachbit/+bug/1372179
                # https://bugs.launchpad.net/bleachbit/+bug/1474848
                # https://github.com/az0/bleachbit/issues/27
                return dir1[0] == dir2[0]
            raise
    # pylint: disable=no-member
    stat1 = os.statvfs(dir1)
    stat2 = os.statvfs(dir2)
    return stat1[stat.ST_DEV] == stat2[stat.ST_DEV]


def sync():
    """Flush file system buffers. sync() is different than fsync()"""
    if 'posix' == os.name:
        rc = ctypes.cdll.LoadLibrary('libc.so.6').sync()
        if 0 != rc:
            logger.error('sync() returned code %d', rc)
    elif 'nt' == os.name:
        # pylint: disable=protected-access
        ctypes.cdll.LoadLibrary('msvcrt.dll')._flushall()


def truncate_f(f):
    """Truncate the file object"""
    try:
        f.truncate(0)
        f.flush()
        os.fsync(f.fileno())
    except OSError as e:
        if e.errno != errno.ENOSPC:
            raise


def uris_to_paths(file_uris):
    """Return a list of paths from text/uri-list"""
    assert isinstance(file_uris, (tuple, list))
    file_paths = []
    for file_uri in file_uris:
        if not file_uri:
            # ignore blank
            continue
        parsed_uri = urllib.parse.urlparse(file_uri)
        if parsed_uri.scheme == 'file':
            file_path = urllib.request.url2pathname(parsed_uri.path)
            if file_path[2] == ':':
                # remove front slash for Windows-style path
                file_path = file_path[1:]
            file_paths.append(file_path)
        else:
            logger.warning('Unsupported scheme: %s', file_uri)
    return file_paths


def whitelisted_posix(path, check_realpath=True):
    """Check whether this POSIX path is whitelisted"""
    from bleachbit.Options import options
    if check_realpath and os.path.islink(path):
        # also check the link name
        if whitelisted_posix(path, False):
            return True
        # resolve symlink
        path = os.path.realpath(path)
    for pathname in options.get_whitelist_paths():
        if pathname[0] == 'file' and path == pathname[1]:
            return True
        if pathname[0] == 'folder':
            if path == pathname[1]:
                return True
            if path.startswith(pathname[1] + os.sep):
                return True
    return False


def whitelisted_windows(path):
    """Check whether this Windows path is whitelisted"""
    from bleachbit.Options import options
    for pathname in options.get_whitelist_paths():
        # Windows is case insensitive
        if pathname[0] == 'file' and path.lower() == pathname[1].lower():
            return True
        if pathname[0] == 'folder':
            if path.lower() == pathname[1].lower():
                return True
            if path.lower().startswith(pathname[1].lower() + os.sep):
                return True
            # Simple drive letter like C:\ matches everything below
            if len(pathname[1]) == 3 and path.lower().startswith(pathname[1].lower()):
                return True
    return False


if 'nt' == os.name:
    whitelisted = whitelisted_windows
else:
    whitelisted = whitelisted_posix


def wipe_contents(path, truncate=True):
    """Wipe files contents

    http://en.wikipedia.org/wiki/Data_remanence
    2006 NIST Special Publication 800-88 (p. 7): "Studies have
    shown that most of today's media can be effectively cleared
    by one overwrite"
    """

    def wipe_write():
        size = getsize(path)
        try:
            f = open(path, 'wb')
        except IOError as e:
            if e.errno == errno.EACCES:  # permission denied
                os.chmod(path, 0o200)  # user write only
                f = open(path, 'wb')
            else:
                raise
        blanks = b'\0' * 4096
        while size > 0:
            f.write(blanks)
            size -= 4096
        f.flush()  # flush to OS buffer
        os.fsync(f.fileno())  # force write to disk
        return f

    # pylint: disable=possibly-used-before-assignment
    if 'nt' == os.name and IsUserAnAdmin():
        # The import placement here avoids a circular import.
        # pylint: disable=import-outside-toplevel
        from bleachbit.WindowsWipe import file_wipe, UnsupportedFileSystemError
        try:
            file_wipe(path)
        except pywinerror as e:
            # 32=The process cannot access the file because it is being used by another process.
            # 33=The process cannot access the file because another process has
            # locked a portion of the file.
            if not e.winerror in (32, 33):
                # handle only locking errors
                raise
            # Try to truncate the file. This makes the behavior consistent
            # with Linux and with Windows when IsUserAdmin=False.
            try:
                with open(path, 'wb') as f:
                    truncate_f(f)
            except IOError as e2:
                if errno.EACCES == e2.errno:
                    # Common when the file is locked
                    # Errno 13 Permission Denied
                    pass
            # translate exception to mark file to deletion in Command.py
            raise WindowsError(e.winerror, e.strerror)
        except UnsupportedFileSystemError:
            warnings.warn(
                _('There was at least one file on a file system that does not support advanced overwriting.'), UserWarning)
            f = wipe_write()
        else:
            # The wipe succeed, so prepare to truncate.
            f = open(path, 'wb')
    else:
        f = wipe_write()
    if truncate:
        truncate_f(f)
    f.close()


def wipe_name(pathname1):
    """Wipe the original filename and return the new pathname"""
    (head, _tail) = os.path.split(pathname1)
    # reference http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
    maxlen = 226
    # first, rename to a long name
    i = 0
    while True:
        try:
            pathname2 = os.path.join(head, __random_string(maxlen))
            os.rename(pathname1, pathname2)
            break
        except OSError:
            if maxlen > 10:
                maxlen -= 10
            i += 1
            if i > 100:
                logger.info('exhausted long rename: %s', pathname1)
                pathname2 = pathname1
                break
    # finally, rename to a short name
    i = 0
    while True:
        try:
            pathname3 = os.path.join(head, __random_string(i + 1))
            os.rename(pathname2, pathname3)
            break
        except:
            i += 1
            if i > 100:
                logger.info('exhausted short rename: %s', pathname2)
                pathname3 = pathname2
                break
    return pathname3


def wipe_path(pathname, idle=False):
    """Wipe the free space in the path
    This function uses an iterator to update the GUI."""

    def temporaryfile():
        # reference
        # http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
        maxlen = 185
        f = None
        while True:
            try:
                f = tempfile.NamedTemporaryFile(
                    dir=pathname, suffix=__random_string(maxlen), delete=False)
                # In case the application closes prematurely, make sure this
                # file is deleted
                atexit.register(
                    delete, f.name, allow_shred=False, ignore_missing=True)
                break
            except OSError as e:
                if e.errno in (errno.ENAMETOOLONG, errno.ENOSPC, errno.ENOENT, errno.EINVAL):
                    # ext3 on Linux 3.5 returns ENOSPC if the full path is greater than 264.
                    # Shrinking the size helps.

                    # Microsoft Windows returns ENOENT "No such file or directory"
                    # or EINVAL "Invalid argument"
                    # when the path is too long such as %TEMP% but not in C:\
                    if maxlen > 5:
                        maxlen -= 5
                        continue
                raise
        return f

    def estimate_completion():
        """Return (percent, seconds) to complete"""
        remaining_bytes = free_space(pathname)
        done_bytes = start_free_bytes - remaining_bytes
        if done_bytes < 0:
            # maybe user deleted large file after starting wipe
            done_bytes = 0
        if 0 == start_free_bytes:
            done_percent = 0
        else:
            done_percent = 1.0 * done_bytes / (start_free_bytes + 1)
        done_time = time.time() - start_time
        rate = done_bytes / (done_time + 0.0001)  # bytes per second
        remaining_seconds = int(remaining_bytes / (rate + 0.0001))
        return 1, done_percent, remaining_seconds

    # Get the file system type from the given path
    fstype = get_filesystem_type(pathname)[0]
    logger.debug(_(f"Wiping path {pathname} with file system type {fstype}"))
    if not os.path.isdir(pathname):
        logger.error(
            _("Path to wipe must be an existing directory: %s"), pathname)
        return

    files = []
    total_bytes = 0
    start_free_bytes = free_space(pathname)
    start_time = time.time()
    done_wiping = False
    try:

        # Because FAT32 has a maximum file size of 4,294,967,295 bytes,
        # this loop is sometimes necessary to create multiple files.
        while True:
            try:
                logger.debug(
                    _('Creating new, temporary file for wiping free space.'))
                f = temporaryfile()
            except OSError as e:
                # Linux gives errno 24
                # Windows gives errno 28 No space left on device
                if e.errno in (errno.EMFILE, errno.ENOSPC):
                    break
                else:
                    raise

            # Remember to delete
            files.append(f)
            last_idle = time.time()
            # Write large blocks to quickly fill the disk.
            blanks = b'\0' * 65536
            writtensize = 0

            while True:

                try:
                    if fstype != 'vfat':
                        f.write(blanks)
                    # On Ubuntu, the size of file should be less than
                    # 4GB. If not, there should be EFBIG error, so the
                    # maximum file size should be less than or equal to
                    # "4GB - 65536byte".
                    elif writtensize < 4 * 1024 * 1024 * 1024 - 65536:
                        writtensize += f.write(blanks)
                    else:
                        break

                except IOError as e:
                    if e.errno == errno.ENOSPC:
                        if len(blanks) > 1:
                            # Try writing smaller blocks
                            blanks = blanks[0:len(blanks) // 2]
                        else:
                            break
                    elif e.errno == errno.EFBIG:
                        break
                    else:
                        raise
                if idle and (time.time() - last_idle) > 2:
                    # Keep the GUI responding, and allow the user to abort.
                    # Also display the ETA.
                    yield estimate_completion()
                    last_idle = time.time()
            # Write to OS buffer
            try:
                f.flush()
            except IOError as e:
                # IOError: [Errno 28] No space left on device
                # seen on Microsoft Windows XP SP3 with ~30GB free space but
                # not on another XP SP3 with 64MB free space
                if e.errno != errno.ENOSPC:
                    logger.error(
                        _("Error #%d when flushing the file buffer."), e.errno)

            os.fsync(f.fileno())  # write to disk
            # For statistics
            total_bytes += f.tell()
            # sync to disk
            sync()
            # statistics
            elapsed_sec = time.time() - start_time
            rate_mbs = (total_bytes / (1000 * 1000)) / elapsed_sec
            logger.debug(_('Wrote {files:,} files and {bytes:,} bytes in {seconds:,} seconds at {rate:.2f} MB/s').format(
                files=len(files), bytes=total_bytes, seconds=int(elapsed_sec), rate=rate_mbs))
            # how much free space is left (should be near zero)
            if 'posix' == os.name:
                # pylint: disable=no-member
                stats = os.statvfs(pathname)
                logger.debug(_("{bytes:,} bytes and {inodes:,} inodes available to non-super-user").format(
                    bytes=stats.f_bsize * stats.f_bavail, inodes=stats.f_favail))
                logger.debug(_("{bytes:,} bytes and {inodes:,} inodes available to super-user").format(
                    bytes=stats.f_bsize * stats.f_bfree, inodes=stats.f_ffree))
            # If no bytes were written to this file, then do not try to create another file.
            # Linux allows writing several 4K files when free_space() = 0,
            # so do not check free_space() < 1.
            # See
            #  * https://github.com/bleachbit/bleachbit/issues/502
            #    Replace `f.tell() < 2` with `len(blanks) < 2`
            #  * https://github.com/bleachbit/bleachbit/issues/1051
            #    Replace `len(blanks) < 2` with `estimated_free_space < 2`
            estimated_free_space = start_free_bytes - total_bytes
            if estimated_free_space < 2:
                logger.debug(
                    'Estimated free space %s is less than 2 bytes, breaking', estimated_free_space)
                break
        done_wiping = True
    finally:
        # Ensure files are closed and deleted even if an exception
        # occurs or generator is not fully consumed.
        # Truncate and close files.
        for f in files:
            if done_wiping:
                try:
                    truncate_f(f)
                except Exception as e:
                    logger.error(
                        'After wiping, truncating file %s failed: %s', f.name, e)

            while True:
                try:
                    # Nikita: I noticed a bug that prevented file handles from
                    # being closed on FAT32. It sometimes takes two .close() calls
                    # to do actually close (and therefore delete) a temporary file
                    f.close()
                    break
                except IOError as e:
                    if e.errno == 0:
                        logger.debug(
                            _("Handled unknown error #0 while truncating file."))
                    time.sleep(0.1)
            # explicitly delete
            try:
                delete(f.name, ignore_missing=True)
            except Exception as e:
                logger.error(
                    'After wiping, error deleting file %s: %s', f.name, e)


def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')


openfiles = OpenFiles()
