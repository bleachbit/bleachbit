
# vim: ts=4:sw=4:expandtab

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
Import Winapp2.ini files
"""

import logging
import os
import glob
import re
from xml.dom.minidom import parseString

import bleachbit
from bleachbit import Cleaner, Windows
from bleachbit.Action import Delete, Winreg
from bleachbit.Language import get_text as _

logger = logging.getLogger(__name__)


# TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
langsecref_map = {
    '3001': ('winapp2_internet_explorer', 'Internet Explorer'),
    '3005': ('winapp2_edge_classic', 'Microsoft Edge'),
    '3006': ('winapp2_edge_chromium', 'Microsoft Edge'),
    # TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
    '3021': ('winapp2_applications', _('Applications')),
    # TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
    '3022': ('winapp2_internet', _('Internet')),
    # TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
    '3023': ('winapp2_multimedia', _('Multimedia')),
    # TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
    '3024': ('winapp2_utilities', _('Utilities')),
    '3025': ('winapp2_windows', 'Microsoft Windows'),
    '3026': ('winapp2_mozilla', 'Firefox/Mozilla'),
    '3027': ('winapp2_opera', 'Opera'),
    '3028': ('winapp2_safari', 'Safari'),
    '3029': ('winapp2_google_chrome', 'Google Chrome'),
    '3030': ('winapp2_thunderbird', 'Thunderbird'),
    '3031': ('winapp2_windows_store', 'Windows Store'),
    '3033': ('winapp2_vivaldi', 'Vivaldi'),
    '3034': ('winapp2_brave', 'Brave'),
    # Section=Games (technically not langsecref)
    'Games': ('winapp2_games', _('Games'))}


def xml_escape(s):
    """Lightweight way to escape XML entities"""
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def section2option(s):
    """Normalize section name to appropriate option name"""
    ret = re.sub(r'[^a-z0-9]', '_', s.lower())
    ret = re.sub(r'_+', '_', ret)
    ret = re.sub(r'(^_|_$)', '', ret)
    return ret


def detectos(required_ver, mock=False):
    """Returns boolean whether the detectos is compatible with the
    current operating system, or the mock version, if given."""
    # Do not compare as string because Windows 10 (build 10.0) comes after
    # Windows 8.1 (build 6.3).
    assert isinstance(required_ver, str)
    current_os = mock or Windows.parse_windows_build()
    required_ver = required_ver.strip()
    if '|' not in required_ver:
        # Exact version
        return Windows.parse_windows_build(required_ver) == current_os
    # Format of min|max
    req_min = required_ver.split('|')[0]
    req_max = required_ver.split('|')[1]
    if req_min and current_os < Windows.parse_windows_build(req_min):
        return False
    if req_max and current_os > Windows.parse_windows_build(req_max):
        return False
    return True


def winapp_expand_vars(pathname):
    """Expand environment variables using special Winapp2.ini rules"""
    # This is the regular expansion
    expand1 = os.path.expandvars(pathname)
    # Winapp2.ini expands %ProgramFiles% to %ProgramW6432%, etc.
    subs = (('ProgramFiles', 'ProgramW6432'),
            ('CommonProgramFiles', 'CommonProgramW6432'))
    for (sub_orig, sub_repl) in subs:
        pattern = re.compile('%{}%'.format(sub_orig), flags=re.IGNORECASE)
        if pattern.match(pathname):
            expand2 = pattern.sub('%{}%'.format(sub_repl), pathname)
            return expand1, os.path.expandvars(expand2)
    return expand1,


def detect_file(pathname):
    """Check whether a path exists for DetectFile#="""
    for expanded in winapp_expand_vars(pathname):
        for _i in glob.iglob(expanded):
            return True
    return False


def special_detect(code):
    """Check whether the SpecialDetect== software exists"""
    # The last two are used only for testing
    sd_keys = {'DET_CHROME': r'HKCU\Software\Google\Chrome',
               'DET_MOZILLA': r'HKCU\Software\Mozilla\Firefox',
               'DET_OPERA': r'HKCU\Software\Opera Software',
               'DET_THUNDERBIRD': r'HKLM\SOFTWARE\Clients\Mail\Mozilla Thunderbird',
               'DET_WINDOWS': r'HKCU\Software\Microsoft',
               'DET_SPACE_QUEST': r'HKCU\Software\Sierra Games\Space Quest'}
    if code in sd_keys:
        return Windows.detect_registry_key(sd_keys[code])
    else:
        logger.error('Unknown SpecialDetect=%s', code)
    return False


def fnmatch_translate(pattern):
    """Same as the original without the end"""
    import fnmatch
    ret = fnmatch.translate(pattern)
    if ret.endswith('$'):
        return ret[:-1]
    return re.sub(r'\\Z(\(\?ms\))?$', '', ret)


class Winapp:

    """Create cleaners from a Winapp2.ini-style file"""

    def __init__(self, pathname, cb_progress=lambda x: None):
        """Create cleaners from a Winapp2.ini-style file"""

        self.cleaners = {}
        self.cleaner_ids = []
        for langsecref in set(langsecref_map.values()):
            self.add_section(langsecref[0], langsecref[1])
        self.errors = 0
        self.parser = bleachbit.RawConfigParser()
        self.parser.read(pathname)
        self.re_detect = re.compile(r'^detect(\d+)?$')
        self.re_detectfile = re.compile(r'^detectfile(\d+)?$')
        self.re_excludekey = re.compile(r'^excludekey\d+$')
        section_total_count = len(self.parser.sections())
        section_done_count = 0
        for section in self.parser.sections():
            try:
                self.handle_section(section)
            except Exception:
                self.errors += 1
                logger.exception('parsing error in section %s', section)
            else:
                section_done_count += 1
                cb_progress(1.0 * section_done_count / section_total_count)

    def add_section(self, cleaner_id, name):
        """Add a section (cleaners)"""
        self.cleaner_ids.append(cleaner_id)
        self.cleaners[cleaner_id] = Cleaner.Cleaner()
        self.cleaners[cleaner_id].id = cleaner_id
        self.cleaners[cleaner_id].name = name
        assert name.strip() == name
        self.cleaners[cleaner_id].description = _('Imported from winapp2.ini')
        # The detect() function in this module effectively does what
        # auto_hide() does, so this avoids redundant, slow processing.
        self.cleaners[cleaner_id].auto_hide = lambda: False

    def section_to_cleanerid(self, langsecref):
        """Given a langsecref (or section name), find the internal
        BleachBit cleaner ID."""
        # pre-defined, such as 3021
        if langsecref in langsecref_map.keys():
            return langsecref_map[langsecref][0]
        # custom, such as games
        cleanerid = 'winapp2_' + section2option(langsecref)
        if cleanerid not in self.cleaners:
            # never seen before
            self.add_section(cleanerid, langsecref)
        return cleanerid

    def excludekey_to_nwholeregex(self, excludekey):
        r"""Translate one ExcludeKey to CleanerML nwholeregex

        Supported examples
        FILE=%LocalAppData%\BleachBit\BleachBit.ini
        FILE=%LocalAppData%\BleachBit\|BleachBit.ini
        FILE=%LocalAppData%\BleachBit\|*.ini
        FILE=%LocalAppData%\BleachBit\|*.ini;*.bak
        PATH=%LocalAppData%\BleachBit\
        PATH=%LocalAppData%\BleachBit\|*.*
        """
        parts = excludekey.split('|')
        parts[0] = parts[0].upper()
        if parts[0] == 'REG':
            raise NotImplementedError('REG not supported in ExcludeKey')

        # the last part contains the filename(s)
        files = None
        files_regex = ''
        if len(parts) == 3:
            files = parts[2].split(';')
            if len(files) == 1:
                # one file pattern like *.* or *.log
                files_regex = fnmatch_translate(files[0])
                if files_regex == '*.*':
                    files = None
            elif len(files) > 1:
                # multiple file patterns like *.log;*.bak
                files_regex = '(%s)' % '|'.join(
                    [fnmatch_translate(f) for f in files])

        # the middle part contains the file
        regexes = []
        for expanded in winapp_expand_vars(parts[1]):
            regex = None
            if not files:
                # There is no third part, so this is either just a folder,
                # or sometimes the file is specified directly.
                regex = fnmatch_translate(expanded)
            if files:
                # match one or more file types, directly in this tree or in any
                # sub folder
                regex = r'%s\\%s' % (
                    re.sub(r'\\\\((?:\))?)$', r'\1', fnmatch_translate(expanded)), files_regex)
            regexes.append(regex)

        if len(regexes) == 1:
            return regexes[0]
        else:
            return '(%s)' % '|'.join(regexes)

    def detect(self, section):
        """Check whether to show the section

        The logic:
        If the DetectOS does not match, the section is inactive.
        If any Detect or DetectFile matches, the section is active.
        If neither Detect or DetectFile was given, the section is active.
        Otherwise, the section is inactive.
        """
        if self.parser.has_option(section, 'detectos'):
            required_ver = self.parser.get(section, 'detectos')
            if not detectos(required_ver):
                return False
        any_detect_option = False
        if self.parser.has_option(section, 'specialdetect'):
            any_detect_option = True
            sd_code = self.parser.get(section, 'specialdetect')
            if special_detect(sd_code):
                return True
        for option in self.parser.options(section):
            if re.match(self.re_detect, option):
                # Detect= checks for a registry key
                any_detect_option = True
                key = self.parser.get(section, option)
                if Windows.detect_registry_key(key):
                    return True
            elif re.match(self.re_detectfile, option):
                # DetectFile= checks for a file
                any_detect_option = True
                key = self.parser.get(section, option)
                if detect_file(key):
                    return True
        return not any_detect_option

    def handle_section(self, section):
        """Parse a section"""
        # check whether the section is active (i.e., whether it will be shown)
        if not self.detect(section):
            return
        # excludekeys ignores a file, path, or registry key
        excludekeys = [
            self.excludekey_to_nwholeregex(self.parser.get(section, option))
            for option in self.parser.options(section)
            if re.match(self.re_excludekey, option)
        ]
        # there are two ways to specify sections: langsecref= and section=
        if self.parser.has_option(section, 'langsecref'):
            # verify the langsecref number is known
            # langsecref_num is 3021, games, etc.
            langsecref_num = self.parser.get(section, 'langsecref')
        elif self.parser.has_option(section, 'section'):
            langsecref_num = self.parser.get(section, 'section')
        else:
            logger.error(
                'neither option LangSecRef nor Section found in section %s', section)
            return
        # find the BleachBit internal cleaner ID
        lid = self.section_to_cleanerid(langsecref_num)
        option_name = section.replace('*', '').strip()
        self.cleaners[lid].add_option(
            section2option(section), option_name, '')
        for option in self.parser.options(section):
            if (
                option
                in {
                    "default",
                    "langsecref",
                    "section",
                    "detectos",
                    "specialdetect",
                }
                or re.match(self.re_detect, option)
                or re.match(self.re_detectfile, option)
                or re.match(self.re_excludekey, option)
            ):
                continue
            if option.startswith('filekey'):
                self.handle_filekey(lid, section, option, excludekeys)
            elif option.startswith('regkey'):
                self.handle_regkey(lid, section, option)
            elif option == 'warning':
                self.cleaners[lid].set_warning(
                    section2option(section), self.parser.get(section, 'warning'))
            else:
                logger.warning(
                    'unknown option %s in section %s', option, section)
                return

    def __make_file_provider(self, dirname, filename, recurse, removeself, excludekeys):
        """Change parsed FileKey to action provider"""
        regex = ''
        if recurse:
            search = 'walk.files'
            path = dirname
            if filename == '*.*':
                if removeself:
                    search = 'walk.all'
            else:
                import fnmatch
                regex = ' regex="^%s$" ' % xml_escape(
                    fnmatch.translate(filename))
        else:
            search = 'glob'
            path = os.path.join(dirname, filename)
            if path.find('*') == -1:
                search = 'file'
        excludekeysxml = ''
        if excludekeys:
            if len(excludekeys) > 1:
                # multiple
                exclude_str = '(%s)' % '|'.join(excludekeys)
            else:
                # just one
                exclude_str = excludekeys[0]
            excludekeysxml = 'nwholeregex="%s"' % xml_escape(exclude_str)
        action_str = '<option command="delete" search="%s" path="%s" %s %s/>' % \
                     (search, xml_escape(path), regex, excludekeysxml)
        yield Delete(parseString(action_str).childNodes[0])
        if removeself:
            search = 'file'
            if dirname.find('*') > -1:
                search = 'glob'
            action_str = '<option command="delete" search="%s" path="%s" type="d"/>' % \
                         (search, xml_escape(dirname))
            yield Delete(parseString(action_str).childNodes[0])

    def handle_filekey(self, lid, ini_section, ini_option, excludekeys):
        """Parse a FileKey# option.

        Section is [Application Name] and option is the FileKey#"""
        elements = self.parser.get(
            ini_section, ini_option).strip().split('|')
        dirnames = winapp_expand_vars(elements.pop(0))
        filenames = ""
        if elements:
            filenames = elements.pop(0)
        recurse = False
        removeself = False
        for element in elements:
            element = element.upper()
            if element == 'RECURSE':
                recurse = True
            elif element == 'REMOVESELF':
                recurse = True
                removeself = True
            else:
                logger.warning(
                    'unknown file option %s in section %s', element, ini_section)
        for filename in filenames.split(';'):
            for dirname in dirnames:
                # If dirname is a drive letter it needs a special treatment on Windows:
                # https://www.reddit.com/r/learnpython/comments/gawqne/why_cant_i_ospathjoin_on_a_drive_letterc/
                dirname = '{}{}'.format(dirname, os.path.sep) if os.path.splitdrive(dirname)[
                    0] == dirname else dirname
                for provider in self.__make_file_provider(dirname, filename, recurse, removeself, excludekeys):
                    self.cleaners[lid].add_action(
                        section2option(ini_section), provider)

    def handle_regkey(self, lid, ini_section, ini_option):
        """Parse a RegKey# option"""
        elements = self.parser.get(
            ini_section, ini_option).strip().split('|')
        path = xml_escape(elements[0])
        name = ""
        if len(elements) == 2:
            name = 'name="%s"' % xml_escape(elements[1])
        action_str = '<option command="winreg" path="%s" %s/>' % (path, name)
        provider = Winreg(parseString(action_str).childNodes[0])
        self.cleaners[lid].add_action(section2option(ini_section), provider)

    def get_cleaners(self):
        """Return the created cleaners"""
        for cleaner_id in self.cleaner_ids:
            if self.cleaners[cleaner_id].is_usable():
                yield self.cleaners[cleaner_id]


def list_winapp_files():
    """List winapp2.ini files"""
    for dirname in (bleachbit.personal_cleaners_dir, bleachbit.system_cleaners_dir):
        fname = os.path.join(dirname, 'winapp2.ini')
        if os.path.exists(fname):
            yield fname


def load_cleaners(cb_progress=lambda x: None):
    """Scan for winapp2.ini files and load them"""
    cb_progress(0.0)
    for pathname in list_winapp_files():
        try:
            inicleaner = Winapp(pathname, cb_progress)
        except Exception:
            logger.exception(
                "Error reading winapp2.ini cleaner '%s'", pathname)
        else:
            for cleaner in inicleaner.get_cleaners():
                Cleaner.backends[cleaner.id] = cleaner
        yield True
