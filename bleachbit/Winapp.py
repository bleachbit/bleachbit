# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2011 Andrew Ziem
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
Import Winapp2.ini files
"""



import Cleaner
import Common
import ConfigParser
import os
import re
import sys
import traceback

from Action import ActionProvider, Delete
from Common import _
from FileUtilities import listdir
from General import boolstr_to_bool, getText
from Windows import detect_registry_key
from xml.dom.minidom import parseString


def xml_escape(s):
    """Lightweight way to escape XML entities"""
    return s.replace('&', '&amp;')


def section2option(s):
    """Normalize section name to appropriate option name"""
    ret = re.sub(r'[^a-z0-9]', '_', s.lower())
    ret = re.sub(r'_+', '_', ret)
    ret = re.sub(r'(^_|_$)', '', ret)
    return ret

def preexpand(s):
    """Prepare pathname for expansion by changing %foo% to ${foo}"""
    return re.sub(r'%([a-zA-Z]+)%', r'${\1}', s)


class Winapp:
    """Create cleaners from a Winapp2.ini-style file"""

    def __init__(self, pathname):
        """Create cleaners from a Winapp2.ini-style file"""

        self.cleaner = Cleaner.Cleaner()
        self.cleaner.id = 'winapp2'
        self.cleaner.description = 'Winapp2.ini temporary description'
        self.cleaner.name = 'Winapp2.ini temporary name'
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(pathname)
        for section in self.parser.sections():
            self.handle_section(section)


    def handle_section(self, section):
        """Parse a section"""
        if self.parser.has_option(section, 'detect'):
            key = self.parser.get(section, 'detect')
            if not detect_registry_key(key):
                return
        if self.parser.has_option(section, 'detectfile'):
            pathname = os.path.expandvars(preexpand(self.parser.get(section, 'detectfile')))
            if not os.path.exists(pathname):
                return
        self.cleaner.add_option(section2option(section), section.replace('*', ''), '')
        for option in self.parser.options(section):
            if option.startswith('filekey'):
                self.handle_filekey(section, option)
            elif option.startswith('regkey'):
                print 'fixme: regkey'
            elif option in ('default', 'detectfile', 'detect'):
                pass
            elif option in ('langsecref'):
                print 'fixme:', option
            else:
                print 'WARNING: unknown option', option


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
        print 'debug:', action_str
        yield Delete(parseString(action_str).childNodes[0])
        if removeself:
            action_str = '<option command="delete" search="file" path="%s"/>' % xml_escape(dirname)
            print 'debug:', action_str
            yield Delete(parseString(action_str).childNodes[0])


    def handle_filekey(self, ini_section, ini_option):
        """Parse a FileKey# option.

        Section is [Application Name] and option is the FileKey#"""
        elements = self.parser.get(ini_section, ini_option).split('|')
        dirname = preexpand(elements.pop(0))
        filename = ""
        if elements:
            filename = elements.pop(0)
        recurse = False
        removeself = False
        for element in elements:
            if 'RECURSE' == element:
                recurse = True
            elif 'REMOVESELF' == element:
                recurse = True
                removeself = True
            else:
                print 'WARNING: unknown file option', element
        print 'debug:', self.parser.get(ini_section, ini_option)
        for provider in self.__make_file_provider(dirname, filename, recurse, removeself):
            for cmd in provider.get_commands():
                print 'debug: cmd', cmd
            self.cleaner.add_action(section2option(ini_section), provider)


    def get_cleaner(self):
        """Return the created cleaner"""
        return self.cleaner


def list_winapp_files():
    """List winapp2.ini files"""
    fn = os.path.join(Common.personal_cleaners_dir, 'winapp2.ini')
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
            cleaner = inicleaner.get_cleaner()
            if cleaner.is_usable():
                Cleaner.backends[cleaner.id] = cleaner
            else:
                print 'debug: "%s" is not usable' % pathname



