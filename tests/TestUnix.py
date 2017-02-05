# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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

from __future__ import absolute_import, print_function

from tests import common
import bleachbit
from bleachbit.Unix import *

import sys
import tempfile
import unittest


@unittest.skipIf('win32' == sys.platform, 'skipping unix tests on windows')
class UnixTestCase(common.BleachbitTestCase):

    """Test case for module Unix"""

    def setUp(self):
        """Initialize unit tests"""
        self.locales = Locales()

    def test_apt(self):
        """Unit test for method apt_autoclean() and apt_autoremove()"""
        if 0 != os.geteuid() or not FileUtilities.exe_exists('apt-get'):
            self.assertRaises(RuntimeError, apt_autoclean)
            self.assertRaises(RuntimeError, apt_autoremove)
        else:
            bytes_freed = apt_autoclean()
            self.assert_(isinstance(bytes_freed, (int, long)))
            bytes_freed = apt_autoremove()
            self.assert_(isinstance(bytes_freed, (int, long)))

    def test_is_broken_xdg_desktop(self):
        """Unit test for is_broken_xdg_desktop()"""
        menu_dirs = ['/usr/share/applications',
                     '/usr/share/autostart',
                     '/usr/share/gnome/autostart',
                     '/usr/share/gnome/apps',
                     '/usr/share/mimelnk',
                     '/usr/share/applnk-redhat/',
                     '/usr/local/share/applications/']
        for dirname in menu_dirs:
            for filename in [fn for fn in FileUtilities.children_in_directory(dirname, False)
                             if fn.endswith('.desktop')]:
                self.assert_(type(is_broken_xdg_desktop(filename) is bool))

    def test_is_running_darwin(self):
        def run_ps():
            return """USER               PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
root               703   0.0  0.0  2471428   2792   ??  Ss   20May16   0:01.30 SubmitDiagInfo
alocaluseraccount   681   0.0  0.0  2471568    856   ??  S    20May16   0:00.81 DiskUnmountWatcher
alocaluseraccount   666   0.0  0.0  2507092   3488   ??  S    20May16   0:17.47 SpotlightNetHelper
root               665   0.0  0.0  2497508    512   ??  Ss   20May16   0:11.30 check_afp
alocaluseraccount   646   0.0  0.1  2502484   5656   ??  S    20May16   0:03.62 DataDetectorsDynamicData
alocaluseraccount   632   0.0  0.0  2471288    320   ??  S    20May16   0:02.79 mdflagwriter
alocaluseraccount   616   0.0  0.0  2497596    520   ??  S    20May16   0:00.41 familycircled
alocaluseraccount   573   0.0  0.0  3602328   2440   ??  S    20May16   0:39.64 storedownloadd
alocaluseraccount   572   0.0  0.0  2531184   3116   ??  S    20May16   0:02.93 LaterAgent
alocaluseraccount   561   0.0  0.0  2471492    584   ??  S    20May16   0:00.21 USBAgent
alocaluseraccount   535   0.0  0.0  2496656    524   ??  S    20May16   0:00.33 storelegacy
root               531   0.0  0.0  2501712    588   ??  Ss   20May16   0:02.40 suhelperd
"""
        self.assertTrue(is_running_darwin('USBAgent', run_ps))
        self.assertFalse(is_running_darwin('does-not-exist', run_ps))
        self.assertRaises(RuntimeError, is_running_darwin, 'foo', lambda: 'invalid-input')

    def test_is_running(self):
        # Fedora 11 doesn't need realpath but Ubuntu 9.04 uses symlink
        # from /usr/bin/python to python2.6
        exe = os.path.basename(os.path.realpath(sys.executable))
        self.assertTrue(is_running(exe))
        self.assertFalse(is_running('does-not-exist'))

    def test_journald_clean(self):
        if not FileUtilities.exe_exists('journalctl'):
            self.assertRaises(RuntimeError, journald_clean)
        else:
            journald_clean()

    def test_locale_regex(self):
        """Unit test for locale_to_language()"""
        tests = [('en', 'en'),
                 ('en_US', 'en'),
                 ('en_US@piglatin', 'en'),
                 ('en_US.utf8', 'en'),
                 ('ko_KR.eucKR', 'ko'),
                 ('pl.ISO8859-2', 'pl'),
                 ('zh_TW.Big5', 'zh')]
        import re
        regex = re.compile('^' + Locales.localepattern + '$')
        for test in tests:
            m = regex.match(test[0])
            self.assert_(m is not None, 'expected positive match for ' + test[0])
            self.assertEqual(m.group("locale"), test[1])
        for test in ['default', 'C', 'English', 'ru_RU.txt', 'ru.txt']:
            self.assert_(regex.match(test) is None, 'expected negative match for '+test)

    def test_localization_paths(self):
        """Unit test for localization_paths()"""
        from xml.dom.minidom import parseString
        configpath = parseString(
            '<path location="/usr/share/locale/" />').firstChild
        locales.add_xml(configpath)
        counter = 0
        for path in locales.localization_paths(['en']):
            self.assert_(os.path.lexists(path))
            # self.assert_(path.startswith('/usr/share/locale'))
            # /usr/share/locale/en_* should be ignored
            self.assert_(path.find('/en_') == -1)
            counter += 1
        self.assert_(
            counter > 0, 'Zero files deleted by localization cleaner.'
                         'This may be an error unless you really deleted all the files.')

    def test_fakelocalizationdirs(self):
        """Create a faked localization hierarchy and clean it afterwards"""
        dirname = tempfile.mkdtemp(prefix='bleachbit-test-localizations')

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
            os.mkdir(os.path.join(dirname, path))
        for path in keepfiles + nukefiles:
            open(os.path.join(dirname, path), 'w').close()

        configxml = '<path directoryregex="^.*$">' \
                    '  <path directoryregex="^(locale|dummyfiles)$">' \
                    '    <path location="." filter="*" />' \
                    '    <regexfilter postfix="\.txt" />' \
                    '  </path>' \
                    '</path>'
        from xml.dom.minidom import parseString
        config = parseString(configxml)
        locales = Locales()
        locales._paths = LocaleCleanerPath(dirname)
        locales.add_xml(config.firstChild, None)
        # normpath because paths may contain ./
        deletelist = [os.path.normpath(path) for path in locales.localization_paths(['en', 'de'])]
        for path in keepdirs + keepfiles:
            self.assert_(os.path.join(dirname, path) not in deletelist)
        for path in nukedirs + nukefiles:
            self.assert_(os.path.join(dirname, path) in deletelist)

    def test_rotated_logs(self):
        """Unit test for rotated_logs()"""
        for path in rotated_logs():
            self.assert_(os.path.exists(path),
                         "Rotated log path '%s' does not exist" % path)

    def test_run_cleaner_cmd(self):
        from subprocess import CalledProcessError
        self.assertRaises(RuntimeError, run_cleaner_cmd, '/hopethisdoesntexist', [])
        self.assertRaises(CalledProcessError, run_cleaner_cmd, 'sh', ['-c', 'echo errormsg; false'])
        # test if regexes for invalid lines work
        self.assertRaises(RuntimeError, run_cleaner_cmd, 'echo', ['This is an invalid line'],
                          error_line_regexes=['invalid'])

        freed_space_regex = r'^Freed ([\d.]+[kMT]?B)'
        lines = ['Test line',
                 'Freed 100B on your hard drive',
                 'Freed 1.9kB, hooray!',
                 'Fred 12MB']
        freed_space = run_cleaner_cmd('echo', ['\n'.join(lines)], freed_space_regex)
        self.assertEqual(freed_space, 2000)

    def test_start_with_computer(self):
        """Unit test for start_with_computer*"""
        b = start_with_computer_check()
        self.assert_(isinstance(b, bool))

        if not os.path.exists(bleachbit.launcher_path) and \
                os.path.exists('bleachbit.desktop'):
            # this happens when BleachBit is not installed
            bleachbit.launcher_path = 'bleachbit.desktop'

        # opposite setting
        start_with_computer(not b)
        two_b = start_with_computer_check()
        self.assert_(isinstance(two_b, bool))
        self.assertEqual(b, not two_b)
        # original setting
        start_with_computer(b)
        three_b = start_with_computer_check()
        self.assert_(isinstance(b, bool))
        self.assertEqual(b, three_b)

    def test_wine_to_linux_path(self):
        """Unit test for wine_to_linux_path()"""
        tests = [("/home/foo/.wine",
                  "C:\\Program Files\\NSIS\\NSIS.exe",
                  "/home/foo/.wine/drive_c/Program Files/NSIS/NSIS.exe")]
        for test in tests:
            self.assertEqual(wine_to_linux_path(test[0], test[1]), test[2])

    def test_yum_clean(self):
        """Unit test for yum_clean()"""
        if 0 != os.geteuid() or os.path.exists('/var/run/yum.pid') \
                or not FileUtilities.exe_exists('yum'):
            self.assertRaises(RuntimeError, yum_clean)
        else:
            bytes_freed = yum_clean()
            self.assert_(isinstance(bytes_freed, (int, long)))
            bleachbit.logger.debug('yum bytes cleaned %d', bytes_freed)
