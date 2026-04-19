# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Main window for the experimental wxPython GUI (MVP).
"""

import logging
import os
import subprocess
import sys

import wx
from wx.lib.agw.customtreectrl import (
    CustomTreeCtrl,
    TR_AUTO_CHECK_CHILD,
    TR_AUTO_TOGGLE_CHILD,
    TR_DEFAULT_STYLE,
    TR_HAS_BUTTONS,
)

from bleachbit import APP_NAME, APP_VERSION, FileUtilities
from bleachbit.Cleaner import backends
from bleachbit.Language import get_text as _
from bleachbit.Options import options

from bleachbit.GUIwx.LoaderThread import LoaderThread
from bleachbit.GUIwx.WorkerThread import WorkerThread

logger = logging.getLogger(__name__)


# Results ListCtrl columns.
COL_CLEANER = 0
COL_OPTION = 1
COL_PATH = 2
COL_SIZE = 3
COL_ACTION = 4


class MainFrame(wx.Frame):
    """Top-level window for the wx MVP."""

    def __init__(self):
        title = '%s %s (wx MVP)' % (APP_NAME, APP_VERSION)
        super().__init__(None, title=title, size=(900, 650))
        self.SetMinSize((640, 480))

        # Per-(cleaner, option) size tracking.  Key '-1' means total.
        self._item_map = {}  # (cleaner_id, option_id) -> TreeItemId
        self._worker_thread = None
        self._loader_thread = None
        # Raw byte sizes keyed by results row index, so sorting by size
        # is numeric even though the visible column is humanised.
        self._row_sizes = []

        self._build_ui()
        self._build_menu()

        self.Bind(wx.EVT_CLOSE, self._on_close)

        # Kick off cleaner registration after the window is shown.
        wx.CallAfter(self._load_cleaners)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar ------------------------------------------------------
        toolbar = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_preview = wx.Button(panel, label=_('Preview'))
        self.btn_clean = wx.Button(panel, label=_('Clean'))
        self.btn_abort = wx.Button(panel, label=_('Abort'))
        self.btn_abort.Disable()

        self.btn_preview.Bind(wx.EVT_BUTTON, self._on_preview)
        self.btn_clean.Bind(wx.EVT_BUTTON, self._on_clean)
        self.btn_abort.Bind(wx.EVT_BUTTON, self._on_abort)

        for b in (self.btn_preview, self.btn_clean, self.btn_abort):
            toolbar.Add(b, 0, wx.RIGHT, 6)

        toolbar.AddStretchSpacer()
        self.chk_expand = wx.CheckBox(panel, label=_('Expand all'))
        self.chk_expand.Bind(wx.EVT_CHECKBOX, self._on_toggle_expand)
        toolbar.Add(self.chk_expand, 0, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(toolbar, 0, wx.ALL | wx.EXPAND, 6)

        # Splitter: left = tree, right = log -----------------------------
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)

        self.tree = CustomTreeCtrl(
            splitter,
            agwStyle=TR_DEFAULT_STYLE
            | TR_HAS_BUTTONS
            | TR_AUTO_CHECK_CHILD
            | TR_AUTO_TOGGLE_CHILD,
        )
        # Placeholder root; hidden.
        self._root = self.tree.AddRoot('')

        right = wx.Panel(splitter)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(right)

        # Results tab ---------------------------------------------------
        self.results = wx.ListCtrl(
            self.notebook,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN,
        )
        self.results.InsertColumn(COL_CLEANER, _('Cleaner'), width=120)
        self.results.InsertColumn(COL_OPTION, _('Option'), width=120)
        self.results.InsertColumn(COL_PATH, _('Path'), width=360)
        self.results.InsertColumn(
            COL_SIZE, _('Size'), format=wx.LIST_FORMAT_RIGHT, width=90)
        self.results.InsertColumn(COL_ACTION, _('Action'), width=100)
        self.results.Bind(
            wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_result_context_menu)
        self.results.Bind(wx.EVT_LIST_COL_CLICK, self._on_result_col_click)
        self.notebook.AddPage(self.results, _('Results'))

        # Log tab -------------------------------------------------------
        self.log = wx.TextCtrl(
            self.notebook,
            style=wx.TE_MULTILINE | wx.TE_READONLY
            | wx.TE_DONTWRAP | wx.HSCROLL,
        )
        font = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_TELETYPE))
        self.log.SetFont(font)
        self.notebook.AddPage(self.log, _('Log'))

        right_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 2)
        right.SetSizer(right_sizer)

        splitter.SplitVertically(self.tree, right, 320)
        outer.Add(splitter, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)

        # Progress bar and status --------------------------------------
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.gauge = wx.Gauge(panel, range=100)
        self.status = wx.StaticText(panel, label='')
        status_sizer.Add(self.gauge, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        status_sizer.Add(self.status, 1, wx.ALIGN_CENTER_VERTICAL)
        outer.Add(status_sizer, 0, wx.ALL | wx.EXPAND, 6)

        panel.SetSizer(outer)

        self.CreateStatusBar(2)
        self.SetStatusWidths([-3, -1])
        self.SetStatusText(_('Ready.'))

    def _build_menu(self):
        mb = wx.MenuBar()
        file_menu = wx.Menu()
        item_exit = file_menu.Append(wx.ID_EXIT, _('Exit'))
        self.Bind(wx.EVT_MENU, lambda _e: self.Close(), item_exit)
        mb.Append(file_menu, _('File'))

        help_menu = wx.Menu()
        item_about = help_menu.Append(wx.ID_ABOUT, _('About'))
        self.Bind(wx.EVT_MENU, self._on_about, item_about)
        mb.Append(help_menu, _('Help'))

        self.SetMenuBar(mb)

    # ------------------------------------------------------------------
    # Cleaner registration (async)
    # ------------------------------------------------------------------
    def _load_cleaners(self):
        self.SetStatusText(_('Loading cleaners\u2026'))
        self.gauge.Pulse()
        # Disable action buttons until registration finishes.
        self.btn_preview.Disable()
        self.btn_clean.Disable()
        self._loader_thread = LoaderThread(
            on_progress=self._on_loader_progress,
            on_done=self._on_loader_done,
            on_error=self._on_loader_error,
        )
        self._loader_thread.start()

    def _on_loader_progress(self, msg):
        self.SetStatusText(msg)

    def _on_loader_done(self):
        self._loader_thread = None
        self.gauge.SetValue(0)
        self._populate_tree()
        self.btn_preview.Enable()
        self.btn_clean.Enable()
        self.SetStatusText(
            _('%d cleaners loaded.') % len(backends))

    def _on_loader_error(self, _exc):
        self._loader_thread = None
        self.gauge.SetValue(0)
        wx.MessageBox(
            _('Failed to load cleaners.  See log for details.'),
            APP_NAME, wx.ICON_ERROR)

    def _populate_tree(self):
        self.tree.DeleteChildren(self._root)
        self._item_map.clear()
        for cleaner_id in sorted(backends):
            cleaner = backends[cleaner_id]
            name = cleaner.get_name() or cleaner_id
            parent = self.tree.AppendItem(
                self._root, name, ct_type=1)
            self.tree.SetItemData(parent, (cleaner_id, None))
            self._item_map[(cleaner_id, -1)] = parent
            for option_id, option_name in cleaner.get_options():
                warning = cleaner.get_warning(option_id)
                label = option_name
                if warning:
                    # Mark warnings with an exclamation mark; the full
                    # text appears on hover / status.
                    label = u'\u26a0  ' + label
                child = self.tree.AppendItem(parent, label, ct_type=1)
                self.tree.SetItemData(child, (cleaner_id, option_id))
                self._item_map[(cleaner_id, option_id)] = child

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------
    def _collect_operations(self):
        """Return dict {cleaner_id: [option_id, ...]} for checked options."""
        operations = {}
        cleaner_item, cookie = self.tree.GetFirstChild(self._root)
        while cleaner_item and cleaner_item.IsOk():
            opt_item, opt_cookie = self.tree.GetFirstChild(cleaner_item)
            while opt_item and opt_item.IsOk():
                if self.tree.IsItemChecked(opt_item):
                    data = self.tree.GetItemData(opt_item)
                    if data and data[1] is not None:
                        cid, oid = data
                        operations.setdefault(cid, []).append(oid)
                opt_item, opt_cookie = self.tree.GetNextChild(
                    cleaner_item, opt_cookie)
            cleaner_item, cookie = self.tree.GetNextChild(
                self._root, cookie)
        for k in list(operations):
            operations[k].sort()
        return operations

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def _on_toggle_expand(self, _evt):
        if self.chk_expand.IsChecked():
            self.tree.ExpandAll()
        else:
            self.tree.CollapseAll()

    def _on_preview(self, _evt):
        self._start_worker(really_delete=False)

    def _on_clean(self, _evt):
        operations = self._collect_operations()
        if not operations:
            self._no_selection()
            return
        msg = _(
            'Are you sure you want to permanently delete the selected items?')
        dlg = wx.MessageDialog(
            self, msg, APP_NAME,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        try:
            if dlg.ShowModal() != wx.ID_YES:
                return
        finally:
            dlg.Destroy()
        self._start_worker(really_delete=True, operations=operations)

    def _on_abort(self, _evt):
        if self._worker_thread is not None:
            self.SetStatusText(_('Aborting\u2026'))
            self._worker_thread.abort()

    def _on_about(self, _evt):
        info = wx.adv.AboutDialogInfo() if hasattr(wx, 'adv') else None
        if info is None:
            import wx.adv  # pylint: disable=import-outside-toplevel
            info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION + ' (wx MVP)')
        info.SetDescription(
            _('Experimental wxPython front-end for BleachBit.'))
        import wx.adv  # pylint: disable=import-outside-toplevel
        wx.adv.AboutBox(info)

    def _on_close(self, evt):
        if self._worker_thread is not None and self._worker_thread.is_alive():
            dlg = wx.MessageDialog(
                self,
                _('A cleaning operation is running.  Abort and exit?'),
                APP_NAME, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
            try:
                if dlg.ShowModal() != wx.ID_YES:
                    evt.Veto()
                    return
            finally:
                dlg.Destroy()
            self._worker_thread.abort()
            self._worker_thread.join(timeout=5.0)
        evt.Skip()

    # ------------------------------------------------------------------
    # Worker lifecycle
    # ------------------------------------------------------------------
    def _no_selection(self):
        wx.MessageBox(
            _('You must select an operation.'),
            APP_NAME, wx.ICON_INFORMATION)

    def _start_worker(self, really_delete, operations=None):
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        if operations is None:
            operations = self._collect_operations()
        if not operations:
            self._no_selection()
            return
        self.log.SetValue('')
        self._clear_results()
        self.gauge.SetValue(0)
        self.status.SetLabel('')
        self.btn_preview.Disable()
        self.btn_clean.Disable()
        self.btn_abort.Enable()
        self._current_really_delete = really_delete
        self._worker_thread = WorkerThread(self, really_delete, operations)
        self._worker_thread.start()

    def _clear_results(self):
        self.results.DeleteAllItems()
        self._row_sizes = []

    # ------------------------------------------------------------------
    # Worker UI callbacks (invoked on main thread via WxUIProxy)
    # ------------------------------------------------------------------
    def append_text(self, msg, tag=None):
        if tag == 'error':
            # No rich formatting yet; prefix.
            msg = '[!] ' + msg
        self.log.AppendText(msg)

    def append_row(self, operation_option, label, size, path):
        """Add one structured result row (called via WxUIProxy).

        ``operation_option`` is 'operation.option_id' as passed to
        :meth:`bleachbit.Worker.Worker.execute`.  ``label`` is the
        action label ('delete', 'shred', 'truncate', ...).
        """
        if '.' in operation_option:
            op_id, opt_id = operation_option.split('.', 1)
        else:
            op_id, opt_id = operation_option, ''
        cleaner = backends.get(op_id)
        cleaner_name = cleaner.get_name() if cleaner else op_id
        option_name = opt_id
        if cleaner:
            for o_id, o_name in cleaner.get_options():
                if o_id == opt_id:
                    option_name = o_name
                    break
        if isinstance(size, int):
            human_size = FileUtilities.bytes_to_human(size)
            size_sort = size
        else:
            human_size = '?'
            size_sort = -1
        idx = self.results.InsertItem(
            self.results.GetItemCount(), cleaner_name)
        self.results.SetItem(idx, COL_OPTION, option_name)
        self.results.SetItem(idx, COL_PATH, path or '')
        self.results.SetItem(idx, COL_SIZE, human_size)
        self.results.SetItem(idx, COL_ACTION, label or '')
        self._row_sizes.append(size_sort)

    def update_progress_bar(self, value):
        if isinstance(value, str):
            self.status.SetLabel(value)
            return
        try:
            frac = float(value)
        except (TypeError, ValueError):
            return
        frac = max(0.0, min(1.0, frac))
        self.gauge.SetValue(int(frac * 100))

    def update_total_size(self, size):
        human = FileUtilities.bytes_to_human(size)
        self.SetStatusText(_('Total: %s') % human, 1)

    def update_item_size(self, op, opid, size):
        human = FileUtilities.bytes_to_human(size)
        if opid == -1:
            key = (op, -1)
        else:
            key = (op, opid)
        item = self._item_map.get(key)
        if not item:
            return
        cleaner = backends.get(op)
        if opid == -1:
            base = cleaner.get_name() if cleaner else op
        else:
            base = None
            if cleaner:
                for o_id, o_name in cleaner.get_options():
                    if o_id == opid:
                        base = o_name
                        break
            if base is None:
                base = opid
        self.tree.SetItemText(item, '%s  \u2014  %s' % (base, human))

    def worker_done(self, worker, really_delete):
        self.btn_preview.Enable()
        self.btn_clean.Enable()
        self.btn_abort.Disable()
        self.gauge.SetValue(100)
        if worker.is_aborted:
            done_msg = _('Aborted.')
        else:
            done_msg = _('Done.')
        # Append summary to status bar.
        n_rows = self.results.GetItemCount()
        if really_delete:
            summary = _('%s\u2003Deleted %d items.') % (done_msg, n_rows)
        else:
            summary = _('%s\u2003%d items in preview.') % (done_msg, n_rows)
        self.status.SetLabel(summary)
        self.SetStatusText(done_msg)
        self._worker_thread = None

    # ------------------------------------------------------------------
    # Results context menu
    # ------------------------------------------------------------------
    def _selected_paths(self):
        paths = []
        idx = self.results.GetFirstSelected()
        while idx != -1:
            paths.append(self.results.GetItemText(idx, COL_PATH))
            idx = self.results.GetNextSelected(idx)
        return [p for p in paths if p]

    def _on_result_context_menu(self, _evt):
        paths = self._selected_paths()
        if not paths:
            return
        menu = wx.Menu()
        item_copy = menu.Append(wx.ID_ANY, _('Copy path'))
        item_open = menu.Append(wx.ID_ANY, _('Open file location'))
        item_skip = menu.Append(
            wx.ID_ANY, _('Always skip this path (add to keep list)'))
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._copy_paths(paths), item_copy)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._open_locations(paths), item_open)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._whitelist_paths(paths), item_skip)
        self.results.PopupMenu(menu)
        menu.Destroy()

    def _copy_paths(self, paths):
        if not wx.TheClipboard.Open():
            return
        try:
            wx.TheClipboard.SetData(
                wx.TextDataObject('\n'.join(paths)))
        finally:
            wx.TheClipboard.Close()
        self.SetStatusText(
            _('Copied %d path(s) to clipboard.') % len(paths))

    def _open_locations(self, paths):
        # De-duplicate parent directories to avoid opening the same
        # folder many times when several selected rows share a parent.
        seen = set()
        for path in paths:
            folder = os.path.dirname(path) or path
            if folder in seen:
                continue
            seen.add(folder)
            self._open_folder(path, folder)

    @staticmethod
    def _open_folder(path, folder):
        """Open the file manager at ``folder`` and, on Windows, select
        ``path`` inside it.
        """
        try:
            if os.name == 'nt':
                # Windows Explorer can highlight the file.
                if os.path.exists(path):
                    subprocess.Popen(
                        ['explorer', '/select,', os.path.normpath(path)])
                else:
                    os.startfile(folder)  # pylint: disable=no-member
            elif sys.platform == 'darwin':
                if os.path.exists(path):
                    subprocess.Popen(['open', '-R', path])
                else:
                    subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except OSError:
            logger.exception('Failed to open %s', folder)

    def _whitelist_paths(self, paths):
        existing = options.get_whitelist_paths()
        existing_paths = {p for (_t, p) in existing}
        added = 0
        new_entries = list(existing)
        for path in paths:
            if not path or path in existing_paths:
                continue
            entry_type = 'folder' if os.path.isdir(path) else 'file'
            new_entries.append((entry_type, path))
            existing_paths.add(path)
            added += 1
        if added:
            options.set_whitelist_paths(new_entries)
        self.SetStatusText(
            _('Added %d path(s) to keep list.') % added)

    def _on_result_col_click(self, evt):
        col = evt.GetColumn()
        self._sort_results(col)

    def _sort_results(self, col):
        """Sort the results ListCtrl by ``col``.

        ``wx.ListCtrl`` does not sort itself; rebuild rows in-memory.
        """
        n = self.results.GetItemCount()
        rows = []
        for i in range(n):
            row = [self.results.GetItemText(i, c) for c in range(5)]
            size_val = (self._row_sizes[i]
                        if i < len(self._row_sizes) else -1)
            rows.append((row, size_val))
        if col == COL_SIZE:
            rows.sort(key=lambda r: r[1])
        else:
            rows.sort(key=lambda r: r[0][col].lower())
        self.results.DeleteAllItems()
        self._row_sizes = []
        for row, size_val in rows:
            idx = self.results.InsertItem(
                self.results.GetItemCount(), row[COL_CLEANER])
            for c in range(1, 5):
                self.results.SetItem(idx, c, row[c])
            self._row_sizes.append(size_val)
