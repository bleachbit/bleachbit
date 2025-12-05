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
Test case for module Cookie
"""

import hashlib
import os
import sqlite3
import tempfile
import unittest
import shutil

from bleachbit import Cookie
from bleachbit.Options import options
from bleachbit.FileUtilities import execute_sqlite3
from tests import common


DEFAULT_COOKIE_FIXTURES = (
    ('example.com', 'session_id'),
    ('google.com', 'pref'),
    ('github.com', 'auth'),
)

DOMAIN_MATCHING_CASES = (
    ('example.com', 'example.com', True, 'Exact host match'),
    ('example.com', '.example.com', True,
     'Domain cookie canonicalizes to base host'),
    ('example.com', 'shop.example.com', True,
     'Subdomain should be preserved when base is allowlisted'),
    ('example.com', '.shop.example.com', True,
     'Firefox/Chromium store domain cookies with dots'),
    ('example.com', 'thisisanexample.com', False,
     'Substring matches must not count'),
    ('example.com', 'example.com.attacker.net', False,
     'Extra label to the right is a different domain'),
    ('example.com', 'shop-example.com', False,
     'Hyphenated host is unrelated'),
    ('www.example.com', 'example.com', False,
     'Host-only cookies should not match parent domain'),
    ('.example.com', 'example.com', True,
     'Leading dots in allowlist should be ignored'),
    ('.example.com', 'www.example.com', True,
     'Leading dots in allowlist should match subdomains'),
    ('.example.com', 'fooexample.com', False,
     'Canonical registrable domain mismatch'),
)


# Additional coverage:
# - Non-SQLite file with non-empty keep list should not be deleted (raises ValueError)
# - SQLite DB with unknown table and non-empty keep list should not be deleted (raises ValueError)
# - When no hosts match keep list, all rows are deleted and the database file is removed

class CookieTestCase(common.BleachbitTestCase):
    """Test cases for Cookie module"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self._original_shred = options.get('shred')
        options.set('shred', True)

    def tearDown(self):
        """Clean up test fixtures"""
        options.set('shred', self._original_shred)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()

    def _get_file_hash(self, filepath):
        """Calculate SHA-256 hash of a file"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).digest()

    def _sample_cookies(self, dotted=False):
        """Return a reusable copy of the default cookie fixtures"""
        cookies = DEFAULT_COOKIE_FIXTURES
        if dotted:
            return [
                (host if host.startswith('.') else f'.{host}', name)
                for host, name in cookies
            ]
        return [(host, name) for host, name in cookies]

    def _create_chrome_cookies_db(self, cookies=None):
        """Create a Chrome cookies database for testing

        Args:
            cookies: Iterable of (host_key, name) tuples. If None, uses
                default test cookies.

        Returns:
            str: Path to the created cookies database
        """
        if cookies is None:
            cookies = self._sample_cookies()

        path = os.path.join(self.temp_dir, 'chrome_cookies.db')
        if os.path.exists(path):
            os.unlink(path)
        sql = '''
            CREATE TABLE cookies (
                host_key TEXT NOT NULL,
                name TEXT NOT NULL
            )
        '''
        execute_sqlite3(path, sql)

        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            for host_key, name in cookies:
                cursor.execute(
                    'INSERT INTO cookies (host_key, name) VALUES (?, ?)',
                    (host_key, name),
                )
            conn.commit()
        finally:
            conn.close()

        return path

    def _find_live_firefox_cookies_file(self):
        """Return path to a real Firefox cookies.sqlite if one exists"""
        search_roots = [
            os.path.expanduser('~/snap/firefox/common/.mozilla/firefox'),
            os.path.expanduser('~/.mozilla/firefox'),
        ]
        appdata = os.environ.get('APPDATA')
        if appdata:
            search_roots.append(os.path.join(
                appdata, 'Mozilla', 'Firefox', 'Profiles'))

        for root in search_roots:
            if not root or not os.path.isdir(root):
                continue
            for dirpath, _dirnames, filenames in os.walk(root):
                if 'cookies.sqlite' in filenames:
                    return os.path.join(dirpath, 'cookies.sqlite')
        return None

    def _create_firefox_cookies_db(self, cookies=None):
        """Create a Firefox cookies database for testing

        Args:
            cookies: Iterable of cookie descriptors. Accepts:
                     * plain host strings
                     * (host, name) tuples
                     If None, uses default test cookies.

        Returns:
            str: Path to the created cookies database
        """
        if cookies is None:
            cookies = self._sample_cookies(dotted=True)

        path = os.path.join(self.temp_dir, 'firefox_cookies.db')
        if os.path.exists(path):
            os.unlink(path)
        sql = '''
            CREATE TABLE moz_cookies (
                id INTEGER PRIMARY KEY,
                host TEXT NOT NULL,
                name TEXT NOT NULL,
                CONSTRAINT moz_uniqueid UNIQUE (host, name)
            )
        '''
        execute_sqlite3(path, sql)

        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            for cookie in cookies:
                host = name = None
                if isinstance(cookie, str):
                    host, name = cookie, ''
                elif isinstance(cookie, (list, tuple)):
                    if len(cookie) >= 2:
                        host, name = cookie[:2]
                    elif len(cookie) == 1:
                        host, name = cookie[0], ''
                if host is None:
                    raise ValueError(
                        'Unsupported cookie format for Firefox test fixture')
                cursor.execute(
                    'INSERT INTO moz_cookies (host, name) VALUES (?, ?)', (host, name))
            conn.commit()
        finally:
            conn.close()

        return path

    def test_delete_cookie_value_error(self):
        """Empty allowlist should raise ValueError (API requires non-empty set)"""
        path = self._create_chrome_cookies_db()

        # Get file hash before operation
        original_hash = self._get_file_hash(path)

        # Test scenarios that should raise ValueError
        scenarios = [
            # Scenario 1: Empty allowlist
            (set(), "Empty allowlist should raise ValueError"),
            # Scenario 2: None allowlist
            (None, "None allowlist should raise ValueError"),
        ]

        for keep_list, description in scenarios:
            with self.subTest(description=description):
                with self.assertRaises(ValueError):
                    Cookie.delete_cookies(path, keep_list, really_delete=True)
                self.assertExists(path)
                new_hash = self._get_file_hash(path)
                self.assertEqual(original_hash, new_hash,
                                 'Database file was modified')

    def test_delete_cookie_bad_file(self):
        """Empty allowlist should raise ValueError (API requires non-empty set)"""
        path_missing = os.path.join(self.temp_dir, 'nonexistent.db')
        path_non_sqlite = os.path.join(self.temp_dir, 'not_sqlite.txt')
        path_wrong_sqlite = os.path.join(self.temp_dir, 'wrong_sqlite.db')

        with open(path_non_sqlite, 'w', encoding='utf-8') as f:
            f.write('not a database')

        execute_sqlite3(
            path_wrong_sqlite, "CREATE TABLE not_browser_related (id INTEGER PRIMARY KEY)")

        scenarios = [
            (path_missing, "Non-existent file", ValueError),
            (path_non_sqlite, "Non-SQLite file", sqlite3.DatabaseError),
            (path_wrong_sqlite, "SQLite file with wrong table", ValueError),
        ]

        for test_path, description, expected_exception in scenarios:
            with self.subTest(description=description):
                original_hash = None
                if not test_path == path_missing:
                    original_hash = self._get_file_hash(test_path)
                with self.assertRaises(expected_exception):
                    Cookie.delete_cookies(
                        test_path, {'example.com'}, really_delete=True)

                if test_path == path_missing:
                    self.assertNotExists(test_path)
                else:
                    self.assertExists(test_path)
                    new_hash = self._get_file_hash(test_path)
                    self.assertEqual(original_hash, new_hash,
                                     'Database file was modified')

    def test_delete_cookies_chrome_with_allowlist(self):
        """Test selectively deleting Chrome cookies with allowlist"""
        path = self._create_chrome_cookies_db()

        # Test deletion with allowlist (keep google.com)
        keep_list = ['google.com']
        result = Cookie.delete_cookies(
            path, set(keep_list), really_delete=True)

        # example.com and github.com deleted
        self.assertEqual(result['total_deleted'], 2)
        self.assertEqual(result['total_kept'], 1)    # google.com kept
        self.assertFalse(result['skipped'])
        self.assertFalse(result['whole_file_deleted'])
        self.assertGreaterEqual(result['file_size_reduction'], 0)

    def test_non_sqlite_file_with_allowlist_raises(self):
        """Non-SQLite file should raise ValueError and not be deleted"""
        # First create a valid cookies db to get the path format right
        path = self._create_chrome_cookies_db()
        # Now remove it and create a non-sqlite file
        os.unlink(path)
        path = os.path.join(self.temp_dir, 'not_sqlite.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('not a database')

        with self.assertRaises(sqlite3.DatabaseError):
            Cookie.delete_cookies(path, {'example.com'}, really_delete=True)

        self.assertTrue(os.path.exists(path))

    def test_sqlite_unknown_table_with_allowlist_raises(self):
        """SQLite DB without known cookies table should raise ValueError"""
        path = os.path.join(self.temp_dir, 'unknown_table.db')
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            'CREATE TABLE something_else (id INTEGER PRIMARY KEY, host TEXT)')
        conn.commit()
        conn.close()

        with self.assertRaises(ValueError):
            Cookie.delete_cookies(path, {'example.com'}, really_delete=True)

        self.assertTrue(os.path.exists(path))

    def test_delete_cookies_when_no_hosts_match_kept(self):
        """If no hosts match keep list, all rows are deleted and file is removed"""
        path = self._create_chrome_cookies_db()

        result = Cookie.delete_cookies(
            path, {'no-such-host.example'}, really_delete=True)

        self.assertEqual(result['total_kept'], 0)
        self.assertEqual(result['total_deleted'], 3)
        self.assertFalse(result['skipped'])
        self.assertTrue(result['whole_file_deleted'])
        self.assertGreaterEqual(result['file_size_reduction'], 0)

        # Verify database file was removed
        self.assertFalse(os.path.exists(path))

    def test_delete_cookies_firefox_with_allowlist(self):
        """Test selectively deleting Firefox cookies with allowlist"""
        path = self._create_firefox_cookies_db()

        # Test deletion with whitelist (keep google.com)
        keep_list = ['google.com']
        result = Cookie.delete_cookies(
            path, set(keep_list), really_delete=True)

        # example.com and github.com deleted
        self.assertEqual(result['total_deleted'], 2)
        self.assertEqual(result['total_kept'], 1)    # google.com kept
        self.assertFalse(result['skipped'])
        self.assertFalse(result['whole_file_deleted'])
        self.assertGreaterEqual(result['file_size_reduction'], 0)

        # Verify the database still exists and has the right cookies
        self.assertTrue(os.path.exists(path))

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        remaining_cookies = cursor.execute(
            'SELECT host FROM moz_cookies').fetchall()
        conn.close()

        self.assertEqual(len(remaining_cookies), 1)
        # Firefox stores domain cookies with a leading dot (e.g., '.google.com').
        self.assertEqual(remaining_cookies[0][0].lstrip('.'), 'google.com')

    def test_delete_firefox_live(self):
        """Test deleting Firefox cookies from a real database"""
        live_path = self._find_live_firefox_cookies_file()
        if not live_path:
            self.skipTest(
                'Skipping live Firefox test because cookies.sqlite was not found')

        def test_scenario(random_count):
            """Helper to test a cookie deletion scenario"""
            self.assertGreaterEqual(random_count, 0)
            temp_db = os.path.join(
                self.temp_dir, f'firefox_live_copy{random_count}.sqlite')
            shutil.copy2(live_path, temp_db)

            # Copy WAL/SHM files if present to keep the database consistent
            for suffix in ('-wal', '-shm'):
                aux_src = f"{live_path}{suffix}"
                if os.path.exists(aux_src):
                    shutil.copy2(aux_src, f"{temp_db}{suffix}")

            # Add a non-existent domain to keep list to test filtering
            doesnotexist = 'doesnotexist1234567890.com'
            if random_count:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                random_hosts = cursor.execute(
                    f'SELECT DISTINCT host FROM moz_cookies ORDER BY RANDOM() LIMIT {random_count}').fetchall()
                conn.close()
                keep_list = {host[0].lstrip('.') for host in random_hosts}
            else:
                keep_list = {doesnotexist}

            preview_result = Cookie.delete_cookies(
                temp_db, keep_list, really_delete=False)
            self.assertIn('total_deleted', preview_result)
            self.assertFalse(preview_result['skipped'])
            self.assertTrue(os.path.exists(temp_db))

            delete_result = Cookie.delete_cookies(
                temp_db, keep_list, really_delete=True)
            self.assertIn('total_deleted', delete_result)
            self.assertFalse(delete_result['skipped'])

            # Check file size reduction accuracy
            size_diff = abs(
                preview_result['file_size_reduction'] - delete_result['file_size_reduction'])
            # The estimate is accurate with shredding enabled, which is
            # how this test is run.
            self.assertLessEqual(
                size_diff, 1024, f"Size difference {size_diff:,} exceeds tolerance")

            if delete_result.get('whole_file_deleted'):
                self.assertFalse(os.path.exists(temp_db))
            else:
                self.assertTrue(os.path.exists(temp_db))
                os.unlink(temp_db)

        # Test scenario 1: Delete all cookies (keep non-existent domain)
        test_scenario(0)
        # Test scenario 2: Delete several random cookies
        test_scenario(10)
        test_scenario(50)

    def test_preview_cookies_deletion_chrome(self):
        """Test previewing Chrome cookie deletion"""
        path = self._create_chrome_cookies_db()

        # Test preview with allowlist
        keep_list = ['google.com']
        result = Cookie.delete_cookies(
            path, set(keep_list), really_delete=False)

        self.assertEqual(result['total_deleted'], 2)
        self.assertEqual(result['total_kept'], 1)
        self.assertFalse(result['skipped'])
        self.assertFalse(result['whole_file_deleted'])
        self.assertGreaterEqual(result['file_size_reduction'], 0)

        # Verify original database is unchanged
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        all_cookies = cursor.execute('SELECT host_key FROM cookies').fetchall()
        conn.close()

        self.assertEqual(len(all_cookies), 3)  # All cookies still there

    def test_allowlist_domain_matching_matrix(self):
        """Table-driven coverage for allowlist domain semantics"""
        for selection, host_value, expect_keep, reason in DOMAIN_MATCHING_CASES:
            with self.subTest(selection=selection, host=host_value, reason=reason):
                cookies = [(host_value, 'token')]
                path = self._create_chrome_cookies_db(cookies)
                result = Cookie.delete_cookies(
                    path, {selection}, really_delete=False)

                if expect_keep:
                    self.assertEqual(result['total_kept'], 1, reason)
                    self.assertEqual(result['total_deleted'], 0)
                else:
                    self.assertEqual(result['total_kept'], 0, reason)
                    self.assertEqual(result['total_deleted'], 1)

    def test_preview_cookies_deletion_no_allowlist(self):
        """Test previewing cookie deletion with no allowlist"""
        # Create test cookies
        cookies_data = [
            ('example.com', 'session_id'),
        ]

        path = self._create_chrome_cookies_db(cookies_data)

        # Test preview with no allowlist (should preview whole file deletion)
        with self.assertRaises(ValueError):
            Cookie.delete_cookies(path, set(), really_delete=False)

    def test_nonexistent_file(self):
        """Test handling of nonexistent cookie files"""
        path = os.path.join(self.temp_dir, 'nonexistent.db')

        # Both deletion and preview should raise ValueError for nonexistent files
        with self.assertRaises(ValueError):
            Cookie.delete_cookies(path, {'example.com'}, really_delete=True)
        with self.assertRaises(ValueError):
            Cookie.delete_cookies(path, {'example.com'}, really_delete=False)

    def test_browser_detection(self):
        """Test automatic browser detection"""
        # Test Chrome detection
        chrome_path = self._create_chrome_cookies_db()
        self.assertEqual(Cookie.detect_browser(
            chrome_path), ('cookies', 'host_key'))

        # Test Firefox detection
        firefox_path = self._create_firefox_cookies_db()
        self.assertEqual(Cookie.detect_browser(
            firefox_path), ('moz_cookies', 'host'))

    def test_empty_database(self):
        """Test handling of empty cookie databases"""
        # Create empty Chrome database
        path = self._create_chrome_cookies_db([])

        # Test deletion with allowlist
        result = Cookie.delete_cookies(
            path, {'example.com'}, really_delete=True)

        self.assertEqual(result['total_deleted'], 0)
        self.assertEqual(result['total_kept'], 0)
        self.assertFalse(result['skipped'])
        self.assertFalse(result['whole_file_deleted'])
        self.assertGreaterEqual(result['file_size_reduction'], 0)


if __name__ == '__main__':
    unittest.main()
