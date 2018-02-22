# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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
Test case for module DeepScan
"""

from __future__ import absolute_import, print_function

from tests import common
from bleachbit.DeepScan import DeepScan, normalized_walk
from bleachbit import expanduser

import os


class DeepScanTestCase(common.BleachbitTestCase):
    """Test Case for module DeepScan"""

    def _test_encoding(self, fn):
        """Test encoding"""

        fullpath = self.write_file(fn)

        ds = DeepScan()
        ds.add_search(self.tempdir, '^%s$' % fn)
        found = False
        for ret in ds.scan():
            if True == ret:
                continue
            print(ret)
            self.assertEqual(ret, fullpath)
            found = True
        self.assertTrue(found, "Did not find '%s'" % fullpath)

        os.unlink(fullpath)
        self.assertNotExists(fullpath)

    def test_encoding(self):
        """Test encoding"""
        for test in ('äöüßÄÖÜ', "עִבְרִית"):
            self._test_encoding(test)

    def test_DeepScan(self):
        """Unit test for class DeepScan.  Preview real files."""
        ds = DeepScan()
        path = expanduser('~')
        ds.add_search(path, '^Makefile$')
        ds.add_search(path, '~$')
        ds.add_search(path, 'bak$')
        ds.add_search(path, '^Thumbs.db$')
        ds.add_search(path, '^Thumbs.db:encryptable$')
        for ret in ds.scan():
            if True == ret:
                # it's yielding control to the GTK idle loop
                continue
            self.assertIsString(ret, "Expecting string but got '%s' (%s)" % (ret, str(type(ret))))
            self.assertLExists(ret)

    def test_delete(self):
        """Delete files in a test environment"""

        # make some files
        f_del1 = self.write_file('foo.txt.bbtestbak')
        f_keep = self.write_file('foo.txt')
        subdir = os.path.join(self.tempdir, 'sub')
        os.mkdir(subdir)
        f_del2 = self.write_file(os.path.join(subdir,'bar.ini.bbtestbak'))

        # sanity check
        self.assertExists(f_del1)
        self.assertExists(f_keep)
        self.assertExists(f_del2)

        # run deep scan
        astr = '<action command="delete" search="deep" regex="\.bbtestbak$" cache="false" path="%s"/>' % self.tempdir
        from tests import TestCleaner
        cleaner = TestCleaner.action_to_cleaner(astr)
        from bleachbit.Worker import backends, Worker
        backends['test'] = cleaner
        operations = {'test': ['option1']}
        from bleachbit import CLI
        ui = CLI.CliCallback()
        worker = Worker(ui, True, operations)
        list(worker.run())

        # validate results
        self.assertFalse(os.path.exists(f_del1))
        self.assertExists(f_keep)
        self.assertFalse(os.path.exists(f_del2))

    def test_normalized_walk_darwin(self):
        import mock

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
