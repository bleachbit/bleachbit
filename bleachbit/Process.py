# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Enumerate and terminate processes
"""

import signal
import glob
import subprocess
from collections import namedtuple
import os

from bleachbit import IS_LINUX, IS_POSIX, IS_WINDOWS

ProcessInfo = namedtuple('ProcessInfo', ['pid', 'name', 'same_user'])

try:
    import psutil
    _has_psutil = True
except ImportError:
    _has_psutil = False


def enumerate_processes():
    """Yield ProcessInfo(pid, name, same_user) for all accessible processes.

    'same_user' is True if the process owner matches the current (real) user.
    On Unix with sudo, compares against the non-root user.
    """
    if _has_psutil and IS_POSIX:
        yield from _enumerate_psutil_posix()
        return
    # Windows should always have psutil.
    if _has_psutil and IS_WINDOWS:
        yield from _enumerate_psutil_windows()
        return
    if IS_LINUX:
        yield from _enumerate_proc_fs()
        return
    if IS_POSIX:
        yield from _enumerate_ps_aux()
        return
    raise RuntimeError('no method to enumerate processes on this system')


def _enumerate_psutil_posix():
    """Enumerate processes with psutils on POSIX"""
    from bleachbit.General import get_real_uid
    target_uid = get_real_uid()
    for proc in psutil.process_iter(['name', 'exe', 'uids']):
        try:
            name = proc.info['name']
            if not name:
                continue
            exe = proc.info.get('exe')
            uids = proc.info.get('uids')
            same_user = uids is not None and uids.real == target_uid
            yield ProcessInfo(proc.pid, name, same_user)
            # exe basename may differ from name (e.g. truncated comm)
            if exe and os.path.basename(exe) != name:
                yield ProcessInfo(proc.pid, os.path.basename(exe), same_user)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _enumerate_psutil_windows():
    """Enumerate processes with psutils on Windows"""

    current_user = psutil.Process().username().lower()
    for proc in psutil.process_iter(['name', 'username']):
        try:
            name = proc.info['name']
            if not name:
                continue
            same_user = (proc.info['username'] or '').lower() == current_user
            yield ProcessInfo(proc.pid, name, same_user)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _enumerate_proc_fs():
    """/proc filesystem strategy (Linux)"""
    from bleachbit.General import get_real_uid
    target_uid = get_real_uid()
    for filename in glob.iglob("/proc/*/exe"):
        pid_dir = os.path.dirname(filename)
        pid = int(os.path.basename(pid_dir))
        name = None
        try:
            target = os.path.realpath(filename)
            # Google Chrome 74 on Ubuntu 19.04 showed up as
            # /opt/google/chrome/chrome (deleted)
            name = os.path.basename(target).replace(' (deleted)', '')
        except OSError:
            # 13 = permission denied
            pass
        except TypeError:
            # TypeError happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            pass

        if not name:
            try:
                with open(os.path.join(pid_dir, 'stat'), 'r',
                          encoding='utf-8') as f:
                    name = f.read().split()[1].strip('()')
            except (OSError, IndexError):
                continue
        same_user = False
        try:
            same_user = os.stat(pid_dir).st_uid == target_uid
        except OSError:
            pass
        yield ProcessInfo(pid, name, same_user)


def _enumerate_ps_aux():
    """ps aux strategy (BSD/macOS)"""
    from bleachbit.General import get_real_username
    current_user = get_real_username()
    ps_out = subprocess.check_output(
        ["ps", "aux", "-c"], universal_newlines=True)
    first_line = ps_out.split('\n', maxsplit=1)[0].strip()
    if "USER" not in first_line or "COMMAND" not in first_line:
        raise RuntimeError("Unexpected ps header format")
    for line in ps_out.split("\n")[1:]:
        parts = line.split()
        if len(parts) < 11:
            continue
        yield ProcessInfo(int(parts[1]), parts[10], parts[0] == current_user)


def is_process_running(exename, require_same_user):
    """Check whether exename is running"""
    ci = os.name == 'nt'  # case-insensitive on Windows
    if ci:
        exename = exename.lower()
    for proc in enumerate_processes():
        name = proc.name.lower() if ci else proc.name
        if name == exename and (not require_same_user or proc.same_user):
            return True
    return False


def terminate_process(exename, require_same_user):
    """Terminate processes matching exename. Returns list of affected PIDs."""
    ci = os.name == 'nt'
    if ci:
        exename = exename.lower()
    terminated = []
    for proc in enumerate_processes():
        name = proc.name.lower() if ci else proc.name
        if name == exename and (not require_same_user or proc.same_user):
            if proc.pid in terminated:
                continue
            try:
                if IS_WINDOWS:
                    psutil.Process(proc.pid).kill()
                else:
                    os.kill(proc.pid, signal.SIGTERM)
                terminated.append(proc.pid)
            except (ProcessLookupError, PermissionError, OSError):
                continue
    return terminated
