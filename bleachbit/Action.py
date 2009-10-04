# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
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
Actions that perform cleaning
"""



import glob
import os
import unittest
import Command
import FileUtilities
import General

if 'posix' == os.name:
    import Unix



###
### File iterators
###


def get_file(path):
    if os.path.lexists(path):
        yield path


def walk_all(top):
    for path in FileUtilities.children_in_directory(top, True):
        yield path


def walk_files(top):
    for path in FileUtilities.children_in_directory(top, False):
        yield path



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


    def file_init(self, action_node):
        """Initialize file search"""
        search = action_node.getAttribute('search')
        self.path = os.path.expanduser(os.path.expandvars( \
            action_node.getAttribute('path')))
        if 'file' == search:
            self.get_paths = get_file
        elif 'glob' == search:
            self.get_paths = glob.glob
        elif 'walk.all' == search:
            self.get_paths = walk_all
        elif 'walk.files' == search:
            self.get_paths = walk_files
        else:
            raise RuntimeError("invalid search '%s'" % search)


    def get_commands(self):
        """Yield each command (which can be previewed or executed)"""
        pass



    def get_paths(self):
        """Overwritten by file_init()"""
        raise RuntimeError('not initialized')


###
### Action providers
###


class AptAutoclean(ActionProvider):
    """Action to run 'apt-get autoclean'"""
    action_key = 'apt.autoclean'


    def __init__(self, action_element):
        pass


    def get_commands(self):
        # Checking executable allows auto-hide to work for non-APT systems
        if FileUtilities.exe_exists('apt-get'):
            yield Command.Function(None, \
                Unix.apt_autoclean, \
                'apt-get autoclean')


class AptAutoremove(ActionProvider):
    """Action to run 'apt-get autoremove'"""
    action_key = 'apt.autoremove'


    def __init__(self, action_element):
        pass

    def get_commands(self):
        # Checking executable allows auto-hide to work for non-APT systems
        if FileUtilities.exe_exists('apt-get'):
            yield Command.Function(None, \
                Unix.apt_autoremove, \
                'apt-get autoremove')


class Delete(ActionProvider):
    """Action to delete files"""
    action_key = 'delete'


    def __init__(self, action_element):
        self.file_init(action_element)

    def get_commands(self):
        for path in self.get_paths(self.path):
            yield Command.Delete(path)



class SqliteVacuum(ActionProvider):
    """Action to vacuum SQLite databases"""
    action_key = 'sqlite.vacuum'

    def __init__(self, action_element):
        self.file_init(action_element)

    def get_commands(self):
        for path in self.get_paths(self.path):
            yield Command.Function( \
                path, \
                FileUtilities.vacuum_sqlite3, \
                # TRANSLATORS: Vacuum is a verb.  The term is jargon
                # from the SQLite database.  Microsoft Access uses
                # the term 'Compact Database' (which you may translate
                # instead).  Another synonym is 'defragment.'
               _('Vacuum'))


class TestActionProvider(ActionProvider):
    """Test ActionProvider"""
    action_key = 'test'

    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)

    def get_commands(self):
        # non-existent file, should fail and continue
        yield Command.Delete("doesnotexist")

        # access denied, should fail and continue
        def accessdenied():
            raise OSError(13, 'Permission denied: /foo/bar')

        yield Command.Function(None, accessdenied, 'Test access denied')
        # Lock the file on Windows.  It should be marked for deletion.
        if 'nt' == os.name:
            f = os.open(self.pathname, os.O_RDWR | os.O_EXCL)
            yield Command.Delete(self.pathname)
            assert(os.path.exists(self.pathname))
            os.close(f)

        # function with path, should succeed
        def pathfunc(path):
            pass
        # self.pathname must exist because it checks the file size
        yield Command.Function(self.pathname, pathfunc, 'pathfunc')

        # function generator without path, should succeed
        def funcgenerator():
            yield long(10)
        yield Command.Function(None, funcgenerator, 'funcgenerator')

        # plain function without path, should succeed
        def intfunc():
            return int(10)
        yield Command.Function(None, intfunc, 'intfunc')

        # truncate real file
        yield Command.Truncate(self.pathname)

        # real file, should succeed
        yield Command.Delete(self.pathname)


class Winreg(ActionProvider):
    """Action to clean the Windows Registry"""
    action_key = 'winreg'

    def __init__(self, action_element):
        self.keyname = General.getText(action_element.childNodes)
        self.name = action_element.getAttribute('name')


    def get_commands(self):
        yield Command.Winreg(self.keyname, self.name)



class YumCleanAll(ActionProvider):
    """Action to run 'yum clean all'"""
    action_key = 'yum.clean_all'


    def __init__(self, action_element):
        pass

    def get_commands(self):
        # Checking allows auto-hide to work for non-APT systems
        if not FileUtilities.exe_exists('yum'):
            raise StopIteration

        yield Command.Function( \
                None, \
                Unix.yum_clean, \
                'yum clean all')



class TestAction(unittest.TestCase):
    """Test cases for Action"""


    def test_Delete(self):
        """Unit test for class Delete"""
        import Cleaner
        import tempfile
        from xml.dom.minidom import parseString
        for dir in ('~', '$HOME'):
            expanded = os.path.expanduser(os.path.expandvars(dir))
            (fd, filename) = tempfile.mkstemp(dir = expanded)
            os.close(fd)
            action_str = '<action command="delete" search="file" path="%s" />' % filename
            dom = parseString(action_str)
            action_node = dom.childNodes[0]
            command = action_node.getAttribute('command')
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
                Cleaner.TestCleaner.validate_result(self, result)
                # delete
                result = cmd.execute(really_delete = True).next()
                self.assert_(not os.path.lexists(filename))




if __name__ == '__main__':
    unittest.main()

