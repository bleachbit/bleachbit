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

import Command
import FileUtilities
import General

if 'posix' == os.name:
    import Unix



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


    def get_commands(self):
        """Yield each command (which can be previewed or executed)"""



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


class Children(ActionProvider):
    """Action to list a directory"""
    action_key = 'children'


    def __init__(self, action_element):
        self.rootpath = General.getText(action_element.childNodes)
        self.rootpath = os.path.expanduser(os.path.expandvars(self.rootpath))
        del_dir_str = action_element.getAttribute('directories')
        self.del_dir = General.boolstr_to_bool(del_dir_str)


    def get_commands(self):
        for pathname in FileUtilities.children_in_directory(self.rootpath, self.del_dir):
            yield Command.Delete(pathname)



class File(ActionProvider):
    """Action to list a single file"""
    action_key = 'file'


    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)


    def get_commands(self):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        if os.path.lexists(expanded):
            yield Command.Delete(expanded)



class Glob(ActionProvider):
    """Action to list files by Unix-shell-like glob"""
    action_key = 'glob'


    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)


    def get_commands(self):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        for pathname in glob.iglob(expanded):
            yield Command.Delete(pathname)



class SqliteVacuum(ActionProvider):
    """Action to vacuum SQLite databases"""
    action_key = 'sqlite.vacuum'

    def __init__(self, action_element):
        self.pathname = General.getText(action_element.childNodes)

    def get_commands(self):
        expanded = os.path.expanduser(os.path.expandvars(self.pathname))
        for pathname in glob.iglob(expanded):
            yield Command.Function( \
                pathname, \
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



