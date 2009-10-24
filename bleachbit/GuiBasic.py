# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Basic GUI code
"""



import gtk
import os

if 'nt' == os.name:
    import Windows



def browse_folder(parent, title):
    """Ask the user to select a folder.  Return the full path or None."""

    if 'nt' == os.name:
        return Windows.browse_folder(parent.window.handle, title)

    # fall back to GTK+
    chooser = gtk.FileChooserDialog( parent = self.parent, \
        title = title,
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
        gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT), \
        action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

    resp = chooser.run()
    pathname = chooser.get_filename()
    chooser.hide()
    chooser.destroy()
    if gtk.RESPONSE_ACCEPT == resp:
        return pathname
    # user cancelled
    return None


def message_dialog(parent, msg, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK):
    """Convenience wrapper for gtk.MessageDialog"""

    dialog = gtk.MessageDialog(parent, \
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        type, \
        buttons, \
        _("You must select an operation"))
    resp = dialog.run()
    dialog.destroy()

    return resp

