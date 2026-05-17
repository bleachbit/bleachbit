# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""File list screen — supports both inline-expand and full-screen overlay modes.

Prototype A: Inline-expand — file list appears below the option node in the tree.
Prototype B: Full-screen overlay — file list takes the whole screen.
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Header, Footer
from textual.binding import Binding

from bleachbit.FileUtilities import bytes_to_human


class FileListWidget(VerticalScroll):
    """Scrollable file list widget — reusable for both inline and overlay modes."""

    BINDINGS = [
        Binding("escape", "dismiss_inline", "Close", show=False),
        Binding("c", "copy_clipboard", "Copy to clipboard", show=False),
        Binding("e", "export_file", "Export to file", show=False),
    ]

    def __init__(self, cleaner_name: str, option_name: str, file_count: int = 10000):
        super().__init__()
        self.cleaner_name = cleaner_name
        self.option_name = option_name
        self.file_count = file_count
        self._files: list[tuple[str, int]] = []
        self._total_size = 0
        self.can_focus = True

    def on_mount(self):
        self._load_files()
        self._render_files()

    def _load_files(self):
        """Load real file data from the BleachBit backend."""
        from bleachbit.tui.backend import get_files_for_option
        self._files = get_files_for_option(self.cleaner_name, self.option_name)
        self._total_size = sum(size for _, size in self._files)

    def _render_files(self):
        """Render the file list with paths and sizes from the backend."""
        if not self._files:
            self.mount(Static("[dim]No files found for this option.[/dim]"))
            return

        total_human = bytes_to_human(self._total_size)
        lines = [
            f"[bold]Files for {self.cleaner_name} -> {self.option_name}[/bold]",
            f"[dim]{len(self._files)} files, {total_human}[/dim]",
            "",
        ]
        for path, size in self._files[:self.file_count]:
            size_str = bytes_to_human(size) if size else "0"
            lines.append(f"  {path}  ({size_str})")

        if len(self._files) > self.file_count:
            remaining = len(self._files) - self.file_count
            lines.append(
                f"  [dim]... and {remaining} more file(s)[/dim]"
            )

        self.mount(Static("\n".join(lines), markup=True))

    def get_all_text(self) -> str:
        """Return all file paths as plain text (for clipboard/export)."""
        return "\n".join(path for path, _ in self._files)

    def action_copy_clipboard(self):
        """Copy all file paths to clipboard."""
        text = self.get_all_text()
        if text:
            self.app.copy_to_clipboard(text)
            self.notify(f"Copied {len(text.splitlines())} file paths to clipboard")
        else:
            self.notify("No file data available", severity="warning")

    def action_export_file(self):
        """Export file list to /tmp/."""
        text = self.get_all_text()
        if not text:
            self.notify("No file data available", severity="warning")
            return
        path = (
            f"/tmp/bleachbit-filelist-{self.cleaner_name}-"
            f"{self.option_name}.txt"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.notify(f"Exported to {path}")

    def action_dismiss_inline(self):
        """Dismiss inline file list and return focus to tree."""
        if self.app._inline_file_list is self:
            self.app._dismiss_inline_file_list()


class FileListOverlay(ModalScreen):
    """Prototype B: Full-screen overlay file list."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("c", "copy_clipboard", "Copy to clipboard"),
        Binding("e", "export_file", "Export to file"),
    ]

    def __init__(self, cleaner_name: str, option_name: str):
        super().__init__()
        self.cleaner_name = cleaner_name
        self.option_name = option_name

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            FileListWidget(self.cleaner_name, self.option_name),
            id="file-list-container",
        )
        yield Footer()

    def action_copy_clipboard(self):
        widget = self.query_one(FileListWidget)
        text = widget.get_all_text()
        if text:
            self.app.copy_to_clipboard(text)
            self.notify(f"Copied {len(text.splitlines())} file paths to clipboard")
        else:
            self.notify("No file data available", severity="warning")

    def action_export_file(self):
        widget = self.query_one(FileListWidget)
        text = widget.get_all_text()
        if not text:
            self.notify("No file data available", severity="warning")
            return
        path = (
            f"/tmp/bleachbit-filelist-{self.cleaner_name}-"
            f"{self.option_name}.txt"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.notify(f"Exported to {path}")

    async def action_dismiss(self, result=None):
        self.dismiss(result)
