# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Help overlay — key binding reference."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding


class HelpScreen(ModalScreen):
    """Help overlay showing all key bindings."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("question_mark", "dismiss", "Close"),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-dialog {
        width: 66;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        padding: 1 0;
        text-style: bold;
    }
    """

    HELP_TEXT = """\
[bold]BleachBit TUI — Key Bindings[/bold]

  [bold]Navigation[/bold]
    up / down  Move within current depth
    right      Expand / enter cleaner group
    left       Collapse / go up to parent
    g / Home   Jump to top
    G / End    Jump to bottom
    /          Search/filter cleaners

  [bold]Actions[/bold]
    Space      Toggle enable/disable on focused item
    Enter      Show file list for focused option
    p          Run preview (all checked options)
    P          Preview focused option only
    d          Run delete (all checked, with confirmation)
    D          Delete focused option only (with confirmation)
    o          Toggle overwrite preference
    i          Toggle file list mode (inline/overlay)

  [bold]File List[/bold]
    Page Up    Scroll up
    Page Down  Scroll down
    n          Next page of files
    p          Previous page of files
    a          Select/deselect all on page
    m          Context menu (whitelist/clean list/copy)
    c          Copy file list to clipboard
    e          Export file list to /tmp/
    Escape     Close inline file list / clear filter

  [bold]General[/bold]
    ?          This help
    Ctrl+P     Preferences
    q          Quit"""

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog"):
            yield Static(r"\[?] Help", id="help-title")
            yield Static(self.HELP_TEXT)

    async def action_dismiss(self, result=None):
        self.dismiss(result)
