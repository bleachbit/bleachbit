# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Minimal preferences dialog for the experimental wxPython GUI.

Only a handful of frequently-used options are surfaced.  The full
preferences dialog (tabs for whitelist, language, drives, etc.) is
out of scope for the MVP.
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


class PreferencesDialog(wx.Dialog):
    """Simple wx preferences dialog with a handful of checkboxes."""

    def __init__(self, parent):
        super().__init__(
            parent, title=_('Preferences'),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._checkboxes = {}
        for key, label in _PREFS:
            cb = wx.CheckBox(panel, label=label)
            cb.SetValue(bool(options.get(key)))
            sizer.Add(cb, 0, wx.ALL, 8)
            self._checkboxes[key] = cb

        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        outer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        outer.Add(panel, 1, wx.EXPAND)
        if btns:
            outer.Add(btns, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizerAndFit(outer)
        self.SetMinSize((420, -1))

    def commit(self):
        """Save the dialog state into ``Options``."""
        for key, cb in self._checkboxes.items():
            options.set(key, cb.GetValue())
