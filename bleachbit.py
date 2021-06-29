#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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

import bleachbit.Unix


if 'posix' == os.name:
    if os.path.isdir('/usr/share/bleachbit'):
        # This path contains bleachbit/{C,G}LI.py .  This section is
        # unnecessary if installing BleachBit in site-packages.
        sys.path.append('/usr/share/')

        if (
                bleachbit.Unix.is_linux_display_protocol_wayland() and
                os.environ['USER'] == 'root' and
                bleachbit.Unix.root_is_not_allowed_to_X_session()
            
        ):
            print('To run any GUI application on Wayland with root you need to allow the root to connect with '
                  'the user\'s X session. For example like this:\n'
                  'xhost si:localuser:root\n'
                  'After finishing with the application you can remove the connection like this:\n'
                  'xhost -si:localuser:root\n'
                  'Please keep in mind that this solution presents a security risk '
                  'as put by Emmanuele Bassi, a GNOME developer: "there are no real, substantiated, technological '
                  'reasons why anybody should run a GUI application as root. By running GUI applications as an admin '
                  'user you are literally running millions of lines of code that have not been audited properly to run '
                  'under elevated privileges; you are also running code that will touch files inside your $HOME and may '
                  'change their ownership on the file system; connect, via IPC, to even more running code, etc. You are '
                  'opening up a massive, gaping security hole. Source:\n'
                  'https://wiki.archlinux.org/title/Running_GUI_applications_as_root'
                  )
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
