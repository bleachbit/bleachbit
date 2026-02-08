# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
File wiping
"""

import atexit
import ctypes
import errno
import os
import random
import string
import struct
import tempfile
import time
import warnings
import logging

from bleachbit.Language import get_text as _

if 'nt' == os.name:
    # pylint: disable=import-error
    from win32com.shell.shell import IsUserAnAdmin

if 'posix' == os.name:
    import fcntl

logger = logging.getLogger(__name__)


def __random_string(length):
    """Return random alphanumeric characters of given length"""
    return ''.join(random.choice(string.ascii_letters + '0123456789_.-')
                   for i in range(length))


def detect_orphaned_wipe_files():
    """Detect orphaned temporary files from interrupted wipe_path operations.

    These files are created by wipe_path() to fill free disk space with zeros.

    Detection criteria:
    - Located in directories from options shred_drives
    - Filename starts with 'empty_'
    - Filename has >100 characters (due to random suffix)
    - No file extension
    - Contains only null bytes when sampled

    Returns:
        list: Paths to detected orphaned wipe files
    """
    from bleachbit.Options import options
    orphaned_files = []

    shred_drives = options.get_list('shred_drives')
    if not shred_drives:
        return orphaned_files

    for drive_path in shred_drives:
        if not os.path.isdir(drive_path):
            continue
        try:
            for entry in os.scandir(drive_path):
                if not entry.is_file():
                    continue
                filename = entry.name
                # Check criteria: starts with 'empty_', >100 chars, no extension
                if not filename.startswith('empty_'):
                    continue
                if len(filename) <= 100:
                    continue
                if '.' in filename:
                    continue
                # Read a small sample to check for null bytes
                try:
                    with open(entry.path, 'rb') as f:
                        sample = f.read(4096)
                        if sample and all(b == 0 for b in sample):
                            orphaned_files.append(entry.path)
                except (IOError, OSError) as e:
                    logger.debug('Could not read file %s: %s', entry.path, e)
        except (IOError, OSError) as e:
            logger.debug('Could not scan directory %s: %s', drive_path, e)

    return orphaned_files


def fitrim(pathname):
    """Perform FITRIM (fstrim) to discard unused blocks on a supported filesystem

    pathname: path to directory
    """
    if os.name != 'posix':
        return False

    fitrim_id = 0xC0185879
    try:

        try:
            # Open the directory
            fd = os.open(pathname, os.O_RDONLY)
            # Get filesystem stats to determine range
            stats = os.statvfs(pathname)

            # struct fstrim_range {
            #     __u64 start;
            #     __u64 len;
            #     __u64 minlen;
            # };
            # Set range to the entire filesystem
            trim_range = struct.pack(
                'QQQ', 0, stats.f_blocks * stats.f_bsize, 0)
            fcntl.ioctl(fd, fitrim_id, trim_range)
            logger.debug(
                "Successfully performed FITRIM on filesystem at %s", pathname)
            return True
        finally:
            os.close(fd)
    except Exception as e:
        if os.geteuid() == 0:
            logger.info("FITRIM failed: %s", e)
        else:
            logger.debug("FITRIM failed: %s", e)
        return False


def sync():
    """Flush file system buffers. sync() is different than fsync()"""
    if 'posix' == os.name:
        rc = ctypes.cdll.LoadLibrary('libc.so.6').sync()
        if 0 != rc:
            logger.error('sync() returned code %d', rc)
    elif 'nt' == os.name:
        # pylint: disable=protected-access
        ctypes.cdll.LoadLibrary('msvcrt.dll')._flushall()


def wipe_contents(path, truncate=True):
    """Wipe files contents

    http://en.wikipedia.org/wiki/Data_remanence
    2006 NIST Special Publication 800-88 (p. 7): "Studies have
    shown that most of today's media can be effectively cleared
    by one overwrite"
    """
    # pylint: disable=import-outside-toplevel
    from bleachbit.FileUtilities import getsize, truncate_f

    def wipe_write():
        from bleachbit.FileUtilities import getsize as _getsize
        size = _getsize(path)
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
        from bleachbit.FileUtilities import pywinerror
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
    # pylint: disable=import-outside-toplevel
    from bleachbit.FileUtilities import delete, free_space, get_filesystem_type, truncate_f

    def temporaryfile():
        # reference
        # http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
        maxlen = 185
        f = None
        while True:
            try:
                f = tempfile.NamedTemporaryFile(
                    dir=pathname,
                    suffix=__random_string(maxlen),
                    delete=False,
                    prefix="empty_"
                )
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

    if fstype in ('ext4', 'btrfs'):
        fitrim(pathname)

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
