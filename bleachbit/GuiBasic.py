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
Basic GUI code
"""

# standard library
import os

# local import
from bleachbit.GtkShim import Gtk, Gdk, GLib, require_gtk
from bleachbit.Language import get_text as _
from bleachbit.Options import options
if os.name == 'nt':
    from bleachbit import Windows

# Ensure GTK is available for this GUI module
require_gtk()


def browse_folder(parent, title, multiple, stock_button):
    """Ask the user to select a folder.  Return the full path or None."""

    if os.name == 'nt' and not os.getenv('BB_NATIVE'):
        ret = Windows.browse_folder(parent, title)
        return [ret] if multiple and not ret is None else ret

    # fall back to GTK+
    chooser = Gtk.FileChooserDialog(transient_for=parent,
                                    title=title,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                        stock_button, Gtk.ResponseType.OK)
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

    if os.name == 'nt' and not os.getenv('BB_NATIVE'):
        return Windows.browse_file(parent, title)

    chooser = Gtk.FileChooserDialog(title=title,
                                    transient_for=parent,
                                    action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                        _("_Open"), Gtk.ResponseType.OK)
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

    if os.name == 'nt' and not os.getenv('BB_NATIVE'):
        return Windows.browse_files(parent, title)

    chooser = Gtk.FileChooserDialog(title=title,
                                    transient_for=parent,
                                    action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                        _("_Delete"), Gtk.ResponseType.OK)
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


def delete_confirmation_dialog(parent, mention_preview, shred_settings=False):
    """Return boolean whether OK to delete files."""
    dialog = Gtk.Dialog(title=_("Delete confirmation"), transient_for=parent,
                        modal=True,
                        destroy_with_parent=True)
    dialog.set_default_size(300, -1)

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                   homogeneous=False, spacing=10)

    if shred_settings:
        notice_text = _("This function deletes all BleachBit settings and then quits the application. Use this to hide your use of BleachBit or to reset its settings. The next time you start BleachBit, the settings will initialize to default values.")
        notice = Gtk.Label(label=notice_text)
        notice.set_line_wrap(True)
        vbox.pack_start(notice, False, True, 0)

    if mention_preview:
        question_text = _(
            "Are you sure you want to permanently delete files according to the selected operations?  The actual files that will be deleted may have changed since you ran the preview.")
    else:
        question_text = _(
            "Are you sure you want to permanently delete these files?")
    question = Gtk.Label(label=question_text)
    question.set_line_wrap(True)
    vbox.pack_start(question, False, True, 0)

    if options.get('expert_mode'):
        cb_popup = Gtk.CheckButton(label=_("Confirm before delete"))
        cb_popup.set_active(options.get('delete_confirmation'))
        vbox.pack_start(cb_popup, False, True, 0)

    dialog.get_content_area().pack_start(vbox, False, True, 0)
    dialog.get_content_area().set_spacing(10)

    dialog.add_button(_('_Delete'), Gtk.ResponseType.ACCEPT)
    dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    dialog.set_default_response(Gtk.ResponseType.CANCEL)

    dialog.show_all()
    ret = dialog.run()
    if options.get('expert_mode'):
        options.set('delete_confirmation', cb_popup.get_active())
    dialog.destroy()
    return ret == Gtk.ResponseType.ACCEPT


def warning_confirm_dialog(parent, option_name, warning_text, show_checkbox=True):
    """Show a warning dialog when enabling an option.

    Returns tuple (confirmed: bool, remember_choice: bool).
    """
    dialog = Gtk.Dialog(title=_('Enable %(option)s') % {'option': option_name},
                        transient_for=parent,
                        modal=True,
                        destroy_with_parent=True)
    content = dialog.get_content_area()
    content.set_border_width(12)
    content.set_spacing(10)

    warning_label = Gtk.Label(label=warning_text)
    warning_label.set_line_wrap(True)
    warning_label.set_xalign(0.0)
    content.pack_start(warning_label, False, False, 0)

    remember_cb = Gtk.CheckButton(
        label=_('Remember my choice for %(option)s') % {'option': option_name})
    remember_cb.set_halign(Gtk.Align.START)
    if show_checkbox:
        content.pack_start(remember_cb, False, False, 0)

    cancel_button = dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    enable_button = dialog.add_button(_("_Enable anyway"), Gtk.ResponseType.OK)
    enable_button.get_style_context().add_class('destructive-action')
    dialog.set_default_response(Gtk.ResponseType.CANCEL)
    cancel_button.grab_focus()

    # Disable enable button for a moment to prevent accident by double-clicking.
    enable_button.set_sensitive(False)

    def enable_button_after_delay():
        enable_button.set_sensitive(True)
        return False

    GLib.timeout_add(500, enable_button_after_delay)

    dialog.show_all()
    response = dialog.run()
    remember_choice = response == Gtk.ResponseType.OK and show_checkbox and remember_cb.get_active()
    dialog.destroy()

    return response == Gtk.ResponseType.OK, remember_choice


def message_dialog(parent, msg, mtype=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, title=None):
    """Convenience wrapper for Gtk.MessageDialog"""

    dialog = Gtk.MessageDialog(transient_for=parent,
                               modal=True,
                               destroy_with_parent=True,
                               message_type=mtype,
                               buttons=buttons,
                               text=msg)
    if title:
        dialog.set_title(title)
    resp = dialog.run()
    dialog.destroy()

    return resp


def open_url(url, parent_window=None, prompt=True):
    """Open an HTTP URL.  Try to run as non-root."""
    # drop privileges so the web browser is running as a normal process
    if os.name == 'posix' and os.getuid() == 0:
        msg = _(
            "Because you are running as root, please manually open this link in a web browser:\n%s") % url
        message_dialog(None, msg, Gtk.MessageType.INFO)
        return
    if prompt:
        # find hostname
        import re
        ret = re.search(r'^http(s)?://([a-z.]+)', url)
        if not ret:
            host = url
        else:
            host = ret.group(2)
        # TRANSLATORS: %s expands to www.bleachbit.org or similar
        msg = _("Open web browser to %s?") % host
        resp = message_dialog(parent_window,
                              msg,
                              Gtk.MessageType.QUESTION,
                              Gtk.ButtonsType.OK_CANCEL,
                              _('Confirm'))
        if Gtk.ResponseType.OK != resp:
            return
    # open web browser
    if os.name == 'nt':
        # in Gtk.show_uri() avoid 'glib.GError: No application is registered as
        # handling this file'
        import webbrowser
        webbrowser.open(url)
    elif (Gtk.get_major_version(), Gtk.get_minor_version()) < (3, 22):
        # Ubuntu 16.04 LTS ships with GTK 3.18
        Gtk.show_uri(None, url, Gdk.CURRENT_TIME)
    else:
        Gtk.show_uri_on_window(parent_window, url, Gdk.CURRENT_TIME)
