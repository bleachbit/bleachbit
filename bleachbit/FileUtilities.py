# -*- coding: future_fstrings -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
File-related utilities
"""

import atexit
import ctypes
import errno
import glob
import locale
import logging
import os
import os.path
import random
import re
import string
import sys
import tempfile
import time
import warnings
from ctypes import wintypes

# do not import psutil here in case of ImportError, like on Windows XP SP3.
import win32file
from pywintypes import error as pywinerror

import bleachbit
import bleachbit.Windows
from bleachbit import _

logger = logging.getLogger(__name__)

os_path_islink = os.path.islink
os.path.islink = lambda path: os_path_islink(
    path) or bleachbit.Windows.is_junction(path)

try:
    from scandir import walk
    import scandir

    class _Win32DirEntryPython(scandir.Win32DirEntryPython):
        def is_symlink(self):
            return super(_Win32DirEntryPython, self).is_symlink() or bleachbit.Windows.is_junction(self.path)

    scandir.scandir = scandir.scandir_python
    scandir.DirEntry = scandir.Win32DirEntryPython = _Win32DirEntryPython
except ImportError:
    if sys.version_info < (3, 5, 0):
        # Python 3.5 incorporated scandir
        logger.warning(
            'scandir is not available, so falling back to slower os.walk()')
    from os import walk


def get_filesystem_type(path):
    """
    * Get file system type from the given path
    * return value: The tuple of (file_system_type, device_name)
    *               @ file_system_type: vfat, ntfs, etc
    *               @ device_name:      C://, D://, etc
    """
    try:
        import psutil
    except ImportError:
        logger.warning(
            'To get the file system type from the given path, you need to install psutil package')
        return ("unknown", "none")

    partitions = {
        partition.mountpoint: (partition.fstype, partition.device)
        for partition in psutil.disk_partitions()
    }

    if path in partitions:
        return partitions[path]

    splitpath = path.split(os.sep)
    for i in range(0, len(splitpath)-1):
        path = os.sep.join(splitpath[:i]) + os.sep
        if path in partitions:
            return partitions[path]

        path = os.sep.join(splitpath[:i])
        if path in partitions:
            return partitions[path]

    return ("unknown", "none")


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

    assert(isinstance(bytes_i, int))

    if 0 == bytes_i:
        return '0B'

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
            yield from children_in_directory(top_, list_directories)
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
            ini_file.write("[DEFAULT]\n")
            for (key, value) in parser._defaults.items():
                str_value = str(value).replace('\n', '\n\t')
                ini_file.write(f"{key} = {str_value}\n")
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
    config = bleachbit.RawConfigParser()
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
    import json
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
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(js, f)


def delete(path, shred=False, ignore_missing=False, allow_shred=True):
    """Delete path that is either file, directory, link or FIFO.

       If shred is enabled as a function parameter or the BleachBit global
       parameter, the path will be shredded unless allow_shred = False.
    """
    from bleachbit.Options import options
    path = extended_path(path)
    do_shred = allow_shred and (shred or options.get('shred'))
    if not os.path.lexists(path):
        if ignore_missing:
            return
        raise OSError(2, 'No such file or directory', path)
    if os.path.isdir(path):
        delpath = path
        if do_shred:
            if not is_dir_empty(path):
                # Avoid renaming non-empty directory like https://github.com/bleachbit/bleachbit/issues/783
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
            except pywinerror as e:
                # 2 = The system cannot find the file specified.
                # This can happen with a broken symlink
                # https://github.com/bleachbit/bleachbit/issues/195
                if 2 != e.winerror:
                    raise
                # If a broken symlink, try os.remove() below.
            except IOError as e:
                # Locked files must propagate so Command.Delete can mark
                # them for deletion on reboot.
                if getattr(e, 'winerror', None) in (32, 33):
                    raise
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
        import chardet
    except ImportError:
        logger.warning(
            'chardet module is not available to detect character encoding')
        return None

    with open(fn, 'rb') as f:
        if not hasattr(chardet, 'universaldetector'):
            # This method works on Ubuntu 16.04 with an older version of the module.
            rawdata = f.read()
            det = chardet.detect(rawdata)
            if det['confidence'] > 0.5:
                return det['encoding']
            return None

        # This method is faster, but it requires a newer version of the module.
        detector = chardet.universaldetector.UniversalDetector()
        for line in f.readlines():
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result['encoding']


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    delimiter = ';'
    path_env = os.getenv('PATH')
    if path_env is None:
        return False
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
    """Execute 'cmds' on SQLite database 'path'"""
    import sqlite3
    import contextlib
    with contextlib.closing(sqlite3.connect(path)) as conn:
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
                if str(exc).find('no such function: ') >= 0:
                    # fixme: determine why randomblob and zeroblob are not
                    # available
                    logger.exception('SQLite function not available')
                else:
                    raise sqlite3.OperationalError(
                        f'{exc}: {path}')
            except sqlite3.DatabaseError as exc:
                raise sqlite3.DatabaseError(
                    f'{exc}: {path}')

        cursor.close()
        conn.commit()


def expand_glob_join(pathname1, pathname2):
    """Join pathname1 and pathname1, expand pathname, glob, and return as list"""
    pathname3 = os.path.expanduser(os.path.expandvars(
        os.path.join(pathname1, pathname2)))
    ret = [pathname4 for pathname4 in glob.iglob(pathname3)]
    return ret


def extended_path(path):
    """Return the extended Windows pathname"""
    # Do not extend the Sysnative paths because on some systems there are problems with path resolution,
    # for example: https://github.com/bleachbit/bleachbit/issues/1574.
    if 'Sysnative' not in path.split(os.sep):
        if path.startswith(r'\\?'):
            return path
        if path.startswith(r'\\'):
            return '\\\\?\\unc\\' + path[2:]
        return '\\\\?\\' + path
    return path


def extended_path_undo(path):
    """"""
    if path.startswith(r'\\?\unc'):
        return '\\' + path[7:]
    if path.startswith(r'\\?'):
        return path[4:]
    return path


def free_space(pathname):
    """Return free space in bytes"""
    try:
        import psutil
    except ImportError:
        free_bytes = wintypes.ULARGE_INTEGER()
        ret = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            pathname,
            ctypes.byref(free_bytes),
            None,
            None)
        if 0 == ret:
            raise ctypes.WinError(ctypes.get_last_error())
        return free_bytes.value
    else:
        return psutil.disk_usage(pathname).free


def getsize(path):
    """Return the actual file size considering spare files
       and symlinks"""
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


def getsizedir(path):
    """Return the size of the contents of a directory"""
    total_bytes = sum(
        getsize(node)
        for node in children_in_directory(path, list_directories=False)
    )
    return total_bytes


def globex(pathname, regex):
    """Yield a list of files with pathname and filter by regex"""
    if type(pathname) is tuple:
        for singleglob in pathname:
            yield from globex(singleglob, regex)
    else:
        for path in glob.iglob(pathname):
            if re.search(regex, path):
                yield path


def guess_overwrite_paths():
    """Guess which partitions to overwrite (to hide deleted files)

    This returns at most one path per partition.

    Minimally, this returns the user's temporary directory (if it
    exists).

    If there are eligible paths, this returns an empty list.
    """
    ret = []
    localtmp = os.path.expandvars('$TMP')
    if localtmp and not os.path.exists(localtmp):
        logger.warning(
            _("The environment variable TMP refers to a directory that does not exist: %s"), localtmp)
        localtmp = None
    try:
        from bleachbit.Windows import get_fixed_drives
    except Exception:
        logger.exception('get_fixed_drives() failed')
        if localtmp:
            return [localtmp]
        return []
    for drive in get_fixed_drives():
        # $TMP is not defined, so no need to compare to drive.
        if not localtmp:
            ret.append(drive)
            continue
        try:
            is_same_partition = same_partition(localtmp, drive)
        except Exception:
            logger.exception(
                "Error in same_partition(%s, %s)", localtmp, drive)
            continue
        if is_same_partition:
            ret.append(localtmp)
        else:
            ret.append(drive)
    if not ret and localtmp:
        return [localtmp]
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
    if hasattr(os, 'scandir'):
        if sys.version_info < (3, 6, 0):
                    # Python 3.5 added os.scandir() without context manager.
            for _i in os.scandir(dirname):
                return False
        else:
            # Python 3.6 added the context manager.
            with os.scandir(dirname) as it:
                for _entry in it:
                    return False
        return True
    # This method is slower, but it works with Python 3.4.
    return len(os.listdir(dirname)) == 0


def is_normal_directory(path):
    """Check whether path is a non-link directory

    Returns False if:
        - path does not exist
        - path is a file
        - path is a reparse point (junction, symlink)
    Returns True if a normal directory
    """

    if not os.path.isdir(path):
        return False
    # On Windows, use GetFileAttributesW to check for reparse point
    # because os.stat().st_reparse_tag is not available in Python 3.4.
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    from ctypes import windll
    attr = windll.kernel32.GetFileAttributesW(path)
    if attr == 0xFFFFFFFF:
        return False
    return not bool(attr & FILE_ATTRIBUTE_REPARSE_POINT)


def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if type(directory) is tuple:
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
    try:
        return free_space(dir1) == free_space(dir2)
    except OSError as e:
        # 5 = access denied: Microsoft Office 2010 Starter Edition has a
        #     virtual drive that gives access denied.
        #     https://bugs.launchpad.net/bleachbit/+bug/1372179
        #     https://bugs.launchpad.net/bleachbit/+bug/1474848
        #     https://github.com/az0/bleachbit/issues/27
        # 1326 = logon failure: disconnected network drive.
        if getattr(e, 'winerror', None) in (5, 1326):
            return dir1[0] == dir2[0]
        raise


def sync():
    """Flush file system buffers. sync() is different than fsync()"""
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
    import urllib.parse
    import urllib.request
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


def whitelisted(path):
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

    from win32com.shell.shell import IsUserAnAdmin

    if IsUserAnAdmin():
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
                with open(path, 'w') as f:
                    truncate_f(f)
            except IOError as e2:
                if errno.EACCES == e2.errno:
                    # Common when the file is locked
                    # Errno 13 Permission Denied
                    pass
            # translate exception to mark file to deletion in Command.py
            raise OSError(0, e.strerror, path, e.winerror)
        except UnsupportedFileSystemError:
            warnings.warn(
                _('There was at least one file on a file system that does not support advanced overwriting.'), UserWarning)
            f = wipe_write()
        else:
            # The wipe succeed, so prepare to truncate.
            f = open(path, 'w')
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

    logger.debug(_("Wiping path: %s"), pathname)
    if not os.path.isdir(pathname):
        logger.error(_("Path to wipe must be an existing directory: %s"), pathname)
        return
    files = []
    total_bytes = 0
    start_free_bytes = free_space(pathname)
    start_time = time.time()
    try:
        # Because FAT32 has a maximum file size of 4,294,967,295 bytes,
        # this loop is sometimes necessary to create multiple files.
        while True:
            try:
                logger.debug(
                    _('Creating new, temporary file for wiping free space.'))
                f = temporaryfile()
                files.append(f)
            except OSError as e:
                # Windows gives errno 28 No space left on device
                if e.errno in (errno.EMFILE, errno.ENOSPC):
                    break
                else:
                    raise

            # Get the file system type from the given path
            fstype = get_filesystem_type(pathname)
            fstype = fstype[0]
            logging.debug('File System: %s', fstype)
            # print(f.name) # Added by Marvin for debugging #issue 1051
            last_idle = time.time()
            # Write large blocks to quickly fill the disk.
            blanks = b'\0' * 65536
            writtensize = 0

            while True:
                try:
                    if fstype != 'vfat':
                        f.write(blanks)
                    # In the ubuntu system, the size of file should be less then 4GB. If not, there should be EFBIG error.
                    # So the maximum file size should be less than or equal to "4GB - 65536byte".
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
                if not e.errno == errno.ENOSPC:
                    logger.error(
                        _("Error #%d when flushing the file buffer."), e.errno)

            os.fsync(f.fileno())  # write to disk
            # For statistics
            total_bytes += f.tell()
            # If no bytes were written, then quit.
            # See https://github.com/bleachbit/bleachbit/issues/502
            if start_free_bytes - total_bytes < 2: # Modified by Marvin to fix the issue #1051 [12/06/2020]
                break
        # sync to disk
        sync()
        # statistics
        elapsed_sec = time.time() - start_time
        rate_mbs = (total_bytes / (1000 * 1000)) / elapsed_sec
        logger.info(_('Wrote {files:,} files and {bytes:,} bytes in {seconds:,} seconds at {rate:.2f} MB/s').format(
                    files=len(files), bytes=total_bytes, seconds=int(elapsed_sec), rate=rate_mbs))
    finally:
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
                        logger.debug(
                            _("Handled unknown error #0 while truncating file."))
                        time.sleep(0.1)
            # explicitly delete
            delete(f.name, ignore_missing=True)


def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')
