
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://www.bleachbit.org
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


import Cleaner
import Common
import ConfigParser
import Windows
import os
import glob
import re
import traceback

from Action import Delete, Winreg
from Common import _
from xml.dom.minidom import parseString


MAX_DETECT = 50

# TRANSLATORS: This is cleaner name for cleaners imported from winapp2.ini
langsecref_map = {'3021': ('winapp2_applications', _('Applications')),
                  # TRANSLATORS: This is cleaner name for cleaners imported
                  # from winapp2.ini
                  '3022': ('winapp2_internet', _('Internet')),
                  # TRANSLATORS: This is cleaner name for cleaners imported
                  # from winapp2.ini
                  '3023': ('winapp2_multimedia', _('Multimedia')),
                  # TRANSLATORS: This is cleaner name for cleaners imported
                  # from winapp2.ini
                  '3024': ('winapp2_utilities', _('Utilities')),
                  # TRANSLATORS: This is cleaner name for cleaners imported
                  # from winapp2.ini.
                  '3025': ('winapp2_windows', 'Microsoft Windows'),
                  '3026': ('winapp2_mozilla', 'Firefox/Mozilla'),
                  '3027': ('winapp2_opera', 'Opera'),
                  '3028': ('winapp2_safari', 'Safari'),
                  '3029': ('winapp2_google_chrome', 'Google Chrome'),
                  '3030': ('winapp2_thunderbird', 'Thunderbird'),
                  '3031': ('winapp2_windows_store', 'Windows Store'),
                  # Section=Games (technically not langsecref)
                  'Games': ('winapp2_games', _('Games'))}


def xml_escape(s):
    """Lightweight way to escape XML entities"""
    return s.replace('&', '&amp;').replace('"', '&quot;')


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
    assert(isinstance(required_ver, (str, unicode)))
    current_os = (mock if mock else Windows.parse_windows_build())
    required_ver = required_ver.strip()
    if required_ver.startswith('|'):
        # This is the maximum version
        # For example, |5.1 means Windows XP (5.1) but not Vista (6.0)
        return current_os <= Windows.parse_windows_build(required_ver[1:])
    elif required_ver.endswith('|'):
        # This is the minimum version
        # For example, 6.1| means Windows 7 or later
        return current_os >= Windows.parse_windows_build(required_ver[:-1])
    else:
        # Exact version
        return Windows.parse_windows_build(required_ver) == current_os


def winapp_expand_vars(pathname):
    """Expand environment variables using special Winapp2.ini rules"""
    # Change %foo% to ${foo} as required by Python 2.5.4 (but not 2.7.8)
    pathname = re.sub(r'%([a-zA-Z0-9]+)%', r'${\1}', pathname)
    # This is the regular expansion
    expand1 = os.path.expandvars(pathname)
    # Winapp2.ini expands %ProgramFiles% to %ProgramW6432%, etc.
    subs = (('ProgramFiles', 'ProgramW6432'),
            ('CommonProgramFiles', 'CommonProgramW6432'))
    for (sub_orig, sub_repl) in subs:
        pattern = re.compile(r'\${%s}' % sub_orig, flags=re.IGNORECASE)
        if pattern.match(pathname):
            expand2 = pattern.sub('${%s}' % sub_repl, pathname)
            return (expand1, os.path.expandvars(expand2))
    return (expand1,)


def detect_file(pathname):
    """Check whether a path exists for DetectFile#="""
    for expanded in winapp_expand_vars(pathname):
        for thispath in glob.iglob(expanded):
            return True
    return False


def fnmatch_translate(pattern):
    """Same as the original without the end"""
    import fnmatch
    r = fnmatch.translate(pattern)
    if r.endswith('$'):
        return r[:-1]
    if r.endswith(r'\Z(?ms)'):
        return r[:-7]
    return r


class Winapp:

    """Create cleaners from a Winapp2.ini-style file"""

    def __init__(self, pathname):
        """Create cleaners from a Winapp2.ini-style file"""

        self.cleaners = {}
        self.cleaner_ids = []
        for langsecref in set(langsecref_map.values()):
            self.add_section(langsecref[0], langsecref[1])
        self.errors = 0
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(pathname)
        for section in self.parser.sections():
            try:
                self.handle_section(section)
            except:
                self.errors += 1
                print 'ERROR: parsing error in section %s' % section
                traceback.print_exc()

    def add_section(self, cleaner_id, name):
        """Add a section (cleaners)"""
        self.cleaner_ids.append(cleaner_id)
        self.cleaners[cleaner_id] = Cleaner.Cleaner()
        self.cleaners[cleaner_id].id = cleaner_id
        self.cleaners[cleaner_id].name = name
        self.cleaners[cleaner_id].description = _('Imported from winapp2.ini')

    def section_to_cleanerid(self, langsecref):
        """Given a langsecref (or section name), find the internal
        BleachBit cleaner ID."""
        # pre-defined, such as 3021
        if langsecref in langsecref_map.keys():
            return langsecref_map[langsecref][0]
        # custom, such as games
        cleanerid = 'winapp2_' + section2option(langsecref)
        if not cleanerid in self.cleaners:
            # never seen before
            self.add_section(cleanerid, langsecref)
        return cleanerid

    def excludekey_to_nwholeregex(self, excludekey):
        """Translate one ExcludeKey to CleanerML nwholeregex

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
        if 'REG' == parts[0]:
            raise NotImplementedError('REG not supported in ExcludeKey')

        # the last part contains the filename(s)
        files = None
        files_regex = ''
        if 3 == len(parts):
            files = parts[2].split(';')
            if 1 == len(files):
                # one file pattern like *.* or *.log
                files_regex = fnmatch_translate(files[0])
                if '*.*' == files_regex:
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
                regex = '%s.*%s' % (
                    fnmatch_translate(expanded), files_regex)
            regexes.append(regex)

        if 1 == len(regexes):
            return regexes[0]
        else:
            return '(%s)' % '|'.join(regexes)

    def handle_section(self, section):
        """Parse a section"""
        # if simple detection fails then discard the section
        if self.parser.has_option(section, 'detect'):
            key = self.parser.get(section, 'detect')
            if not Windows.detect_registry_key(key):
                return
        if self.parser.has_option(section, 'detectfile'):
            if not detect_file(self.parser.get(section, 'detectfile')):
                return
        if self.parser.has_option(section, 'detectos'):
            required_ver = self.parser.get(section, 'detectos')
            if not detectos(required_ver):
                return
        # in case of multiple detection, discard if none match
        if self.parser.has_option(section, 'detectfile1'):
            matches = 0
            for n in range(1, MAX_DETECT):
                option_id = 'detectfile%d' % n
                if self.parser.has_option(section, option_id):
                    if detect_file(self.parser.get(section, option_id)):
                        matches = matches + 1
            if 0 == matches:
                return
        if self.parser.has_option(section, 'detect1'):
            matches = 0
            for n in range(1, MAX_DETECT):
                option_id = 'detect%d' % n
                if self.parser.has_option(section, option_id):
                    if Windows.detect_registry_key(self.parser.get(section, option_id)):
                        matches = matches + 1
            if 0 == matches:
                return
        # excludekeys ignores a file, path, or registry key
        excludekeys = []
        if self.parser.has_option(section, 'excludekey1'):
            for n in range(1, MAX_DETECT):
                option_id = 'excludekey%d' % n
                if self.parser.has_option(section, option_id):
                    excludekeys.append(
                        self.excludekey_to_nwholeregex(self.parser.get(section, option_id)))
        # there are two ways to specify sections: langsecref= and section=
        if self.parser.has_option(section, 'langsecref'):
            # verify the langsecref number is known
            # langsecref_num is 3021, games, etc.
            langsecref_num = self.parser.get(section, 'langsecref')
        elif self.parser.has_option(section, 'section'):
            langsecref_num = self.parser.get(section, 'section')
        else:
            print 'ERROR: neither option LangSecRef nor Section found in section %s' % (section)
            return
        # find the BleachBit internal cleaner ID
        lid = self.section_to_cleanerid(langsecref_num)
        self.cleaners[lid].add_option(
            section2option(section), section.replace('*', ''), '')
        for option in self.parser.options(section):
            if option.startswith('filekey'):
                self.handle_filekey(lid, section, option, excludekeys)
            elif option.startswith('regkey'):
                self.handle_regkey(lid, section, option)
            elif option == 'warning':
                self.cleaners[lid].set_warning(
                    section2option(section), self.parser.get(section, 'warning'))
            elif option in ('default', 'detectfile', 'detect', 'langsecref', 'section') \
                or ['detect%d' % x for x in range(1, MAX_DETECT)] \
                    or ['detectfile%d' % x for x in range(1, MAX_DETECT)]:
                pass
            else:
                print 'WARNING: unknown option %s in section %s' % (option, section)
                return

    def __make_file_provider(self, dirname, filename, recurse, removeself, excludekeys):
        """Change parsed FileKey to action provider"""
        regex = ''
        if recurse:
            search = 'walk.files'
            path = dirname
            if filename.startswith('*.'):
                filename = filename.replace('*.', '.')
            if '.*' == filename:
                if removeself:
                    search = 'walk.all'
            else:
                import fnmatch
                regex = ' regex="%s" ' % (fnmatch.translate(filename))
        else:
            search = 'glob'
            path = os.path.join(dirname, filename)
            if -1 == path.find('*'):
                search = 'file'
        excludekeysxml = ''
        if excludekeys:
            if len(excludekeys) > 1:
                # multiple
                exclude_str = '(%s)' % '|'.join(excludekeys)
            else:
                # just one
                exclude_str = excludekeys[0]
            excludekeysxml = 'nwholeregex="%s"' % exclude_str
        action_str = '<option command="delete" search="%s" path="%s" %s %s/>' % \
            (search, xml_escape(path), regex, excludekeysxml)
        yield Delete(parseString(action_str).childNodes[0])
        if removeself:
            action_str = '<option command="delete" search="file" path="%s"/>' % xml_escape(
                dirname)
            yield Delete(parseString(action_str).childNodes[0])

    def handle_filekey(self, lid, ini_section, ini_option, excludekeys):
        """Parse a FileKey# option.

        Section is [Application Name] and option is the FileKey#"""
        elements = self.parser.get(ini_section, ini_option).strip().split('|')
        dirnames = winapp_expand_vars(elements.pop(0))
        filenames = ""
        if elements:
            filenames = elements.pop(0)
        recurse = False
        removeself = False
        for element in elements:
            element = element.upper()
            if 'RECURSE' == element:
                recurse = True
            elif 'REMOVESELF' == element:
                recurse = True
                removeself = True
            else:
                print 'WARNING: unknown file option %s in section %s' % (element, ini_section)
        for filename in filenames.split(';'):
            for dirname in dirnames:
                for provider in self.__make_file_provider(dirname, filename, recurse, removeself, excludekeys):
                    self.cleaners[lid].add_action(
                        section2option(ini_section), provider)

    def handle_regkey(self, lid, ini_section, ini_option):
        """Parse a RegKey# option"""
        elements = self.parser.get(ini_section, ini_option).strip().split('|')
        path = xml_escape(elements[0])
        name = ""
        if 2 == len(elements):
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
    for dirname in (Common.personal_cleaners_dir, Common.system_cleaners_dir):
        fn = os.path.join(dirname, 'winapp2.ini')
        if os.path.exists(fn):
            yield fn


def load_cleaners():
    """Scan for winapp2.ini files and load them"""
    for pathname in list_winapp_files():
        try:
            inicleaner = Winapp(pathname)
        except:
            print "Error reading winapp2.ini cleaner '%s'" % pathname
            traceback.print_exc()
        else:
            for cleaner in inicleaner.get_cleaners():
                Cleaner.backends[cleaner.id] = cleaner
