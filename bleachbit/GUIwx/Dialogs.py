# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Common dialogs for the experimental wxPython GUI.

These are the wx counterparts of the dialogs in ``bleachbit.GuiBasic``
and reuse its translated msgids.  They use ``wx.RichMessageDialog``,
which is the native task dialog on Windows, so screen readers read the
title, the message, the checkbox and the buttons without extra work.
"""

import logging
import os
from urllib.parse import urlsplit

import wx

from bleachbit import IS_POSIX
from bleachbit.Language import get_text as _
from bleachbit.Options import options

logger = logging.getLogger(__name__)


def gtk_mnemonic_to_wx(label):
    """Convert a translated GTK menu mnemonic to wx syntax.

    GTK marks a mnemonic with ``_`` and escapes a literal underscore as
    ``__``. wx uses ``&`` and escapes a literal ampersand as ``&&``.
    Reusing the GTK menu msgids lets the wx front-end benefit from the
    existing translations without displaying the GTK mnemonic marker.
    """
    converted = []
    index = 0
    while index < len(label):
        char = label[index]
        if char == '&':
            converted.append('&&')
        elif char == '_':
            if index + 1 < len(label) and label[index + 1] == '_':
                converted.append('_')
                index += 1
            elif index + 1 == len(label):
                # A dangling GTK marker cannot designate a mnemonic.
                converted.append('_')
            else:
                converted.append('&')
        else:
            converted.append(char)
        index += 1
    return ''.join(converted)


def _cancel_label():
    # TRANSLATORS: Label for the Cancel button in several dialog windows:
    # file chooser, folder choose, delete confirmation, and warning dialogs.
    # The underscore indicates the accelerator key.
    return gtk_mnemonic_to_wx(_("_Cancel"))


def delete_confirmation_dialog(parent, mention_preview):
    """Return whether it is OK to delete files.

    Like ``GuiBasic.delete_confirmation_dialog``: in expert mode the
    dialog has a *Confirm before delete* checkbox, which is saved to
    the ``delete_confirmation`` option whatever the answer.
    """
    if mention_preview:
        # TRANSLATORS: This message appears in a dialog window when the user
        # asks the user to confirm deleting files when a preview was run.
        question_text = _("Are you sure you want to permanently delete files "
                          "according to the selected operations?  The actual files that will be "
                          "deleted may have changed since you ran the preview.")
    else:
        # TRANSLATORS: This message appears in a dialog window when the user
        # asks the user to confirm deleting files when no preview was run.
        question_text = _("Are you sure you want to permanently delete "
                          "these files?")
    # OK/Cancel (relabelled) rather than Yes/No, so Escape cancels.
    # Cancel is the default button, like the GTK dialog.
    dlg = wx.RichMessageDialog(
        parent, question_text,
        # TRANSLATORS: Title of the delete confirmation dialog.
        _("Delete confirmation"),
        wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_WARNING)
    dlg.SetOKCancelLabels(
        # TRANSLATORS: Label for the Delete button in the file choose dialog
        # and delete confirmation dialog.
        gtk_mnemonic_to_wx(_("_Delete")), _cancel_label())
    expert_mode = options.get('expert_mode')
    if expert_mode:
        dlg.ShowCheckBox(
            # TRANSLATORS: Check button shown in the confirm delete dialog.
            # If unchecked, then it will not confirm next time.
            _("Confirm before delete"),
            bool(options.get('delete_confirmation')))
    try:
        ret = dlg.ShowModal()
        if expert_mode:
            options.set('delete_confirmation', dlg.IsCheckBoxChecked())
    finally:
        dlg.Destroy()
    return ret == wx.ID_OK


def warning_confirm_dialog(parent, option_name, warning_text,
                           show_checkbox=True):
    """Show a warning dialog when enabling an option.

    Returns a tuple ``(confirmed, remember_choice)``, like
    ``GuiBasic.warning_confirm_dialog``.  *Cancel* is the default
    button, so pressing Enter does not enable the option, and Escape
    cancels.
    """
    dlg = wx.RichMessageDialog(
        parent, warning_text,
        # TRANSLATORS: Title of a warning dialog. %(option)s is the name
        # of the option being enabled (e.g. "shred files").
        _('Enable %(option)s') % {'option': option_name},
        wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_WARNING)
    dlg.SetOKCancelLabels(
        # TRANSLATORS: Button label in a warning dialog to confirm enabling an option.
        # The underscore is the accelerator key.
        gtk_mnemonic_to_wx(_('_Enable anyway')), _cancel_label())
    if show_checkbox:
        dlg.ShowCheckBox(
            # TRANSLATORS: Check button label. %(option)s is the name of
            # the option being enabled (e.g. "shred files").
            _('Remember my choice for %(option)s') % {'option': option_name})
    try:
        confirmed = dlg.ShowModal() == wx.ID_OK
        remember_choice = (confirmed and show_checkbox
                           and dlg.IsCheckBoxChecked())
    finally:
        dlg.Destroy()
    return confirmed, remember_choice


def open_url(url, parent=None, prompt=True):
    """Open an HTTP URL in the web browser, like ``GuiBasic.open_url``."""
    if not url.lower().startswith(('http://', 'https://')):
        logger.error('refusing to open URL with disallowed scheme: %s', url)
        return
    if IS_POSIX and os.getuid() == 0:
        # TRANSLATORS: This is an error message shown to root users.
        # %s expands to a web URL.
        msg = _("Because you are running as root, please manually open "
                "this link in a web browser:\n%s") % url
        wx.MessageBox(msg, style=wx.OK | wx.ICON_INFORMATION, parent=parent)
        return
    if prompt:
        # Name the whole host the browser goes to: the GTK pattern stops
        # at a digit or hyphen, and at the "@" of "user@host".
        try:
            host = urlsplit(url).hostname or url
        except ValueError:
            host = url
        dlg = wx.MessageDialog(
            parent,
            # TRANSLATORS: The question appears in a confirmation dialog.
            # %s expands to www.bleachbit.org or similar
            _("Open web browser to %s?") % host,
            # TRANSLATORS: Title of a confirmation dialog.
            _('Confirm'),
            wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
        finally:
            dlg.Destroy()
    wx.LaunchDefaultBrowser(url)
