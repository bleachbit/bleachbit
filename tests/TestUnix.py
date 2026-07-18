# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Unix
"""

from unittest import mock
import os
import random
import re
import subprocess
import tempfile
import unittest
from xml.dom.minidom import parseString

from tests import common
from bleachbit import logger
from bleachbit.FileUtilities import children_in_directory, exe_exists
from bleachbit.VFS import ListVFS
from bleachbit.Unix import (
    _is_broken_xdg_desktop_application,
    apt_autoclean,
    apt_autoremove,
    clear_snapd_cache,
    dnf_autoremove,
    dnf_clean,
    parse_dnf_freed_space,
    find_available_locales,
    find_best_locale,
    get_apt_size,
    get_distribution_name_version_distro,
    get_distribution_name_version_os_release,
    get_distribution_name_version_platform_freedesktop,
    get_distribution_name_version,
    get_purgeable_locales,
    get_trash_paths,
    is_broken_xdg_desktop,
    is_unix_display_protocol_wayland,
    journald_clean,
    JOURNALD_REGEX,
    LocaleCleanerPath,
    Locales,
    pacman_cache,
    root_is_not_allowed_to_X_session,
    snapd_is_active,
    snap_disabled_clean,
    snap_disabled_preview,
    snap_parse_list,
    rotated_logs,
    run_cleaner_cmd,
    wine_to_linux_path,
    yum_clean,
)


class FakeConfig:
    def __init__(self, options):
        self.options = options

    def has_option(self, section, option):
        return section in self.options and option in self.options[section]

    def get(self, section, option):
        return self.options[section][option]


class UnixTestCase(common.BleachbitTestCase):

    """Test case for module Unix"""

    def setUp(self):
        """Initialize unit tests"""
        self.locales = Locales()
        clear_snapd_cache()
        super().setUp()

    @common.skipIfWindows
    def test_apt(self):
        """Unit test for method apt_autoclean() and apt_autoremove()"""
        if 0 != os.geteuid() or not exe_exists('apt-get'):
            self.assertRaises(RuntimeError, apt_autoclean)
            self.assertRaises(RuntimeError, apt_autoremove)
        else:
            bytes_freed = apt_autoclean()
            self.assertIsInteger(bytes_freed)
            logger.debug('apt bytes cleaned %d', bytes_freed)
            bytes_freed = apt_autoremove()
            self.assertIsInteger(bytes_freed)
            logger.debug('apt bytes cleaned %d', bytes_freed)

    def test_apt_autoclean_mock(self):
        """Unit test for apt_autoclean() parsing of 'Del' lines"""
        # apt >= 3.2 (Ubuntu 26.04) prints a space between the size and units
        output = '\n'.join((
            'Del libcurl3t64-gnutls 8.18.0-1ubuntu2.2 [417 kB]',
            'Del libcurl4t64 8.18.0-1ubuntu2.2 [426 kB]',
            'Del curl 8.18.0-1ubuntu2.2 [272 kB]',
        ))
        with mock.patch('bleachbit.Unix.FileUtilities.exe_exists', return_value=True), \
                mock.patch('bleachbit.Unix.subprocess.check_output', return_value=output):
            self.assertEqual(apt_autoclean(), 417000 + 426000 + 272000)

        # older apt printed the size without a space
        output = 'Del curl 8.18.0-1ubuntu2.2 [272kB]'
        with mock.patch('bleachbit.Unix.FileUtilities.exe_exists', return_value=True), \
                mock.patch('bleachbit.Unix.subprocess.check_output', return_value=output):
            self.assertEqual(apt_autoclean(), 272000)

    @common.skipIfWindows
    def test_find_available_locales(self):
        """Unit test for method find_available_locales()"""
        locales = find_available_locales()
        self.assertIsInstance(locales, list)
        for locale in locales:
            self.assertIsLanguageCode(locale)

    def test_find_available_locales_mock(self):
        """Unit test for method find_available_locales() with mock"""
        mock_locales = ['C', 'C.utf8', 'en_US.utf8',
                        'es_MX', 'es_MX.iso88591', 'es_MX.utf8', 'POSIX']
        with mock.patch('bleachbit.Unix.General.run_external') as mock_run_external:
            mock_run_external.return_value = (
                0, "\n".join(mock_locales) + "\n", "")
            locales = find_available_locales()
            self.assertEqual(locales, mock_locales)
            mock_run_external.assert_called_once_with(['locale', '-a'])

    @mock.patch('locale.getlocale')
    @mock.patch('bleachbit.Unix.find_available_locales')
    def test_find_best_locale(self, mock_find_available_locales, mock_getlocale):
        """Unit test for method find_best_locale()"""
        mock_find_available_locales.return_value = [
            'C',
            'C.utf8',
            'de_DE.utf8',
            'en_US.iso88591',
            'en_US.utf8',
            'es_MX',
            'es_MX.iso88591',
            'es_MX.utf8',
            'nds_DE.utf8',
            'POSIX',
        ]
        mock_getlocale.return_value = ('en_US', 'UTF-8')
        for locale in ('en', 'en_US', 'en_US.utf8'):
            self.assertEqual(find_best_locale(locale), 'en_US.UTF-8')

        mock_find_available_locales.assert_called()
        mock_getlocale.assert_called()

        for locale in ('de', 'de_DE', 'de_DE.utf8'):
            self.assertEqual(find_best_locale(locale), 'de_DE.utf8')

        # Test language with a three-letter code.
        for locale in ('nds', 'nds_DE', 'nds_DE.utf8'):
            self.assertEqual(find_best_locale(locale), 'nds_DE.utf8')

        # Reverse the list.
        mock_find_available_locales.return_value = mock_find_available_locales.return_value[
            ::-1]
        for locale in ('en', 'en_US', 'en_US.utf8'):
            self.assertEqual(find_best_locale(locale), 'en_US.UTF-8')

        # ISO-8859-1 is less preferred than UTF-8
        mock_find_available_locales.return_value.remove('en_US.utf8')
        mock_getlocale.return_value = ('es_MX', 'UTF-8')
        for locale in ('en', 'en_US'):
            self.assertEqual(find_best_locale(locale), 'en_US.iso88591')

        mock_getlocale.return_value = ('es_MX', 'UTF-8')
        mock_find_available_locales.return_value = ['C', 'C.utf8', 'en_US.utf8',
                                                    'es_MX.iso88591', 'es_MX.utf8', 'POSIX']
        for locale in ('es', 'es_MX', 'es_MX.utf8'):
            self.assertEqual(find_best_locale(locale), 'es_MX.UTF-8')

        self.assertEqual(find_best_locale('C'), 'C')
        self.assertEqual(find_best_locale(''), 'C')
        self.assertEqual(find_best_locale('POSIX'), 'POSIX')

        self.assertRaises(AssertionError, find_best_locale, None)
        self.assertRaises(AssertionError, find_best_locale, [])

    @unittest.skipUnless(exe_exists('apt-get'),
                         'skipping tests for unavailable apt-get')
    def test_get_apt_size(self):
        """Unit test for method get_apt_size()"""
        size = get_apt_size()
        self.assertIsInteger(size)
        self.assertGreaterEqual(size, 0)

    @common.skipIfWindows
    def test_get_distribution_name_version(self):
        """Unit test for method get_distribution_name_version()"""
        ret_real = get_distribution_name_version()
        ret_platform_freedesktop = get_distribution_name_version_platform_freedesktop()
        ret_distro = get_distribution_name_version_distro()
        ret_os_release = get_distribution_name_version_os_release()

        for ret in (ret_real, ret_platform_freedesktop, ret_distro, ret_os_release):
            if ret is None:
                continue
            self.assertIsInstance(ret, str)
            self.assertGreater(len(ret), 0)
            self.assertLess(len(ret), 100)
            self.assertIn(' ', ret)
        if ret_platform_freedesktop and ret_os_release:
            self.assertEqual(ret_platform_freedesktop, ret_os_release)
        if ret_distro and ret_os_release:
            self.assertEqual(ret_distro, ret_os_release)

        self.assertIsNotNone(ret_real)

    @common.skipIfWindows
    def test_is_broken_xdg_desktop_real(self):
        """Unit test for is_broken_xdg_desktop()

        Check it does not crash on real-world .desktop files.
        """
        menu_dirs = ['/usr/share/applications',
                     '~/.local/share/applications',
                     '~/snap/steam/common/.local/share/applications',
                     '/usr/share/autostart',
                     '/usr/share/gnome/autostart',
                     '/usr/share/gnome/apps',
                     '/usr/share/mimelnk',
                     '/usr/share/applnk-redhat/',
                     '/usr/local/share/applications/',
                     '/usr/share/ubuntu-wayland/']
        for dirname in menu_dirs:
            for filename in [fn for fn in children_in_directory(os.path.expanduser(dirname), False)
                             if fn.endswith('.desktop')
                             ]:
                self.assertIsInstance(is_broken_xdg_desktop(filename), bool)

    @common.skipIfWindows
    @mock.patch('bleachbit.Unix.logger.info')
    def test_is_broken_xdg_desktop_other(self, mock_logger):
        """Unit test for is_broken_xdg_desktop() using non-.desktop files"""
        system_dirs = ['/usr/bin', '/usr/lib', '/etc']
        filenames = []
        for dirname in system_dirs:
            for filename in children_in_directory(dirname, False):
                if filename.endswith('.desktop'):
                    continue
                filenames.append(filename)
        sample_size = min(1000, len(filenames))
        sampled_filenames = random.sample(filenames, sample_size)
        for filename in sampled_filenames:
            result = is_broken_xdg_desktop(filename)
            self.assertTrue(
                result, msg=f"Expected is_broken_xdg_desktop({filename}) to return True, but got {result}")
            mock_logger.assert_called()
            mock_logger.reset_mock()

    def test_is_broken_xdg_desktop_wine(self):
        """Unit test for certain Wine .desktop file

        https://github.com/bleachbit/bleachbit/issues/1756
        """
        if not os.getenv('PATH'):
            self.skipTest("PATH environment variable is not set")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', prefix='bleachbit-xdg-') as tmp:
            tmp.write("""[Desktop Entry]
Name=What's New
Exec=env WINEPREFIX="/home/bem/.wine" wine C:\\\\windows\\\\command\\\\start.exe /Unix /home/bem/.wine/dosdevices/c:/users/Public/Start\\ Menu/Programs/Biet-O-Matic/What\\'s\\ New.lnk
Type=Application
StartupNotify=true
Path=/home/bem/.wine/dosdevices/c:/Program Files (x86)/Biet-O-Matic
Icon=6B19_WhatsNew.0""")
            tmp.flush()
            self.assertIsInstance(is_broken_xdg_desktop(tmp.name), bool)

    @mock.patch('bleachbit.FileUtilities.exe_exists')
    @common.skipIfWindows
    def test_is_broken_xdg_desktop_chrome(self, mock_exe_exists):
        """Unit test for certain Chrome .desktop file

        https://github.com/bleachbit/bleachbit/issues/1729
        """
        mock_exe_exists.return_value = True
        with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', prefix='bleachbit-xdg-') as tmp:
            tmp.write("""#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Terminal=false
Type=Application
Name=Google News
Exec=/opt/google/chrome/google-chrome --profile-directory=Default --app-id=abcdefghijklmnopqrstuvwxy
Icon=chrome-abcdefghijklmnopqrstuvwxy-Default
StartupWMClass=crx_abcdefghijklmnopqrstuvwxy""")
            tmp.flush()
            self.assertFalse(is_broken_xdg_desktop(tmp.name))

    @common.skipIfWindows
    def test_is_broken_xdg_desktop_chatgpt(self):
        """Unit test for certain ChatGPT .desktop file

        Linux Mint made this file for a Web App.

        I changed Exec from vivaldi-stale to test without mock.

        https://github.com/bleachbit/bleachbit/issues/1729
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', prefix='bleachbit-xdg-') as tmp:
            tmp.write("""[Desktop Entry]
Version=1.0
Name=ChatGPT
Comment=Web App
Exec=ls --app="https://chatgpt.com/" --class=WebApp-ChatGPT3878 --name=WebApp-ChatGPT3878
Terminal=false
X-MultipleArgs=false
Type=Application
Icon=/home/username/.local/share/icons/icons8-chatgpt-150.svg
Categories=GTK;Network;
MimeType=text/html;text/xml;application/xhtml_xml;
StartupWMClass=chatgpt.com
StartupNotify=true
X-WebApp-Browser=Vivaldi
X-WebApp-URL=https://chatgpt.com
X-WebApp-CustomParameters=
X-WebApp-Navbar=false
X-WebApp-PrivateWindow=false
X-WebApp-Isolated=false
Keywords=deepseek,chatgpt,gpt,gemini,ai
Hidden=false
NoDisplay=false
PrefersNonDefaultGPU=false""")
            tmp.flush()
            self.assertFalse(is_broken_xdg_desktop(tmp.name))


    @common.skipIfWindows
    def test_get_trash_paths(self):
        """Unit test for get_trash_paths()"""
        seen = []
        for p in get_trash_paths():
            seen.append(p)
            self.assertExists(p.path)
        self.assertEqual(len(seen), len(set(p.path for p in seen)), "Duplicate trash paths found")


    @common.skipIfWindows
    def test_desktop_valid_exe(self):
        """Unit test for .desktop file with valid Unix exe (not env)"""
        fake_config = FakeConfig({"Desktop Entry": {"Exec": "ls"}})
        if os.getenv('PATH'):
            result = _is_broken_xdg_desktop_application(
                fake_config, "foo.desktop")
            self.assertFalse(result)
        else:
            with self.assertRaises(RuntimeError):
                _is_broken_xdg_desktop_application(fake_config, "foo.desktop")

    def test_desktop_shlex_failure(self):
        """Unit test for .desktop file with shlex exception

        Malformed Exec values (unbalanced quotes) are undefined behavior per
        the XDG spec. The function returns False so the file is preserved
        rather than risking deletion of a working launcher.
        """
        fake_config = FakeConfig(
            {"Desktop Entry": {"Exec": "env ENVVAR=bar ls \"notepad.exe"}})
        result = _is_broken_xdg_desktop_application(
            fake_config, "foo.desktop")
        self.assertFalse(result)

    @mock.patch('bleachbit.FileUtilities.exe_exists')
    def test_desktop_quoted_exe_with_spaces(self, mock_exe_exists):
        """Regression test for #2118: AppImage .desktop with quoted Exec path

        Before the fix, the naive ``split(" ")[0]`` returned the executable
        path with its surrounding double-quotes still attached, so
        ``exe_exists`` reported it missing and the .desktop file was flagged
        for deletion.
        """
        mock_exe_exists.return_value = True
        fake_config = FakeConfig({"Desktop Entry": {
            "Exec": '"/home/user/Applications/AppManager" %u'}})
        result = _is_broken_xdg_desktop_application(
            fake_config, "com.github.AppManager.desktop")
        self.assertFalse(result)
        mock_exe_exists.assert_called_with('/home/user/Applications/AppManager')

    @mock.patch('bleachbit.FileUtilities.exe_exists')
    def test_desktop_quoted_exe_path_containing_spaces(self, mock_exe_exists):
        """Quoted Exec path that itself contains spaces must round-trip."""
        mock_exe_exists.return_value = True
        fake_config = FakeConfig({"Desktop Entry": {
            "Exec": '"/home/user/Applications/Converter NOW" %f'}})
        result = _is_broken_xdg_desktop_application(
            fake_config, "converter.desktop")
        self.assertFalse(result)
        mock_exe_exists.assert_called_with(
            '/home/user/Applications/Converter NOW')

    def test_desktop_empty_exec(self):
        """Whitespace-only Exec is treated as broken."""
        fake_config = FakeConfig({"Desktop Entry": {"Exec": "   "}})
        result = _is_broken_xdg_desktop_application(
            fake_config, "foo.desktop")
        self.assertTrue(result)

    @common.skipIfWindows
    def test_desktop_env_valid(self):
        """Unit test for .desktop file with valid env Exec"""
        fake_config = FakeConfig(
            {"Desktop Entry": {"Exec": "env FOO=bar ls /usr/bin"}})
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
        self.assertFalse(result)

    @mock.patch('bleachbit.FileUtilities.exe_exists')
    def test_desktop_missing_wine(self, mock_exe_exists):
        """Unit test for .desktop file without Wine installed"""
        mock_exe_exists.side_effect = [
            True, False]  # First True for 'env', then False for 'wine'
        fake_config = FakeConfig(
            {"Desktop Entry": {"Exec": "env WINEPREFIX=/some/path wine notepad.exe"}})
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
        self.assertTrue(result)
        mock_exe_exists.assert_has_calls([mock.call('env'), mock.call('wine')])

    @mock.patch('os.path.exists')
    @mock.patch('bleachbit.FileUtilities.exe_exists')
    def test_desktop_wine_valid_windows_exe(self, mock_exe_exists, mock_path_exists):
        """Unit test for .desktop file pointing to valid Windows application"""
        fake_config = FakeConfig({"Desktop Entry": {
                                 "Exec": r"/usr/bin/env WINEPREFIX=/some/path wine C:\\Windows\\notepad.exe"}})
        mock_exe_exists.return_value = True  # for env and wine
        mock_path_exists.return_value = True  # for notepad
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
        self.assertFalse(result)

    @mock.patch('os.path.exists')
    @mock.patch('bleachbit.FileUtilities.exe_exists')
    def test_desktop_env_missing_windows_exe(self, mock_exe_exists, mock_path_exists):
        """Unit test for .desktop file with env pointing to missing Windows application"""
        fake_config = FakeConfig({"Desktop Entry": {
                                 "Exec": "env WINEPREFIX=/some/path wine_exe does_not_exist.exe"}})
        mock_exe_exists.return_value = True  # for env and wine
        mock_path_exists.return_value = False  # for does_not_exist.exe
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
        self.assertTrue(result)

    def test_desktop_missing_keys(self):
        """Unit test for .desktop file missing keys"""

        test_cases = [
            ("", "Blank file"),
            ("[Desktop Entry]\n", "missing Type and Name"),
            ("[Desktop Entry]\nType=Application\n", "missing Name key"),
            ("[Desktop Entry]\nName=Test\n", "missing Type key"),
            ("[Desktop Entry]\nType=Link\nName=Test\n",
             "Type=Link and missing URL key"),
            ("[Desktop Entry]\nType=Application\nName=Test",
             "Type=Application and missing Exec"),
            ("garbage", "Not a .desktop file"),
            ("#/bin/bash\necho hello world", "Bash script")
        ]

        for content, description in test_cases:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
                tf.write(content)
                tf.flush()
                result = is_broken_xdg_desktop(tf.name)
                self.assertTrue(result, f"Failed case: {description}")
            os.unlink(tf.name)

    @common.skipIfWindows
    def test_journald_clean(self):
        if not exe_exists('journalctl'):
            self.assertRaises(RuntimeError, journald_clean)
        else:
            try:
                journald_clean()
            except RuntimeError as rte:
                # On my system as a regular user, this succeeds.
                # On Travis running Trusty, this worked.
                # On Travis running Xenial, there is a permissions error.
                if common.have_root():
                    raise rte

    def test_journald_regex(self):
        """Test the regex for journald_clean()"""
        positive_cases = ('Vacuuming done, freed 0B of archived journals on disk.',
                          'Vacuuming done, freed 1K of archived journals on disk.',
                          'Vacuuming done, freed 100.0M of archived journals on disk.',
                          'Vacuuming done, freed 1G of archived journals on disk.',
                          'Vacuuming done, freed 0B of archived journals from /run/log/journal.',
                          'Vacuuming done, freed 1.0G of archived journals from /var/log/journal/123abc.')
        regex = re.compile(JOURNALD_REGEX)
        for pos in positive_cases:
            self.assertTrue(regex.match(pos))
        negative_cases = ('Deleted archived journal /var/log/journal/123/system@123-123.journal~ (56.0M).',
                          'Archived and active journals take up 100.0M on disk.')
        for neg in negative_cases:
            self.assertFalse(regex.match(neg))

    def test_get_purgeable_locales(self):
        """Unit test for method get_purgeable_locales()"""
        # 'en' implies 'en_US'
        locales_to_keep = ['en', 'en_AU', 'en_CA', 'en_GB']
        purgeable_locales = get_purgeable_locales(locales_to_keep)
        self.assertIsInstance(purgeable_locales, frozenset)
        self.assertIn('es', purgeable_locales)
        self.assertIn('pt', purgeable_locales)
        self.assertIn('de', purgeable_locales)
        for keep in locales_to_keep + ['en_US']:
            self.assertNotIn(keep, purgeable_locales)

        # 'en_US' keeps 'en' but discards 'en_AU'.
        purgeable_locales = get_purgeable_locales(['en_US'])
        self.assertNotIn('en', purgeable_locales)
        self.assertNotIn('en_US', purgeable_locales)
        self.assertIn('en_AU', purgeable_locales)

    def test_locale_regex(self):
        """Unit test for locale_to_language()"""
        tests = {'en': 'en',
                 'en_US': 'en',
                 'en_US@piglatin': 'en',
                 'en_US.utf8': 'en',
                 'ko_KR.eucKR': 'ko',
                 'pl.ISO8859-2': 'pl',
                 'zh_TW.Big5': 'zh'}
        regex = re.compile('^' + Locales.localepattern + '$')
        for locale, tlc in tests.items():
            m = regex.match(locale)
            self.assertIsNotNone(m, 'expected positive match for ' + locale)
            self.assertEqual(m.group("locale"), tlc)
        for test in ['default', 'C', 'English', 'ru_RU.txt', 'ru.txt']:
            self.assertIsNone(regex.match(
                test), 'expected negative match for ' + test)

    @common.skipIfWindows
    def test_localization_paths(self):
        """Unit test for localization_paths()"""
        configpath = parseString(
            '<path location="/usr/share/locale/" filter="*" />').firstChild
        self.locales.add_xml(configpath)
        counter = 0
        for path in self.locales.localization_paths(['en', 'en_AU', 'en_CA', 'en_GB']):
            self.assertLExists(path)
            self.assertTrue(path.startswith('/usr/share/locale'))
            # /usr/share/locale/en_* should be ignored
            self.assertEqual(path.find('/en_'), -1, 'expected path ' + path +
                             ' to not contain /en_')
            counter += 1
        self.assertGreater(counter, 0, 'Zero files deleted by localization cleaner. ' +
                                       'This may be an error unless you really deleted all the files.')

    @common.skipIfWindows
    def test_fakelocalizationdirs(self):
        """Create a faked localization hierarchy and clean it afterwards"""

        keepdirs = [
            'important_dontdelete',
            'important_dontdelete/ru',
            'delete',
            'delete/locale',
            'delete/locale/en',
            'delete/dummyfiles',
            'foobar',
            'foobar/locale']
        nukedirs = [
            'delete/locale/ru',
            'foobar/locale/ru']
        keepfiles = [
            'delete/dummyfiles/dontdeleteme_ru.txt',
            'important_dontdelete/exceptthisone_ru.txt',
            'delete/dummyfiles/en.txt',
            'delete/dummyfiles/ru.dic']
        nukefiles = [
            'delete/dummyfiles/ru.txt',
            'delete/locale/ru_RU.UTF8.txt']
        for path in keepdirs + nukedirs:
            os.mkdir(os.path.join(self.tempdir, path))
        for path in keepfiles + nukefiles:
            self.write_file(path)

        configxml = '<path directoryregex="^.*$">' \
                    '  <path directoryregex="^(locale|dummyfiles)$">' \
                    '    <path location="." filter="*" />' \
                    r'    <regexfilter postfix="\.txt" />' \
                    '  </path>' \
                    '</path>'
        config = parseString(configxml)
        self.locales._paths = LocaleCleanerPath(self.tempdir)
        self.locales.add_xml(config.firstChild, None)
        # normpath because paths may contain ./
        deletelist = [os.path.normpath(
            path) for path in self.locales.localization_paths(['en', 'de'])]
        for path in keepdirs + keepfiles:
            self.assertNotIn(os.path.join(self.tempdir, path), deletelist)
        for path in nukedirs + nukefiles:
            self.assertIn(os.path.join(self.tempdir, path), deletelist)

    @common.skipIfWindows
    def test_rotated_logs_real(self):
        """Unit test for rotated_logs()"""
        for path in rotated_logs():
            self.assertLExists(
                path, f"Rotated log path '{path}' does not exist")

    @mock.patch('bleachbit.FileUtilities.whitelisted')
    @mock.patch('bleachbit.FileUtilities.children_in_directory')
    def test_rotated_logs_mock(self, mock_cid, mock_whitelisted):
        mock_whitelisted.side_effect = lambda path: path.startswith(
            '/var/log/whitelisted/')
        expected_delete = [
            '/var/log/apt/history.log.1.gz',
            '/var/log/auth.log.3.old',
            '/var/log/dmesg.0',
            '/var/log/dmesg.1.gz',
            '/var/log/foo.gz',
            '/var/log/foo.old',
            '/var/log/foo/bar.0',
            '/var/log/foo/bar.gz',
            '/var/log/foo/bar.old',
            '/var/log/kern.log-20230601',
            '/var/log/messages-20090118.bz2',
            '/var/log/messages-20090118.gz',
            '/var/log/messages-20090118.xz',
            '/var/log/messages-20090118',
            '/var/log/messages.2.bz2',
            '/var/log/samba/log.smbd-20250126.gz',
            '/var/log/syslog.1',
            '/var/log/syslog.2.xz',
            '/var/log/cups/access_log.9'

        ]
        expected_keep = [
            '/var/log/dmesg',
            '/var/log/packages/foo.0',
            '/var/log/removed_packages/foo.0',
            '/var/log/removed_scripts/foo.0',
            '/var/log/samba/log.192.168.0.1',
            '/var/log/samba/log.172.17.0.1',
            '/var/log/scripts/foo.0',
            '/var/log/syslog',
            '/var/log/sysstat/sar24',
            '/var/log/whitelisted/foo.0'
        ]
        mock_cid.return_value = iter(expected_delete + expected_keep)
        result = list(rotated_logs())
        self.assertEqual(set(result), set(expected_delete))
        for path in expected_keep:
            self.assertNotIn(path, result)
        mock_cid.assert_called_once_with('/var/log')
        mock_whitelisted.assert_called()

    @common.skipIfWindows
    def test_run_cleaner_cmd(self):
        """Unit test for run_cleaner_cmd()"""
        self.assertRaises(RuntimeError, run_cleaner_cmd,
                          '/hopethisdoesntexist', [])
        # Use absolute path in case like `env -i`.
        which_sh = 'sh' if exe_exists('sh') else '/usr/bin/sh'
        self.assertRaises(subprocess.CalledProcessError, run_cleaner_cmd,
                          which_sh, ['-c', 'echo errormsg; false'])
        # test if regexes for invalid lines work
        self.assertRaises(RuntimeError, run_cleaner_cmd, 'echo', ['This is an invalid line'],
                          error_line_regexes=['invalid'])

        freed_space_regex = r'^Freed ([\d.]+[kMT]?B)'
        lines = ['Test line',
                 'Freed 100B on your hard drive',
                 'Freed 1.9kB, hooray!',
                 'Fred 12MB']
        freed_space = run_cleaner_cmd(
            'echo', ['\n'.join(lines)], freed_space_regex)
        self.assertEqual(freed_space, 2000)

    @common.skipIfWindows
    def test_wine_to_linux_path(self):
        """Unit test for wine_to_linux_path()"""
        wineprefix = "/home/foo/.wine"
        windows_pathname = "C:\\Program Files\\NSIS\\NSIS.exe"
        result = "/home/foo/.wine/drive_c/Program Files/NSIS/NSIS.exe"
        self.assertEqual(wine_to_linux_path(
            wineprefix, windows_pathname), result)

    @common.skipIfWindows
    def test_yum_clean(self):
        """Unit test for yum_clean()"""
        if 0 != os.geteuid() or os.path.exists('/var/run/yum.pid') \
                or not exe_exists('yum'):
            self.assertRaises(RuntimeError, yum_clean)
        else:
            bytes_freed = yum_clean()
            self.assertIsInteger(bytes_freed)
            logger.debug('yum bytes cleaned %d', bytes_freed)

    @common.skipIfWindows
    def test_dnf_clean(self):
        """Unit test for dnf_clean()"""
        if 0 != os.geteuid() or os.path.exists('/var/run/dnf.pid') \
                or not exe_exists('dnf'):
            self.assertRaises(RuntimeError, dnf_clean)
        else:
            bytes_freed = dnf_clean()
            self.assertIsInteger(bytes_freed)
            logger.debug('dnf bytes cleaned %d', bytes_freed)

    @common.skipIfWindows
    @mock.patch('bleachbit.Language.setup_translation')
    @mock.patch('bleachbit.Unix.FileUtilities.exe_exists')
    @mock.patch('bleachbit.Unix.General.run_external')
    @mock.patch('bleachbit.Unix.FileUtilities.getsizedir')
    @mock.patch('bleachbit.Unix.os.path')
    def test_dnf_clean_mock(self, mock_path, mock_getsizedir, mock_run,
                            mock_exe, mock_setup):
        """Unit test for dnf_clean() with mock for DNF4 and DNF5"""
        # Don't call setup_translation() for real because it uses
        # os.path.exists(), which is mocked here.
        mock_setup.return_value = None
        mock_exe.return_value = True
        mock_path.exists.return_value = True
        # dnf.pid present -> RuntimeError
        self.assertRaises(RuntimeError, dnf_clean)

        mock_path.exists.return_value = False

        # DNF5 reports freed space directly in its summary line, so the
        # getsizedir fallback (post-run measurement) must not be used.
        # The pre-run measurement still happens once for the DNF4 fallback.
        mock_run.return_value = (
            0, 'Removed 12 files, 3 directories '
            '(total of 25 MiB). 0 errors occurred.\n', '')
        mock_getsizedir.reset_mock()
        self.assertEqual(dnf_clean(), 25 * 1024 ** 2)
        self.assertEqual(mock_getsizedir.call_count, 1)

        # DNF5 "nothing to clean" still parses to 0 bytes.
        mock_run.return_value = (
            0, 'Removed 0 files, 0 directories '
            '(total of 0 B). 0 errors occurred.\n', '')
        self.assertEqual(dnf_clean(), 0)

        # DNF4 does not report freed space, so fall back to the cache
        # directory size difference (old - new).
        mock_run.return_value = (0, 'Cleaning repos: ', '')
        mock_getsizedir.side_effect = [1000, 250]
        self.assertEqual(dnf_clean(), 750)

        # DNF4 invalid output line raises RuntimeError.
        mock_run.return_value = (
            0, 'You need to be root to perform this command.\n', '')
        mock_getsizedir.side_effect = None
        mock_getsizedir.return_value = 1000
        self.assertRaises(RuntimeError, dnf_clean)

        # DNF4 non-zero exit code raises RuntimeError.
        mock_run.return_value = (1, '', 'some error')
        self.assertRaises(RuntimeError, dnf_clean)

        # dnf not installed -> RuntimeError.
        mock_exe.return_value = False
        self.assertRaises(RuntimeError, dnf_clean)

    @common.skipIfWindows
    def test_dnf_autoremove_real(self):
        """Unit test for dnf_autoremove() with real dnf"""
        if 0 != os.geteuid() or os.path.exists('/var/run/dnf.pid') \
                or not exe_exists('dnf'):
            self.assertRaises(RuntimeError, dnf_clean)
        else:
            bytes_freed = dnf_autoremove()
            self.assertIsInteger(bytes_freed)
            logger.debug('dnf bytes cleaned %d', bytes_freed)

    @common.skipIfWindows
    @mock.patch('bleachbit.Language.setup_translation')
    @mock.patch('bleachbit.Unix.os.path')
    @mock.patch('bleachbit.General.run_external')
    def test_dnf_autoremove_mock(self, mock_run, mock_path, mock_setup):
        """Unit test for dnf_autoremove() with mock"""
        # Don't call setup_translation() for real because it uses
        # os.path.exists(), which is mocked here.
        mock_setup.return_value = None
        mock_path.exists.return_value = True
        self.assertRaises(RuntimeError, dnf_autoremove)

        mock_path.exists.return_value = False
        mock_run.return_value = (1, 'stdout', 'stderr')
        self.assertRaises(RuntimeError, dnf_autoremove)

        mock_run.return_value = (0, 'Nothing to do.', 'stderr')
        bytes_freed = dnf_autoremove()
        self.assertEqual(bytes_freed, 0)

        mock_run.return_value = (
            0, 'Remove  112 Packages\nFreed space: 299 M\n', 'stderr')
        bytes_freed = dnf_autoremove()
        # dnf's format_number() uses 1024-based binary units, so 299 M
        # means 299 * 1024**2, not 299 * 1000**2.
        self.assertEqual(bytes_freed, 299 * 1024 ** 2)

        # DNF5 autoremove reports the net freed size in its summary line.
        mock_run.return_value = (
            0, 'After this operation, 299 MiB will be freed '
            '(install 0 B, remove 299 MiB).\n', 'stderr')
        bytes_freed = dnf_autoremove()
        self.assertEqual(bytes_freed, 299 * 1024 ** 2)

    @common.skipIfWindows
    def test_parse_dnf_freed_space(self):
        """Directly test parse_dnf_freed_space()"""
        # DNF4 autoremove: "Freed space: <n> <unit>"
        dnf4_cases = [
            ('Freed space: 0  \n', 0),
            ('Freed space: 500  \n', 500),
            ('Freed space: 999  \n', 999),
            ('Freed space: 1.5 k\n', int(1.5 * 1024)),
            ('Freed space: 10 k\n', 10 * 1024),
            ('Freed space: 5.0 M\n', int(5.0 * 1024 ** 2)),
            ('Freed space: 299 M\n', 299 * 1024 ** 2),
            ('Freed space: 1.0 G\n', int(1.0 * 1024 ** 3)),
            ('Freed space: 1.5 T\n', int(1.5 * 1024 ** 4)),
            ('Nothing to do.\n', None),
            ('', None),
        ]
        # DNF5 autoremove: "After this operation, <n> <unit> will be freed
        # (install <n> <unit>, remove <n> <unit>)."
        dnf5_autoremove_cases = [
            ('After this operation, 0 B will be freed '
             '(install 0 B, remove 0 B).\n', 0),
            ('After this operation, 500 B will be freed '
             '(install 0 B, remove 500 B).\n', 500),
            ('After this operation, 1 KiB will be freed '
             '(install 0 B, remove 1 KiB).\n', 1024),
            ('After this operation, 10 KiB will be freed '
             '(install 0 B, remove 10 KiB).\n', 10 * 1024),
            ('After this operation, 5 MiB will be freed '
             '(install 0 B, remove 5 MiB).\n', 5 * 1024 ** 2),
            ('After this operation, 299 MiB will be freed '
             '(install 0 B, remove 299 MiB).\n', 299 * 1024 ** 2),
            ('After this operation, 1 GiB will be freed '
             '(install 0 B, remove 1 GiB).\n', 1024 ** 3),
            ('After this operation, 2 TiB will be freed '
             '(install 0 B, remove 2 TiB).\n', 2 * 1024 ** 4),
            ('After this operation, 1.5 MiB will be freed '
             '(install 0 B, remove 1.5 MiB).\n', int(1.5 * 1024 ** 2)),
            ('Nothing to do.\n', None),
            ('', None),
        ]
        # DNF5 "clean all": "Removed <f> files, <d> directories (total of
        # <n> <unit>). <n> errors occurred."
        dnf5_clean_cases = [
            ('Removed 0 files, 0 directories (total of 0 B). '
             '0 errors occurred.\n', 0),
            ('Removed 1 files, 0 directories (total of 500 B). '
             '0 errors occurred.\n', 500),
            ('Removed 1 files, 0 directories (total of 999 B). '
             '0 errors occurred.\n', 999),
            ('Removed 1 files, 0 directories (total of 1 KiB). '
             '0 errors occurred.\n', 1024),
            ('Removed 5 files, 1 directories (total of 10 KiB). '
             '0 errors occurred.\n', 10 * 1024),
            ('Removed 5 files, 1 directories (total of 5 MiB). '
             '0 errors occurred.\n', 5 * 1024 ** 2),
            ('Removed 5 files, 1 directories (total of 299 MiB). '
             '0 errors occurred.\n', 299 * 1024 ** 2),
            ('Removed 5 files, 1 directories (total of 1 GiB). '
             '0 errors occurred.\n', 1024 ** 3),
            ('Removed 5 files, 1 directories (total of 2 TiB). '
             '0 errors occurred.\n', 2 * 1024 ** 4),
            ('Removed 12 files, 3 directories (total of 25 MiB). '
             '0 errors occurred.\n', 25 * 1024 ** 2),
            ('Cache directory "/var/cache/libdnf5" does not exist. '
             'Nothing to clean.\n', None),
            ('', None),
        ]
        for output, expected in dnf4_cases + dnf5_autoremove_cases \
                + dnf5_clean_cases:
            with self.subTest(output=output.strip()):
                self.assertEqual(parse_dnf_freed_space(output), expected)

    @common.skipIfWindows
    def test_pacman_cache(self):
        """Unit test for pacman_cache()"""
        if 0 != os.geteuid() or os.path.exists('/var/lib/pacman/db.lck') \
                or not exe_exists('paccache'):
            self.assertRaises(RuntimeError, pacman_cache)
        else:
            bytes_freed = pacman_cache()
            self.assertIsInteger(bytes_freed)
            logger.debug('pacman bytes cleaned %d', bytes_freed)

    @common.skipIfWindows
    @mock.patch('bleachbit.Unix.General.run_external')
    @mock.patch('bleachbit.Unix.exe_exists')
    @mock.patch('bleachbit.Unix.os.path')
    def test_pacman_cache_mock(self, mock_path, mock_exe_exists, mock_run):
        """Unit test pacman_cache() parse logic without pacman installed"""
        mock_path.exists.return_value = False
        mock_exe_exists.return_value = True
        mock_run.return_value = (
            0,
            "==> finished: 3 packages removed (42.31 M freed)\n",
            ''
        )

        bytes_freed = pacman_cache()
        self.assertEqual(bytes_freed, 42310000)

        mock_run.assert_called_once_with(['paccache', '-rk0'])

        # real paccache reports binary units (MiB), not decimal (M)
        mock_run.return_value = (
            0,
            "==> finished: 3 packages removed (42.31 MiB freed)\n",
            ''
        )
        bytes_freed = pacman_cache()
        self.assertEqual(bytes_freed, 44365250)

    def test_snapd_is_active_no_snap(self):
        """Unit test for snapd_is_active() when snap is not installed"""
        with mock.patch('bleachbit.Unix.exe_exists', return_value=False):
            self.assertFalse(snapd_is_active())

    def test_snapd_is_active_no_systemctl(self):
        """Unit test for snapd_is_active() when systemctl is not installed"""
        with mock.patch('bleachbit.Unix.exe_exists', side_effect=lambda x: x == 'snap'):
            self.assertFalse(snapd_is_active())

    def test_snapd_is_active_inactive(self):
        """Unit test for snapd_is_active() when snapd.socket is inactive"""
        with mock.patch('bleachbit.Unix.exe_exists', return_value=True), \
                mock.patch('bleachbit.General.run_external', return_value=(1, '', '')):
            self.assertFalse(snapd_is_active())

    def test_snapd_is_active_active(self):
        """Unit test for snapd_is_active() when snapd.socket is active"""
        with mock.patch('bleachbit.Unix.exe_exists', return_value=True), \
                mock.patch('bleachbit.General.run_external', return_value=(0, '', '')):
            self.assertTrue(snapd_is_active())

    def test_snapd_is_active_timeout(self):
        """Unit test for snapd_is_active() timeout handling"""
        with mock.patch('bleachbit.Unix.exe_exists', return_value=True), \
                mock.patch('bleachbit.General.run_external') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                ['systemctl', 'is-active', '--quiet', 'snapd.socket'], 5)
            self.assertFalse(snapd_is_active())

    @common.skipIfWindows
    @common.skipUnlessDestructive
    def test_snap_disabled_clean(self):
        """Unit test for snap_disabled_clean()"""
        if not exe_exists('snap'):
            self.assertRaises(RuntimeError, snap_disabled_clean)
        else:
            bytes_freed = snap_disabled_clean()
            self.assertIsInteger(bytes_freed)
            logger.debug('snap disabled bytes freed %d', bytes_freed)

    @common.skipIfWindows
    def test_snap_disabled_preview(self):
        """Unit test for snap_disabled_preview()"""
        if not exe_exists('snap'):
            self.assertRaises(RuntimeError, snap_disabled_preview)
        else:
            bytes_freed = snap_disabled_preview()
            self.assertIsInstance(bytes_freed, int)
            logger.debug('snap disabled bytes freed %d', bytes_freed)

    @common.skipIfWindows
    def test_snap_timeout(self):
        """Unit test for snap_disabled_full() timeout handling"""
        with mock.patch('bleachbit.Unix.snapd_is_active', return_value=True), \
                mock.patch('bleachbit.General.run_external') as mock_run:
            # Simulate snap list --all hanging
            mock_run.side_effect = subprocess.TimeoutExpired(
                ['snap', 'list', '--all'], 10)
            with self.assertRaises(RuntimeError) as cm:
                snap_disabled_preview()
            self.assertIn('timed out', str(cm.exception))

    def test_snap_parse_list_real_data(self):
        """Unit test for snap_parse_list() with real 'snap list --all' output"""
        sample = (
            "Name                       Version                         Rev    Tracking            Publisher             Notes\n"
            "astral-uv                  0.8.9                           902    latest/stable       lengau                classic\n"
            "astral-uv                  0.7.21                          759    latest/stable       lengau                disabled,classic\n"
            "bare                       1.0                             5      latest/stable       canonical**           base\n"
            "cheese                     44.1                            78     latest/stable       ken-vandine*          -\n"
            "cheese                     44.1                            76     latest/stable       ken-vandine*          disabled\n"
        )
        expected = [
            ('astral-uv', '759'),
            ('cheese', '76')
        ]
        result = snap_parse_list(sample)
        self.assertEqual(result, expected)

    def test_snap_parse_list_no_snaps_message(self):
        """Unit test for snap_parse_list() with 'no snaps installed' output"""
        sample = "No snaps are installed yet. Try 'snap install hello-world'.\n"
        result = snap_parse_list(sample)
        self.assertEqual(result, [])

    @common.skipIfWindows
    def test_is_unix_display_protocol_wayland_no_mock(self):
        """Unit test for test_is_unix_display_protocol_wayland() with no mock"""
        ret = is_unix_display_protocol_wayland()
        self.assertIsInstance(ret, bool)

    @common.skipIfWindows
    def test_is_unix_display_protocol_wayland_mock_env(self):
        """Unit test for test_is_unix_display_protocol_wayland() by mocking os.environ"""
        # The environment variables take precedence.
        with mock.patch.dict('os.environ', {'XDG_SESSION_TYPE': 'x11'}, clear=True):
            self.assertFalse(is_unix_display_protocol_wayland())
        with mock.patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}, clear=True):
            self.assertTrue(is_unix_display_protocol_wayland())
        with mock.patch.dict('os.environ', {'WAYLAND_DISPLAY': 'yes'}, clear=True):
            self.assertTrue(is_unix_display_protocol_wayland())

    @common.skipIfWindows
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_is_unix_display_protocol_wayland_mock_no_env(self):
        """Unit test for test_is_unix_display_protocol_wayland() by clearing os.environ"""
        self.assertEqual(len(os.environ), 0)

        # Check that it does not throw an exception.
        is_unix_display_protocol_wayland()

        display_protocol = None

        def side_effect_func(value):
            if len(value) == 1:
                return (0, 'SESSION  UID USER   SEAT  TTY \n      2 1000 debian seat0 tty2\n\n1 sessions listed.\n', '')
            if len(value) > 1:
                return (0, f'Type={display_protocol}\n', '')
            assert False  # should never reach here

        for display_protocol, assert_method in [['wayland', self.assertTrue], ['donotexist', self.assertFalse]]:
            with mock.patch('bleachbit.General.run_external') as mock_run_external:
                mock_run_external.side_effect = side_effect_func
                is_wayland = is_unix_display_protocol_wayland()
                assert mock_run_external.called
            self.assertIsInstance(is_wayland, bool)
            assert_method(is_wayland)

        with mock.patch('bleachbit.General.run_external') as mock_run_external:
            mock_run_external.side_effect = FileNotFoundError('not found')
            self.assertFalse(is_unix_display_protocol_wayland())
            assert mock_run_external.called

        with mock.patch('bleachbit.General.run_external') as mock_run_external:
            mock_run_external.side_effect = lambda a: (1, None, None)
            self.assertFalse(is_unix_display_protocol_wayland())
            assert mock_run_external.called

        with mock.patch('bleachbit.General.run_external') as mock_run_external:
            mock_run_external.side_effect = lambda a: (
                0, 'test of invalid output from loginctl', None)
            self.assertFalse(is_unix_display_protocol_wayland())
            assert mock_run_external.called

    @common.skipIfWindows
    def test_xhost_autorized_root(self):
        error_code = None

        def side_effect_func(*args, **_kwargs):
            self.assertEqual(args[0][0], 'xhost')
            return (error_code,
                    '',
                    '')

        for error_code, expected_root_autorized in [[1, True], [0, False]]:
            with mock.patch('bleachbit.General.run_external') as mock_run_external:
                mock_run_external.side_effect = side_effect_func
                root_autorized = root_is_not_allowed_to_X_session()
            self.assertIsInstance(root_autorized, bool)
            self.assertEqual(expected_root_autorized, root_autorized)

    @common.skipIfWindows
    def test_get_trash_paths_snap_symlink(self):
        """Do not follow symlinks in ~/snap when finding trash"""
        with common.set_temporary_env('HOME', self.tempdir):
            # Create snap structure: snap/app/238/.local/share/Trash/files/
            real_rev = os.path.join(self.tempdir, 'snap', 'app', '238')
            trash_files = os.path.join(
                real_rev, '.local', 'share', 'Trash', 'files')
            os.makedirs(trash_files)
            test_file = os.path.join(trash_files, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            # Create symlink current -> 238
            current_dir = os.path.join(self.tempdir, 'snap', 'app', 'current')
            os.symlink('238', current_dir)

            paths = [cmd.path for cmd in get_trash_paths()]
            # Should find the test file through the real path
            self.assertIn(test_file, paths)
            # Should NOT find it through the symlink
            symlink_path = os.path.join(
                self.tempdir, 'snap', 'app', 'current', '.local', 'share',
                'Trash', 'files', 'test.txt')
            self.assertNotIn(symlink_path, paths)


class LocalizationsTestCase(common.BleachbitTestCase):

    """Test case for localizations in Unix module"""

    @staticmethod
    def _get_recognized_paths(vfs):
        """Load localizations.xml and return paths recognized by it using the given VFS."""
        xml_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'cleaners', 'localizations.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_doc = parseString(f.read())

        localizations_node = None
        for child in xml_doc.firstChild.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.nodeName == 'localizations':
                localizations_node = child
                break
        assert localizations_node is not None, 'localizations.xml must contain a <localizations> element'

        locales = Locales(vfs=vfs)
        for child in localizations_node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                locales.add_xml(child)

        recognized = set()
        for (locale, specifier, path) in locales._paths.get_localizations('/'):
            recognized.add(path)
        return recognized

    @staticmethod
    def _path_matches_recognized(test_path, recognized):
        """Return True if test_path is in recognized or is a child/descendant of one."""
        if test_path in recognized:
            return True
        for rec_path in recognized:
            if test_path.startswith(rec_path + '/'):
                return True
        return False

    def test_localization_paths_positive(self):
        """Verify each path in localization_paths_positive.txt is matched by localizations.xml

        Uses a virtual filesystem so the test verifies actual XML rule matching
        without requiring a real /var/lib/flatpak tree.
        """
        data_file = os.path.join(os.path.dirname(
            __file__), 'localization_paths_positive.txt')
        self.assertExists(data_file)

        with open(data_file, 'r', encoding='utf-8') as f:
            test_paths = [line.strip() for line in f if line.strip()
                          and not line.strip().startswith('#')]
        self.assertGreater(len(test_paths), 0,
                           'Test data file should contain at least one path')

        vfs = ListVFS(test_paths)
        recognized = self._get_recognized_paths(vfs)

        for test_path in test_paths:
            self.assertTrue(
                self._path_matches_recognized(test_path, recognized),
                f'Path not matched by localizations.xml: {test_path}'
            )

    def test_localization_paths_negative(self):
        """Verify non-localization paths in flatpak are NOT matched

        Uses a virtual filesystem so the test verifies that paths
        that look similar to localizations are correctly rejected.
        """
        data_file = os.path.join(os.path.dirname(
            __file__), 'localization_paths_negative.txt')
        self.assertExists(data_file)

        with open(data_file, 'r', encoding='utf-8') as f:
            negative_paths = [line.strip() for line in f if line.strip(
            ) and not line.strip().startswith('#')]
        self.assertGreater(len(negative_paths), 0,
                           'Test data file should contain at least one path')

        positive_file = os.path.join(os.path.dirname(
            __file__), 'localization_paths_positive.txt')
        with open(positive_file, 'r', encoding='utf-8') as f:
            positive_paths = [line.strip() for line in f if line.strip(
            ) and not line.strip().startswith('#')]

        vfs = ListVFS(positive_paths + negative_paths)
        recognized = self._get_recognized_paths(vfs)

        for neg_path in negative_paths:
            self.assertFalse(
                self._path_matches_recognized(neg_path, recognized),
                f'Path should NOT be matched by localizations.xml: {neg_path}'
            )
