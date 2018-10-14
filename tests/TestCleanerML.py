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

    def run_all(self, xmlcleaner, really_delete):
        """Helper function to execute all options in a cleaner"""
        for (option_id, __name) in xmlcleaner.cleaner.get_options():
            for cmd in xmlcleaner.cleaner.get_commands(option_id):
                for result in cmd.execute(really_delete):
                    common.validate_result(self, result, really_delete)

    def test_CleanerML(self):
        """Unit test for class CleanerML"""

        xmlcleaner = CleanerML("doc/example_cleaner.xml")

        self.assertIsInstance(xmlcleaner, CleanerML)
        self.assertIsInstance(xmlcleaner.cleaner, Cleaner.Cleaner)

        # preview
        self.run_all(xmlcleaner, False)

        # really delete if user allows
        if common.destructive_tests('example_cleaner.xml'):
            self.run_all(xmlcleaner, True)


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
        os.chdir('po')
        try:
            create_pot()
        finally:
            os.chdir('..')

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

    def test_os_match(self):
        """Unit test for os_match"""
        xmlcleaner = CleanerML("doc/example_cleaner.xml")

        # blank always matches
        self.assertTrue(xmlcleaner.os_match(""))

        # as Linux
        self.assertFalse(xmlcleaner.os_match('windows', 'linux2'))
        self.assertTrue(xmlcleaner.os_match('linux', 'linux2'))
        self.assertTrue(xmlcleaner.os_match('unix', 'linux2'))

        # as Windows
        self.assertFalse(xmlcleaner.os_match('linux', 'win32'))
        self.assertFalse(xmlcleaner.os_match('unix', 'win32'))
        self.assertTrue(xmlcleaner.os_match('windows', 'win32'))

        # as unknown operating system
        with self.assertRaises(RuntimeError):
            xmlcleaner.os_match('linux', 'hal9000')

    def test_pot_fragment(self):
        """Unit test for pot_fragment()"""
        self.assertIsString(pot_fragment("Foo", 'bar.xml'))

    def test_var(self):
        """Test the <var> element"""
        xml_str = r"""
<cleaner id="testvar">
    <label>cleaner label</label>
    <description>cleaner description</description>
    <var name="basepath">
        <value>%%LocalAppData%%\FooDoesNotExist</value>
        <value>~/.config/FooDoesNotExist</value>
        <value>{tempdir}/a</value>
        <value>{tempdir}/b</value>
    </var>
    <option id="option1">
        <label>option1 label</label>
        <description>option1 description</description>
        <action search="file" command="delete" path="$$basepath$$/test.log" />
    </option>
</cleaner>
""".format(**{'tempdir': self.tempdir})
        # write XML cleaner
        cml_path = os.path.join(self.tempdir, 'test.xml')
        self.write_file(cml_path, xml_str)

        # create two canaries
        test_log_path_a = os.path.join(self.tempdir, 'a', 'test.log')
        test_log_path_b = os.path.join(self.tempdir, 'b', 'test.log')
        common.touch_file(test_log_path_a)
        common.touch_file(test_log_path_b)
        self.assertExists(test_log_path_a)
        self.assertExists(test_log_path_b)

        # parse XML to XML cleaner instance
        xmlc = CleanerML(cml_path)
        self.assertIsInstance(xmlc, CleanerML)
        self.assertIsInstance(xmlc.cleaner, Cleaner.Cleaner)
        self.assertTrue(xmlc.cleaner.is_usable())

        # run preview
        self.run_all(xmlc, False)
        self.assertExists(test_log_path_a)
        self.assertExists(test_log_path_b)

        # really delete
        self.run_all(xmlc, True)
        self.assertNotExists(test_log_path_a)
        self.assertNotExists(test_log_path_b)

