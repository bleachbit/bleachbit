#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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

    # The two imports from bleachbit must come after sys.path.append(..)
    import bleachbit.Unix
    from bleachbit.Language import get_text as _

    if (
        bleachbit.Unix.is_display_protocol_wayland_and_root_not_allowed()
    ):
        print(_('To run a GUI application on Wayland with root, allow access with this command:\n'
              'xhost si:localuser:root\n'
                'See more about xhost at https://docs.bleachbit.org/doc/frequently-asked-questions.html'))
        sys.exit(1)

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
