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


def _add_posix_share_to_path():
    """Setup path on POSIX systems for AppImage"""
    if os.name != 'posix':
        return
    # Add the appropriate share directory to sys.path so we can import bleachbit.
    # This must happen before importing from bleachbit.Bootstrap.
    #
    _launcher_dir = os.path.dirname(os.path.abspath(__file__))
    if not (os.path.isfile(os.path.join(_launcher_dir, 'bleachbit', '__init__.py')) and
            os.path.isfile(os.path.join(_launcher_dir, 'bleachbit', 'Unix.py'))):
        _appdir = os.environ.get('APPDIR')
        if _appdir:
            _share = os.path.normpath(os.path.join(_appdir, 'usr/share/'))
            if os.path.isfile(os.path.join(_share, 'bleachbit', '__init__.py')):
                sys.path.insert(0, _share)
        elif os.path.isfile('/usr/share/bleachbit/__init__.py'):
            sys.path.append('/usr/share/')


def main():
    """Main entry point"""
    _add_posix_share_to_path()
    from bleachbit.Bootstrap import bootstrap, check_wayland_and_root
    bootstrap()

    # Check for GUI only when needed: this avoids a Gtk warning when
    # a display is not available.
    if len(sys.argv) == 1 or '--gui' in sys.argv:
        from bleachbit.GtkShim import is_gtk_available
        have_gui = is_gtk_available()
    else:
        have_gui = False

    # If no arguments provided and display is available, then
    # assume the user wants to start the GUI.
    # If Wayland is a problem and no explicit CLI args were provided,
    # then fall back to CLI.
    if 1 == len(sys.argv) and have_gui and not check_wayland_and_root():
        # Import GUI inside the condition for Linux packagers to
        # separate GUI into another package.
        import bleachbit.GuiApplication  # pylint: disable=import-outside-toplevel
        app = bleachbit.GuiApplication.Bleachbit()
        sys.exit(app.run(sys.argv))

    # Either CLI args were provided or no display is available
    import bleachbit.CLI  # pylint: disable=import-outside-toplevel
    # If no args and defaulting to CLI, print usage information
    if 1 == len(sys.argv) and not have_gui:
        sys.argv.append('--help')
    try:
        bleachbit.CLI.process_cmd_line()
    except BrokenPipeError:
        # The downstream pipe consumer (e.g., `less`) closed before we
        # finished writing.  Redirect stdout to devnull to suppress the
        # secondary BrokenPipeError raised by the interpreter while
        # flushing stdout at shutdown, then exit with the conventional
        # SIGPIPE status (128 + 13).
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
        sys.exit(141)


if __name__ == '__main__':
    main()
