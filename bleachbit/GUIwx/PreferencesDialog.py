# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Preferences dialog for the experimental wxPython GUI.

Mirrors the pages of the GTK preferences dialog
(``bleachbit.GuiPreferences``): General, Updates, Languages, Cookies,
Keep list, Custom and Drives.  The options are the same ``Options``
keys, so a choice made in one front-end carries over to the other.
Options that only affect GTK rendering (Windows 10 theme, Fontconfig
backend) have no wx counterpart and are not shown.
"""

import html
import json
import logging
import os
import re
import threading
import time

import wx
import wx.adv
import wx.dataview as dv
from wx.lib.wordwrap import wordwrap

import bleachbit
from bleachbit import (General, IS_POSIX, IS_WINDOWS, ProtectedPath,
                       online_update_notification_enabled)
from bleachbit.Constant import (EMPTY_SPACE_WARNING, REQUIRES_EXPERT_MODE,
                                URL_COOKIE_MGR)
from bleachbit.Cookie import (COOKIE_KEEP_LIST_FILENAME, list_unique_cookies,
                              load_keep_list)
from bleachbit.FileUtilities import open_for_overwrite
from bleachbit.General import sanitize_surrogates
from bleachbit.GUIwx.Accessibility import (NoticeBar, set_accessible_description,
                                           set_accessible_name, set_tooltip)
from bleachbit.GUIwx.Dialogs import open_url, warning_confirm_dialog
from bleachbit.Language import (find_supported_language_code,
                                get_active_language_code,
                                get_supported_language_code_name_dict,
                                setup_translation)
from bleachbit.Language import get_text as _, nget_text as _n, pget_text as _p
from bleachbit.Options import options
from bleachbit.PathUtils import normalize_path

logger = logging.getLogger(__name__)

# TRANSLATORS: Shown as a tooltip in the preferences window and as
# a description in a confirmation dialog.
EXPERT_MODE_DESCRIPTION = _(
    'Expert mode enables advanced features and relaxes guardrails. '
    'Use extra caution in expert mode.')

# TRANSLATORS: Used both as (1) a checkbox label in the preferences dialog
# to bypass some safety guardails for advanced users and (2) the title of
# dialog asking to confirm this choice.
EXPERT_MODE_MSG = _('Expert mode')

# TRANSLATORS: Notice shown in an infobar after changing a preference
# that requires starting the application to be effective.
RESTART_APP_MSG = _("Restart BleachBit for full effect.")

# Page identifiers for the locations panel.
LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2

COOKIE_DISCOVERY_WARN_THRESHOLD = 15.0  # seconds
COOKIE_DISCOVERY_DEBUG_THRESHOLD = 5.0  # seconds

# Left indent of a sub-option under the option it depends on.
_SUB_OPTION_INDENT = 18

# Width in pixels at which long labels wrap.
_WRAP_WIDTH = 560


def supports_dark_mode():
    """Return whether this wxPython can switch to dark mode."""
    return hasattr(wx.App, 'SetAppearance')


def apply_appearance(at_startup=False):
    """Apply the ``dark_mode`` option, the counterpart of the GTK
    ``gtk-application-prefer-dark-theme`` setting.

    On GTK and macOS, wx follows the system appearance by default and
    ``SetAppearance`` changes the existing windows too.  On Windows,
    dark mode is opt-in and applies to windows created afterwards, so
    it is applied only at startup and a change needs a restart.
    """
    app = wx.GetApp()
    if app is None or not supports_dark_mode():
        return
    dark = bool(options.get('dark_mode'))
    if wx.Platform == '__WXMSW__':
        if not (at_startup and dark):
            return
        appearance = wx.App.Appearance.Dark
    else:
        appearance = (wx.App.Appearance.Dark if dark
                      else wx.App.Appearance.System)
    result = app.SetAppearance(appearance)
    if result != wx.App.AppearanceResult.Ok:
        logger.debug('Could not change the appearance: %s', result)


def _is_dark():
    """Return whether the application uses a dark appearance."""
    try:
        return wx.SystemSettings.GetAppearance().IsDark()
    except AttributeError:
        return False


def _section(parent, sizer, title):
    """Add a titled group and return ``(box, box_sizer)``.

    Controls are created as children of the ``wx.StaticBox``, so screen
    readers announce the group name when the focus moves into it.
    """
    box_sizer = wx.StaticBoxSizer(wx.VERTICAL, parent, title)
    sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 6)
    return box_sizer.GetStaticBox(), box_sizer


def _wrap(label, width=_WRAP_WIDTH):
    """Wrap a label's text to ``width`` pixels.

    Unlike ``wx.StaticText.Wrap``, which breaks lines only at spaces,
    this also breaks text without spaces, such as Chinese or Japanese.
    """
    label.SetLabelText(wordwrap(label.GetLabelText(), width,
                                wx.ClientDC(label), breakLongWords=True))
    return label


def _notice(parent, text, light_bg, dark_bg):
    """Return a coloured panel holding a wrapped notice."""
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(
        wx.Colour(*(dark_bg if _is_dark() else light_bg)))
    label = _wrap(wx.StaticText(panel, label=text))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(label, 0, wx.ALL, 6)
    panel.SetSizer(sizer)
    return panel


def _wrapped_text(parent, text):
    return _wrap(wx.StaticText(parent, label=text))


def _split_link_markup(markup):
    """Split ``"text <a href='...'>link</a> rest"`` into its parts.

    Returns ``(before, link_text, after)``; ``link_text`` is ``None``
    when the (translated) text has no link.
    """
    match = re.match(r'(?s)^(.*?)<a\s[^>]*>(.*?)</a>(.*)$', markup)
    if not match:
        return html.unescape(re.sub(r'<[^>]+>', '', markup)), None, ''
    return tuple(html.unescape(part) for part in match.groups())


class _LanguagesPanel(wx.Panel):
    """Panel for the GTK *Languages* page.

    The *BleachBit interface language* section has an *Auto-detect
    language* checkbox and, below it, a *Language:* dropdown that is
    enabled only while auto-detect is off.  On POSIX systems, a list
    of *Language files to keep when cleaning applications* follows.
    Changes are saved to ``Options`` immediately, and ``on_change`` is
    called after an interface language change so the dialog can ask
    for a restart.
    """

    def __init__(self, parent, on_change):
        super().__init__(parent)
        self._on_change = on_change

        try:
            supported_langs = get_supported_language_code_name_dict()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error('Failed to get list of supported languages: %s', exc)
            supported_langs = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        box, box_sizer = _section(
            self, sizer,
            # TRANSLATORS: Section title on the preferences languages page.
            _('BleachBit interface language'))

        is_auto_detect = bool(options.get('auto_detect_lang'))
        self._cb_auto = wx.CheckBox(box, label=_('Auto-detect language'))
        self._cb_auto.SetValue(is_auto_detect)
        set_tooltip(
            self._cb_auto,
            # TRANSLATORS: Tooltip explaining the auto-detect language option.
            _('Automatically detect the system language'))
        self._cb_auto.Bind(wx.EVT_CHECKBOX, self._on_auto_detect)

        # The label is created right before the dropdown so screen
        # readers on Windows use it as the dropdown's name.
        # TRANSLATORS: Label for the language selection dropdown.
        self._lang_label = wx.StaticText(box, label=_('Language:'))
        self._lang_codes = []
        labels = []
        lang_items = (supported_langs.items() if supported_langs is not None
                      else (('en_US', 'English'),))
        for lang_code, native in lang_items:
            self._lang_codes.append(lang_code)
            labels.append('%s (%s)' % (native, lang_code)
                          if native else lang_code)
        self._choice = wx.Choice(box, choices=labels)
        self._select_supported_language(get_active_language_code())
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

        self._keep_list = None
        # Windows does not have locale cleaner.
        if IS_POSIX:
            if supported_langs is None:
                # There is no English fallback here, so let the failure
                # propagate, as in the GTK GUI.
                supported_langs = get_supported_language_code_name_dict()
            self._build_keep_list(sizer, supported_langs)

        self.SetSizer(sizer)

    def _build_keep_list(self, sizer, supported_langs):
        # TRANSLATORS: Section title on the preferences languages page.
        title = _('Language files to keep when cleaning applications')
        box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, title)
        sizer.Add(box_sizer, 1, wx.EXPAND | wx.ALL, 6)
        box = box_sizer.GetStaticBox()
        # A DataViewListCtrl is the native, accessible GtkTreeView on
        # Linux, where this list is shown.
        self._keep_list = dv.DataViewListCtrl(box, size=(300, 200))
        set_accessible_name(self._keep_list, title)
        # TRANSLATORS: Column header in the languages treeview.
        # This column controls whether to keep the language.
        self._keep_list.AppendToggleColumn(
            _('Keep'), mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        # TRANSLATORS: Column header in the languages treeview showing the
        # language code (e.g., 'en_US').
        self._keep_list.AppendTextColumn(
            _('Code'), flags=dv.DATAVIEW_COL_RESIZABLE | dv.DATAVIEW_COL_SORTABLE)
        # TRANSLATORS: Column header in the languages treeview showing the
        # native name of the language.
        self._keep_list.AppendTextColumn(
            _('Name'), flags=dv.DATAVIEW_COL_RESIZABLE | dv.DATAVIEW_COL_SORTABLE)
        for lang, native in supported_langs.items():
            self._keep_list.AppendItem(
                [bool(options.get_language(lang)), lang, native or ''])
        self._keep_list.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED,
                             self._on_keep_language)
        box_sizer.Add(self._keep_list, 1, wx.EXPAND | wx.ALL, 6)

    def _on_keep_language(self, evt):
        """Save the *Keep* checkbox of a language row."""
        if evt.GetColumn() != 0:
            return
        row = self._keep_list.ItemToRow(evt.GetItem())
        if row == wx.NOT_FOUND:
            return
        langid = self._keep_list.GetTextValue(row, 1)
        options.set_language(langid, self._keep_list.GetToggleValue(row, 0))

    def _select_supported_language(self, lang_code):
        """Select the best matching language in the dropdown.

        Returns the selected language code, or ``None`` if there is no
        matching entry.  Like the GTK GUI, falls back to English.
        """
        matched = find_supported_language_code(lang_code, self._lang_codes)
        if matched is None:
            matched = find_supported_language_code('en', self._lang_codes)
        if matched is None:
            self._choice.SetSelection(wx.NOT_FOUND)
            return None
        self._choice.SetSelection(self._lang_codes.index(matched))
        return matched

    def _update_sensitivity(self):
        enabled = not self._cb_auto.GetValue()
        self._lang_label.Enable(enabled)
        self._choice.Enable(enabled)

    def _on_auto_detect(self, _evt):
        is_auto_detect = self._cb_auto.GetValue()
        options.set('auto_detect_lang', is_auto_detect)
        self._update_sensitivity()
        # Clear first so detection below sees the system locale rather
        # than a stale forced value.
        options.set('forced_language', '', section='bleachbit')
        # Show the detected language, so the dropdown never shows a
        # forced language that no longer applies.
        matched = self._select_supported_language(get_active_language_code())
        if matched and not is_auto_detect:
            # Keep the detected language now that it is no longer
            # automatically detected, like the GTK GUI.
            options.set('forced_language', matched, section='bleachbit')
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


class _CookiesPanel(wx.Panel):
    """Panel for the GTK *Cookies* page (``GuiCookie.CookieManagerPane``).

    Lists the cookie hosts found in the browsers plus those already in
    the keep list.  A checked host is kept when cleaning cookies.
    Changes are saved to the same JSON keep list as the GTK GUI as
    soon as they are made.

    The hosts are found on a background thread the first time the page
    is shown (see :meth:`ensure_loaded`), because opening every browser
    cookie database can be slow.  The list is a ``wx.ListCtrl`` with
    native checkboxes, which screen readers on Windows read as
    checkable items.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._hosts = []      # [[checked, host], ...] sorted by host
        self._visible = []    # indices into _hosts, in display order
        self._sort_descending = False
        self._show_selected_only = False
        self._updating = False
        self._is_loading = False
        self._loaded = False
        self.keep_list_path = os.path.join(
            bleachbit.options_dir, COOKIE_KEEP_LIST_FILENAME)
        self.saved_domains = set()

        sizer = wx.BoxSizer(wx.VERTICAL)

        instructions = wx.StaticText(
            self,
            # TRANSLATORS: Instruction label in the manage cookies dialog.
            label=_("Select the cookies to keep when cleaning cookies "
                    "across browsers."))
        font = instructions.GetFont()
        font.MakeBold()
        instructions.SetFont(font)
        _wrap(instructions)
        sizer.Add(instructions, 0, wx.ALL, 6)

        # TRANSLATORS: This is a notice in the cookie manager about supported
        # cookie types. The hyperlink points to the documentation website.
        # Cookies refer to standard HTTP cookies.
        # Site data includes LocalStorage, IndexedDB, and other website storage.
        before, link_text, after = _split_link_markup(
            _("Only cookies are preserved. Site data is always deleted. "
              "<a href='{url}'>Learn more</a>"))
        notice_row = wx.BoxSizer(wx.HORIZONTAL)
        notice_row.Add(wx.StaticText(self, label=before.strip()), 0,
                       wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        if link_text:
            # A native link: screen readers read it as a link.
            link = wx.adv.HyperlinkCtrl(
                self, label=link_text, url=URL_COOKIE_MGR)
            link.Bind(wx.adv.EVT_HYPERLINK, self._on_link)
            notice_row.Add(link, 0, wx.ALIGN_CENTER_VERTICAL)
        if after.strip():
            notice_row.Add(wx.StaticText(self, label=after.strip()), 0,
                           wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        sizer.Add(notice_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        search_row = wx.BoxSizer(wx.HORIZONTAL)
        # TRANSLATORS: Label for the search entry in the manage cookies dialog.
        search_label = _("Search:")
        search_row.Add(wx.StaticText(self, label=search_label), 0,
                       wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self._search = wx.TextCtrl(self)
        set_accessible_name(self._search, search_label)
        # TRANSLATORS: Placeholder text in the search entry in the manage cookies dialog.
        # 'Filter' is a verb meaning to narrow down the list by typing.
        self._search.SetHint(_("Filter cookies..."))
        self._search.Bind(wx.EVT_TEXT, self._on_search_changed)
        search_row.Add(self._search, 1, wx.ALIGN_CENTER_VERTICAL)
        # GTK uses a toggle button; a checkbox is the wx control that
        # screen readers report as on/off with the expected role.
        # TRANSLATORS: Toggle button label in the manage cookies dialog.
        # "Show" is a command (imperative).
        # 'Selected' refers to selected cookies (the noun "cookies" is implied).
        self._selected_toggle = wx.CheckBox(self, label=_("Show Selected"))
        set_tooltip(
            self._selected_toggle,
            # TRANSLATORS: Tooltip for the "Show Selected" toggle button.
            _("Only show cookies that are currently selected"))
        self._selected_toggle.Bind(wx.EVT_CHECKBOX, self._on_selected_toggle)
        search_row.Add(self._selected_toggle, 0,
                       wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(search_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)

        # TRANSLATORS: Status message shown while the cookie list is loading
        # in the cookie manager dialog window.
        # "Loading" is a present participle (ongoing action).
        # To indicate an ongoing operation, include the ellipsis as literal
        # Unicode (…) or as Unicode escape (\u2026).
        self._loading_label = wx.StaticText(
            self, label=_("Loading cookies\u2026"))
        self._loading_label.Hide()
        sizer.Add(self._loading_label, 0, wx.ALIGN_CENTER | wx.TOP, 6)

        self._list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(-1, 200))
        self._list.EnableCheckBoxes(True)
        # TRANSLATORS: Column header in the manage cookies dialog.
        # 'Host' is a noun meaning the website hostname (domain name) of the cookie.
        self._list.InsertColumn(0, _("Host"), width=480)
        # TRANSLATORS: Sidebar label for the page managing browser cookies in
        # the Preferences dialog.
        set_accessible_name(self._list, _("Cookies"))
        set_accessible_description(
            self._list, lambda: self._stat_label.GetLabel())
        self._list.Bind(wx.EVT_LIST_ITEM_CHECKED,
                        lambda evt: self._on_item_toggled(evt, True))
        self._list.Bind(wx.EVT_LIST_ITEM_UNCHECKED,
                        lambda evt: self._on_item_toggled(evt, False))
        self._list.Bind(wx.EVT_LIST_COL_CLICK, self._on_col_click)
        self._list.Bind(wx.EVT_SIZE, self._on_list_size)
        sizer.Add(self._list, 1, wx.EXPAND | wx.ALL, 6)

        bottom = wx.BoxSizer(wx.HORIZONTAL)
        self._stat_label = wx.StaticText(self, label='')
        bottom.Add(self._stat_label, 1, wx.ALIGN_CENTER_VERTICAL)
        # TRANSLATORS: Button label in the manage cookies dialog.
        self._select_all_btn = wx.Button(self, label=_("Select All"))
        self._select_all_btn.Bind(
            wx.EVT_BUTTON, lambda _evt: self._set_visible_selection(True))
        bottom.Add(self._select_all_btn, 0, wx.LEFT, 6)
        # TRANSLATORS: Button label in the manage cookies dialog.
        self._deselect_all_btn = wx.Button(self, label=_("Deselect All"))
        self._deselect_all_btn.Bind(
            wx.EVT_BUTTON, lambda _evt: self._set_visible_selection(False))
        bottom.Add(self._deselect_all_btn, 0, wx.LEFT, 6)
        sizer.Add(bottom, 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(sizer)
        self._update_stat_label()

    # -- loading -----------------------------------------------------
    def ensure_loaded(self):
        """Start finding cookie hosts, the first time the page is shown."""
        if self._loaded or self._is_loading:
            return
        try:
            self.saved_domains = load_keep_list()
        except (OSError, ValueError) as exc:
            # Do not offer to save a list we could not read: saving
            # would replace the user's keep list.
            logger.error('Failed to load cookie keep list %s: %s',
                         self.keep_list_path, exc)
            self._set_controls_enabled(False)
            return
        self._is_loading = True
        self._set_controls_enabled(False)
        self._loading_label.Show()
        self.Layout()
        threading.Thread(target=self._discover, daemon=True,
                         name='BleachBitCookieDiscovery').start()

    def _set_controls_enabled(self, enabled):
        for ctrl in (self._list, self._select_all_btn,
                     self._deselect_all_btn):
            ctrl.Enable(enabled)

    def _discover(self):
        start = time.monotonic()
        discovered = []
        try:
            discovered = list_unique_cookies()
        except (OSError, RuntimeError, ValueError) as exc:  # pragma: no cover
            logger.error('Failed to enumerate cookies: %s', exc)
        duration = time.monotonic() - start
        if duration >= COOKIE_DISCOVERY_WARN_THRESHOLD:
            logger.warning('Enumerating cookie hosts took %.2fs', duration)
        elif duration >= COOKIE_DISCOVERY_DEBUG_THRESHOLD:
            logger.debug('Enumerating cookie hosts took %.2fs', duration)
        if wx.GetApp() is not None:
            wx.CallAfter(self._finish_populate, discovered)

    def _finish_populate(self, discovered):
        """Fill the list on the main thread once discovery finishes."""
        if not self:
            # The dialog was closed while cookies were being found.
            return
        self._is_loading = False
        self._loaded = True
        self._loading_label.Hide()
        self._set_controls_enabled(True)
        all_hosts = {h.strip() for h in discovered if h}
        all_hosts.update(self.saved_domains)
        self._hosts = [[host in self.saved_domains, host]
                       for host in sorted(all_hosts, key=str.lower)]
        self.Layout()
        self._refresh_list()

    # -- list --------------------------------------------------------
    def _refresh_list(self):
        """Rebuild the visible rows from the search and *Show Selected*."""
        needle = self._search.GetValue().lower()
        visible = [
            index for index, (checked, host) in enumerate(self._hosts)
            if (not needle or needle in host.lower())
            and (not self._show_selected_only or checked)]
        if self._sort_descending:
            visible.reverse()
        self._visible = visible
        self._updating = True
        self._list.Freeze()
        try:
            self._list.DeleteAllItems()
            for row, index in enumerate(visible):
                checked, host = self._hosts[index]
                self._list.InsertItem(row, host)
                if checked:
                    self._list.CheckItem(row, True)
        finally:
            self._list.Thaw()
            self._updating = False
        self._update_stat_label()

    def _update_stat_label(self):
        """Show how many hosts are kept, like the GTK stat label."""
        total = len(self._hosts)
        selected = sum(1 for checked, _host in self._hosts if checked)
        visible = len(self._visible)
        if visible < total:
            # TRANSLATORS: %(selected)d is the count of selected cookies,
            # %(total)d is the total count, %(visible)d is the visible count
            text = _n("%(selected)d of %(total)d cookie kept (%(visible)d visible)",
                      "%(selected)d of %(total)d cookies kept (%(visible)d visible)",
                      selected) % {'selected': selected, 'total': total,
                                   'visible': visible}
        else:
            # TRANSLATORS: %(selected)d is the count of selected cookies,
            # %(total)d is the total count
            text = _n("%(selected)d of %(total)d cookie kept",
                      "%(selected)d of %(total)d cookies kept",
                      selected) % {'selected': selected, 'total': total}
        self._stat_label.SetLabel(text)

    def _on_item_toggled(self, evt, checked):
        if self._updating:
            return
        row = evt.GetIndex()
        if not 0 <= row < len(self._visible):
            return
        self._hosts[self._visible[row]][0] = checked
        self.save_changes()
        if self._show_selected_only and not checked:
            # The row no longer matches the filter.  Rebuild after the
            # event, not while the list control is handling it.
            wx.CallAfter(self._refresh_if_alive)
        else:
            self._update_stat_label()

    def _refresh_if_alive(self):
        if self:
            self._refresh_list()

    def _set_visible_selection(self, is_selected):
        """Check or uncheck the hosts that match the current filter."""
        if self._is_loading or not self._loaded:
            return
        for index in self._visible:
            self._hosts[index][0] = is_selected
        self.save_changes()
        self._refresh_list()

    def _on_search_changed(self, _evt):
        self._refresh_list()

    def _on_selected_toggle(self, _evt):
        self._show_selected_only = self._selected_toggle.GetValue()
        self._refresh_list()

    def _on_col_click(self, _evt):
        # The list starts in ascending order, like the GTK sort column.
        self._sort_descending = not self._sort_descending
        if hasattr(self._list, 'ShowSortIndicator'):
            self._list.ShowSortIndicator(0, not self._sort_descending)
        self._refresh_list()

    def _on_list_size(self, evt):
        # Let the single Host column fill the list, like the GTK column.
        width = self._list.GetClientSize().width
        if width > 0:
            self._list.SetColumnWidth(0, width)
        evt.Skip()

    def _on_link(self, evt):
        open_url(evt.GetURL(), self, prompt=True)

    # -- saving ------------------------------------------------------
    def save_changes(self):
        """Save the checked hosts to the JSON keep list."""
        keep_list = sorted(host for checked, host in self._hosts if checked)
        try:
            mkfile = not os.path.exists(self.keep_list_path)
            with open_for_overwrite(self.keep_list_path,
                                    encoding='utf-8') as f:
                json.dump(keep_list, f, indent=2)
            if mkfile and General.sudo_mode():
                General.chownself(self.keep_list_path)
            self.saved_domains = set(keep_list)
            return True
        except OSError as exc:
            logger.error('Failed to save cookie keep list %s: %s',
                         self.keep_list_path, exc)
            return False


class _LocationsPanel(wx.Panel):
    """Panel that manages either the keep list or the custom-paths list.

    Changes are saved to ``Options`` immediately, matching the GTK GUI.
    Notices go to ``owner.show_infobar`` (the preferences dialog).
    """

    def __init__(self, parent, page_type, owner=None):
        super().__init__(parent)
        self._page_type = page_type
        self._owner = owner if owner is not None else wx.GetTopLevelParent(
            parent)

        if page_type == LOCATIONS_WHITELIST:
            # TRANSLATORS: Notice label at the top of the keeplist (whitelist)
            # page in the preferences dialog.
            # "Paths" is used generically to refer to both files and folders.
            notice_text = _('These paths will not be deleted or modified.')
            colors = ((220, 240, 225), (32, 64, 44))
            self._pathnames = list(options.get_whitelist_paths())
            self._save = options.set_whitelist_paths
            # TRANSLATORS: Sidebar label for the "keep list" (whitelist) page of
            # the preferences dialog. This page lists paths that will be preserved
            # (not deleted) during cleaning.
            list_name = _('Keep list')
        elif page_type == LOCATIONS_CUSTOM:
            # TRANSLATORS: Notice label at the top of the custom (delete)
            # page in the preferences dialog.
            notice_text = _('These locations can be selected for deletion.')
            colors = ((248, 226, 200), (72, 48, 20))
            self._pathnames = list(options.get_custom_paths())
            self._save = options.set_custom_paths
            # TRANSLATORS: Sidebar label for the page where users add their own paths to clean.
            # Short label meaning "Custom locations".
            list_name = _('Custom')
        else:
            raise ValueError('Invalid page type: %r' % (page_type,))

        notice_panel = _notice(self, notice_text, *colors)

        self._list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        set_accessible_name(self._list, list_name)
        # Read the notice with the list, since it is not focusable.
        set_accessible_description(self._list, notice_text)
        # TRANSLATORS: Column header in the preferences dialog showing whether
        # the item is a file or folder.
        self._list.InsertColumn(0, _('Type'), width=80)
        # TRANSLATORS: In the tree view "Path" is used generically to refer to a
        # file, a folder, or a pattern describing either
        self._list.InsertColumn(1, _('Path'), width=420)
        self._reload_list()

        btn_add_file = wx.Button(
            self,
            # TRANSLATORS: Button label in the preferences for adding a file.
            label=_p('button', 'Add file'))
        btn_add_folder = wx.Button(
            self,
            # TRANSLATORS: Button label in the preferences for adding a folder.
            label=_p('button', 'Add folder'))
        btn_remove = wx.Button(self, label=_p('button', 'Remove'))
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

    def _notify(self, message, flags=wx.ICON_INFORMATION):
        show = getattr(self._owner, 'show_infobar', None)
        if show is not None:
            show(message, flags)
        else:
            wx.MessageBox(message, _('Preferences'), wx.OK | flags, self)

    def _is_expert_mode(self):
        is_expert = getattr(self._owner, 'is_expert_mode', None)
        if is_expert is not None:
            return is_expert()
        return bool(options.get('expert_mode'))

    def _reload_list(self):
        self._list.DeleteAllItems()
        for path_type, path in self._pathnames:
            # TRANSLATORS: Noun used as a column header in the preferences dialog.
            type_str = _('File') if path_type == 'file' else _('Folder')
            idx = self._list.InsertItem(self._list.GetItemCount(), type_str)
            self._list.SetItem(idx, 1, sanitize_surrogates(path))

    def _path_already_listed(self, pathname):
        """Show an error and return True if pathname is in either list."""
        for _path_type, path in options.get_whitelist_paths():
            if path == pathname:
                # TRANSLATORS: Error message shown in the infobar.
                self._notify(_('This path already exists in the keep list.'),
                             wx.ICON_ERROR)
                return True
        for _path_type, path in options.get_custom_paths():
            if path == pathname:
                # TRANSLATORS: Error message shown in the infobar.
                self._notify(_('This path already exists in the custom list.'),
                             wx.ICON_ERROR)
                return True
        return False

    def _check_protected_path(self, pathname):
        """Check if the path is protected and warn the user if so.

        Returns True if it is safe to proceed, False if not.  Mirrors
        ``GuiPreferences.PreferencesDialog._check_protected_path``.
        """
        match_info = ProtectedPath.check_protected_path(pathname)
        if match_info is None:
            return True
        if not self._is_expert_mode():
            self._notify(
                # TRANSLATORS: Error message shown in the infobar.
                _('This path is protected. To bypass protection, enable expert mode.'),
                wx.ICON_WARNING)
            return False
        normalized = normalize_path(
            pathname, case_sensitive=match_info['case_sensitive'])
        warning_key = 'protected_path:' + normalized
        if options.get_warning_preference(warning_key):
            return True
        with wx.BusyCursor():
            impact = ProtectedPath.calculate_impact(pathname)
        warning_msg = ProtectedPath.get_warning_message(pathname, impact)
        confirmed, remember = warning_confirm_dialog(
            self,
            # TRANSLATORS: Title of warning dialog shown when adding a protected path.
            _('Protected Path'),
            warning_msg)
        if confirmed and remember:
            options.remember_warning_preference(warning_key)
        return confirmed

    def _add(self, pathname, path_type):
        if not pathname:
            return
        if self._path_already_listed(pathname):
            return
        # Check for protected paths when adding to the custom (delete) list.
        if (self._page_type == LOCATIONS_CUSTOM
                and not self._check_protected_path(pathname)):
            return
        self._pathnames.append((path_type, pathname))
        self._save(self._pathnames)
        self._reload_list()
        # TRANSLATORS: %s is a file or folder path that was just added
        self._notify(_('Added: %s') % sanitize_surrogates(pathname))

    def _on_add_file(self, _evt):
        with wx.FileDialog(
                self,
                # TRANSLATORS: Title of a file chooser dialog.
                _('Choose a file'),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._add(dlg.GetPath(), 'file')

    def _on_add_folder(self, _evt):
        with wx.DirDialog(
                self,
                # TRANSLATORS: Title of a folder chooser dialog.
                _('Choose a folder'),
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._add(dlg.GetPath(), 'folder')

    def _on_remove(self, _evt):
        idx = self._list.GetFirstSelected()
        if idx < 0:
            return
        _path_type, path = self._pathnames.pop(idx)
        self._save(self._pathnames)
        self._reload_list()
        # TRANSLATORS: %s is a file or folder path that was just removed
        self._notify(_('Removed: %s') % sanitize_surrogates(path))


class _DrivesPanel(wx.Panel):
    """Panel for the GTK *Drives* page.

    Lists one writable folder per drive whose empty space is wiped by
    the *Free disk space* cleaner option (``shred_drives``).  Changes
    are saved immediately, as in the GTK GUI.
    """

    def __init__(self, parent):
        super().__init__(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # TRANSLATORS: 'empty' means 'unallocated'.
        # The user should decide which drives to wipe. Then, for each
        # chosen drive, the user should specify one folder per drive.
        # For example, to wipe C:\, the user may choose %TEMP% which
        # is a folder anywhere on C:.
        instruction = _("Choose a writable folder for each drive for "
                        "which to wipe empty space.")
        sizer.Add(_wrapped_text(self, instruction), 0, wx.ALL, 6)
        sizer.Add(_wrapped_text(self, EMPTY_SPACE_WARNING), 0,
                  wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self._pathnames = sorted(options.get_list('shred_drives') or [])
        self._list = wx.ListBox(
            self, choices=self._pathnames, style=wx.LB_SINGLE)
        # TRANSLATORS: Sidebar label for the drives page of the preferences dialog.
        set_accessible_name(self._list, _('Drives'))
        # Read the instruction with the list, since it is not focusable.
        set_accessible_description(self._list, instruction)
        sizer.Add(self._list, 1, wx.EXPAND | wx.ALL, 6)

        # TRANSLATORS: In the preferences dialog, this button adds a path to
        # the list of paths
        btn_add = wx.Button(self, label=_p('button', 'Add'))
        # TRANSLATORS: In the preferences dialog, this button removes a path
        # from the list of paths
        btn_remove = wx.Button(self, label=_p('button', 'Remove'))
        btn_add.Bind(wx.EVT_BUTTON, self._on_add)
        btn_remove.Bind(wx.EVT_BUTTON, self._on_remove)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_add, 0, wx.RIGHT, 6)
        btn_sizer.Add(btn_remove, 0)
        sizer.Add(btn_sizer, 0, wx.ALL, 6)
        self.SetSizer(sizer)

    def add_drive(self, pathname):
        """Add a folder and save the list."""
        if not pathname:
            return
        self._pathnames.append(pathname)
        self._list.Append(pathname)
        options.set_list('shred_drives', self._pathnames)

    def _on_add(self, _evt):
        with wx.DirDialog(
                self,
                # TRANSLATORS: Title of a folder chooser dialog.
                _('Choose a folder'),
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.add_drive(dlg.GetPath())

    def _on_remove(self, _evt):
        idx = self._list.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        del self._pathnames[idx]
        self._list.Delete(idx)
        options.set_list('shred_drives', self._pathnames)


class PreferencesDialog(wx.Dialog):
    """wx preferences dialog, with the pages of the GTK dialog.

    Checkboxes on the General and Updates pages are saved by
    :meth:`commit` when the dialog is closed with OK.  The other pages
    save their changes immediately, as in the GTK GUI.
    """

    def __init__(self, parent, page=None):
        super().__init__(
            parent,
            # TRANSLATORS: Title for the preferences dialog
            title=_('Preferences'),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        # Set when the interface language changes, so the caller can
        # reload the cleaners in the new language.
        self.language_changed = False
        # Set when the cleaner tree must be reloaded (the counterpart
        # of the GTK ``refresh_operations`` flag).
        self.refresh_operations = False
        self._checkboxes = {}
        self._requires = {}
        self._btn_reset_warnings = None
        self._page_ids = []

        # Non-blocking notices, like the GTK InfoBar.
        self._infobar = NoticeBar(self)
        self._notebook = wx.Notebook(self)

        pages = (
            # TRANSLATORS: Sidebar label for the general settings page of the preferences dialog.
            ('general', self._build_general_page, _('General'), True),
            # TRANSLATORS: Sidebar label for the software updates page of the preferences dialog.
            ('updates', self._build_updates_page, _('Updates'),
             online_update_notification_enabled),
            ('languages',
             lambda nb: _LanguagesPanel(nb, self._on_language_changed),
             # TRANSLATORS: Sidebar label for the "Languages" page in the Preferences dialog.
             _('Languages'), True),
            # TRANSLATORS: Sidebar label for the page managing browser cookies in
            # the Preferences dialog.
            ('cookies', _CookiesPanel, _('Cookies'), True),
            ('keep-list',
             lambda nb: _LocationsPanel(nb, LOCATIONS_WHITELIST, self),
             _('Keep list'), True),
            ('custom',
             lambda nb: _LocationsPanel(nb, LOCATIONS_CUSTOM, self),
             _('Custom'), True),
            ('drives', _DrivesPanel, _('Drives'), True),
        )
        for page_id, build, title, condition in pages:
            if condition:
                self._notebook.AddPage(build(self._notebook), title)
                self._page_ids.append(page_id)
        self._update_sensitivity()
        self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,
                            self._on_page_changed)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._infobar, 0, wx.EXPAND)
        outer.Add(self._notebook, 1, wx.EXPAND | wx.ALL, 6)
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if btns:
            outer.Add(btns, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(outer)
        self.SetMinSize((640, 520))
        self.Fit()
        self.select_page(page)

    # -- pages -------------------------------------------------------
    def _add_checkbox(self, parent, sizer, label, key, tooltip=None,
                      requires=None, indent=0):
        """Add a checkbox for a boolean option, saved by :meth:`commit`.

        ``requires`` names the option whose checkbox must be checked
        for this one to be enabled, like ``requires_option`` in the
        GTK GUI.  An option overridden on the command line is disabled.
        """
        cb = wx.CheckBox(parent, label=label)
        cb.SetValue(bool(options.get(key)))
        if tooltip:
            set_tooltip(cb, tooltip)
        cb.Bind(wx.EVT_CHECKBOX, lambda _evt, k=key: self._on_checkbox(k))
        if indent:
            # Indent a sub-option under the option it depends on.
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.AddSpacer(indent)
            row.Add(cb)
            sizer.Add(row, 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        else:
            sizer.Add(cb, 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        self._checkboxes[key] = cb
        self._requires[key] = requires
        return cb

    def _build_general_page(self, notebook):
        page = wx.Panel(notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # TRANSLATORS: Section title (noun) on the Preferences - General page
        # for options related to cleaning stored data.
        box, box_sizer = _section(page, sizer, _('Cleaning'))
        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences dialog.
            _('Overwrite contents of files to prevent recovery'), 'shred',
            # TRANSLATORS: Tooltip for the shred checkbox in the preferences dialog.
            tooltip=_('Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower.'))
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences dialog.
            _('Exit after cleaning'), 'exit_done')
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences dialog.
            # Ask for confirmation before deleting items.
            _('Confirm before delete'), 'delete_confirmation',
            tooltip=REQUIRES_EXPERT_MODE, requires='expert_mode')
        self._btn_reset_warnings = wx.Button(
            box,
            # TRANSLATORS: Button label in the preferences. 'Reset' is a verb.
            label=_('Reset warning confirmations'))
        set_tooltip(self._btn_reset_warnings, REQUIRES_EXPERT_MODE)
        self._btn_reset_warnings.Bind(wx.EVT_BUTTON, self._on_reset_warnings)
        box_sizer.Add(self._btn_reset_warnings, 0,
                      wx.LEFT | wx.RIGHT | wx.TOP, 6)
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: This means to hide cleaners which would do
            # nothing. For example, if Firefox were never used on
            # this system, this option would hide Firefox to simplify
            # the list of cleaners.
            _('Hide irrelevant cleaners'), 'auto_hide')
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences.
            _('Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)'),
            'units_iec')
        box_sizer.AddSpacer(6)

        # TRANSLATORS: Section title in Preferences for user interface options
        # such as dark mode and window behavior.
        box, box_sizer = _section(page, sizer, _('Interface'))
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label to remember the window size and position
            # between application launches.
            _('Remember window geometry'), 'remember_geometry')
        if supports_dark_mode():
            self._add_checkbox(
                box, box_sizer,
                # TRANSLATORS: Checkbox label to enable dark mode in the UI.
                _('Dark mode'), 'dark_mode')
        box_sizer.AddSpacer(6)

        box, box_sizer = _section(
            # TRANSLATORS: Section title on the preferences general page,
            # labelling options for OS integration and advanced/developer features.
            page, sizer, _('Integration and advanced'))
        if not IS_WINDOWS:
            self._add_checkbox(
                box, box_sizer,
                # TRANSLATORS: Checkbox label in the preferences dialog.
                # 'Shred' means securely delete a file to prevent data recovery.
                # 'Context menu' is the menu shown on right-click.
                # 'KDE Plasma' is a Linux desktop environment (proper noun, do not translate).
                _('Add the shred context menu to KDE Plasma'),
                'kde_shred_menu_option')
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label to show diagnostic log messages for
            # troubleshooting.
            _('Show debug messages'), 'debug')
        self._add_checkbox(
            box, box_sizer, EXPERT_MODE_MSG, 'expert_mode',
            tooltip=EXPERT_MODE_DESCRIPTION)
        box_sizer.AddSpacer(6)

        page.SetSizer(sizer)
        return page

    def _build_updates_page(self, notebook):
        page = wx.Panel(notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        # TRANSLATORS: Section title on the preferences updates page.
        box, box_sizer = _section(page, sizer, _('Update notifications'))
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences dialog.
            _('Check periodically for software updates via the Internet'),
            'check_online_updates',
            # TRANSLATORS: Tooltip for the online updates checkbox in the preferences dialog.
            tooltip=_('If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update.'))
        self._add_checkbox(
            box, box_sizer,
            # TRANSLATORS: Checkbox label in the preferences dialog.
            _('Check for new beta releases'), 'check_beta',
            requires='check_online_updates', indent=_SUB_OPTION_INDENT)
        if IS_WINDOWS:
            self._add_checkbox(
                box, box_sizer,
                # TRANSLATORS: Checkbox label in the preferences dialog.
                # Winapp2.ini is a set of cleaning rules from this project:
                # https://github.com/MoscaDotTo/Winapp2
                _('Download and update cleaners from community (winapp2.ini)'),
                'update_winapp2',
                requires='check_online_updates', indent=_SUB_OPTION_INDENT)
        box_sizer.AddSpacer(6)
        page.SetSizer(sizer)
        return page

    # -- checkbox behaviour ------------------------------------------
    def _update_sensitivity(self):
        """Enable each checkbox only while the option it needs is on."""
        for key, required in self._requires.items():
            enabled = not options.has_override(key)
            if required is not None and required in self._checkboxes:
                enabled = enabled and self._checkboxes[required].GetValue()
            self._checkboxes[key].Enable(enabled)
        if self._btn_reset_warnings is not None:
            self._btn_reset_warnings.Enable(self.is_expert_mode())

    def _on_checkbox(self, key):
        cb = self._checkboxes[key]
        if key == 'expert_mode' and cb.GetValue():
            confirmed, _remember = warning_confirm_dialog(
                self, EXPERT_MODE_MSG, EXPERT_MODE_DESCRIPTION,
                show_checkbox=False)
            if not confirmed:
                cb.SetValue(False)
        elif key == 'dark_mode' and wx.Platform == '__WXMSW__':
            # See apply_appearance(): Windows needs a restart.
            self.show_infobar(RESTART_APP_MSG, wx.ICON_INFORMATION)
        self._update_sensitivity()

    def _on_reset_warnings(self, _evt):
        """Reset saved warning confirmations."""
        options.clear_warning_preferences()
        self.show_infobar(
            # TRANSLATORS: Success message shown in the infobar.
            _('Warning confirmations reset.'), wx.ICON_INFORMATION)

    def is_expert_mode(self):
        """Return the expert mode chosen in the dialog (maybe not saved yet)."""
        cb = self._checkboxes.get('expert_mode')
        if cb is None:
            return bool(options.get('expert_mode'))
        return cb.GetValue()

    # -- pages and notices -------------------------------------------
    def select_page(self, page_id):
        """Show the requested page, e.g. ``'cookies'`` or ``'custom'``."""
        if not page_id or page_id not in self._page_ids:
            return
        index = self._page_ids.index(page_id)
        # ChangeSelection does not send a page-changed event.
        self._notebook.ChangeSelection(index)
        self._page_shown(index)

    def get_page(self, page_id):
        """Return the panel of a page, or ``None`` if it is not shown."""
        if page_id not in self._page_ids:
            return None
        return self._notebook.GetPage(self._page_ids.index(page_id))

    def _on_page_changed(self, evt):
        if evt.GetEventObject() is self._notebook:
            self._page_shown(evt.GetSelection())
        evt.Skip()

    def _page_shown(self, index):
        page = self._notebook.GetPage(index)
        if isinstance(page, _CookiesPanel):
            # Finding cookies can be slow, so do it when first shown,
            # like the GTK GUI.
            page.ensure_loaded()

    def _on_language_changed(self):
        self.language_changed = True
        self.refresh_operations = True
        # Translate now so the notice is shown in the chosen language.
        # TRANSLATORS: Notice shown in an infobar after changing a
        # preference that requires starting the application to be
        # effective.
        self.show_infobar(_('Restart BleachBit for full effect.'),
                          wx.ICON_INFORMATION)

    def show_infobar(self, message, flags=wx.ICON_INFORMATION):
        """Show a non-blocking notice that hides itself after a while."""
        self._infobar.show_notice(message, flags)

    # -- saving ------------------------------------------------------
    def commit(self):
        """Save the General and Updates checkboxes into ``Options``.

        Applies the side effects the GTK GUI applies when a checkbox is
        toggled.  The other pages are saved as the user edits them, so
        nothing more is needed here.
        """
        changed = set()
        for key, cb in self._checkboxes.items():
            value = cb.GetValue()
            if bool(options.get(key)) != value:
                changed.add(key)
            options.set(key, value)
        if 'debug' in changed:
            from bleachbit.Log import set_root_log_level  # pylint: disable=import-outside-toplevel
            set_root_log_level(options.get('debug'))
        if 'auto_hide' in changed:
            self.refresh_operations = True
        if 'kde_shred_menu_option' in changed:
            from bleachbit.DesktopMenuOptions import install_kde_service_menu_file  # pylint: disable=import-outside-toplevel
            install_kde_service_menu_file()
        if 'dark_mode' in changed:
            apply_appearance()
        return changed
