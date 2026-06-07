# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for Common
"""

# standard imports
import os

# first party imports
from tests import common


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
            'de-CH',  # seen in Fedora in Docker
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
        for lang_code in lang_codes:
            if lang_code in common.SKIP_ALIAS_CODES:
                continue
            self.assertIsLanguageCode(lang_code)

    def test_environment(self):
        """Test for important environment variables"""
        # useful for researching
        # grep -Poh "([\\$%]\w+)" cleaners/*xml | cut -b2- | sort | uniq -i
        # bleachbit/init.py sets these variables on posix, if they do not exist.
        # Docker does not set USER
        envs = {'posix': ['HOME', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME'],
                'nt': ['AppData', 'CommonAppData', 'Documents', 'ProgramFiles', 'UserProfile', 'WinDir']}
        for env in envs[os.name]:
            e = os.getenv(env)
            self.assertIsNotNone(e, f"Environment variable {env} is not set")
            self.assertNotEqual(
                e.strip(), "", f"Environment variable {env} is empty")

    def test_get_put_env(self):
        """Unit test for get_env() and put_env()"""
        self.assertIsNone(common.get_env('PUTENV_TEST'))

        common.put_env('PUTENV_TEST', '1')
        self.assertEqual('1', common.get_env('PUTENV_TEST'))

        common.put_env('PUTENV_TEST', None)
        self.assertIsNone(common.get_env('PUTENV_TEST'))

    @common.skipUnlessWindows
    def test_get_opened_windows_titles(self):
        """Unit test for get_opened_windows_titles()"""
        titles = common.get_opened_windows_titles()

        self.assertIsInstance(titles, list, "Should return a list")
        self.assertGreater(len(titles), 0,
                           f"Should have at least one window title. Got: {titles}")

        # Verify all items are strings and none are empty
        for title in titles:
            self.assertIsInstance(
                title, str, f"All titles should be strings, got {type(title)}")
            self.assertGreater(len(title.strip()), 0,
                               f"Window title should not be empty or whitespace-only: '{title}'")

    def test_mock_missing_package(self):
        """Test mock_missing_package context manager"""
        # Inside the context, importing logging should raise an errorl.
        with common.mock_missing_package('logging', clear_prefixes=('bleachbit.CLI',)):
            with self.assertRaises(ImportError):
                import logging  # pylint: disable=import-outside-toplevel
            with self.assertRaises(ImportError):
                import bleachbit.CLI  # pylint: disable=import-outside-toplevel
            # Importing sys should be unaffected.
            import sys  # pylint: disable=import-outside-toplevel
        # Outside the context, importing should work.
        import logging  # pylint: disable=import-outside-toplevel
        import bleachbit.CLI  # pylint: disable=import-outside-toplevel

    def test_set_temporary_env(self):
        """Test set_temporary_env context manager"""
        # Test with an environment variable that was not set before.
        self.assertIsNone(os.environ.get('TEST_VAR_NEW'))
        with common.set_temporary_env('TEST_VAR_NEW', 'test_value'):
            self.assertEqual('test_value', os.environ.get('TEST_VAR_NEW'))
        # Outside the context, the environment variable should be unset.
        self.assertIsNone(os.environ.get('TEST_VAR_NEW'))

        # Test with an environment variable that was set before.
        os.environ['TEST_VAR_EXISTING'] = 'original_value'
        with common.set_temporary_env('TEST_VAR_EXISTING', 'override_value'):
            self.assertEqual('override_value',
                             os.environ.get('TEST_VAR_EXISTING'))
        # Outside the context, the environment variable should be restored.
        self.assertEqual('original_value', os.environ.get('TEST_VAR_EXISTING'))
        del os.environ['TEST_VAR_EXISTING']

    def test_run_with_invalid_slow_test_threshold(self):
        """Test that an invalid BLEACHBIT_SLOW_TEST_THRESHOLD does not crash the runner"""
        with common.set_temporary_env('BLEACHBIT_SLOW_TEST_THRESHOLD', 'not_a_number'):
            class DummyTestCase(common.BleachbitTestCase):
                def test_pass(self):
                    pass
            dummy = DummyTestCase('test_pass')
            result = dummy.run()
            self.assertTrue(result.wasSuccessful())

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
