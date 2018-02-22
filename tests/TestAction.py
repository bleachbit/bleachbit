# vim: ts=4:sw=4:expandtab
# coding=utf-8

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
Test cases for module Action
"""

from __future__ import absolute_import, print_function

from bleachbit.Action import *
from bleachbit import FSE, expanduser, expandvars
from tests import common

import shutil
import sys
import tempfile
import unittest
from xml.dom.minidom import parseString


def _action_str_to_commands(action_str):
    """Parse <action> and return commands"""
    dom = parseString(action_str)
    action_node = dom.childNodes[0]
    delete = Delete(action_node)
    for cmd in delete.get_commands():
        yield cmd


def _action_str_to_results(action_str):
    """Parse <action> and return list of results

    It lists the files, but it does not really delete them.
    """
    return [cmd.execute(False).next() for cmd in _action_str_to_commands(action_str)]


def benchmark_filter(this_filter):
    """Measure how fast listing files is with and without filter"""
    n_files = 100000
    print('benchmark of %d files' % n_files)

    # make a directory with many files
    dirname = tempfile.mkdtemp(prefix='bleachbit-action-bench')
    for x in range(0, n_files):
        common.touch_file(os.path.join(dirname, str(x)))

    # scan directory
    import time
    start = time.time()
    filter_code = ''
    if 'regex' == this_filter:
        # This regex matches everything, so the "no filter" and regex
        # are comparable
        filter_code = 'regex="."'
    action_str = u'<action command="delete" search="glob" path="%s/*" %s />' % \
        (dirname, filter_code)
    results = _action_str_to_results(action_str)
    end = time.time()
    elapsed_seconds = end - start
    rate = n_files / elapsed_seconds
    print('filter %s: elapsed: %.2f seconds, %.2f files/second' % (this_filter, elapsed_seconds, rate))

    # clean up
    shutil.rmtree(dirname)

    return rate


def dir_is_empty(dirname):
    """Check whether a directory is empty"""
    return not os.listdir(dirname)


class ActionTestCase(common.BleachbitTestCase):

    """Test cases for Action"""

    def _test_action_str(self, action_str):
        """Parse <action> and test it"""
        dom = parseString(action_str)
        action_node = dom.childNodes[0]
        command = action_node.getAttribute('command')
        filename = action_node.getAttribute('path')
        search = action_node.getAttribute('search')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(action_node)
        self.assertNotEqual(provider, None)
        for cmd in provider.get_commands():
            self.assertIsInstance(cmd, (Command.Delete, Command.Ini, Command.Json, Command.Function))
            if 'process' != command:
                # process does not have a filename
                self.assertLExists(filename)
            # preview
            result = cmd.execute(really_delete=False).next()
            common.validate_result(self, result)
            self.assertNotEqual('/', result['path'])
            # delete
            ret = cmd.execute(really_delete=True).next()
            if 'delete' == command:
                self.assertNotLExists(cmd.path)
            elif 'truncate' == command:
                self.assertLExists(filename)
                os.remove(filename)
                self.assertNotLExists(filename)
            elif command in 'process':
                pass
            elif command in ('ini', 'json'):
                self.assertLExists(filename)
            else:
                raise RuntimeError("Unknown command '%s'" % command)
        if 'walk.all' == search:
            self.assertTrue(dir_is_empty(filename), 'directory not empty after walk.all: %s' % filename)

    def test_delete(self):
        """Unit test for class Delete"""
        paths = [u'~']
        if 'nt' == os.name:
            # Python 2.6 and later supports %foo%
            paths.append(u'%USERPROFILE%')
            # Python 2.5 and later supports $foo
            paths.append(u'${USERPROFILE}')
            paths.append(u'$USERPROFILE')
        if 'posix' == os.name:
            paths.append(u'$HOME')
        for path in paths:
            for mode in ('delete', 'truncate', 'delete_forward'):
                expanded = expanduser(expandvars(path))
                filename = self.mkstemp(dir=expanded, prefix='bleachbit-action-delete')
                command = mode
                if 'delete_forward' == mode:
                    # forward slash needs to be normalized on Windows
                    if 'nt' == os.name:
                        command = 'delete'
                        filename = filename.replace('\\', '/')
                    else:
                        # test not needed on this OS
                        os.remove(filename)
                        continue
                action_str = u'<action command="%s" search="file" path="%s" />' % \
                    (command, filename)
                self._test_action_str(action_str)
                self.assertNotExists(filename)

    def test_delete_special_filenames(self):
        """Unit test for deleting special filenames"""
        tests = [
            'normal',
            'space in name',
            'sigil$should-not-be-expanded',
        ]
        for test in tests:
            pathname = self.write_file(test)
            action_str = u'<action command="delete" search="file" path="%s" />' % pathname
            self._test_action_str(action_str)
            self.assertNotExists(pathname)

    def test_ini(self):
        """Unit test for class Ini"""
        from tests.TestFileUtilities import test_ini_helper

        def execute_ini(path, section, parameter):
            effective_parameter = ""
            if parameter is not None:
                effective_parameter = 'parameter="%s"' % parameter
            action_str = u'<action command="ini" search="file" path="%s" section="%s" %s />' \
                % (path, section, effective_parameter)
            self._test_action_str(action_str)

        test_ini_helper(self, execute_ini)

    def test_json(self):
        """Unit test for class Json"""
        from tests.TestFileUtilities import test_json_helper

        def execute_json(path, address):
            action_str = u'<action command="json" search="file" path="%s" address="%s" />' \
                % (path, address)
            self._test_action_str(action_str)

        test_json_helper(self, execute_json)

    def test_process(self):
        """Unit test for process action"""
        cmds = {'nt': 'cmd.exe /c dir', 'posix': 'dir'}
        tests = [u'<action command="process" cmd="%s" />',
                 u'<action command="process" wait="false" cmd="%s" />',
                 u'<action command="process" wait="f" cmd="%s" />',
                 u'<action command="process" wait="no" cmd="%s" />',
                 u'<action command="process" wait="n" cmd="%s" />'
                 ]

        for test in tests:
            self._test_action_str(test % cmds[os.name])

    def test_regex(self):
        """Unit test for regex option"""
        _iglob = glob.iglob
        glob.iglob = lambda x: ['/tmp/foo1', '/tmp/foo2', '/tmp/bar1']
        _getsize = FileUtilities.getsize
        FileUtilities.getsize = lambda x: 1

        # should match three files using no regexes
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" />'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 3)

        # should match second file using positive regex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" regex="^foo2$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], '/tmp/foo2')

        # On Windows should be case insensitive
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" regex="^FOO2$"/>'
        results = _action_str_to_results(action_str)
        if 'nt' == os.name:
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['path'], '/tmp/foo2')
        else:
            self.assertEqual(len(results), 0)

        # should match second file using negative regex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" nregex="^(foo1|bar1)$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], '/tmp/foo2')

        # should match second file using both regexes
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" regex="^f" nregex="1$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], '/tmp/foo2')

        # should match nothing using positive regex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" regex="^bar$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 0)

        # should match nothing using negative regex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" nregex="."/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 0)

        # should give an error
        action_str = u'<action command="delete" search="invalid" path="/tmp/foo*" regex="^bar$"/>'
        self.assertRaises(RuntimeError, lambda: _action_str_to_results(action_str))

        # clean up
        glob.iglob = _iglob
        FileUtilities.getsize = _getsize

    def test_wholeregex(self):
        """Unit test for wholeregex filter"""
        _iglob = glob.iglob
        glob.iglob = lambda x: ['/tmp/foo1', '/tmp/foo2', '/tmp/bar1']
        _getsize = FileUtilities.getsize
        FileUtilities.getsize = lambda x: 1

        # should match three files using no regexes
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" />'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 3)

        # should match two files using wholeregex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" wholeregex="^/tmp/foo.*$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['path'], '/tmp/foo1')

        # should match third file using nwholeregex
        action_str = u'<action command="delete" search="glob" path="/tmp/foo*" nwholeregex="^/tmp/foo.*$"/>'
        results = _action_str_to_results(action_str)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], '/tmp/bar1')

        # clean up
        glob.iglob = _iglob
        FileUtilities.getsize = _getsize

    def test_type(self):
        """Unit test for type attribute"""
        dirname = self.mkdtemp(prefix='bleachbit-action-type')
        filename = os.path.join(dirname, 'file')

        # this should not delete anything
        common.touch_file(filename)
        action_str = u'<action command="delete" search="file" type="d" path="%s" />' % filename
        self._test_action_str(action_str)
        self.assertExists(filename)

        # should delete file
        action_str = u'<action command="delete" search="file" type="f" path="%s" />' % filename
        self._test_action_str(action_str)
        self.assertNotExists(filename)

        # should delete file
        common.touch_file(filename)
        action_str = u'<action command="delete" search="file" path="%s" />' % filename
        self._test_action_str(action_str)
        self.assertNotExists(filename)

        # should not delete anything
        action_str = u'<action command="delete" search="file" type="f" path="%s" />' % dirname
        self._test_action_str(action_str)
        self.assertExists(dirname)

        # should delete directory
        action_str = u'<action command="delete" search="file" type="d" path="%s" />' % dirname
        self._test_action_str(action_str)
        self.assertNotExists(dirname)

    def test_walk_all(self):
        """Unit test for walk.all"""
        dirname = self.mkdtemp(prefix='bleachbit-walk-all')

        # this sub-directory should be deleted
        subdir = os.path.join(dirname, 'sub')
        os.mkdir(subdir)
        self.assertExists(subdir)

        # this file should be deleted too
        filename = os.path.join(subdir, 'file')
        common.touch_file(filename)

        action_str = u'<action command="delete" search="walk.all" path="%s" />' % dirname
        self._test_action_str(action_str)
        self.assertNotExists(subdir)

        os.rmdir(dirname)

    def test_walk_files(self):
        """Unit test for walk.files"""
        paths = {'posix': '/var', 'nt': '$WINDIR\\system32'}

        action_str = u'<action command="delete" search="walk.files" path="%s" />' % paths[os.name]
        results = 0
        for cmd in _action_str_to_commands(action_str):
            result = cmd.execute(False).next()
            common.validate_result(self, result)
            path = result['path']
            self.assertFalse(os.path.isdir(path), "%s is a directory" % path)
            results += 1
        self.assertGreater(results, 0)


def suite():
    return unittest.makeSuite(ActionTestCase)


if __name__ == '__main__':
    if 1 < len(sys.argv) and 'benchmark' == sys.argv[1]:
        for this_filter in ['none', 'regex']:
            rates = []
            iterations = 1
            if 3 == len(sys.argv):
                iterations = int(sys.argv[2])
            for x in range(0, iterations):
                rate = benchmark_filter(this_filter)
                rates.append(rate)
            # combine all the rates for easy copy and paste into R for analysis
            print('rates for filter %s=%s' % (this_filter, ','.join([str(rate) for rate in rates])))
        sys.exit()
    unittest.main()
