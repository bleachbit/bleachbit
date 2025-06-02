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
import tempfile

from tests import common
from bleachbit.SystemInformation import get_system_information, get_version


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

    def test_gtk_settings_ini_scenarios(self):
        """Test GTK settings.ini scenarios in get_system_information"""
        if os.name == 'nt':
            env_key = 'LOCALAPPDATA'
        else:
            env_key = 'XDG_CONFIG_HOME'

        orig_env = os.environ.get(env_key)
        try:
            with tempfile.TemporaryDirectory() as temp_config_home:
                os.environ[env_key] = temp_config_home
                gtk_config_home = os.path.join(temp_config_home, 'gtk-3.0')
                gtk_settings_ini = os.path.join(gtk_config_home, 'settings.ini')

                # 1. Directory does not exist
                # (gtk_config_home not created)
                result = get_system_information()
                self.assertIn('GTK_CONFIG_HOME = not found', result)

                # 2. Directory exists but is empty (settings.ini not present)
                os.makedirs(gtk_config_home, exist_ok=True)
                result = get_system_information()
                self.assertIn(f'GTK_CONFIG_HOME = found', result)
                self.assertIn('GTK_SETTINGS_INI = not found', result)

                # 3. settings.ini exists but lacks [Settings] section
                with open(gtk_settings_ini, 'w', encoding='utf-8') as f:
                    f.write('# empty ini file\n')
                result = get_system_information()
                self.assertIn(f'GTK_SETTINGS_INI = 17 bytes', result)
                self.assertIn('GTK font name = not found in settings.ini', result)

                # 4. [Settings] section exists but no gtk-font-name
                with open(gtk_settings_ini, 'w', encoding='utf-8') as f:
                    f.write('[Settings]\n')
                result = get_system_information()
                self.assertIn('GTK font name = not found in settings.ini', result)

                # 5. [Settings] section with gtk-font-name key
                with open(gtk_settings_ini, 'w', encoding='utf-8') as f:
                    f.write('[Settings]\ngtk-font-name = Noto Sans 11\n')
                result = get_system_information()
                self.assertIn('GTK font name = Noto Sans 11', result)
        finally:
            if orig_env is None:
                del os.environ[env_key]
            else:
                os.environ[env_key] = orig_env


