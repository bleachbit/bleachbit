# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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
Test cases for module CleanerML
"""
from __future__ import absolute_import, print_function

from tests import common
from bleachbit.CleanerML import *


class CleanerMLTestCase(common.BleachbitTestCase):
    """Test cases for CleanerML"""

    def setUp(self):
        """Prepare for each test method"""
        # BleachbitTestCase.setUp() resets the current working directory
        super(CleanerMLTestCase, self).setUp()
        # This test case expects another working directory.
        os.chdir('tests')

    def test_CleanerML(self):
        """Unit test for class CleanerML"""

        xmlcleaner = CleanerML("../doc/example_cleaner.xml")

        self.assertIsInstance(xmlcleaner, CleanerML)
        self.assertIsInstance(xmlcleaner.cleaner, Cleaner.Cleaner)

        def run_all(really_delete):
            for (option_id, __name) in xmlcleaner.cleaner.get_options():
                for cmd in xmlcleaner.cleaner.get_commands(option_id):
                    for result in cmd.execute(really_delete):
                        common.validate_result(self, result, really_delete)

        # preview
        run_all(False)

        # really delete if user allows
        if common.destructive_tests('example_cleaner.xml'):
            run_all(True)


    def test_boolstr_to_bool(self):
        """Unit test for boolstr_to_bool()"""
        tests = [('True', True),
                 ('False', False)]

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
            self.assertExists(pathname)

    def test_load_cleaners(self):
        """Unit test for load_cleaners()"""
        # normal
        load_cleaners()

        # should catch exception with invalid XML
        pcd = bleachbit.personal_cleaners_dir
        bleachbit.personal_cleaners_dir = self.mkdtemp(prefix='bleachbit-cleanerml-load')
        self.write_file(os.path.join(bleachbit.personal_cleaners_dir, 'invalid.xml'),
                        contents='<xml><broken>')
        load_cleaners()
        import shutil
        shutil.rmtree(bleachbit.personal_cleaners_dir)
        bleachbit.personal_cleaners_dir = pcd

    def test_pot_fragment(self):
        """Unit test for pot_fragment()"""
        self.assertIsString(pot_fragment("Foo", 'bar.xml'))
