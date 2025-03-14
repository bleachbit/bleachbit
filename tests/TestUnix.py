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
Test case for module Unix
"""

from unittest import mock
import os
import random
import re
import sys
import tempfile
import unittest
from xml.dom.minidom import parseString

from tests import common
from bleachbit import logger
from bleachbit.General import get_real_username
from bleachbit.FileUtilities import children_in_directory, exe_exists
from bleachbit.Unix import (
    apt_autoclean,
    apt_autoremove,
    find_available_locales,
    get_distribution_name_version,
    get_distribution_name_version_distro,
    get_distribution_name_version_os_release,
    get_distribution_name_version_platform_freedesktop,
    Locales,
    _is_broken_xdg_desktop_application,
    is_broken_xdg_desktop,
    get_purgeable_locales,
    get_apt_size,
    find_best_locale,
    LocaleCleanerPath,
    yum_clean,
    dnf_clean,
    dnf_autoremove,
    wine_to_linux_path,
    root_is_not_allowed_to_X_session,
    rotated_logs,
    run_cleaner_cmd,
    journald_clean,
    is_unix_display_protocol_wayland,
    is_process_running_ps_aux,
    is_process_running,
    JOURNALD_REGEX
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
        super(UnixTestCase, self).setUp()

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
        if sys.version_info >= (3, 10):
            self.assertIsNotNone(ret_platform_freedesktop)

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
    def test_desktop_valid_exe(self):
        """Unit test for .desktop file with valid Unix exe (not env)"""
        fake_config = FakeConfig({"Desktop Entry": {"Exec": "ls"}})
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
        self.assertFalse(result)

    @common.skipIfWindows
    def test_desktop_env_shlex_failure(self):
        """Unit test for .desktop file with shlex exception"""
        fake_config = FakeConfig(
            {"Desktop Entry": {"Exec": "env ENVVAR=bar ls \"notepad.exe"}})
        result = _is_broken_xdg_desktop_application(fake_config, "foo.desktop")
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
                                 "Exec": r"env WINEPREFIX=/some/path wine C:\\Windows\\notepad.exe"}})
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

    @mock.patch('subprocess.check_output')
    @common.skipIfWindows
    def test_is_process_running_ps_aux(self, mock_check_output):
        username = get_real_username()
        ps_out = f"""USER               PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
root               703   0.0  0.0  2471428   2792   ??  Ss   20May16   0:01.30 SubmitDiagInfo
alocaluseraccount   681   0.0  0.0  2471568    856   ??  S    20May16   0:00.81 DiskUnmountWatcher
alocaluseraccount   666   0.0  0.0  2507092   3488   ??  S    20May16   0:17.47 SpotlightNetHelper
root               665   0.0  0.0  2497508    512   ??  Ss   20May16   0:11.30 check_afp
alocaluseraccount   646   0.0  0.1  2502484   5656   ??  S    20May16   0:03.62 DataDetectorsDynamicData
alocaluseraccount   632   0.0  0.0  2471288    320   ??  S    20May16   0:02.79 mdflagwriter
alocaluseraccount   616   0.0  0.0  2497596    520   ??  S    20May16   0:00.41 familycircled
alocaluseraccount   573   0.0  0.0  3602328   2440   ??  S    20May16   0:39.64 storedownloadd
alocaluseraccount   572   0.0  0.0  2531184   3116   ??  S    20May16   0:02.93 LaterAgent
{username}   561   0.0  0.0  2471492    584   ??  S    20May16   0:00.21 USBAgent
alocaluseraccount   535   0.0  0.0  2496656    524   ??  S    20May16   0:00.33 storelegacy
root               531   0.0  0.0  2501712    588   ??  Ss   20May16   0:02.40 suhelperd
"""
        mock_check_output.return_value = ps_out

        tests = [
            (True, 'USBAgent', False),
            (True, 'USBAgent', True),
            (False, 'does-not-exist', False),
            (False, 'does-not-exist', True)
        ]

        for expected, exename, require_same_user in tests:
            with self.subTest(exename=exename, require_same_user=require_same_user):
                result = is_process_running_ps_aux(exename, require_same_user)
                self.assertEqual(
                    expected, result, f'is_process_running_ps_aux(exename={exename}, require_same_user={require_same_user})')

        mock_check_output.return_value = 'invalid-input'
        self.assertRaises(
            RuntimeError, is_process_running_ps_aux, 'foo', False)
        self.assertRaises(RuntimeError, is_process_running_ps_aux, 'foo', True)

    @common.skipIfWindows
    def test_is_process_running(self):
        # Fedora 11 doesn't need realpath but Ubuntu 9.04 uses symlink
        # from /usr/bin/python to python2.6
        exe = os.path.basename(os.path.realpath(sys.executable))
        self.assertTrue(is_process_running(exe, False))
        self.assertTrue(is_process_running(exe, True),
                        f'is_running({exe}, True)')
        non_user_exes = ('polkitd', 'bluetoothd', 'NetworkManager',
                         'gdm3', 'snapd', 'systemd-journald')
        for exe in non_user_exes:
            self.assertFalse(is_process_running(exe, True),
                             f'is_running({exe}, True)')
        self.assertFalse(is_process_running('does-not-exist', True))
        self.assertFalse(is_process_running('does-not-exist', False))

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
            '/var/log/messages-20090118.xz'
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
        from subprocess import CalledProcessError
        self.assertRaises(RuntimeError, run_cleaner_cmd,
                          '/hopethisdoesntexist', [])
        self.assertRaises(CalledProcessError, run_cleaner_cmd,
                          'sh', ['-c', 'echo errormsg; false'])
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
        self.assertEqual(bytes_freed, 299000000)

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
