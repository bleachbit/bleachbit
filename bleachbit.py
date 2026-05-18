# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Launcher
"""

import sys

# change error handling to avoid popup with GTK 3
# https://github.com/bleachbit/bleachbit/issues/651
import win32api
import win32con
win32api.SetErrorMode(win32con.SEM_FAILCRITICALERRORS |
                        win32con.SEM_NOGPFAULTERRORBOX | win32con.SEM_NOOPENFILEERRORBOX)

if 1 == len(sys.argv):
    import bleachbit.GUI
    app = bleachbit.GUI.Bleachbit()
    sys.exit(app.run(sys.argv))

import bleachbit.CLI
bleachbit.CLI.process_cmd_line()