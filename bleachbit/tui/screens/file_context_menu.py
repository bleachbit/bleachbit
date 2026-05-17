# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""File context menu — actions on selected files."""

import os

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding

from bleachbit.Options import options


class FileContextMenu(ModalScreen):
    """Context menu for file list — whitelist, clean list, clipboard, open dir."""

    BINDINGS = [
        Binding("w", "add_whitelist", "Add to keep list"),
        Binding("c", "add_cleanlist", "Add to clean list"),
        Binding("y", "copy_paths", "Copy to clipboard"),
        Binding("o", "open_dir", "Open directory"),
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    FileContextMenu {
        align: center middle;
    }

    #ctx-dialog {
        width: 52;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #ctx-title {
        text-align: center;
        padding: 0 0 1 0;
        text-style: bold;
    }

    #ctx-body {
        padding: 0 0 1 0;
    }

    #ctx-actions {
        padding: 1 0 0 0;
    }
    """

    def __init__(self, paths: list[str]):
        super().__init__()
        self._paths = paths

    def compose(self) -> ComposeResult:
        count = len(self._paths)
        preview = ", ".join(self._paths[:3])
        if count > 3:
            preview += f" ... and {count - 3} more"

        with Container(id="ctx-dialog"):
            yield Static(f"{count} file(s) selected", id="ctx-title")
            yield Static(preview, id="ctx-body")
            yield Static(
                "[bold]w[/bold]=Add to keep list  "
                "[bold]c[/bold]=Add to clean list  "
                "[bold]y[/bold]=Copy  "
                "[bold]o[/bold]=Open dir",
                id="ctx-actions",
            )

    def action_add_whitelist(self):
        """Add selected paths to the keep list (whitelist)."""
        existing = options.get_whitelist_paths()
        existing_paths = {p for _, p in existing}
        new_entries = []
        for path in self._paths:
            if path not in existing_paths:
                p_type = 'folder' if os.path.isdir(path) else 'file'
                new_entries.append((p_type, path))
        if new_entries:
            options.set_whitelist_paths(existing + new_entries)
            self.notify(f"Added {len(new_entries)} path(s) to keep list")
        else:
            self.notify("All paths already in keep list")
        self.dismiss()

    def action_add_cleanlist(self):
        """Add selected paths to custom clean list."""
        existing = options.get_custom_paths()
        existing_paths = {p for _, p in existing}
        new_entries = []
        for path in self._paths:
            if path not in existing_paths:
                p_type = 'folder' if os.path.isdir(path) else 'file'
                new_entries.append((p_type, path))
        if new_entries:
            options.set_custom_paths(existing + new_entries)
            self.notify(f"Added {len(new_entries)} path(s) to clean list")
        else:
            self.notify("All paths already in clean list")
        self.dismiss()

    def action_copy_paths(self):
        """Copy selected paths to clipboard."""
        text = "\n".join(self._paths)
        self.app.copy_to_clipboard(text)
        self.notify(f"Copied {len(self._paths)} path(s) to clipboard")
        self.dismiss()

    def action_open_dir(self):
        """Show the containing directories of selected files."""
        dirs = sorted(set(os.path.dirname(p) for p in self._paths))
        preview = "\n".join(dirs[:5])
        if len(dirs) > 5:
            preview += f"\n... and {len(dirs) - 5} more directories"
        self.app.copy_to_clipboard(preview)
        self.notify(
            f"Copied {len(dirs)} director{'y' if len(dirs) == 1 else 'ies'} to clipboard"
        )
        self.dismiss()

    async def action_dismiss(self, result=None):
        self.dismiss(result)