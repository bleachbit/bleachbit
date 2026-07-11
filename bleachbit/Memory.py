# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Wipe memory
"""

import logging
import os
import re
import subprocess
import sys

from bleachbit import FileUtilities
from bleachbit import General
from bleachbit import Log
from bleachbit.Language import get_text as _
from bleachbit.Wipe import wipe_contents

logger = logging.getLogger(__name__)


def count_swap_linux():
    """Count the number of swap devices in use"""
    count = 0
    with open("/proc/swaps") as f:
        for line in f:
            if line[0] == '/':
                count += 1
    return count


def get_proc_swaps():
    """Return the output of 'swapon -s'"""
    # Usually 'swapon -s' is identical to '/proc/swaps'
    # Here is one exception:
    # https://bugs.launchpad.net/ubuntu/+source/bleachbit/+bug/1092792
    (rc, stdout, _stderr) = General.run_external(['swapon', '-s'])
    if 0 == rc:
        return stdout
    logger.debug(
        _("The command 'swapoff -s' failed, so falling back to /proc/swaps for swap information."))
    return open("/proc/swaps").read()


def parse_swapoff(swapoff):
    """Parse the output of swapoff and return the device name"""
    # English is 'swapoff on /dev/sda5' but German is 'swapoff für ...'
    # Example output in English with LVM and hyphen: 'swapoff on /dev/mapper/lubuntu-swap_1'
    # This matches swap devices and swap files
    ret = re.search(r'^swapoff (\w* )?(/[\w/.-]+)$', swapoff)
    if not ret:
        # no matches
        return None
    return ret.group(2)


def disable_swap_linux():
    """Disable Linux swap and return list of devices"""
    if 0 == count_swap_linux():
        return
    logger.debug(_("Disabling swap."))
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
        if ret is None:
            raise RuntimeError(f"Unexpected output:\nargs='{args}'\n"
                               f"stdout='{stdout}'\nstderr='{stderr}'")
        devices.append(ret)
    return devices


def enable_swap_linux():
    """Enable Linux swap"""
    logger.debug(_("Re-enabling swap."))
    args = ["swapon", "-a"]
    (rc, _stdout, stderr) = General.run_external(args)
    if 0 != rc:
        raise RuntimeError(stderr.replace("\n", ""))


def make_self_oom_target_linux(uid=None):
    """Make the current process the primary target for Linux out-of-memory killer

    The optional ``uid`` avoids relying on environment variables such as
    SUDO_UID, which systemd-run does not forward to transient units by
    default. When ``uid`` is None, the real user ID is looked up as before.
    """
    path = f'/proc/{os.getpid()}/oom_score_adj'
    if os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write('1000')
    # OOM likes nice processes
    logger.debug(_("Setting nice value %d for this process."), os.nice(19))
    # OOM prefers non-privileged processes
    try:
        if uid is None:
            uid = General.get_real_uid()
        if uid > 0:
            # TRANSLATORS: Debug message when a process gives up root/admin privileges.
            # %(pid)d is the integer process ID; %(uid)d is the integer user ID to switch to.
            drop_msg = _("Dropping privileges of process ID %(pid)d to user ID %(uid)d.")
            logger.debug(drop_msg, {'pid': os.getpid(), 'uid': uid})
            os.seteuid(uid)
    except:
        logger.exception('Error when dropping privileges')


def fill_memory_linux():
    """Fill unallocated memory"""
    report_free()
    allocbytes = int(physical_free() * 0.4)
    if allocbytes < 1024:
        return
    bytes_str = FileUtilities.bytes_to_human(allocbytes)
    # TRANSLATORS: The variable is a quantity like 5kB
    logger.info(_("Allocating and wiping %s of memory."),
                bytes_str)
    try:
        buf = '\x00' * allocbytes
    except MemoryError:
        pass
    else:
        fill_memory_linux()
        # TRANSLATORS: The variable is a quantity like 5kB
        logger.debug(_("Freeing %s of memory."), bytes_str)
        del buf
    report_free()


def _memory_child_script(real_uid):
    """Return the Python source executed by the memory-wiping child process

    The child makes itself the OOM target and fills memory. ``real_uid`` is
    passed explicitly because systemd-run does not forward the caller's
    environment (e.g. SUDO_UID) to transient units. When ``real_uid`` is
    None the child re-derives it via ``General.get_real_uid()``, which
    inside a systemd scope typically resolves to 0 (root) and skips the
    privilege drop -- this is acceptable because the scope already runs
    with the caller's credentials.
    """
    return (
        "from bleachbit.Memory import make_self_oom_target_linux, "
        "fill_memory_linux; "
        f"make_self_oom_target_linux({real_uid!r}); "
        "fill_memory_linux()"
    )


def _run_memory_child_systemd_scope():
    """Run the memory-wiping child in its own transient systemd scope.

    The child is isolated via a separate scope so that systemd's default
    OOMPolicy=stop (see DefaultOOMPolicy in systemd-system.conf(5)) does
    not kill the parent (and the rest of the parent's session unit) when
    the kernel OOM-kills the child. Without this isolation the parent
    dies before it can re-enable swap, leaving the system without swap.

    Returns the child's exit status (0 on success, the signal number if
    killed by a signal such as the OOM killer, or None if the child could
    not be started this way -- in which case the caller should fall back
    to ``_run_memory_child_fork``).
    """
    if not FileUtilities.exe_exists('systemd-run'):
        return None
    try:
        real_uid = General.get_real_uid()
    except Exception:
        real_uid = None
    # Make the bleachbit package importable when running from a source
    # checkout. When installed, this is harmless (the directory is already
    # on sys.path).
    pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    python_path = os.pathsep.join(
        p for p in (pkg_parent, env.get('PYTHONPATH', '')) if p)
    env['PYTHONPATH'] = python_path
    # The child is launched via "python -c", so it cannot see --debug in
    # sys.argv. Forward the parent's debug state via an environment variable
    # so the child's logger (initialized on import) matches the parent's.
    if Log.is_debugging_enabled_via_cli():
        env['BLEACHBIT_DEBUG'] = '1'
    # Include the PID so concurrent runs do not collide on a fixed unit
    # name (systemd-run refuses to create a unit that already exists).
    args = [
        'systemd-run', '--scope', '--collect', '--quiet',
        f'--unit=bleachbit-wipe-memory-{os.getpid()}',
        '--property=OOMPolicy=kill',
        '--', sys.executable, '-c', _memory_child_script(real_uid),
    ]
    def run_scope(scope_args):
        logger.debug('Running command: %s', ' '.join(scope_args))
        try:
            return subprocess.run(
                scope_args, env=env, capture_output=True, text=True)
        except FileNotFoundError:
            return None

    proc = run_scope(args)
    if proc is None:
        return None
    # Ubuntu 22.04 LTS (supported until April 2027) uses systemd 249, which
    # does not support OOMPolicy= for scope units. A separate scope still
    # isolates the child from the parent, so retry without that property.
    if proc.returncode != 0 and 'OOMPolicy' in (proc.stderr or ''):
        legacy_args = [
            arg for arg in args if arg != '--property=OOMPolicy=kill']
        proc = run_scope(legacy_args)
        if proc is None:
            return None
    rc = proc.returncode
    # subprocess.run reports -N when the child died from signal N (e.g. the
    # OOM killer sends SIGKILL, reported as -9). Normalize to the signal
    # number so the caller can recognize OOM death as 9.
    if rc < 0:
        return -rc
    # A non-zero, non-signal exit code means systemd-run itself failed to
    # create the scope (e.g. no systemd as PID 1, no D-Bus session, or a
    # permission error) -- the child never ran. Fall back to fork so
    # memory is still wiped in those environments.
    if rc != 0:
        err = (proc.stderr or '').strip()
        if err:
            logger.debug(
                'systemd-run returned %d (%s); falling back to fork()',
                rc, err)
        else:
            logger.debug(
                'systemd-run returned %d; falling back to fork()', rc)
        return None
    return rc


def _run_memory_child_fork():
    """Run the memory-wiping child via os.fork() (fallback used when
    systemd-run is unavailable). Returns the child's exit status."""
    try:
        real_uid = General.get_real_uid()
    except Exception:
        real_uid = None
    child_pid = os.fork()
    if 0 == child_pid:
        make_self_oom_target_linux(real_uid)
        fill_memory_linux()
        os._exit(0)
    else:
        # TRANSLATORS: This is a debugging message that the parent process
        # is waiting for the child process. %(parent_pid)d is the parent
        # process ID; %(child_pid)d is the child process ID.
        logger.debug(_("The function wipe_memory() with process ID %(parent_pid)d is "
                       "waiting for child process ID %(child_pid)d."),
                     {'parent_pid': os.getpid(), 'child_pid': child_pid})
        status = os.waitpid(child_pid, 0)[1]
        if os.WIFSIGNALED(status):
            return os.WTERMSIG(status)
        return os.WEXITSTATUS(status)


def get_swap_size_linux(device, proc_swaps=None):
    """Return the size of the partition in bytes"""
    if proc_swaps is None:
        proc_swaps = get_proc_swaps()
    line = proc_swaps.split('\n')[0]
    if not re.search(r'Filename\s+Type\s+Size', line):
        raise RuntimeError("Unexpected first line in swap summary '%s'" % line)
    for line in proc_swaps.split('\n')[1:]:
        ret = re.search(r"%s\s+\w+\s+([0-9]+)\s" % device, line)
        if ret:
            return int(ret.group(1)) * 1024
    raise RuntimeError("error: cannot find size of swap device '%s'\n%s" %
                       (device, proc_swaps))


def get_swap_uuid(device):
    """Find the UUID for the swap device"""
    uuid = None
    args = ['blkid', device, '-s', 'UUID']
    (_rc, stdout, _stderr) = General.run_external(args)
    for line in stdout.split('\n'):
        # example: /dev/sda5: UUID="ee0e85f6-6e5c-42b9-902f-776531938bbf"
        ret = re.search(r"^%s: UUID=\"([a-z0-9-]+)\"" % device, line)
        if ret is not None:
            uuid = ret.group(1)
    # TRANSLATORS: Debug message. 'Found' is a past tense verb (short for
    # "Found [that] the UUID for swap device ..."). %(device)s is the device
    # path (e.g., /dev/sda5); %(uuid)s is a UUID string
    # (e.g., ee0e85f6-6e5c-42b9-902f-776531938bbf). Do not translate variables.
    logger.debug(_("Found UUID for swap device %(device)s is %(uuid)s."),
                 {'device': device, 'uuid': uuid})
    return uuid


def physical_free_darwin(run_vmstat=None):
    def parse_line(k, v):
        return k, int(v.strip(" ."))

    def get_page_size(line):
        m = re.match(
            r"Mach Virtual Memory Statistics: \(page size of (\d+) bytes\)",
            line)
        if m is None:
            raise RuntimeError("Can't parse vm_stat output")
        return int(m.groups()[0])
    if run_vmstat is None:
        def run_vmstat():
            return subprocess.check_output(["vm_stat"])
    output = iter(run_vmstat().split("\n"))
    page_size = get_page_size(next(output))
    vm_stat = dict(parse_line(*l.split(":")) for l in output if l != "")
    return vm_stat["Pages free"] * page_size


def physical_free_linux():
    """Return the physical free memory on Linux"""
    free_bytes = 0
    with open("/proc/meminfo") as f:
        for line in f:
            line = line.replace("\n", "")
            ret = re.search(r'^(MemFree|Cached):[ ]*([0-9]*) kB', line)
            if ret is not None:
                kb = int(ret.group(2))
                free_bytes += kb * 1024
    if free_bytes > 0:
        return free_bytes
    else:
        raise Exception("unknown")


def physical_free_windows():
    """Return physical free memory on Windows"""

    from ctypes import c_ulong, c_ulonglong, Structure, sizeof, windll, byref

    class MEMORYSTATUSEX(Structure):
        _fields_ = [
            ('dwLength', c_ulong),
            ('dwMemoryLoad', c_ulong),
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
    return z.ullAvailPhys


def physical_free():
    if sys.platform == 'linux':
        return physical_free_linux()
    elif 'win32' == sys.platform:
        return physical_free_windows()
    elif 'darwin' == sys.platform:
        return physical_free_darwin()
    else:
        raise RuntimeError('unsupported platform for physical_free()')


def report_free():
    """Report free memory"""
    bytes_free = physical_free()
    bytes_str = FileUtilities.bytes_to_human(bytes_free)
    # TRANSLATORS: The variable is a quantity like 5kB
    logger.debug(_("Physical free memory is %s."),
                 bytes_str)


def wipe_swap_linux(devices, proc_swaps):
    """Shred the Linux swap file and then reinitialize it"""
    if devices is None:
        return
    if 0 < count_swap_linux():
        raise RuntimeError('Cannot wipe swap while it is in use')
    for device in devices:
        # if '/cryptswap' in device:
        #    logger.info('Skipping encrypted swap device %s.', device)
        #    continue
        # TRANSLATORS: The variable is a device like /dev/sda2
        logger.info(_("Wiping the swap device %s."), device)
        safety_limit_bytes = 29 * 1024 ** 3  # 29 gibibytes
        actual_size_bytes = get_swap_size_linux(device, proc_swaps)
        if actual_size_bytes > safety_limit_bytes:
            raise RuntimeError(
                f'swap device {device} is larger ({actual_size_bytes})'
                f' than expected ({safety_limit_bytes})')
        uuid = get_swap_uuid(device)
        # wipe
        wipe_contents(device, truncate=False)
        # reinitialize
        # TRANSLATORS: The variable is a device like /dev/sda2
        logger.debug(_("Reinitializing the swap device %s."), device)
        args = ['mkswap', device]
        if uuid:
            args.append("-U")
            args.append(uuid)
        (rc, _stdout, stderr) = General.run_external(args)
        if 0 != rc:
            raise RuntimeError(stderr.replace("\n", ""))


def wipe_memory():
    """Wipe unallocated memory"""
    for cmd in ('swapon', 'swapoff', 'blkid'):
        if not FileUtilities.exe_exists(cmd):
            raise RuntimeError(f"wipe_memory: Command {cmd} not found")
    # cache the file because 'swapoff' changes it
    proc_swaps = get_proc_swaps()
    devices = disable_swap_linux()
    yield True  # process GTK+ idle loop
    # TRANSLATORS: The variable is a device like /dev/sda2
    logger.debug(_("Detected these swap devices: %s"), str(devices))
    wipe_swap_linux(devices, proc_swaps)
    yield True
    # Prefer a separate systemd scope so that systemd's unit-level OOM
    # policy cannot kill the parent when the child is OOM-killed. Fall back
    # to a plain fork where systemd-run is unavailable.
    rc = _run_memory_child_systemd_scope()
    if rc is None:
        rc = _run_memory_child_fork()
    if rc not in (0, 9):
        logger.warning(
            _("The child memory-wiping process returned code %d."), rc)
    enable_swap_linux()
    yield 0  # how much disk space was recovered
