# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module DeepScan
"""

# standard imports
import os
import shutil
import sys
import unittest
from unittest import mock

# first party imports
from tests import common
from tests import TestCleaner
from tests.common import SPECIAL_TEST_STRINGS
from bleachbit.DeepScan import DeepScan, Search, normalized_walk


class DeepScanTestCase(common.BleachbitTestCase):
    """Test Case for module DeepScan"""

    def _test_encoding(self, fn):
        """Test encoding"""

        fullpath = self.write_file(fn + ".bak")

        # Add Unicode paths to encourage a crash.
        subdir = os.path.join(self.tempdir, 'ɡælɪk.dir')
        os.mkdir(subdir)
        subfile = os.path.join(subdir, 'ɡælɪk.file')
        common.touch_file(subfile)

        searches = {self.tempdir: []}
        searches[self.tempdir].append(
            Search(command='delete', regex=r'\.[Bb][Aa][Kk]$'))
        ds = DeepScan(searches)
        found = False
        for cmd in ds.scan():
            if cmd == True:
                # True is used to yield to GTK+, but it is not
                # needed in this test.
                continue
            self.assertExists(cmd.path)
            if cmd.path == fullpath:
                found = True
        self.assertTrue(found, "Did not find '%s'" % fullpath)

        os.unlink(fullpath)
        self.assertNotExists(fullpath)

        shutil.rmtree(subdir)

    def test_encoding(self):
        """Test encoding"""
        for test in SPECIAL_TEST_STRINGS:
            self._test_encoding(test)

    def test_DeepScan(self):
        """Unit test for class DeepScan.  Preview real files."""
        path = os.path.expanduser('~')
        searches = {path: []}
        for regex in ('^(Makefile|Thumbs(:encryptable)?\\.db|[^.].*[0-9A-Za-z]~|bak)$'):
            searches[path].append(Search(command='delete', regex=regex))
        ds = DeepScan(searches)
        for cmd in ds.scan():
            if True == cmd:
                # it's yielding control to the GTK idle loop
                continue
            self.assertLExists(cmd.path)

    def _test_delete(self, command):
        """Delete files in a test environment"""

        # make some files
        f_del = self.write_file('foo.txt.bbtestbak')
        f_keep = self.write_file('foo.txt')
        subdir = os.path.join(self.tempdir, 'sub')
        os.mkdir(subdir)
        f_del2 = self.write_file(os.path.join(subdir, 'bar.ini.bbtestbak'))
        f_del3 = self.write_file(os.path.join(subdir, 'bar.ini.bbtestBAK'))

        # sanity check
        self.assertExists(f_del)
        self.assertExists(f_keep)
        self.assertExists(f_del2)

        # run deep scan
        def run_deep_scan(regex):
            astr = '<action command="{}" search="deep" cache="false" path="{}" {}/>'.format(
                command, self.tempdir, regex)
            cleaner = TestCleaner.action_to_cleaner(astr)
            from bleachbit.Worker import backends, Worker
            backends['test'] = cleaner
            operations = {'test': ['option1']}
            from bleachbit import CLI
            ui = CLI.CliCallback()
            worker = Worker(ui, True, operations)
            list(worker.run())
            del backends['test']

        # validate results
        run_deep_scan(r'regex="\.bbtestbak$" wholeregex="sub.*\.bbtestbak$"')
        self.assertExists(f_del)
        self.assertExists(f_keep)
        self.assertFalse(os.path.exists(f_del2))
        if 'posix' == os.name:
            self.assertExists(f_del3)
        else:
            self.assertFalse(os.path.exists(f_del3))

        # validate results
        run_deep_scan(r'regex="\.bbtestbak$"')
        self.assertFalse(os.path.exists(f_del))
        self.assertExists(f_keep)

        # cleanup
        os.unlink(f_keep)
        if 'posix' == os.name:
            os.unlink(f_del3)
        os.rmdir(subdir)

    def test_delete(self):
        self._test_delete('delete')

    def test_shred(self):
        self._test_delete('shred')

    @unittest.skipUnless('darwin' == sys.platform, 'Not on Darwin')
    def test_normalized_walk_darwin(self):

        with mock.patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/foo', ('bar',), ['ba\xcc\x80z']),
                ('/foo/bar', (), ['spam', 'eggs']),
            ]
            with mock.patch('platform.system') as mock_platform_system:
                mock_platform_system.return_value = 'Darwin'
                self.assertEqual(list(normalized_walk('.')), [
                    ('/foo', ('bar',), ['b\xc3\xa0z']),
                    ('/foo/bar', (), ['spam', 'eggs']),
                ])

        with mock.patch('os.walk') as mock_walk:
            expected = [
                ('/foo', ('bar',), ['baz']),
                ('/foo/bar', (), ['spam', 'eggs']),
            ]
            mock_walk.return_value = expected
            self.assertEqual(list(normalized_walk('.')), expected)
