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
Test cases for module CleanerML
"""



import unittest
import sys

sys.path.append('.')
import TestCleaner
from bleachbit.CleanerML import *



class CleanerMLTestCase(unittest.TestCase):
    """Test cases for CleanerML"""

    def test_CleanerML(self):
        """Unit test for class CleanerML"""
        if os.path.exists('./doc/example_cleaner.xml'):
            os.chdir('tests')
        xmlcleaner = CleanerML("../doc/example_cleaner.xml")

        self.assert_(isinstance(xmlcleaner, CleanerML))
        self.assert_(isinstance(xmlcleaner.cleaner, Cleaner.Cleaner))

        for (option_id, __name) in xmlcleaner.cleaner.get_options():
            for cmd in xmlcleaner.cleaner.get_commands(option_id):
                for result in cmd.execute(False):
                    TestCleaner.validate_result(self, result)


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
        self.assert_(type(pot_fragment("Foo", 'bar.xml')) is str)



def suite():
    return unittest.makeSuite(CleanerMLTestCase)


if __name__ == '__main__':
    unittest.main()

