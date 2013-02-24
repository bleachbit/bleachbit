#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2013 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Test FileUtilities.wipe_path
"""

import os
import sys
import tempfile
import time
import traceback

sys.path.append('.')
from bleachbit.FileUtilities import delete, listdir, wipe_path
from bleachbit.General import run_external

def create_disk_image(n_bytes):
    """Make blank file and return filename"""
    (fd, filename) = tempfile.mkstemp(suffix='disk-image', prefix='bleachbit-wipe-test')
    for x in range(1, int(n_bytes/1e5)):
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
    assert(rc==0)


def make_dirty(mountpoint):
    counter = 0
    contents = 'sssshhhh' * 512
    while True:
        try:
            f = tempfile.NamedTemporaryFile(mode='w', suffix='secret', dir=mountpoint, delete=False)
        except:
            print 'error creating temporary file'
            break

        try:
            f.write(contents)
            f.flush()
            counter += 1
        except IOError:
            break

        try:
            f.close()
        except:
            print 'error closing temporary file %s' % f.name
            break
    print 'made %d files' % counter


def mount_filesystem(filename, mountpoint):
    args = ['mount', '-o', 'loop', filename, mountpoint]
    (rc, stdout, stderr) = run_external(args)
    if stderr:
        print stderr
    assert(rc==0)
    print 'mounted %s at %s' % (filename, mountpoint)


def unmount_filesystem(mountpoint):
    time.sleep(0.5) # avoid "in use" error
    args = ['umount', mountpoint]
    attempts = 0
    while True:
        (rc, stdout, stderr) = run_external(args)
        if stderr:
            print stderr
        if 0 == rc:
            break
        attempts += 1
        time.sleep(attempts * 2)
        if attempts > 5:
            raise RuntimeError('cannot umount')


def verify_cleanliness(filename):
    """Return True if the file is clean"""
    found_secret = run_external(['grep','-q', 'secret', filename])[0] == 0 # filename
    found_sshh = run_external(['grep','-q', 'sssshhhh', filename])[0] == 0 # contents
    clean = (found_secret*1) + (found_sshh*10)
    print '%s is clean: %s' % (filename, clean)
    return clean


def test_wipe_sub(n_bytes, mkfs_cmd):
    """Test FileUtilities.wipe_path"""
    if 'nt' == os.name:
        print 'WARNING: test_wipe() not supported on Windows'
        return
    filename = create_disk_image(n_bytes)
    print 'created disk image %s' % filename

    # format filesystem
    format_filesystem(filename, mkfs_cmd)

    # mount
    mountpoint = tempfile.mkdtemp('bleachbit-wipe-mountpoint')
    mount_filesystem(filename, mountpoint)

    # make dirty
    make_dirty(mountpoint)

    # verify dirtiness
    unmount_filesystem(mountpoint)
    assert(verify_cleanliness(filename) == 11)
    mount_filesystem(filename, mountpoint)

    # standard delete
    print 'standard delete'
    for secretfile in listdir(mountpoint):
        delete(secretfile, shred = False)

    # verify dirtiness
    unmount_filesystem(mountpoint)
    assert(verify_cleanliness(filename) == 11)
    mount_filesystem(filename, mountpoint)

    # really wipe
    print 'wiping %s' % mountpoint
    for w in wipe_path(mountpoint):
        pass

    # unmount
    unmount_filesystem(mountpoint)

    # verify cleanliness
    assert(verify_cleanliness(filename) == 0)

    # remove temporary
    delete(filename)
    delete(mountpoint)


def test_wipe():
    """Test wiping on several kinds of file systems"""
    n_bytes=2000000
    mkfs_cmds = ( ('/sbin/mkfs.ext3', '-q', '-F', 'filename'),
        ('/sbin/mkfs.ext4', '-q', '-F', 'filename'),
        ('/sbin/mkfs.ntfs', '-F', 'filename'),
        ('/sbin/mkfs.vfat', 'filename') )
    for mkfs_cmd in mkfs_cmds:
        print
        print '*' * 70
        print ' '.join(mkfs_cmd)
        print '*' * 70
        print
        try:
            test_wipe_sub(n_bytes, mkfs_cmd)
        except:
            print sys.exc_info()[1]
            traceback.print_exc()


test_wipe()
