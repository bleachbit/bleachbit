# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
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
Wipe memory
"""



import ctypes
import os
import re
import subprocess
import sys
import time
import unittest

import FileUtilities
import General



def count_swap_linux():
    """Count the number of swap devices in use"""
    f = open("/proc/swaps")
    count = 0
    for line in f:
        if line[0] == '/':
            count += 1
    return count


def disable_swap_linux():
    """Disable Linux swap and return list of devices"""
    if 0 == count_swap_linux():
        return
    print "debug: disabling swap"
    args = ["swapoff", "-a", "-v"]
    (rc, stdout, stderr) = General.run_external(args)
    if 0 != rc:
        raise RuntimeError(stderr.replace("\n", ""))
    devices = []
    for line in stdout.split('\n'):
        line = line.replace('\n', '')
        if '' == line:
            continue
        ret = re.search('^swapoff on (/dev/[hs]d[a-z][0-9]+)$', line)
        if None == ret:
            raise RuntimeError("Unexpected output:\nargs='%(args)s'\nstdout='%(stdout)s'\nstderr='%(stderr)s'" \
                % { 'args' : str(args), 'stdout' : stdout, 'stderr' : stderr } )
        devices.append(ret.group(1))
    return devices


def enable_swap_linux():
    """Enable Linux swap"""
    print "debug: re-enabling swap"
    args = ["swapon", "-a"]
    p = subprocess.Popen(args, stderr=subprocess.PIPE)
    p.wait()
    outputs = p.communicate()
    if 0 != p.returncode:
        raise RuntimeError(outputs[1].replace("\n", ""))


def fill_memory_linux():
    """Fill unallocated memory"""
    report_free()
    libc = ctypes.cdll.LoadLibrary("libc.so.6")
    bytes = int(physical_free() * 0.95) # more than 95% causes segfault
    megabytes = bytes / (1024**2)
    print "info: allocating %d bytes of memory (%.2f MB)" % (bytes, megabytes)
    time.sleep(2)
    buffer = libc.malloc(bytes)
    print "debug: wiping the memory I just allocated"
    libc.memset(buffer, 0x00, bytes)
    report_free()
    print "debug: freeing memory"
    libc.free(buffer)
    report_free()


def get_swap_uuid(device):
    """Find the UUID for the swap device"""
    uuid = None
    args = ['blkid', device, '-s', 'UUID']
    (rc, stdout, stderr) = General.run_external(args)
    for line in stdout.split('\n'):
        # example: /dev/sda5: UUID="ee0e85f6-6e5c-42b9-902f-776531938bbf"
        ret = re.search("^%s: UUID=\"([a-z0-9-]+)\"" % device, line)
        if None != ret:
            uuid = ret.group(1)
    print "debug: uuid(%s)='%s'" % (device, uuid)
    return uuid


def physical_free_linux():
    """Return the physical free memory on Linux"""
    f = open("/proc/meminfo")
    bytes = 0
    for line in f:
        line = line.replace("\n","")
        ret = re.search('(MemFree|Cached):[ ]*([0-9]*) kB', line)
        if None != ret:
            kb = int(ret.group(2))
            bytes += kb * 1024
    if bytes > 0:
        return bytes
    else:
        raise Exception("unknown")


def physical_free_windows():
    """Return physical free memory on Windows"""

    from ctypes import c_long, c_ulonglong
    from ctypes.wintypes import Structure, sizeof, windll, byref

    class MEMORYSTATUSEX(Structure):
        _fields_ = [
            ('dwLength', c_long),
            ('dwMemoryLoad', c_long),
            ('ullTotalPhys', c_ulonglong),
            ('ullAvailPhys', c_ulonglong),
            ('ullTotalPageFile', c_ulonglong),
            ('ullAvailPageFile', c_ulonglong),
            ('ullTotalVirtual', c_ulonglong),
            ('ullAvailVirtual', c_ulonglong),
            ('ullExtendedVirtual', c_ulonglong),
        ]

    def GlobalMemoryStatusEx():
        x = MEMORYSTATUSEX()
        x.dwLength = sizeof(x)
        windll.kernel32.GlobalMemoryStatusEx(byref(x))
        return x

    z = GlobalMemoryStatusEx()
    print z
    return z.ullAvailPhys


def physical_free():
    if 'linux2' == sys.platform:
        return physical_free_linux()
    elif 'win32' == sys.platform:
        return physical_free_windows()
    else:
        raise RuntimeError('unsupported platform for physical_free()')


def report_free():
    """Report free memory"""
    bytes = physical_free()
    print "debug: physical free: %d B (%d MB)" % (bytes, bytes/1024**2)


def wipe_swap_linux(devices):
    """Shred the Linux swap file and then reinitilize it"""
    if None == devices:
        return
    if 0 < count_swap_linux():
        raise RuntimeError('Cannot wipe swap while it is in use')
    for device in devices:
        print "info: wiping swap device '%s'" % device
        uuid = get_swap_uuid(device)
        # wipe
        FileUtilities.wipe_contents(device, truncate = False)
        # reinitialize
        print "debug: reinitializing swap device ", device
        args = ['mkswap', device]
        if uuid:
            args.append("-U")
            args.append(uuid)
        (rc, stdout, stderr) = General.run_external(args)
        if 0 != rc:
            raise RuntimeError(stderr.replace("\n", ""))


def wipe_memory():
    """Wipe unallocated memory"""
    devices = disable_swap_linux()
    yield True # process GTK+ idle loop
    print 'debug: wipe_memory(), devices=', devices
    wipe_swap_linux(devices)
    yield True
    child_pid = os.fork()
    if 0 == child_pid:
        fill_memory_linux()
        sys.exit(0)
    else:
        print 'debug: wipe_memory() pid %d waiting for child pid %d' % \
            (os.getpid(), child_pid)
        os.waitpid(child_pid, 0)
    enable_swap_linux()
    yield 0 # how much disk space was recovered


class TestMemory(unittest.TestCase):
    """Unit test for module Memory"""


    def test_count_linux_swap(self):
        """Test for method count_linux_swap"""
        if 'linux2' != sys.platform:
            return
        n_swaps = count_swap_linux()
        self.assert_(isinstance(n_swaps, (int, long)))
        self.assert_(n_swaps >= 0)
        self.assert_(n_swaps < 10)


    def test_physical_free(self):
        """Test for method physical_free"""
        self.assert_(isinstance(physical_free(), (int, long)))
        self.assert_(physical_free() > 0)
        report_free()


    def test_get_swap_uuid(self):
        """Test for method get_swap_uuid"""
        if 'linux2' != sys.platform:
            return
        self.assertEqual(get_swap_uuid('/dev/doesnotexist'), None)


if __name__ == '__main__':
    unittest.main()


