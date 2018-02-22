#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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
"""

from __future__ import absolute_import, print_function

from bleachbit.FileUtilities import delete, free_space, listdir, wipe_path
from bleachbit.General import run_external

import logging
import os
import sys
import tempfile
import time
import traceback
import unittest

logger = logging.getLogger('bleachbit')


def create_disk_image(n_bytes):
    """Make blank file and return filename"""
    (fd, filename) = tempfile.mkstemp(
        suffix='disk-image', prefix='bleachbit-wipe-test')
    for x in range(1, int(n_bytes / 1e5)):
        os.write(fd, '\x00' * 100000)
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
    logger.debug('created %d files and wrote to %d files', create_counter, write_counter)


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
    logger.debug('found %d sssshhhhh in image (contents) and %d secret (filename)', sssshhhh_count, secret_count)

    clean = ((secret_count > 0) * 1) + ((sssshhhh_count > 0) * 10)
    print('%s is clean: %s', filename, clean)
    return clean


@unittest.skipIf('nt' == os.name, 'test_wipe() not supported on Windows')
def test_wipe_sub(n_bytes, mkfs_cmd):
    """Test FileUtilities.wipe_path"""

    filename = create_disk_image(n_bytes)
    print('created disk image %s' % filename)

    # format filesystem
    format_filesystem(filename, mkfs_cmd)

    # mount
    mountpoint = tempfile.mkdtemp(prefix='bleachbit-wipe-mountpoint')
    mount_filesystem(filename, mountpoint)

    # baseline free disk space
    print('df for clean filesystem')
    print(run_external(['df', mountpoint])[1])

    # make dirty
    make_dirty(mountpoint)

    # verify dirtiness
    unmount_filesystem(mountpoint)
    assert(verify_cleanliness(filename) == 11)
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
    logger.debug('deleted %d files', delete_counter)

    # check
    print('df for empty, dirty filesystem')
    print(run_external(['df', mountpoint])[1])

    # verify dirtiness
    unmount_filesystem(mountpoint)
    assert(verify_cleanliness(filename) == 11)
    mount_filesystem(filename, mountpoint)
    expected_free_space = free_space(mountpoint)

    # measure effectiveness of multiple wipes
    for i in range(1, 10):
        print('*' * 30)
        print('* pass %d *' % i)
        print('*' * 30)

        # remount
        if i > 1:
            mount_filesystem(filename, mountpoint)\

        # really wipe
        print('wiping %s' % mountpoint)
        for w in wipe_path(mountpoint):
            pass

        # verify cleaning process freed all space it allocated
        actual_free_space = free_space(mountpoint)
        if not expected_free_space == actual_free_space:
            print ('expecting %d free space but got %d' %
                   (expected_free_space, actual_free_space))
            import pdb
            pdb.set_trace()

        # unmount
        unmount_filesystem(mountpoint)

        # verify cleanliness
        cleanliness = verify_cleanliness(filename)

    assert(cleanliness < 2)

    # remove temporary
    delete(filename)
    delete(mountpoint)


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
