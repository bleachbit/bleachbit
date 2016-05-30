#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://www.bleachbit.org
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
Test case for module CLI
"""


import copy
import os
import sys
import tempfile
import unittest

sys.path.append('.')
from bleachbit.CLI import *
from bleachbit.General import run_external
from bleachbit import FileUtilities


class CLITestCase(unittest.TestCase):

    """Test case for module CLI"""

    def setUp(self):
        if os.path.exists('TestCLI.py'):
            os.chdir('..')

    def _test_preview(self, args, stdout=None, env=None):
        """Helper to test preview"""
        # Use devnull because in some cases the buffer will be too large,
        # and the other alternative, the screen, is not desirable.
        if stdout:
            stdout_ = None
        else:
            stdout_ = open(os.devnull, 'w')
        output = run_external(args, stdout=stdout_, env=env)
        if not stdout:
            stdout_.close()
        self.assertEqual(output[0], 0, "Return code = %d, stderr='%s'"
                         % (output[0], output[2]))
        pos = output[2].find('Traceback (most recent call last)')
        if pos > -1:
            print "Saw the following error when using args '%s':\n %s" \
                % (args, output[2])
        self.assertEqual(pos, -1)

    def test_args_to_operations(self):
        """Unit test for args_to_operations()"""
        tests = (
            (['adobe_reader.*'],
             {'adobe_reader': [u'cache', u'mru', u'tmp']}),
            (['adobe_reader.mru'], {'adobe_reader': [u'mru']}))
        for test in tests:
            o = args_to_operations(test[0], False)
            self.assertEqual(o, test[1])

    def test_cleaners_list(self):
        """Unit test for cleaners_list()"""
        for cleaner in cleaners_list():
            self.assert_(
                isinstance(
                    cleaner,
                    str) or isinstance(
                        cleaner,
                        unicode))

    def test_encoding(self):
        """Unit test for encoding"""
        if 'posix' != os.name:
            return

        (fd, filename) = tempfile.mkstemp(
            prefix='bleachbit-test-cli-encoding-\xe4\xf6\xfc~', dir='/tmp')
        os.close(fd)
        self.assert_(os.path.exists(filename))

        env = copy.deepcopy(os.environ)
        env['LANG'] = 'en_US'  # not UTF-8
        path = os.path.join('bleachbit', 'CLI.py')
        args = [sys.executable, path, '-p', 'system.tmp']
        # If Python pipes stdout to file or devnull, the test may give
        # a false negative.  It must print stdout to terminal.
        self._test_preview(args, stdout=True, env=env)

        os.remove(filename)
        self.assert_(not os.path.exists(filename))

    def test_invalid_locale(self):
        """Unit test for invalid locales"""
        lang = os.environ['LANG']
        os.environ['LANG'] = 'blahfoo'
        # tests are run from the parent directory
        path = os.path.join('bleachbit', 'CLI.py')
        args = [sys.executable, path, '--version']
        output = run_external(args)
        self.assertNotEqual(output[1].find('Copyright'), -1, str(output))
        os.environ['LANG'] = lang

    def test_preview(self):
        """Unit test for --preview option"""
        args_list = []
        path = os.path.join('bleachbit', 'CLI.py')
        big_args = [sys.executable, path, '--preview', ]
        for cleaner in cleaners_list():
            args_list.append([sys.executable, path, '--preview', cleaner])
            big_args.append(cleaner)
        args_list.append(big_args)

        for args in args_list:
            self._test_preview(args)

    def test_delete(self):
        """Unit test for --delete option"""
        (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-cli-delete')
        os.close(fd)
        if 'nt' == os.name:
            import win32api
            filename = os.path.normcase(win32api.GetLongPathName(filename))
        # replace delete function for testing
        save_delete = FileUtilities.delete
        deleted_paths = []

        def dummy_delete(path, shred=False):
            self.assert_(os.path.exists(path))
            deleted_paths.append(os.path.normcase(path))
        FileUtilities.delete = dummy_delete
        FileUtilities.delete(filename)
        self.assert_(os.path.exists(filename))
        operations = args_to_operations(['system.tmp'], False)
        preview_or_clean(operations, True)
        FileUtilities.delete = save_delete
        self.assert_(filename in deleted_paths,
                     "%s not found deleted" % filename)
        os.remove(filename)
        self.assert_(not os.path.exists(filename))

    def test_shred(self):
        """Unit test for --shred"""
        suffixes = ['', '.', '.txt']
        dirs = ['.', None]
        for dir_ in dirs:
            for suffix in suffixes:
                (fd, filename) = tempfile.mkstemp(
                    prefix='bleachbit-test-cli-shred', suffix=suffix, dir=dir_)
                os.close(fd)
                if '.' == dir_:
                    filename = os.path.basename(filename)
                self.assert_(os.path.exists(filename))
                path = os.path.join('bleachbit', 'CLI.py')
                args = [sys.executable, path, '--shred', filename]
                output = run_external(args, stdout=open(os.devnull, 'w'))
                self.assert_(not os.path.exists(filename))


def suite():
    return unittest.makeSuite(CLITestCase)


if __name__ == '__main__':
    unittest.main()
