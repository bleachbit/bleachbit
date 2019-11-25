# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2019 Andrew Ziem
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
from __future__ import absolute_import

import bleachbit
from bleachbit import expanduser, _

import atexit
import codecs
import errno
import glob
import locale
import logging
import os, os.path
import random
import re
import stat
import string
import sys
import subprocess
import tempfile
import time

logger = logging.getLogger(__name__)

if 'nt' == os.name:
    from pywintypes import error as pywinerror
    import win32file
    import bleachbit.Windows
    os_path_islink = os.path.islink
    os.path.islink = lambda path: os_path_islink(path) or bleachbit.Windows.is_junction(path)

if 'posix' == os.name:
    from bleachbit.General import WindowsError
    pywinerror = WindowsError

try:
    from scandir import walk
    if 'nt' == os.name:
        import scandir
        import bleachbit.Windows

        class _Win32DirEntryPython(scandir.Win32DirEntryPython):
            def is_symlink(self):
                return super(_Win32DirEntryPython, self).is_symlink() or bleachbit.Windows.is_junction(self.path)

        scandir.scandir = scandir.scandir_python
        scandir.DirEntry = scandir.Win32DirEntryPython = _Win32DirEntryPython
except ImportError:
    logger.warning('scandir is not available, so falling back to slower os.walk()')
    from os import walk


def open_files_linux():
    return glob.iglob("/proc/*/fd/*")


def open_files_lsof(run_lsof=None):
    if run_lsof is None:
        def run_lsof():
            return subprocess.check_output(["lsof", "-Fn", "-n"])
    for f in run_lsof().split("\n"):
        if f.startswith("n/"):
            yield f[1:]  # Drop lsof's "n"


def open_files():
    if sys.platform.startswith('linux'):
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

    assert(isinstance(bytes_i, (int, long)))

    if 0 == bytes_i:
        return "0"

    if bytes_i >= base ** 3:
        decimals = 2
    elif bytes_i >= base:
        decimals = 1
    else:
        decimals = 0

    for exponent in range(0, len(prefixes)):
        if bytes_i < base:
            abbrev = round(bytes_i, decimals)
            suf = prefixes[exponent]
            return locale.str(abbrev) + suf + 'B'
        else:
            bytes_i /= base
    return 'A lot.'


def children_in_directory(top, list_directories=False):
    """Iterate files and, optionally, subdirectories in directory"""
    if type(top) is tuple:
        for top_ in top:
            for pathname in children_in_directory(top_, list_directories):
                yield pathname
        return
    for (dirpath, dirnames, filenames) in walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def clean_ini(path, section, parameter):
    """Delete sections and parameters (aka option) in the file"""

    def write(parser, ini_file):
        """
        Reimplementation of the original RowConfigParser write function.

        This function is 99% same as its origin. The only change is
        removing a cast to str. This is needed to handle unicode chars.
        """
        if parser._defaults:
            ini_file.write("[%s]\n" % "DEFAULT")
            for (key, value) in parser._defaults.items():
                ini_file.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            ini_file.write("\n")
        for section in parser._sections:
            ini_file.write("[%s]\n" % section)
            for (key, value) in parser._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (parser._optcre == parser.OPTCRE):
                    # The line bellow is the only changed line of the original function.
                    # This is the orignal line for reference:
                    # key = " = ".join((key, str(value).replace('\n', '\n\t')))
                    key = " = ".join((key, value.replace('\n', '\n\t')))
                ini_file.write("%s\n" % (key))
            ini_file.write("\n")

    try:
        import chardet

    except ImportError:
        has_chardet = False
        logger.warning('chardet is not available, so falling to utf-8 encoding')

    else:
        has_chardet = True
        # detect .ini file encoding
        with open(path) as file_:
            detector = chardet.universaldetector.UniversalDetector()
            for line in file_.readlines():
                detector.feed(line)
                if detector.done: break
            detector.close()

    # read file to parser
    config = bleachbit.RawConfigParser()
    config.write = write
    fp = codecs.open(path, 'r', encoding=detector.result['encoding'] if has_chardet else 'utf_8_sig')
    config.readfp(fp)

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
        fp = codecs.open(path, 'wb', encoding=detector.result['encoding'] if has_chardet else 'utf_8')
        config.write(config, fp)


def clean_json(path, target):
    """Delete key in the JSON file"""
    import json
    changed = False
    targets = target.split('/')

    # read file to parser
    js = json.load(open(path, 'r'))

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
            del(pos[new_target])
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
        json.dump(js, open(path, 'w'))


def delete(path, shred=False, ignore_missing=False, allow_shred=True):
    """Delete path that is either file, directory, link or FIFO.

       If shred is enabled as a function parameter or the BleachBit global
       parameter, the path will be shredded unless allow_shred = False.
    """
    from bleachbit.Options import options
    is_special = False
    path = extended_path(path)
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
        if allow_shred and (shred or options.get('shred')):
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
        if allow_shred and (shred or options.get('shred')):
            try:
                wipe_contents(path)
            except pywinerror as e:
                # 2 = The system cannot find the file specified.
                # This can happen with a broken symlink
                # https://github.com/bleachbit/bleachbit/issues/195
                if 2 != e.winerror:
                    raise
                # If a broken symlink, try os.remove() below.
            except IOError as e:
                # permission denied (13) happens shredding MSIE 8 on Windows 7
                logger.debug("IOError #%s shredding '%s'", e.errno, path, exc_info=True)
            # wipe name
            os.remove(wipe_name(path))
        else:
            # unlink
            os.remove(path)
    else:
        logger.info(_("Special file type cannot be deleted: %s"), path)


def ego_owner(filename):
    """Return whether current user owns the file"""
    return os.lstat(filename).st_uid == os.getuid()


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    delimiter = ':'
    if 'nt' == os.name:
        delimiter = ';'
    for dirname in os.getenv('PATH').split(delimiter):
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
    """Execute 'cmds' on SQLite database 'path'"""
    import sqlite3
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # overwrites deleted content with zeros
    # https://www.sqlite.org/pragma.html#pragma_secure_delete
    from bleachbit.Options import options
    if options.get('shred'):
        cursor.execute('PRAGMA secure_delete=ON')

    for cmd in cmds.split(';'):
        try:
            cursor.execute(cmd)
        except sqlite3.OperationalError as exc:
            if exc.message.find('no such function: ') >= 0:
                # fixme: determine why randomblob and zeroblob are not
                # available
                logger.exception(exc.message)
            else:
                raise sqlite3.OperationalError(
                    '%s: %s' % (bleachbit.decode_str(exc), path))
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                '%s: %s' % (bleachbit.decode_str(exc), path))
    cursor.close()
    conn.commit()
    conn.close()


def expand_glob_join(pathname1, pathname2):
    """Join pathname1 and pathname1, expand pathname, glob, and return as list"""
    ret = []
    pathname3 = expanduser(bleachbit.expandvars(os.path.join(pathname1, pathname2)))
    for pathname4 in glob.iglob(pathname3):
        ret.append(pathname4)
    return ret


def expandvars(path):
    return bleachbit.expandvars(path)


def extended_path(path):
    """If applicable, return the extended Windows pathname"""
    if 'nt' == os.name:
        if path.startswith(r'\\?'):
            return path
        if path.startswith(r'\\'):
            return '\\\\?\\unc\\' + path[2:]
        return '\\\\?\\' + path
    return path


def extended_path_undo(path):
    """"""
    if 'nt' == os.name:
        if path.startswith(r'\\?\unc'):
            return '\\' + path[7:]
        if path.startswith(r'\\?'):
            return path[4:]
    return path


def free_space(pathname):
    """Return free space in bytes"""
    if 'nt' == os.name:
        from bleachbit import Windows
        if Windows.parse_windows_build() >= 6:
            # This works better with UTF-8 paths.
            import psutil
            return psutil.disk_usage(pathname).free
        else:
            # This works better with Windows XP but not UTF-8.
            # Deprecated.
            _fb, _tb, total_free_bytes = win32file.GetDiskFreeSpaceEx(pathname)
            return total_free_bytes
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
        finddata = win32file.FindFilesW(extended_path(path))
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
    total_bytes = 0
    for node in children_in_directory(path, list_directories=False):
        total_bytes += getsize(node)
    return total_bytes


def globex(pathname, regex):
    """Yield a list of files with pathname and filter by regex"""
    if type(pathname) is tuple:
        for singleglob in pathname:
            for path in globex(singleglob, regex):
                yield path
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
        home = expanduser('~/.cache')
        if not os.path.exists(home):
            home = expanduser("~")
        ret.append(home)
        if not same_partition(home, '/tmp/'):
            ret.append('/tmp')
    elif 'nt' == os.name:
        localtmp = bleachbit.expandvars('$TMP')
        if not os.path.exists(localtmp):
            logger.warning(_("%TMP% does not exist: %s"), localtmp)
            localtmp = None
        from bleachbit.Windows import get_fixed_drives
        for drive in get_fixed_drives():
            if localtmp and same_partition(localtmp, drive):
                ret.append(localtmp)
            else:
                ret.append(drive)
    else:
        NotImplementedError('Unsupported OS in guess_overwrite_paths')
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
        raise ValueError("Invalid format: '%s'" % hformat)
    matches = re.match(r'^(\d+(?:\.\d+)?) ?([' + suffixes + ']?)B?$', human)
    if matches is None:
        raise ValueError("Invalid input for '%s' (hformat='%s')" % (human, hformat))
    (amount, suffix) = matches.groups()

    if '' == suffix:
        exponent = 0
    else:
        exponent = suffixes.find(suffix) + 1
    return int(float(amount) * base**exponent)


def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if type(directory) is tuple:
        for dirname in directory:
            for pathname in listdir(dirname):
                yield pathname
        return
    dirname = expanduser(directory)
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
    stat1 = os.statvfs(dir1)
    stat2 = os.statvfs(dir2)
    return stat1[stat.ST_DEV] == stat2[stat.ST_DEV]


def sync():
    """Flush file system buffers. sync() is different than fsync()"""
    if 'posix' == os.name:
        import ctypes
        rc = ctypes.cdll.LoadLibrary('libc.so.6').sync()
        if 0 != rc:
            logger.error('sync() returned code %d', rc)
    if 'nt' == os.name:
        import ctypes
        ctypes.cdll.LoadLibrary('msvcrt.dll')._flushall()


def truncate_f(f):
    """Truncate the file object"""
    f.truncate(0)
    f.flush()
    os.fsync(f.fileno())


def uris_to_paths(file_uris):
    """Return a list of paths from text/uri-list"""
    import urlparse
    import urllib
    assert isinstance(file_uris, (tuple, list))
    file_paths = []
    for file_uri in file_uris:
        if not file_uri:
            # ignore blank
            continue
        parsed_uri = urlparse.urlparse(file_uri)
        if parsed_uri.scheme == 'file':
            file_path = urllib.url2pathname(parsed_uri.path)
            if file_path[2] == ':':
                # remove front slash for Windows-style path
                file_path = file_path[1:]
            file_path_unicode = file_path.decode("utf-8")
            file_paths.append(file_path_unicode)
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
        blanks = chr(0) * 4096
        while size > 0:
            f.write(blanks)
            size -= 4096
        f.flush()  # flush to OS buffer
        os.fsync(f.fileno())  # force write to disk
        return f

    if 'nt' == os.name:
        from win32com.shell.shell import IsUserAnAdmin

    if 'nt' == os.name and IsUserAnAdmin():
        from bleachbit.WindowsWipe import file_wipe, UnsupportedFileSystemError
        import warnings
        from bleachbit import _
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
        except UnsupportedFileSystemError as e:
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
            os.rename(pathname1,  pathname2)
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
        maxlen = 245
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
                if e.errno in (errno.ENAMETOOLONG, errno.ENOSPC, errno.ENOENT):
                    # ext3 on Linux 3.5 returns ENOSPC if the full path is greater than 264.
                    # Shrinking the size helps.

                    # Microsoft Windows returns ENOENT "No such file or directory"
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

    logger.debug(_("Wiping path: %s") % pathname)
    files = []
    total_bytes = 0
    start_free_bytes = free_space(pathname)
    start_time = time.time()
    # Because FAT32 has a maximum file size of 4,294,967,295 bytes,
    # this loop is sometimes necessary to create multiple files.
    while True:
        try:
            logger.debug(_('Creating new, temporary file for wiping free space.'))
            f = temporaryfile()
        except OSError as e:
            # Linux gives errno 24
            # Windows gives errno 28 No space left on device
            if e.errno in (errno.EMFILE, errno.ENOSPC):
                break
            else:
                raise
        last_idle = time.time()
        # Write large blocks to quickly fill the disk.
        blanks = chr(0) * 65535
        while True:
            try:
                f.write(blanks)
            except IOError as e:
                if e.errno == errno.ENOSPC:
                    if len(blanks) > 1:
                        # Try writing smaller blocks
                        blanks = blanks[0: (len(blanks) / 2)]
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
            if not e.errno == errno.ENOSPC:
                logger.error(_("Error #%d when flushing the file buffer." % e.errno))

        os.fsync(f.fileno())  # write to disk
        # Remember to delete
        files.append(f)
        # For statistics
        total_bytes += f.tell()
        # If no bytes were written, then quit.
        # See https://github.com/bleachbit/bleachbit/issues/502
        if f.tell() < 2:
            break
    # sync to disk
    sync()
    # statistics
    elapsed_sec = time.time() - start_time
    rate_mbs = (total_bytes / (1000 * 1000)) / elapsed_sec
    logger.info(_('Wrote {files:,} files and {bytes:,} bytes in {seconds:,} seconds at {rate:.2f} MB/s').format(
                files=len(files), bytes=total_bytes, seconds=int(elapsed_sec), rate=rate_mbs))
    # how much free space is left (should be near zero)
    if 'posix' == os.name:
        stats = os.statvfs(pathname)
        logger.info(_("{bytes:,} bytes and {inodes:,} inodes available to non-super-user").format(
                    bytes=stats.f_bsize * stats.f_bavail, inodes=stats.f_favail))
        logger.info(_("{bytes:,} bytes and {inodes:,} inodes available to super-user").format(
                    bytes=stats.f_bsize * stats.f_bfree, inodes=stats.f_ffree))
    # truncate and close files
    for f in files:
        truncate_f(f)

        while True:
            try:
                # Nikita: I noticed a bug that prevented file handles from
                # being closed on FAT32. It sometimes takes two .close() calls
                # to do actually close (and therefore delete) a temporary file
                f.close()
                break
            except IOError as e:
                if e.errno == 0:
                    logger.debug(_("Handled unknown error #0 while truncating file."))
                    time.sleep(0.1)
        # explicitly delete
        delete(f.name, ignore_missing=True)


def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')


openfiles = OpenFiles()
