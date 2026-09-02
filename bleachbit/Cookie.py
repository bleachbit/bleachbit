# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Cookie module for selective deletion of cookies
"""

import contextlib
import json
import logging
import os
from pathlib import Path

import bleachbit
from bleachbit import FileUtilities
from bleachbit.Special import sqlite_table_exists, _sqlite_uri

logger = logging.getLogger(__name__)

COOKIE_KEEP_LIST_FILENAME = "cookie_keep_list.json"


def _estimate_in_memory_size(conn, table_name, delete_query, params):
    """Return estimated database size (bytes) after deleting rows in-memory.

    Args:
        conn: SQLite database connection
        table_name (str): Name of the table being modified
        delete_query (str): SQL DELETE query to execute
        params (tuple): Parameters for the DELETE query

    Returns:
        int or None: Estimated size in bytes after deletion, or None if estimation fails
    """
    mem_conn = None
    try:
        # In FreeBSD, sqlite3 is a separate package
        # pylint: disable=import-outside-toplevel
        import sqlite3
        mem_conn = sqlite3.connect(':memory:')
        conn.backup(mem_conn)
        mem_cursor = mem_conn.cursor()
        mem_cursor.execute(delete_query, params)
        mem_conn.commit()

        mem_conn.isolation_level = None
        mem_cursor.execute('VACUUM')
        page_count = mem_cursor.execute('PRAGMA page_count').fetchone()[0]
        page_size = mem_cursor.execute('PRAGMA page_size').fetchone()[0]
        return page_count * page_size
    except sqlite3.Error as exc:
        logger.debug(
            'In-memory size estimation failed for %s: %s', table_name, exc)
        return None
    finally:
        if mem_conn:
            mem_conn.close()


def _get_db_disk_size(path):
    """Return total on-disk footprint for a SQLite DB, including WAL/SHM."""
    total = 0
    for suffix in ('', '-wal', '-shm'):
        candidate = f"{path}{suffix}"
        if not os.path.exists(candidate):
            continue
        try:
            total += FileUtilities.getsize(candidate)
        except OSError as exc:
            logger.debug('Failed to get size for %s: %s', candidate, exc)
    return total


def _checkpoint_wal(conn, path):
    """Checkpoint and truncate WAL to keep disk footprint accurate."""
    import sqlite3  # pylint: disable=import-outside-toplevel
    prev_isolation = conn.isolation_level
    try:
        conn.isolation_level = None
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    except sqlite3.Error as exc:
        logger.debug('WAL checkpoint failed for %s: %s', path, exc)
    finally:
        conn.isolation_level = prev_isolation


def _delete_auxiliary_journal_files(path, shred_enabled):
    """Delete SQLite auxiliary files (-wal/-shm) if present."""
    for suffix in ('-wal', '-shm'):
        candidate = f"{path}{suffix}"
        if not os.path.exists(candidate):
            continue
        try:
            FileUtilities.delete(candidate, shred_enabled)
        except OSError as exc:
            logger.debug('Failed to delete %s: %s', candidate, exc)


# SQLite table configurations for different cookie databases
SQLITE_TABLES = {
    'moz_cookies': {
        'table_name': 'moz_cookies',
        'host_column': 'host'
    },
    'cookies': {
        'table_name': 'cookies',
        'host_column': 'host_key'
    }
}



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
        #   +0: page size
        #   +4: cookie count
        #   +8: cookie record offsets
        cookie_count = struct.unpack_from("<I", page, 4)[0]

        offsets_end = 8 + (cookie_count * 4)

        if offsets_end > len(page):
            raise ValueError(f"invalid Safari cookie offsets: {path}")

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

        cookie_count = struct.unpack_from("<I", page, 4)[0]
        offsets_end = 8 + (cookie_count * 4)

        if offsets_end > len(page):
            raise ValueError(f"invalid Safari cookie offsets: {path}")

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

    PAGE_MARKER = b"\x00\x01\x00\x00"   # 0x00000100 little endian
    END_OF_TABLE_MARKER = b"\x00\x00\x00\x00"

    output_pages = []

    for page in pages:
        records = page["records"]

        header = bytearray()

        # Page marker (constant, NOT a page-size field).
        header.extend(PAGE_MARKER)

        # Cookie count.
        header.extend(struct.pack("<I", len(records)))

        # Cookie records start right after: marker(4) + count(4) +
        # offset table (4*N) + end-of-table marker (4).
        record_offset = 8 + (len(records) * 4) + 4

        for _, record in records:
            header.extend(struct.pack("<I", record_offset))
            record_offset += len(record)

        # End-of-table marker, required before the first record.
        header.extend(END_OF_TABLE_MARKER)

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
            pass
        raise

def detect_browser(path):
    """Detect the browser type based on the cookies database file"""
    if not os.path.exists(path):
        raise ValueError(f"cookies file not found: {path}")
    for table_config in SQLITE_TABLES.values():
        if sqlite_table_exists(path, table_config['table_name']):
            return table_config['table_name'], table_config['host_column']
    raise ValueError(f"invalid cookies file: {path}")


def list_cookies(path):
    """List cookies in the database"""
    if is_safari_binarycookies(path):
        return [(domain,) for domain in list_safari_cookies(path)]

    import sqlite3  # pylint: disable=import-outside-toplevel
    (table_name, host_column) = detect_browser(path)
    uri = _sqlite_uri(path)
    with contextlib.closing(sqlite3.connect(uri, uri=True)) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT distinct {host_column} FROM {table_name}")
        return cursor.fetchall()


def load_keep_list():
    """Load cookie domains to keep from options directory.

    This does not swallow file permission error or JSON parsing errors:
    when cleaning, these cases should not be treated equally to an empty
    keep list.
    """
    path = os.path.join(bleachbit.options_dir, COOKIE_KEEP_LIST_FILENAME)
    domains = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return domains

    if isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item:
                domains.add(item.lstrip('.').lower())
    return domains


def delete_cookies(path, keep_list, really_delete=False):
    """Process cookies with optional deletion based on keep list

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

    if is_safari_binarycookies(path):
        original_size = _get_db_disk_size(path)

        if original_size <= 0:
            raise RuntimeError(
                f"cookies database is empty: {path}")

        pages = _read_safari_cookie_records(path)

        domains = [
            str(d).lstrip('.').lower()
            for d in keep_list
        ]

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
                    for d in domains
                )

                if keep:
                    kept_count += 1
                    new_records.append((domain, record))
                else:
                    deleted_count += 1

            new_pages.append({
                "records": new_records,
            })

        # Preview
        if not really_delete:
            if kept_count == 0:
                return {
                    "total_deleted": deleted_count,
                    "total_kept": 0,
                    "skipped": False,
                    "whole_file_deleted": True,
                    "file_size_reduction": original_size,
                    "file_size_estimation_method": "whole_file",
                    "file_size_reduction_ratio": None,
                    "file_size_reduction_in_memory": None,
                }

            ratio_estimate = 0

            if total_before > 0:
                ratio_estimate = int(
                    (deleted_count / total_before) * original_size
                )

            return {
                "total_deleted": deleted_count,
                "total_kept": kept_count,
                "skipped": False,
                "whole_file_deleted": False,
                "file_size_reduction": ratio_estimate,
                "file_size_estimation_method": "ratio",
                "file_size_reduction_ratio": ratio_estimate,
                "file_size_reduction_in_memory": None,
            }

        # Real deletion
        if deleted_count == 0:
            return {
                "total_deleted": 0,
                "total_kept": kept_count,
                "skipped": False,
                "whole_file_deleted": False,
                "file_size_reduction": 0,
                "file_size_estimation_method": "actual",
                "file_size_reduction_ratio": None,
                "file_size_reduction_in_memory": None,
            }

        if kept_count == 0:
            try:
                FileUtilities.delete(path, shred_enabled)

                return {
                    "total_deleted": deleted_count,
                    "total_kept": 0,
                    "skipped": False,
                    "whole_file_deleted": True,
                    "file_size_reduction": original_size,
                }

            except OSError as e:
                logger.error(
                    "Failed to delete Safari cookie database %s: %s",
                    path, e)

                return {
                    "total_deleted": 0,
                    "total_kept": 0,
                    "skipped": True,
                    "whole_file_deleted": False,
                    "file_size_reduction": 0,
                }

        try:
            _write_safari_cookie_records(path, new_pages)

        except (OSError, ValueError) as e:
            logger.error(
                "Failed to rewrite Safari cookie database %s: %s",
                path, e)

            return {
                "total_deleted": 0,
                "total_kept": kept_count,
                "skipped": True,
                "whole_file_deleted": False,
                "file_size_reduction": 0,
            }

        new_size = _get_db_disk_size(path)

        return {
            "total_deleted": deleted_count,
            "total_kept": kept_count,
            "skipped": False,
            "whole_file_deleted": False,
            "file_size_reduction": max(
                0, original_size - new_size),
            "file_size_estimation_method": "actual",
            "file_size_reduction_ratio": None,
            "file_size_reduction_in_memory": None,
        }

    import sqlite3  # pylint: disable=import-outside-toplevel
    # Find the first matching table configuration
    (table_name, host_column) = detect_browser(path)

    original_size = _get_db_disk_size(path)
    if original_size <= 0:
        raise RuntimeError(f"cookies database is empty: {path}")

    # Set up connection. Preview opens read-only; the percent-encoded URI
    # keeps a '?' in the path from defeating the mode.
    uri = _sqlite_uri(path, None if really_delete else 'ro')

    try:
        with contextlib.closing(sqlite3.connect(uri, uri=True)) as conn:
            cursor = conn.cursor()
            if shred_enabled:
                cursor.execute('PRAGMA secure_delete = ON;')

            # Get total count
            total_before = cursor.execute(
                f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            # Build predicate for domain-level keep semantics
            # Match exact domain and any subdomain (both Firefox and Chromium)
            domains = [str(d).lstrip('.').lower() for d in keep_list]
            or_clauses = []
            params = []
            for d in domains:
                or_clauses.append(f"{host_column} = ?")
                params.append(d)
                or_clauses.append(f"{host_column} LIKE ?")
                params.append(f"%.{d}")
            keep_predicate = '(' + ' OR '.join(or_clauses) + ')'

            # Count cookies that will be kept
            kept_count = cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {keep_predicate}",
                tuple(params)
            ).fetchone()[0]

            deleted_count = total_before - kept_count
            delete_query = f"DELETE FROM {table_name} WHERE NOT {keep_predicate}"

            ratio_estimate = 0

            if really_delete and deleted_count > 0:
                if kept_count == 0:
                    # No cookies are being kept: delete the whole database file
                    conn.close()
                    if shred_enabled:
                        _delete_auxiliary_journal_files(path, True)
                    try:
                        FileUtilities.delete(path, shred_enabled)
                        return {
                            "total_deleted": deleted_count,
                            "total_kept": 0,
                            "skipped": False,
                            "whole_file_deleted": True,
                            "file_size_reduction": original_size,
                        }
                    except OSError as e:
                        logger.error(
                            "Failed to delete cookie database %s: %s", path, e)
                        return {
                            "total_deleted": 0,
                            "total_kept": 0,
                            "skipped": True,
                            "whole_file_deleted": False,
                            "file_size_reduction": 0,
                        }

                # Perform actual deletion: delete anything NOT matching keep predicate
                cursor.execute(delete_query, tuple(params))
                # Commit deletion before VACUUM
                conn.commit()
                # Run VACUUM in autocommit mode to avoid 'cannot VACUUM from within a transaction'
                prev_isolation = conn.isolation_level
                try:
                    conn.isolation_level = None
                    cursor.execute('VACUUM')
                except sqlite3.Error as e:
                    logger.warning("VACUUM failed on %s: %s", path, e)
                finally:
                    conn.isolation_level = prev_isolation
                if shred_enabled:
                    _checkpoint_wal(conn, path)
                    conn.close()
                    _delete_auxiliary_journal_files(path, True)
                new_size = _get_db_disk_size(path)
                size_reduction = original_size - new_size
                estimation_method = 'actual'
                ratio_estimate = None
                memory_estimate = None
            else:
                # Preview mode or nothing to delete
                if kept_count == 0:
                    # No cookies being kept: entire file would be deleted
                    size_reduction = original_size
                    estimation_method = 'whole_file'
                    ratio_estimate = None
                    memory_estimate = None
                else:
                    if total_before > 0:
                        ratio_estimate = int(
                            (deleted_count / total_before) * original_size)
                    memory_estimate = None
                    if deleted_count > 0 and shred_enabled:
                        # In-memory method is accurate when shredding is enabled
                        memory_size = _estimate_in_memory_size(
                            conn, table_name, delete_query, tuple(params))
                        if memory_size is not None:
                            memory_estimate = max(
                                0, original_size - memory_size)

                    if memory_estimate is not None:
                        size_reduction = memory_estimate
                        estimation_method = 'in_memory'
                    else:
                        size_reduction = ratio_estimate
                        estimation_method = 'ratio'

            return {
                "total_deleted": deleted_count,
                "total_kept": kept_count,
                "skipped": False,
                "whole_file_deleted": False,
                "file_size_reduction": size_reduction,
                "file_size_estimation_method": estimation_method,
                "file_size_reduction_ratio": ratio_estimate,
                "file_size_reduction_in_memory": memory_estimate,
            }

    except sqlite3.Error as e:
        logger.error("SQLite error processing %s: %s", path, e)
        return {
            "total_deleted": 0,
            "total_kept": 0,
            "skipped": True,
            "whole_file_deleted": False,
            "file_size_reduction": 0,
        }


def list_unique_cookies():
    """Return unique cookie hostnames across all cleaners with cookie actions.

    Iterates through every registered cleaner, locates actions whose
    ``command="cookie"`` and aggregates the existing cookie database files
    they target.  Each database is opened using :func:`list_cookies`, and the
    distinct host entries are returned as a sorted list.

    Returns:
        list[str]: Sorted, de-duplicated list of cookie host strings.
    """

    import sqlite3  # pylint: disable=import-outside-toplevel
    cookie_files = set()
    # Import backends here to avoid a circular import.
    from bleachbit.Cleaner import backends as cleaner_backends
    for cleaner in cleaner_backends.values():
        actions = getattr(cleaner, 'actions', ())
        for option_id, action in actions:
            if getattr(action, 'action_key', None) != 'cookie':
                continue
            try:
                paths = list(action.get_paths())
            except (OSError, RuntimeError) as exc:
                logger.debug('Unable to enumerate cookie paths for %s.%s: %s',
                             cleaner.get_id(), option_id, exc)
                continue
            for path in paths:
                if path and os.path.isfile(path):
                    cookie_files.add(path)

    unique_hosts = set()
    for path in cookie_files:
        try:
            rows = list_cookies(path)
        except (ValueError, sqlite3.Error, OSError) as exc:
            logger.debug('Skipping cookie database %s: %s', path, exc)
            continue
        for row in rows:
            host = row[0] if isinstance(row, (list, tuple)) else row
            if host:
                unique_hosts.add(str(host))

    return sorted(unique_hosts)
