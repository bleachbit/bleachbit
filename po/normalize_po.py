#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.
"""Normalize .pot/.po files for gettext on Windows.

xgettext on Windows may emit backslashes in #: lines and CRLF line endings.
msgcat can also emit invalid reference continuations (leading whitespace without
#:) when inputs mix backslashes and CRLF. This script repairs those lines,
converts paths to forward slashes, and writes Unix (LF) newlines.
"""

from __future__ import print_function

import argparse
import re
import sys

_SOURCE_REF = re.compile(
    r'^(?:#:\s*)?(?P<path>(?:\.\./)?(?:cleaners/|bleachbit/|data/)\S+\.(?:xml|py|ui))$'
)


def _normalize_reference_line(line):
    """Return a normalized #: line, or None if line is not a source reference."""
    match = _SOURCE_REF.match(line.strip().replace('\\', '/'))
    if match:
        return '#: %s' % match.group('path').replace('\\', '/')
    if line.startswith('#:'):
        return line.replace('\\', '/')
    if line[:1] in ' \t':
        raw = line.strip()
        if raw.replace('\\', '/').startswith('../'):
            return '#: %s' % raw.replace('\\', '/')
    return None


def normalize_po(path):
    with open(path, 'rb') as handle:
        text = handle.read().decode('utf-8')
    lines = text.splitlines()
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        for line in lines:
            ref = _normalize_reference_line(line)
            if ref is not None:
                line = ref
            handle.write(line + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pofile', help='Path to the .pot or .po file to update in place')
    args = parser.parse_args(argv)
    try:
        normalize_po(args.pofile)
    except IOError as err:
        print('error: %s' % err, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
