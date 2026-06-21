# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Backend bridge: connects BleachBit's real Worker to the Textual TUI.

Converts BleachBit's yield-based cooperative iterator pattern into
async/Message-based communication suitable for Textual's event loop.

The Worker runs in a thread.  Its ui callback posts Textual Messages
into the app so the tree, status bar, and log update live.
"""

from __future__ import annotations

import logging

from textual.message import Message

from bleachbit.Cleaner import backends, register_cleaners
from bleachbit import Worker, Options

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Textual Messages posted by the backend
# ---------------------------------------------------------------------------

class LogMessage(Message):
    """A line of text to append to the output log."""
    def __init__(self, text: str, tag: str | None = None):
        super().__init__()
        self.text = text
        self.tag = tag


class ProgressMessage(Message):
    """Progress bar update (float fraction or str label)."""
    def __init__(self, status):
        super().__init__()
        self.status = status


class TotalSizeMessage(Message):
    """Total bytes deleted (or to-be-deleted) so far."""
    def __init__(self, total_bytes: int):
        super().__init__()
        self.total_bytes = total_bytes


class ItemSizeMessage(Message):
    """Per-option byte count finished."""
    def __init__(self, operation: str, option_id: str, size: int):
        super().__init__()
        self.operation = operation
        self.option_id = option_id
        self.size = size


class WorkerDoneMessage(Message):
    """Worker finished (or was aborted)."""
    def __init__(self, worker, really_delete: bool):
        super().__init__()
        self.total_bytes = worker.total_bytes
        self.total_deleted = worker.total_deleted
        self.total_errors = worker.total_errors
        self.total_special = worker.total_special
        self.really_delete = really_delete


# ---------------------------------------------------------------------------
# TUI callback — drop-in for the GTK ui object that Worker expects
# ---------------------------------------------------------------------------

class TuiCallback:
    """Implements the ui interface that BleachBit's Worker calls.

    Instead of updating GTK widgets, it posts Textual Messages to the
    running App so the TUI can react.
    """

    def __init__(self, app):
        self.app = app

    def append_text(self, msg, tag=None):
        self.app.post_message(LogMessage(msg, tag))

    def update_progress_bar(self, status):
        self.app.post_message(ProgressMessage(status))

    def update_total_size(self, size):
        self.app.post_message(TotalSizeMessage(size))

    def update_item_size(self, operation, option_id, size):
        self.app.post_message(ItemSizeMessage(operation, option_id, size))

    def worker_done(self, worker, really_delete):
        self.app.post_message(WorkerDoneMessage(worker, really_delete))


# ---------------------------------------------------------------------------
# Cleaner list loading
# ---------------------------------------------------------------------------

_cleaners_loaded = False


def load_cleaners() -> dict:
    """Ensure cleaners are registered and return the backends dict.

    Returns the same module-level ``bleachbit.Cleaner.backends`` dict
    keyed by cleaner ID.

    Errors during cleaner registration are logged but not fatal —
    the TUI will show whatever cleaners loaded successfully.
    """
    global _cleaners_loaded
    if not _cleaners_loaded:
        try:
            list(register_cleaners())
        except Exception:
            logger.exception("Error loading cleaners — some may be unavailable")
        _cleaners_loaded = True
    return backends


def get_cleaner_tree_data() -> list[tuple]:
    """Return ordered list of (cleaner_id, cleaner_name, [(option_id, option_name, description)]) .

    Ready to feed into the CleanerTree widget.

    Applies auto-hide: cleaners with no usable options are hidden when
    the 'auto_hide' preference is enabled (default: True).
    """
    load_cleaners()
    auto_hide_enabled = Options.options.get('auto_hide')
    result = []
    for key in sorted(backends):
        backend = backends[key]
        try:
            c_id = backend.get_id()
            c_name = backend.get_name()
        except Exception:
            logger.exception("Error reading cleaner %s — skipping", key)
            continue

        try:
            if not any(backend.get_options()):
                continue
        except Exception:
            logger.exception("Error reading options for cleaner %s — skipping", c_id)
            continue

        try:
            # Auto-hide: skip cleaners not already enabled that have no usable options
            c_enabled = Options.options.get_tree(c_id, None)
            if not c_enabled and auto_hide_enabled and backend.auto_hide():
                continue
            # Build description lookup
            desc_map = {}
            for dname, ddesc in backend.get_option_descriptions():
                desc_map[dname] = ddesc
            opts = []
            for o_id, o_name in backend.get_options():
                opts.append((o_id, o_name, desc_map.get(o_name, "")))
        except Exception:
            logger.exception("Error building option list for cleaner %s — skipping", c_id)
            continue
        result.append((c_id, c_name, opts))
    return result


# ---------------------------------------------------------------------------
# Worker runner — threaded, async-friendly
# ---------------------------------------------------------------------------

def run_worker_in_thread(app, really_delete: bool, operations: dict):
    """Run BleachBit's Worker in a dedicated thread.

    Posts progress/result Messages to *app* via TuiCallback.
    This function is intended to be called from a Textual worker thread
    (``@work(thread=True)``).

    If the Worker crashes, a WorkerDoneMessage is still posted so the
    TUI never hangs.
    """
    cb = TuiCallback(app)
    worker = Worker.Worker(cb, really_delete, operations)
    app._current_worker = worker
    try:
        for _ in worker.run():
            pass
    except StopIteration:
        pass
    except Exception:
        logger.exception("Worker thread crashed")
        # Post a done message so the TUI recovers
        cb.worker_done(worker, really_delete)


# ---------------------------------------------------------------------------
# Operations helpers
# ---------------------------------------------------------------------------

def build_operations(enabled_options: list[tuple[str, str]]) -> dict:
    """Convert [(cleaner_id, option_id), ...] to the dict Worker expects.

    Example return: {'firefox': ['cache', 'cookies'], 'system': ['tmp']}
    """
    ops: dict[str, list[str]] = {}
    for c_id, o_id in enabled_options:
        ops.setdefault(c_id, []).append(o_id)
    return ops


# ---------------------------------------------------------------------------
# Overwrite / shred
# ---------------------------------------------------------------------------

def get_overwrite() -> bool:
    """Read the current overwrite (shred) preference from BleachBit config."""
    return Options.options.get("shred")


def set_overwrite(value: bool):
    """Write the overwrite (shred) preference to BleachBit config."""
    Options.options.set("shred", value)


# ---------------------------------------------------------------------------
# File listing — collect real file paths for a cleaner option
# ---------------------------------------------------------------------------

def get_files_for_option(cleaner_id: str, option_id: str) -> list[tuple[str, int]]:
    """Return list of (path, size_bytes) for files targeted by a cleaner option.

    Uses FileActionProvider.get_paths() when available (CleanerML-based
    cleaners) for expanded file lists.  Falls back to collecting paths
    from Command objects for legacy (hard-coded) cleaners.

    All errors are logged and the function returns whatever files it
    was able to collect — never raises to the caller.
    """
    from bleachbit import FileUtilities

    try:
        load_cleaners()
        backend = backends.get(cleaner_id)
        if not backend:
            return []
    except Exception:
        logger.exception("Error loading cleaners for file listing")
        return []

    files: list[tuple[str, int]] = []

    try:
        # Route A: iterate registered action providers (CleanerML-based cleaners)
        for action_opt_id, action in backend.actions:
            if action_opt_id != option_id:
                continue
            if hasattr(action, 'get_paths'):
                for path in action.get_paths():
                    try:
                        size = FileUtilities.getsize(path)
                    except (OSError, PermissionError):
                        size = 0
                    files.append((path, size or 0))
            else:
                for cmd in action.get_commands():
                    cmd_path = getattr(cmd, 'path', None)
                    if cmd_path:
                        try:
                            size = FileUtilities.getsize(cmd_path)
                        except (OSError, PermissionError):
                            size = 0
                        files.append((cmd_path, size or 0))

        # Route B: legacy cleaners that override get_commands() directly
        if not files:
            for cmd in backend.get_commands(option_id):
                cmd_path = getattr(cmd, 'path', None)
                if cmd_path:
                    try:
                        size = FileUtilities.getsize(cmd_path)
                    except (OSError, PermissionError):
                        size = 0
                    files.append((cmd_path, size or 0))
    except Exception:
        logger.exception("Error collecting files for %s / %s", cleaner_id, option_id)

    return files
