# vim: ts=4:sw=4:expandtab

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
Test case for Common
"""

from tests import common

import os


class CommonTestCase(common.BleachbitTestCase):
    """Test case for Common."""

    def test_assertIsLanguageCode_hardcoded(self):
        """Test assertIsLanguageCode() using hard-coded values"""
        valid_codes = [
            'be@latin',
            'C.UTF-8',
            'C.utf8',
            'C',
            'de_DE.iso88591',
            'de-CH', # seen in Fedora in Docker
            'en-US',
            'en_US',
            'en',
            'fr_FR.utf8',
            'ja_JP.SJIS',
            'ko_KR.eucKR',
            'nb_NO.ISO-8859-1',
            'POSIX',
            'ru_RU.KOI8-R',
            'zh_Hant',
        ]

        invalid_codes = ['e', 'en_', 'english', 'en_US_', '123',
                         'en_us', 'en_US.',
                         'en_us.utf8',
                         'en_us.UTF-8',
                         'utf8',
                         'UTF-8',
                         '.utf8',
                         '.UTF-8',
                         '',
                         [],
                         0,
                         None]
        invalid_codes.extend([code + ' ' for code in valid_codes])
        invalid_codes.extend([' ' + code for code in valid_codes])

        for code in valid_codes:
            self.assertIsLanguageCode(code)

        for code in invalid_codes:
            with self.assertRaises(AssertionError, msg=f'Expected exception for {code}'):
                self.assertIsLanguageCode(code)

    def test_assertIsLanguageCode_live(self):
        """Test assertIsLanguageCode() using live data"""
        from bleachbit import locale_dir
        locale_dirs = list(set([locale_dir, '/usr/share/locale']))
        lang_codes = []
        # Skip directories that are not valid language codes
        skip_dirs = {'l10n'}
        for locale_dir in locale_dirs:
            if not os.path.isdir(locale_dir):
                continue
            for lang_code in os.listdir(locale_dir):
                if not os.path.isdir(os.path.join(locale_dir, lang_code)):
                    continue
                if lang_code in skip_dirs:
                    continue
                lang_codes.append(lang_code)
        if os.path.exists('/etc/locale.alias'):
            with open('/etc/locale.alias', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith('#'):
                        parts = line.split()
                        if len(parts) > 1:
                            lang_codes.append(parts[1])
        # /etc/locale.alias may list the qaa-qtz range, which is reserved for
        # private use rather than a concrete locale. Skip it if present.
        skip_alias_codes = {'qaa-qtz'}

        for lang_code in lang_codes:
            if lang_code in skip_alias_codes:
                continue
            self.assertIsLanguageCode(lang_code)

    def test_environment(self):
        """Test for important environment variables"""
        # useful for researching
        # grep -Poh "([\\$%]\w+)" cleaners/*xml | cut -b2- | sort | uniq -i
        # bleachbit/init.py sets these variables on posix, if they do not exist.
        envs = {'posix': ['HOME', 'USER', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME'],
                'nt': ['AppData', 'CommonAppData', 'Documents', 'ProgramFiles', 'UserProfile', 'WinDir']}
        for env in envs[os.name]:
            e = os.getenv(env)
            self.assertIsNotNone(e)
            self.assertNotEqual(e.strip(), '')

    def test_get_put_env(self):
        """Unit test for get_env() and put_env()"""
        self.assertIsNone(common.get_env('PUTENV_TEST'))

        common.put_env('PUTENV_TEST', '1')
        self.assertEqual('1', common.get_env('PUTENV_TEST'))

        common.put_env('PUTENV_TEST', None)
        self.assertIsNone(common.get_env('PUTENV_TEST'))

    def test_touch_file(self):
        """Unit test for touch_file"""
        fn = os.path.join(self.tempdir, 'test_touch_file')
        self.assertNotExists(fn)

        # Create empty file.
        common.touch_file(fn)
        from bleachbit.FileUtilities import getsize
        self.assertExists(fn)
        self.assertEqual(0, getsize(fn))

        # Increase size of file.
        fsize = 2**13
        with open(fn, "w") as f:
            f.write(' ' * fsize)
        self.assertEqual(fsize, getsize(fn))

        # Do not truncate.
        common.touch_file(fn)
        self.assertExists(fn)
        self.assertEqual(fsize, getsize(fn))
