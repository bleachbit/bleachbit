# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Wipe memory
"""


import os
import re
import subprocess
import sys
import traceback

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


def get_proc_swaps():
    """Return the output of 'swapon -s'"""
    # Usually 'swapon -s' is identical to '/proc/swaps'
    # Here is one exception:
    # https://bugs.launchpad.net/ubuntu/+source/bleachbit/+bug/1092792
    (rc, stdout, _) = General.run_external(['swapon', '-s'])
    if 0 == rc:
        return stdout
    print 'debug: "swapoff -s" failed so falling back to /proc/swaps'
    return open("/proc/swaps").read()


def parse_swapoff(swapoff):
    """Parse the output of swapoff and return the device name"""
    # English is 'swapoff on /dev/sda5' but German is 'swapoff für ...'
    # Example output in English with LVM and hyphen: 'swapoff on /dev/mapper/lubuntu-swap_1'
    # This matches swap devices and swap files
    ret = re.search('^swapoff .* (/[\w/\.-]+)$', swapoff)
    if not ret:
        # no matches
        return None
    return ret.group(1)


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
        ret = parse_swapoff(line)
        if None == ret:
            raise RuntimeError("Unexpected output:\nargs='%(args)s'\nstdout='%(stdout)s'\nstderr='%(stderr)s'"
                               % {'args': str(args), 'stdout': stdout, 'stderr': stderr})
        devices.append(ret)
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


def make_self_oom_target_linux():
    """Make the current process the primary target for Linux out-of-memory killer"""
    # In Linux 2.6.36 the system changed from oom_adj to oom_score_adj
    path = '/proc/%d/oom_score_adj' % os.getpid()
    if os.path.exists(path):
        open(path, 'w').write('1000')
    else:
        path = '/proc/%d/oomadj' % os.getpid()
        if os.path.exists(path):
            open(path, 'w').write('15')
    # OOM likes nice processes
    print 'debug: new nice value', os.nice(19)
    # OOM prefers non-privileged processes
    try:
        uid = General.getrealuid()
        if uid > 0:
            print "debug: dropping privileges of pid %d to uid %d" % \
                (os.getpid(), uid)
            os.seteuid(uid)
    except:
        traceback.print_exc()


def fill_memory_linux():
    """Fill unallocated memory"""
    report_free()
    allocbytes = int(physical_free() * 0.4)
    if allocbytes < 1024:
        return
    megabytes = allocbytes / (1024 ** 2)
    print "info: allocating and wiping %.2f MB (%d B) memory" % (megabytes, allocbytes)
    try:
        buf = '\x00' * allocbytes
    except MemoryError:
        pass
    else:
        fill_memory_linux()
        print "debug: freeing %.2f MB memory" % megabytes
        del buf
    report_free()


def get_swap_size_linux(device, proc_swaps=None):
    """Return the size of the partition in bytes"""
    if None == proc_swaps:
        proc_swaps = get_proc_swaps()
    line = proc_swaps.split('\n')[0]
    if not re.search('Filename\s+Type\s+Size', line):
        raise RuntimeError("Unexpected first line in swap summary '%s'" % line)
    for line in proc_swaps.split('\n')[1:]:
        ret = re.search("%s\s+\w+\s+([0-9]+)\s" % device, line)
        if ret:
            return int(ret.group(1)) * 1024
    raise RuntimeError("error: cannot find size of swap device '%s'\n%s" %
                      (device, proc_swaps))


def get_swap_uuid(device):
    """Find the UUID for the swap device"""
    uuid = None
    args = ['blkid', device, '-s', 'UUID']
    (_, stdout, _) = General.run_external(args)
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
    free_bytes = 0
    for line in f:
        line = line.replace("\n", "")
        ret = re.search('(MemFree|Cached):[ ]*([0-9]*) kB', line)
        if None != ret:
            kb = int(ret.group(2))
            free_bytes += kb * 1024
    if free_bytes > 0:
        return free_bytes
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
    if sys.platform.startswith('linux'):
        return physical_free_linux()
    elif 'win32' == sys.platform:
        return physical_free_windows()
    else:
        raise RuntimeError('unsupported platform for physical_free()')


def report_free():
    """Report free memory"""
    bytes_free = physical_free()
    print "debug: physical free: %d B (%d MB)" % \
        (bytes_free, bytes_free / 1024 ** 2)


def wipe_swap_linux(devices, proc_swaps):
    """Shred the Linux swap file and then reinitilize it"""
    if None == devices:
        return
    if 0 < count_swap_linux():
        raise RuntimeError('Cannot wipe swap while it is in use')
    for device in devices:
        print "info: wiping swap device '%s'" % device
        if get_swap_size_linux(device, proc_swaps) > 8 * 1024 ** 3:
            raise RuntimeError(
                'swap device %s is larger than expected' % device)
        uuid = get_swap_uuid(device)
        # wipe
        FileUtilities.wipe_contents(device, truncate=False)
        # reinitialize
        print "debug: reinitializing swap device %s" % device
        args = ['mkswap', device]
        if uuid:
            args.append("-U")
            args.append(uuid)
        (rc, _, stderr) = General.run_external(args)
        if 0 != rc:
            raise RuntimeError(stderr.replace("\n", ""))


def wipe_memory():
    """Wipe unallocated memory"""
    # cache the file because 'swapoff' changes it
    proc_swaps = get_proc_swaps()
    devices = disable_swap_linux()
    yield True  # process GTK+ idle loop
    print 'debug: detected swap devices:', devices
    wipe_swap_linux(devices, proc_swaps)
    yield True
    child_pid = os.fork()
    if 0 == child_pid:
        make_self_oom_target_linux()
        fill_memory_linux()
        sys.exit(0)
    else:
        print 'debug: wipe_memory() pid %d waiting for child pid %d' % \
            (os.getpid(), child_pid)
        rc = os.waitpid(child_pid, 0)[1]
        if 0 != rc:
            print 'warning: child process returned code %d' % rc
    enable_swap_linux()
    yield 0  # how much disk space was recovered
