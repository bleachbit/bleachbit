# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
Actions that perform cleaning
"""

import glob
import os
import sys

import globals
from FileUtilities import children_in_directory

if 'win32' == sys.platform:
    import Windows


class Action:
    """Generic cleaning action"""

    def __init__(self):
        """Initialize"""
        self.actions = []


    def add_list_children(self, pathname, list_directories = False):
        """Add action to list children of 'pathname'"""
        self.actions += ( ('list_children', pathname, list_directories), )


    def add_list_file(self, pathname):
        """Add action to list 'pathname'"""
        self.actions += ( ('list_file', pathname), )


    def add_list_glob(self, pathname):
        """Add action to list files by glob of 'pathname'"""
        self.actions += ( ('list_glob', pathname), )


    def add_windows_registry(self, key, name = None):
        """Add action to delete a Windows registry key or named value"""
        self.actions += ( ('winreg', key, name), )


    def list_files(self):
        """List files by previously-defined actions
        (those actions which list files for deletion)"""
        for action in self.actions:
            action_type = action[0]
            action_path = os.path.expanduser(os.path.expandvars(action[1]))
            if 'list_children' == action_type:
                rootpath = action_path
                directories = action[2]
                for pathname in children_in_directory(rootpath, directories):
                    yield pathname
            elif 'list_file' == action_type:
                pathname = action_path
                if os.path.lexists(pathname):
                    yield pathname
            elif 'list_glob' == action_type:
                for pathname in glob.iglob(action_path):
                  yield pathname
            elif 'winreg' == action_type:
                pass
            else:
                raise RuntimeError("Unknown action type: '%s'" % action_type)


    def other_cleanup(self, really_delete = False):
        """List special operations by previously-defined actions"""
        for action in self.actions:
            action_type = action[0]
            action_path = os.path.expanduser(os.path.expandvars(action[1]))
            if action_type in ('list_children', 'list_file', 'list_glob'):
                pass
            elif 'winreg' == action_type:
                key = action[1]
                name = None
                if len(action) > 2:
                    name = action[2]
                str = None # string representation
                ret = None # return value meaning 'deleted' or 'delete-able'
                if name:
                    str = '%s<%s>' % (key, name)
                    ret = Windows.delete_registry_value(key, name, really_delete)
                else:
                    ret = Windows.delete_registry_key(key, really_delete)
                    str = key
                if not ret:
                    # nothing to delete or nothing was deleted
                    return
                if really_delete:
                    yield (0, str)
                else:
                    yield str
            else:
                raise RuntimeError("Unknown action type: '%s'" % action_type)


import unittest

class TestAction(unittest.TestCase):

    def test_Action(self):
        action = Action()
        action.add_list_children('/bin')
        action.add_list_children('/sbin')
        action.add_list_file('~/.bash_history')
        action.add_list_glob('/sbin/fsck*')
        for pathname in action.list_files():
            self.assert_(os.path.lexists(pathname))


if __name__ == '__main__':
    unittest.main()

