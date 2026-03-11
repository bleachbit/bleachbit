# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import os
import sys

from bleachbit.Language import get_text as _
from bleachbit.Network import unset_sslkeylogfile
from bleachbit.Options import options

if os.name == 'nt':
    from bleachbit import Windows


def get_startup_messages(auto_exit):
    """Return a list of startup messages

    Can have a side effects
        - set first_start to False
        - unset environment variable

    Return: list of tuples (message, is_error) where is_error is True
    for error messages.
    """
    ret_msgs = []

    # Call unset_sslkeylogfile before checking for updates.
    if unset_sslkeylogfile(False):
        ret_msgs.append((
            'The environment variable SSLKEYLOGFILE is not supported', True))

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
