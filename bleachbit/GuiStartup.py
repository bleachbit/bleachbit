# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import logging
import os
import stat
import sys
from importlib.util import find_spec

import bleachbit
from bleachbit import IS_MAC, IS_POSIX, IS_WINDOWS
from bleachbit.General import unset_sslkeylogfile
from bleachbit.Language import get_text as _
from bleachbit.Options import options

if IS_WINDOWS:
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
    # On FreeBSD, sqlite3 is a separate package.
    deps = ['psutil', 'requests', 'sqlite3', 'urllib3']
    if IS_WINDOWS:
        deps.append('plyer')

    # find_spec() avoids executing the modules just to test they exist
    missing = []
    for dep in deps:
        try:
            if find_spec(dep) is None:
                missing.append(dep)
        except (ImportError, ValueError):
            missing.append(dep)
    return sorted(missing)


def _get_posix_permission_issues(fstat, options_file):
    """Check POSIX-specific ownership and access issues.

    Returns (has_error, lines).
    """
    lines = []
    has_error = False
    import pwd  # pylint: disable=import-outside-toplevel
    from bleachbit.General import get_real_uid, get_real_username
    try:
        file_owner = pwd.getpwuid(fstat.st_uid).pw_name
    except (KeyError, OverflowError):
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
        if os.geteuid() == 0:
            lines.append('File owner does not match current user '
                         '(root can access regardless)')
        else:
            has_error = True
            lines.append('File owner does not match current user')
    # os.access checks
    lines.append(f'os.access R_OK: {os.access(options_file, os.R_OK)}')
    lines.append(f'os.access W_OK: {os.access(options_file, os.W_OK)}')
    return has_error, lines


def _lookup_account_name_or_sid(sid):
    """Resolve a SID to an account name and its string form.

    Returns ``(account_name, sid_str)``. ``sid_str`` is the canonical
    string representation of ``sid`` and is always returned, regardless
    of whether ``LookupAccountSid`` succeeds.

    Issue 2271 observed that ``LookupAccountSid`` failed when the SID
    belonged to an account from other Windows instance in dual-boot
    system with shared NTFS. In that case ``account_name`` falls back
    to ``sid_str`` so the ownership comparison can still proceed by SID.
    """
    if not IS_WINDOWS:
        raise RuntimeError("This function is only available on Windows")
    import win32security  # pylint: disable=import-outside-toplevel
    import pywintypes  # pylint: disable=import-outside-toplevel
    sid_str = win32security.ConvertSidToStringSid(sid)
    try:
        return win32security.LookupAccountSid(None, sid)[0], sid_str
    except pywintypes.error as e:
        logger.debug('LookupAccountSid failed (%s); falling back to SID string', e)
        return sid_str, sid_str


def _get_windows_user_info():
    """Get Windows user information.

    Returns (current_sid, current_name, token_groups).
    """
    if not IS_WINDOWS:
        raise RuntimeError("This function is only available on Windows")
    import win32api  # pylint: disable=import-outside-toplevel
    import win32file  # pylint: disable=import-outside-toplevel
    import win32security  # pylint: disable=import-outside-toplevel
    process_token = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        win32security.TOKEN_QUERY)
    current_sid = win32security.GetTokenInformation(
        process_token, win32security.TokenUser)[0]
    current_name, current_sid_str = _lookup_account_name_or_sid(current_sid)
    token_groups = win32security.GetTokenInformation(
        process_token, win32security.TokenGroups)
    win32file.CloseHandle(process_token)
    # Convert PySID objects to string representation for hashing
    group_sids = {win32security.ConvertSidToStringSid(
        g[0]) for g in token_groups}
    return current_sid_str, current_name, group_sids


def _get_windows_file_owner(filepath):
    """Get the owner of a file on Windows.

    Returns (owner_sid_str, owner_name).
    """
    if not IS_WINDOWS:
        raise RuntimeError("This function is only available on Windows")
    import win32security  # pylint: disable=import-outside-toplevel
    file_sd = win32security.GetFileSecurity(
        filepath, win32security.OWNER_SECURITY_INFORMATION)
    file_owner_sid = file_sd.GetSecurityDescriptorOwner()
    file_owner_name, file_owner_sid_str = _lookup_account_name_or_sid(
        file_owner_sid)
    return file_owner_sid_str, file_owner_name


def _get_windows_permission_issues(options_file):
    """Check Windows-specific ownership issues.

    Returns (has_error, lines).
    """
    if not IS_WINDOWS:
        raise RuntimeError("This function is only available on Windows")
    lines = []
    has_error = False
    try:
        file_owner_sid_str, file_owner_name = _get_windows_file_owner(
            options_file)
        current_sid, current_name, group_sids = _get_windows_user_info()
        lines.append(f'File owner: {file_owner_name}')
        lines.append(f'Current user: {current_name}')
        # Administrators owns the directory, and the created file inherits
        # from the owner. This is not representative of a normal installation.
        if 'GITHUB_ACTIONS' in os.environ and file_owner_name == 'Administrators':
            lines.append('Skipping file ownership check in CI')
            return False, lines
        if file_owner_sid_str != current_sid and file_owner_sid_str not in group_sids:
            if file_owner_name == file_owner_sid_str:
                # The file owner's SID could not be resolved to an account
                # name (e.g., issue #2271).
                lines.append(
                    'File owner SID could not be resolved to an account name '
                    '(may be from another Windows installation)')
            else:
                has_error = True
                lines.append('File owner does not match current user')
    except Exception as e:
        has_error = True
        lines.append(f'Could not check file ownership: {e}')
    return has_error, lines


def _get_config_permission_issues():
    """Check for permission and file access issues with the
    configuration.

    If no errors, returns False.
    If errors found, returns list of strings with info.
    """
    lines = []
    has_error = False

    _options_file = bleachbit.options_file
    _options_dir = bleachbit.options_dir

    try:
        with open(_options_file, 'rb') as f:
            f.read(1)
    except FileNotFoundError:
        # A missing configuration file is normal on first start and is
        # not a permission issue. The append test below verifies that
        # the file can be created/written.
        pass
    except (IOError, OSError, PermissionError) as e:
        has_error = True
        lines.append(f"Read error: {type(e).__name__}: {e}")

    try:
        with open(_options_file, 'a') as f:
            f.write('')
    except (IOError, OSError, PermissionError) as e:
        has_error = True
        lines.append(f"Write error: {type(e).__name__}: {e}")

    try:
        fstat = os.stat(_options_file)
        mode = stat.filemode(fstat.st_mode)
        lines.append(f'File: {_options_file}')
        lines.append(
            f'Permissions: {mode} ({oct(stat.S_IMODE(fstat.st_mode))})')
    except OSError as e:
        has_error = True
        lines.append(f'Cannot stat {_options_file}: {e}')

    # Directory info
    try:
        dstat = os.stat(_options_dir)
        dmode = stat.filemode(dstat.st_mode)
        lines.append(f'Directory: {_options_dir}')
        lines.append(
            f'Directory permissions: {dmode} ({oct(stat.S_IMODE(dstat.st_mode))})')
    except OSError as e:
        has_error = True
        lines.append(f'Cannot stat directory {_options_dir}: {e}')

    # File ownership vs current user
    if 'fstat' in locals():
        if IS_POSIX:
            _has_error, _lines = _get_posix_permission_issues(
                fstat, _options_file)
            has_error = has_error or _has_error
            lines.extend(_lines)
        elif IS_WINDOWS:
            _has_error, _lines = _get_windows_permission_issues(
                _options_file)
            has_error = has_error or _has_error
            lines.extend(_lines)

    if has_error:
        return lines
    return False


def _has_selected_warning_option():
    """Check if any selected cleaning option has a warning.

    Returns True if any selected option has a warning, False otherwise.
    """
    from bleachbit.Cleaner import backends  # pylint: disable=import-outside-toplevel
    if not backends:
        return False
    for cleaner_id, cleaner in backends.items():
        for (o_id, _o_name) in cleaner.get_options():
            if options.get_tree(cleaner_id, o_id):
                if cleaner.get_warning(o_id):
                    return True
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
            f'The configuration file {bleachbit.options_file} may have a permissions issue, so existing '
            'preferences might not be loaded, and changes may not be saved. If your preferences are saved, '
            'then you may ignore this error message or report it as a bad error message.\n\n'
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

    # Check if any selected cleaning option has a warning
    if not options.get('expert_mode') and _has_selected_warning_option():
        ret_msgs.append((
            # TRANSLATORS: "Expert Mode" is the name of a feature/setting found in
            # Preferences. Keep it consistent with the translation of "Expert Mode"
            # in the preferences dialog. This message appears when cleaning options
            # with warnings are selected but expert mode is disabled.
            _('One or more selected cleaning options have warnings and '
              'require Expert Mode to clean. Enable it in preferences.'), False))

    if not options.get('delete_confirmation') and not options.get('expert_mode'):
        ret_msgs.append((
            # TRANSLATORS: "Expert Mode" is the name of a feature/setting found in
            # Preferences. Keep it consistent with the translation of "Expert Mode"
            # in the preferences dialog. This message appears when the user tries to
            # skip a delete confirmation without enabling Expert Mode.
            _('Delete confirmation is disabled but expert mode is not enabled. '
              'Enable Expert Mode in preferences to skip delete confirmations.'), False))

    # Show information for first start.
    # (The first start flag is set also for each new version.)
    if options.get("first_start") and not auto_exit:
        if IS_POSIX:
            ret_msgs.append((
                # TRANSLATORS: First-start hint for Linux users shown in
                # the log on the main screen.
                _('Access the application menu by clicking the hamburger icon on the title bar.'), False))
        elif IS_WINDOWS:
            ret_msgs.append((
                # TRANSLATORS: First-start hint for Windows users shown in
                # the log on the main screen.
                _('Access the application menu by clicking the logo on the title bar.'), False))
        options.set('first_start', False)

    # Show notice about admin privileges.
    if IS_POSIX and os.path.expanduser('~') == '/root':
        ret_msgs.append((
            # TRANSLATORS: Warning shown on startup when running BleachBit as root on Linux.
            # It means, for example, that cleaning a browser will clean root's browser data.
            _('You are running BleachBit with administrative privileges for cleaning '
              'shared parts of the system, and references to the user profile folder '
              'will clean only the root account.'), False))
    if IS_WINDOWS:
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

    if IS_MAC:
        from bleachbit.Mac import is_full_disk_access_enabled
        if not is_full_disk_access_enabled():
            ret_msgs.append((
                # TRANSLATORS: Startup warning on macOS when the application
                # lacks Full Disk Access.
                _('Full Disk Access is not granted to BleachBit. macOS will '
                  'block access and some cleaners will not work. Grant Full '
                  'Disk Access to this application in System Settings > '
                  'Privacy & Security > Full Disk Access.'), True))

    return ret_msgs
