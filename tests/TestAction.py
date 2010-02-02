# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Test cases for module Action
"""



import sys
import tempfile
import unittest
from xml.dom.minidom import parseString

sys.path.append('.')
from bleachbit.Action import *

import common



class ActionTestCase(unittest.TestCase):
    """Test cases for Action"""


    def _action_str_to_commands(self, action_str):
        """Parse <action> and return commands"""
        dom = parseString(action_str)
        action_node = dom.childNodes[0]
        delete = Delete(action_node)
        for cmd in delete.get_commands():
            yield cmd


    def _action_str_to_result(self, action_str):
        """Parse <action> and return result"""
        cmd = self._action_str_to_commands(action_str).next()
        result = cmd.execute(False).next()
        return result


    def _test_action_str(self, action_str):
        """Parse <action> and test it"""
        dom = parseString(action_str)
        action_node = dom.childNodes[0]
        command = action_node.getAttribute('command')
        filename = action_node.getAttribute('path')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(action_node)
        self.assertNotEqual(provider, None)
        for cmd in provider.get_commands():
            self.assert_(isinstance(cmd, Command.Delete))
            self.assert_(os.path.lexists(filename))
            # preview
            result = cmd.execute(really_delete = False).next()
            common.validate_result(self, result)
            self.assertNotEqual('/', result['path'])
            # delete
            result = cmd.execute(really_delete = True).next()
            if 'delete' == command:
                self.assert_(not os.path.lexists(filename))
            elif 'truncate' == command:
                self.assert_(os.path.lexists(filename))
                os.remove(filename)
                self.assert_(not os.path.lexists(filename))
            else:
                raise RuntimeError("Unknown command '%s'" % command)


    def test_delete(self):
        """Unit test for class Delete"""
        for path in ('~', '$HOME'):
            for command in ('delete', 'truncate'):
                expanded = os.path.expanduser(os.path.expandvars(path))
                (fd, filename) = tempfile.mkstemp(dir = expanded)
                os.close(fd)
                action_str = '<action command="%s" search="file" path="%s" />' % \
                    (command, filename)
                self._test_action_str(action_str)


    def test_regex(self):
        """Unit test for regex option"""
        _iglob = glob.iglob
        glob.iglob = lambda x: ['/tmp/foo1', '/tmp/foo2']
        _getsize = FileUtilities.getsize
        FileUtilities.getsize = lambda x: 1
        # return regex match
        action_str = '<action command="delete" search="glob" path="/tmp/foo" regex="^foo2$"/>'
        result = self._action_str_to_result(action_str)
        self.assert_(result['path'], '/tmp/foo2')
        # return nothing
        action_str = '<action command="delete" search="glob" path="/tmp/foo" regex="^bar$"/>'
        self.assertRaises(StopIteration, lambda : self._action_str_to_result(action_str))
        # expect error
        action_str = '<action command="delete" search="invalid" path="/tmp/foo" regex="^bar$"/>'
        self.assertRaises(RuntimeError, lambda : self._action_str_to_result(action_str))
        # clean up
        glob.iglob = _iglob
        FileUtilities.getsize = _getsize

    def test_walk_files(self):
        """Unit test for walk.files"""
        if 'posix' == os.name:
            path = '/var'
        elif 'nt' == os.name:
            path = '$WINDIR\\system32'
        action_str = '<action command="delete" search="walk.files" path="%s" />' % path
        results = 0
        for cmd in self._action_str_to_commands(action_str):
            result = cmd.execute(False).next()
            common.validate_result(self, result)
            path = result['path']
            self.assert_(not os.path.isdir(path), \
                "%s is a directory" % path)
            results += 1
        self.assert_(results > 0)


def suite():
    return unittest.makeSuite(ActionTestCase)


if __name__ == '__main__':
    unittest.main()

