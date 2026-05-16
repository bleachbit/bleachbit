#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Launcher
"""

import os
import sys

have_gui = True


def _add_posix_share_to_path():
    """Add the appropriate share directory to sys.path for POSIX systems."""
    _launcher_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if running from source directory
    if (os.path.isfile(os.path.join(_launcher_dir, 'bleachbit', '__init__.py')) and
            os.path.isfile(os.path.join(_launcher_dir, 'bleachbit', 'Unix.py'))):
        return

    # AppImage sets APPDIR environment variable
    _appdir = os.environ.get('APPDIR')
    if _appdir:
        _share = os.path.normpath(os.path.join(_appdir, 'usr/share/'))
        if os.path.isfile(os.path.join(_share, 'bleachbit', '__init__.py')):
            sys.path.insert(0, _share)
            return

    # System installation
    if os.path.isfile('/usr/share/bleachbit/__init__.py'):
        sys.path.append('/usr/share/')


def _apply_fontconfig_backend_preference():
    """On Windows, set PANGOCAIRO_BACKEND=fc if the user chose fontconfig.

    It is important that this runs before Gtk.
    """
    if os.name != 'nt':
        return
    try:
        from bleachbit.Options import options
        if options.get('use_fontconfig_backend'):
            os.environ['PANGOCAIRO_BACKEND'] = 'fc'
    except Exception:
        pass


_apply_fontconfig_backend_preference()

if 'posix' == os.name:
    _add_posix_share_to_path()

    # The two imports from bleachbit must come after sys.path is adjusted.
    import bleachbit.Unix
    from bleachbit.Language import get_text as _

    if (
        bleachbit.Unix.is_display_protocol_wayland_and_root_not_allowed()
    ):
        print(_('To run a GUI application on Wayland with root, allow access with this command:\n'
              'xhost si:localuser:root\n'
                'See more about xhost at https://docs.bleachbit.org/doc/frequently-asked-questions.html'))
        sys.exit(1)
    # Check for GUI only when needed: this avoids a Gtk warning when
    # a display is not available.
    if len(sys.argv) == 1 or '--gui' in sys.argv:
        from bleachbit.GtkShim import HAVE_GTK
        have_gui = HAVE_GTK
    else:
        have_gui = False

if os.name == 'nt':
    # change error handling to avoid popup with GTK 3
    # https://github.com/bleachbit/bleachbit/issues/651
    import win32api  # pylint: disable=import-error
    import win32con  # pylint: disable=import-error
    win32api.SetErrorMode(win32con.SEM_FAILCRITICALERRORS |
                          win32con.SEM_NOGPFAULTERRORBOX | win32con.SEM_NOOPENFILEERRORBOX)

# Use GUI if no arguments provided and display is available
if 1 == len(sys.argv) and have_gui:
    # Import GUI inside the condition for Linux packagers to
    # separate GUI into another package.
    import bleachbit.GuiApplication  # pylint: disable=ungrouped-imports
    app = bleachbit.GuiApplication.Bleachbit()
    sys.exit(app.run(sys.argv))
else:
    # Either CLI args were provided or no display is available
    import bleachbit.CLI
    # If no args and defaulting to CLI, print usage information
    if 1 == len(sys.argv) and not have_gui:
        sys.argv.append('--help')
    bleachbit.CLI.process_cmd_line()
