# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test FileUtilities.wipe_path
"""

from bleachbit.FileUtilities import delete, free_space, listdir, wipe_path
from bleachbit.General import run_external

import logging
import os
import sys
import tempfile
import time
import traceback

logger = logging.getLogger('bleachbit')


def create_disk_image(n_bytes):
    """Make blank file and return filename"""
    (fd, filename) = tempfile.mkstemp(
        suffix='disk-image', prefix='bleachbit-wipe-test')
    for _x in range(1, int(n_bytes / 1e5)):
        os.write(fd, b'\x00' * 100000)
    os.close(fd)
    return filename


def format_filesystem(filename, mkfs_cmd):
    args = []
    for arg in mkfs_cmd:
        if arg == 'filename':
            args.append(filename)
        else:
            args.append(arg)
    (rc, stdout, stderr) = run_external(args)
    assert(rc == 0)


def make_dirty(mountpoint):
    create_counter = 0
    write_counter = 0
    contents = 'sssshhhh' * 512
    while True:
        try:
            fn = os.path.join(mountpoint, 'secret' + str(create_counter))
            f = open(fn, 'w')
            create_counter += 1
        except:
            logger.error('while creating temporary file #%d', create_counter)
            break

        try:
            f.write(contents)
            f.flush()
            write_counter += 1
        except IOError:
            break

        try:
            f.close()
        except:
            logger.error('while closing temporary file %s', f.name)
            break
    logger.debug('created %d files and wrote to %d files',
                 create_counter, write_counter)


def mount_filesystem(filename, mountpoint):
    args = ['mount', '-o', 'loop', filename, mountpoint]
    (rc, stdout, stderr) = run_external(args)
    if stderr:
        print(stderr)
    assert(rc == 0)
    print('mounted %s at %s', filename, mountpoint)


def unmount_filesystem(mountpoint):
    time.sleep(0.5)  # avoid "in use" error
    args = ['umount', mountpoint]
    attempts = 0
    while True:
        (rc, stdout, stderr) = run_external(args)
        if stderr:
            print(stderr)
        if 0 == rc:
            break
        attempts += 1
        time.sleep(attempts * 2)
        if attempts > 5:
            raise RuntimeError('cannot umount')


def verify_cleanliness(filename):
    """Return True if the file is clean"""
    strings_ret = run_external(['strings', filename])
    secret_count = strings_ret[1].count('secret')  # filename
    sssshhhh_count = strings_ret[1].count('sssshhhh')  # contents
    logger.debug('found %d sssshhhhh in image (contents) and %d secret (filename)',
                 sssshhhh_count, secret_count)

    clean = ((secret_count > 0) * 1) + ((sssshhhh_count > 0) * 10)
    print('%s is clean: %s', filename, clean)
    return clean




def test_wipe():
    """Test wiping on several kinds of file systems"""
    n_bytes = 10000000
    mkfs_cmds = (('/sbin/mkfs.ext3', '-q', '-F', 'filename'),)
#        ('/sbin/mkfs.ext4', '-q', '-F', 'filename'))
#        ('/sbin/mkntfs', '-F', 'filename'),
#        ('/sbin/mkfs.vfat', 'filename') )
    for mkfs_cmd in mkfs_cmds:
        print()
        print('*' * 70)
        print(' '.join(mkfs_cmd))
        print('*' * 70)
        print()
        try:
            test_wipe_sub(n_bytes, mkfs_cmd)
        except:
            print(sys.exc_info()[1])
            traceback.print_exc()


test_wipe()
