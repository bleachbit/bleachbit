#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Delete the cleaners that have nothing to do on a platform

Packaging uses this so a package only ships the cleaners for its
operating system. The platform uses the sys.platform names, such as
linux, win32, darwin, or freebsd.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable-next=wrong-import-position
from bleachbit.CleanerML import prune_cleaners


def main():
    """Command line entry point"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        'platform', help='target sys.platform, such as linux or win32')
    parser.add_argument(
        'dirname', nargs='+', help='directory of cleaner XML files')
    args = parser.parse_args()
    for dirname in args.dirname:
        for pathname in prune_cleaners(dirname, args.platform):
            print(f'deleted {pathname}')


if __name__ == '__main__':
    main()
