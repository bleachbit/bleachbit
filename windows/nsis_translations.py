#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

"""Generate NSIS translation resources from PO files."""

import argparse
import ast
import os
import re
import sys

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

    pattern = re.compile(
        r'^\s*LangString\s+(\S+)\s+\$\{(LANG_[^}]+)\}\s+"(.*)"\s*$')

    with open(nsh_path, encoding='utf-8') as nsh_file:
        for line in nsh_file:
            stripped = line.strip()
            if stripped.startswith('!ifdef LANG_'):
                current_lang = stripped.split()[1]
                lang_strings.setdefault(current_lang, {})
                continue
            if current_lang and stripped.startswith('!endif'):
                current_lang = None
                continue
            if current_lang is None:
                header_lines.append(line)
                continue

            match = pattern.match(line)
            if match:
                key, lang_macro, text = match.groups()
                lang_strings.setdefault(lang_macro, {})[key] = text

    return header_lines, lang_strings


def _unescape_nsis_text(text):
    """Convert NSIS-escaped sequences to plain text for PO generation."""
    text = text.replace('$\r$\n', '\n')
    text = text.replace('$\n', '\n').replace('$\r', '\n')
    text = text.replace('$\\"', '"').replace('$"', '"')
    return text


def _escape_po_text(text):
    """Escape text for safe inclusion inside PO msgid/msgstr entries."""
    return (text.replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n'))


def _escape_nsis_text(text):
    """Escape arbitrary text so it is valid inside an NSIS LangString."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\n', '$\\r$\\n')
    text = text.replace('"', '$\\"')
    return text


def write_nsis_pot():
    """Generate the template POT file using the English NSIS strings."""
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
            base_text = existing_entries.get(key, english_strings[key])
            if locale == 'en':
                text = english_strings[key]
            else:
                text = locale_entries.get(key, base_text)
            lines.append(
                f'\tLangString {key} ${{{lang_macro}}} "{_escape_nsis_text(text)}"\n')
        lines.append('!endif\n\n')

    with open(OUTPUT_NSH, 'w', encoding='utf-8') as nsh_file:
        nsh_file.write(''.join(lines))


def main():
    """CLI entry point for generating NSIS POT and language files."""
    parser = argparse.ArgumentParser(
        description='Generate NSIS translation files from PO sources.')
    parser.add_argument('--pot', action='store_true',
                        help='Generate po/nsis.pot from NSIS English strings.')
    parser.add_argument('--generate', action='store_true',
                        help='Generate NsisInclude/BleachBitLang.nsh from po/*.po.')
    args = parser.parse_args()

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
