#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Backport Weblate translation updates from master into the backport branch.

The backport branch has its own template (bleachbit.pot) with strings that differ
from master. Master receives Weblate updates; this script copies those updates
for shared msgids while keeping backport-only translations intact.

Requires: Python 3, polib (`pip install polib`), and GNU gettext (msgmerge).

Typical workflow after refreshing po/bleachbit.pot in the backport worktree:

    \\path\\to\\Python313\\python.exe po\\backport_translations.py

Ensure the master worktree (default: sibling ../bleachbit) is on the branch that
receives Weblate commits (usually master) before running.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

try:
    import polib
except ImportError:
    print(
        "error: polib is required. Install with: pip install polib",
        file=sys.stderr,
    )
    sys.exit(1)


GETTEXT_CANDIDATES = [
    os.environ.get("GETTEXT_DIR"),
    r"C:\msys64\usr\bin",
    r"C:\msys64\mingw64\bin",
    "/usr/bin",
]


@dataclass
class LangStats:
    synced: bool = False
    updated: int = 0
    unchanged: int = 0
    backport_only: int = 0
    master_untranslated: int = 0
    skipped: str = ""


@dataclass
class Summary:
    languages: dict[str, LangStats] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def find_gettext_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    for directory in GETTEXT_CANDIDATES:
        if not directory:
            continue
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            return path
        if os.name == "nt" and not name.lower().endswith(".exe"):
            path_exe = path + ".exe"
            if os.path.isfile(path_exe):
                return path_exe
    raise FileNotFoundError(
        f"Cannot find {name}. Install GNU gettext or set GETTEXT_DIR."
    )


def entry_key(entry: polib.POEntry) -> tuple[str, str]:
    return (entry.msgctxt or "", entry.msgid)


def is_plural(entry: polib.POEntry) -> bool:
    return bool(entry.msgid_plural or entry.msgstr_plural)


def has_translation(entry: polib.POEntry) -> bool:
    if is_plural(entry):
        return bool(entry.msgstr_plural) and any(
            value.strip() for value in entry.msgstr_plural.values()
        )
    return bool(entry.msgstr and entry.msgstr.strip())


def copy_translation(
    target: polib.POEntry, source: polib.POEntry
) -> bool:
    """Copy msgstr from source into target. Return True if target changed."""
    if is_plural(target) or is_plural(source):
        if not source.msgstr_plural:
            return False
        new_plural = dict(source.msgstr_plural)
        if target.msgstr_plural == new_plural:
            return False
        target.msgid_plural = source.msgid_plural or target.msgid_plural
        target.msgstr_plural = new_plural
        target.msgstr = source.msgstr
    else:
        if target.msgstr == source.msgstr:
            return False
        target.msgstr = source.msgstr

    if "fuzzy" in target.flags:
        target.flags.remove("fuzzy")
    return True


def lf_copy(src_path: str, suffix: str) -> tuple[str, bool]:
    """Copy src to a temp file with LF line endings if needed. Return (path, is_temp)."""
    with open(src_path, "rb") as handle:
        data = handle.read()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if normalized == data:
        return src_path, False
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, dir=os.path.dirname(src_path))
    os.close(fd)
    with open(tmp_path, "wb") as handle:
        handle.write(normalized)
    return tmp_path, True


def sync_with_pot(msgmerge: str, po_path: str, pot_path: str) -> polib.POFile:
    """Run msgmerge so the .po matches the backport template."""
    po_input, po_temp = lf_copy(po_path, ".po")
    pot_input, pot_temp = lf_copy(pot_path, ".pot")
    with tempfile.NamedTemporaryFile(
        suffix=".po", delete=False, dir=os.path.dirname(po_path)
    ) as tmp:
        tmp_path = tmp.name

    temp_inputs = [
        path
        for path, is_temp in ((po_input, po_temp), (pot_input, pot_temp))
        if is_temp
    ]
    try:
        result = subprocess.run(
            [
                msgmerge,
                "--no-fuzzy-matching",
                "-o",
                tmp_path,
                po_input,
                pot_input,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return polib.pofile(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        for path in temp_inputs:
            if os.path.exists(path):
                os.remove(path)


def backport_language(
    lang: str,
    *,
    master_po_dir: str,
    backport_po_dir: str,
    pot_path: str,
    msgmerge: str,
    dry_run: bool,
) -> LangStats:
    stats = LangStats()
    backport_po_path = os.path.join(backport_po_dir, lang + ".po")
    master_po_path = os.path.join(master_po_dir, lang + ".po")

    if not os.path.isfile(master_po_path):
        stats.skipped = "no matching master .po"
        return stats

    try:
        backport_po = sync_with_pot(msgmerge, backport_po_path, pot_path)
    except RuntimeError as exc:
        stats.skipped = f"msgmerge failed: {exc}"
        return stats

    stats.synced = True
    master_po = polib.pofile(master_po_path)
    master_map = {
        entry_key(entry): entry
        for entry in master_po
        if not entry.obsolete and entry.msgid
    }

    for entry in backport_po:
        if entry.obsolete or not entry.msgid:
            continue

        master_entry = master_map.get(entry_key(entry))
        if master_entry is None:
            stats.backport_only += 1
            continue

        if not has_translation(master_entry):
            stats.master_untranslated += 1
            continue

        if copy_translation(entry, master_entry):
            stats.updated += 1
        else:
            stats.unchanged += 1

    if not dry_run and stats.updated:
        backport_po.save(backport_po_path)

    return stats


def default_master_dir(backport_po_dir: str) -> str:
    sibling = os.path.normpath(
        os.path.join(os.path.dirname(backport_po_dir), "..", "bleachbit", "po")
    )
    return sibling


def parse_args(argv: list[str]) -> argparse.Namespace:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description=(
            "Copy Weblate translation updates from master into backport .po files "
            "for shared msgids, without dropping backport-only strings."
        )
    )
    parser.add_argument(
        "--master-po-dir",
        default=os.environ.get("BLEACHBIT_MASTER_PO_DIR"),
        help=(
            "Directory containing master-branch .po files "
            "(default: ../bleachbit/po or BLEACHBIT_MASTER_PO_DIR)"
        ),
    )
    parser.add_argument(
        "--backport-po-dir",
        default=script_dir,
        help="Directory containing backport .po files (default: this script's directory)",
    )
    parser.add_argument(
        "--pot",
        default="bleachbit.pot",
        help="Backport template filename inside --backport-po-dir (default: bleachbit.pot)",
    )
    parser.add_argument(
        "--lang",
        action="append",
        dest="langs",
        metavar="CODE",
        help="Process only this language (repeatable). Default: all backport .po files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing .po files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    backport_po_dir = os.path.abspath(args.backport_po_dir)
    master_po_dir = args.master_po_dir
    if not master_po_dir:
        master_po_dir = default_master_dir(backport_po_dir)
    master_po_dir = os.path.abspath(master_po_dir)

    pot_path = os.path.join(backport_po_dir, args.pot)
    if not os.path.isfile(pot_path):
        print(f"error: pot file not found: {pot_path}", file=sys.stderr)
        return 1
    if not os.path.isdir(master_po_dir):
        print(f"error: master po directory not found: {master_po_dir}", file=sys.stderr)
        return 1

    try:
        msgmerge = find_gettext_tool("msgmerge")
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.langs:
        languages = args.langs
    else:
        languages = sorted(
            os.path.splitext(name)[0]
            for name in os.listdir(backport_po_dir)
            if name.endswith(".po")
        )

    print(f"Master .po source: {master_po_dir}")
    print(f"Backport .po dir:  {backport_po_dir}")
    print(f"Backport template: {pot_path}")
    if args.dry_run:
        print("Dry run: no files will be modified.")
    print()

    summary = Summary()
    total_updated = 0

    for lang in languages:
        stats = backport_language(
            lang,
            master_po_dir=master_po_dir,
            backport_po_dir=backport_po_dir,
            pot_path=pot_path,
            msgmerge=msgmerge,
            dry_run=args.dry_run,
        )
        summary.languages[lang] = stats

        if stats.skipped:
            print(f"{lang}: skipped ({stats.skipped})")
            continue

        total_updated += stats.updated
        print(
            f"{lang}: updated {stats.updated}, unchanged {stats.unchanged}, "
            f"backport-only {stats.backport_only}, "
            f"master untranslated {stats.master_untranslated}"
        )

    print()
    if args.dry_run:
        print(f"Would update {total_updated} translated strings across all languages.")
    else:
        print(f"Updated {total_updated} translated strings across all languages.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
