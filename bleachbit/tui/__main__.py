# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Entry point: python -m bleachbit.tui"""
from bleachbit.tui.app import BleachBitTUI

if __name__ == "__main__":
    BleachBitTUI().run()
