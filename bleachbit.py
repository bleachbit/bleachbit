#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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

if 'posix' == os.name and os.path.isdir('/usr/share/bleachbit'):
    # This path contains bleachbit/{C,G}LI.py .  This section is
    # unnecessary if installing BleachBit in site-packages.
    sys.path.append('/usr/share/')


if 1 == len(sys.argv):
    import gtk
    try:
        gtk.gdk.Screen().get_display()
    except RuntimeError:
        print "Could not open X display"
        sys.exit(1)
    import bleachbit.GUI
    gui = bleachbit.GUI.GUI()
    gtk.main()
else:
    import bleachbit.CLI
    bleachbit.CLI.process_cmd_line()
