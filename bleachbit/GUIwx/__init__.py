# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Experimental wxPython GUI for BleachBit (MVP).

This package coexists with the GTK GUI (``bleachbit.GuiApplication``).
It is launched from the top-level script ``bleachbit-wx.py``.

Design notes
------------
* Reuses ``bleachbit.Cleaner``, ``bleachbit.CleanerML``, ``bleachbit.Options``
  and ``bleachbit.Worker`` unchanged.
* Runs ``Worker.run()`` on a background thread and marshals UI updates
  back to the wx main thread via ``wx.CallAfter``.
* The thread seam is intentional so the worker can later move to a
  subprocess (including an elevated subprocess) without changing the
  front-end.
"""
