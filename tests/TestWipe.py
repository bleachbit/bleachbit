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

"""
Test FileUtilities.wipe_path

Example invocations:

# Run unit test that wipes a disk image. This is safe.
sudo python3 -m unittest -v tests.TestWipe

# Equivalent to above
sudo python3 -m tests.TestWipe

# Run unit test with specific filesystem
sudo BB_FS=ext3 python3 -m unittest -v tests.TestWipe

# Wipe a real device---dangerous with all file system types
sudo python3 -m tests.TestWipe --destroy /dev/sdb4

# Wipe a real device---dangerous with ext3
sudo python3 -m tests.TestWipe --destroy /dev/sdb4 --format ext3


"""

import argparse
import logging
import os
import stat
import sys
import tempfile
import time
import unittest

from bleachbit.FileUtilities import delete, exe_exists, free_space, listdir, wipe_path
from bleachbit.General import run_external
from tests import common

logger = logging.getLogger('bleachbit')

IMAGE_SIZE_BYTES = 2097152
MAX_WIPES = 3
FS_TYPES = ('ext3', 'ext4', 'ntfs', 'vfat')  # 'xfs'


def create_disk_image(n_bytes, fs_type):
    """Make blank file and return filename

    The filename prefix includes the mkfs program basename to aid debugging.
    """
    (fd, filename) = tempfile.mkstemp(
        suffix='disk-image', prefix=f'bleachbit-wipe-test-{fs_type}-')
    try:
        os.ftruncate(fd, n_bytes)
    finally:
        os.close(fd)
    return filename


def run_or_die(args):
    """Run command and die if it fails

    In case of success, return stdout.
    """
    (rc, stdout, stderr) = run_external(args)
    assert (rc == 0), f"Command failed with return code {rc}, stderr: {stderr}"
    return stdout


def format_filesystem(filename, fs_type):
    """Format filesystem

    FIXME: some file systems require larger image size than default.
    * btrfs requires 114,294,784 bytes
    * xfs requires 300MB

    Potential improvement later: add option to partially fill a block device.
    mkfs.fat accepts argument as block size (1024B)
    mkfs.ntfs accepts argument as sector size (512B)
    mkfs.ext4 accepts argument as 1024B blocks or with optional suffix like 5G
    """
    fs_commands = {
        'ext3': ('/sbin/mkfs.ext3', '-q', '-F', filename),
        'ext4': ('/sbin/mkfs.ext4', '-q', '-F', filename),
        # 'xfs': ('/sbin/mkfs.xfs', '-q', '-f', filename),
        'ntfs': ('/sbin/mkntfs', '-F', filename),
        'vfat': ('/sbin/mkfs.fat', '-F', '32', filename)
    }
    cmd = fs_commands[fs_type]
    run_or_die(cmd)


def make_dirty(mountpoint):
    """Make filesystem dirty by writing

    Files have "secret" in their name and "sssshhhh" in their contents.
    """
    create_counter = 0
    write_counter = 0
    contents = 'sssshhhh' * 512
    while True:
        try:
            fn = os.path.join(mountpoint, 'secret' + str(create_counter))
            with open(fn, 'w', encoding='utf-8') as f:
                create_counter += 1
                f.write(contents)
                f.flush()
                write_counter += 1
        except IOError:
            logger.error(
                'error while creating or writing to temporary file #%d', create_counter)
            break
    create_counter_str = f"{create_counter:,}"
    write_counter_str = f"{write_counter:,}"
    logger.debug('created %s files and wrote to %s files',
                 create_counter_str, write_counter_str)


def mount_filesystem(device_or_image, mountpoint):
    """Mount filesystem from either a real device or disk image"""
    if _is_block_device(device_or_image):
        option = 'rw,nosuid,nodev,noexec'
    else:
        option = 'loop'
    args = ['mount', '-o', option, device_or_image, mountpoint]
    run_or_die(args)
    logger.debug('mounted %s at %s', device_or_image, mountpoint)


def unmount_filesystem(mountpoint):
    """Unmount filesystem

    In case of error, retry up to 5 times.
    """
    time.sleep(0.5)  # avoid "in use" error
    args = ['umount', mountpoint]
    attempts = 0
    while True:
        (rc, _, stderr) = run_external(args)
        if stderr:
            logger.error(stderr)
        if 0 == rc:
            break
        attempts += 1
        time.sleep(attempts * 2)
        if attempts > 5:
            raise RuntimeError('cannot umount')


def assert_clean(filename, fs_type, expect_clean):
    """Assert cleanliness or dirtiness of a disk image.

    Semantics:
    - If expect_clean is True: assert no contents markers remain.
    - If expect_clean is False: assert contents markers remain (dirty).
    - If expect_clean is None: skip assertion.

    Filename remnants are logged but not asserted because detectability varies by filesystem.

    Returns count of file contents markers.
    """
    # ASCII strings for covers ext*, FAT, and file contents
    (rc_ascii, out_ascii, _err_ascii) = run_external(['strings', filename])
    if rc_ascii != 0:
        out_ascii = ''

    # UTF-16LE strings for covers NTFS filename storage
    out_le = ''
    if 'ntfs' == fs_type:
        (rc_le, out_le, _err_le) = run_external(['strings', '-el', filename])
        if rc_le != 0:
            out_le = ''

    # Filenames may be stored as ASCII or UTF-16LE depending on filesystem
    filename_count = max(out_ascii.count('secret'), out_le.count('secret'))

    # File contents were written as ASCII text
    contents_count = out_ascii.count('sssshhhh')
    contents_count_str = f"{contents_count:,}"
    filename_count_str = f"{filename_count:,}"

    logger.debug('found %s markers in image contents and %s markers in filenames',
                 contents_count_str, filename_count_str)

    if expect_clean is None:
        pass
    elif expect_clean:
        assert contents_count == 0, (
            f'Contents not wiped: found {contents_count_str} markers; '
            f'filename markers: {filename_count_str}; '
            f'fs: {fs_type}')
    else:
        assert contents_count > 0, (
            'No contents marker found; filesystem not dirty '
            f'(filename markers: {filename_count_str}); '
            f'fs: {fs_type}')
    return contents_count


@common.skipIfWindows
def wipe_helper(fs_type, n_bytes=None, device_path=None, passes=MAX_WIPES, sleep_seconds=5):
    """Test FileUtilities.wipe_path on image or block device

    For device image, pass device_path and set n_bytes to None.
    For image, pass n_bytes and set device_path to None.
    """

    assert isinstance(fs_type, str)
    assert fs_type in FS_TYPES

    is_device = False
    if device_path:
        if _is_block_device(device_path):
            filename = device_path
        else:
            raise ValueError(f'Not a block device: {device_path}')
        _real_device_warning(device_path, sleep_seconds)
        is_device = True
        assert n_bytes is None, 'n_bytes must be None when using a block device'
    else:
        assert isinstance(n_bytes, int)
        assert n_bytes > 0
        filename = create_disk_image(n_bytes, fs_type)
        logger.debug('created disk image %s', filename)

    for exe in ('strings', 'df'):
        if not exe_exists(exe):
            raise RuntimeError(f'{exe} not found')

    # format filesystem
    format_filesystem(filename, fs_type)

    # mount
    mountpoint = tempfile.mkdtemp(prefix='bleachbit-wipe-mountpoint')
    mount_filesystem(filename, mountpoint)

    # baseline free disk space
    logger.debug('df for clean filesystem %s', mountpoint)
    logger.debug(run_external(['df', mountpoint])[1])

    # make dirty
    make_dirty(mountpoint)

    # verify dirtiness (require contents marker; filenames may not be detectable on all FS)
    unmount_filesystem(mountpoint)
    content_markers_dirty = assert_clean(filename, fs_type, expect_clean=False)
    mount_filesystem(filename, mountpoint)

    # standard delete
    logger.info('standard delete')
    delete_counter = 0
    for secretfile in listdir(mountpoint):
        if 'secret' not in secretfile:
            # skip lost+found
            continue
        delete(secretfile, shred=False)
        delete_counter += 1
    logger.debug('deleted %s files', f"{delete_counter:,}")

    # check
    logger.debug('df for empty, dirty filesystem %s', mountpoint)
    logger.debug(run_external(['df', mountpoint])[1])

    # verify dirtiness again (require contents marker; filenames may not be detectable)
    unmount_filesystem(mountpoint)
    assert_clean(filename, fs_type, expect_clean=False)
    mount_filesystem(filename, mountpoint)
    expected_free_space = free_space(mountpoint)

    content_markers_list = []
    # measure effectiveness of multiple wipes
    for i in range(1, passes + 1):
        print('*' * 30)
        print(f'* pass {i} for {fs_type} *')
        print('*' * 30)

        # remount
        if i > 1:
            mount_filesystem(filename, mountpoint)

        # really wipe
        logger.info('wiping %s', mountpoint)

        old_level = logging.getLogger('bleachbit.FileUtilities').level
        logging.getLogger('bleachbit.FileUtilities').setLevel(logging.INFO)
        try:
            for _w in wipe_path(mountpoint):
                pass
        finally:
            logging.getLogger('bleachbit.FileUtilities').setLevel(old_level)

        # verify cleaning process freed all space it allocated
        actual_free_space = free_space(mountpoint)
        if not expected_free_space == actual_free_space:
            logger.error('expecting %d free space but got %d',
                         expected_free_space, actual_free_space)

        # unmount
        unmount_filesystem(mountpoint)

        # Require contents to be wiped. Wiping filenames is not supported.
        content_markers = assert_clean(filename, fs_type, None)
        content_markers_list.append(content_markers)
        effectiveness = 100 * (content_markers_dirty -
                               content_markers) / content_markers_dirty
        print(
            f"Pass {i}: Content markers: {content_markers:,}, Effectiveness: {effectiveness:.1f}%")
        if content_markers == 0:
            break

    # show content marker counts to help user understand wiping effectiveness
    if content_markers_list == [0]:
        print('100% effective on first pass!')
    else:
        print(f"\nContent marker counts by pass: {content_markers_list}")
        if len(content_markers_list) > 1:
            if content_markers_list[0] > min(content_markers_list):
                print('Wiping had incremental improvement after first pass')
            else:
                print('Wiping did not improve after first pass')

    if not is_device:
        delete(filename)
    delete(mountpoint)
    if content_markers > 0:
        raise AssertionError(f'Contents not wiped for {fs_type}')


class WipeTestCase(common.BleachbitTestCase):
    """Test case for file wiping operations"""

    @common.skipIfWindows
    @common.test_also_with_sudo
    def test_wipe(self):
        """Test wiping on several kinds of file systems"""
        fs_types = FS_TYPES
        # Optional filter example: sudo BB_FS=ext3 python3 -m unittest tests.TestWipe
        env_fs = os.environ.get('BB_FS') or os.environ.get('bb_fs')
        if env_fs:
            if env_fs not in FS_TYPES:
                raise ValueError(
                    f'BB_FS={env_fs} did not match valid file system type')
            fs_types = (env_fs,)
        for fs_type in fs_types:
            if common.have_root():
                wipe_helper(fs_type=fs_type,
                            n_bytes=IMAGE_SIZE_BYTES)
            else:
                # Mount will fail
                with self.assertRaises(AssertionError):
                    wipe_helper(fs_type=fs_type,
                                n_bytes=IMAGE_SIZE_BYTES)


def suite():
    """Return a test suite"""
    return unittest.makeSuite(WipeTestCase)


def _real_device_warning(target_desc, sleep_seconds):
    border = '=' * 78
    msg = (
        f"\n{border}\n"
        f"DANGEROUS OPERATION REQUESTED\n\n"
        f"You requested wiping all data on: {target_desc}\n"
        f"This is DESTRUCTIVE and will lead to DATA LOSS.\n"
        f"Proceeding in {sleep_seconds} seconds. Press Ctrl+C to abort.\n"
        f"{border}\n"
    )
    print(msg)
    for i in range(sleep_seconds, 0, -1):
        print(f"Starting in {i}...", end='\r', flush=True)
        time.sleep(1)
    print(' ' * 40, end='\r', flush=True)


def _is_block_device(path):
    """Return True if path is a block device."""
    try:
        st = os.stat(path)
        return stat.S_ISBLK(st.st_mode)
    except Exception:
        return False


def _ensure_not_mounted(device_path):
    """Exit if the given device is mounted anywhere.

    Uses 'findmnt' to query mount targets for the source device (and its
    realpath). If mounted anywhere, exit safely.
    """
    if not device_path:
        return
    if not exe_exists('findmnt'):
        raise RuntimeError('findmnt not found')
    # Check real path in case of link such as /dev/disk/by-uuid/..
    candidates = [device_path]
    real = os.path.realpath(device_path)
    if real != device_path:
        candidates.append(real)

    for dev in candidates:
        rc, out, _err = run_external(['findmnt', dev])
        if rc == 0 and out.strip():
            print(
                f"Refusing to operate on {device_path}: mounted at {out.strip()}")
            sys.exit(3)


def main():
    """Main"""
    if len(sys.argv) == 1:
        unittest.main()
        return

    parser = argparse.ArgumentParser(
        description=(
            'Run TestWipe as a destructive tool to wipe free space on a real block device.'
            'By default, without arguments, this script runs unittests.'
            'DANGER! Do not delete your data! Carefully check the options!'
        )
    )
    parser.add_argument('--destroy', required=True,
                        help='Block device (e.g., /dev/sdb1) that will be destroyed!')
    parser.add_argument(
        '--format', help='Comma-separated filesystems to format before wiping (ext3,ext4,ntfs,vfat)')
    parser.add_argument('--passes', type=int, default=1,
                        help='Number of wipe passes (default: 1)')
    parser.add_argument('--sleep', type=int, default=5,
                        help='Seconds to wait before start (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if not common.have_root():
        print('Use sudo to run this script')
        sys.exit(2)

    # Parse formats list if provided
    formats = FS_TYPES
    if args.format:
        raw = [s.strip().lower() for s in args.format.split(',') if s.strip()]
        invalid = [fs for fs in raw if fs not in FS_TYPES]
        if invalid:
            print(f"Error: unsupported filesystem(s): {', '.join(invalid)}")
            sys.exit(2)
        formats = raw if raw else None

    _ensure_not_mounted(args.destroy)

    for fs_type in formats:
        wipe_helper(fs_type=fs_type,
                    device_path=args.destroy,
                    passes=args.passes,
                    sleep_seconds=args.sleep,
                    )
    sys.exit(0)


if __name__ == '__main__':
    main()
