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

import CleanerBackend
from Action import Action
from FileUtilities import listdir


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

    def __init__(self, pathname, xlate_cb = None):
        """Create cleaner from XML in pathname.

        If xlate_cb is set, use it as a callback for each
        translate-able string.
        """

        self.action = None
        self.cleaner = CleanerBackend.Cleaner()
        self.option_id = None
        self.option_name = None
        self.option_description = None
        self.xlate_cb = xlate_cb
        if None == self.xlate_cb:
            self.xlate_cb = lambda x: None # do nothing

        dom = xml.dom.minidom.parse(pathname)

        self.handle_cleaner(dom.getElementsByTagName('cleaner')[0])


    def get_cleaner(self):
        """Return the created cleaner"""
        return self.cleaner


    def handle_cleaner(self, cleaner):
        """<cleaner> element"""
        self.cleaner.id = cleaner.getAttribute('id')
        self.handle_cleaner_label(cleaner.getElementsByTagName('label')[0])
        description = cleaner.getElementsByTagName('description')
        if description:
            self.handle_cleaner_description(description[0])
        self.handle_cleaner_options(cleaner.getElementsByTagName('option'))


    def handle_cleaner_label(self, label):
        """<label> element under <cleaner>"""
        self.cleaner.name = _(getText(label.childNodes))
        translate = label.getAttribute('translate')
        if translate and boolstr_to_bool(translate):
            self.xlate_cb(self.cleaner.name)


    def handle_cleaner_description(self, description):
        """<description> element under <cleaner>"""
        self.cleaner.description = _(getText(description.childNodes))
        self.xlate_cb(self.cleaner.description)


    def handle_cleaner_options(self, options):
        """<option> elements"""
        for option in options:

            self.action = Action()
            self.option_id = option.getAttribute('id')
            self.option_description = None
            self.option_name = None

            self.handle_cleaner_option_label(option.getElementsByTagName('label')[0])
            description = option.getElementsByTagName('description')
            self.handle_cleaner_option_description(description[0])

            for action in option.getElementsByTagName('action'):
                self.handle_cleaner_option_action(action)

            self.cleaner.add_option(self.option_id, self.option_name, self.option_description)
            self.cleaner.add_action(self.option_id, self.action)


    def handle_cleaner_option_label(self, label):
        """<label> element under <option>"""
        self.option_name = _(getText(label.childNodes))
        self.xlate_cb(self.option_name)


    def handle_cleaner_option_description(self, description):
        """<description> element under <option>"""
        self.option_description = _(getText(description.childNodes))
        self.xlate_cb(self.option_description)


    def handle_cleaner_option_action(self, action):
        """<action> element under <option>"""
        atype = action.getAttribute('type')
        pathname = getText(action.childNodes)
        if 'children' == atype:
            children = boolstr_to_bool(action.getAttribute('directories'))
            self.action.add_list_children(pathname, children)
        elif 'file' == atype:
            self.action.add_list_file(pathname)
        elif 'glob' == atype:
            self.action.add_list_glob(pathname)
        else:
            raise RuntimeError("Invalid action type '%s'" % atype)


def list_cleanerml_files(local_only = False):
    """List CleanerML files"""
    cleanerdirs = ( 'cleaners', \
        '~/.config/bleachbit/cleaners' )
    if not local_only:
        cleanerdirs += ( '/usr/share/bleachbit/cleaners', )
    for pathname in listdir(cleanerdirs):
        if not pathname.lower().endswith('.xml'):
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
            cleaner = xmlcleaner.get_cleaner()
            CleanerBackend.backends[cleaner.id] = cleaner


def pot_fragment(string):
    """Create a string fragment for generating .pot files"""
    ret = '''# ../cleaners/*xml
msgid "%s"
msgstr ""

''' % string
    return ret


def create_pot():
    """Create a .pot for translation using gettext"""

    cleaners = []
    strings = []

    for pathname in listdir('../cleaners'):
        if not pathname.lower().endswith(".xml"):
            continue
        try:
            xmlcleaner = CleanerML(pathname, \
                lambda newstr: strings.append(newstr))
        except:
            print "error reading '%s'" % pathname
            traceback.print_exc()

    f = open('../po/cleanerml.pot', 'w')
    for string in sorted(set(strings)):
        f.write(pot_fragment(string))
    f.close()


import unittest

class TestCleanerML(unittest.TestCase):
    """Test cases for CleanerML"""

    def test_CleanerML(self):
        """Unit test for class CleanerML"""
        xmlcleaner = CleanerML("../doc/example_cleaner.xml")

        self.assert_(isinstance(xmlcleaner, CleanerML))
        self.assert_(isinstance(xmlcleaner.cleaner, CleanerBackend.Cleaner))

        for (option_id, __name, __value) in xmlcleaner.cleaner.get_options():
            # enable all options
            xmlcleaner.cleaner.set_option(option_id, True)

        for pathname in xmlcleaner.cleaner.list_files():
            self.assert_(os.path.exists(pathname))



    def test_boolstr_to_bool(self):
        """Unit test for boolstr_to_bool()"""
        tests = [ ('True', True), \
            ('False', False) ]

        for (arg, output) in tests:
            self.assertEqual(boolstr_to_bool(arg), output)
            self.assertEqual(boolstr_to_bool(arg.lower()), output)
            self.assertEqual(boolstr_to_bool(arg.upper()), output)


    def test_create_pot(self):
        """Unit test for create_pot()"""
        create_pot()


    def test_list_cleanerml_files(self):
        """Unit test for list_cleanerml_files()"""
        for pathname in list_cleanerml_files():
            self.assert_(os.path.exists(pathname))


    def test_load_cleaners(self):
        """Unit test for load_cleaners()"""
        load_cleaners()


    def test_pot_fragment(self):
        """Unit test for pot_fragment()"""
        self.assert_(type(pot_fragment("Foo")) is str)


if __name__ == '__main__':
    import sys
    if 2 == len(sys.argv) and 'pot' == sys.argv[1]:
        create_pot()
    else:
        unittest.main()

