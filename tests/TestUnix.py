# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2012 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Test case for module Unix
"""


import os
import sys
import unittest

sys.path.append('.')
from bleachbit.Unix import *




class UnixTestCase(unittest.TestCase):
    """Test case for module Unix"""


    def setUp(self):
        """Initialize unit tests"""
        self.locales = Locales()


    def test_apt_autoclean(self):
        """Unit test for method apt_autoclean()"""
        if 0 != os.geteuid() or not FileUtilities.exe_exists('apt-get'):
            self.assertRaises(RuntimeError, apt_autoclean)
        else:
            bytes_freed = apt_autoclean()
            self.assert_(isinstance(bytes_freed, (int, long)))


    def test_guess_overwrite_paths(self):
        """Unit test for guess_overwrite_paths()"""
        for path in guess_overwrite_paths():
            self.assert_(os.path.isdir(path))


    def test_is_broken_xdg_desktop(self):
        """Unit test for is_broken_xdg_desktop()"""
        menu_dirs = [ '/usr/share/applications', \
            '/usr/share/autostart', \
            '/usr/share/gnome/autostart', \
            '/usr/share/gnome/apps', \
            '/usr/share/mimelnk', \
            '/usr/share/applnk-redhat/', \
            '/usr/local/share/applications/' ]
        for dirname in menu_dirs:
            for filename in [fn for fn in FileUtilities.children_in_directory(dirname, False) \
                if fn.endswith('.desktop')]:
                self.assert_(type(is_broken_xdg_desktop(filename) is bool))


    def test_is_running(self):
        # Fedora 11 doesn't need realpath but Ubuntu 9.04 uses symlink
        # from /usr/bin/python to python2.6
        exe = os.path.basename(os.path.realpath(sys.executable))
        self.assertEqual(True, is_running(exe))


    def test_iterate_languages(self):
        """Unit test for the method iterate_languages()"""
        for language in self.locales.iterate_languages():
            self.assert_(type(language) is str)
            self.assert_(len(language) > 0)
            self.assert_(len(language) < 9)


    def test_locale_to_language(self):
        """Unit test for locale_to_language()"""
        tests = [ ('en', 'en'),
            ('en_US', 'en'),
            ('en_US@piglatin', 'en'),
            ('en_US.utf8', 'en'),
            ('klingon', 'klingon'),
            ('pl.ISO8859-2', 'pl'),
            ('sr_Latn', 'sr'),
            ('zh_TW.Big5', 'zh') ]
        for test in tests:
            self.assertEqual(locale_to_language(test[0]), test[1])

        self.assertRaises(ValueError, locale_to_language, 'default')
        self.assertRaises(ValueError, locale_to_language, 'C')
        self.assertRaises(ValueError, locale_to_language, 'English')


    def test_locale_globex(self):
        """Unit test for locale_globex"""

        locale = locale_globex('/bin/ls', '(ls)$').next()
        self.assertEqual(locale, ('ls', '/bin/ls'))

        fakepath = '/usr/share/omf/gedit/gedit-es.omf'

        def test_yield(pathname, regex):
            """Replacement for globex()"""
            yield fakepath

        old_globex = FileUtilities.globex
        FileUtilities.globex = test_yield

        func = locale_globex('/usr/share/omf/*/*-*.omf', '-([a-z]{2}).omf$')
        actual = func.next()
        expect = ('es', fakepath)
        self.assertEqual(actual, expect, "Expected '%s' but got '%s'" % (expect, actual))
        FileUtilities.globex = old_globex


    def test_localization_paths(self):
        """Unit test for localization_paths()"""
        for path in locales.localization_paths(lambda x, y: False):
            self.assert_(os.path.lexists(path))


    def test_native_name(self):
        """Unit test for native_name()"""
        tests = [ ('en', 'English'),
            ('es', 'Español') ]
        for test in tests:
            self.assertEqual(self.locales.native_name(test[0]), test[1])


    def test_rotated_logs(self):
        """Unit test for rotated_logs()"""
        for path in rotated_logs():
            self.assert_(os.path.exists(path), \
                "Rotated log path '%s' does not exist" % path)


    def test_start_with_computer(self):
        """Unit test for start_with_computer*"""
        b = start_with_computer_check()
        self.assert_(isinstance(b, bool))
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
        tests = [ ("/home/foo/.wine", \
            "C:\\Program Files\\NSIS\\NSIS.exe", \
            "/home/foo/.wine/drive_c/Program Files/NSIS/NSIS.exe") ]
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
            print 'debug: yum bytes cleaned %d', bytes_freed



def suite():
    return unittest.makeSuite(UnixTestCase)


if __name__ == '__main__' and 'posix' == os.name:
    unittest.main()

