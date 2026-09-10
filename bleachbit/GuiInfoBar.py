# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Non-blocking message bar shared by the main window and the dialogs
"""

from bleachbit.GtkShim import Gtk, GLib

# Seconds a message stays up before it dismisses itself
INFOBAR_TIMEOUT = 15


class InfoBarMixin:
    """Add a self-dismissing Gtk.InfoBar to a window or dialog.

    The host calls _build_infobar() once with the container to pack into,
    then show_infobar() to display a message. `infobar` and `infobar_label`
    stay plain widgets so callers (and tests) can query them directly.
    """

    _infobar_timeout_id = None

    def _build_infobar(self, container):
        """Create the InfoBar and pack it into container"""
        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect('response', self._on_infobar_response)
        self.infobar_label = Gtk.Label()
        self.infobar_label.set_line_wrap(True)
        self.infobar.get_content_area().add(self.infobar_label)
        container.pack_start(self.infobar, False, False, 0)
        self._infobar_timeout_id = None

    def _cancel_infobar_timeout(self):
        """Drop the pending auto-dismiss, if any"""
        if self._infobar_timeout_id:
            GLib.source_remove(self._infobar_timeout_id)
            self._infobar_timeout_id = None

    def _on_infobar_response(self, _infobar, _response_id):
        """Handle InfoBar close button click"""
        self._cancel_infobar_timeout()
        self.infobar.hide()

    def _hide_infobar(self):
        """Hide the InfoBar (used for auto-dismiss timeout)"""
        self._infobar_timeout_id = None
        self.infobar.hide()
        return False  # Remove from GLib timeout

    def show_infobar(self, message, message_type=Gtk.MessageType.ERROR):
        """Show a non-blocking InfoBar message that auto-dismisses

        Args:
            message: The message to display
            message_type: Gtk.MessageType (ERROR, WARNING, INFO, etc.)
        """
        self._cancel_infobar_timeout()
        self.infobar_label.set_text(message)
        self.infobar.set_message_type(message_type)
        self.infobar.show_all()
        self._infobar_timeout_id = GLib.timeout_add_seconds(
            INFOBAR_TIMEOUT, self._hide_infobar)
