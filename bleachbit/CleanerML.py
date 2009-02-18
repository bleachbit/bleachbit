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
Create cleaners from CleanerML (markup language)
"""

import os
import traceback
import xml.dom.minidom


import globals
import CleanerBackend
from Action import Action
from FileUtilities import children_in_directory


def getText(nodelist):
    """"http://docs.python.org/library/xml.dom.minidom.html"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError('Invalid boolean: %s' % value)


class CleanerML:
    """Create a cleaner from CleanerML"""

    def __init__(self, pathname):
        """Create cleaner from XML in pathname"""

        self.action = None
        self.cleaner = CleanerBackend.Cleaner()
        self.option_id = None
        self.option_name = None
        self.option_description = None

        dom = xml.dom.minidom.parse(pathname)

        self.handleCleaners(dom.getElementsByTagName('cleaners')[0])


    def getCleaner(self):
        """Return the created cleaner"""
        return self.cleaner


    def handleCleaners(self, cleaners):
        for cleaner in cleaners.getElementsByTagName('cleaner'):
            self.handleCleaner(cleaner)


    def handleCleaner(self, cleaner):
        self.cleaner.id = cleaner.getAttribute('id')
        self.handleCleanerLabel(cleaner.getElementsByTagName('label')[0])
        description = cleaner.getElementsByTagName('description')
        if description:
            self.handleCleanerDescription(description[0])
        self.handleCleanerOptions(cleaner.getElementsByTagName('option'))


    def handleCleanerLabel(self, label):
        self.cleaner.name = _(getText(label.childNodes))


    def handleCleanerDescription(self, description):
        self.cleaner.description = _(getText(description.childNodes))


    def handleCleanerOptions(self, options):
        for option in options:

            self.action = Action()
            self.option_id = option.getAttribute('id')

            self.handleCleanerOptionLabel(option.getElementsByTagName('label')[0])
            description = option.getElementsByTagName('description')
            if description:
                self.handleCleanerOptionDescription(description[0])

            for action in option.getElementsByTagName('action'):
                self.handleCleanerOptionAction(action)

            self.cleaner.add_option(self.option_id, self.option_name, self.option_description)
            self.cleaner.add_action(self.option_id, self.action)


    def handleCleanerOptionLabel(self, label):
        self.option_name = _(getText(label.childNodes))


    def handleCleanerOptionDescription(self, description):
        self.option_description = _(getText(description.childNodes))


    def handleCleanerOptionAction(self, action):
        type = action.getAttribute('type')
        pathname = getText(action.childNodes)
        if 'children' == type:
            children = boolstr_to_bool(action.getAttribute('directories'))
            self.action.add_list_children(pathname, children)
        if 'file' == type:
            self.action.add_list_file(pathname)
        if 'glob' == type:
            self.action.add_list_glob(pathname)


def list_cleanerml_files(local_only = False):
    """List CleanerML files"""
    cleanerdirs = ( 'cleaners', \
        '~/.config/bleachbit/cleaners' )
    if not local_only:
        cleanerdirs += ( '/usr/share/bleachbit/cleaners', )
    for pathname in children_in_directory(cleanerdirs):
        if not pathname.endswith('.xml'):
            continue
        import stat
        st = os.stat(pathname)
        if stat.S_IMODE(st[stat.ST_MODE]) & 2:
            print "warning: ignoring cleaner '%s' because it is world writable" % pathname
            continue
        yield pathname


def load_cleaners():
    """Scan for CleanerML and load them"""
    for pathname in list_cleanerml_files():
        try:
            xmlcleaner = CleanerML(pathname)
        except:
            print "Error reading file '%s'" % pathname
            traceback.print_exc()
        else:
            cleaner = xmlcleaner.getCleaner()
            CleanerBackend.backends[cleaner.id] = cleaner


def pot_fragment(string):
    """Create a string fragment for generaring .pot files"""
    ret = '''# ../cleaners/*xml
msgid "%s"
msgstr ""

''' % string
    return ret


def create_pot():
    """Create a .pot for translation using gettext"""
    cleaners = []

    for pathname in children_in_directory('../cleaners'):
        xmlcleaner = CleanerML(pathname)
        cleaner = xmlcleaner.getCleaner()
        cleaners += ( ( cleaner, ) )

    strings = []

    for cleaner in cleaners:
        strings += ( cleaner.get_name(), )
        strings += ( cleaner.get_description(), )

    f = open('../po/cleanerml.pot', 'w')
    for string in strings:
        f.write(pot_fragment(string))
    f.close()


import unittest

class TestCleanerML(unittest.TestCase):
    """Test cases for CleanerML"""

    def test_CleanerML(self):
        xmlcleaner = CleanerML("cleaner.xml")

        self.assert_(isinstance(xmlcleaner, CleanerML))
        self.assert_(isinstance(xmlcleaner.cleaner, CleanerBackend.Cleaner))

        for (option_id, __name, __value) in xmlcleaner.cleaner.get_options():
            # enable all options
            xmlcleaner.cleaner.set_option(option_id, True)

        for pathname in xmlcleaner.cleaner.list_files():
            self.assert_(os.path.exists(pathname))

    def test_create_pot(self):
        """Unit test for create_pot()"""
        create_pot()


if __name__ == '__main__':
    import sys
    if 2 == len(sys.argv) and 'pot' == sys.argv[1]:
        create_pot()
    else:
        unittest.main()

