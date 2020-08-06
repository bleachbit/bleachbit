#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Launcher
"""

import os
import sys

if 'posix' == os.name:
    if os.path.isdir('/usr/share/bleachbit'):
        # This path contains bleachbit/{C,G}LI.py .  This section is
        # unnecessary if installing BleachBit in site-packages.
        sys.path.append('/usr/share/')

if os.name == 'nt':
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
else:
    import bleachbit.CLI
    bleachbit.CLI.process_cmd_line()
