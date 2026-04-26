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
import wx.dataview as dv

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


class _SystemInformationDialog(wx.Dialog):
    """Dialog showing system information with Copy/Anonymize buttons."""

    def __init__(self, parent, text, anonymize_func):
        super().__init__(
            parent,
            # TRANSLATORS: Title of the system information dialog.
            title=_('System information'),
            size=(640, 480),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._original_text = text
        self._anonymize_func = anonymize_func

        sizer = wx.BoxSizer(wx.VERTICAL)
        self._text_ctrl = wx.TextCtrl(
            self, value=text,
            style=wx.TE_MULTILINE | wx.TE_READONLY
            | wx.TE_DONTWRAP | wx.HSCROLL,
        )
        font = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_TELETYPE))
        self._text_ctrl.SetFont(font)
        sizer.Add(self._text_ctrl, 1, wx.EXPAND | wx.ALL, 6)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        # TRANSLATORS: Button label in the system information dialog to
        # replace the username with a placeholder.
        self._btn_anonymize = wx.Button(self, label=_('Anonymize'))
        self._btn_anonymize.Bind(wx.EVT_BUTTON, self._on_anonymize)
        self._btn_copy = wx.Button(self, label=_('Copy'))
        self._btn_copy.Bind(wx.EVT_BUTTON, self._on_copy)
        btn_close = wx.Button(self, wx.ID_CLOSE, _('Close'))
        btn_close.Bind(wx.EVT_BUTTON, lambda _e: self.EndModal(wx.ID_CLOSE))
        self.SetEscapeId(wx.ID_CLOSE)
        btns.AddStretchSpacer()
        btns.Add(self._btn_anonymize, 0, wx.RIGHT, 6)
        btns.Add(self._btn_copy, 0, wx.RIGHT, 6)
        btns.Add(btn_close, 0)
        sizer.Add(btns, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(sizer)

    def _on_anonymize(self, _evt):
        anonymized = self._anonymize_func(self._text_ctrl.GetValue())
        self._text_ctrl.SetValue(anonymized)
        # Single-use button.
        self._btn_anonymize.Disable()

    def _on_copy(self, _evt):
        if not wx.TheClipboard.Open():
            return
        try:
            wx.TheClipboard.SetData(
                wx.TextDataObject(self._text_ctrl.GetValue()))
        finally:
            wx.TheClipboard.Close()


class _CleanerNode:
    """Stable identity object for a cleaner row in the tree."""
    __slots__ = ('cleaner_id', 'name', 'display')

    def __init__(self, cleaner_id, name):
        self.cleaner_id = cleaner_id
        self.name = name
        # ``display`` is what the model returns for the text column.
        # ``update_item_size`` mutates this to append a size suffix.
        self.display = name


class _OptionNode:
    """Stable identity object for an option row in the tree."""
    __slots__ = ('cleaner_id', 'option_id', 'label', 'display')

    def __init__(self, cleaner_id, option_id, label):
        self.cleaner_id = cleaner_id
        self.option_id = option_id
        self.label = label
        self.display = label


class _CleanerTreeModel(dv.PyDataViewModel):
    """``wx.dataview`` model exposing cleaners and options.

    Two columns:

    * Column 0 — boolean toggle (the per-row checkbox).  Activated by
      mouse click or by the space bar when the row is selected.  This
      maps directly to UIA's *Toggle* pattern on Windows, so screen
      readers (NVDA, JAWS, Narrator) announce the check state — the
      central reason for this rewrite.
    * Column 1 — text label (cleaner name or option label, possibly
      with a size suffix appended after a preview run).

    Check state lives in :class:`Options` (the same ``[tree]`` section
    used by the GTK UI), not in this model: ``GetValue`` reads it,
    ``SetValue`` writes it.  Cascading parent <-> children semantics
    are implemented in ``SetValue``.
    """

    def __init__(self):
        super().__init__()
        # Lifetime of the Python objects we hand to the view via
        # ``ObjectToItem`` is managed by us; ``UseWeakRefs(False)``
        # tells the C++ side it can keep them.
        self.UseWeakRefs(False)
        self._cleaners = []  # type: list[_CleanerNode]
        self._cleaner_by_id = {}
        self._options = {}   # cleaner_id -> [_OptionNode]
        self._filter = ''

    # -- data setup ---------------------------------------------------
    def set_data(self, entries):
        """Replace all data.  ``entries`` is the list produced by
        :meth:`MainFrame._populate_tree`.
        """
        self._cleaners = []
        self._cleaner_by_id = {}
        self._options = {}
        for cleaner_id, name, opts in entries:
            cn = _CleanerNode(cleaner_id, name)
            self._cleaners.append(cn)
            self._cleaner_by_id[cleaner_id] = cn
            self._options[cleaner_id] = [
                _OptionNode(cleaner_id, oid, lbl) for oid, lbl in opts]
        self.Cleared()

    def set_filter(self, text):
        self._filter = text or ''
        self.Cleared()

    # -- filter helpers ----------------------------------------------
    def _cleaner_matches(self, cn):
        if not self._filter:
            return True
        if self._filter in cn.name.lower():
            return True
        return any(self._filter in o.label.lower()
                   for o in self._options.get(cn.cleaner_id, ()))

    def _visible_cleaners(self):
        if not self._filter:
            return self._cleaners
        return [c for c in self._cleaners if self._cleaner_matches(c)]

    def _visible_options(self, cleaner_id):
        opts = self._options.get(cleaner_id, [])
        if not self._filter:
            return opts
        cn = self._cleaner_by_id.get(cleaner_id)
        if cn and self._filter in cn.name.lower():
            return opts
        return [o for o in opts if self._filter in o.label.lower()]

    def all_options(self, cleaner_id):
        return self._options.get(cleaner_id, [])

    def cleaner_node(self, cleaner_id):
        return self._cleaner_by_id.get(cleaner_id)

    def option_node(self, cleaner_id, option_id):
        for o in self._options.get(cleaner_id, ()):
            if o.option_id == option_id:
                return o
        return None

    def cleaner_nodes(self):
        return list(self._cleaners)

    def is_cleaner_partial(self, cleaner_id):
        opts = self._options.get(cleaner_id, [])
        if not opts:
            return False
        n = sum(1 for o in opts
                if options.get_tree(cleaner_id, o.option_id))
        return 0 < n < len(opts)

    def is_cleaner_any_checked(self, cleaner_id):
        return any(options.get_tree(cleaner_id, o.option_id)
                   for o in self._options.get(cleaner_id, ()))

    # -- DataViewModel interface -------------------------------------
    def IsContainer(self, item):  # noqa: N802 - wx API
        if not item:
            return True  # invisible root
        obj = self.ItemToObject(item)
        return isinstance(obj, _CleanerNode)

    def HasContainerColumns(self, item):  # noqa: N802
        # ``item`` is part of the wx interface; we always say yes so
        # cleaner rows render text + toggle just like option rows.
        del item
        return True

    def GetParent(self, item):  # noqa: N802
        if not item:
            return dv.NullDataViewItem
        obj = self.ItemToObject(item)
        if isinstance(obj, _CleanerNode):
            return dv.NullDataViewItem
        cn = self._cleaner_by_id.get(obj.cleaner_id)
        if cn is None:
            return dv.NullDataViewItem
        return self.ObjectToItem(cn)

    def GetChildren(self, parent, children):  # noqa: N802
        if not parent:
            kids = self._visible_cleaners()
        else:
            obj = self.ItemToObject(parent)
            if isinstance(obj, _CleanerNode):
                kids = self._visible_options(obj.cleaner_id)
            else:
                return 0
        for k in kids:
            children.append(self.ObjectToItem(k))
        return len(kids)

    def GetColumnCount(self):  # noqa: N802
        return 2

    def GetColumnType(self, col):  # noqa: N802
        return 'bool' if col == 0 else 'string'

    def GetValue(self, item, col):  # noqa: N802
        obj = self.ItemToObject(item)
        if col == 0:
            if isinstance(obj, _OptionNode):
                return options.get_tree(obj.cleaner_id, obj.option_id)
            return self.is_cleaner_any_checked(obj.cleaner_id)
        # Text column.
        return obj.display

    def SetValue(self, value, item, col):  # noqa: N802
        if col != 0:
            return False
        obj = self.ItemToObject(item)
        new = bool(value)
        if isinstance(obj, _OptionNode):
            options.set_tree(obj.cleaner_id, obj.option_id, new)
            cn = self._cleaner_by_id.get(obj.cleaner_id)
            if cn is not None:
                # Recompute parent's check + bold attribute.
                self.ItemChanged(self.ObjectToItem(cn))
        else:
            for o in self._options.get(obj.cleaner_id, ()):
                options.set_tree(o.cleaner_id, o.option_id, new)
                self.ValueChanged(self.ObjectToItem(o), 0)
            self.ItemChanged(item)
        return True

    def GetAttr(self, item, col, attr):  # noqa: N802
        obj = self.ItemToObject(item)
        if (isinstance(obj, _CleanerNode) and col == 1
                and self.is_cleaner_partial(obj.cleaner_id)):
            attr.SetBold(True)
            return True
        return False

    # -- label updates (size suffix) ---------------------------------
    def set_display(self, cleaner_id, option_id, display):
        if option_id is None or option_id == -1:
            cn = self._cleaner_by_id.get(cleaner_id)
            if cn is not None:
                cn.display = display
                self.ItemChanged(self.ObjectToItem(cn))
            return
        o = self.option_node(cleaner_id, option_id)
        if o is not None:
            o.display = display
            self.ItemChanged(self.ObjectToItem(o))


class MainFrame(wx.Frame):
    """Top-level window for the wx MVP."""

    def __init__(self):
        title = '%s %s (wx MVP)' % (APP_NAME, APP_VERSION)
        super().__init__(None, title=title, size=(900, 650))
        self.SetMinSize((640, 480))

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
        # Current tree filter query (case-insensitive substring match).
        self._tree_filter_text = ''
        # True while WxUIProxy is delivering a batch of worker callbacks.
        self._in_batch = False

        self._build_ui()
        self._build_menu()
        self._build_accelerators()

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
        self.btn_preview.SetToolTip(
            _('Preview what would be cleaned without deleting anything '
              '(F5).'))
        self.btn_clean = wx.Button(panel, label=_('Clean'))
        self.btn_clean.SetToolTip(
            _('Permanently delete the selected items (Ctrl+Enter).'))
        self.btn_abort = wx.Button(panel, label=_('Abort'))
        self.btn_abort.SetToolTip(
            _('Abort the running operation (Esc).'))
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
        # Accessible name for screen readers (no visible label).
        self.tree_search.SetName(_('Search cleaners and options'))
        self.tree_search.SetDescriptiveText(_('Search options\u2026'))
        self.tree_search.ShowCancelButton(True)
        self.tree_search.Bind(wx.EVT_TEXT, self._on_tree_filter_changed)
        self.tree_search.Bind(
            wx.EVT_SEARCHCTRL_CANCEL_BTN,
            lambda _e: self.tree_search.SetValue(''))
        tree_sizer.Add(self.tree_search, 0, wx.EXPAND | wx.BOTTOM, 2)
        # ``wx.dataview.DataViewCtrl`` driven by a custom
        # :class:`_CleanerTreeModel`.  Unlike ``CustomTreeCtrl`` (which
        # is owner-drawn and invisible to MSAA/UIA), DataViewCtrl maps
        # to a native UIA Grid on Windows and exposes the toggle
        # column via the *Toggle* pattern, so screen readers (NVDA,
        # JAWS, Narrator) announce the per-row check state.  This is
        # the central accessibility win for blind users.
        self.tree = dv.DataViewCtrl(
            tree_panel,
            style=dv.DV_SINGLE | dv.DV_NO_HEADER | dv.DV_ROW_LINES,
        )
        self.tree.SetName(_('Cleaners'))
        self._tree_model = _CleanerTreeModel()
        self.tree.AssociateModel(self._tree_model)
        # ``AssociateModel`` does not take ownership in PyDataViewModel;
        # ``DecRef`` balances the implicit ``IncRef`` so the model is
        # garbage-collected with the frame.
        self._tree_model.DecRef()
        # Toggle column: activatable so a click or space bar toggles
        # the bool, which the model persists via ``Options.set_tree``.
        toggle = dv.DataViewToggleRenderer(
            mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        col_toggle = dv.DataViewColumn(
            _('On'), toggle, 0, width=44,
            align=wx.ALIGN_CENTER)
        self.tree.AppendColumn(col_toggle)
        text = dv.DataViewTextRenderer()
        col_text = dv.DataViewColumn(
            _('Cleaner'), text, 1, width=260,
            align=wx.ALIGN_LEFT,
            flags=dv.DATAVIEW_COL_RESIZABLE)
        self.tree.AppendColumn(col_text)
        # By default ``DataViewCtrl`` draws the tree expander button on
        # the first column, which would overlap the checkbox and eat
        # its clicks.  Move the expander to the text column so column 0
        # is dedicated to the toggle.
        self.tree.SetExpanderColumn(col_text)
        self.tree.Bind(
            dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
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
        self.filter_entry.SetName(_('Filter results and log'))
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
        self.results.SetName(_('Results'))
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
        self.log.SetName(_('Log'))
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
        self.gauge.SetName(_('Progress'))
        self.status = wx.StaticText(panel, label='')
        self.status.SetName(_('Status'))
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
            wx.ID_ANY, _('Shred files\u2026') + '\tCtrl+Shift+F',
            _('Permanently delete specific files.'))
        self.Bind(wx.EVT_MENU, self._on_shred_files, item_shred_files)
        item_shred_folders = file_menu.Append(
            wx.ID_ANY, _('Shred folders\u2026') + '\tCtrl+Shift+D',
            _('Permanently delete specific folders.'))
        self.Bind(wx.EVT_MENU, self._on_shred_folders, item_shred_folders)
        file_menu.AppendSeparator()
        item_prefs = file_menu.Append(
            wx.ID_PREFERENCES, _('Preferences\u2026') + '\tCtrl+,')
        self.Bind(wx.EVT_MENU, self._on_preferences, item_prefs)
        file_menu.AppendSeparator()
        item_exit = file_menu.Append(
            wx.ID_EXIT, _('Exit') + '\tCtrl+Q')
        self.Bind(wx.EVT_MENU, lambda _e: self.Close(), item_exit)
        mb.Append(file_menu, _('File'))

        help_menu = wx.Menu()
        item_sysinfo = help_menu.Append(
            wx.ID_ANY, _('System information\u2026'),
            _('Show information useful for bug reports.'))
        self.Bind(wx.EVT_MENU, self._on_system_information, item_sysinfo)
        item_about = help_menu.Append(
            wx.ID_ABOUT, _('About') + '\tF1')
        self.Bind(wx.EVT_MENU, self._on_about, item_about)
        mb.Append(help_menu, _('Help'))

        self.SetMenuBar(mb)

    def _build_accelerators(self):
        """Bind global keyboard shortcuts for accessibility.

        These are deliberately added via ``wx.AcceleratorTable`` rather
        than baked into translatable button labels, so existing
        translations are not invalidated.  They give screen-reader and
        keyboard-only users a way to drive the main actions without
        tabbing through the toolbar.
        """
        id_preview = wx.NewIdRef()
        id_clean = wx.NewIdRef()
        id_abort = wx.NewIdRef()
        id_focus_filter = wx.NewIdRef()
        id_focus_tree_search = wx.NewIdRef()

        def _safe(handler, btn):
            def _wrapped(_evt):
                if btn.IsEnabled():
                    handler(None)
            return _wrapped

        self.Bind(wx.EVT_MENU,
                  _safe(self._on_preview, self.btn_preview), id=id_preview)
        self.Bind(wx.EVT_MENU,
                  _safe(self._on_clean, self.btn_clean), id=id_clean)
        self.Bind(wx.EVT_MENU,
                  _safe(self._on_abort, self.btn_abort), id=id_abort)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self.filter_entry.SetFocus(),
                  id=id_focus_filter)
        self.Bind(wx.EVT_MENU,
                  lambda _e: self.tree_search.SetFocus(),
                  id=id_focus_tree_search)

        entries = [
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5, id_preview),
            wx.AcceleratorEntry(
                wx.ACCEL_CTRL, wx.WXK_RETURN, id_clean),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, id_abort),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('F'), id_focus_filter),
            wx.AcceleratorEntry(
                wx.ACCEL_CTRL, ord('L'), id_focus_tree_search),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

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
        """Build cleaner metadata and hand it to the model.

        The model owns the per-row check state (read/written via
        :class:`Options`) and renders rows lazily via the DataViewCtrl,
        so we no longer need to walk live tree items here.
        """
        hidden = getattr(self, '_hidden_cleaners', set())
        entries = []
        for cleaner_id in sorted(backends):
            if cleaner_id == '_gui':
                continue
            if cleaner_id in hidden:
                continue
            cleaner = backends[cleaner_id]
            name = cleaner.get_name() or cleaner_id
            opts = []
            for option_id, option_name in cleaner.get_options():
                warning = cleaner.get_warning(option_id)
                label = option_name
                if warning:
                    # Mark warnings with an exclamation mark; the full
                    # text appears on hover / status.
                    label = u'\u26a0  ' + option_name
                opts.append((option_id, label))
            entries.append((cleaner_id, name, opts))
        self._tree_model.set_data(entries)

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------
    def _collect_operations(self):
        """Return dict {cleaner_id: [option_id, ...]} for checked options.

        Reads :class:`Options` directly so check state is honoured even
        when the tree filter has hidden some rows.
        """
        operations = {}
        for cn in self._tree_model.cleaner_nodes():
            for o in self._tree_model.all_options(cn.cleaner_id):
                if options.get_tree(o.cleaner_id, o.option_id):
                    operations.setdefault(o.cleaner_id, []).append(
                        o.option_id)
        for k in list(operations):
            operations[k].sort()
        return operations

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def _on_toggle_expand(self, _evt):
        expand = self.chk_expand.IsChecked()
        for cn in self._tree_model.cleaner_nodes():
            item = self._tree_model.ObjectToItem(cn)
            if expand:
                self.tree.Expand(item)
            else:
                self.tree.Collapse(item)

    # ------------------------------------------------------------------
    # Tree filter / bulk-selection helpers
    # ------------------------------------------------------------------
    def _on_tree_filter_changed(self, _evt):
        self._tree_filter_text = (
            self.tree_search.GetValue().strip().lower())
        self._tree_model.set_filter(self._tree_filter_text)
        # When filtering, expand all visible cleaners so matching
        # options are immediately readable by a screen reader.
        if self._tree_filter_text:
            for cn in self._tree_model.cleaner_nodes():
                self.tree.Expand(self._tree_model.ObjectToItem(cn))

    def _set_all_checked(self, checked, predicate=None):
        """Check or uncheck every option that ``predicate`` accepts.

        ``predicate`` receives ``(cleaner_id, option_id, option_label)``.
        Iterates over the model's full dataset (not the live view) so
        options hidden by the current filter are still updated.
        """
        touched = set()
        for cn in self._tree_model.cleaner_nodes():
            for o in self._tree_model.all_options(cn.cleaner_id):
                if predicate is not None and not predicate(
                        o.cleaner_id, o.option_id, o.label):
                    continue
                cur = options.get_tree(o.cleaner_id, o.option_id)
                if cur != checked:
                    options.set_tree(o.cleaner_id, o.option_id, checked)
                    self._tree_model.ValueChanged(
                        self._tree_model.ObjectToItem(o), 0)
                    touched.add(o.cleaner_id)
        for cleaner_id in touched:
            cn = self._tree_model.cleaner_node(cleaner_id)
            if cn is not None:
                self._tree_model.ItemChanged(
                    self._tree_model.ObjectToItem(cn))

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
        obj = None
        if item and item.IsOk():
            obj = self._tree_model.ItemToObject(item)
        if isinstance(obj, _OptionNode):
            cid, oid = obj.cleaner_id, obj.option_id
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
        elif isinstance(obj, _CleanerNode):
            mi_check_cleaner = menu.Append(
                wx.ID_ANY, _('Check all options in this cleaner'))
            mi_uncheck_cleaner = menu.Append(
                wx.ID_ANY, _('Uncheck all options in this cleaner'))
            self.Bind(
                wx.EVT_MENU,
                lambda _e, c=obj.cleaner_id:
                    self._set_cleaner_children(c, True),
                mi_check_cleaner)
            self.Bind(
                wx.EVT_MENU,
                lambda _e, c=obj.cleaner_id:
                    self._set_cleaner_children(c, False),
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

    def _set_cleaner_children(self, cleaner_id, checked):
        """Check/uncheck every option of ``cleaner_id`` via the model."""
        for o in self._tree_model.all_options(cleaner_id):
            if options.get_tree(o.cleaner_id, o.option_id) != checked:
                options.set_tree(o.cleaner_id, o.option_id, checked)
                self._tree_model.ValueChanged(
                    self._tree_model.ObjectToItem(o), 0)
        cn = self._tree_model.cleaner_node(cleaner_id)
        if cn is not None:
            self._tree_model.ItemChanged(
                self._tree_model.ObjectToItem(cn))

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

    def _on_system_information(self, _evt):
        """Show the system information dialog."""
        from bleachbit.SystemInformation import (
            anonymize_system_information, get_system_information)
        txt = get_system_information(gui='wx')
        dlg = _SystemInformationDialog(self, txt, anonymize_system_information)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

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
        display = '%s  \u2014  %s' % (base, human)
        self._tree_model.set_display(op, opid, display)

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
        # "Delete now" only makes sense in preview mode: after a clean
        # run the files are already gone.  Registry rows have no path
        # and are filtered out by the ``paths`` list.
        in_preview = not getattr(self, '_current_really_delete', False)
        item_delete = menu.Append(
            wx.ID_ANY, _('Delete selected file(s)'))
        item_delete.Enable(bool(paths) and in_preview)
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
        self.Bind(wx.EVT_MENU,
                  lambda _e: self._shred_paths(paths), item_delete)
        for item, key in uncheck_items:
            self.Bind(wx.EVT_MENU,
                      lambda _e, k=key: self._uncheck_option(*k), item)
        self.results.PopupMenu(menu)
        menu.Destroy()

    def _uncheck_option(self, cleaner_id, option_id):
        """Uncheck (cleaner_id, option_id) via the model and persist."""
        o = self._tree_model.option_node(cleaner_id, option_id)
        if o is None:
            return
        # Persist + notify the model so the row repaints and the
        # cleaner's check/bold state recomputes.
        options.set_tree(cleaner_id, option_id, False)
        self._tree_model.ValueChanged(
            self._tree_model.ObjectToItem(o), 0)
        cn = self._tree_model.cleaner_node(cleaner_id)
        if cn is not None:
            self._tree_model.ItemChanged(
                self._tree_model.ObjectToItem(cn))
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
