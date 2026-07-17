# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test cases for module Action
"""

# standard imports
import glob
import logging
import os
import shutil
import sys
import tempfile
import time
import unittest
import xml.parsers.expat
from unittest import mock
from xml.dom.minidom import parseString
from xml.sax.saxutils import quoteattr

# first party imports
import bleachbit.FileUtilities
from bleachbit import IS_WINDOWS, IS_POSIX, IS_LINUX, IS_MAC, FS_CASE_SENSITIVE, logger
from bleachbit.Action import ActionProvider, Command, Delete, has_glob, expand_multi_var
from bleachbit.CleanerML import CleanerML
from tests import common
from tests.TestFileUtilities import ini_helper
from tests.TestFileUtilities import json_helper


def _action_str_to_commands(action_str):
    """Parse <action> and return commands"""
    dom = parseString(action_str)
    action_node = dom.childNodes[0]
    delete = Delete(action_node)
    yield from delete.get_commands()


def _action_str_to_results(action_str):
    """Parse <action> and return list of results

    It lists the files, but it does not really delete them.
    """
    return [next(cmd.execute(False)) for cmd in _action_str_to_commands(action_str)]


def benchmark_filter(filter_type):
    """Measure how fast listing files is with and without filter"""
    n_files = 100000
    logger.info('benchmark of %d files', n_files)

    # make a directory with many files
    dirname = tempfile.mkdtemp(prefix='bleachbit-action-bench')
    for x in range(0, n_files):
        common.touch_file(os.path.join(dirname, str(x)))

    # scan directory
    start = time.time()
    filter_code = ''
    if 'regex' == filter_type:
        # This regex matches everything, so the "no filter" and regex
        # are comparable
        filter_code = 'regex="."'
    action_str = f'<action command="delete" search="glob" path="{dirname}/*" {filter_code} />'
    _action_str_to_results(action_str)
    end = time.time()
    elapsed_seconds = end - start
    rate = n_files / elapsed_seconds
    logger.info('filter %s: elapsed: %.2f seconds, %.2f files/second',
                filter_type, elapsed_seconds, rate)

    # clean up
    shutil.rmtree(dirname)

    return rate


def dir_is_empty(dirname):
    """Check whether a directory is empty"""
    return not os.listdir(dirname)


class ActionTestCase(common.BleachbitTestCase):

    """Test cases for Action"""

    _TEST_PROCESS_CMD = 'cmd.exe /c dir' if IS_WINDOWS else 'dir'
    _TEST_PROCESS_SIMPLE = '<action command="process" cmd={cmd} />'

    def _test_action_str(self, action_str, expect_exists=True):
        """Parse <action> and test it"""
        try:
            dom = parseString(action_str)
        except xml.parsers.expat.ExpatError as e:
            self.fail(f"parse error: {action_str}: {e}")
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
            self.assertIsInstance(
                cmd, (Command.Delete, Command.Ini, Command.Json, Command.Function))
            if 'process' != command and not has_glob(filename) and expect_exists:
                # process does not have a filename
                self.assertLExists(filename)
            # preview
            result = next(cmd.execute(really_delete=False))
            common.validate_result(self, result)
            self.assertNotEqual('/', result['path'])
            # delete
            next(cmd.execute(really_delete=True))
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
                raise RuntimeError(f'Unknown command {command}')
        if 'walk.all' == search:
            if expect_exists:
                self.assertTrue(dir_is_empty(
                    filename), f'directory not empty after walk.all: {filename}')

    def test_delete(self):
        """Unit test for class Delete"""
        paths = ['~']
        if IS_WINDOWS:
            # Python 2.6 and later supports %foo%
            paths.append('%USERPROFILE%')
            # Python 2.5 and later supports $foo
            paths.append('${USERPROFILE}')
            paths.append('$USERPROFILE')
        elif IS_POSIX:
            paths.append('$HOME')
        for path in paths:
            for mode in ('delete', 'truncate', 'delete_forward'):
                expanded = os.path.expanduser(os.path.expandvars(path))
                filename = self.mkstemp(
                    dir=expanded, prefix='bleachbit-action-delete')
                command = mode
                if 'delete_forward' == mode:
                    # forward slash needs to be normalized on Windows
                    if IS_WINDOWS:
                        command = 'delete'
                        filename = filename.replace('\\', '/')
                    else:
                        # test not needed on this OS
                        os.remove(filename)
                        continue
                action_str = f'<action command="{command}" search="file" path="{filename}" />'
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
            action_str = f'<action command="delete" search="file" path="{pathname}" />'
            self._test_action_str(action_str)
            self.assertNotExists(pathname)

    def test_expand_multi_var(self):
        """Unit test for the function expand_multi_var"""
        # each test is a tuple in format (input_str, vars, expected)
        tests = (
            # no variables
            ('/var/foo1', None, ('/var/foo1',)),
            # unknown variable
            ('/var/foo2$$bar$$', None, ('/var/foo2$$bar$$',)),
            # unused variable
            ('/var/foo3_$$bar$$', {'baz': ('a',)}, ('/var/foo3_$$bar$$',)),
            # used variable with one value
            ('/var/foo4_$$bar$$', {'bar': ('a',)}, ('/var/foo4_a',)),
            # used variable with two values
            ('/var/foo5_$$bar$$', {'bar': ('a', 'b')},
             ('/var/foo5_a', '/var/foo5_b')),
            # the system is case sensitive
            ('/var/foo6_$$BAR$$', {'bar': ('a',)}, ('/var/foo6_$$BAR$$',)),
            ('/var/foo7_$$bar$$', {'BAR': ('a',)}, ('/var/foo7_$$bar$$',)),
            # Windows-style
            (r'c:\temp\foo8_$$bar$$', {'bar': ('a',)}, (r'c:\temp\foo8_a',)),
            (r'$$basepath$$\file9.log', {'basepath': (
                r'c:\temp',)}, (r'c:\temp\file9.log',)),
            # two variables with one value each
            ('/var/foo10_$$foo$$_$$bar$$',
             {'foo': 'a', 'bar': 'b'}, ('/var/foo10_a_b',)),
            # two variables with 1 and 2 values, respectively
            ('/var/foo10_$$foo$$_$$bar$$',
             {'foo': 'a', 'bar': ('b', 'c')}, ('/var/foo10_a_b', '/var/foo10_a_c')),

        )

        for test in tests:
            input_str = test[0]
            variables = test[1]
            expected = test[2]
            actual = expand_multi_var(input_str, variables)
            self.assertSequenceEqual(actual, expected)

    def test_windows_system_var(self):
        """Unit test for expanding %WindowsSystem% in action paths."""
        action_xml = (
            r'<action command="delete" search="file" '
            r'path="%WindowsSystem%\foo.log"/>'
        )
        action_node = parseString(action_xml).childNodes[0]
        expanded = [r'C:\Windows\Sysnative\foo.log',
                    r'C:\Windows\SysWOW64\foo.log']
        with mock.patch('bleachbit.Action.IS_WINDOWS', True), \
                mock.patch('bleachbit.Action.Windows', create=True) as mock_windows:
            mock_windows.expand_windows_system_vars.return_value = expanded
            action = Delete(action_node)
        self.assertEqual(expanded, action.paths)
        mock_windows.expand_windows_system_vars.assert_called_once_with(
            r'%WindowsSystem%\foo.log')

    def test_has_glob(self):
        """Unit test for function has_glob()"""
        tests = ((r'c:\windows\*.log', True),
                 (r'c:\windows\temp.log', False),
                 (r'c:\windows\temp?.log', True),
                 (r'c:\windows\temp[abc].log', True))
        for (test_input, test_expected) in tests:
            test_actual = has_glob(test_input)
            test_msg = f'test input: {test_input}, expected: {test_expected}, actual: {test_actual}'
            self.assertEqual(test_actual, test_expected, test_msg)

    def test_ini(self):
        """Unit test for class Ini"""
        def execute_ini(path, section, parameter):
            effective_parameter = ""
            if parameter is not None:
                effective_parameter = f'parameter="{parameter}"'
            action_str = (
                '<action command="ini" search="file" '
                f'path="{path}" section="{section}" {effective_parameter} />'
            )
            self._test_action_str(action_str)

        ini_helper(self, execute_ini)

    def test_json(self):
        """Unit test for class Json"""
        def execute_json(path, address):
            action_str = (
                '<action command="json" search="file" '
                f'path="{path}" address="{address}" />'
            )
            self._test_action_str(action_str)

        json_helper(self, execute_json)

    def test_process(self):
        """Unit test for process action"""
        tests = [ActionTestCase._TEST_PROCESS_SIMPLE,
                 '<action command="process" cmd={cmd} wait="{wait}" />',
                 ]

        if IS_WINDOWS:
            cmds = [
                'ping /?',
                '%windir%\\System32\\ping.exe /?',
                '"%windir%\\System32\\ping.exe" /?',
            ]
        else:
            ls_flag = '-l'
            cmds = ['ls', f'ls {ls_flag}', f'/bin/ls {ls_flag}', '/bin/ls']
        for cmd in cmds:
            cmd_qa = quoteattr(cmd)
            for wait in ('true', 't', 'false', 'f', 'no', 'n'):
                for test in tests:
                    self._test_action_str(test.format(cmd=cmd_qa, wait=wait))

    def test_process_with_space(self):
        """Test process action with space in command"""
        # This is a regression test for a bug where spaces in commands were not handled correctly
        delete_me = self.write_file('delete me.txt')
        if IS_WINDOWS:
            cmd = f'cmd /c del "{delete_me}"'
        else:
            delete_me_escaped = delete_me.replace(" ", "\\ ")
            cmd = f'rm {delete_me_escaped}'
        cmd_qa = quoteattr(cmd)
        action_str = f'<action command="process" cmd={cmd_qa} wait="true" />'
        self._test_action_str(action_str)
        self.assertNotExists(delete_me)

    def test_process_space(self):
        """Unit test for process action with space in path

        https://github.com/bleachbit/bleachbit/pull/871
        """
        fn = os.path.join(self.tempdir, 'file with space.txt')
        common.touch_file(fn)
        if IS_WINDOWS:
            cmd = f'cmd /c del &quot;{fn}&quot;'
        else:
            fn_for_cmd = fn.replace(" ", "\\ ")
            cmd = f'rm {fn_for_cmd}'
        action_str = f'<action command="process" wait="true" cmd="{cmd}" />'
        self._test_action_str(action_str)
        self.assertNotExists(fn)

    def test_process_unicode_stderr(self):
        """
        Test what happens when we have return code != 0 and unicode string in stderr.

        In other words we test the case when we have an error and a non-ascii language setting.
        """
        with mock.patch('bleachbit.Action.General.run_external', return_value=(11, '', 'Уникод, който чупи кода!')):
            # If exception occurs in logger `handleError` is called.
            with mock.patch.object(logging.Handler, 'handleError') as MockHandleError:
                try:
                    # When GtkLoggerHandler is used the exceptions are raised directly
                    # and handleError is not called
                    self._test_action_str(
                        ActionTestCase._TEST_PROCESS_SIMPLE.format(cmd=quoteattr(ActionTestCase._TEST_PROCESS_CMD)))
                except UnicodeDecodeError:
                    self.fail(
                        "test_process_unicode_stderr() raised UnicodeDecodeError unexpectedly!")
                else:
                    MockHandleError.assert_not_called()

    def test_regex(self):
        """Unit test for regex option"""
        with mock.patch('glob.iglob', lambda x: ['/tmp/foo1', '/tmp/foo2', '/tmp/bar1']), \
                mock.patch('bleachbit.FileUtilities.getsize', lambda x: 1):
            # should match three files using no regexes
            action_str = '<action command="delete" search="glob" path="/tmp/foo*" />'
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 3)

            # should match second file using positive regex
            action_str = '<action command="delete" search="glob" path="/tmp/foo*" regex="^foo2$"/>'
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['path'], '/tmp/foo2')

            # On case-insensitive filesystems (Windows, macOS) the regex
            # should match case-insensitively.
            action_str = '<action command="delete" search="glob" path="/tmp/foo*" regex="^FOO2$"/>'
            results = _action_str_to_results(action_str)
            if FS_CASE_SENSITIVE:
                self.assertEqual(len(results), 0)
            else:
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]['path'], '/tmp/foo2')

            # should match second file using negative regex
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" nregex="^(foo1|bar1)$"/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['path'], '/tmp/foo2')

            # should match second file using both regexes
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" regex="^f" nregex="1$"/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['path'], '/tmp/foo2')

            # should match nothing using positive regex
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" regex="^bar$"/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 0)

            # should match nothing using negative regex
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" nregex="."/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 0)

            # should give an error
            action_str = (
                '<action command="delete" search="invalid" '
                'path="/tmp/foo*" regex="^bar$"/>'
            )
            self.assertRaises(
                RuntimeError, lambda: _action_str_to_results(action_str))

    def test_search_glob(self):
        """Unit test for search=glob"""

        fname = 'abcdefg'
        pathname = self.write_file(fname)
        tests = (pathname,
                 os.path.join(self.tempdir, 'abc*'),
                 os.path.join(self.tempdir, '*efg'),
                 os.path.join(self.tempdir, 'a*c*e*g'),
                 os.path.join(self.tempdir, 'a?cdefg'),
                 os.path.join(self.tempdir, 'a?????g'),
                 os.path.join(self.tempdir, '[a-z]b?d*'))
        for test in tests:
            with self.subTest(test=test):
                pathname = self.write_file(fname)
                self.assertExists(pathname)
                action_str = (
                    '<action command="delete" search="glob" '
                    f'path="{test}" />'
                )
                self._test_action_str(action_str)
                self.assertNotExists(pathname)

    def test_wholeregex(self):
        """Unit test for wholeregex filter"""
        with mock.patch('glob.iglob', lambda x: ['/tmp/foo1', '/tmp/foo2', '/tmp/bar1']), \
                mock.patch('bleachbit.FileUtilities.getsize', lambda x: 1):
            # should match three files using no regexes
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" />'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 3)

            # should match two files using wholeregex
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" wholeregex="^/tmp/foo.*$"/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['path'], '/tmp/foo1')

            # should match third file using nwholeregex
            action_str = (
                '<action command="delete" search="glob" '
                'path="/tmp/foo*" nwholeregex="^/tmp/foo.*$"/>'
            )
            results = _action_str_to_results(action_str)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['path'], '/tmp/bar1')

    def test_type(self):
        """Unit test for type attribute"""
        dirname = self.mkdtemp(prefix='bleachbit-action-type')
        filename = os.path.join(dirname, 'file')

        # this should not delete anything
        common.touch_file(filename)
        action_str = f'<action command="delete" search="file" type="d" path="{filename}" />'
        self._test_action_str(action_str)
        self.assertExists(filename)

        # should delete file
        action_str = f'<action command="delete" search="file" type="f" path="{filename}" />'
        self._test_action_str(action_str)
        self.assertNotExists(filename)

        # should delete file
        common.touch_file(filename)
        action_str = f'<action command="delete" search="file" path="{filename}" />'
        self._test_action_str(action_str)
        self.assertNotExists(filename)

        # should not delete anything
        action_str = f'<action command="delete" search="file" type="f" path="{dirname}" />'
        self._test_action_str(action_str)
        self.assertExists(dirname)

        # should delete directory
        action_str = f'<action command="delete" search="file" type="d" path="{dirname}" />'
        self._test_action_str(action_str)
        self.assertNotExists(dirname)

    def test_walk_all_top(self):
        """Unit test for walk.all and walk.top"""

        variants = ('all', 'top')
        for variant in variants:
            dirname = self.mkdtemp(prefix=f'bleachbit-walk-{variant}')

            # this sub-directory should be deleted
            subdir = os.path.join(dirname, 'sub')
            os.mkdir(subdir)
            self.assertExists(subdir)

            # this file should be deleted too
            filename = os.path.join(subdir, 'file')
            common.touch_file(filename)

            action_str = f'<action command="delete" search="walk.{variant}" path="{dirname}" />'
            self._test_action_str(action_str)
            self.assertNotExists(subdir)
            if variant == 'all':
                self.assertExists(dirname)
                os.rmdir(dirname)
            elif variant == 'top':
                self.assertNotExists(dirname)

            # If the path does not exist, it should be silently ignored.
            # The top directory no long exists, so just replay it.
            self._test_action_str(action_str, False)

    def test_walk_files(self):
        """Unit test for walk.files"""
        path = r'$WINDIR\system32' if IS_WINDOWS else '/var'

        action_str = f'<action command="delete" search="walk.files" path="{path}" />'
        results = 0
        for cmd in _action_str_to_commands(action_str):
            result = next(cmd.execute(False))
            common.validate_result(self, result)
            path = result['path']
            self.assertFalse(os.path.isdir(path), f'{path} is a directory')
            results += 1
        self.assertGreater(results, 0)

    def test_walk_files_cache_survives_early_abandon(self):
        """An abandoned walk.files generator must not poison the cache"""
        dirname = self.mkdtemp(prefix='bleachbit-walk-cache')
        filenames = [os.path.join(dirname, f'file{i}') for i in range(3)]
        for filename in filenames:
            common.touch_file(filename)

        action_str = f'<action command="delete" search="walk.files" path="{dirname}" />'

        # Abandon after the first result, like Cleaner.auto_hide() does
        commands = _action_str_to_commands(action_str)
        next(commands)
        del commands

        # A fresh walk of the same path must still see every file
        results = [next(cmd.execute(False))['path']
                  for cmd in _action_str_to_commands(action_str)]
        self.assertEqual(sorted(results), sorted(filenames))

    def test_package_manager_missing(self):
        """Unit test for when package manager is not installed"""
        with mock.patch('bleachbit.Language.setup_translation', return_value=None), \
                mock.patch('bleachbit.FileUtilities.exe_exists', return_value=False), \
                mock.patch('bleachbit.Unix.exe_exists', return_value=False):
            # APT is excluded because it includes walk.all.
            for cleaner_name in ['snap', 'pacman', 'yum', 'dnf']:
                # Reset run_external mock for each test.
                with self.subTest(cleaner_name=cleaner_name), mock.patch('bleachbit.General.run_external') as mock_run_external:
                    cleaner = CleanerML(
                        f'cleaners/{cleaner_name}.xml').get_cleaner()
                    # Cleaner remains usable because the action is registered, but it should auto-hide.
                    self.assertEqual(IS_LINUX, cleaner.is_usable())
                    self.assertTrue(cleaner.auto_hide())
                    mock_run_external.assert_not_called()


def main():
    """Main function"""
    if 1 < len(sys.argv) and 'benchmark' == sys.argv[1]:
        for this_filter in ['none', 'regex']:
            rates = []
            iterations = 1
            if 3 == len(sys.argv):
                iterations = int(sys.argv[2])
            for _x in range(0, iterations):
                rate = benchmark_filter(this_filter)
                rates.append(rate)
            # combine all the rates for easy copy and paste into R for analysis
            print(
                f'rates for filter {this_filter}={",".join([str(rate) for rate in rates])}')
        sys.exit()
    unittest.main()


if __name__ == '__main__':
    main()
