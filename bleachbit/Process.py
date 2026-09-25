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
import time
from collections import namedtuple
import os

from bleachbit import IS_LINUX, IS_POSIX, IS_WINDOWS

ProcessInfo = namedtuple('ProcessInfo', ['pid', 'name', 'same_user'])

# Resolved on first use, not at import
_psutil = None
_has_psutil = None


def _import_psutil():
    """Return the psutil module, or None when it is not installed"""
    global _psutil, _has_psutil  # pylint: disable=global-statement
    if _has_psutil is None:
        try:
            import psutil  # pylint: disable=import-outside-toplevel
        except ImportError:
            _psutil, _has_psutil = None, False
        else:
            _psutil, _has_psutil = psutil, True
    return _psutil


def enumerate_processes():
    """Yield ProcessInfo(pid, name, same_user) for all accessible processes.

    'same_user' is True if the process owner matches the current (real) user.
    On Unix with sudo, compares against the non-root user.
    """
    if _import_psutil() and IS_POSIX:
        yield from _enumerate_psutil_posix()
        return
    # Windows should always have psutil.
    if _import_psutil() and IS_WINDOWS:
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
    psutil = _import_psutil()
    target_uid = get_real_uid()
    for proc in psutil.process_iter(['name', 'exe', 'uids', 'cmdline']):
        try:
            name = proc.info['name']
            if not name:
                continue
            exe = proc.info.get('exe')
            uids = proc.info.get('uids')
            same_user = uids is not None and uids.real == target_uid
            names = {name}
            # exe basename may differ from name (e.g. truncated comm)
            if exe:
                names.add(os.path.basename(exe))
            # argv[0] may differ from exe (e.g. a versioned binary like
            # ~/.local/share/claude/versions/2.1.270 launched as 'claude')
            cmdline = proc.info.get('cmdline')
            if cmdline:
                names.add(os.path.basename(cmdline[0]))
            for proc_name in names:
                if proc_name:
                    yield ProcessInfo(proc.pid, proc_name, same_user)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _enumerate_psutil_windows():
    """Enumerate processes with psutils on Windows"""
    psutil = _import_psutil()
    current_user = psutil.Process().username().lower()
    for proc in psutil.process_iter(['name', 'username', 'cmdline']):
        try:
            name = proc.info['name']
            if not name:
                continue
            same_user = (proc.info['username'] or '').lower() == current_user
            names = {name}
            cmdline = proc.info.get('cmdline')
            if cmdline:
                names.add(os.path.basename(cmdline[0]))
            for proc_name in names:
                if proc_name:
                    yield ProcessInfo(proc.pid, proc_name, same_user)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _enumerate_proc_fs():
    """/proc filesystem strategy (Linux)"""
    from bleachbit.General import get_real_uid
    target_uid = get_real_uid()
    for filename in glob.iglob("/proc/*/exe"):
        pid_dir = os.path.dirname(filename)
        base = os.path.basename(pid_dir)
        if not base.isdigit():
            # skip /proc/self and /proc/thread-self
            continue
        pid = int(base)
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
                    stat_content = f.read()
                # comm is field 2, wrapped in parens, and may contain spaces
                name = stat_content[stat_content.index('(') + 1:
                                    stat_content.rindex(')')]
            except (OSError, ValueError):
                continue
        try:
            same_user = os.stat(pid_dir).st_uid == target_uid
        except OSError:
            # the process exited between listing and stat
            same_user = False
        yield ProcessInfo(pid, name, same_user)
        # argv[0] may differ from the exe name (e.g. a versioned binary
        # launched through a symlink)
        try:
            with open(os.path.join(pid_dir, 'cmdline'), 'rb') as f:
                argv0 = os.path.basename(
                    f.read().split(b'\x00')[0].decode('utf-8', 'replace'))
        except OSError:
            argv0 = ''
        if argv0 and argv0 != name:
            yield ProcessInfo(pid, argv0, same_user)


def _enumerate_ps_aux():
    """ps aux strategy (BSD/macOS)"""
    from bleachbit.General import (get_real_username, resolve_exe,
                                   sanitize_root_env)
    current_user = get_real_username()
    # sanitize the env so a hostile inherited LD_*/DYLD_* cannot redirect
    # this child when BleachBit runs as root.
    ps_out = subprocess.check_output(
        [resolve_exe('ps'), "aux", "-c"], universal_newlines=True,
        env=sanitize_root_env(dict(os.environ)))
    first_line = ps_out.split('\n', maxsplit=1)[0].strip()
    if "USER" not in first_line or "COMMAND" not in first_line:
        raise RuntimeError("Unexpected ps header format")
    for line in ps_out.split("\n")[1:]:
        # COMMAND is the last column and may contain spaces
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        yield ProcessInfo(int(parts[1]), parts[10].strip(), parts[0] == current_user)


class ProcessCache:

    """Cached way to determine whether a process is running"""

    def __init__(self, max_age_seconds=10):
        self.max_age_seconds = max_age_seconds
        self.last_scan_time = None
        self.processes = ()

    def invalidate(self):
        """Drop the cache so the next get() rescans"""
        self.last_scan_time = None
        self.processes = ()

    def get(self):
        """Return the process list, rescanning when stale.

        The scan expires so an application started mid-run is still noticed.
        """
        if self.last_scan_time is None or \
                (time.time() - self.last_scan_time) > self.max_age_seconds:
            self.processes = tuple(enumerate_processes())
            self.last_scan_time = time.time()
        return self.processes


process_cache = ProcessCache()


def is_process_running(exename, require_same_user):
    """Check whether exename is running"""
    ci = IS_WINDOWS  # case-insensitive on Windows
    if ci:
        exename = exename.lower()
    for proc in process_cache.get():
        name = proc.name.lower() if ci else proc.name
        if name == exename and (not require_same_user or proc.same_user):
            return True
    return False


def is_pid_running(pid, require_same_user):
    """Check whether a process with this PID is running"""
    return any(proc.pid == pid and (not require_same_user or proc.same_user)
               for proc in process_cache.get())


def terminate_process(exename, require_same_user):
    """Terminate processes matching exename. Returns list of affected PIDs."""
    ci = IS_WINDOWS
    if ci:
        exename = exename.lower()
    terminated = []
    # Not the cache: a stale PID may since have been recycled
    for proc in enumerate_processes():
        name = proc.name.lower() if ci else proc.name
        if name == exename and (not require_same_user or proc.same_user):
            if proc.pid in terminated:
                continue
            try:
                if IS_WINDOWS:
                    _import_psutil().Process(proc.pid).kill()
                else:
                    os.kill(proc.pid, signal.SIGTERM)
                terminated.append(proc.pid)
            except (ProcessLookupError, PermissionError, OSError):
                continue
    if terminated:
        process_cache.invalidate()
    return terminated
