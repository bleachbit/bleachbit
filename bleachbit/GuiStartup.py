# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import os
import sys
from importlib import import_module

from bleachbit import options_file
from bleachbit.Language import get_text as _
from bleachbit.Network import unset_sslkeylogfile
from bleachbit.Options import is_config_writable, options

if os.name == 'nt':
    from bleachbit import Windows




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


def get_startup_messages(auto_exit):
    """Return a list of startup messages

    Can have a side effects
        - set first_start to False
        - unset environment variable

    Return: list of tuples (message, is_error) where is_error is True
    for error messages.
    """
    ret_msgs = []

    if not is_config_writable():
        ret_msgs.append((
            f'The configuration file {options_file} is not writable, so preferences will not '
            'be saved.', True))

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
