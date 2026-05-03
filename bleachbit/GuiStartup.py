# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import logging
import os
import stat
import sys
from importlib import import_module

from bleachbit import options_dir, options_file, IS_POSIX, IS_WINDOWS
from bleachbit.Language import get_text as _
from bleachbit.Network import unset_sslkeylogfile
from bleachbit.Options import options

if os.name == 'nt':
    from bleachbit import Windows

logger = logging.getLogger(__name__)


def _is_version_upgrade(old_version, target_version):
    """Check if upgrading from old_version to >= target_version"""
    try:
        old_parts = [int(x) for x in old_version.split('.')]
        target_parts = [int(x) for x in target_version.split('.')]

        # Pad shorter version with zeros
        max_len = max(len(old_parts), len(target_parts))
        old_parts.extend([0] * (max_len - len(old_parts)))
        target_parts.extend([0] * (max_len - len(target_parts)))

        # Check if old_version < target_version
        return old_parts < target_parts
    except (ValueError, AttributeError):
        return False


def _get_missing_dependencies():
    """Check for missing optional dependencies.

    Returns: list of missing dependency names
    """
    deps = ['chardet', 'psutil', 'requests', 'urllib3']
    if os.name == 'nt':
        deps.append('plyer')

    missing = []
    for dep in deps:
        try:
            import_module(dep)
        except ImportError:
            missing.append(dep)
    return sorted(missing)


def _get_config_permission_issues():
    """Check for permission and file access issues with the
    configuration.

    If no errors, returns False.
    If errors found, returns list of strings with info.
    """
    lines = []
    has_error = False

    try:
        with open(options_file, 'rb') as f:
            f.read(1)
    except (IOError, OSError, PermissionError) as e:
        has_error = True
        lines.append(f"Read error: {type(e).__name__}: {e}")

    try:
        with open(options_file, 'a') as f:
            f.write('')
    except (IOError, OSError, PermissionError) as e:
        has_error = True
        lines.append(f"Write error: {type(e).__name__}: {e}")

    try:
        fstat = os.stat(options_file)
        mode = stat.filemode(fstat.st_mode)
        lines.append(f'File: {options_file}')
        lines.append(
            f'Permissions: {mode} ({oct(stat.S_IMODE(fstat.st_mode))})')
    except OSError as e:
        has_error = True
        lines.append(f'Cannot stat {options_file}: {e}')

    # Directory info
    try:
        dstat = os.stat(options_dir)
        dmode = stat.filemode(dstat.st_mode)
        lines.append(f'Directory: {options_dir}')
        lines.append(
            f'Directory permissions: {dmode} ({oct(stat.S_IMODE(dstat.st_mode))})')
    except OSError as e:
        has_error = True
        lines.append(f'Cannot stat directory {options_dir}: {e}')

    # File ownership vs current user
    if IS_POSIX:
        import pwd  # pylint: disable=import-outside-toplevel
        from bleachbit.General import get_real_uid, get_real_username
        try:
            file_owner = pwd.getpwuid(fstat.st_uid).pw_name
        except (KeyError, OverflowError):
            has_error = True
            file_owner = str(fstat.st_uid)
        current_uid = get_real_uid()
        try:
            current_user = get_real_username()
        except RuntimeError:
            has_error = True
            current_user = str(current_uid)
        lines.append(f'File owner: {file_owner} (uid {fstat.st_uid})')
        lines.append(f'Current user: {current_user} (uid {current_uid})')
        if fstat.st_uid != current_uid:
            has_error = True
            lines.append('File owner does not match current user')
        # os.access checks
        lines.append(f'os.access R_OK: {os.access(options_file, os.R_OK)}')
        lines.append(f'os.access W_OK: {os.access(options_file, os.W_OK)}')
    elif IS_WINDOWS:
        try:
            import win32security  # pylint: disable=import-outside-toplevel
            file_sd = win32security.GetFileSecurity(
                options_file, win32security.OWNER_SECURITY_INFORMATION)
            file_owner_sid = file_sd.GetSecurityDescriptorOwner()
            file_owner_name = win32security.LookupAccountSid(
                None, file_owner_sid)[0]
            process_token = win32security.OpenProcessToken(
                win32security.GetCurrentProcess(),
                win32security.TOKEN_QUERY)
            token_user = win32security.GetTokenInformation(
                process_token, win32security.TokenUser)
            current_sid = token_user[0]
            current_name = win32security.LookupAccountSid(
                None, current_sid)[0]
            import win32file  # pylint: disable=import-outside-toplevel
            win32file.CloseHandle(process_token)
            lines.append(f'File owner: {file_owner_name}')
            lines.append(f'Current user: {current_name}')
            if file_owner_sid != current_sid:
                has_error = True
                lines.append('File owner does not match current user')
        except Exception as e:
            has_error = True
            lines.append(f'Could not check file ownership: {e}')

    if has_error:
        return lines
    return False


def get_startup_messages(auto_exit):
    """Return a list of startup messages

    Can have a side effects
        - set first_start to False
        - unset environment variable

    Return: list of tuples (message, is_error) where is_error is True
    for error messages.
    """
    ret_msgs = []

    perm_issues_list = _get_config_permission_issues()
    if perm_issues_list:
        perm_issues_str = '\n'.join(perm_issues_list)
        ret_msgs.append((
            f'The configuration file {options_file} has a permissions issue, so existing '
            'preferences might not be loaded, and changes may not be saved.\n\n'
            f'{perm_issues_str}', True))

    missing_deps = _get_missing_dependencies()

    if missing_deps:
        ret_msgs.append((
            f'Missing optional Python packages: {", ".join(missing_deps)}. '
            'Some features may be limited.', True))

    # Call unset_sslkeylogfile before checking for updates.
    if unset_sslkeylogfile(False):
        ret_msgs.append((
            'The environment variable SSLKEYLOGFILE is not supported', True))

    # Show version update advice for upgrades from <5.1.0 to >=5.1.0
    old_version = options.get_old_version()
    if old_version and _is_version_upgrade(old_version, "5.1.0"):
        ret_msgs.append((
            # TRANSLATORS: Update notification for users upgrading from versions
            # older than 5.1.0.
            _('Cleaning options with warnings now require expert mode. Enable it in '
              'preferences to clean them.'), False))

    # Show information for first start.
    # (The first start flag is set also for each new version.)
    if options.get("first_start") and not auto_exit:
        if os.name == 'posix':
            ret_msgs.append((
                # TRANSLATORS: First-start hint for Linux users shown in
                # the log on the main screen.
                _('Access the application menu by clicking the hamburger icon on the title bar.'), False))
        elif os.name == 'nt':
            ret_msgs.append((
                # TRANSLATORS: First-start hint for Windows users shown in
                # the log on the main screen.
                _('Access the application menu by clicking the logo on the title bar.'), False))
        options.set('first_start', False)

    # Show notice about admin privileges.
    if os.name == 'posix' and os.path.expanduser('~') == '/root':
        ret_msgs.append((
            # TRANSLATORS: Warning shown on startup when running BleachBit as root on Linux.
            # It means, for example, that cleaning a browser will clean root's browser data.
            _('You are running BleachBit with administrative privileges for cleaning '
              'shared parts of the system, and references to the user profile folder '
              'will clean only the root account.'), False))
    if os.name == 'nt':
        from win32com.shell.shell import IsUserAnAdmin
        if options.get('shred') and not IsUserAnAdmin():
            ret_msgs.append((
                # TRANSLATORS: Warning shown on startup on Windows.
                _('Run BleachBit with administrator privileges to improve the '
                  'accuracy of overwriting the contents of files.'), False))
        if Windows.is_ots_elevation():
            ret_msgs.append((
                # TRANSLATORS: Warning shown on startup on Windows when elevated
                # with different account. It means, for example, that cleaning a
                # browser will clean the browser data of the administrator account.
                _('You elevated privileges using a different account to clean '
                  'shared parts of the system. User-specific paths will refer to '
                  'the administrator account, so to clean your profile, run '
                  'BleachBit again as a standard user.'), False))

        if 'windowsapps' in sys.executable.lower():
            ret_msgs.append((
                # TRANSLATORS: Warning shown on startup on Windows when running
                # unofficial Microsoft Store version. Advises user to get genuine
                # version from official website.
                _('There is no official version of BleachBit on the Microsoft Store. '
                  'Get the genuine version at https://www.bleachbit.org where it is '
                  'always free of charge.'), False))

    return ret_msgs
