# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
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
Import Winapp2.ini files
"""


import Cleaner
import Common
import ConfigParser
import Windows
import os
import re
import traceback

from Action import Delete, Winreg
from Common import _
from platform import uname
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
                  # 3026 = Firefox/Mozilla
                  '3026': ('winapp2_mozilla', 'Firefox/Mozilla'),
                  # 3027 = Opera
                  '3027': ('winapp2_opera', 'Opera'),
                  # 3028 = Safari
                  '3028': ('winapp2_safari', 'Safari'),
                  # 3029 = Google Chrome
                  '3029': ('winapp2_google_chrome', 'Google Chrome'),
                  # 3030 = Thunderbird
                  '3030': ('winapp2_thunderbird', 'thunderbird'),
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


def preexpand(s):
    """Prepare pathname for expansion by changing %foo% to ${foo}"""
    return re.sub(r'%([a-zA-Z]+)%', r'${\1}', s)


def detectos(required_ver, mock=False):
    """Returns boolean whether the detectos is compatible with the
    current operating system, or the mock version, if given."""
    current_os = (mock if mock else uname()[3])[0:3]
    required_ver = required_ver.strip()
    if required_ver.startswith('|'):
        # This is the maximum version
        # For example, |5.1 means Windows XP (5.1) but not Vista (6.0)
        return current_os <= required_ver[1:]
    elif required_ver.endswith('|'):
        # This is the minimum version
        # For example, 6.1| means Windows 7 or later
        return current_os >= required_ver[:-1]
    else:
        # Exact version
        return required_ver == current_os


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

    def handle_section(self, section):
        """Parse a section"""
        def detect_file(rawpath):
            pathname = os.path.expandvars(preexpand(rawpath))
            return os.path.exists(pathname)
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
        # not yet implemented
        if self.parser.has_option(section, 'excludekey'):
            print 'ERROR: ExcludeKey not implemented, section=', section
            return
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
                self.handle_filekey(lid, section, option)
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

    def __make_file_provider(self, dirname, filename, recurse, removeself):
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
                regex = ' regex="%s" ' % (re.escape(filename) + '$')
        else:
            search = 'glob'
            path = os.path.join(dirname, filename)
            if -1 == path.find('*'):
                search = 'file'
        action_str = '<option command="delete" search="%s" path="%s" %s/>' % \
            (search, xml_escape(path), regex)
        yield Delete(parseString(action_str).childNodes[0])
        if removeself:
            action_str = '<option command="delete" search="file" path="%s"/>' % xml_escape(
                dirname)
            yield Delete(parseString(action_str).childNodes[0])

    def handle_filekey(self, lid, ini_section, ini_option):
        """Parse a FileKey# option.

        Section is [Application Name] and option is the FileKey#"""
        elements = self.parser.get(ini_section, ini_option).strip().split('|')
        dirname = preexpand(elements.pop(0))
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
            for provider in self.__make_file_provider(dirname, filename, recurse, removeself):
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
