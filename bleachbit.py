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

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk

class Bleachbit(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        
    def on_activate(self, data=None):
        import bleachbit.GUI
        gui = bleachbit.GUI.GUI(self)
        gui.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

if 'posix' == os.name and os.path.isdir('/usr/share/bleachbit'):
    # This path contains bleachbit/{C,G}LI.py .  This section is
    # unnecessary if installing BleachBit in site-packages.
    sys.path.append('/usr/share/')


if 1 == len(sys.argv):
    app = Bleachbit()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
else:
    import bleachbit.CLI
    bleachbit.CLI.process_cmd_line()
