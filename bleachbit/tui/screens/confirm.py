# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Delete confirmation modal — Y/N prompt before destructive delete."""

from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.binding import Binding

from rich.text import Text

from bleachbit.FileUtilities import bytes_to_human
from bleachbit.Language import get_text as _


class ConfirmScreen(ModalScreen[bool]):
    """Y/N confirmation dialog for delete operation."""

    BINDINGS = [
        Binding("y", "confirm_yes", _("Yes")),
        Binding("n", "confirm_no", _("No")),
        Binding("escape", "confirm_no", _("Cancel")),
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
        super().__init__()
        self.cleaner_count = cleaner_count
        self.option_count = option_count
        self.total_files = total_files
        self.total_size = total_size

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Static(_("[!] Confirm Delete"), id="confirm-title", markup=False)
            yield Static(
                _("Delete %(total_files)d files (%(size)s) across %(cleaner_count)d cleaners (%(option_count)d options)?") % {
                    "total_files": self.total_files,
                    "size": bytes_to_human(self.total_size),
                    "cleaner_count": self.cleaner_count,
                    "option_count": self.option_count
                },
                id="confirm-body",
            )
            with Center(id="confirm-buttons"):
                yield Button(Text(_("[Y] Yes")), variant="error", id="btn-yes")
                yield Button(Text(_("[N] No")), variant="primary", id="btn-no")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm_yes(self):
        self.dismiss(True)

    def action_confirm_no(self):
        self.dismiss(False)
