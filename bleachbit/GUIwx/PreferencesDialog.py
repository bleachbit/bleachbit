# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Preferences dialog for the experimental wxPython GUI.

Currently surfaces a few common boolean options on a General tab
plus parity with the GTK GUI for the Keep list (whitelist) and
Custom (paths to delete) lists.
"""

import wx

from bleachbit.Language import get_text as _
from bleachbit.Options import options


# (option_key, label) pairs.  Order is preserved in the dialog.
_PREFS = (
    ('delete_confirmation', _('Confirm before deleting files')),
    ('shred',
     _('Overwrite contents of files to prevent recovery (slow)')),
    ('check_online_updates', _('Check periodically for software updates')),
    ('debug', _('Log debug messages')),
)


# Page identifiers for the locations panel.
LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2


class _LocationsPanel(wx.Panel):
    """Panel that manages either the keep list or the custom-paths list.

    Changes are saved to ``Options`` immediately, matching the GTK GUI.
    """

    def __init__(self, parent, page_type):
        super().__init__(parent)
        self._page_type = page_type

        if page_type == LOCATIONS_WHITELIST:
            # TRANSLATORS: Notice at the top of the keep list (whitelist)
            # page in the preferences dialog.
            notice_text = _('Keep list: these paths will not be deleted '
                            'or modified during cleaning.')
            notice_bg = wx.Colour(220, 240, 225)
            self._pathnames = list(options.get_whitelist_paths())
            self._save = options.set_whitelist_paths
        elif page_type == LOCATIONS_CUSTOM:
            # TRANSLATORS: Notice at the top of the custom (delete)
            # page in the preferences dialog.
            notice_text = _('Custom list: these paths can be selected '
                            'for deletion from the main window.')
            notice_bg = wx.Colour(248, 226, 200)
            self._pathnames = list(options.get_custom_paths())
            self._save = options.set_custom_paths
        else:
            raise ValueError('Invalid page type: %r' % (page_type,))

        notice_panel = wx.Panel(self)
        notice_panel.SetBackgroundColour(notice_bg)
        np_sizer = wx.BoxSizer(wx.VERTICAL)
        notice = wx.StaticText(notice_panel, label=notice_text)
        notice.Wrap(520)
        np_sizer.Add(notice, 0, wx.ALL, 6)
        notice_panel.SetSizer(np_sizer)

        self._list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        # TRANSLATORS: Column header (file or folder).
        self._list.InsertColumn(0, _('Type'), width=80)
        # TRANSLATORS: Column header for a file or folder path.
        self._list.InsertColumn(1, _('Path'), width=420)
        self._reload_list()

        btn_add_file = wx.Button(self, label=_('Add file'))
        btn_add_folder = wx.Button(self, label=_('Add folder'))
        btn_remove = wx.Button(self, label=_('Remove'))
        btn_add_file.Bind(wx.EVT_BUTTON, self._on_add_file)
        btn_add_folder.Bind(wx.EVT_BUTTON, self._on_add_folder)
        btn_remove.Bind(wx.EVT_BUTTON, self._on_remove)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_add_file, 0, wx.RIGHT, 6)
        btn_sizer.Add(btn_add_folder, 0, wx.RIGHT, 6)
        btn_sizer.Add(btn_remove, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notice_panel, 0, wx.EXPAND | wx.ALL, 6)
        sizer.Add(self._list, 1, wx.EXPAND | wx.ALL, 6)
        sizer.Add(btn_sizer, 0, wx.ALL, 6)
        self.SetSizer(sizer)

    def _reload_list(self):
        self._list.DeleteAllItems()
        for path_type, path in self._pathnames:
            type_str = _('File') if path_type == 'file' else _('Folder')
            idx = self._list.InsertItem(self._list.GetItemCount(), type_str)
            self._list.SetItem(idx, 1, path)

    def _path_already_listed(self, pathname):
        """Warn and return True if pathname is in either list."""
        for _path_type, path in options.get_whitelist_paths():
            if path == pathname:
                wx.MessageBox(
                    _('This path already exists in the keep list.'),
                    _('Preferences'), wx.OK | wx.ICON_WARNING, self)
                return True
        for _path_type, path in options.get_custom_paths():
            if path == pathname:
                wx.MessageBox(
                    _('This path already exists in the custom list.'),
                    _('Preferences'), wx.OK | wx.ICON_WARNING, self)
                return True
        return False

    def _add(self, pathname, path_type):
        if not pathname:
            return
        if self._path_already_listed(pathname):
            return
        self._pathnames.append((path_type, pathname))
        self._save(self._pathnames)
        self._reload_list()

    def _on_add_file(self, _evt):
        with wx.FileDialog(
                self, _('Choose a file'),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._add(dlg.GetPath(), 'file')

    def _on_add_folder(self, _evt):
        with wx.DirDialog(
                self, _('Choose a folder'),
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._add(dlg.GetPath(), 'folder')

    def _on_remove(self, _evt):
        idx = self._list.GetFirstSelected()
        if idx < 0:
            return
        del self._pathnames[idx]
        self._save(self._pathnames)
        self._reload_list()


class PreferencesDialog(wx.Dialog):
    """wx preferences dialog: General options + Keep list + Custom list."""

    def __init__(self, parent):
        super().__init__(
            parent, title=_('Preferences'),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        notebook = wx.Notebook(self)

        # General page (checkboxes, saved on OK via commit()).
        general = wx.Panel(notebook)
        gen_sizer = wx.BoxSizer(wx.VERTICAL)
        self._checkboxes = {}
        for key, label in _PREFS:
            cb = wx.CheckBox(general, label=label)
            cb.SetValue(bool(options.get(key)))
            gen_sizer.Add(cb, 0, wx.ALL, 8)
            self._checkboxes[key] = cb
        general.SetSizer(gen_sizer)
        notebook.AddPage(general, _('General'))

        # Keep list / Custom list pages (saved immediately).
        notebook.AddPage(
            _LocationsPanel(notebook, LOCATIONS_WHITELIST),
            _('Keep list'))
        notebook.AddPage(
            _LocationsPanel(notebook, LOCATIONS_CUSTOM),
            _('Custom'))

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(notebook, 1, wx.EXPAND | wx.ALL, 6)
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if btns:
            outer.Add(btns, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(outer)
        self.SetMinSize((620, 480))
        self.Fit()

    def commit(self):
        """Save the General-tab checkbox state into ``Options``.

        The keep list and custom list are persisted as the user
        edits them, so nothing more is needed here.
        """
        for key, cb in self._checkboxes.items():
            options.set(key, cb.GetValue())
