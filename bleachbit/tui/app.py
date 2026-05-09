# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""BleachBit TUI — Main application.

Phase 2: Connected to real BleachBit backend.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual import work

from bleachbit.tui.cleaner_tree import CleanerTree
from bleachbit.tui.screens.file_list import FileListOverlay, FileListWidget
from bleachbit.tui.screens.confirm import ConfirmScreen
from bleachbit.tui.screens.help_screen import HelpScreen
from bleachbit.tui.backend import (
    get_cleaner_tree_data,
    load_cleaners,
    build_operations,
    run_worker_in_thread,
    get_overwrite,
    set_overwrite,
    get_files_for_option,
    LogMessage,
    ProgressMessage,
    TotalSizeMessage,
    ItemSizeMessage,
    WorkerDoneMessage,
)
from bleachbit.FileUtilities import bytes_to_human
from bleachbit.Options import options


class BleachBitTUI(App):
    """BleachBit Terminal UI — keyboard-driven system cleaner."""

    TITLE = "BleachBit TUI"
    SUB_TITLE = "Phase 2 MVP"

    CSS = """
    #alpha-banner {
        height: 1;
        background: $warning 20%;
        color: $warning;
        text-style: bold;
        padding: 0 1;
    }

    #status-bar {
        height: 1;
        background: $boost;
        color: $text-muted;
        padding: 0 1;
    }

    #status-bar .idle {
        color: $text-muted;
    }

    #status-bar .working {
        color: $warning;
    }

    #status-bar .done {
        color: $success;
    }

    #main-container {
        height: 1fr;
    }

    CleanerTree {
        height: 1fr;
    }

    FileListWidget {
        height: 1fr;
        border: solid $accent;
        margin: 0 0 1 0;
    }

    #output-log {
        height: 10;
        border: solid $primary;
        background: $surface;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("p", "preview", "Preview", show=True),
        Binding("d", "delete", "Delete", show=True),
        Binding("P", "preview_focused", "Preview focused", show=True),
        Binding("D", "delete_focused", "Delete focused", show=True),
        Binding("o", "toggle_overwrite", "Overwrite", show=True),
        Binding("i", "toggle_file_mode", "File mode", show=True),
        Binding("question_mark", "show_help", "Help", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self._file_list_mode = "overlay"  # "overlay" or "inline"
        self._is_working = False
        self._inline_file_list = None
        self._current_worker = None  # reference to Worker for abort
        self._log_lines: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("This is alpha-level software. Please use caution.", id="alpha-banner")
        yield Static("Status: idle", id="status-bar")
        with Container(id="main-container"):
            yield CleanerTree()
        yield VerticalScroll(Static("", id="output-text", markup=False), id="output-log")
        yield Footer()

    def on_mount(self):
        """Load real cleaner data and set up."""
        load_cleaners()
        tree = self.query_one(CleanerTree)
        tree.populate_tree(get_cleaner_tree_data())

        overwrite = get_overwrite()
        overwrite_status = 'ON' if overwrite else 'OFF'
        self._update_status("idle", f"Ready. Press ? for help.  Overwrite: {overwrite_status}")

    # --- Status bar helpers ---

    def _update_status(self, state: str, message: str = ""):
        status_bar = self.query_one("#status-bar", Static)
        if state == "working":
            status_bar.update(f"[working]Status: {message}[/working]")
        elif state == "done":
            status_bar.update(f"[done]Status: {message}[/done]")
        else:
            status_bar.update(f"[idle]Status: {message}[/idle]")

    # --- Output log ---

    def _append_log(self, text: str):
        """Append a line to the output log widget."""
        self._log_lines.append(text)
        # Keep only last 200 lines
        if len(self._log_lines) > 200:
            self._log_lines = self._log_lines[-200:]
        output = self.query_one("#output-text", Static)
        output.update("\n".join(self._log_lines))

    # --- Backend message handlers ---

    def on_log_message(self, message: LogMessage):
        self._append_log(message.text.strip())

    def on_progress_message(self, message: ProgressMessage):
        pass  # progress bar not shown in Phase 2 MVP

    def on_total_size_message(self, message: TotalSizeMessage):
        tree = self.query_one(CleanerTree)
        tree.update_root_total(message.total_bytes)

    def on_item_size_message(self, message: ItemSizeMessage):
        tree = self.query_one(CleanerTree)
        tree.update_option_size(message.operation, message.option_id, message.size)

    def on_worker_done_message(self, message: WorkerDoneMessage):
        self._is_working = False
        self._current_worker = None
        tree = self.query_one(CleanerTree)

        if message.total_errors:
            tree.set_errors_for_active_operations(message.total_errors)

        tree.update_root_total_full(message.total_deleted, message.total_bytes)

        action_word = "Deleted" if message.really_delete else "Would delete"
        self._update_status(
            "done",
            f"{action_word} {message.total_deleted} files "
            f"({bytes_to_human(message.total_bytes)}).  "
            f"Errors: {message.total_errors}.",
        )
        self.notify(
            f"{'Delete' if message.really_delete else 'Preview'} complete: "
            f"{message.total_deleted} files, {bytes_to_human(message.total_bytes)}",
            title="Operation complete",
        )

    # --- Actions ---

    def action_preview(self):
        """Run preview (dry-run) operation."""
        if self._is_working:
            self.notify("Already working...", severity="warning")
            return
        self._run_operation(delete=False)

    def action_delete(self):
        """Run delete operation with confirmation."""
        if self._is_working:
            self.notify("Already working...", severity="warning")
            return
        self._confirm_and_delete()

    def action_preview_focused(self):
        """Preview only the currently focused option (shift-P)."""
        if self._is_working:
            self.notify("Already working...", severity="warning")
            return
        tree = self.query_one(CleanerTree)
        focused = tree.get_focused_option()
        if focused is None:
            self.notify("Focus an option first.", severity="warning")
            return
        self._run_operation(delete=False, enabled=[focused])

    def action_delete_focused(self):
        """Delete only the currently focused option with confirmation (shift-D)."""
        if self._is_working:
            self.notify("Already working...", severity="warning")
            return
        tree = self.query_one(CleanerTree)
        focused = tree.get_focused_option()
        if focused is None:
            self.notify("Focus an option first.", severity="warning")
            return
        self._confirm_and_delete_focused(focused)

    @work(exclusive=True)
    async def _confirm_and_delete_focused(self, focused):
        """Show confirmation dialog for focused option, then delete if confirmed."""
        c_id, o_id = focused
        files = get_files_for_option(c_id, o_id)
        total_files = len(files)
        total_size = sum(size for _, size in files)

        confirmed = await self.push_screen_wait(
            ConfirmScreen(1, 1, total_files, total_size)
        )
        if confirmed:
            self._run_operation(delete=True, enabled=[focused])

    @work(exclusive=True)
    async def _confirm_and_delete(self):
        """Show confirmation dialog, then delete if confirmed."""
        tree = self.query_one(CleanerTree)
        enabled = tree.get_enabled_options()

        if not enabled:
            self.notify("No options enabled. Enable some first.", severity="warning")
            return

        cleaner_count = tree.get_enabled_cleaner_count()
        option_count = tree.get_enabled_option_count()

        total_files = 0
        total_size = 0
        for c_id, o_id in enabled:
            files = get_files_for_option(c_id, o_id)
            total_files += len(files)
            total_size += sum(size for _, size in files)

        confirmed = await self.push_screen_wait(
            ConfirmScreen(cleaner_count, option_count, total_files, total_size)
        )

        if confirmed:
            self._run_operation(delete=True)

    @work(exclusive=True, thread=True)
    async def _run_operation(self, delete: bool, enabled=None):
        """Run a real preview or delete operation via BleachBit Worker.

        If *enabled* is None, uses all checked options from the tree.
        Otherwise *enabled* should be a list of (cleaner_id, option_id) tuples.
        """
        self._is_working = True
        tree = self.query_one(CleanerTree)

        if enabled is None:
            enabled = tree.get_enabled_options()

        if not enabled:
            self.notify("No options enabled. Enable some first.", severity="warning")
            self._is_working = False
            return

        op_name = "Deleting" if delete else "Previewing"
        self._update_status("working", f"{op_name}...")
        self._log_lines = []
        self.query_one("#output-text", Static).update("")

        operations = build_operations(enabled)
        # Propagate overwrite preference via bleachbit Options
        overwrite = get_overwrite()
        # Shred if overwrite is on AND we are actually deleting
        if delete and overwrite:
            options.set("shred", True)
        elif delete and not overwrite:
            options.set("shred", False)

        run_worker_in_thread(self, delete, operations)

        # Mark done via WorkerDoneMessage handler (on_worker_done_message)

    def action_toggle_overwrite(self):
        """Toggle overwrite preference via BleachBit config."""
        current = get_overwrite()
        set_overwrite(not current)
        state = "ON" if not current else "OFF"
        self.notify(f"Overwrite: {state}")
        self._update_status(
            "idle",
            f"Ready. Press ? for help.  Overwrite: {state}",
        )

    def action_toggle_file_mode(self):
        """Toggle between inline and overlay file list display."""
        if self._file_list_mode == "overlay":
            self._file_list_mode = "inline"
            self.notify("File list mode: inline")
        else:
            self._file_list_mode = "overlay"
            self.notify("File list mode: overlay")

    def action_show_help(self):
        """Show help overlay."""
        self.push_screen(HelpScreen())

    async def action_quit(self):
        """Quit the application."""
        if self._is_working:
            self._is_working = False
            self.notify("Aborting...")
        else:
            self.exit()

    # --- Handle OptionSelected from CleanerTree ---

    def on_cleaner_tree_option_selected(self, message: CleanerTree.OptionSelected):
        """Handle Enter key on an option node — show file list."""
        if self._file_list_mode == "overlay":
            self.push_screen(
                FileListOverlay(message.cleaner_name, message.option_name)
            )
        else:
            self._show_inline_file_list(message.cleaner_name, message.option_name)

    def _show_inline_file_list(self, cleaner_name: str, option_name: str):
        """Show file list inline below the tree."""
        if self._inline_file_list is not None:
            self._inline_file_list.remove()
            self._inline_file_list = None

        container = self.query_one("#main-container", Container)
        widget = FileListWidget(cleaner_name, option_name)
        container.mount(widget)
        self._inline_file_list = widget
        self.set_timer(0.1, lambda: self.query_one(CleanerTree).focus())
