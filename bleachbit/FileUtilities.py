# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://www.bleachbit.org
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


import atexit
import codecs
import errno
import glob
import locale
import logging
import os
import random
import re
import stat
import string
import sys
import tempfile
import time
import ConfigParser
import Common

if 'nt' == os.name:
    import pywintypes
    import win32file

if 'posix' == os.name:
    from General import WindowsError


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
        for filename in glob.iglob("/proc/*/fd/*"):
            try:
                target = os.path.realpath(filename)
            except TypeError:
                # happens, for example, when link points to
                # '/etc/password\x00 (deleted)'
                continue
            if self.file_qualifies(target):
                self.files.append(target)

    def is_open(self, filename):
        """Return boolean whether filename is open by running process"""
        if None == self.last_scan_time or (time.time() -
                                           self.last_scan_time) > 10:
            self.scan()
        return filename in self.files


def __random_string(length):
    """Return random alphanumeric characters of given length"""
    return ''.join(random.choice(string.ascii_letters + '0123456789_.-')
                   for i in xrange(length))


def bytes_to_human(bytes_i):
    """Display a file size in human terms (megabytes, etc.) using preferred standard (SI or IEC)"""

    if bytes_i < 0:
        return '-' + bytes_to_human(-bytes_i)

    from Options import options
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
    for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def clean_ini(path, section, parameter):
    """Delete sections and parameters (aka option) in the file"""

    # read file to parser
    config = ConfigParser.RawConfigParser()
    fp = codecs.open(path, 'r', encoding='utf_8_sig')
    config.readfp(fp)

    # change file
    changed = False
    if config.has_section(section):
        if None == parameter:
            changed = True
            config.remove_section(section)
        elif config.has_option(section, parameter):
            changed = True
            config.remove_option(section, parameter)

    # write file
    if changed:
        from Options import options
        fp.close()
        if options.get('shred'):
            delete(path, True)
        fp = codecs.open(path, 'wb', encoding='utf_8')
        config.write(fp)


def clean_json(path, target):
    """Delete key in the JSON file"""
    try:
        import json
    except:
        import simplejson as json
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
        from Options import options
        if options.get('shred'):
            delete(path, True)
        # write file
        json.dump(js, open(path, 'w'))


def delete(path, shred=False, ignore_missing=False, allow_shred=True):
    """Delete path that is either file, directory, link or FIFO.

       If shred is enabled as a function parameter or the BleachBit global
       parameter, the path will be shredded unless allow_shred = False.
    """
    from Options import options
    logger = logging.getLogger(__name__)
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
        except OSError, e:
            # [Errno 39] Directory not empty
            # https://bugs.launchpad.net/bleachbit/+bug/1012930
            if errno.ENOTEMPTY == e.errno:
                logger.info("directory is not empty: %s", path)
            else:
                raise
        except WindowsError, e:
            # WindowsError: [Error 145] The directory is not empty:
            # 'C:\\Documents and Settings\\username\\Local Settings\\Temp\\NAILogs'
            # Error 145 may happen if the files are scheduled for deletion
            # during reboot.
            if 145 == e.winerror:
                logger.info("directory is not empty: %s", path)
            else:
                raise
    elif os.path.isfile(path):
        # wipe contents
        if allow_shred and (shred or options.get('shred')):
            try:
                wipe_contents(path)
            except IOError, e:
                # permission denied (13) happens shredding MSIE 8 on Windows 7
                logger.debug("IOError #%s shredding '%s'", e.errno, path)
            # wipe name
            os.remove(wipe_name(path))
        else:
            # unlink
            os.remove(path)
    else:
        logger.info("special file type cannot be deleted: %s", path)


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
    for cmd in cmds.split(';'):
        try:
            cursor.execute(cmd)
        except sqlite3.DatabaseError, exc:
            raise sqlite3.DatabaseError(
                '%s: %s' % (Common.decode_str(exc), path))
        except sqlite3.OperationalError, exc:
            logger = logging.getLogger(__name__)
            if exc.message.find('no such function: ') >= 0:
                # fixme: determine why randomblob and zeroblob are not
                # available
                logger.warning(exc.message)
            else:
                raise sqlite3.OperationalError(
                    '%s: %s' % (Common.decode_str(exc), path))
    cursor.close()
    conn.commit()
    conn.close()


def expand_glob_join(pathname1, pathname2):
    """Join pathname1 and pathname1, expand pathname, glob, and return as list"""
    ret = []
    pathname3 = os.path.expanduser(
        expandvars(os.path.join(pathname1, pathname2)))
    for pathname4 in glob.iglob(pathname3):
        ret.append(pathname4)
    return ret


def expandvars(path):
    if (2, 5) == sys.version_info[0:2] and 'nt' == os.name:
        # Python 2.5 should not change $foo when foo is unknown, but
        # it actually strips it out.
        import backport
        expandvars = backport.expandvars
        return backport.expandvars(path)
    else:
        expandvars = os.path.expandvars
        return os.path.expandvars(path)


def extended_path(path):
    """If applicable, return the extended Windows pathname"""
    if 'nt' == os.name:
        if path.startswith(r'\\?'):
            return path
        if path.startswith(r'\\'):
            return '\\\\?\\unc\\' + path[2:]
        return '\\\\?\\' + path
    return path


def free_space(pathname):
    """Return free space in bytes"""
    if 'nt' == os.name:
        _, _, free_bytes = win32file.GetDiskFreeSpaceEx(pathname)
        return free_bytes
    mystat = os.statvfs(pathname)
    return mystat.f_bfree * mystat.f_bsize


def getsize(path):
    """Return the actual file size considering spare files
       and symlinks"""
    if 'posix' == os.name:
        try:
            __stat = os.lstat(path)
        except OSError, e:
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
        if finddata == []:
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
        home = os.path.expanduser('~/.cache')
        if not os.path.exists(home):
            home = os.path.expanduser("~")
        ret.append(home)
        if not same_partition(home, '/tmp/'):
            ret.append('/tmp')
    elif 'nt' == os.name:
        localtmp = expandvars('$TMP')
        logger = logging.getLogger(__name__)
        if not os.path.exists(localtmp):
            logger.warning('%TMP% does not exist: %s', localtmp)
            localtmp = None
        else:
            from win32file import GetLongPathName
            localtmp = GetLongPathName(localtmp)
        from Windows import get_fixed_drives
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
        multiplier = {'B': 1, 'kB': 1000, 'MB': 1000 ** 2,
                      'GB': 1000 ** 3, 'TB': 1000 ** 4}
        matches = re.findall("^([0-9]*)(\.[0-9]{1,2})?([kMGT]{0,1}B)$", human)
    elif 'du' == hformat:
        multiplier = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2,
                      'GB': 1024 ** 3, 'TB': 1024 ** 4}
        matches = re.findall("^([0-9]*)(\.[0-9]{1,2})?([KMGT]{0,1}B)$", human)
    else:
        raise ValueError("Invalid format: '%s'" % hformat)
    if [] == matches or 2 > len(matches[0]):
        raise ValueError(
            "Invalid input for '%s' (hformat='%s')" % (human, hformat))
    return int(float(matches[0][0] + matches[0][1]) * multiplier[matches[0][2]])


def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if type(directory) is tuple:
        for dirname in directory:
            for pathname in listdir(dirname):
                yield pathname
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
        except pywintypes.error, e:
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
            logger = logging.getLogger(__name__)
            logge.error('sync() returned code %d' % rc)
    if 'nt' == os.name:
        import ctypes
        ctypes.cdll.LoadLibrary('msvcrt.dll')._flushall()


def whitelisted(path):
    """Check whether this path is whitelisted"""
    from Options import options
    for pathname in options.get_whitelist_paths():
        if pathname[0] == 'file' and path == pathname[1]:
            return True
        if pathname[0] == 'folder':
            if path == pathname[1]:
                return True
            if path.startswith(pathname[1] + os.sep):
                return True
        if 'nt' == os.name:
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
    size = getsize(path)
    try:
        f = open(path, 'wb')
    except IOError, e:
        if e.errno == errno.EACCES:  # permission denied
            os.chmod(path, 0200)  # user write only
            f = open(path, 'wb')
        else:
            raise
    blanks = chr(0) * 4096
    while size > 0:
        f.write(blanks)
        size -= 4096
    f.flush()  # flush to OS buffer
    os.fsync(f.fileno())  # force write to disk
    if truncate:
        f.truncate(0)
        f.flush()
        os.fsync(f.fileno())
    f.close()


def wipe_name(pathname1):
    """Wipe the original filename and return the new pathname"""
    logger = logging.getLogger(__name__)
    (head, _) = os.path.split(pathname1)
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
            i = i + 1
            if i > 100:
                logger.info('exhausted short rename: %s', pathname2)
                pathname3 = pathname2
                break
    return pathname3


def wipe_path(pathname, idle=False):
    """Wipe the free space in the path
    This function uses an iterator to update the GUI."""

    logger = logging.getLogger(__name__)

    def temporaryfile():
        # reference
        # http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
        maxlen = 245
        f = None
        while True:
            try:
                kwargs = {
                    'dir': pathname, 'suffix': __random_string(maxlen)}
                if sys.hexversion >= 0x02060000:
                    kwargs['delete'] = False
                f = tempfile.NamedTemporaryFile(**kwargs)
                # In case the application closes prematurely, make sure this
                # file is deleted
                atexit.register(
                    delete, f.name, allow_shred=False, ignore_missing=True)
                break
            except OSError, e:
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
        return (1, done_percent, remaining_seconds)

    logger.debug("wipe_path('%s')", pathname)
    files = []
    total_bytes = 0
    start_free_bytes = free_space(pathname)
    start_time = time.time()
    # Because FAT32 has a maximum file size of 4,294,967,295 bytes,
    # this loop is sometimes necessary to create multiple files.
    while True:
        try:
            logger.debug('creating new, temporary file to wipe path')
            f = temporaryfile()
        except OSError, e:
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
            except IOError, e:
                if e.errno == errno.ENOSPC:
                    if len(blanks) > 1:
                        # Try writing smaller blocks
                        blanks = blanks[0: (len(blanks) / 2)]
                    else:
                        break
                elif e.errno != errno.EFBIG:
                    raise
            if idle and (time.time() - last_idle) > 2:
                # Keep the GUI responding, and allow the user to abort.
                # Also display the ETA.
                yield estimate_completion()
                last_idle = time.time()
        # Write to OS buffer
        try:
            f.flush()
        except:
            # IOError: [Errno 28] No space left on device
            # seen on Microsoft Windows XP SP3 with ~30GB free space but
            # not on another XP SP3 with 64MB free space
            logger.info("info: exception on f.flush()")
        os.fsync(f.fileno())  # write to disk
        # Remember to delete
        files.append(f)
        # For statistics
        total_bytes += f.tell()
        # If no bytes were written, then quit
        if f.tell() < 1:
            break
    # sync to disk
    sync()
    # statistics
    elapsed_sec = time.time() - start_time
    rate_mbs = (total_bytes / (1000 * 1000)) / elapsed_sec
    logger.info('wrote %d files and %d bytes in %d seconds at %.2f MB/s',
                len(files), total_bytes, elapsed_sec, rate_mbs)
    # how much free space is left (should be near zero)
    if 'posix' == os.name:
        stats = os.statvfs(pathname)
        logger.info('%d bytes and %d inodes available to non-super-user',
                    stats.f_bsize * stats.f_bavail, stats.f_favail)
        logger.info('%d bytes and %d inodes available to super-user',
                    stats.f_bsize * stats.f_bfree, stats.f_ffree)
    # truncate and close files
    for f in files:
        f.truncate(0)

        while True:
            try:
                # Nikita: I noticed a bug that prevented file handles from
                # being closed on FAT32. It sometimes takes two .close() calls
                # to do actually close (and therefore delete) a temporary file
                f.close()
                break
            except IOError, e:
                if e.errno == 0:
                    logger.debug('handled unknown error 0')
                    time.sleep(0.1)
        # explicitly delete
        # Python 2.5.4 always deletes NamedTemporaryFile, so
        # ignore missing in older Python here.
        delete(f.name, ignore_missing=sys.hexversion < 0x02060000)


def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')


openfiles = OpenFiles()
