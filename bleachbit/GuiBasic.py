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
Basic GUI code
"""


from gi.repository import Gtk
from gi.repository import Gdk
import os

if 'nt' == os.name:
    import Windows

from Common import _


def browse_folder(parent, title, multiple, stock_button):
    """Ask the user to select a folder.  Return the full path or None."""

    if 'nt' == os.name and None == os.getenv('BB_NATIVE'):
        ret = Windows.browse_folder(
            parent.window.handle if parent else None, title)
        return [ret] if multiple and not ret is None else ret

    # fall back to GTK+
    chooser = Gtk.FileChooserDialog(transient_for=parent,
                                    title=title,
                                    action = Gtk.FileChooserAction.SELECT_FOLDER)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL, stock_button, Gtk.ResponseType.OK)
    chooser.set_default_response(Gtk.ResponseType.OK)
    chooser.set_select_multiple(multiple)
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    if multiple:
        ret = chooser.get_filenames()
    else:
        ret = chooser.get_filename()
    chooser.hide()
    chooser.destroy()
    if Gtk.ResponseType.OK != resp:
        # user cancelled
        return None
    return ret


def browse_file(parent, title):
    """Prompt user to select a single file"""

    if 'nt' == os.name and None == os.getenv('BB_NATIVE'):
        return Windows.browse_file(parent.window.handle, title)

    chooser = Gtk.FileChooserDialog(title=title,
                                    transient_for=parent,
                                    action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL, _("_Open"), Gtk.ResponseType.OK)
    chooser.set_default_response(Gtk.ResponseType.OK)
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    path = chooser.get_filename()
    chooser.destroy()

    if Gtk.ResponseType.OK != resp:
        # user cancelled
        return None

    return path


def browse_files(parent, title):
    """Prompt user to select multiple files to delete"""

    if 'nt' == os.name and None == os.getenv('BB_NATIVE'):
        return Windows.browse_files(parent.window.handle, title)

    chooser = Gtk.FileChooserDialog(title=title,
                                    transient_for=parent,
                                    action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL, _("_Delete"), Gtk.ResponseType.OK)
    chooser.set_default_response(Gtk.ResponseType.OK)
    chooser.set_select_multiple(True)
    chooser.set_current_folder(os.path.expanduser('~'))
    resp = chooser.run()
    paths = chooser.get_filenames()
    chooser.destroy()

    if Gtk.ResponseType.OK != resp:
        # user cancelled
        return None

    return paths


def delete_confirmation_dialog(parent, mention_preview):
    """Return boolean whether OK to delete files."""
    dialog = Gtk.Dialog(title=_("Delete confirmation"), transient_for=parent,
                        modal=True,
                        destroy_with_parent=True)
    dialog.set_default_size(300, -1)

    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    if mention_preview:
        question_text = _(
            "Are you sure you want to permanently delete files according to the selected operations?  The actual files that will be deleted may have changed since you ran the preview.")
    else:
        question_text = _(
            "Are you sure you want to permanently delete these files?")

    question = Gtk.Label(label=question_text)
    question.set_line_wrap(True)
    hbox.pack_start(question, False, True, 0)
    dialog.vbox.pack_start(hbox, False, True, 0)
    dialog.vbox.set_spacing(10)

    dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    dialog.add_button(_('_Delete'), Gtk.ResponseType.ACCEPT)
    dialog.set_default_response(Gtk.ResponseType.CANCEL)

    dialog.show_all()
    ret = dialog.run()
    dialog.destroy()
    return ret == Gtk.ResponseType.ACCEPT


def message_dialog(parent, msg, mtype=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK):
    """Convenience wrapper for Gtk.MessageDialog"""

    dialog = Gtk.MessageDialog(transient_for=parent,
                               modal=True,
                               destroy_with_parent=True,
                               message_type=mtype,
                               buttons=buttons,
                               text=msg)
    resp = dialog.run()
    dialog.destroy()

    return resp


def open_url(url, parent_window=None, prompt=True):
    """Open an HTTP URL.  Try to run as non-root."""
    # drop privileges so the web browser is running as a normal process
    if 'posix' == os.name and 0 == os.getuid():
        msg = _(
            "Because you are running as root, please manually open this link in a web browser:\n%s") % url
        message_dialog(None, msg, Gtk.MessageType.INFO)
        return
    if prompt:
        # find hostname
        import re
        ret = re.search('^http(s)?://([a-z\.]+)', url)
        if None == ret:
            host = url
        else:
            host = ret.group(2)
        # TRANSLATORS: %s expands to bleachbit.sourceforge.net or similar
        msg = _("Open web browser to %s?") % host
        resp = message_dialog(parent_window, msg,
                              Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL)
        if Gtk.ResponseType.OK != resp:
            return
    # open web browser
    if 'nt' == os.name:
        # in Gtk.show_uri() avoid 'glib.GError: No application is registered as
        # handling this file'
        import webbrowser
        webbrowser.open(url)
    else:
        Gtk.show_uri(None, url, Gdk.CURRENT_TIME)
