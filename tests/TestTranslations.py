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

import ast
import os
import re
import shutil
import subprocess
import unittest
import warnings

_PO_DIR = os.path.join(os.path.dirname(__file__), '..', 'po')

# Matches ${name} placeholders used in NSIS strings, e.g. ${prodname}.
_NSIS_PLACEHOLDER = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


def _parse_po_string(token):
    """Return the decoded PO string literal from the raw token."""
    token = token.strip()
    if not token:
        return ''
    with warnings.catch_warnings():
        # An invalid escape sequence (e.g. ``\q``) raises SyntaxWarning,
        # which CI turns into an error under PYTHONWARNINGS=error. Decode
        # it the way Python does (keeping the backslash) instead.
        warnings.simplefilter('ignore')
        return ast.literal_eval(token)


def _parse_po(path):
    """Yield (msgctxt, msgid, msgstr) tuples from a .po file.

    Minimal stdlib parser; handles multi-line quoted strings and ignores
    fuzzy/obsolete entries. Sufficient for placeholder consistency checks.
    """
    msgctxt = None
    msgid = None
    msgstr = None
    fuzzy = False
    field = None  # which multiline field we are accumulating into

    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for raw_line in [*f, '\n']:
            line = raw_line.rstrip('\n')
            if not line.strip():
                if msgid and msgstr and not fuzzy:
                    results.append((msgctxt, msgid, msgstr))
                msgctxt, msgid, msgstr = None, None, None
                fuzzy = False
                field = None
            elif line.startswith('#,') and 'fuzzy' in line:
                fuzzy = True
            elif line.startswith('#'):
                continue
            elif line.startswith('msgctxt '):
                msgctxt = _parse_po_string(line[len('msgctxt '):])
                field = 'msgctxt'
            elif line.startswith('msgid '):
                msgid = _parse_po_string(line[len('msgid '):])
                field = 'msgid'
            elif line.startswith('msgstr '):
                msgstr = _parse_po_string(line[len('msgstr '):])
                field = 'msgstr'
            elif line.startswith('"'):
                text = _parse_po_string(line)
                if field == 'msgctxt' and msgctxt is not None:
                    msgctxt += text
                elif field == 'msgid' and msgid is not None:
                    msgid += text
                elif field == 'msgstr' and msgstr is not None:
                    msgstr += text
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

    def _po_entries(self, po_path, failures):
        """Parse a .po file, recording a clean failure if it is malformed."""
        try:
            return _parse_po(po_path)
        except (SyntaxError, ValueError) as e:
            failures.append(
                f"{os.path.basename(po_path)}: parse error: {e!r}")
            return []

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
            for msgctxt, msgid, msgstr in self._po_entries(po_path, failures):
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

    def test_no_excess_backslash_escapes(self):
        """Translations must not contain excess backslash escapes.

        Regression test for excess escaping in Indonesian and Sinhala, where
        quotes or newlines had extra backslashes (``\\\\\\"`` or ``\\\\\\n``).
        """
        failures = []
        for po_path in self._po_files():
            for msgctxt, msgid, msgstr in self._po_entries(po_path, failures):
                if '\\"' in msgstr or '\\\n' in msgstr:
                    failures.append(
                        f"{os.path.basename(po_path)}: msgctxt={msgctxt!r} "
                        f"msgid={msgid!r} msgstr={msgstr!r}")
        self.assertEqual([], failures,
                         "Unexpected backslash escapes in translations:\n" +
                         "\n".join(failures))

    def test_parse_po_string_decodes_escapes(self):
        """PO string parser decodes escaped quotes and backslash-newline."""
        self.assertEqual(_parse_po_string('"Say \\"hello\\""'), 'Say "hello"')
        self.assertEqual(_parse_po_string('"Line 1\\\\\\n"'), 'Line 1\\\n')

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
