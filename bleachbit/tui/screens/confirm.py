# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Delete confirmation modal — Y/N prompt before destructive delete."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.binding import Binding

from rich.text import Text

from bleachbit.FileUtilities import bytes_to_human
from bleachbit.Language import get_text as _


class ConfirmScreen(ModalScreen[bool]):
    """Y/N confirmation dialog for delete operation."""

    # These do not show without a footer.
    BINDINGS = [
        Binding("y", "confirm_yes"),
        Binding("n", "confirm_no"),
        Binding("q", "confirm_no"), # q=quit
        Binding("escape", "confirm_no"),
        Binding("left", "focus_yes_btn"),
        Binding("right", "focus_no_btn"),
    ]

    CSS = """
    ConfirmScreen {
        align: center middle;
    }

    #confirm-dialog {
        width: 50;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #confirm-title {
        text-align: center;
        padding: 1 0;
        text-style: bold;
        color: $warning;
    }

    #confirm-body {
        padding: 0 0 1 0;
    }

    #confirm-buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }
    """

    def __init__(self, cleaner_count: int, option_count: int, total_files: int, total_size: int):
        """Initialize the confirmation dialog with delete statistics."""
        super().__init__()
        self.cleaner_count = cleaner_count
        self.option_count = option_count
        self.total_files = total_files
        self.total_size = total_size

    def compose(self) -> ComposeResult:
        """Build the dialog UI."""
        with Container(id="confirm-dialog"):
            # TRANSLATORS: This is a confirmation dialog title for a destructive action.
            yield Static(_("[!] Confirm Delete"), id="confirm-title", markup=False)
            yield Static(
                _("Delete %(total_files)s files (%(size)s) across %(cleaner_count)s cleaners (%(option_count)s options)?") % {
                    "total_files": f"{self.total_files:n}",
                    "size": bytes_to_human(self.total_size),
                    "cleaner_count": f"{self.cleaner_count:n}",
                    "option_count": f"{self.option_count:n}"
                },
                id="confirm-body",
            )
            with Horizontal(id="confirm-buttons"):
                # TRANSLATORS: This is a button label to confirm deletion.
                yield Button(Text(_("[Y] Yes")), variant="error", id="btn-yes")
                # TRANSLATORS: This is a button label to decline deletion.
                yield Button(Text(_("[N] No")), variant="primary", id="btn-no")

    def on_mount(self) -> None:
        """Focus the No button on mount."""
        # For caution, default to the no button.
        self.query_one("#btn-no", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss when a button is pressed."""
        self.dismiss(event.button.id == 'btn-yes')

    def action_confirm_yes(self) -> None:
        """Dismiss with True, confirmed=yes."""
        self.dismiss(True)

    def action_confirm_no(self) -> None:
        """Dismiss with False, confirmed=no."""
        self.dismiss(False)

    def action_focus_yes_btn(self) -> None:
        """Move focus to the Yes button."""
        self.query_one("#btn-yes", Button).focus()

    def action_focus_no_btn(self) -> None:
        """Move focus to the No button."""
        self.query_one("#btn-no", Button).focus()
