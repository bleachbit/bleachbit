# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
wx application entry point for the experimental wxPython GUI.
"""

import logging

import wx

from bleachbit.GUIwx.MainFrame import MainFrame

logger = logging.getLogger(__name__)


class BleachBitWxApp(wx.App):
    """Top-level :class:`wx.App` for the wx MVP."""

    def OnInit(self):  # noqa: N802 - wx API
        frame = MainFrame()
        frame.Show()
        self.SetTopWindow(frame)
        return True


def run():
    """Start the wx GUI and block until the window closes."""
    app = BleachBitWxApp(False)
    app.MainLoop()
    return 0
