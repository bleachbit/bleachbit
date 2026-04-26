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
    EVT_TREE_ITEM_CHECKED,
    TR_DEFAULT_STYLE,
    TR_HAS_BUTTONS,
)

from bleachbit import APP_NAME, APP_VERSION, Cleaner, FileUtilities
from bleachbit.Cleaner import backends
from bleachbit.Language import get_text as _
from bleachbit.Log import GtkLoggerHandler
from bleachbit.Options import options

from bleachbit.GUIwx.LoaderThread import LoaderThread
from bleachbit.GUIwx.PreferencesDialog import PreferencesDialog
from bleachbit.GUIwx.WorkerThread import WorkerThread

logger = logging.getLogger(__name__)

# Keywords used by the "Select safe" toolbar button to select low-risk
# options (caches, logs, vacuum, temporary files).  Kept intentionally
# simple; the logic may later move to CleanerML metadata.
_SAFE_OPTION_KEYWORDS = ('cache', 'log', 'vacuum', 'temp')

# Hard cap on the number of lines that the Log ``wx.TextCtrl`` will
# render.  Previewing a large cache (e.g. 100k+ Firefox files) calls
# ``append_text`` once per file; every batched ``Thaw`` then re-lays
# out the entire text buffer, which on GTK is roughly O(N) per thaw
# and freezes the UI.  All entries are still retained in
# ``_log_entries`` (so a filtered view can re-render up to the cap),
# but the widget itself is capped.  The structured Results tab is
# virtual and has no such cap.
_LOG_DISPLAY_LINE_CAP = 5000


# Results ListCtrl columns.
COL_CLEANER = 0
COL_OPTION = 1
COL_PATH = 2
COL_SIZE = 3
COL_ACTION = 4

_ROW_FIELDS = ('cleaner_name', 'option_name', 'path', 'size_human', 'action')


class _VirtualResultsList(wx.ListCtrl):
    """Virtual ``wx.ListCtrl`` backed by ``MainFrame._visible_rows()``.

    A virtual control renders only the visible items on demand, so
    ``append_row`` becomes O(1) regardless of how many rows we have
    already accumulated.  Without this, inserting tens of thousands
    of rows during a preview of, for example, Firefox cache freezes
    the wx main thread for many seconds.
    """

    def __init__(self, parent, owner):
        super().__init__(
            parent,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.BORDER_SUNKEN,
        )
        self._owner = owner

    # ``OnGetItemText`` is called by wx for every cell it needs to
    # paint.  Keep it trivial.
    def OnGetItemText(self, item, column):  # noqa: N802 - wx naming
        rows = self._owner._visible
        if not 0 <= item < len(rows):
            return ''
        row = rows[item]
        field = _ROW_FIELDS[column]
        return row[field]


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
        # All result rows as dicts {cleaner_id, option_id, cleaner_name,
        # option_name, path, size, size_human, action}.  ``_visible`` is
        # the filtered/sorted projection that the virtual ListCtrl reads
        # from; it is the same list object as ``_rows`` when no filter
        # is active.
        self._rows = []
        self._visible = self._rows
        # All log entries as (msg, tag).  The log TextCtrl is a filtered
        # projection of this, capped at ``_LOG_DISPLAY_LINE_CAP`` lines.
        self._log_entries = []
        # Number of lines currently rendered in ``self.log``; when it
        # reaches the cap we stop writing to the widget to avoid the
        # O(N) GTK relayout that freezes the UI on huge previews.
        self._log_display_count = 0
        self._log_truncated = False
        # Filter state.
        self._filter_text = ''
        self._errors_only = False
        # Block the tree-check handler while we restore persisted state
        # or while we programmatically cascade check changes.
        self._suspend_check_persist = False
        self._suspend_cascade = False
        # Current tree filter query (case-insensitive substring match).
        self._tree_filter_text = ''
        # True while WxUIProxy is delivering a batch of worker callbacks.
        self._in_batch = False

        self._build_ui()
        self._build_menu()

        # Route ``bleachbit`` logger records (e.g. Worker's per-file
        # "Access denied: ..." errors) to the Log tab.  Despite its
        # name, ``GtkLoggerHandler`` is not GTK-specific: it just calls
        # the supplied callback.  The callback is marshalled to the wx
        # main thread because Worker runs on a background thread.
        self._log_handler = GtkLoggerHandler(self._log_from_any_thread)
        logging.getLogger('bleachbit').addHandler(self._log_handler)

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
        self.btn_select_safe = wx.Button(panel, label=_('Select safe'))
        self.btn_select_safe.SetToolTip(
            _('Check only low-risk options (cache, log, vacuum, '
              'temporary files).'))
        self.btn_deselect_all = wx.Button(panel, label=_('Deselect all'))
        self.btn_deselect_all.SetToolTip(
            _('Uncheck every option in the tree.'))

        self.btn_preview.Bind(wx.EVT_BUTTON, self._on_preview)
        self.btn_clean.Bind(wx.EVT_BUTTON, self._on_clean)
        self.btn_abort.Bind(wx.EVT_BUTTON, self._on_abort)
        self.btn_select_safe.Bind(wx.EVT_BUTTON, self._on_select_safe)
        self.btn_deselect_all.Bind(wx.EVT_BUTTON, self._on_deselect_all)

        for b in (self.btn_preview, self.btn_clean, self.btn_abort,
                  self.btn_select_safe, self.btn_deselect_all):
            toolbar.Add(b, 0, wx.RIGHT, 6)

        toolbar.AddStretchSpacer()
        self.chk_expand = wx.CheckBox(panel, label=_('Expand all'))
        self.chk_expand.Bind(wx.EVT_CHECKBOX, self._on_toggle_expand)
        toolbar.Add(self.chk_expand, 0, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(toolbar, 0, wx.ALL | wx.EXPAND, 6)

        # Splitter: left = tree (+ its search box), right = log ---------
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)

        tree_panel = wx.Panel(splitter)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree_search = wx.SearchCtrl(
            tree_panel, style=wx.TE_PROCESS_ENTER)
        self.tree_search.SetDescriptiveText(_('Search options\u2026'))
        self.tree_search.ShowCancelButton(True)
        self.tree_search.Bind(wx.EVT_TEXT, self._on_tree_filter_changed)
        self.tree_search.Bind(
            wx.EVT_SEARCHCTRL_CANCEL_BTN,
            lambda _e: self.tree_search.SetValue(''))
        tree_sizer.Add(self.tree_search, 0, wx.EXPAND | wx.BOTTOM, 2)
        self.tree = CustomTreeCtrl(
            tree_panel,
            agwStyle=TR_DEFAULT_STYLE | TR_HAS_BUTTONS,
        )
        # Placeholder root; hidden.
        self._root = self.tree.AddRoot('')
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,
                       self._on_tree_context_menu)
        tree_sizer.Add(self.tree, 1, wx.EXPAND)
        tree_panel.SetSizer(tree_sizer)

        right = wx.Panel(splitter)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Filter bar (applies to both tabs) ----------------------------
        filter_row = wx.BoxSizer(wx.HORIZONTAL)
        filter_row.Add(
            wx.StaticText(right, label=_('Filter:')),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.filter_entry = wx.SearchCtrl(
            right, style=wx.TE_PROCESS_ENTER)
        self.filter_entry.ShowCancelButton(True)
        self.filter_entry.Bind(wx.EVT_TEXT, self._on_filter_changed)
        self.filter_entry.Bind(
            wx.EVT_SEARCHCTRL_CANCEL_BTN,
            lambda _e: self.filter_entry.SetValue(''))
        filter_row.Add(self.filter_entry, 1, wx.ALIGN_CENTER_VERTICAL)
        self.chk_errors_only = wx.CheckBox(right, label=_('Errors only'))
        self.chk_errors_only.Bind(wx.EVT_CHECKBOX, self._on_errors_only)
        filter_row.Add(
            self.chk_errors_only, 0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        right_sizer.Add(filter_row, 0, wx.EXPAND | wx.ALL, 2)

        self.notebook = wx.Notebook(right)

        # Results tab ---------------------------------------------------
        # Virtual list: the widget pulls cells from ``self._visible``
        # via ``_VirtualResultsList.OnGetItemText`` on demand, which
        # keeps append_row O(1) even for very large previews.
        self.results = _VirtualResultsList(self.notebook, self)
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

        splitter.SplitVertically(tree_panel, right, 320)
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
        item_shred_files = file_menu.Append(
            wx.ID_ANY, _('Shred files\u2026'),
            _('Permanently delete specific files.'))
        self.Bind(wx.EVT_MENU, self._on_shred_files, item_shred_files)
        item_shred_folders = file_menu.Append(
            wx.ID_ANY, _('Shred folders\u2026'),
            _('Permanently delete specific folders.'))
        self.Bind(wx.EVT_MENU, self._on_shred_folders, item_shred_folders)
        file_menu.AppendSeparator()
        item_prefs = file_menu.Append(
            wx.ID_PREFERENCES, _('Preferences\u2026'))
        self.Bind(wx.EVT_MENU, self._on_preferences, item_prefs)
        file_menu.AppendSeparator()
        item_exit = file_menu.Append(wx.ID_EXIT, _('Exit'))
        self.Bind(wx.EVT_MENU, lambda _e: self.Close(), item_exit)
        mb.Append(file_menu, _('File'))

        help_menu = wx.Menu()
        item_about = help_menu.Append(wx.ID_ABOUT, _('About'))
        self.Bind(wx.EVT_MENU, self._on_about, item_about)
        mb.Append(help_menu, _('Help'))

        self.SetMenuBar(mb)

        # Tree-check persistence.
        self.tree.Bind(EVT_TREE_ITEM_CHECKED, self._on_tree_item_checked)

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

    def _on_loader_done(self, hidden=None):
        self._loader_thread = None
        self.gauge.SetValue(0)
        self._hidden_cleaners = set(hidden or ())
        self._populate_tree()
        self.btn_preview.Enable()
        self.btn_clean.Enable()
        n_visible = len(backends) - len(self._hidden_cleaners)
        if self._hidden_cleaners:
            self.SetStatusText(
                _('%(shown)d cleaners loaded '
                  '(%(hidden)d hidden as irrelevant).') % {
                    'shown': n_visible,
                    'hidden': len(self._hidden_cleaners)})
        else:
            self.SetStatusText(
                _('%d cleaners loaded.') % n_visible)

    def _on_loader_error(self, _exc):
        self._loader_thread = None
        self.gauge.SetValue(0)
        wx.MessageBox(
            _('Failed to load cleaners.  See log for details.'),
            APP_NAME, wx.ICON_ERROR)

    def _populate_tree(self):
        self.tree.DeleteChildren(self._root)
        self._item_map.clear()
        # Restore persisted check state from Options; skip change events
        # while we do so to avoid writing everything back out.
        self._suspend_check_persist = True
        try:
            hidden = getattr(self, '_hidden_cleaners', set())
            for cleaner_id in sorted(backends):
                cleaner = backends[cleaner_id]
                # Hide the synthetic '_gui' cleaner used for shred.
                if cleaner_id == '_gui':
                    continue
                # Auto-hide: skip cleaners that have nothing to clean.
                # The hidden set is computed off the main thread by
                # LoaderThread so this stays cheap.
                if cleaner_id in hidden:
                    continue
                name = cleaner.get_name() or cleaner_id
                parent = self.tree.AppendItem(
                    self._root, name, ct_type=1)
                # Plain 2-state checkbox.  CustomTreeCtrl's 3-state
                # click handler cycles UNCHECKED -> CHECKED ->
                # UNDETERMINED, which feels broken for a toggle, so we
                # indicate "partial" (some but not all children
                # checked) by making the parent bold in
                # _refresh_parent_state.
                self.tree.SetItemData(parent, (cleaner_id, None))
                self._item_map[(cleaner_id, -1)] = parent
                for option_id, option_name in cleaner.get_options():
                    warning = cleaner.get_warning(option_id)
                    label = option_name
                    if warning:
                        # Mark warnings with an exclamation mark; the
                        # full text appears on hover / status.
                        label = u'\u26a0  ' + label
                    child = self.tree.AppendItem(parent, label, ct_type=1)
                    self.tree.SetItemData(child, (cleaner_id, option_id))
                    self._item_map[(cleaner_id, option_id)] = child
                    if options.get_tree(cleaner_id, option_id):
                        self.tree.CheckItem(child, True)
                self._refresh_parent_state(parent)
        finally:
            self._suspend_check_persist = False
        self._apply_tree_filter()

    def _on_tree_item_checked(self, evt):
        """Cascade check state between parent and children and persist.

        Fires for both the cleaner row (parent) and the option row
        (child).  When a parent is toggled we force all its children to
        match; when a child is toggled we recompute the parent's
        all/none/mixed state and persist the child.
        """
        evt.Skip()
        if self._suspend_check_persist or self._suspend_cascade:
            return
        item = evt.GetItem()
        data = self.tree.GetItemData(item)
        if not data:
            return
        cleaner_id, option_id = data
        self._suspend_cascade = True
        try:
            if option_id is None:
                # Parent toggled by the user: propagate to children.
                checked = bool(self.tree.IsItemChecked(item))
                child, cookie = self.tree.GetFirstChild(item)
                while child and child.IsOk():
                    cdata = self.tree.GetItemData(child)
                    if bool(self.tree.IsItemChecked(child)) != checked:
                        self.tree.CheckItem(child, checked)
                        if cdata and cdata[1] is not None:
                            options.set_tree(cdata[0], cdata[1], checked)
                    child, cookie = self.tree.GetNextChild(item, cookie)
                # Parent cannot be "partial" after a user toggle; make
                # sure the bold-for-mixed styling is cleared.
                self.tree.SetItemBold(item, False)
                self.tree.RefreshLine(item)
            else:
                # Child toggled: persist and refresh the parent.
                options.set_tree(
                    cleaner_id, option_id,
                    self.tree.IsItemChecked(item))
                parent = self.tree.GetItemParent(item)
                self._refresh_parent_state(parent)
        finally:
            self._suspend_cascade = False

    def _refresh_parent_state(self, parent):
        """Sync ``parent`` checkbox + bold marker to its children.

        * All children checked -> parent CHECKED, normal weight.
        * No children checked  -> parent UNCHECKED, normal weight.
        * Some children checked -> parent CHECKED + bold (mixed hint).

        Uses ``CheckItem`` rather than ``SetItem3StateValue`` because
        the latter does not call ``RefreshLine``, leaving collapsed
        parents visually stale.
        """
        if not parent or not parent.IsOk():
            return
        n_total = 0
        n_checked = 0
        child, cookie = self.tree.GetFirstChild(parent)
        while child and child.IsOk():
            n_total += 1
            if self.tree.IsItemChecked(child):
                n_checked += 1
            child, cookie = self.tree.GetNextChild(parent, cookie)
        if n_total == 0:
            return
        target = n_checked > 0
        is_partial = 0 < n_checked < n_total
        prev = self._suspend_cascade
        self._suspend_cascade = True
        try:
            if bool(self.tree.IsItemChecked(parent)) != target:
                self.tree.CheckItem(parent, target)
            self.tree.SetItemBold(parent, is_partial)
            self.tree.RefreshLine(parent)
        finally:
            self._suspend_cascade = prev

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
            # CustomTreeCtrl does not implement CollapseAll; walk the
            # top-level cleaner items and collapse each one instead.
            item, cookie = self.tree.GetFirstChild(self._root)
            while item and item.IsOk():
                self.tree.Collapse(item)
                item, cookie = self.tree.GetNextChild(self._root, cookie)

    # ------------------------------------------------------------------
    # Tree filter / bulk-selection helpers
    # ------------------------------------------------------------------
    def _iter_tree(self):
        """Yield (parent_item, child_item, cleaner_id, option_id)."""
        parent, pcookie = self.tree.GetFirstChild(self._root)
        while parent and parent.IsOk():
            child, ccookie = self.tree.GetFirstChild(parent)
            while child and child.IsOk():
                cdata = self.tree.GetItemData(child) or (None, None)
                yield parent, child, cdata[0], cdata[1]
                child, ccookie = self.tree.GetNextChild(parent, ccookie)
            parent, pcookie = self.tree.GetNextChild(self._root, pcookie)

    def _on_tree_filter_changed(self, _evt):
        self._tree_filter_text = (
            self.tree_search.GetValue().strip().lower())
        self._apply_tree_filter()

    def _apply_tree_filter(self):
        """Hide tree rows that do not match ``self._tree_filter_text``."""
        needle = self._tree_filter_text
        parent, pcookie = self.tree.GetFirstChild(self._root)
        while parent and parent.IsOk():
            pname = self.tree.GetItemText(parent).lower()
            parent_match = (not needle) or (needle in pname)
            any_child_visible = False
            child, ccookie = self.tree.GetFirstChild(parent)
            while child and child.IsOk():
                cname = self.tree.GetItemText(child).lower()
                visible = (not needle) or parent_match or (needle in cname)
                self.tree.HideItem(child, not visible)
                any_child_visible = any_child_visible or visible
                child, ccookie = self.tree.GetNextChild(parent, ccookie)
            self.tree.HideItem(
                parent, not (parent_match or any_child_visible))
            if needle and (parent_match or any_child_visible):
                self.tree.Expand(parent)
            parent, pcookie = self.tree.GetNextChild(self._root, pcookie)
        self.tree.Refresh()

    def _set_all_checked(self, checked, predicate=None):
        """Check or uncheck every option that ``predicate`` accepts.

        ``predicate`` receives ``(cleaner_id, option_id, option_label)``.
        Runs with the cascade guard active so we only refresh each
        parent once at the end.
        """
        self._suspend_cascade = True
        touched_parents = set()
        try:
            for parent, child, cid, oid in self._iter_tree():
                if oid is None:
                    continue
                if predicate is not None:
                    label = self.tree.GetItemText(child)
                    if not predicate(cid, oid, label):
                        continue
                if self.tree.IsItemChecked(child) != checked:
                    self.tree.CheckItem(child, checked)
                    options.set_tree(cid, oid, checked)
                touched_parents.add(parent)
        finally:
            self._suspend_cascade = False
        for parent in touched_parents:
            self._refresh_parent_state(parent)

    def _on_select_safe(self, _evt):
        """Check only low-risk options; uncheck everything else."""
        def is_safe(_cid, _oid, label):
            low = label.lower()
            return any(k in low for k in _SAFE_OPTION_KEYWORDS)
        # First uncheck all, then check the safe ones.  Doing it in two
        # passes keeps the final state deterministic regardless of the
        # user's previous selections.
        self._set_all_checked(False)
        self._set_all_checked(True, predicate=is_safe)
        self.SetStatusText(_('Selected low-risk options.'))

    def _on_deselect_all(self, _evt):
        self._set_all_checked(False)
        self.SetStatusText(_('Unchecked all options.'))

    def _on_tree_context_menu(self, evt):
        item = evt.GetItem()
        menu = wx.Menu()
        # Per-option actions (only when right-clicking an option row).
        if item and item.IsOk():
            data = self.tree.GetItemData(item)
            if data and data[1] is not None:
                cid, oid = data
                cleaner = backends.get(cid)
                cname = cleaner.get_name() if cleaner else cid
                oname = oid
                if cleaner:
                    for o_id, o_name in cleaner.get_options():
                        if o_id == oid:
                            oname = o_name
                            break
                label = _('%(cleaner)s \u2014 %(option)s') % {
                    'cleaner': cname, 'option': oname}
                mi_preview_one = menu.Append(
                    wx.ID_ANY, _('Preview only %s') % label)
                mi_clean_one = menu.Append(
                    wx.ID_ANY, _('Clean only %s') % label)
                mi_filter_log = menu.Append(
                    wx.ID_ANY, _('Filter log by %s') % label)
                self.Bind(
                    wx.EVT_MENU,
                    lambda _e, c=cid, o=oid:
                        self._run_single_option(c, o, really_delete=False),
                    mi_preview_one)
                self.Bind(
                    wx.EVT_MENU,
                    lambda _e, c=cid, o=oid:
                        self._run_single_option(c, o, really_delete=True),
                    mi_clean_one)
                self.Bind(
                    wx.EVT_MENU,
                    lambda _e, text=oname: self._filter_log_by(text),
                    mi_filter_log)
                menu.AppendSeparator()
            elif data and data[1] is None:
                # Parent row: quick (un)check all children.
                mi_check_cleaner = menu.Append(
                    wx.ID_ANY, _('Check all options in this cleaner'))
                mi_uncheck_cleaner = menu.Append(
                    wx.ID_ANY, _('Uncheck all options in this cleaner'))
                self.Bind(
                    wx.EVT_MENU,
                    lambda _e, p=item: self._set_parent_children(p, True),
                    mi_check_cleaner)
                self.Bind(
                    wx.EVT_MENU,
                    lambda _e, p=item: self._set_parent_children(p, False),
                    mi_uncheck_cleaner)
                menu.AppendSeparator()
        mi_deselect = menu.Append(
            wx.ID_ANY, _('Deselect all options'))
        self.Bind(wx.EVT_MENU, self._on_deselect_all, mi_deselect)
        mi_safe = menu.Append(
            wx.ID_ANY, _('Select safe (cache, log, vacuum, temp)'))
        self.Bind(wx.EVT_MENU, self._on_select_safe, mi_safe)
        self.tree.PopupMenu(menu)
        menu.Destroy()

    def _run_single_option(self, cleaner_id, option_id, really_delete):
        """Preview or clean a single (cleaner, option) without touching
        the user's tree selection.
        """
        if self._worker_thread is not None and self._worker_thread.is_alive():
            wx.MessageBox(
                _('An operation is already running.'),
                APP_NAME, wx.ICON_INFORMATION)
            return
        if really_delete:
            msg = _('Are you sure you want to permanently delete '
                    'the selected items?')
            dlg = wx.MessageDialog(
                self, msg, APP_NAME,
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
            try:
                if dlg.ShowModal() != wx.ID_YES:
                    return
            finally:
                dlg.Destroy()
        self._start_worker(
            really_delete=really_delete,
            operations={cleaner_id: [option_id]})

    def _filter_log_by(self, text):
        """Apply ``text`` as the result/log filter and focus the Log tab."""
        self.filter_entry.SetValue(text)
        # SetValue fires EVT_TEXT, which calls _on_filter_changed.
        self.notebook.SetSelection(1)
        self.SetStatusText(_('Log filtered by %s.') % text)

    def _set_parent_children(self, parent, checked):
        """Check/uncheck every child of ``parent`` and refresh state."""
        self._suspend_cascade = True
        try:
            child, cookie = self.tree.GetFirstChild(parent)
            while child and child.IsOk():
                cdata = self.tree.GetItemData(child)
                if self.tree.IsItemChecked(child) != checked:
                    self.tree.CheckItem(child, checked)
                    if cdata and cdata[1] is not None:
                        options.set_tree(cdata[0], cdata[1], checked)
                child, cookie = self.tree.GetNextChild(parent, cookie)
        finally:
            self._suspend_cascade = False
        self._refresh_parent_state(parent)

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
        import wx.adv  # pylint: disable=import-outside-toplevel
        info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION + ' (wx MVP)')
        info.SetDescription(
            _('Experimental wxPython front-end for BleachBit.'))
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
        # Detach the log handler so any stray worker-thread log
        # records after shutdown do not try to touch destroyed widgets.
        handler = getattr(self, '_log_handler', None)
        if handler is not None:
            logging.getLogger('bleachbit').removeHandler(handler)
            self._log_handler = None
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
        self._log_entries = []
        self._log_display_count = 0
        self._log_truncated = False
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
        self._rows = []
        self._visible = self._rows
        self.results.SetItemCount(0)

    # ------------------------------------------------------------------
    # Worker UI callbacks (invoked on main thread via WxUIProxy)
    # ------------------------------------------------------------------
    def begin_batch(self):
        """Freeze heavy widgets around a chunk of worker callbacks.

        Called by :class:`WxUIProxy` before a batch of queued events is
        delivered, so thousands of ``AppendText`` calls do not trigger a
        repaint per item.  We also suppress per-row ``SetItemCount``
        calls inside :meth:`append_row`; the count is synced in
        :meth:`end_batch` instead.
        """
        self._in_batch = True
        self.log.Freeze()

    def end_batch(self):
        """Thaw the widgets frozen by :meth:`begin_batch` and sync row count."""
        self.log.Thaw()
        self._in_batch = False
        # Single SetItemCount per chunk instead of one per appended row.
        self.results.SetItemCount(len(self._visible))

    def _log_from_any_thread(self, msg, tag=None):
        """Route a logger record to :meth:`append_text` safely.

        The ``bleachbit`` logger may fire from the Worker thread.  wx
        widgets can only be touched from the main thread, so marshal
        via ``wx.CallAfter`` when called off the main thread.
        """
        if wx.IsMainThread():
            self.append_text(msg, tag)
        else:
            wx.CallAfter(self.append_text, msg, tag)

    def append_text(self, msg, tag=None):
        self._log_entries.append((msg, tag))
        if not self._log_entry_visible(msg, tag):
            return
        # Hard cap the TextCtrl render at ``_LOG_DISPLAY_LINE_CAP``
        # lines regardless of tag: a cleaner run that errors on every
        # file (e.g. System - Localizations without root) can produce
        # tens of thousands of logger.error records, each of which
        # would otherwise trigger an O(N) GTK relayout and freeze the
        # UI.  All entries remain in ``_log_entries`` so the filter
        # and errors-only views can re-render up to the cap.
        if self._log_truncated:
            return
        if self._log_display_count >= _LOG_DISPLAY_LINE_CAP:
            self._log_truncated = True
            self.log.AppendText(
                _('\n\n[Log display truncated at %d lines; '
                  'further entries are kept in memory and can be '
                  'seen by typing a search in the filter box.]\n')
                % _LOG_DISPLAY_LINE_CAP)
            return
        # ``wx.TextCtrl.AppendText`` on GTK scrolls and repaints per
        # call; during a large preview the batching in WxUIProxy
        # already Freezes this widget for us.
        display = ('[!] ' + msg) if tag == 'error' else msg
        self.log.AppendText(display)
        self._log_display_count += 1

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
        row = {
            'cleaner_id': op_id,
            'option_id': opt_id,
            'cleaner_name': cleaner_name,
            'option_name': option_name,
            'path': path or '',
            'size': size_sort,
            'size_human': human_size,
            'action': label or '',
        }
        self._rows.append(row)
        # Fast path: when no filter is active ``_visible`` is the same
        # list object as ``_rows`` and is therefore already up to date.
        if self._visible is not self._rows and self._row_visible(row):
            self._visible.append(row)
        # Inside a WxUIProxy batch, SetItemCount is deferred to
        # end_batch so we do not call it thousands of times per second.
        if not getattr(self, '_in_batch', False):
            self.results.SetItemCount(len(self._visible))

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
    def _selected_indices(self):
        idxs = []
        idx = self.results.GetFirstSelected()
        while idx != -1:
            idxs.append(idx)
            idx = self.results.GetNextSelected(idx)
        return idxs

    def _selected_rows(self):
        """Return the row dicts behind the selected ListCtrl rows."""
        visible = self._visible_rows()
        return [visible[i] for i in self._selected_indices()
                if i < len(visible)]

    def _selected_paths(self):
        return [r['path'] for r in self._selected_rows() if r['path']]

    def _on_result_context_menu(self, _evt):
        rows = self._selected_rows()
        paths = [r['path'] for r in rows if r['path']]
        if not rows:
            return
        menu = wx.Menu()
        item_copy = menu.Append(wx.ID_ANY, _('Copy path'))
        item_copy.Enable(bool(paths))
        item_open = menu.Append(wx.ID_ANY, _('Open file location'))
        item_open.Enable(bool(paths))
        item_skip = menu.Append(
            wx.ID_ANY, _('Always skip this path (add to keep list)'))
        item_skip.Enable(bool(paths))
        # Build a de-duplicated list of (cleaner_id, option_id) pairs for
        # the "uncheck option" entry.  One menu item per distinct option
        # so the user can target exactly which cleaning option to drop.
        opt_keys = []
        seen = set()
        for row in rows:
            key = (row['cleaner_id'], row['option_id'])
            if key in seen or not row['option_id']:
                continue
            seen.add(key)
            opt_keys.append((key, row['cleaner_name'], row['option_name']))
        if opt_keys:
            menu.AppendSeparator()
        uncheck_items = []
        for key, cname, oname in opt_keys:
            label = _('Uncheck option: %s \u2014 %s') % (cname, oname)
            item = menu.Append(wx.ID_ANY, label)
            uncheck_items.append((item, key))
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._copy_paths(paths), item_copy)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._open_locations(paths), item_open)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._whitelist_paths(paths), item_skip)
        for item, key in uncheck_items:
            self.Bind(wx.EVT_MENU,
                      lambda _e, k=key: self._uncheck_option(*k), item)
        self.results.PopupMenu(menu)
        menu.Destroy()

    def _uncheck_option(self, cleaner_id, option_id):
        """Uncheck (cleaner_id, option_id) in the tree and persist."""
        item = self._item_map.get((cleaner_id, option_id))
        if item is None:
            return
        # Unchecking fires EVT_TREE_ITEM_CHECKED which persists via
        # Options.set_tree.  No extra bookkeeping needed here.
        self.tree.CheckItem(item, False)
        cleaner = backends.get(cleaner_id)
        cname = cleaner.get_name() if cleaner else cleaner_id
        self.SetStatusText(
            _('Unchecked %(cleaner)s \u2014 %(option)s.') % {
                'cleaner': cname, 'option': option_id})

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
        keys = {
            COL_CLEANER: lambda r: r['cleaner_name'].lower(),
            COL_OPTION: lambda r: r['option_name'].lower(),
            COL_PATH: lambda r: r['path'].lower(),
            COL_SIZE: lambda r: r['size'],
            COL_ACTION: lambda r: r['action'].lower(),
        }
        # Sort the underlying list, then rebuild the filter projection.
        self._rows.sort(key=keys.get(col, keys[COL_CLEANER]))
        self._refresh_results()

    # ------------------------------------------------------------------
    # Filtering (search + errors-only)
    # ------------------------------------------------------------------
    def _on_filter_changed(self, _evt):
        self._filter_text = self.filter_entry.GetValue().strip().lower()
        self._refresh_results()
        self._refresh_log()

    def _on_errors_only(self, _evt):
        self._errors_only = self.chk_errors_only.IsChecked()
        # The Results view has no 'error' concept; error messages all go
        # to the Log.  Switch to the Log tab for immediate feedback.
        if self._errors_only:
            self.notebook.SetSelection(1)
        self._refresh_results()
        self._refresh_log()

    def _row_visible(self, row):
        if self._errors_only:
            # Results rows have no error concept; hide them all when
            # "errors only" is active.
            return False
        if not self._filter_text:
            return True
        needle = self._filter_text
        for field in ('cleaner_name', 'option_name', 'path', 'action'):
            if needle in row[field].lower():
                return True
        return False

    def _log_entry_visible(self, msg, tag):
        if self._errors_only and tag != 'error':
            return False
        if self._filter_text and self._filter_text not in msg.lower():
            return False
        return True

    def _visible_rows(self):
        return self._visible

    def _refresh_results(self):
        """Rebuild ``self._visible`` from ``self._rows`` + filter."""
        if self._errors_only:
            # Results have no 'error' concept.
            self._visible = []
        elif not self._filter_text:
            self._visible = self._rows
        else:
            needle = self._filter_text
            self._visible = [
                r for r in self._rows
                if needle in r['cleaner_name'].lower()
                or needle in r['option_name'].lower()
                or needle in r['path'].lower()
                or needle in r['action'].lower()
            ]
        self.results.SetItemCount(len(self._visible))
        self.results.Refresh()

    def _refresh_log(self):
        self.log.Freeze()
        try:
            self.log.SetValue('')
            self._log_display_count = 0
            self._log_truncated = False
            for msg, tag in self._log_entries:
                if not self._log_entry_visible(msg, tag):
                    continue
                if self._log_truncated:
                    break
                if self._log_display_count >= _LOG_DISPLAY_LINE_CAP:
                    self._log_truncated = True
                    self.log.AppendText(
                        _('\n\n[Log display truncated at %d lines; '
                          'refine the filter to see more.]\n')
                        % _LOG_DISPLAY_LINE_CAP)
                    break
                display = ('[!] ' + msg) if tag == 'error' else msg
                self.log.AppendText(display)
                self._log_display_count += 1
        finally:
            self.log.Thaw()

    # ------------------------------------------------------------------
    # Shred arbitrary files / folders
    # ------------------------------------------------------------------
    def _on_shred_files(self, _evt):
        dlg = wx.FileDialog(
            self, _('Choose files to shred'),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            paths = list(dlg.GetPaths())
        finally:
            dlg.Destroy()
        self._shred_paths(paths)

    def _on_shred_folders(self, _evt):
        # wx.DirDialog does not support multi-select on all platforms,
        # so loop until the user cancels.
        paths = []
        while True:
            dlg = wx.DirDialog(
                self, _('Choose a folder to shred (Cancel to finish)'),
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
            )
            try:
                if dlg.ShowModal() != wx.ID_OK:
                    break
                paths.append(dlg.GetPath())
            finally:
                dlg.Destroy()
        if paths:
            self._shred_paths(paths)

    def _shred_paths(self, paths):
        if not paths:
            return
        if self._worker_thread is not None and self._worker_thread.is_alive():
            wx.MessageBox(
                _('An operation is already running.'),
                APP_NAME, wx.ICON_INFORMATION)
            return
        if options.get('delete_confirmation'):
            msg = _('Permanently delete the %d selected item(s)?  '
                    'This cannot be undone.') % len(paths)
            dlg = wx.MessageDialog(
                self, msg, APP_NAME,
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
            try:
                if dlg.ShowModal() != wx.ID_YES:
                    return
            finally:
                dlg.Destroy()
        # Register a transient cleaner; the GTK UI uses the same hook.
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)
        self._start_worker(
            really_delete=True, operations={'_gui': ['files']})

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------
    def _on_preferences(self, _evt):
        dlg = PreferencesDialog(self)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                dlg.commit()
        finally:
            dlg.Destroy()
