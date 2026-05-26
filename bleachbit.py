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
import warnings


def has_console():
    """Check if a console window is available"""
    if not hasattr(sys, 'frozen'):
        return True
    # py2exe sets sys.frozen to 'console_exe' or 'windows_exe'
    return sys.frozen == 'console_exe'


def bootstrap():
    """Bootstrap the application"""
    if os.name != 'nt':
        print('This version requires Windows.')
        sys.exit(1)

    # change error handling to avoid popup with GTK 3
    # https://github.com/bleachbit/bleachbit/issues/651
    import win32api
    import win32con
    win32api.SetErrorMode(win32con.SEM_FAILCRITICALERRORS |
                          win32con.SEM_NOGPFAULTERRORBOX | win32con.SEM_NOOPENFILEERRORBOX)

    if has_console():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            import win_unicode_console
            win_unicode_console.enable()

    # set up environment variables
    from bleachbit import Windows
    Windows.setup_environment()

    # Use our `font.conf`` (see commit 3385952b37d78).
    os.environ.pop('FONTCONFIG_FILE', None)


def main():
    """Main entry point"""
    bootstrap()
    if 1 == len(sys.argv):
        import bleachbit.GUI
        app = bleachbit.GUI.Bleachbit()
        sys.exit(app.run(sys.argv))

    import bleachbit.CLI
    bleachbit.CLI.process_cmd_line()


if __name__ == '__main__':
    main()
    sys.exit(0)
