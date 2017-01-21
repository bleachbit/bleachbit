# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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

from __future__ import absolute_import, division, print_function, unicode_literals

from bleachbit.DeepScan import DeepScan, normalized_walk
from bleachbit.Common import expanduser
from tests import common

import os
import shutil
import tempfile
import unittest


class DeepScanTestCase(unittest.TestCase, common.AssertFile, common.TypeAsserts):

    """Test Case for module DeepScan"""

    def _test_encoding(self, fn):
        """Test encoding"""

        tempd = tempfile.mkdtemp(prefix='bleachbit-test-deepscan')
        self.assertExists(tempd)

        fullpath = os.path.join(tempd, fn)
        common.touch_file(fullpath)

        ds = DeepScan()
        ds.add_search(tempd, '^%s$' % fn)
        found = False
        for ret in ds.scan():
            if True == ret:
                continue
            self.assert_(ret == fullpath)
            found = True
        self.assert_(found, "Did not find '%s'" % fullpath)

        os.unlink(fullpath)
        self.assertNotExists(fullpath)
        os.rmdir(tempd)
        self.assertNotExists(tempd)

    def test_encoding(self):
        """Test encoding"""
        tests = ('äöüßÄÖÜ',
                 "עִבְרִית")

        for test in tests:
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
        base = tempfile.mkdtemp(prefix='bleachbit-deepscan-test')
        f_del1 = os.path.join(base, 'foo.txt.bbtestbak')
        common.touch_file(f_del1)
        f_keep = os.path.join(base, 'foo.txt')
        common.touch_file(f_keep)
        subdir = os.path.join(base, 'sub')
        os.mkdir(subdir)
        f_del2 = os.path.join(base, 'sub/bar.ini.bbtestbak')
        common.touch_file(f_del2)

        # sanity check
        self.assertExists(f_del1)
        self.assertExists(f_keep)
        self.assertExists(f_del2)

        # run deep scan
        astr = '<action command="delete" search="deep" regex="\.bbtestbak$" cache="false" path="%s"/>' % base
        import TestCleaner
        cleaner = TestCleaner.action_to_cleaner(astr)
        from bleachbit.Worker import backends, Worker
        backends['test'] = cleaner
        operations = {'test': ['option1']}
        from bleachbit import CLI
        ui = CLI.CliCallback()
        worker = Worker(ui, True, operations)
        run = worker.run()
        while next(run):
            pass

        # validate results

        self.assertFalse(os.path.exists(f_del1))
        self.assertExists(f_keep)
        self.assertFalse(os.path.exists(f_del2))

        # clean up
        shutil.rmtree(base)

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


def suite():
    return unittest.makeSuite(DeepScanTestCase)


if __name__ == '__main__':
    unittest.main()
