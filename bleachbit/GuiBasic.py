# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
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

from Common import _



def browse_folder(parent, title):
    """Ask the user to select a folder.  Return the full path or None."""

    if 'nt' == os.name:
        return Windows.browse_folder(parent.window.handle, title)

    # fall back to GTK+
    chooser = gtk.FileChooserDialog( parent = parent, \
        title = title,
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
        gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT), \
        action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    pathname = chooser.get_filename()
    chooser.hide()
    chooser.destroy()
    if gtk.RESPONSE_ACCEPT == resp:
        return pathname
    # user cancelled
    return None


def browse_file(parent, title):
    """Prompt user to select a single file"""

    if 'nt' == os.name:
        return Windows.browse_file(parent.window.handle, title)

    chooser = gtk.FileChooserDialog(title = title,
        parent = parent,
        action = gtk.FILE_CHOOSER_ACTION_OPEN,
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    path = chooser.get_filename()
    chooser.destroy()

    if gtk.RESPONSE_OK != resp:
        # user cancelled
        return None

    return path


def browse_files(parent, title):
    """Prompt user to select multiple files to delete"""

    if 'nt' == os.name:
        return Windows.browse_files(parent.window.handle, title)

    chooser = gtk.FileChooserDialog(title = title,
        parent = parent,
        action = gtk.FILE_CHOOSER_ACTION_OPEN,
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_DELETE, gtk.RESPONSE_OK))
    chooser.set_select_multiple(True)
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    paths = chooser.get_filenames()
    chooser.destroy()

    if gtk.RESPONSE_OK != resp:
        # user cancelled
        return None

    return paths


def delete_confirmation_dialog(parent, mention_preview):
    """Return boolean whether OK to delete files."""
    dialog = gtk.Dialog(title = _("Delete confirmation"), parent = parent, flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
    dialog.set_default_size(300, -1)

    hbox = gtk.HBox(homogeneous=False, spacing=10)
    icon = gtk.Image()
    icon.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icon, False)
    if mention_preview:
        question_text = _("Are you sure you want to permanently delete files according to the selected operations?  The actual files that will be deleted may have changed since you ran the preview.")
    else:
        question_text = _("Are you sure you want to permanently delete these files?")

    question = gtk.Label(question_text)
    question.set_line_wrap(True)
    hbox.pack_start(question, False)
    dialog.vbox.pack_start(hbox, False)
    dialog.vbox.set_spacing(10)

    dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dialog.add_button(gtk.STOCK_DELETE, gtk.RESPONSE_ACCEPT)
    dialog.set_default_response(gtk.RESPONSE_CANCEL)

    dialog.show_all()
    ret = dialog.run()
    dialog.destroy()
    return ret == gtk.RESPONSE_ACCEPT


def message_dialog(parent, msg, mtype = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK):
    """Convenience wrapper for gtk.MessageDialog"""

    dialog = gtk.MessageDialog(parent, \
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        mtype, \
        buttons, \
        msg)
    resp = dialog.run()
    dialog.destroy()

    return resp


def open_url(url):
    """Open an HTTP URL.  Try to run as non-root."""
    print "debug: on_url('%s')" % (url,)
    # drop privileges so the web browser is running as a normal process
    if 'posix' == os.name and 0 == os.getuid():
        msg = _("Because you are running as root, please manually open this link in a web browser:\n%s") % url
        message_dialog(None, msg, gtk.MESSAGE_INFO)
        return
    try:
        import gnomevfs
        gnomevfs.url_show(url)
        return
    except:
        import webbrowser
        webbrowser.open(url)

