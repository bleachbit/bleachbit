# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Integration specific to macOS
"""

import errno
import logging
import os
import platform
import plistlib
import re
import shlex
import subprocess
import xml.parsers.expat
from pathlib import Path

from bleachbit import APP_NAME, FileUtilities, IS_MAC
from bleachbit.Language import normalize_locale_code

logger = logging.getLogger(__name__)

# Shared between the Safari BinaryCookies reader and writer, so the
# reader can validate that a page's structure actually matches what
# the writer (and real Safari) produces before trusting cookie_count.
SAFARI_PAGE_MARKER = b"\x00\x00\x01\x00"
SAFARI_END_OF_TABLE_MARKER = b"\x00\x00\x00\x00"

# macOS 10.0-10.15 (Cheetah..Catalina) used '10.x' with the release
# identified by the SECOND component (the old scheme this dict was
# originally written for). Since macOS 11 (Big Sur), Apple dropped
# the '10.' prefix and the release is identified by the FIRST
# component instead (11, 12, ..., 26); using split('.')[1] against a
# modern version string reads the minor/patch number instead of the
# release identifier, so e.g. '26.6.2' incorrectly looked up '6' and
# showed 'Snow Leopard'. Two separate dicts, keyed by the field that
# actually identifies the release in each scheme.
MACOSX_DICT_LEGACY = {
    '5': 'Leopard',
    '6': 'Snow Leopard',
    '7': 'Lion',
    '8': 'Mountain Lion',
    '9': 'Mavericks',
    '10': 'Yosemite',
    '11': 'El Capitan',
    '12': 'Sierra',
    '13': 'High Sierra',
    '14': 'Mojave',
    '15': 'Catalina',
}
MACOSX_DICT_MODERN = {
    '11': 'Big Sur',
    '12': 'Monterey',
    '13': 'Ventura',
    '14': 'Sonoma',
    '15': 'Sequoia',
    '26': 'Tahoe',
}


def _read_global_preferences_plist():
    """Return the parsed contents of ~/Library/Preferences/
    .GlobalPreferences.plist as a dict, or None if it cannot be read
    or does not parse to a dictionary."""
    path = os.path.expanduser(
        '~/Library/Preferences/.GlobalPreferences.plist')
    try:
        with open(path, 'rb') as f:
            data = plistlib.load(f)
            if isinstance(data, dict):
                return data
            logger.debug('unexpected non-dict root in %s: %r',
                         path, type(data))
            return None
    except (OSError, ValueError, xml.parsers.expat.ExpatError) as e:
        logger.debug('failed to read %s: %s', path, e)
        return None


def _get_apple_locale_via_defaults():
    """Return AppleLocale by shelling out to `defaults read -g
    AppleLocale`, or None on any failure.

    This is the fallback path: reliable when tested from a terminal,
    but observed to consistently fail (falling through to the 'C'
    locale) when the app is launched via an actual Finder double-click
    rather than a terminal or `open` -- `_read_global_preferences_plist`
    above does not depend on spawning a subprocess at all, so it is
    unaffected by whatever session/TCC context differs between those
    two launch paths, and is tried first.
    """
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleLocale'],
            capture_output=True, text=True, timeout=2, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        # SubprocessError covers TimeoutExpired, which is not an OSError.
        logger.debug('failed to read AppleLocale: %s', e)
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def get_macos_locale():
    """Return the user's preferred locale on macOS, e.g. 'es_ES'.

    On macOS, locale.getlocale() reflects POSIX environment variables
    (LANG/LC_ALL), which are not set when the app is launched from
    Finder (as opposed to a terminal) and can be stale or inconsistent
    with the user's actual System Settings > General > Language & Region
    preference. AppleLocale reflects the real system preference
    regardless of how the app was launched.

    Prefer reading AppleLocale directly from .GlobalPreferences.plist
    (pure file I/O, no subprocess); if AppleLocale is absent from the
    plist, fall back to the first entry of AppleLanguages in the same
    plist, and finally to `defaults read -g AppleLocale` if the plist
    itself cannot be read.
    """
    value = None
    prefs = _read_global_preferences_plist()
    if isinstance(prefs, dict):
        apple_locale = prefs.get('AppleLocale')
        if isinstance(apple_locale, str) and apple_locale:
            value = apple_locale
        else:
            languages = prefs.get('AppleLanguages')
            if isinstance(languages, (list, tuple)) and languages:
                first_lang = languages[0]
                if isinstance(first_lang, str) and first_lang:
                    # AppleLanguages uses hyphens ('es-ES'); AppleLocale and
                    # everywhere else in this codebase use underscores.
                    value = first_lang.replace('-', '_')

    if not value or not isinstance(value, str):
        value = _get_apple_locale_via_defaults()

    if not isinstance(value, str) or not value:
        return None
    # AppleLocale can include a variant suffix like 'es_ES@currency=EUR'.
    value = normalize_locale_code(value)
    return value or None


def notify_macos(msg):
    """Show a pop-up notification on macOS via osascript.

    The macOS GTK stack ships no libnotify typelib, so route the message
    through AppleScript's ``display notification``, which posts it to the
    system Notification Center.
    """
    if not IS_MAC:
        raise RuntimeError("notify_macos() is only for macOS")

    def _escape(text):
        # AppleScript string literals: escape backslash then double quote.
        return text.replace('\\', '\\\\').replace('"', '\\"')

    script = 'display notification "{}" with title "{}"'.format(
        _escape(msg), _escape(APP_NAME))
    # osascript is a signed Apple binary launched as a child of
    # BleachBit's own (unsigned/ad-hoc-signed) bundled Python -- same
    # issue as delete_with_admin_privileges() above: inheriting
    # DYLD_LIBRARY_PATH (set by the bundled Python to find its own
    # packaged libraries) or any other DYLD_* variable trips the
    # kernel's code-signing check (cs_invalid_page) inside a
    # strictly-signed system binary, killing it with SIGKILL.
    # Reproduced against a real /Applications/BleachBit.app on a Mac
    # mini M1 (Apple Silicon, no Rosetta translation involved),
    # confirmed via the unified system log and crash reports
    # (parentProc: BleachBit, termination: CODESIGNING/Invalid Page).
    # Intermittent -- not observed on a Mac mini M4 with the identical
    # app bundle, likely a dyld-internal timing/race rather than
    # anything specific to either machine's files -- but confirmed
    # repeatable across multiple runs and reinstalls on the M1. Give
    # osascript a clean environment instead of silently inheriting
    # BleachBit's, same as the elevated-delete path.
    clean_env = {k: v for k, v in os.environ.items()
                 if not k.startswith('DYLD_')}
    try:
        subprocess.run(['osascript', '-e', script],
                       capture_output=True, timeout=5, check=False,
                       env=clean_env)
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug('osascript notification failed: %s', e)


# Paths that macOS guards with TCC (Transparency, Consent and Control)
# when Full Disk Access is not granted to the calling process. Each is
# TCC-protected and expected to exist on a typical macOS install, so an
# EPERM when scanning one of them is a strong signal that FDA is off.
_FDA_PROBE_PATHS = (
    '~/Library/Safari/',
    '~/Library/Caches/com.apple.Safari/',
    '~/Library/Containers/com.apple.Safari/',
)


def is_full_disk_access_enabled():
    """Detect whether Full Disk Access is enabled on macOS.

    Returns False if a TCC-protected probe path is blocked with EPERM.
    Returns True on non-macOS, when no probe exists, or when accessible.
    """
    if not IS_MAC:
        return True
    for probe in _FDA_PROBE_PATHS:
        path = os.path.expanduser(probe)
        if not os.path.exists(path):
            logger.debug('FDA probe skipped: %s (does not exist)', path)
            continue
        try:
            # Consume the iterator so the scandir() call actually opens
            # the directory and triggers the TCC check.
            list(os.scandir(path))
        except OSError as e:
            if e.errno == errno.EPERM:
                logger.debug('FDA probe blocked: %s', path)
                return False
            # EACCES is a normal Unix mode issue, not a TCC guard.
            # Any other OSError is also not a TCC signal.
            logger.debug('FDA probe skipped %s: %s', path, e)
    return True


def macos_version_name(version=None):
    """Return the marketing/release name for a macOS version string, e.g. 'Tahoe'."""
    if version is None:
        if not hasattr(platform, 'mac_ver'):
            return None
        version = platform.mac_ver()[0]
    if not version:
        return None
    version_parts = version.split('.')
    version_major = version_parts[0]
    name = MACOSX_DICT_MODERN.get(version_major)
    if name is None and version_major == '10' and len(version_parts) > 1:
        name = MACOSX_DICT_LEGACY.get(version_parts[1])
    return name


def _get_cookie_disk_size(path):
    """Return total on-disk footprint for a cookie file."""
    if not os.path.exists(path):
        return 0
    try:
        return FileUtilities.getsize(path)
    except OSError as exc:
        logger.debug('Failed to get size for %s: %s', path, exc)
        return 0


def is_safari_binarycookies(path):
    """Return True if path is a Safari Binary Cookies database."""
    try:
        with open(path, 'rb') as f:
            return f.read(4) == b'cook'
    except OSError:
        return False


def list_safari_cookies(path):
    """List unique cookie domains from a Safari Binary Cookies database."""
    import struct

    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < 8 or data[:4] != b'cook':
        raise ValueError(f"invalid Safari cookies file: {path}")

    # Binary Cookies file header:
    #   4 bytes: magic "cook"
    #   4 bytes: page count (big endian)
    #   4 * page_count: page sizes (big endian)
    page_count = struct.unpack_from(">I", data, 4)[0]

    if page_count == 0:
        return []

    page_table_end = 8 + (page_count * 4)

    if page_table_end > len(data):
        raise ValueError(f"invalid Safari cookies page table: {path}")

    page_sizes = struct.unpack_from(
        f">{page_count}I", data, 8)

    domains = set()
    offset = page_table_end

    for page_size in page_sizes:
        if page_size < 8 or offset + page_size > len(data):
            raise ValueError(f"invalid Safari cookies page size: {path}")

        page = data[offset:offset + page_size]

        # Safari BinaryCookies page header is little endian:
        #   +0: page marker (constant)
        #   +4: cookie count
        #   +8: cookie record offsets
        if page[0:4] != SAFARI_PAGE_MARKER:
            raise ValueError(f"invalid Safari cookies page marker: {path}")

        cookie_count = struct.unpack_from("<I", page, 4)[0]

        offsets_end = 8 + (cookie_count * 4)

        if offsets_end > len(page):
            raise ValueError(f"invalid Safari cookie offsets: {path}")

        if page[offsets_end:offsets_end + 4] != SAFARI_END_OF_TABLE_MARKER:
            raise ValueError(
                f"invalid Safari cookies end-of-table marker: {path}")

        for i in range(cookie_count):
            cookie_offset = struct.unpack_from(
                "<I", page, 8 + (i * 4))[0]

            if cookie_offset + 20 > len(page):
                continue

            cookie_size = struct.unpack_from(
                "<I", page, cookie_offset)[0]

            if cookie_size < 20 or cookie_offset + cookie_size > len(page):
                continue

            # Cookie record:
            #   +0  size
            #   +4  unknown
            #   +8  flags
            #   +12 unknown
            #   +16 domain string offset
            #   +20 name string offset
            #   +24 path string offset
            #   +28 value string offset
            domain_offset = struct.unpack_from(
                "<I", page, cookie_offset + 16)[0]

            domain_pos = cookie_offset + domain_offset

            if domain_pos >= len(page):
                continue

            end = page.find(b'\x00', domain_pos)

            if end == -1:
                continue

            domain = page[domain_pos:end].decode(
                'utf-8', errors='ignore').strip().lower()

            if domain:
                domains.add(domain.lstrip('.'))

        offset += page_size

    return sorted(domains)


def _read_safari_cookie_records(path):
    """Read Safari BinaryCookies and return pages with cookie records."""
    import struct

    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < 8 or data[:4] != b'cook':
        raise ValueError(f"invalid Safari cookies file: {path}")

    page_count = struct.unpack_from(">I", data, 4)[0]
    page_table_end = 8 + (page_count * 4)

    if page_table_end > len(data):
        raise ValueError(f"invalid Safari cookies page table: {path}")

    page_sizes = struct.unpack_from(
        f">{page_count}I", data, 8)

    pages = []
    offset = page_table_end

    for page_size in page_sizes:
        if page_size < 8 or offset + page_size > len(data):
            raise ValueError(f"invalid Safari cookies page size: {path}")

        page = data[offset:offset + page_size]

        # The page marker and end-of-table marker are constants the
        # writer always emits (see safari_pages_to_bytes below); the
        # writer always produces both correctly, so relying only on
        # cookie_count without checking them would silently trust a
        # page that a hand-crafted or corrupted file never actually
        # laid out this way.
        if page[0:4] != SAFARI_PAGE_MARKER:
            raise ValueError(f"invalid Safari cookies page marker: {path}")

        cookie_count = struct.unpack_from("<I", page, 4)[0]
        offsets_end = 8 + (cookie_count * 4)

        if offsets_end > len(page):
            raise ValueError(f"invalid Safari cookie offsets: {path}")

        if page[offsets_end:offsets_end + 4] != SAFARI_END_OF_TABLE_MARKER:
            raise ValueError(
                f"invalid Safari cookies end-of-table marker: {path}")

        records = []

        for i in range(cookie_count):
            cookie_offset = struct.unpack_from(
                "<I", page, 8 + (i * 4))[0]

            if cookie_offset + 20 > len(page):
                continue

            cookie_size = struct.unpack_from(
                "<I", page, cookie_offset)[0]

            if cookie_size < 20:
                continue

            if cookie_offset + cookie_size > len(page):
                continue

            record = page[cookie_offset:cookie_offset + cookie_size]

            domain_offset = struct.unpack_from(
                "<I", record, 16)[0]

            domain_pos = domain_offset

            if domain_pos >= len(record):
                continue

            end = record.find(b'\x00', domain_pos)

            if end == -1:
                continue

            domain = record[domain_pos:end].decode(
                'utf-8', errors='ignore').strip().lower()

            if domain:
                records.append((domain.lstrip('.'), record))

        # Not preserved: the real per-page layout is
        #   +0  4 bytes  page marker constant 0x00000100
        #   +4  4 bytes  cookie count
        #   +8  N*4      offset table
        #   +8+N*4  4    end-of-table marker 0x00000000
        #   ...          cookie records
        # There is no meaningful "unknown" field at +8: on write, the
        # marker and offset table are always regenerated from scratch.
        pages.append({
            "records": records,
        })

        offset += page_size

    return pages


def _serialize_safari_cookie_records(pages):
    """Serialize Safari BinaryCookies pages to bytes.

    Per-page layout (all fields little endian), confirmed against
    independent implementations of the format:
        +0          4 bytes  page marker, constant 0x00000100
        +4          4 bytes  cookie count (N)
        +8          N*4      offset table (absolute, page-relative)
        +8+N*4      4 bytes  end-of-table marker, constant 0x00000000
        +12+N*4     ...      cookie records, back to back

    Note this does NOT store the page's own size inside the page: the
    size of each page is only recorded in the file-level page-size
    table (see the caller), exactly as real Safari-written files do.
    """
    import struct

    output_pages = []

    for page in pages:
        records = page["records"]

        header = bytearray()

        # Page marker (constant, NOT a page-size field).
        header.extend(SAFARI_PAGE_MARKER)

        # Cookie count.
        header.extend(struct.pack("<I", len(records)))

        # Cookie records start right after: marker(4) + count(4) +
        # offset table (4*N) + end-of-table marker (4).
        record_offset = 8 + (len(records) * 4) + 4

        for _, record in records:
            header.extend(struct.pack("<I", record_offset))
            record_offset += len(record)

        # End-of-table marker, required before the first record.
        header.extend(SAFARI_END_OF_TABLE_MARKER)

        for _, record in records:
            header.extend(record)

        output_pages.append(bytes(header))

    data = bytearray()
    data.extend(b'cook')
    data.extend(struct.pack(">I", len(output_pages)))

    for page in output_pages:
        data.extend(struct.pack(">I", len(page)))

    for page in output_pages:
        data.extend(page)

    return bytes(data)


def _write_safari_cookie_records(path, pages):
    """Rewrite a Safari BinaryCookies database with selected records."""
    import tempfile

    data = _serialize_safari_cookie_records(pages)

    directory = str(Path(path).parent)

    fd, temp_path = tempfile.mkstemp(
        prefix=".Cookies.binarycookies.",
        dir=directory
    )

    try:
        with open(fd, 'wb', closefd=True) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass  # best-effort cleanup, original error takes priority
        raise


def _cookie_result(total_deleted, total_kept, skipped, whole_file_deleted,
                   file_size_reduction, method=None, ratio=None, in_memory=None):
    """Build a Safari cookie deletion result dict with a stable schema.

    Every branch returns the same set of keys; estimation fields default
    to None when not applicable (e.g. whole-file delete, error fallback).
    """
    return {
        "total_deleted": total_deleted,
        "total_kept": total_kept,
        "skipped": skipped,
        "whole_file_deleted": whole_file_deleted,
        "file_size_reduction": file_size_reduction,
        "file_size_estimation_method": method,
        "file_size_reduction_ratio": ratio,
        "file_size_reduction_in_memory": in_memory,
    }


def _filter_safari_cookie_records(pages, keep_domains):
    """Split cookie records into kept and deleted sets by domain.

    A record is kept when its domain equals or is a subdomain of any
    domain in keep_domains.

    Returns (new_pages, total_before, kept_count, deleted_count).
    """
    total_before = 0
    kept_count = 0
    deleted_count = 0
    new_pages = []

    for page in pages:
        new_records = []
        for domain, record in page["records"]:
            total_before += 1
            keep = any(
                domain == d or domain.endswith("." + d)
                for d in keep_domains
            )
            if keep:
                kept_count += 1
                new_records.append((domain, record))
            else:
                deleted_count += 1
        new_pages.append({"records": new_records})

    return new_pages, total_before, kept_count, deleted_count


def _preview_safari_cookie_deletion(deleted_count, kept_count, total_before,
                                    original_size):
    """Build a preview result dict without modifying the file."""
    if kept_count == 0:
        return _cookie_result(
            total_deleted=deleted_count,
            total_kept=0,
            skipped=False,
            whole_file_deleted=True,
            file_size_reduction=original_size,
            method="whole_file",
        )

    ratio_estimate = 0
    if total_before > 0:
        ratio_estimate = int((deleted_count / total_before) * original_size)

    return _cookie_result(
        total_deleted=deleted_count,
        total_kept=kept_count,
        skipped=False,
        whole_file_deleted=False,
        file_size_reduction=ratio_estimate,
        method="ratio",
        ratio=ratio_estimate,
    )


def _apply_safari_cookie_deletion(path, new_pages, kept_count, deleted_count,
                                  original_size, shred_enabled):
    """Perform real deletion and return a result dict."""
    if deleted_count == 0:
        return _cookie_result(
            total_deleted=0,
            total_kept=kept_count,
            skipped=False,
            whole_file_deleted=False,
            file_size_reduction=0,
            method="actual",
        )

    if kept_count == 0:
        try:
            FileUtilities.delete(path, shred_enabled)
            return _cookie_result(
                total_deleted=deleted_count,
                total_kept=0,
                skipped=False,
                whole_file_deleted=True,
                file_size_reduction=original_size,
            )
        except OSError as e:
            logger.error(
                "Failed to delete Safari cookie database %s: %s",
                path, e)
            return _cookie_result(
                total_deleted=0,
                total_kept=0,
                skipped=True,
                whole_file_deleted=False,
                file_size_reduction=0,
            )

    try:
        _write_safari_cookie_records(path, new_pages)
    except (OSError, ValueError) as e:
        logger.error(
            "Failed to rewrite Safari cookie database %s: %s",
            path, e)
        return _cookie_result(
            total_deleted=0,
            total_kept=kept_count,
            skipped=True,
            whole_file_deleted=False,
            file_size_reduction=0,
        )

    new_size = _get_cookie_disk_size(path)
    return _cookie_result(
        total_deleted=deleted_count,
        total_kept=kept_count,
        skipped=False,
        whole_file_deleted=False,
        file_size_reduction=max(0, original_size - new_size),
        method="actual",
    )


def delete_safari_cookies(path, keep_list, really_delete=False):
    """Process Safari cookies with optional deletion based on keep list

    Args:
        path (str): Path to the cookies database file
        keep_list (set): Set of hosts to preserve (must not be empty)
        really_delete (bool): If True, perform actual deletion. If False, only preview.

    Returns:
        dict: Results dictionary with deletion statistics

    Raises:
        ValueError: If keep_list is empty
    """
    if not keep_list:
        raise ValueError("keep_list must not be empty")
    assert isinstance(keep_list, set)

    from bleachbit.Options import options
    shred_enabled = options.get('shred')

    original_size = _get_cookie_disk_size(path)
    if original_size <= 0:
        raise RuntimeError(
            f"cookies database is empty: {path}")

    pages = _read_safari_cookie_records(path)
    keep_domains = [str(d).lstrip('.').lower() for d in keep_list]

    new_pages, total_before, kept_count, deleted_count = \
        _filter_safari_cookie_records(pages, keep_domains)

    if not really_delete:
        return _preview_safari_cookie_deletion(
            deleted_count, kept_count, total_before, original_size)

    return _apply_safari_cookie_deletion(
        path, new_pages, kept_count, deleted_count,
        original_size, shred_enabled)


# Deliberately narrow: this only ever allows deleting things inside an
# orphaned app-version folder matching this exact structure (e.g. what
# orphaned_framework_versions() in Unix.py finds under a browser's
# .app bundle). BleachBit's general-purpose protected-path list
# (bleachbit.ProtectedPath) is designed as a safety net for ordinary,
# unprivileged deletion -- it does not cover macOS system paths like
# /System or /Library at all (confirmed by hand: check_protected_path
# returned None for '/System'), so it is not a safe gate on its own
# for a function that deletes with root privileges via `rm -rf`. A
# structural allowlist that this function can only ever touch paths
# of this one specific shape is a much stronger guarantee than trying
# to enumerate everything that must be refused.
_ELEVATED_DELETE_ALLOWED_PATH_RE = re.compile(
    r'^(/Applications/[^/]+\.app/Contents/Frameworks/'
    r'[^/]+\.framework/Versions/[^/]+)(/.*)?$')


def elevated_delete_paths_eligible(paths):
    """Return whether every path in paths matches
    _ELEVATED_DELETE_ALLOWED_PATH_RE, i.e. whether
    delete_with_admin_privileges() would actually accept them.

    Lets a caller (e.g. the GUI) decide whether to offer the
    elevated-retry prompt at all, instead of only finding out it was
    never going to work after the user has already said yes.
    """
    if not paths:
        return True
    return all(
        path and _ELEVATED_DELETE_ALLOWED_PATH_RE.match(path)
        for path in paths)


def delete_with_admin_privileges(paths):
    """Delete the given files/directories using macOS's native
    per-action privilege-elevation prompt (osascript's 'do shell
    script ... with administrator privileges'), the same mechanism
    apps such as OnyX use, instead of requiring the whole application
    to be launched as root.

    Refuses to proceed unless every path matches
    _ELEVATED_DELETE_ALLOWED_PATH_RE -- see the comment above it for
    why BleachBit's general-purpose protected-path list is not a safe
    enough gate here on its own.

    Returns True if the deletion succeeded, False if any path was
    rejected, the user canceled the privilege prompt (osascript exits
    non-zero with 'User canceled.' / '(-128)' in stderr), or the
    deletion itself failed for any other reason.
    """
    if not paths:
        return True

    # A single orphaned version folder can contain hundreds of
    # individual files, each reported as its own failed path -- rm -rf
    # on every one of those individually (rather than once on the
    # shared parent folder) risks building a shell command longer than
    # the operating system allows for a single process invocation.
    # Collapse to the unique '.../Versions/<version>' root(s) instead;
    # rm -rf on the folder itself removes everything inside in one
    # shot, and doubles as the same allowlist check as before.
    version_dirs = set()
    for path in paths:
        match = _ELEVATED_DELETE_ALLOWED_PATH_RE.match(path) if path else None
        if not match:
            logger.error(
                'refusing elevated delete of path outside the allowed '
                'orphaned-app-version pattern: %r', path)
            return False
        version_dirs.add(match.group(1))

    shell_cmd = 'rm -rf -- ' + \
        ' '.join(shlex.quote(p) for p in sorted(version_dirs))
    # Escape for embedding inside an AppleScript double-quoted string
    # literal -- a separate escaping step from shlex.quote's
    # shell-level escaping above, since the whole shell_cmd string is
    # itself embedded inside an outer AppleScript string.
    applescript_cmd = shell_cmd.replace('\\', '\\\\').replace('"', '\\"')
    script = 'do shell script "%s" with administrator privileges' % applescript_cmd

    # osascript is a signed Apple binary launched as a child of
    # BleachBit's own (unsigned/ad-hoc-signed) bundled Python. If it
    # inherits DYLD_LIBRARY_PATH (set by the bundled Python to find its
    # own packaged libraries) or any other DYLD_* variable, the
    # dynamic linker's attempt to honor it inside a strictly-signed
    # system binary trips the kernel's code-signing check
    # (cs_invalid_page), which kills the process with SIGKILL before
    # it produces any output -- reproduced against a real
    # /Applications/BleachBit.app launched from Finder (returncode -9,
    # empty stdout/stderr). Give osascript a clean environment instead
    # of silently inheriting BleachBit's.
    clean_env = {k: v for k, v in os.environ.items()
                 if not k.startswith('DYLD_')}

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=120, check=False,
            env=clean_env)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        logger.debug('failed to run osascript for elevated delete: %s', e)
        return False

    if result.returncode != 0:
        logger.debug('elevated delete failed or was canceled: %s',
                     result.stderr.strip())
        return False
    return True
