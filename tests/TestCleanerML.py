# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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


import unittest
import sys

sys.path.append('.')
from bleachbit.CleanerML import *

import common


class CleanerMLTestCase(unittest.TestCase, common.AssertFile):

    """Test cases for CleanerML"""

    def test_CleanerML(self):
        """Unit test for class CleanerML"""
        if os.path.exists('./doc/example_cleaner.xml'):
            os.chdir('tests')
        xmlcleaner = CleanerML("../doc/example_cleaner.xml")

        self.assert_(isinstance(xmlcleaner, CleanerML))
        self.assert_(isinstance(xmlcleaner.cleaner, Cleaner.Cleaner))

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
        import tempfile
        pcd = Common.personal_cleaners_dir
        Common.personal_cleaners_dir = tempfile.mkdtemp(
            prefix='bleachbit-cleanerml-load')
        fn_xml = os.path.join(Common.personal_cleaners_dir, 'invalid.xml')
        f = open(fn_xml, 'w')
        f.write('<xml><broken>')
        f.close()
        load_cleaners()
        import shutil
        shutil.rmtree(Common.personal_cleaners_dir)
        Common.personal_cleaners_dir = pcd

    def test_pot_fragment(self):
        """Unit test for pot_fragment()"""
        self.assert_(isinstance(pot_fragment("Foo", 'bar.xml'), str))


def suite():
    return unittest.makeSuite(CleanerMLTestCase)


if __name__ == '__main__':
    unittest.main()
