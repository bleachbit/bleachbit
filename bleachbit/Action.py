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

import FileUtilities
import General

if 'linux2' == sys.platform:
    import Unix

if 'win32' == sys.platform:
    import Windows



###
### Plugin framework
### http://martyalchin.com/2008/jan/10/simple-plugin-framework/
###

class PluginMount(type):
    """A simple plugin framework"""


    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)



class ActionProvider:
    """Abstract base class for performing individual cleaning actions"""
    __metaclass__ = PluginMount


    def __init__(self, action_node):
        """Create ActionProvider from CleanerML <action>"""
        pass


    def list_files(self):
        """Yield each pathname to be deleted"""
        raise StopIteration


    def other_cleanup(self, really_delete):
        """Perform specialized cleanup (more complex than deleting a file)"""
        raise StopIteration



###
### Action providers
###


class AptAutoclean(ActionProvider):
    """Action to run 'apt-get autoclean'"""
    action_key = 'apt.autoclean'


    def __init__(self, action_element):
        pass


    def other_cleanup(self, really_delete):
        if really_delete:
            yield (Unix.apt_autoclean(), "apt-get autoclean")
        else:
            # Checking allows auto-hide to work for non-APT systems
            if FileUtilities.exe_exists('apt-get'):
                yield "apt-get autoclean"


class AptAutoremove(ActionProvider):
    """Action to run 'apt-get autoremove'"""
    action_key = 'apt.autoremove'


    def __init__(self, action_element):
        pass


    def other_cleanup(self, really_delete):
        if really_delete:
            yield (Unix.apt_autoremove(), "apt-get autoremove")
        else:
            # Checking allows auto-hide to work for non-APT systems
            if FileUtilities.exe_exists('apt-get'):
                yield "apt-get autoremove"


class Children(ActionProvider):
    """Action to list a directory"""
    action_key = 'children'


    def __init__(self, action_element):
        self.rootpath = General.getText(action_element.childNodes)
        self.rootpath = os.path.expanduser(os.path.expandvars(self.rootpath))
        del_dir_str = action_element.getAttribute('directories')
        self.del_dir = General.boolstr_to_bool(del_dir_str)


    def list_files(self):
        for pathname in FileUtilities.children_in_directory(self.rootpath, self.del_dir):
            yield pathname



class File(ActionProvider):
    """Action to list a single file"""
    action_key = 'file'


    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)


    def list_files(self):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        if os.path.lexists(expanded):
            yield expanded



class Glob(ActionProvider):
    """Action to list files by Unix-shell-like glob"""
    action_key = 'glob'


    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)


    def list_files(self):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        for pathname in glob.iglob(expanded):
            yield pathname



class SqliteVacuum(ActionProvider):
    """Action to vacuum SQLite databases"""
    action_key = 'sqlite.vacuum'

    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)


    def other_cleanup(self, really_delete):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        for pathname in glob.iglob(expanded):
            if really_delete:
                old_size = FileUtilities.getsize(pathname)
                FileUtilities.vacuum_sqlite3(pathname)
                new_size = FileUtilities.getsize(pathname)
                # TRANSLATORS: Vacuumed may also be translated 'compacted'
                # or 'optimized.'  The '%s' is a file name.
                yield (old_size - new_size, _("Vacuumed: %s") % pathname)
            else:
                yield _("Vacuumed: %s") % pathname



class Winreg(ActionProvider):
    """Action to clean the Windows Registry"""
    action_key = 'winreg'

    def __init__(self, action_element):
        self.keyname = General.getText(action_element.childNodes)
        self.name = action_element.getAttribute('name')


    def other_cleanup(self, really_delete):
        name = None
        _str = None # string representation
        ret = None # return value meaning 'deleted' or 'delete-able'
        if name:
            _str = '%s<%s>' % (self.keyname, name)
            ret = Windows.delete_registry_value(self.keyname, name, really_delete)
        else:
            ret = Windows.delete_registry_key(self.keyname, really_delete)
            _str = self.keyname
        if not ret:
            # nothing to delete or nothing was deleted
            return
        if really_delete:
            yield (0, _str)
        else:
            yield _str


###
### ActionContainer class
###

class ActionContainer:
    """Generic cleaning action which may execute multiple
       action providers"""


    def __init__(self):
        """Initialize"""
        self.providers = []


    def add_action_provider(self, actionprovider):
        """Add action provider"""
        self.providers += ( actionprovider, )


    def list_files(self):
        """List files by previously-defined actions
        (those actions which list files for deletion)"""
        for provider in self.providers:
            for pathname in provider.list_files():
                yield pathname


    def other_cleanup(self, really_delete = False):
        """List special operations by previously-defined actions"""
        for provider in self.providers:
            for ret in provider.other_cleanup(really_delete):
                yield ret


import unittest

class TestAction(unittest.TestCase):
    """Test case for module Action"""


    def setUp(self):
        """Prepare for unit tests"""
        self.actions = []
        if 'linux2' == sys.platform:
            self.actions.append('<action type="file">~/.bash_history</action>')
            self.actions.append('<action type="glob">/sbin/*sh</action>')
            self.actions.append('<action type="children" directories="false">/sbin/</action>')
            self.actions.append('<action type="children" directories="true">/var/log/</action>')
        if 'win32' == sys.platform:
            self.actions.append('<action type="file">$WINDIR\\notepad.exe</action>')
            self.actions.append('<action type="glob">$WINDIR\\system32\\*.dll</action>')
            self.actions.append( \
                '<action type="children" directories="false">$WINDIR\\system\\</action>')
            self.actions.append( \
                '<action type="children" directories="true">$WINDIR\\system32\\</action>')

        self.assert_(len(self.actions) > 0)


    def test_ActionContainer(self):
        """Test class ActionContainer"""
        from xml.dom.minidom import parseString
        for action_str in self.actions:
            container = ActionContainer()
            dom = parseString(action_str)
            action_node = dom.childNodes[0]
            atype = action_node.getAttribute('type')
            provider = None
            for actionplugin in ActionProvider.plugins:
                if actionplugin.action_key == atype:
                    provider = actionplugin(action_node)
            container.add_action_provider(provider)
            pathname = container.list_files().next()
            self.assert_(os.path.lexists(pathname), "Does not exist: '%s'" % pathname)
            for pathname in container.list_files():
                self.assert_(os.path.lexists(pathname), "Does not exist: '%s'" % pathname)
            for pathname in container.other_cleanup(really_delete = False):
                self.assert_(type(pathname) is str)


if __name__ == '__main__':
    unittest.main()

