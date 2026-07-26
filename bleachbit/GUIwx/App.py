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

    # Set by ``run()`` before ``OnInit`` runs.
    _auto_exit = False
    _shred_paths = None

    def OnInit(self):  # noqa: N802 - wx API
        frame = MainFrame(shred_paths=self._shred_paths,
                          auto_exit=self._auto_exit)
        frame.Show()
        self.SetTopWindow(frame)
        if self._shred_paths:
            # Shred paths supplied on the command line (e.g. the Windows
            # Explorer context-menu invocation ``--gui-wx --exit path``).
            # Run on the next event-loop iteration so the window is
            # fully realized first; ``MainFrame.worker_done`` closes the
            # window when ``auto_exit`` is set.  Mirrors the GTK behavior
            # in ``GuiApplication.do_activate``.
            wx.CallAfter(frame._shred_paths, self._shred_paths)
        elif self._auto_exit:
            # Used by automated testing (e.g. ``--gui-wx --exit``) to
            # verify the GUI can start without keeping it open.  Close
            # the top window after the event loop starts so the window
            # actually gets created and shown first.
            wx.CallAfter(frame.Close)
        return True


def run(auto_exit=False, shred_paths=None):
    """Start the wx GUI and block until the window closes."""
    # ``OnInit`` runs during ``wx.App.__init__``, so the parameters must
    # be visible on the class before the instance is constructed.
    BleachBitWxApp._auto_exit = auto_exit
    BleachBitWxApp._shred_paths = shred_paths
    app = BleachBitWxApp(False)
    app.MainLoop()
    return 0
