#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

"""Launcher for the Qt-based BleachBit frontend."""

import os
import sys


def main():
    # When running from source tree, ensure local package is preferred.
    repo_root = os.path.dirname(os.path.abspath(__file__))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from bleachbit.QtApplication import run_qt_gui
    return run_qt_gui()


if __name__ == "__main__":
    raise SystemExit(main())

