# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module SystemInformation
"""

from tests import common
from bleachbit.SystemInformation import get_system_information, get_version, anonymize_system_information
import os
import tempfile


class SystemInformationTestCase(common.BleachbitTestCase):
    """Test Case for module SystemInformation"""

    def test_get_system_information(self):
        """Test get_system_information"""
        # at least it does not crash
        ret = get_system_information()
        self.assertIsString(ret)

    def test_get_version(self):
        """Test get_version"""
        ret = get_version()
        self.assertIsString(ret)
        # check it is in a.b.c.d or a.b.c format
        self.assertRegex(ret, r'^\d+\.\d+\.\d+(\.\d+)?$')
        ret = get_version(four_parts=True)
        self.assertIsString(ret)
        # check it is in a.b.c.d format
        self.assertRegex(ret, r'^\d+\.\d+\.\d+\.\d+$')


    def test_anonymize_system_information(self):
        """Test anonymize_system_information function"""
        home_dir = os.path.expanduser('~')

        # Test path anonymization via expanduser
        home_token = '~' if os.name == 'posix' else '%userprofile%'
        test_input = f"""BleachBit version = 4.6.0
local_cleaners_dir = {home_dir}/.local/share/bleachbit/cleaners
options_dir = {home_dir}/.config/bleachbit
os.getenv(LOGNAME) = testuser
os.getenv(USER) = testuser
os.getenv(SUDO_UID) = 1000"""

        result = anonymize_system_information(test_input)

        # Home directory should be replaced with a token
        self.assertIn(
            f'local_cleaners_dir = {home_token}/.local/share/bleachbit/cleaners', result)
        self.assertIn(f'options_dir = {home_token}/.config/bleachbit', result)
        self.assertNotIn(home_dir, result)
        self.assertNotIn(home_dir.lower(), result.lower())

        # Non-root user should be masked
        self.assertIn('os.getenv(LOGNAME) = *non-root*', result)
        self.assertIn('os.getenv(USER) = *non-root*', result)

        # SUDO_UID should remain unchanged
        self.assertIn('os.getenv(SUDO_UID) = 1000', result)

        # Windows paths go through expanduser too
        if os.name == 'nt':
            # Test case-insensitive Windows path anonymization
            test_windows_case = f"""os.getenv(APPDATA) = {home_dir.upper()}\\AppData\\Roaming
os.getenv(USERPROFILE) = {home_dir.lower()}
os.getenv(LocalAppData) = {home_dir}\\AppData\\Local"""

            result_windows_case = anonymize_system_information(test_windows_case)
            self.assertIn(
                'os.getenv(APPDATA) = %userprofile%\\AppData\\Roaming', result_windows_case)
            self.assertIn(
                'os.getenv(USERPROFILE) = %userprofile%', result_windows_case)
            self.assertIn(
                'os.getenv(LocalAppData) = %userprofile%\\AppData\\Local', result_windows_case)
            self.assertNotIn(home_dir.upper(), result_windows_case)
            self.assertNotIn(home_dir.lower(), result_windows_case)

        # Test that non-sensitive data remains unchanged
        test_unchanged = """BleachBit version = 5.1.0
gi.version = 3.55.0
GTK version = 3.24.51"""

        result_unchanged = anonymize_system_information(test_unchanged)
        self.assertEqual(test_unchanged, result_unchanged)

    def test_anonymize_preserves_structure(self):
        """Test that anonymization preserves the structure of system information"""
        original = get_system_information()
        anonymized = anonymize_system_information(original)

        # Both should have the same number of lines
        self.assertEqual(len(original.split('\n')),
                         len(anonymized.split('\n')))

        # Both should be non-empty strings
        self.assertIsString(original)
        self.assertIsString(anonymized)
        self.assertTrue(len(anonymized) > 0)
