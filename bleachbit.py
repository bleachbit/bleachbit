#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

if 'nt' == os.name:
    from bleachbit.Windows import setup_environment
    setup_environment()

if 'posix' == os.name:
    if os.path.isdir('/usr/share/bleachbit'):
        # This path contains bleachbit/{C,G}LI.py .  This section is
        # unnecessary if installing BleachBit in site-packages.
        sys.path.append('/usr/share/')

    # XDG base directory specification
    envs = {
        'XDG_DATA_HOME': os.path.expanduser('~/.local/share'),
        'XDG_CONFIG_HOME': os.path.expanduser('~/.config'),
        'XDG_CACHE_HOME': os.path.expanduser('~/.cache')
    }
    for varname, value in envs.iteritems():
        if not os.getenv(varname):
            os.putenv(varname, value)

if 1 == len(sys.argv):
    import gtk
    try:
        gtk.gdk.Screen().get_display()
    except RuntimeError:
        print("Could not open X display")
        sys.exit(1)
    import bleachbit.GUI
    gui = bleachbit.GUI.GUI()
    gtk.main()
else:
    import bleachbit.CLI
    bleachbit.CLI.process_cmd_line()
