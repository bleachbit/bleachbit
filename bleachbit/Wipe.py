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
import secrets
import string
import struct
import tempfile
import time
import warnings
import logging

import bleachbit
from bleachbit import IS_LINUX, IS_MAC, IS_POSIX, IS_WINDOWS
from bleachbit.Language import get_text as _

if IS_WINDOWS:
    # pylint: disable=import-error
    from win32com.shell.shell import IsUserAnAdmin

if IS_POSIX:
    import fcntl

logger = logging.getLogger(__name__)

FILENAME_CHARS = string.ascii_lowercase + \
    string.digits + '_.-+~!@#$%^&()=[]{},'
if bleachbit.FS_CASE_SENSITIVE:
    FILENAME_CHARS += string.ascii_uppercase

WINDOWS_RESERVED_FILENAMES = {
    'CON',
    'PRN',
    'AUX',
    'NUL',
    'CONIN$',
    'CONOUT$',
}
WINDOWS_RESERVED_FILENAMES.update(
    {'COM%d' % number for number in range(1, 10)})
WINDOWS_RESERVED_FILENAMES.update(
    {'LPT%d' % number for number in range(1, 10)})


def __random_string(length):
    """Return random alphanumeric characters of given length"""
    return ''.join(secrets.choice(FILENAME_CHARS)
                   for i in range(length))


def __valid_random_filename(filename):
    """Check if a filename is valid for use as a temporary file.

    This function is intended for limited scope for use with
    __random_string(), so this function assumes

        - Input characters are limited to FILENAME_CHARS.
        - No null bytes, path separators, or low ASCII characters.
        - The argument is a filename (not a path).

    On Windows, this checks for invalid characters, reserved names, and other
    restrictions.
    """
    if not filename:
        return False
    if filename in ('.', '..'):
        return False
    if not IS_WINDOWS:
        return True
    if filename.endswith((' ', '.')):
        return False
    # After updating to Python 3.13, use os.path.isreserved() here.
    if filename.rstrip(' .').split('.', 1)[0].upper() in WINDOWS_RESERVED_FILENAMES:
        return False
    if set(filename) & set('<>:"/\\|?*'):
        return False
    return True


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
    if not IS_POSIX:
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
    if IS_LINUX:
        rc = ctypes.cdll.LoadLibrary('libc.so.6').sync()
        if 0 != rc:
            logger.error('sync() returned code %d', rc)
    elif IS_MAC:
        # On macOS, sync() is in libSystem.B.dylib
        libc = ctypes.cdll.LoadLibrary('libSystem.B.dylib')
        libc.sync()
    elif IS_WINDOWS:
        # pylint: disable=protected-access
        ctypes.cdll.LoadLibrary('msvcrt.dll')._flushall()


def wipe_write(path):
    """Overwrite a file's contents with zeros without truncating it.

    Return the open file handle; the caller must close it."""
    # pylint: disable=import-outside-toplevel
    from bleachbit.FileUtilities import getsize
    size = getsize(path)
    try:
        f = open(path, 'wb')
    except IOError as e:
        if e.errno == errno.EACCES:  # permission denied
            os.chmod(path, 0o200)  # user write only
            f = open(path, 'wb')
        else:
            raise
    try:
        blanks = b'\0' * 4096
        while size > 0:
            f.write(blanks)
            size -= 4096
        f.flush()  # flush to OS buffer
        os.fsync(f.fileno())  # force write to disk
    except BaseException:
        f.close()
        raise
    return f


def wipe_contents(path):
    """Wipe files contents

    https://en.wikipedia.org/wiki/Data_remanence
    2006 NIST Special Publication 800-88 (p. 7): "Studies have
    shown that most of today's media can be effectively cleared
    by one overwrite"
    """
    # pylint: disable=import-outside-toplevel
    from bleachbit.FileUtilities import truncate_f

    # pylint: disable=possibly-used-before-assignment
    if IS_WINDOWS and IsUserAnAdmin():
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
            f = wipe_write(path)
        else:
            # The wipe succeeded and already overwrote the file in place.
            # Reopen with 'wb' to truncate it to zero
            f = open(path, 'wb')
    else:
        f = wipe_write(path)
    try:
        truncate_f(f)
    finally:
        f.close()


def wipe_name(pathname1):
    """Wipe the original filename and return the new pathname

    File systems vary in how they store a pathname and how they respond
    to renaming. In general, renaming to a longer name can cause more
    data remnance.

    This function tries to rename the file a single time to a random
    name with the identical length.


    """
    (head, tail) = os.path.split(pathname1)
    target_length = len(tail)
    attempt_count = 0
    while True:
        attempt_count += 1
        if attempt_count > 100:
            logger.info('exhausted same-length rename: %s', pathname1)
            pathname2 = pathname1
            break
        new_tail = __random_string(target_length)
        if not __valid_random_filename(new_tail):
            continue
        pathname2 = os.path.join(head, new_tail)
        if os.path.lexists(pathname2):
            continue
        try:
            os.rename(pathname1, pathname2)
            break
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EPERM, errno.EROFS):
                pathname2 = pathname1
                break
            continue

    return pathname2


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
    # TRANSLATORS: Debug log message shown during file wiping. 'Wiping' is a
    # present participle (ongoing action) refering to secure overwrite.
    # %(pathname)s is the file/directory path; %(fstype)s is the file system type
    # (e.g., ext3, ntfs). Do not translate placeholders.
    logger.debug(_("Wiping path %(pathname)s with file system type %(fstype)s"),
                 {"pathname": pathname, "fstype": fstype})
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
                # Linux gives errno 122 Disk quota exceeded (EDQUOT)
                if e.errno in (errno.EMFILE, errno.ENOSPC, errno.EDQUOT):
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
                    if e.errno in (errno.ENOSPC, errno.EDQUOT):
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
                # [Errno 122] Disk quota exceeded (EDQUOT) is treated the same
                # way because the file is as full as the quota allows.
                if e.errno not in (errno.ENOSPC, errno.EDQUOT):
                    logger.error(
                        _("Error #%d when flushing the file buffer."), e.errno)

            os.fsync(f.fileno())  # write to disk
            # For statistics
            total_bytes += f.tell()
            # sync to disk
            sync()
            # statistics
            elapsed_sec = time.time() - start_time
            rate_mbs = (total_bytes / (1000 * 1000)) / \
                elapsed_sec if elapsed_sec else 0
            # TRANSLATORS: Debug message summarizing a write operation. All placeholders
            # are numeric: %(file_count)d = integer number of files written;
            # %(total_bytes)d = integer total bytes written; %(elapsed_sec)d = integer
            # elapsed seconds; %(rate_mbs).2f = decimal megabytes per second (e.g., 3.14).
            # Do not translate variables.
            logger.debug(_('Wrote %(file_count)d files and %(total_bytes)d bytes '
                         'in %(elapsed_sec)d seconds at %(rate_mbs).2f MB/s'),
                         {"file_count": len(files), "total_bytes": total_bytes,
                         "elapsed_sec": int(elapsed_sec), "rate_mbs": rate_mbs})
            # how much free space is left (should be near zero)
            if IS_POSIX:
                # pylint: disable=no-member
                stats = os.statvfs(pathname)
                # TRANSLATORS: Debug message showing disk space available to regular (non-root) users.
                # %(bytes)d is an integer count of bytes free; %(inodes)d is an integer count of inodes free.
                # Do not translate variables.
                logger.debug(_("%(bytes)d bytes and %(inodes)d inodes available to non-super-user"),
                             {"bytes": stats.f_bsize * stats.f_bavail, "inodes": stats.f_favail})
                # TRANSLATORS: Debug message showing disk space available to the root (admin) user.
                # %(bytes)d is an integer count of bytes free; %(inodes)d is an integer count of inodes free.
                # Do not translate variables.
                logger.debug(_("%(bytes)d bytes and %(inodes)d inodes available to super-user"),
                             {"bytes": stats.f_bsize * stats.f_bfree, "inodes": stats.f_ffree})
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
                            _("Encountered unknown error #0 while truncating file."))
                    time.sleep(0.1)
            # explicitly delete
            try:
                delete(f.name, ignore_missing=True)
            except Exception as e:
                logger.error(
                    'After wiping, error deleting file %s: %s', f.name, e)
