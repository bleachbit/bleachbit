# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Preferences dialog for the experimental wxPython GUI.

Currently surfaces a few common boolean options on a General tab
plus parity with the GTK GUI for the interface language, the Keep
list (whitelist) and Custom (paths to delete) lists.
"""

import logging

import wx

from bleachbit.Language import (get_active_language_code,
                                get_supported_language_code_name_dict,
                                setup_translation)
from bleachbit.Language import get_text as _
from bleachbit.Options import options

logger = logging.getLogger(__name__)


# (option_key, label) pairs.  Order is preserved in the dialog.
_PREFS = (
    # Reuse the GTK front-end's msgids so the existing translations apply to
    # both interfaces.
    ('delete_confirmation', _('Confirm before delete')),
    ('shred',
     _('Overwrite contents of files to prevent recovery')),
    ('check_online_updates',
     _('Check periodically for software updates via the Internet')),
    ('debug', _('Show debug messages')),
)


# Page identifiers for the locations panel.
LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2

# Milliseconds before an infobar notice hides itself, as in the GTK GUI.
_INFOBAR_TIMEOUT_MS = 15000


class _LanguagesPanel(wx.Panel):
    """Panel that chooses the BleachBit interface language.

    Mirrors the "BleachBit interface language" section of the GTK
    Languages page: an *Auto-detect language* checkbox and, below it,
    a *Language:* dropdown that is enabled only while auto-detect is
    off.  Changes are saved to ``Options`` immediately, and
    ``on_change`` is called so the dialog can ask for a restart.
    """

    def __init__(self, parent, on_change):
        super().__init__(parent)
        self._on_change = on_change

        try:
            supported_langs = get_supported_language_code_name_dict()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error('Failed to get list of supported languages: %s', exc)
            supported_langs = {'en_US': 'English'}

        box_sizer = wx.StaticBoxSizer(
            wx.VERTICAL, self,
            # TRANSLATORS: Section title on the preferences languages page.
            _('BleachBit interface language'))
        box = box_sizer.GetStaticBox()

        is_auto_detect = bool(options.get('auto_detect_lang'))
        self._cb_auto = wx.CheckBox(box, label=_('Auto-detect language'))
        self._cb_auto.SetValue(is_auto_detect)
        self._cb_auto.SetToolTip(
            _('Automatically detect the system language'))
        self._cb_auto.Bind(wx.EVT_CHECKBOX, self._on_auto_detect)

        # The label is created right before the dropdown so screen
        # readers on Windows use it as the dropdown's name.
        self._lang_label = wx.StaticText(box, label=_('Language:'))
        self._lang_codes = []
        labels = []
        for lang_code, native in supported_langs.items():
            self._lang_codes.append(lang_code)
            labels.append('%s (%s)' % (native, lang_code)
                          if native else lang_code)
        self._choice = wx.Choice(box, choices=labels)
        self._select_active_language()
        self._choice.Bind(wx.EVT_CHOICE, self._on_language)

        lang_row = wx.BoxSizer(wx.HORIZONTAL)
        lang_row.Add(self._lang_label, 0,
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        lang_row.Add(self._choice, 0, wx.ALIGN_CENTER_VERTICAL)

        box_sizer.Add(self._cb_auto, 0, wx.ALL, 6)
        # Indent the dropdown under the checkbox, like the GTK GUI.
        box_sizer.Add(lang_row, 0, wx.LEFT, 20)
        box_sizer.AddSpacer(6)
        self._update_sensitivity()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(sizer)

    def _select_active_language(self):
        """Select the language in use now, or nothing if it is not listed."""
        current_lang_code = get_active_language_code()
        if current_lang_code in self._lang_codes:
            self._choice.SetSelection(
                self._lang_codes.index(current_lang_code))
        else:
            self._choice.SetSelection(wx.NOT_FOUND)

    def _update_sensitivity(self):
        enabled = not self._cb_auto.GetValue()
        self._lang_label.Enable(enabled)
        self._choice.Enable(enabled)

    def _on_auto_detect(self, _evt):
        is_auto_detect = self._cb_auto.GetValue()
        options.set('auto_detect_lang', is_auto_detect)
        if is_auto_detect:
            options.set('forced_language', '', section='bleachbit')
        # The active language may have changed (e.g. back to the system
        # language), so do not leave a stale choice in the dropdown.
        self._select_active_language()
        self._update_sensitivity()
        self._language_changed()

    def _on_language(self, _evt):
        idx = self._choice.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        lang_code = self._lang_codes[idx]
        if lang_code == options.get('forced_language'):
            return
        options.set('forced_language', lang_code, section='bleachbit')
        self._language_changed()

    def _language_changed(self):
        # Translate strings created from now on (e.g. reloaded cleaner
        # names) in the new language; the rest of the window needs a
        # restart, as in the GTK GUI.
        setup_translation()
        self._on_change()


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
            notice_text = _('These paths will not be deleted or modified.')
            notice_bg = wx.Colour(220, 240, 225)
            self._pathnames = list(options.get_whitelist_paths())
            self._save = options.set_whitelist_paths
        elif page_type == LOCATIONS_CUSTOM:
            # TRANSLATORS: Notice at the top of the custom (delete)
            # page in the preferences dialog.
            notice_text = _('These locations can be selected for deletion.')
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
    """wx preferences dialog: General options, Languages, Keep list and
    Custom list."""

    def __init__(self, parent):
        super().__init__(
            parent, title=_('Preferences'),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        # Set when the interface language changes, so the caller can
        # reload the cleaners in the new language.
        self.language_changed = False
        self._infobar_timer = None
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

        # Non-blocking notices, like the GTK InfoBar.
        self._infobar = wx.InfoBar(self)
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

        # Languages page (saved immediately), in the same place as in
        # the GTK GUI: right after General.
        notebook.AddPage(
            _LanguagesPanel(notebook, self._on_language_changed),
            # TRANSLATORS: Label for the "Languages" page in the
            # Preferences dialog.
            _('Languages'))

        # Keep list / Custom list pages (saved immediately).
        notebook.AddPage(
            _LocationsPanel(notebook, LOCATIONS_WHITELIST),
            _('Keep list'))
        notebook.AddPage(
            _LocationsPanel(notebook, LOCATIONS_CUSTOM),
            _('Custom'))

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._infobar, 0, wx.EXPAND)
        outer.Add(notebook, 1, wx.EXPAND | wx.ALL, 6)
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if btns:
            outer.Add(btns, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(outer)
        self.SetMinSize((620, 480))
        self.Fit()

    def _on_language_changed(self):
        self.language_changed = True
        # Translate now so the notice is shown in the chosen language.
        # TRANSLATORS: Notice shown in an infobar after changing a
        # preference that requires starting the application to be
        # effective.
        self.show_infobar(_('Restart BleachBit for full effect.'),
                          wx.ICON_INFORMATION)

    def show_infobar(self, message, flags=wx.ICON_INFORMATION):
        """Show a non-blocking notice that hides itself after a while."""
        self._infobar.ShowMessage(message, flags)
        if self._infobar_timer is None:
            self._infobar_timer = wx.CallLater(
                _INFOBAR_TIMEOUT_MS, self._infobar.Dismiss)
        else:
            self._infobar_timer.Restart(_INFOBAR_TIMEOUT_MS)

    def _on_destroy(self, evt):
        if evt.GetEventObject() is self and self._infobar_timer is not None:
            self._infobar_timer.Stop()
            self._infobar_timer = None
        evt.Skip()

    def commit(self):
        """Save the General-tab checkbox state into ``Options``.

        The keep list and custom list are persisted as the user
        edits them, so nothing more is needed here.
        """
        for key, cb in self._checkboxes.items():
            options.set(key, cb.GetValue())
