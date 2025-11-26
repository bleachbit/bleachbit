# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
Actions that perform cleaning
"""

# standard imports
import glob
import logging
import os
import re
from itertools import product

# first party imports
from bleachbit import Command, FileUtilities, General, Special, DeepScan
from bleachbit import fs_scan_re_flags
from bleachbit.Language import get_text as _

if os.name == 'posix':
    from bleachbit import Unix

if os.name == 'nt':
    from bleachbit import Windows

logger = logging.getLogger(__name__)


def has_glob(s):
    """Checks whether the string contains any glob characters"""
    return re.search(r'[?*\[\]]', s) is not None


def expand_multi_var(s, variables):
    """Expand strings with potentially-multiple values.

    The placeholder is written in the format $$foo$$.

    The function always returns a list of one or more strings.
    """
    if not variables or s.find('$$') == -1:
        # The input string is missing $$ or no variables are given.
        return (s,)
    var_keys_used = []
    ret = []
    for var_key in variables.keys():
        sub = f'$${var_key}$$'
        if s.find(sub) > -1:
            var_keys_used.append(var_key)
    if not var_keys_used:
        # No matching variables used, so return input string unmodified.
        return (s,)
    # filter the dictionary to the keys used
    vars_used = {key: value for key,
                 value in variables.items() if key in var_keys_used}
    # create a product of combinations
    vars_product = (dict(zip(vars_used, x))
                    for x in product(*vars_used.values()))
    for var_set in vars_product:
        ms = s  # modified version of input string
        for var_key, var_value in var_set.items():
            sub = f'$${var_key}$$'
            ms = ms.replace(sub, var_value)
        ret.append(ms)
    if ret:
        return ret
    # The string has $$, but it did not match anything
    return (s,)

#
# Plugin framework
# http://martyalchin.com/2008/jan/10/simple-plugin-framework/
#


class PluginMount(type):

    """A simple plugin framework"""

    def __init__(cls, _name, _bases, _attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)


class ActionProvider(metaclass=PluginMount):

    """Abstract base class for performing individual cleaning actions"""

    def __init__(self, action_node, path_vars=None):
        """Create ActionProvider from CleanerML <action>"""

    def get_deep_scan(self):
        """Return a dictionary used to construct a deep scan"""
        raise StopIteration

    def get_commands(self):
        """Yield each command (which can be previewed or executed)"""


#
# base class
#
class FileActionProvider(ActionProvider):

    """Base class for providers which work on individual files"""
    action_key = '_file'
    CACHEABLE_SEARCHERS = ('walk.files',)
    # global cache <search_type, path, list_of_entries>
    cache = ('nothing', '', tuple())

    def __init__(self, action_element, path_vars=None):
        """Initialize file search"""
        ActionProvider.__init__(self, action_element, path_vars)
        self.regex = action_element.getAttribute('regex')
        assert (isinstance(self.regex, (str, type(None))))
        self.nregex = action_element.getAttribute('nregex')
        assert (isinstance(self.nregex, (str, type(None))))
        self.wholeregex = action_element.getAttribute('wholeregex')
        assert (isinstance(self.wholeregex, (str, type(None))))
        self.nwholeregex = action_element.getAttribute('nwholeregex')
        assert (isinstance(self.nwholeregex, (str, type(None))))
        self.search = action_element.getAttribute('search')
        self.object_type = action_element.getAttribute('type')
        self._set_paths(action_element.getAttribute('path'), path_vars)
        self.ds = None
        if 'deep' == self.search:
            self.ds = (self.paths[0], DeepScan.Search(
                command=action_element.getAttribute('command'),
                regex=self.regex, nregex=self.nregex,
                wholeregex=self.wholeregex, nwholeregex=self.nwholeregex))
            if len(self.paths) != 1:
                logger.warning(
                    # TRANSLATORS: Multi-value variables are explained
                    # in the online documentation. Basically, they are like
                    # an environment variable, but each multi-value variable
                    # can have multiple values. They're a way to make CleanerML
                    # files more concise.
                    _("Deep scan does not support multi-value variable."))
        if not any([self.object_type, self.regex, self.nregex,
                    self.wholeregex, self.nwholeregex]):
            # If the filter is not needed, bypass it for speed.
            self.get_paths = self._get_paths

    def _set_paths(self, raw_path, path_vars):
        """Set the list of paths to work on"""
        self.paths = []
        # expand special $$foo$$ which may give multiple values
        for path2 in expand_multi_var(raw_path, path_vars):
            path3 = os.path.expanduser(os.path.expandvars(path2))
            if os.name == 'nt' and path3:
                # convert forward slash to backslash for compatibility with getsize()
                # and for display.  Do not convert an empty path, or it will become
                # the current directory (.).
                path3 = os.path.normpath(path3)
            self.paths.append(path3)

    def get_deep_scan(self):
        if self.ds is None:
            return
        yield self.ds

    def get_paths(self):
        """Process the filters: regex, nregex, type

        If a filter is defined and it fails to match, this function
        returns False. Otherwise, this function returns True."""

        # optimize tight loop, avoid slow python "."
        regex = self.regex
        nregex = self.nregex
        wholeregex = self.wholeregex
        nwholeregex = self.nwholeregex
        basename = os.path.basename
        object_type = self.object_type
        if self.regex:
            regex_c_search = re.compile(self.regex, fs_scan_re_flags).search
        else:
            regex_c_search = None

        if self.nregex:
            nregex_c_search = re.compile(self.nregex, fs_scan_re_flags).search
        else:
            nregex_c_search = None

        if self.wholeregex:
            wholeregex_c_search = re.compile(
                self.wholeregex, fs_scan_re_flags).search
        else:
            wholeregex_c_search = None

        if self.nwholeregex:
            nwholeregex_c_search = re.compile(
                self.nwholeregex, fs_scan_re_flags).search
        else:
            nwholeregex_c_search = None

        for path in self._get_paths():
            if regex and not regex_c_search(basename(path)):
                continue

            if nregex and nregex_c_search(basename(path)):
                continue

            if wholeregex and not wholeregex_c_search(path):
                continue

            if nwholeregex and nwholeregex_c_search(path):
                continue

            if object_type:
                if 'f' == object_type and not os.path.isfile(path):
                    continue
                elif 'd' == object_type and not os.path.isdir(path):
                    continue

            yield path

    def _get_paths(self):
        """Return a filtered list of files"""

        def get_file(path):
            if os.path.lexists(path):
                yield path

        def get_walk_all(top):
            """Delete files and directories inside a directory but not the top directory"""
            for expanded in glob.iglob(top):
                path = None  # sentinel value
                yield from FileUtilities.children_in_directory(expanded, True)
                # This condition executes when there are zero iterations
                # in the loop above.
                if path is None:
                    # This is a lint checker because this scenario may
                    # indicate the cleaner developer made a mistake.
                    if os.path.isfile(expanded):
                        logger.debug(
                            # TRANSLATORS: This is a lint-style warning that there seems to be a
                            # mild mistake in the CleanerML file because walk.all is expected to
                            # be used with directories instead of with files. Do not translate
                            # search="walk.all" and path="%s"
                            _('search="walk.all" used with regular file path="%s"'),
                            expanded,
                        )

        def get_walk_files(top):
            """Delete files inside a directory but not any directories"""
            for expanded in glob.iglob(top):
                yield from FileUtilities.children_in_directory(expanded, False)

        def get_top(top):
            """Delete directory contents and the directory itself"""
            yield from get_walk_all(top)
            if os.path.exists(top):
                yield top

        if 'deep' == self.search:
            return

        search_functions = {
            'file': get_file,
            'glob': glob.iglob,
            'walk.all': get_walk_all,
            'walk.files': get_walk_files,
            'walk.top': get_top
        }

        if self.search not in search_functions:
            raise RuntimeError(f"Invalid search='{self.search}'")

        func = search_functions[self.search]

        cache = self.__class__.cache
        for input_path in self.paths:
            if self.search == 'glob' and not has_glob(input_path):
                # TRANSLATORS: This is a lint-style warning that the CleanerML file
                # specified a search for glob, but the path specified didn't have any
                # wildcard patterns. Therefore, maybe the developer either missed
                # the wildcard or should search using path="file" which does not
                # expect or support wildcards in the path.
                logger.debug(_('path="%s" is not a glob pattern'), input_path)

            # use cache
            if self.search in self.CACHEABLE_SEARCHERS and cache[0] == self.search and cache[1] == input_path:
                # logger.debug(_('using cached walk for path %s'), input_path)
                for x in cache[2]:
                    yield x
                return
            # if self.search in self.CACHEABLE_SEARCHERS:
            #    logger.debug('not using cache because it has (%s,%s) and we want (%s,%s)',
            #                 cache[0], cache[1], self.search, input_path)
            self.__class__.cache = ('cleared by', input_path, tuple())

            # build new cache
            # logger.debug('%s walking %s', id(self), input_path)

            if self.search in self.CACHEABLE_SEARCHERS:
                cache = self.__class__.cache = (self.search, input_path, [])
                for path in func(input_path):
                    cache[2].append(path)
                    yield path
            else:
                for path in func(input_path):
                    yield path

    def get_commands(self):
        raise NotImplementedError('not implemented')


#
# Action providers
#


class AptAutoclean(ActionProvider):

    """Action to run 'apt-get autoclean'"""
    action_key = 'apt.autoclean'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        assert os.name == 'posix'
        # If apt-get is not installed, then enable fast auto-hide.
        # The exe_exists() function is fast.
        if not FileUtilities.exe_exists('apt-get'):
            return
        yield Command.Function(None,
                               # pylint: disable=possibly-used-before-assignment
                               Unix.apt_autoclean,
                               'apt-get autoclean')


class AptAutoremove(ActionProvider):

    """Action to run 'apt-get autoremove'"""
    action_key = 'apt.autoremove'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        if not FileUtilities.exe_exists('apt-get'):
            return
        yield Command.Function(None,
                               Unix.apt_autoremove,
                               'apt-get autoremove')


class AptClean(ActionProvider):

    """Action to run 'apt-get clean'"""
    action_key = 'apt.clean'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        if not FileUtilities.exe_exists('apt-get'):
            return
        yield Command.Function(None,
                               Unix.apt_clean,
                               'apt-get clean')


class ChromeAutofill(FileActionProvider):

    """Action to clean 'autofill' table in Google Chrome/Chromium"""
    action_key = 'chrome.autofill'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_autofill,
                _('Clean file'))


class ChromeDatabases(FileActionProvider):

    """Action to clean Databases.db in Google Chrome/Chromium"""
    action_key = 'chrome.databases_db'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_databases_db,
                _('Clean file'))


class ChromeFavicons(FileActionProvider):

    """Action to clean 'Favicons' file in Google Chrome/Chromium"""
    action_key = 'chrome.favicons'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_favicons,
                _('Clean file'))


class ChromeHistory(FileActionProvider):

    """Action to clean 'History' file in Google Chrome/Chromium"""
    action_key = 'chrome.history'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_history,
                _('Clean file'))


class ChromeKeywords(FileActionProvider):

    """Action to clean 'keywords' table in Google Chrome/Chromium"""
    action_key = 'chrome.keywords'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_keywords,
                _('Clean file'))


class Delete(FileActionProvider):

    """Action to delete files"""
    action_key = 'delete'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Delete(path)


class Ini(FileActionProvider):

    """Action to clean .ini configuration files"""
    action_key = 'ini'

    def __init__(self, action_element, path_vars=None):
        FileActionProvider.__init__(self, action_element, path_vars)
        self.section = action_element.getAttribute('section')
        self.parameter = action_element.getAttribute('parameter')
        if self.parameter == "":
            self.parameter = None

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Ini(path, self.section, self.parameter)


class Journald(ActionProvider):
    """Action to run 'journalctl --vacuum-time=1'"""
    action_key = 'journald.clean'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        # If journalctl is not installed, then enable fast auto-hide.
        if not FileUtilities.exe_exists('journalctl'):
            return
        yield Command.Function(None, Unix.journald_clean, 'journalctl --vacuum-time=1')


class Json(FileActionProvider):

    """Action to clean JSON configuration files"""
    action_key = 'json'

    def __init__(self, action_element, path_vars=None):
        FileActionProvider.__init__(self, action_element, path_vars)
        self.address = action_element.getAttribute('address')

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Json(path, self.address)


class MozillaUrlHistory(FileActionProvider):

    """Action to clean Mozilla (Firefox) URL history in places.sqlite"""
    action_key = 'mozilla.url.history'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(path,
                                   Special.delete_mozilla_url_history,
                                   _('Clean file'))


class MozillaFavicons(FileActionProvider):

    """Action to clean Mozilla (Firefox) URL history in places.sqlite"""
    action_key = 'mozilla.favicons'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(path,
                                   Special.delete_mozilla_favicons,
                                   _('Clean file'))


class OfficeRegistryModifications(FileActionProvider):

    """Action to delete LibreOffice history"""
    action_key = 'office_registrymodifications'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_office_registrymodifications,
                _('Clean'))


class Process(ActionProvider):

    """Action to run a process"""
    action_key = 'process'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)
        self.cmd = os.path.expandvars(action_element.getAttribute('cmd'))
        # by default, wait
        self.wait = True
        wait = action_element.getAttribute('wait')
        if wait and wait.lower()[0] in ('f', 'n'):
            # false or no
            self.wait = False

    def get_commands(self):

        def run_process():
            try:
                args = General.shell_split(self.cmd)
                (rc, stdout, stderr) = General.run_external(args, wait=self.wait)
            except Exception as e:
                raise RuntimeError(
                    f'Exception in external command\nCommand: {args}\nError: {str(e)}') from e
            if self.wait and 0 != rc:
                logger.warning('Command: %s\nReturn code: %d\nStdout: %s\nStderr: %s\n',
                               args, rc, stdout, stderr)
            return 0
        yield Command.Function(path=None, func=run_process,
                               label=_("Run external command: %s") % self.cmd)


class Shred(FileActionProvider):

    """Action to shred files (override preference)"""
    action_key = 'shred'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Shred(path)


class SqliteVacuum(FileActionProvider):

    """Action to vacuum SQLite databases"""
    action_key = 'sqlite.vacuum'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                FileUtilities.vacuum_sqlite3,
                # TRANSLATORS: Vacuum is a verb.  The term is jargon
                # from the SQLite database.  Microsoft Access uses
                # the term 'Compact Database' (which you may translate
                # instead).  Another synonym is 'defragment.'
                _('Vacuum'))


class Truncate(FileActionProvider):

    """Action to truncate files"""
    action_key = 'truncate'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Truncate(path)


class WinShellChangeNotify(ActionProvider):

    """Action to clean the Windows Registry"""
    action_key = 'win.shell.change.notify'

    def get_commands(self):
        assert os.name == 'nt'
        yield Command.Function(
            None,
            # pylint: disable=possibly-used-before-assignment
            Windows.shell_change_notify,
            _('Refresh Windows shell'))


class Winreg(ActionProvider):

    """Action to clean the Windows Registry"""
    action_key = 'winreg'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)
        self.keyname = action_element.getAttribute('path')
        self.name = action_element.getAttribute('name')

    def get_commands(self):
        yield Command.Winreg(self.keyname, self.name)


class YumCleanAll(ActionProvider):

    """Action to run 'yum clean all'"""
    action_key = 'yum.clean_all'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        # If yum is not installed, then enable fast auto-hide.
        if not FileUtilities.exe_exists('yum'):
            return

        yield Command.Function(
            None,
            Unix.yum_clean,
            'yum clean all')


class DnfCleanAll(ActionProvider):

    """Action to run 'dnf clean all'"""
    action_key = 'dnf.clean_all'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        # If dnf is not installed, then enable fast auto-hide.
        if not FileUtilities.exe_exists('dnf'):
            return

        yield Command.Function(
            None,
            Unix.dnf_clean,
            'dnf clean all')


class DnfAutoremove(ActionProvider):

    """Action to run 'dnf autoremove'"""
    action_key = 'dnf.autoremove'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        # If dnf is not installed, then enable fast auto-hide.
        if not FileUtilities.exe_exists('dnf'):
            return

        yield Command.Function(
            None,
            Unix.dnf_autoremove,
            'dnf autoremove')


class PacmanCache(ActionProvider):

    """Action to run `paccache -rk0'"""
    action_key = 'pacman.cache'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        if not FileUtilities.exe_exists('paccache'):
            return

        yield Command.Function(
            None,
            Unix.pacman_cache,
            'paccache -rk0')


class SnapDisabled(ActionProvider):

    """Action to remove disabled snaps"""
    action_key = 'snap.disabled'

    def __init__(self, action_element, path_vars=None):
        ActionProvider.__init__(self, action_element, path_vars)

    def get_commands(self):
        # If snap is not installed, then enable fast auto-hide.
        if not FileUtilities.exe_exists('snap'):
            return
        yield Command.Function(
            None,
            Unix.snap_disabled_clean,
            'snap remove disabled',
            preview_func=Unix.snap_disabled_preview)
