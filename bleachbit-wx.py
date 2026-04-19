#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Launcher for the experimental wxPython front-end.

Usage::

    python3 bleachbit-wx.py

This front-end coexists with the GTK GUI (``bleachbit.py``) and the
CLI (``bleachbit.py --help``).  It shares the same backend modules
(``Cleaner``, ``CleanerML``, ``Options``, ``Worker``) and on-disk
configuration.
"""

import os
import sys


def main():
    # Mirror the Linux path fix-up from bleachbit.py so the script
    # works from a system install too.
    if os.name == 'posix' and os.path.isdir('/usr/share/bleachbit'):
        sys.path.append('/usr/share/')

    try:
        import wx  # noqa: F401  (verify availability early)
    except ImportError as exc:
        sys.stderr.write(
            'wxPython is required for this GUI.  Install with:\n'
            '    pip install wxPython\n'
            '\n%s\n' % exc)
        return 2

    from bleachbit.GUIwx.App import run
    return run()


if __name__ == '__main__':
    sys.exit(main())
