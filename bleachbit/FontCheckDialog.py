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

"""Dialog used to verify text rendering on Windows.

This is a temporary workaround.
"""


from bleachbit.GtkShim import require_gtk, Gtk
from bleachbit.Language import get_text as _

require_gtk()

from gi.repository import Pango


ALT_FONT = "Arial 14"

RESPONSE_TEXT_BLURRY = 1001
RESPONSE_TEXT_UNREADABLE = 1002


def _apply_alt_font(widget):
    """Apply the alternate font to a label or label-like widget."""
    desc = Pango.FontDescription(ALT_FONT)
    widget.modify_font(desc)


def create_font_check_dialog(parent=None):
    """Return the dialog prompting the user about font rendering."""
    dialog = Gtk.Dialog(
        # TRANSLATORS: Title of the font check dialog
        title=_("Font check"),
        transient_for=parent,
        modal=True
    )
    dialog.set_border_width(12)
    dialog.set_resizable(False)

    dialog.add_buttons(
        # TRANSLATORS: Button label in the font check dialog
        _("Text is okay"), Gtk.ResponseType.YES,
        # TRANSLATORS: Button label in the font check dialog. This is one of
        # three buttons the user can click to report how the text appears.
        # The user clicks this if the text is readable but appears fuzzy.
        _("Text is blurry"), RESPONSE_TEXT_BLURRY,
        # TRANSLATORS: Button label in the font check dialog in case the font
        # looks like an alien language. This is one of three buttons the user
        # can click to report how the text appears.
        _("Text is unrecognizable"), RESPONSE_TEXT_UNREADABLE,
    )

    # To ensure user can read them, apply the alternate font to all buttons.
    for response_id in (
        Gtk.ResponseType.YES,
        RESPONSE_TEXT_BLURRY,
        RESPONSE_TEXT_UNREADABLE,
    ):
        button = dialog.get_widget_for_response(response_id)
        if button is not None:
            _apply_alt_font(button)

    content = dialog.get_content_area()
    content.set_spacing(8)

    # TRANSLATORS: Question shown in the font check dialog displayed
    # on startup on Windows. There are bugs that for some users the
    # font is blurry or resembles an alien language.
    text_quality_msg = _('Does all the text in this window look okay?')
    label_default = Gtk.Label(label=text_quality_msg)
    label_default.set_xalign(0.0)
    label_default.set_line_wrap(True)

    label_alt = Gtk.Label(label=text_quality_msg)
    label_alt.set_xalign(0.0)
    label_alt.set_line_wrap(True)
    _apply_alt_font(label_alt)

    content.pack_start(label_default, False, False, 0)
    content.pack_start(label_alt, False, False, 0)

    dialog.show_all()
    return dialog
