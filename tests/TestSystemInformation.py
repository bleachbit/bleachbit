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

import os
import re
from unittest import mock


from tests import common
from bleachbit.SystemInformation import _get_home_dirs_to_anonymize, get_system_information, get_version, anonymize_system_information


class SystemInformationTestCase(common.BleachbitTestCase):
    """Test Case for module SystemInformation"""

    def test_get_system_information(self):
        """Test get_system_information"""
        # at least it does not crash
        ret = get_system_information()
        self.assertIsString(ret)

    @common.skipUnlessWindows
    def test_get_system_information_invalid_unicode_userprofile(self):
        invalid_userprofile = 'C:\\Users\\invalid\ud803'
        original_getenv = os.getenv

        def getenv(name, default=None):
            if name == 'USERPROFILE':
                return invalid_userprofile
            return original_getenv(name, default)

        with mock.patch('bleachbit.SystemInformation.os.getenv', side_effect=getenv):
            ret = get_system_information()

        encoded = ret.encode('utf-8')
        self.assertIn(b'C:\\Users\\invalid\\ud803', encoded)

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

    @common.skipIfWindows
    def test_anonymize_system_information_posix_non_root(self):
        """Test anonymization on POSIX with a non-root home directory."""
        home_dir = os.path.expanduser('~')
        if home_dir in ('/root', '/'):
            self.skipTest('requires a non-root POSIX home directory')

        test_input = f"""BleachBit version = 5.1.0
local_cleaners_dir = {home_dir}/.local/share/bleachbit/cleaners
options_dir = {home_dir}/.config/bleachbit
os.getenv(LOGNAME) = testuser
os.getenv(USER) = testuser
os.getenv(SUDO_UID) = 1000"""

        result = anonymize_system_information(test_input)

        self.assertIn(
            'local_cleaners_dir = ~/.local/share/bleachbit/cleaners', result)
        self.assertIn('options_dir = ~/.config/bleachbit', result)
        self.assertNotIn(home_dir, result)
        self.assertNotIn(home_dir.lower(), result.lower())
        self.assertIn('os.getenv(LOGNAME) = *non-root*', result)
        self.assertIn('os.getenv(USER) = *non-root*', result)
        self.assertIn('os.getenv(SUDO_UID) = 1000', result)

    @common.skipUnlessWindows
    def test_anonymize_system_information_windows(self):
        """Test anonymization on Windows with environment variables."""
        home_dir = os.path.expanduser('~')
        test_input = f"""os.getenv(APPDATA) = {home_dir.upper()}\\AppData\\Roaming
os.getenv(USERPROFILE) = {home_dir.lower()}
os.getenv(LocalAppData) = {home_dir}\\AppData\\Local"""

        result = anonymize_system_information(test_input)

        self.assertIn(
            'os.getenv(APPDATA) = %userprofile%\\AppData\\Roaming', result)
        self.assertIn(
            'os.getenv(USERPROFILE) = %userprofile%', result)
        self.assertIn(
            'os.getenv(LocalAppData) = %userprofile%\\AppData\\Local', result)
        self.assertIsNone(re.search(re.escape(home_dir),
                          result, flags=re.IGNORECASE))

    @common.skipUnlessWindows
    def test_anonymize_system_information_windows_short_path(self):
        """Test anonymization handles Windows short (8.3) paths."""
        # Create a directory with Unicode characters that will have a short path
        username = '我可以喝漂白剂而不伤及自身'
        unicode_dir = self.mkdir(username)

        try:
            import win32api
            short_path = win32api.GetShortPathName(unicode_dir)
        except (ImportError, OSError):
            self.skipTest('win32api not available or short path not supported')

        if short_path == unicode_dir:
            self.skipTest('Short path generation not enabled on this system')

        self.assertTrue(os.path.samefile(unicode_dir, short_path))

        with mock.patch('bleachbit.SystemInformation.os.path.expanduser', return_value=unicode_dir):
            from bleachbit.SystemInformation import _get_home_dirs_to_anonymize
            home_dirs = _get_home_dirs_to_anonymize()

        self.assertIn(short_path, home_dirs)
        self.assertTrue(os.path.samefile(home_dirs[0], home_dirs[1]))

        test_input = f"os.getenv(TMP) = {short_path}\\AppData\\Local\\Temp"
        with mock.patch('bleachbit.SystemInformation._get_home_dirs_to_anonymize',
                        return_value=[unicode_dir, short_path]):
            anonymized = anonymize_system_information(test_input)

        self.assertIn('%userprofile%', anonymized)
        self.assertNotIn(username, anonymized)
        self.assertNotIn(short_path, anonymized)
        self.assertNotIn(unicode_dir, anonymized)

    def test_anonymize_system_information_preserves_non_sensitive_data(self):
        """Test that non-sensitive data remains unchanged during anonymization."""
        test_unchanged = """BleachBit version = 5.1.0
gi.version = 3.55.0
GTK version = 3.24.51"""

        result = anonymize_system_information(test_unchanged)
        self.assertEqual(test_unchanged, result)

    def test_anonymize_system_information_preserves_root(self):
        """Root username should not be mislabeled as non-root."""
        test_input = """BleachBit version = 5.1.0
local_cleaners_dir = /root/.local/share/bleachbit/cleaners
options_dir = /root/.config/bleachbit
personal_cleaners_dir = /root/.config/bleachbit/cleaners
os.getenv(LOGNAME) = root
os.getenv(USER) = root
os.getenv(SUDO_UID) = 1000
os.path.expanduser(~") = /root"""
        result = anonymize_system_information(test_input)
        self.assertEqual(test_input, result)

    def test_anonymize_system_information_masks_real_home_dir(self):
        """Preserve /root while anonymizing the real non-root home directory."""
        # Mixing /root and user-specific paths is a normal scenario when
        # running from source `sudo python3 bleachbit.py`.
        test_input = """personal_cleaners_dir = /root/.config/bleachbit/cleaners
system_cleaners_dir = /home/regularuser/software/bleachbit/cleaners
__file__ = /home/regularuser/software/bleachbit/bleachbit/SystemInformation.py"""
        home_token = '~' if os.name == 'posix' else '%userprofile%'

        with mock.patch('bleachbit.SystemInformation._get_home_dirs_to_anonymize',
                        return_value=['/home/regularuser']):
            result = anonymize_system_information(test_input)

        self.assertIn(
            f'system_cleaners_dir = {home_token}/software/bleachbit/cleaners', result)
        self.assertIn(
            f'__file__ = {home_token}/software/bleachbit/bleachbit/SystemInformation.py', result)
        self.assertNotIn('/home/regularuser', result)

    def test_anonymize_preserves_structure(self):
        """Test that anonymization preserves the structure of system information"""
        # This is the only anonymization test with the real get_system_information().
        original = get_system_information()
        anonymized = anonymize_system_information(original)

        # Both should have the same number of lines
        self.assertEqual(len(original.split('\n')),
                         len(anonymized.split('\n')))

        # Both should have the same number of equal signs (key-value delimiters)
        self.assertEqual(original.count(' = '), anonymized.count(' = '))

        # Both should be non-empty strings
        self.assertIsString(original)
        self.assertIsString(anonymized)
        self.assertTrue(len(anonymized) > 0)
