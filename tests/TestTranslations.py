# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Tests for translation (.po) files.

These checks cover bugs that ``msgfmt --check`` cannot catch, such as
NSIS ``${placeholder}`` typos in translations (see commit 104a6211 which
fixed ``${proname}`` -> ``${prodname}`` in Italian).

For format-string validation run ``make -C po tests``.
"""

import os
import re
import shutil
import subprocess
import unittest

_PO_DIR = os.path.join(os.path.dirname(__file__), '..', 'po')

# Matches ${name} placeholders used in NSIS strings, e.g. ${prodname}.
_NSIS_PLACEHOLDER = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


def _parse_po(path):
    """Yield (msgctxt, msgid, msgstr) tuples from a .po file.

    Minimal stdlib parser; handles multi-line quoted strings and ignores
    fuzzy/obsolete entries. Sufficient for placeholder consistency checks.
    """
    msgctxt = None
    msgid = None
    msgstr = None
    field = None  # which multiline field we are accumulating into

    def _unescape(s):
        return s.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')

    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('msgctxt '):
                msgctxt = _unescape(line[len('msgctxt '):].strip().strip('"'))
                field = None
            elif line.startswith('msgid '):
                msgid = _unescape(line[len('msgid '):].strip().strip('"'))
                field = 'msgid'
            elif line.startswith('msgstr '):
                msgstr = _unescape(line[len('msgstr '):].strip().strip('"'))
                field = 'msgstr'
            elif line.startswith('"'):
                text = _unescape(line.strip().strip('"'))
                if field == 'msgid':
                    msgid += text
                elif field == 'msgstr':
                    msgstr += text
            elif line == '':
                if msgid is not None and msgstr:
                    results.append((msgctxt, msgid, msgstr))
                msgctxt, msgid, msgstr = None, None, None
                field = None
    if msgid is not None and msgstr:
        results.append((msgctxt, msgid, msgstr))
    return results


def _xgettext_entries(source_path):
    """Return (msgid, hints) for each entry xgettext extracts from a file.

    ``hints`` are the ``#.`` extracted comments, i.e. the TRANSLATORS
    hints that translators see in the .pot file. Return None when
    xgettext is not installed.
    """
    xgettext = shutil.which('xgettext')
    if xgettext is None:
        return None
    proc = subprocess.run(
        [xgettext, '--language=Python', '--from-code=UTF-8',
         '--add-comments=TRANSLATORS', '-k_', '-o', '-', source_path],
        capture_output=True, encoding='utf-8', check=True)
    entries = []
    for block in proc.stdout.split('\n\n'):
        hints = []
        msgid = ''
        in_msgid = False
        for line in block.splitlines():
            if line.startswith('#. '):
                hints.append(line[3:])
            elif line.startswith('msgid '):
                in_msgid = True
                msgid = line[len('msgid '):].strip()[1:-1]
            elif line.startswith('msgstr'):
                in_msgid = False
            elif in_msgid and line.startswith('"'):
                msgid += line.strip()[1:-1]
        if msgid:
            entries.append((msgid, hints))
    return entries


class TestTranslations(unittest.TestCase):
    """Validate .po files beyond what msgfmt --check covers."""

    def _po_files(self):
        po_dir = os.path.abspath(_PO_DIR)
        return [os.path.join(po_dir, f)
                for f in os.listdir(po_dir) if f.endswith('.po')]

    def test_nsis_placeholders_match(self):
        """NSIS translations must keep the same ${...} placeholders as msgid.

        Regression test for commit 104a6211 (Italian ${proname} typo).
        """
        failures = []
        for po_path in self._po_files():
            for msgctxt, msgid, msgstr in _parse_po(po_path):
                if not msgctxt or not msgctxt.startswith('nsis:'):
                    continue
                expected = sorted(_NSIS_PLACEHOLDER.findall(msgid))
                actual = sorted(_NSIS_PLACEHOLDER.findall(msgstr))
                if expected != actual:
                    failures.append(
                        f"{os.path.basename(po_path)}: msgctxt={msgctxt} "
                        f"expected={expected} actual={actual}")
        self.assertEqual([], failures,
                         "NSIS placeholder mismatch in translations:\n" +
                         "\n".join(failures))

    def test_elevated_retry_strings_have_translator_hints(self):
        """The elevated-retry dialog strings must reach translators with hints.

        xgettext attaches a TRANSLATORS comment only when it is on the
        row right before the string (see doc/CONTRIBUTING.md). A hint
        above ``msg = _(`` with the string on the next row is lost.
        """
        source = os.path.join(os.path.dirname(__file__), '..',
                              'bleachbit', 'GuiWindow.py')
        entries = _xgettext_entries(source)
        if entries is None:
            self.skipTest('xgettext not found')
        fragments = (
            'Retry with administrator privileges?',
            'Files deleted successfully.',
            'The elevated deletion failed or was canceled.',
        )
        for fragment in fragments:
            matching = [hints for msgid, hints in entries
                        if fragment in msgid]
            self.assertTrue(matching, f'string not extracted: {fragment!r}')
            self.assertTrue(
                any(hint.startswith('TRANSLATORS') for hint in matching[0]),
                f'missing TRANSLATORS hint for: {fragment!r}')


if __name__ == '__main__':
    unittest.main()
