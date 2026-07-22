# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Targeted diagnostics for "Access denied" errors on Windows (issue #2233).

This module runs a focused set of tests and returns lines of text via a
callback so the GUI can display them with ``append_text()``.  The goal is
to collect enough information to identify whether the root cause is:

  * ACL / permission mismatch (WinError 5)
  * File locking by a running browser process (WinError 32)
  * BleachBit running elevated while browser data belongs to a different user
  * Security software blocking deletes in browser data directories

No source changes are made to the cleaning logic itself — this is purely
diagnostic.
"""

import os
import re
import stat
import tempfile

from bleachbit import IS_WINDOWS


def run_diagnostics(log):
    """Run all diagnostic tests, calling ``log(text)`` for each line.

    Args:
        log: callable(str) — typically ``self.append_text`` on the GUI.
    """
    _log_system_information(log)
    _log_current_user_and_elevation(log)
    _log_browser_processes(log)
    if IS_WINDOWS:
        _log_security_software(log)
        _log_file_permission_tests(log)
        _log_sqlite_open_tests(log)
    else:
        log("File permission and SQLite tests are Windows-only. Skipping.\n")
    log("\n=== Diagnostics Complete ===\n")
    log("Please copy this log (use the Copy Log button) and paste it into "
        "the issue: https://github.com/bleachbit/bleachbit/issues/2233\n",
        'error')


def _log_system_information(log):
    """Print system information including BleachBit version and OS."""
    log("\n--- System Information ---\n")
    try:
        from bleachbit.SystemInformation import get_system_information
        log(get_system_information() + "\n")
    except Exception as e:
        log(f"Error getting system information: {e}\n", 'error')


def _log_current_user_and_elevation(log):
    """Print the current process user and whether the process is elevated."""
    log("\n--- Current User & Elevation ---\n")
    if not IS_WINDOWS:
        try:
            import getpass
            log(f"Current user: {getpass.getuser()}\n")
        except Exception as e:
            log(f"Error checking user: {e}\n", 'error')
        return
    try:
        import win32api
        import win32security
        token = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
        sid, _ = win32security.GetTokenInformation(
            token, win32security.TokenUser)
        sid_str = win32security.ConvertSidToStringSid(sid)
        username = win32security.LookupAccountSid(None, sid)[0]
        log(f"Current user: {username}\n")
        log(f"Current user SID: {sid_str}\n")
        try:
            elevation = win32security.GetTokenInformation(
                token, win32security.TokenElevation)
            is_elevated = bool(elevation[0]) if elevation else False
            log(f"Process elevated (UAC): {is_elevated}\n")
        except Exception as e:
            log(f"Could not check elevation: {e}\n")
        # Also check the "real" user when running under sudo-for-Windows
        try:
            from bleachbit.General import get_real_username
            real_user = get_real_username()
            if real_user and real_user != username:
                log(f"Real (non-elevated) user: {real_user}\n")
        except Exception:
            pass
    except Exception as e:
        log(f"Error checking Windows user/elevation: {e}\n", 'error')


def _log_browser_processes(log):
    """Enumerate running browser processes with PID, name, and user."""
    log("\n--- Browser Processes ---\n")
    browser_re = re.compile(r'chrome|firefox|edge|msedgewebview|brave',
                            re.IGNORECASE)
    found = False
    try:
        from bleachbit.Process import enumerate_processes
        import psutil
        for proc in enumerate_processes():
            if not browser_re.search(proc.name):
                continue
            found = True
            try:
                username = psutil.Process(proc.pid).username()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                username = "same user" if proc.same_user else "other user"
            log(f"  PID {proc.pid}: {proc.name} (user: {username})\n")
    except Exception as e:
        log(f"Error enumerating processes: {e}\n", 'error')
    if not found:
        log("  No browser processes found.\n")


# Security software process-name fragments. Not exhaustive — we are
# looking for anything that might intercept file deletes.
_AV_PROCESS_KEYWORDS = (
    'defender', 'msmpeng', 'avast', 'avg', 'norton', 'kaspersky',
    'mcafee', 'bitdefender', 'eset', 'malwarebytes', 'mbam',
    'f-secure', 'sophos', 'trendmicro', 'avira', 'comodo',
    'emsisoft', 'gdata', 'panda', 'voodooshield', 'webroot',
    'zonealarm', '360tray', 'bdredline', 'clamd', 'immunet',
    'spybot', 'adaware', 'spyshelter', 'zemana',
)


def _log_security_software(log):
    """Detect installed/running security software that may block deletes.

    AV/filter-driver products are a strong candidate for issue #2233
    because they intercept file operations and can return ACCESS_DENIED
    even when the file's DACL allows the current user to delete it.
    On-demand scanners are particularly suspect because they activate
    when a file is touched, which would explain why Preview (which only
    lists files) succeeds while Clean (which opens/deletes files) fails.
    """
    log("\n--- Security Software ---\n")
    _log_av_products_wmi(log)
    _log_security_processes(log)
    _log_defender_status(log)


def _log_av_products_wmi(log):
    """List registered AV products via WMI SecurityCenter2."""
    try:
        import win32com.client
        locator = win32com.client.Dispatch('WbemScripting.SWbemLocator')
        server = locator.ConnectServer('.', r'root\SecurityCenter2')
        products = server.ExecQuery('SELECT * FROM AntiVirusProduct')
        count = 0
        for p in products:
            count += 1
            log(f"  Registered AV: {p.displayName}\n")
            try:
                log(f"    productState: {p.productState}\n")
            except Exception:
                pass
            try:
                log(f"    pathToSignedProductExe: "
                    f"{p.pathToSignedProductExe}\n")
            except Exception:
                pass
            try:
                log(f"    pathToSignedReportingExe: "
                    f"{p.pathToSignedReportingExe}\n")
            except Exception:
                pass
        if count == 0:
            log("  No AV products registered via SecurityCenter2.\n")
    except Exception as e:
        log(f"  WMI SecurityCenter2 query failed: {e}\n", 'error')


def _log_security_processes(log):
    """List running processes whose names match known AV/security tools."""
    try:
        import subprocess
        result = subprocess.run(
            ['tasklist', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10)
        found = set()
        for line in result.stdout.splitlines():
            parts = line.split('"')
            if len(parts) < 2:
                continue
            name = parts[1].lower()
            for kw in _AV_PROCESS_KEYWORDS:
                if kw in name:
                    found.add(name)
                    break
        if found:
            log("  Security-related processes running:\n")
            for name in sorted(found):
                log(f"    {name}\n")
        else:
            log("  No common security software processes found.\n")
    except Exception as e:
        log(f"  Error listing security processes: {e}\n", 'error')


def _log_defender_status(log):
    """Check Windows Defender real-time protection and exclusions."""
    log("\n  Windows Defender details:\n")
    # Real-time protection status
    try:
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows Defender\Real-Time Protection')
            try:
                val, _ = winreg.QueryValueEx(
                    key, 'DisableRealtimeMonitoring')
                state = 'DISABLED' if val else 'ENABLED'
                log(f"    Real-time protection: {state}\n")
            except FileNotFoundError:
                log("    Real-time protection: ENABLED (default)\n")
            winreg.CloseKey(key)
        except PermissionError:
            log("    Real-time protection: (registry access denied)\n",
                'error')
    except Exception as e:
        log(f"    Error reading Defender status: {e}\n", 'error')
    # Exclusions (requires admin — log access denied if not elevated)
    try:
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths')
            i = 0
            excluded = []
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    excluded.append(name)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            if excluded:
                log("    Excluded paths:\n")
                for p in excluded:
                    log(f"      {p}\n")
            else:
                log("    Excluded paths: (none)\n")
        except PermissionError:
            log("    Excluded paths: (registry access denied — "
                "not elevated)\n", 'error')
        except FileNotFoundError:
            log("    Excluded paths: (key not found)\n")
    except Exception as e:
        log(f"    Error reading Defender exclusions: {e}\n", 'error')


# ---------------------------------------------------------------------------
# Windows-specific file and SQLite tests
# ---------------------------------------------------------------------------

def _get_browser_data_dirs():
    """Return list of (label, path) for known browser data directories."""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        return []
    return [
        ('Edge',
         os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data',
                      'Default')),
        ('Chrome',
         os.path.join(local_app_data, 'Google', 'Chrome', 'User Data',
                      'Default')),
        ('Firefox profiles',
         os.path.join(local_app_data, 'Mozilla', 'Firefox', 'Profiles')),
    ]


def _get_firefox_profile_dirs():
    """Return list of Firefox profile directories under the Profiles root."""
    profiles_root = os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.isdir(profiles_root):
        return []
    import glob
    return sorted(glob.glob(os.path.join(profiles_root, '*')))


def _dump_file_security(filepath, log, current_sid_str=None):
    """Print owner and DACL for a Windows file.

    Returns True if the current user (matching current_sid_str) has an
    ALLOW ACE granting DELETE access; False otherwise; None if unknown.
    """
    current_user_has_delete = False
    try:
        import win32security
        import win32con
        sd = win32security.GetFileSecurity(
            filepath,
            win32security.OWNER_SECURITY_INFORMATION
            | win32security.DACL_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        owner_name, owner_domain, _ = win32security.LookupAccountSid(
            None, owner_sid)
        owner_sid_str = win32security.ConvertSidToStringSid(owner_sid)
        log(f"    Owner: {owner_domain}\\{owner_name} (SID: {owner_sid_str})\n")
        dacl = sd.GetSecurityDescriptorDacl()
        if dacl is None:
            log("    DACL: (null — no ACL, full access to everyone)\n")
            return
        ace_count = dacl.GetAceCount()
        log(f"    DACL entries ({ace_count}):\n")
        for i in range(ace_count):
            ace = dacl.GetAce(i)
            # ACE tuple format varies by pywin32 version and ACL revision.
            # Observed formats:
            #   ((type, flags), mask, sid)  — 3 elements (current pywin32)
            #   (type, flags, mask, sid)    — 4 elements (older docs)
            # The last element is always the SID, and the mask is the
            # second-to-last. The first element/elements carry type+flags.
            ace_sid = ace[-1]
            mask = ace[-2]
            head = ace[:-2]
            if isinstance(head[0], (tuple, list)):
                ace_type, ace_flags = head[0]
            else:
                ace_type, ace_flags = head[0], head[1] if len(head) > 1 else 0
            try:
                account, domain, _ = win32security.LookupAccountSid(
                    None, ace_sid)
                sid_str = win32security.ConvertSidToStringSid(ace_sid)
                acct_label = f"{domain}\\{account}"
            except Exception:
                sid_str = win32security.ConvertSidToStringSid(ace_sid)
                acct_label = sid_str
            # Decode common permission bits
            perms = []
            if mask & win32con.DELETE:
                perms.append('DELETE')
            if mask & win32con.READ_CONTROL:
                perms.append('READ_CONTROL')
            if mask & win32con.WRITE_DAC:
                perms.append('WRITE_DAC')
            if mask & win32con.WRITE_OWNER:
                perms.append('WRITE_OWNER')
            if mask & 0x10000:  # GENERIC_READ
                perms.append('GENERIC_READ')
            if mask & 0x20000:  # GENERIC_WRITE
                perms.append('GENERIC_WRITE')
            if mask & 0x40000:  # GENERIC_EXECUTE
                perms.append('GENERIC_EXECUTE')
            if mask & 0x80000000:  # GENERIC_ALL
                perms.append('GENERIC_ALL')
            ace_type_name = {
                0: 'ALLOW', 1: 'DENY', 2: 'AUDIT'
            }.get(ace_type, str(ace_type))
            log(f"      [{i}] {ace_type_name} {acct_label}: "
                f"{', '.join(perms) or hex(mask)}\n")
            # Track whether the current user has an ALLOW DELETE ACE.
            if (ace_type == 0 and current_sid_str
                    and sid_str == current_sid_str
                    and (mask & win32con.DELETE
                         or mask & 0x80000000)):  # GENERIC_ALL
                current_user_has_delete = True
    except Exception as e:
        log(f"    Could not read security info: {e}\n", 'error')
    return current_user_has_delete


def _test_temp_file_in_dir(dirpath, log):
    """Try to create and delete a temp file in dirpath.

    This tests whether the directory allows write+delete for the current
    user, independent of any specific browser file.
    """
    try:
        fd, tmppath = tempfile.mkstemp(
            prefix='bb_diag_', suffix='.tmp', dir=dirpath)
        os.close(fd)
        log(f"    Create temp file: OK ({tmppath})\n")
    except PermissionError as e:
        winerr = getattr(e, 'winerror', None)
        log(f"    Create temp file: FAILED (WinError {winerr}: {e})\n",
            'error')
        return
    except OSError as e:
        winerr = getattr(e, 'winerror', None)
        log(f"    Create temp file: FAILED (WinError {winerr}: {e})\n",
            'error')
        return
    try:
        os.remove(tmppath)
        log(f"    Delete temp file: OK\n")
    except PermissionError as e:
        winerr = getattr(e, 'winerror', None)
        log(f"    Delete temp file: FAILED (WinError {winerr}: {e})\n",
            'error')
    except OSError as e:
        winerr = getattr(e, 'winerror', None)
        log(f"    Delete temp file: FAILED (WinError {winerr}: {e})\n",
            'error')


def _test_delete_existing_file(filepath, log):
    """Try to open an existing file with DELETE access and log the WinError.

    We do NOT actually want to delete the user's files — instead we test
    whether we *could* by opening with DELETE access and closing.

    Returns the WinError code on failure, or None on success.
    """
    try:
        import win32file
        import win32con
        # Open with DELETE access but don't actually delete.
        handle = win32file.CreateFileW(
            filepath,
            win32con.DELETE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
            | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None)
        win32file.CloseHandle(handle)
        log(f"    Open with DELETE access: OK (file is deletable)\n")
        return None
    except Exception as e:
        winerr = getattr(e, 'winerror', None)
        log(f"    Open with DELETE access: FAILED "
            f"(WinError {winerr}: {e})\n", 'error')
        return winerr


def _log_file_permission_tests(log):
    """Run file permission tests on each browser data directory."""
    log("\n--- File Permission Tests ---\n")
    # Capture current user SID once for the contradiction check below.
    current_sid_str = None
    try:
        import win32api
        import win32security
        token = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
        sid, _ = win32security.GetTokenInformation(
            token, win32security.TokenUser)
        current_sid_str = win32security.ConvertSidToStringSid(sid)
    except Exception:
        pass
    for label, dirpath in _get_browser_data_dirs():
        log(f"\n[{label}] {dirpath}\n")
        if not os.path.isdir(dirpath):
            log("  Directory does not exist. Skipping.\n")
            continue
        # Test 1: create + delete a temp file in the directory
        log("  Test: create+delete temp file in directory:\n")
        _test_temp_file_in_dir(dirpath, log)
        # Test 2: find a sample existing file and dump its security
        sample = _find_sample_file(dirpath)
        if sample:
            log(f"  Sample file: {sample}\n")
            try:
                fstat = os.stat(sample)
                mode = stat.filemode(fstat.st_mode)
                log(f"    stat mode: {mode} "
                    f"({oct(stat.S_IMODE(fstat.st_mode))})\n")
            except OSError as e:
                log(f"    stat failed: {e}\n", 'error')
            has_delete = _dump_file_security(
                sample, log, current_sid_str)
            winerr = _test_delete_existing_file(sample, log)
            _check_av_contradiction(has_delete, winerr, log)
        else:
            log("  No sample file found in directory.\n")
        # For Firefox, iterate profile subdirectories
        if label == 'Firefox profiles':
            for prof_dir in _get_firefox_profile_dirs():
                log(f"\n  [Firefox profile] {prof_dir}\n")
                log("  Test: create+delete temp file:\n")
                _test_temp_file_in_dir(prof_dir, log)
                prof_sample = _find_sample_file(prof_dir)
                if prof_sample:
                    log(f"  Sample file: {prof_sample}\n")
                    has_delete = _dump_file_security(
                        prof_sample, log, current_sid_str)
                    winerr = _test_delete_existing_file(
                        prof_sample, log)
                    _check_av_contradiction(has_delete, winerr, log)


def _check_av_contradiction(has_delete_permission, open_winerror, log):
    """Flag the signature of AV/filter-driver blocking.

    If the DACL says the current user has an ALLOW DELETE ACE, but
    opening the file with DELETE access fails with WinError 5
    (ERROR_ACCESS_DENIED), something is intercepting the operation
    between the ACL check and the file open — most likely a security
    filter driver (AV/EDR). This is the strongest indicator that
    security software, not permissions or file locking, is the cause.
    """
    if has_delete_permission and open_winerror == 5:
        log("    *** CONTRADICTION DETECTED: DACL grants DELETE to "
            "current user, but Open with DELETE failed with WinError 5.\n",
            'error')
        log("    *** This strongly suggests a security filter driver "
            "(AV/EDR) is intercepting file operations.\n", 'error')
        log("    *** Check the Security Software section above and "
            "consider adding BleachBit to AV exclusions.\n", 'error')


def _find_sample_file(dirpath):
    """Return path of a regular file in dirpath, or None."""
    try:
        for entry in os.listdir(dirpath):
            full = os.path.join(dirpath, entry)
            if os.path.isfile(full):
                return full
    except (PermissionError, OSError):
        return None
    return None


def _log_sqlite_open_tests(log):
    """Try opening known SQLite databases and log the result."""
    log("\n--- SQLite Open Tests ---\n")
    try:
        import sqlite3
    except ImportError:
        log("sqlite3 module not available.\n", 'error')
        return
    # Collect candidate database paths
    candidates = []
    for label, dirpath in _get_browser_data_dirs():
        if not os.path.isdir(dirpath):
            continue
        if label == 'Firefox profiles':
            for prof_dir in _get_firefox_profile_dirs():
                for db in ('cookies.sqlite', 'places.sqlite',
                           'formhistory.sqlite'):
                    p = os.path.join(prof_dir, db)
                    if os.path.exists(p):
                        candidates.append((f"Firefox/{db}", p))
        else:
            for db in ('Cookies', 'History', 'Web Data', 'Favicons',
                       'Top Sites', 'Shortcuts'):
                p = os.path.join(dirpath, db)
                if os.path.exists(p):
                    candidates.append((f"{label}/{db}", p))
    if not candidates:
        log("  No SQLite databases found in browser data directories.\n")
        return
    for label, dbpath in candidates:
        log(f"\n  [{label}] {dbpath}\n")
        log(f"    exists: {os.path.exists(dbpath)}, "
            f"size: {os.path.getsize(dbpath) if os.path.exists(dbpath) else 'N/A'} bytes\n")
        # Test 1: plain connect (how execute_sqlite3 does it)
        try:
            conn = sqlite3.connect(dbpath)
            conn.execute('SELECT 1 FROM sqlite_master LIMIT 1')
            conn.close()
            log("    plain sqlite3.connect(): OK\n")
        except Exception as e:
            log(f"    plain sqlite3.connect(): FAILED ({e})\n", 'error')
        # Test 2: URI read-only (how _get_sqlite_values does it)
        try:
            from urllib.parse import quote
            abs_path = os.path.abspath(dbpath).replace('\\', '/')
            uri = f'file:{quote(abs_path, safe="/:")}?mode=ro'
            conn = sqlite3.connect(uri, uri=True)
            conn.execute('SELECT 1 FROM sqlite_master LIMIT 1')
            conn.close()
            log(f"    URI read-only: OK ({uri})\n")
        except Exception as e:
            log(f"    URI read-only: FAILED ({e})\n", 'error')
        # Test 3: old-style URI (with backslashes, as the pre-fix code did)
        try:
            old_uri = f'file:{dbpath}?mode=ro'
            conn = sqlite3.connect(old_uri, uri=True)
            conn.execute('SELECT 1 FROM sqlite_master LIMIT 1')
            conn.close()
            log(f"    old-style URI (backslashes): OK\n")
        except Exception as e:
            log(f"    old-style URI (backslashes): FAILED ({e})\n",
                'error')
