#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Generate NSIS translation resources from PO files.

Reads strings:
- English strings from windows/NsisInclude/NsisMultiUserLang.nsh
- localized from strings po/*.po

Then, it writes:
- English strings to po/nsis.pot (template)
- localized strings to windows/NsisInclude/NsisMultiUserLang.nsh

This script is invoked by ``make nsis.pot`` in po/ (``po/Makefile``)
or run manually via CLI flags."""

import argparse
import ast
import os
import re
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PO_DIR = os.path.join(ROOT_DIR, 'po')
NSIS_MULTIUSER_LANG = os.path.join(
    ROOT_DIR, 'windows', 'NsisInclude', 'NsisMultiUserLang.nsh')
OUTPUT_NSH = NSIS_MULTIUSER_LANG
OUTPUT_POT = os.path.join(PO_DIR, 'nsis.pot')

LANGUAGE_MAP = [
    ('en', 'LANG_ENGLISH'),
    ('sq', 'LANG_ALBANIAN'),
    ('ar', 'LANG_ARABIC'),
    ('hy', 'LANG_ARMENIAN'),
    ('ast', 'LANG_ASTURIAN'),
    ('eu', 'LANG_BASQUE'),
    ('be', 'LANG_BELARUSIAN'),
    ('bs', 'LANG_BOSNIAN'),
    ('bg', 'LANG_BULGARIAN'),
    ('ca', 'LANG_CATALAN'),
    ('hr', 'LANG_CROATIAN'),
    ('cs', 'LANG_CZECH'),
    ('da', 'LANG_DANISH'),
    ('nl', 'LANG_DUTCH'),
    ('et', 'LANG_ESTONIAN'),
    ('fi', 'LANG_FINNISH'),
    ('fr', 'LANG_FRENCH'),
    ('gl', 'LANG_GALICIAN'),
    ('de', 'LANG_GERMAN'),
    ('el', 'LANG_GREEK'),
    ('he', 'LANG_HEBREW'),
    ('hu', 'LANG_HUNGARIAN'),
    ('id', 'LANG_INDONESIAN'),
    ('it', 'LANG_ITALIAN'),
    ('ja', 'LANG_JAPANESE'),
    ('ko', 'LANG_KOREAN'),
    ('ku', 'LANG_KURDISH'),
    ('lv', 'LANG_LATVIAN'),
    ('lt', 'LANG_LITHUANIAN'),
    ('ms', 'LANG_MALAY'),
    ('nb', 'LANG_NORWEGIAN'),
    ('nn', 'LANG_NORWEGIANNYNORSK'),
    ('pl', 'LANG_POLISH'),
    ('pt', 'LANG_PORTUGUESE'),
    ('pt_BR', 'LANG_PORTUGUESEBR'),
    ('ro', 'LANG_ROMANIAN'),
    ('ru', 'LANG_RUSSIAN'),
    ('sr', 'LANG_SERBIAN'),
    ('zh_CN', 'LANG_SIMPCHINESE'),
    ('sk', 'LANG_SLOVAK'),
    ('sl', 'LANG_SLOVENIAN'),
    ('es', 'LANG_SPANISH'),
    ('sv', 'LANG_SWEDISH'),
    ('th', 'LANG_THAI'),
    ('zh_TW', 'LANG_TRADCHINESE'),
    ('tr', 'LANG_TURKISH'),
    ('uk', 'LANG_UKRAINIAN'),
    ('uz', 'LANG_UZBEK'),
    ('vi', 'LANG_VIETNAMESE'),
]

TRANSLATION_HINTS = {
    'ALREADY_INSTALLED': 'Dialog shown when an older version is detected. {prodname} is replaced with the product name. Do not translate placeholder.',
    'MULTIUSER_ADMIN_CREDENTIALS_REQUIRED': 'Message shown on the installation mode page description when admin rights are needed.',
    'MULTIUSER_ADMIN_UNINSTALL_CREDENTIALS_REQUIRED': 'Message shown on the installation mode page description when admin rights are needed to uninstall.',
    'MULTIUSER_ALL_USERS_UMUI': 'Radio button label for Ultra Modern UI (NSIS). Same as MULTIUSER_ALL_USERS but without the & accelerator.',
    'MULTIUSER_ALL_USERS': 'Radio button label. The & sets the keyboard accelerator (hotkey). Place & before the letter that should be the shortcut key.',
    'MULTIUSER_CURRENT_USER_UMUI': 'Radio button label for Ultra Modern UI (NSIS). Same as MULTIUSER_CURRENT_USER but without the & accelerator. {USER} is a placeholder that will be replaced with the Windows username.',
    'MULTIUSER_CURRENT_USER': 'Radio button label. The & sets the keyboard accelerator (hotkey). Place & before the letter that should be the shortcut key. {USER} is a placeholder that will be replaced with the Windows username.',
    'MULTIUSER_ELEVATION_ERROR': 'Error message shown in dialog box during installation on Windows. {ERROR} is a placeholder that will be replaced with the error details.',
    'MULTIUSER_ELEVATION_NOT_SUPPORTED': 'Error message shown in a dialog box when Windows does not support elevation.',
    'MULTIUSER_INSTALLED_ALL_USERS': 'Radio button option for the method of installation. {VERSION} and {FOLDER} are placeholders replaced by the installer with the installed version and folder path.',
    'MULTIUSER_INSTALLED_CURRENT_USER': 'Radio button option for the method of installation. {VERSION} and {FOLDER} are placeholders replaced by the installer with the installed version and folder path.',
    'MULTIUSER_PAGE_TITLE': 'Title of the installation mode page in the Windows installer. User selects whether to install for all users or the current user.',
    'SECTION_DESKTOP_NAME': 'Name of the desktop section in the Windows installer: user selects which desktop items to install.',
    'SECTION_QUICK_LAUNCH_NAME': 'Name of the quick launch section in the Windows installer: quick launch is a toolbar in the Windows taskbar that allows users to quickly access frequently used programs.',
    'SECTION_SHORTCUTS_NAME': 'Name of the shortcuts section in the Windows installer: user selects which shortcuts to install.',
    'SECTION_START_MENU_NAME': 'Name of the start menu section in the Windows installer: user selects which start menu items to install.',
    'SECTION_TRANSLATIONS_NAME': 'Name of the translations section in the Windows installer: user selects which translations to install.',
    'SHORTCUT_DEBUGGING_TERMINAL': 'Shortcut name for a desktop shortcut that opens a debugging terminal.',
    'SHORTCUT_NO_UAC': 'Shortcut name for a desktop shortcut that runs without UAC elevation (admin privileges).',
    'SHRED_SHELL_MENU': 'Context menu item in Windows Explorer for securely shredding files.',
}


def _get_all_nsis_langstring_keys():
    """Extract all unique LangString key names from the NSIS language file."""
    _header, lang_strings = _parse_nsis_lang_strings(NSIS_MULTIUSER_LANG)
    all_keys = set()
    for _lang_macro, strings in lang_strings.items():
        all_keys.update(strings.keys())
    return all_keys


def validate_translation_hints():
    """Validate that all TRANSLATION_HINTS keys correspond to real LangString definitions.

    Raises:
        RuntimeError: If any hints reference non-existent LangString keys.
    """
    actual_keys = _get_all_nsis_langstring_keys()
    hint_keys = set(TRANSLATION_HINTS.keys())
    orphaned_hints = hint_keys - actual_keys

    if orphaned_hints:
        raise RuntimeError(
            f'TRANSLATION_HINTS contains orphaned keys not found in NSIS files: '
            f'{sorted(orphaned_hints)}'
        )

def _parse_po_string(token):
    """Return the decoded PO string literal from the raw token."""
    token = token.strip()
    if not token:
        return ''
    return ast.literal_eval(token)


def _parse_po_file(po_path):
    """Parse a PO file and return a mapping of msgctxt to translated text."""
    entries = {}
    current_ctx = None
    current_id = None
    current_str = None
    state = None

    with open(po_path, encoding='utf-8') as po_file:
        for raw_line in po_file:
            line = raw_line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            if line.startswith('msgctxt '):
                if current_ctx and current_id is not None and current_str is not None:
                    entries[current_ctx] = current_str if current_str else current_id
                current_ctx = _parse_po_string(line[len('msgctxt '):])
                current_id = None
                current_str = None
                state = 'msgctxt'
                continue
            if line.startswith('msgid '):
                current_id = _parse_po_string(line[len('msgid '):])
                state = 'msgid'
                continue
            if line.startswith('msgstr '):
                current_str = _parse_po_string(line[len('msgstr '):])
                state = 'msgstr'
                continue
            if line.startswith('"'):
                text = _parse_po_string(line)
                if state == 'msgctxt' and current_ctx is not None:
                    current_ctx += text
                elif state == 'msgid' and current_id is not None:
                    current_id += text
                elif state == 'msgstr' and current_str is not None:
                    current_str += text

        if current_ctx and current_id is not None and current_str is not None:
            entries[current_ctx] = current_str if current_str else current_id

    return entries


def _parse_nsis_lang_strings(nsh_path):
    """Extract header lines and LangString definitions from an NSIS file."""
    header_lines = []
    lang_strings = {}
    current_lang = None
    in_header = True

    pattern = re.compile(
        r'^\s*LangString\s+(\S+)\s+\$\{(LANG_[^}]+)\}\s+"(.*)"\s*$')

    with open(nsh_path, encoding='utf-8') as nsh_file:
        for line in nsh_file:
            stripped = line.strip()
            if stripped.startswith('!ifdef LANG_'):
                current_lang = stripped.split()[1]
                lang_strings.setdefault(current_lang, {})
                in_header = False
                continue
            if current_lang and stripped.startswith('!endif'):
                current_lang = None
                continue
            if current_lang is None and in_header:
                if stripped.startswith('; This file is auto-generated'):
                    in_header = False
                    continue
                header_lines.append(line)
                continue

            match = pattern.match(line)
            if match:
                key, lang_macro, text = match.groups()
                lang_strings.setdefault(lang_macro, {})[key] = _unescape_nsis_text(text)

    return header_lines, lang_strings


def _unescape_nsis_text(text):
    """Convert NSIS-escaped sequences to plain text for PO generation."""
    text = text.replace(r'$\r$\n', '\n')
    text = text.replace(r'$\n', '\n').replace(r'$\r', '\n')
    text = text.replace(r'$\"', '"')
    return text


def _escape_po_text(text):
    """Escape text for safe inclusion inside PO msgid/msgstr entries."""
    return (text.replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n'))


def _escape_nsis_text(text):
    """Escape arbitrary text so it is valid inside an NSIS LangString."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\n', r'$\r$\n')
    text = text.replace('"', r'$\"')
    return text


def write_nsis_pot():
    """Generate the template POT file using the English NSIS strings."""
    # Validate hints before generating POT
    validate_translation_hints()
    _header, lang_strings = _parse_nsis_lang_strings(NSIS_MULTIUSER_LANG)
    english_strings = lang_strings.get('LANG_ENGLISH', {})
    if not english_strings:
        raise RuntimeError(
            'No LANG_ENGLISH strings found in NSIS language file.')
    header = (
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: bleachbit\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n\n'
    )

    lines = [header]
    for key in sorted(english_strings):
        msgid = _escape_po_text(_unescape_nsis_text(english_strings[key]))
        lines.append('#: windows/NsisInclude/NsisMultiUserLang.nsh\n')
        hint = TRANSLATION_HINTS.get(key)
        if hint:
            lines.append(f'#. TRANSLATORS: {hint}\n')
        if '&' in msgid:
            lines.append(
                '#. TRANSLATORS: The character \'&\' positions the keyboard accelerator key.\n'
                '#. TRANSLATORS: For example, \'&anyone\' sets \'a\' as the accelerator key (Alt+a).\n')
        lines.append(f'msgctxt "nsis:{key}"\n')
        lines.append(f'msgid "{msgid}"\n')
        lines.append('msgstr ""\n\n')

    with open(OUTPUT_POT, 'w', encoding='utf-8') as pot_file:
        pot_file.write(''.join(lines))


def write_nsis_langfile():
    """Render the NSIS LangString include file from PO translation data."""
    header_lines, lang_strings = _parse_nsis_lang_strings(NSIS_MULTIUSER_LANG)
    english_strings = lang_strings.get('LANG_ENGLISH', {})
    if not english_strings:
        raise RuntimeError(
            'No LANG_ENGLISH strings found in NSIS language file.')
    translations = {}

    for locale, _lang_macro in LANGUAGE_MAP:
        if locale == 'en':
            translations[locale] = {}
            continue
        po_path = os.path.join(PO_DIR, f'{locale}.po')
        if not os.path.exists(po_path):
            translations[locale] = {}
            continue
        entries = _parse_po_file(po_path)
        nsis_entries = {
            key[len('nsis:'):]: value
            for key, value in entries.items()
            if key.startswith('nsis:')
        }
        translations[locale] = nsis_entries

    lines = list(header_lines)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] = lines[-1] + '\n'
    lines.extend([
        '; This file is auto-generated by windows/nsis_translations.py\n',
        '; Do not edit manually.\n',
        '; Source: po/*.po\n',
        '\n',
    ])

    for locale, lang_macro in LANGUAGE_MAP:
        lines.append(f'!ifdef {lang_macro}\n')
        locale_entries = translations.get(locale, {})
        existing_entries = lang_strings.get(lang_macro, {})
        for key in sorted(english_strings):
            if locale == 'en':
                text = english_strings[key]
            else:
                translated = locale_entries.get(key, '')
                if translated:
                    text = translated
                else:
                    text = existing_entries.get(key, english_strings[key])
            lines.append(
                f'\tLangString {key} ${{{lang_macro}}} "{_escape_nsis_text(text)}"\n')
        lines.append('!endif\n\n')

    with open(OUTPUT_NSH, 'w', encoding='utf-8') as nsh_file:
        nsh_file.write(''.join(lines))


class TestNsisEscaping(unittest.TestCase):
    """Test cases for NSIS text escaping and unescaping functions."""

    def test_unescape_nsis_newlines(self):
        """Test unescaping NSIS newline sequences."""
        self.assertEqual(_unescape_nsis_text(r'Line1$\r$\nLine2'), 'Line1\nLine2')
        self.assertEqual(_unescape_nsis_text(r'Line1$\nLine2'), 'Line1\nLine2')
        self.assertEqual(_unescape_nsis_text(r'Line1$\rLine2'), 'Line1\nLine2')

    def test_unescape_nsis_quotes(self):
        """Test unescaping NSIS quote sequences."""
        self.assertEqual(_unescape_nsis_text(r'Text with $\"quotes$\"'), 'Text with "quotes"')

    def test_unescape_nsis_dollar_signs(self):
        """Test that literal dollar signs in NSIS strings are preserved."""
        self.assertEqual(_unescape_nsis_text(r'$\"{FOLDER}$\"'), '"{FOLDER}"')
        self.assertEqual(_unescape_nsis_text('Price: $100'), 'Price: $100')

    def test_unescape_nsis_no_double_escaping(self):
        """Regression test: ensure we don't treat $$ as an escape sequence."""
        text = r'$\"{FOLDER}$\"'
        result = _unescape_nsis_text(text)
        self.assertEqual(result, '"{FOLDER}"')
        self.assertNotIn('$$', result)

    def test_escape_po_text_backslashes(self):
        """Test escaping backslashes for PO format."""
        self.assertEqual(_escape_po_text('path\\to\\file'), 'path\\\\to\\\\file')

    def test_escape_po_text_quotes(self):
        """Test escaping quotes for PO format."""
        self.assertEqual(_escape_po_text('Say "hello"'), 'Say \\"hello\\"')

    def test_escape_po_text_newlines(self):
        """Test escaping newlines for PO format."""
        self.assertEqual(_escape_po_text('Line1\nLine2'), 'Line1\\nLine2')

    def test_escape_nsis_newlines(self):
        """Test escaping newlines for NSIS format."""
        self.assertEqual(_escape_nsis_text('Line1\nLine2'), 'Line1$\\r$\\nLine2')
        self.assertEqual(_escape_nsis_text('Line1\r\nLine2'), 'Line1$\\r$\\nLine2')

    def test_escape_nsis_quotes(self):
        """Test escaping quotes for NSIS format."""
        self.assertEqual(_escape_nsis_text('Text with "quotes"'), 'Text with $\\"quotes$\\"')

    def test_escape_nsis_no_dollar_escaping(self):
        """Regression test: ensure we don't escape literal $ as $$."""
        text = 'Price: $100'
        result = _escape_nsis_text(text)
        self.assertEqual(result, 'Price: $100')
        self.assertNotIn('$$', result)

    def test_roundtrip_nsis_to_po_to_nsis(self):
        """Test that NSIS -> PO -> NSIS roundtrip preserves content."""
        original_nsis = r'Version {VERSION} is installed in $\"{FOLDER}$\".'
        unescaped = _unescape_nsis_text(original_nsis)
        self.assertEqual(unescaped, 'Version {VERSION} is installed in "{FOLDER}".')
        po_escaped = _escape_po_text(unescaped)
        self.assertEqual(po_escaped, 'Version {VERSION} is installed in \\"{FOLDER}\\".')
        back_to_plain = po_escaped.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        self.assertEqual(back_to_plain, 'Version {VERSION} is installed in "{FOLDER}".')
        back_to_nsis = _escape_nsis_text(back_to_plain)
        self.assertEqual(back_to_nsis, original_nsis)

    def test_complex_string_with_multiple_escapes(self):
        """Test handling of strings with multiple escape sequences."""
        nsis_text = r'${prodname} is installed.$\r$\nClick $\"OK$\" to continue.'
        unescaped = _unescape_nsis_text(nsis_text)
        self.assertEqual(unescaped, '${prodname} is installed.\nClick "OK" to continue.')
        re_escaped = _escape_nsis_text(unescaped)
        self.assertEqual(re_escaped, nsis_text)

    def test_parse_po_string(self):
        """Test PO string literal parsing."""
        self.assertEqual(_parse_po_string('"Hello world"'), 'Hello world')
        self.assertEqual(_parse_po_string('"Line1\\nLine2"'), 'Line1\nLine2')
        self.assertEqual(_parse_po_string('"Say \\"hi\\""'), 'Say "hi"')
        self.assertEqual(_parse_po_string(''), '')
        self.assertEqual(_parse_po_string('  '), '')

    def test_parse_nsis_stops_at_autogen_marker(self):
        """Regression test: ensure header parsing stops at auto-generated marker."""
        content = '''/*
Header line 1
Header line 2
*/


; This file is auto-generated by windows/nsis_translations.py
; Do not edit manually.
; Source: po/*.po

!ifdef LANG_ENGLISH
\tLangString TEST_KEY ${LANG_ENGLISH} "Test value"
!endif
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nsh', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            header_lines, lang_strings = _parse_nsis_lang_strings(temp_path)
            # Header should not include the auto-generated comment or anything after it
            header_text = ''.join(header_lines)
            self.assertNotIn('auto-generated', header_text)
            # But it should have parsed the LangStrings
            self.assertIn('LANG_ENGLISH', lang_strings)
            self.assertEqual(lang_strings['LANG_ENGLISH']['TEST_KEY'], 'Test value')
        finally:
            os.unlink(temp_path)

    def test_parse_nsis_unescapes_text(self):
        """Regression test: ensure parsing unescapes NSIS text to prevent duplication."""
        content = '''!ifdef LANG_ENGLISH
\tLangString TEST_QUOTES ${LANG_ENGLISH} "Text with $\\"quotes$\\""
\tLangString TEST_NEWLINE ${LANG_ENGLISH} "Line1$\\r$\\nLine2"
!endif
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nsh', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            _header, lang_strings = _parse_nsis_lang_strings(temp_path)
            # Text should be unescaped when read
            self.assertEqual(lang_strings['LANG_ENGLISH']['TEST_QUOTES'], 'Text with "quotes"')
            self.assertEqual(lang_strings['LANG_ENGLISH']['TEST_NEWLINE'], 'Line1\nLine2')
            # Should not contain NSIS escape sequences
            self.assertNotIn('$\\', lang_strings['LANG_ENGLISH']['TEST_QUOTES'])
            self.assertNotIn('$\\', lang_strings['LANG_ENGLISH']['TEST_NEWLINE'])
        finally:
            os.unlink(temp_path)

    def test_roundtrip_prevents_escape_duplication(self):
        """Regression test: ensure read-write cycle doesn't duplicate escapes."""
        original_escaped = r'Version {VERSION} is installed in $\"{FOLDER}$\".'

        # Simulate reading from file (should unescape)
        unescaped = _unescape_nsis_text(original_escaped)
        self.assertEqual(unescaped, 'Version {VERSION} is installed in "{FOLDER}".')

        # Simulate writing back to file (should re-escape)
        re_escaped = _escape_nsis_text(unescaped)
        self.assertEqual(re_escaped, original_escaped)

        # Multiple cycles should not change the result
        for _ in range(5):
            unescaped = _unescape_nsis_text(re_escaped)
            re_escaped = _escape_nsis_text(unescaped)
            self.assertEqual(re_escaped, original_escaped)
            # Should never have doubled escapes like $\$\
            self.assertNotIn('$\\$\\', re_escaped)

    def test_validate_translation_hints_passes_with_valid_hints(self):
        """Test that validation passes when all hints correspond to real strings."""
        # This should not raise any exception since we cleaned up orphaned hints
        validate_translation_hints()

    def test_validate_translation_hints_fails_on_orphaned_hints(self):
        """Test that validation raises RuntimeError for orphaned hints."""
        original_hints = TRANSLATION_HINTS.copy()
        try:
            # Add a fake hint that doesn't correspond to any real LangString
            TRANSLATION_HINTS['FAKE_ORPHANED_KEY'] = 'This hint has no corresponding LangString.'
            with self.assertRaises(RuntimeError) as context:
                validate_translation_hints()
            self.assertIn('FAKE_ORPHANED_KEY', str(context.exception))
        finally:
            # Restore original hints
            TRANSLATION_HINTS.clear()
            TRANSLATION_HINTS.update(original_hints)


def main():
    """CLI entry point for generating NSIS POT and language files."""
    parser = argparse.ArgumentParser(
        description='Generate NSIS translation files from PO sources.')
    parser.add_argument('--pot', action='store_true',
                        help='Generate po/nsis.pot from NSIS English strings.')
    parser.add_argument('--generate', action='store_true',
                        help='Generate NsisInclude/BleachBitLang.nsh from po/*.po.')
    parser.add_argument('--unittest', action='store_true',
                        help='Run unit tests.')
    args = parser.parse_args()

    if args.unittest:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestNsisEscaping)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1

    if not args.pot and not args.generate:
        parser.print_help()
        return 2

    if args.pot:
        write_nsis_pot()
    if args.generate:
        write_nsis_langfile()

    return 0


if __name__ == '__main__':
    sys.exit(main())
