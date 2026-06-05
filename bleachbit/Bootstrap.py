# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Prepare to start the application
"""

import getpass
import os
import re
import sys

from bleachbit import IS_POSIX, IS_WINDOWS

# pylint: disable=invalid-name
_bootstrapped = False


def _apply_fontconfig_backend_preference():
    """On Windows, set PANGOCAIRO_BACKEND=fc if the user chose fontconfig.

    It is important that this runs before Gtk.
    """
    if not IS_WINDOWS:
        return
    try:
        from bleachbit.Options import options  # pylint: disable=import-outside-toplevel
        if options.get('use_fontconfig_backend'):
            os.environ['PANGOCAIRO_BACKEND'] = 'fc'
    except Exception:
        pass


def check_wayland_and_root():
    """Check if Wayland is being used and root is not allowed.

    Returns True if there is a problem
    False if no problem (e.g., not root, not Wayland)
    """
    if not IS_POSIX:
        return False

    # The two imports from bleachbit must come after sys.path is adjusted.
    import bleachbit.Unix  # pylint: disable=import-outside-toplevel
    from bleachbit.Language import get_text as _  # pylint: disable=import-outside-toplevel

    # FIXME: if started from launcher (.desktop file), there may be no console
    # to which to print this message.
    if bleachbit.Unix.is_display_protocol_wayland_and_root_not_allowed():
        print(_('To run a GUI application on Wayland with root, allow access with this command:\n'
              'xhost si:localuser:root\n'
                'See more about xhost at https://docs.bleachbit.org/doc/frequently-asked-questions.html'), file=sys.stderr)
        return True
    return False


def _bootstrap_posix():
    """Bootstrap for POSIX systems"""
    # os.path.expanduser('~') returns '~' unchanged when HOME is unset
    # and the user has no passwd entry (e.g., Docker containers).
    from bleachbit import _home_dir, logger
    home_dir = _home_dir()
    if not os.getenv('HOME') and home_dir == '/tmp':
        logger.warning('HOME not set and no passwd entry; using %s', home_dir)

    # Set fallbacks for environment variables.
    envs = {
        'HOME': home_dir,
        'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
        'XDG_CACHE_HOME': os.path.join(home_dir, '.cache'),
        'XDG_CONFIG_HOME': os.path.join(home_dir, '.config'),
        'XDG_DATA_HOME': os.path.join(home_dir, '.local', 'share')
    }
    if not os.getenv('USER'):
        try:
            envs['USER'] = getpass.getuser()
        except (OSError, KeyError):
            pass
    for varname, value in envs.items():
        if not os.getenv(varname):
            os.environ[varname] = value


def _bootstrap_windows():
    """Bootstrap for Windows"""
    from bleachbit import Windows
    Windows.setup_environment()

    # Use our `font.conf` (see commit 3385952b37d78).
    os.environ.pop('FONTCONFIG_FILE', None)

    # change error handling to avoid popup with GTK 3
    # https://github.com/bleachbit/bleachbit/issues/651
    import win32api  # pylint: disable=import-error
    import win32con  # pylint: disable=import-error
    win32api.SetErrorMode(win32con.SEM_FAILCRITICALERRORS |
                          win32con.SEM_NOGPFAULTERRORBOX | win32con.SEM_NOOPENFILEERRORBOX)

    # Set GDK_PIXBUF_MODULE_FILE based on the Python DLL location.
    # This ensures GTK can find the pixbuf loaders when running from
    # a bundled/frozen environment where the standard paths may not apply.
    import win32process
    for process in win32process.EnumProcessModules(-1):
        name = win32process.GetModuleFileNameEx(-1, process)
        if re.search(r'python\d+.dll$', name, re.IGNORECASE):
            bindir = os.path.dirname(name)
            os.environ['GDK_PIXBUF_MODULE_FILE'] = os.path.join(
                bindir, 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')


def bootstrap():
    """Bootstrap the application"""
    global _bootstrapped  # pylint: disable=global-statement
    if _bootstrapped:
        return
    _bootstrapped = True
    _apply_fontconfig_backend_preference()
    if IS_WINDOWS:
        _bootstrap_windows()
    elif IS_POSIX:
        _bootstrap_posix()
