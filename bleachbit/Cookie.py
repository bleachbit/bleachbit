# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Cookie module for selective deletion of cookies
"""

import contextlib
import logging
import os
import sqlite3

from bleachbit import FileUtilities
from bleachbit.Special import sqlite_table_exists

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
        if os.path.exists(candidate):
            try:
                total += FileUtilities.getsize(candidate)
            except OSError as exc:
                logger.debug('Failed to get size for %s: %s', candidate, exc)
    return total


def _checkpoint_wal(conn, path):
    """Checkpoint and truncate WAL to keep disk footprint accurate."""
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
    (table_name, host_column) = detect_browser(path)
    uri = f'file:{path}'
    with contextlib.closing(sqlite3.connect(uri, uri=bool(uri.startswith('file:')))) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT distinct {host_column} FROM {table_name}")
        return cursor.fetchall()


def delete_cookies(path, keep_list, really_delete=False):
    """Process cookies with optional deletion based on allowlist

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

    # Find the first matching table configuration
    (table_name, host_column) = detect_browser(path)

    original_size = _get_db_disk_size(path)
    assert original_size > 0

    # Set up connection
    uri = f'file:{path}'
    if not really_delete:
        uri += '?mode=ro'

    from bleachbit.Options import options
    shred_enabled = options.get('shred')

    try:
        with contextlib.closing(sqlite3.connect(uri, uri=bool(uri.startswith('file:')))) as conn:
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
                    logger.warning(f"VACUUM failed on {path}: {e}")
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
        logger.error(f"SQLite error processing {path}: {e}")
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

    cookie_files = set()
    # Import here to avoid a circular import.
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
