#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
BleachBit TUI Launcher

Entry point for the frozen Windows executable.  Supports both TUI
(interactive terminal UI) and CLI (command-line scripting) modes:

    bleachbit_tui.exe                          → TUI
    bleachbit_tui.exe --tui                    → TUI (explicit)
    bleachbit_tui.exe --preview firefox.cache  → CLI (scripting)
    bleachbit_tui.exe --clean firefox.cache    → CLI (scripting)
    bleachbit_tui.exe --list-cleaners          → CLI (scripting)

No GTK dependencies required for either mode.
"""

import os
import sys

if os.name == 'nt':
    # Suppress Windows error popups during file operations.
    # These imports are available via pypiwin32 (required for
    # BleachBit's Windows functionality like file wiping).
    import win32api  # pylint: disable=import-error
    import win32con  # pylint: disable=import-error
    win32api.SetErrorMode(win32con.SEM_FAILCRITICALERRORS |
                          win32con.SEM_NOGPFAULTERRORBOX |
                          win32con.SEM_NOOPENFILEERRORBOX)

if __name__ == "__main__":
    # --tui flag takes priority, matching bleachbit.py behavior
    if '--tui' in sys.argv:
        sys.argv.remove('--tui')

    if len(sys.argv) == 1:
        # No arguments — start interactive TUI
        from bleachbit.tui.app import BleachBitTUI
        BleachBitTUI().run()
    else:
        # Has arguments — delegate to CLI (scripting mode)
        import bleachbit.CLI
        bleachbit.CLI.process_cmd_line()
