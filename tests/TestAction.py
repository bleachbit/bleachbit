# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2015 Andrew Ziem
# http://bleachbit.sourceforge.net
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


import shutil
import sys
import tempfile
import unittest
from xml.dom.minidom import parseString

sys.path.append('.')
from bleachbit.Action import *

import common


def _action_str_to_commands(action_str):
    """Parse <action> and return commands"""
    dom = parseString(action_str)
    action_node = dom.childNodes[0]
    delete = Delete(action_node)
    for cmd in delete.get_commands():
        yield cmd


def _action_str_to_results(action_str):
    """Parse <action> and return list of results"""
    return [cmd.execute(False).next() for cmd in _action_str_to_commands(action_str)]


def benchmark_regex():
    """Measure how fast the regex option is"""
    n_files = 100000
    print 'benchmark of %d files' % n_files

    # make a directory with many files
    dirname = tempfile.mkdtemp(prefix='bleachbit-action-bench')
    for x in xrange(0, n_files):
        common.touch_file(os.path.join(dirname, str(x)))

    # scan directory
    import time
    start = time.time()
    action_str = '<action command="delete" search="glob" path="%s/*" regex="^12$"/>' % dirname
    results = _action_str_to_results(action_str)
    end = time.time()
    elapsed_seconds = end-start
    print 'elapsed: %.2f seconds, %.2f files/second' % (elapsed_seconds, n_files/elapsed_seconds)

    # clean up
    shutil.rmtree(dirname)


def dir_is_empty(dirname):
    """Check whether a directory is empty"""
    return not os.listdir(dirname)


class ActionTestCase(unittest.TestCase):

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
            self.assert_(
                isinstance(cmd, (Command.Delete, Command.Ini, Command.Json)))
            self.assert_(os.path.lexists(filename))
            # preview
            result = cmd.execute(really_delete=False).next()
            common.validate_result(self, result)
            self.assertNotEqual('/', result['path'])
            # delete
            ret = cmd.execute(really_delete=True).next()
            if 'delete' == command:
                self.assert_(not os.path.lexists(cmd.path),
                             'exists: %s' % cmd.path)
            elif 'truncate' == command:
                self.assert_(os.path.lexists(filename))
                os.remove(filename)
                self.assert_(not os.path.lexists(filename))
            elif command in ('ini', 'json'):
                self.assert_(os.path.lexists(filename))
            else:
                raise RuntimeError("Unknown command '%s'" % command)
        if 'walk.all' == search:
            self.assert_(dir_is_empty(filename),
                         'directory not empty after walk.all: %s' % filename)

    def test_delete(self):
        """Unit test for class Delete"""
        paths = ['~']
        if 'nt' == os.name:
            if sys.version_info[0] == 2 and sys.version_info[1] > 5:
                # Python 2.6 and later supports %
                paths.append('%USERPROFILE%')
            paths.append('${USERPROFILE}')
            paths.append('$USERPROFILE')
        if 'posix' == os.name:
            paths.append('$HOME')
        for path in paths:
            for mode in ('delete', 'truncate', 'delete_forward'):
                expanded = os.path.expanduser(os.path.expandvars(path))
                (fd, filename) = tempfile.mkstemp(
                    dir=expanded, prefix='bleachbit-action-delete')
                os.close(fd)
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
                action_str = '<action command="%s" search="file" path="%s" />' % \
                    (command, filename)
                self._test_action_str(action_str)
                self.assert_(not os.path.exists(filename))

    def test_ini(self):
        """Unit test for class Ini"""
        from TestFileUtilities import test_ini_helper

        def execute_ini(path, section, parameter):
            effective_parameter = ""
            if None != parameter:
                effective_parameter = 'parameter="%s"' % parameter
            action_str = '<action command="ini" search="file" path="%s" section="%s" %s />' \
                % (path, section, effective_parameter)
            self._test_action_str(action_str)

        test_ini_helper(self, execute_ini)

    def test_json(self):
        """Unit test for class Json"""
        from TestFileUtilities import test_json_helper

        def execute_json(path, address):
            action_str = '<action command="json" search="file" path="%s" address="%s" />' \
                % (path, address)
            self._test_action_str(action_str)

        test_json_helper(self, execute_json)

    def test_regex(self):
        """Unit test for regex option"""
        _iglob = glob.iglob
        glob.iglob = lambda x: ['/tmp/foo1', '/tmp/foo2']
        _getsize = FileUtilities.getsize
        FileUtilities.getsize = lambda x: 1

        # should match second file using positive regex
        action_str = '<action command="delete" search="glob" path="/tmp/foo" regex="^foo2$"/>'
        results = _action_str_to_results(action_str)
        self.assert_(1 == len(results))
        self.assertEqual(results[0]['path'], '/tmp/foo2')

        # should match nothing
        action_str = '<action command="delete" search="glob" path="/tmp/foo" regex="^bar$"/>'
        results = _action_str_to_results(action_str)
        self.assert_(0 == len(results))

        # should give an error
        action_str = '<action command="delete" search="invalid" path="/tmp/foo" regex="^bar$"/>'
        self.assertRaises(
            RuntimeError, lambda: _action_str_to_results(action_str))
        # clean up
        glob.iglob = _iglob
        FileUtilities.getsize = _getsize

    def test_walk_all(self):
        """Unit test for walk.all"""
        dirname = tempfile.mkdtemp(prefix='bleachbit-walk-all')

        # this sub-directory should be deleted
        subdir = os.path.join(dirname, 'sub')
        os.mkdir(subdir)
        self.assert_(os.path.exists(subdir))

        # this file should be deleted too
        filename = os.path.join(subdir, 'file')
        open(filename, 'a').close()

        action_str = '<action command="delete" search="walk.all" path="%s" />' % dirname
        self._test_action_str(action_str)
        self.assert_(not os.path.exists(subdir))

    def test_walk_files(self):
        """Unit test for walk.files"""
        if 'posix' == os.name:
            path = '/var'
        elif 'nt' == os.name:
            path = '$WINDIR\\system32'
        action_str = '<action command="delete" search="walk.files" path="%s" />' % path
        results = 0
        for cmd in _action_str_to_commands(action_str):
            result = cmd.execute(False).next()
            common.validate_result(self, result)
            path = result['path']
            self.assert_(not os.path.isdir(path),
                         "%s is a directory" % path)
            results += 1
        self.assert_(results > 0)


def suite():
    return unittest.makeSuite(ActionTestCase)


if __name__ == '__main__':
    if 2 == len(sys.argv) and 'benchmark' == sys.argv[1]:
        benchmark_regex()
        sys.exit()
    unittest.main()
