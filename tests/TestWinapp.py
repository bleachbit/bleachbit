# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Test cases for module Winapp
"""


import os
import shutil
import sys
import tempfile
import unittest

sys.path.append('.')
from bleachbit.Winapp import Winapp, detectos, detect_file, section2option
from bleachbit.Windows import detect_registry_key, parse_windows_build

import common

def CreateSubKey(sub_key):
    import _winreg
    hkey = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, sub_key)
    hkey.Close()


keyfull = 'HKCU\\Software\\BleachBit\\DeleteThisKey'

def get_winapp2():
    """Download and cache winapp2.ini.  Return local filename."""
    url = "https://rawgit.com/bleachbit/winapp2.ini/master/Winapp2-combined.ini"
    tmpdir = None
    if 'posix' == os.name:
        tmpdir = '/tmp'
    if 'nt' == os.name:
        tmpdir = os.getenv('TMP')
    fn = os.path.join(tmpdir, 'bleachbit_test_winapp2.ini')
    if os.path.exists(fn):
        import time
        import stat
        age_seconds = time.time() - os.stat(fn)[stat.ST_MTIME]
        if age_seconds > (24 * 36 * 36):
            print 'note: deleting stale file %s ' % fn
            os.remove(fn)
    if not os.path.exists(fn):
        f = file(fn, 'w')
        import urllib2
        txt = urllib2.urlopen(url).read()
        f.write(txt)
    return fn


class WinappTestCase(unittest.TestCase):

    """Test cases for Winapp"""

    def run_all(self, cleaner, really_delete):
        """Test all the cleaner options"""
        for (option_id, __name) in cleaner.get_options():
            for cmd in cleaner.get_commands(option_id):
                for result in cmd.execute(really_delete):
                    common.validate_result(self, result, really_delete)

    def test_remote(self):
        """Test with downloaded file"""
        winapps = Winapp(get_winapp2())
        for cleaner in winapps.get_cleaners():
            self.run_all(cleaner, False)

    def test_detectos(self):
        """Test detectos function"""
        # Tests are in the format (required_ver, mock, expected_return)
        tests = (('5.1', '5.1', True),
                 ('5.1', '6.0', False),
                 ('6.0', '5.1', False),
                 # 5.1 is the maximum version
                 ('|5.1', '5.1', True),
                 ('|5.1', '6.0', False),
                 ('|5.1', '10.0', False),
                 # 10.0 is the maximum version
                 ('|10.0', '5.1', True),
                 ('|10.0', '10.0', True),
                 ('|10.0', '10.1', False),
                 # 6.1 is the minimum version
                 ('6.1|', '5.1', False),
                 ('6.1|', '6.0', False),
                 ('6.1|', '6.1', True),
                 ('6.1|', '6.2', True),
                 ('6.1|', '10.0', True),
                 ('6.2|', '5.1', False),
                 ('6.2|', '6.0', False),
                 ('6.2|', '6.1', False),
                 ('6.2|', '6.2', True),
                 # 10.0 is the minimum
                 ('10.0|', '5.1', False),
                 ('10.0|', '10.0', True))
        for (s, mock, expected_return) in tests:
            mock = parse_windows_build(mock)
            actual_return = detectos(s, mock)
            self.assertEqual(expected_return, actual_return,
                             'detectos(%s, %s)==%s instead of %s' % (s, mock,
                                                                     actual_return, expected_return))

    def test_detect_file(self):
        """Test detect_file function"""
        tests = [('%windir%\\system32\\kernel32.dll', True),
                 ('%windir%\\system32', True),
                 ('%ProgramFiles%\\Internet Explorer', True),
                 ('%ProgramFiles%\\Internet Explorer\\', True),
                 ('%windir%\\doesnotexist', False),
                 ('%windir%\\system*', True),
                 ('%windir%\\*ystem32', True),
                 ('%windir%\\*ystem3*', True)]
        # On 64-bit Windows, Winapp2.ini expands the %ProgramFiles% environment
        # variable to also %ProgramW6432%, so test unique entries in
        # %ProgramW6432%.
        import struct
        if not 32 == 8 * struct.calcsize('P'):
            raise NotImplementedError('expecting 32-bit Python')
        if os.getenv('ProgramW6432'):
            dir_64 = os.listdir(os.getenv('ProgramFiles'))
            dir_32 = os.listdir(os.getenv('ProgramW6432'))
            dir_32_unique = set(dir_32) - set(dir_64)
            if dir_32 and not dir_32_unique:
                raise RuntimeError(
                    'Test expects objects in %ProgramW6432% not in %ProgramFiles%')
            for pathname in dir_32_unique:
                tests.append(('%%ProgramFiles%%\\%s' % pathname, True))
        else:
            print 'NOTE: skipping %ProgramW6432% tests because WoW64 not detected'
        for (pathname, expected_return) in tests:
            actual_return = detect_file(pathname)
            msg = 'detect_file(%s) returned %s' % (pathname, actual_return)
            self.assertEqual(expected_return, actual_return, msg)

    def setup_fake(self, f1_filename=None):
        """Setup the test environment"""
        subkey = 'Software\\BleachBit\\DeleteThisKey\\AndThisKey'

        dirname = tempfile.mkdtemp(prefix='bleachbit-test-winapp')
        f1 = os.path.join(dirname, f1_filename or 'deleteme.log')
        file(f1, 'w').write('')

        dirname2 = os.path.join(dirname, 'sub')
        os.mkdir(dirname2)
        f2 = os.path.join(dirname2, 'deleteme.log')
        file(f2, 'w').write('')

        fbak = os.path.join(dirname, 'deleteme.bak')
        file(fbak, 'w').write('')

        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertTrue(os.path.exists(fbak))

        CreateSubKey(subkey)

        self.assertTrue(detect_registry_key(keyfull))
        self.assertTrue(detect_registry_key('HKCU\\%s' % subkey))

        return (dirname, f1, f2, fbak)

    def ini2cleaner(self, body, do_next=True):
        """Write a minimal Winapp2.ini"""
        ini = file(self.ini_fn, 'w')
        ini.write('[someapp]\n')
        ini.write('LangSecRef=3021\n')
        ini.write(body)
        ini.write('\n')
        ini.close()
        self.assertTrue(os.path.exists(self.ini_fn))
        if do_next:
            return Winapp(self.ini_fn).get_cleaners().next()
        else:
            return Winapp(self.ini_fn).get_cleaners()

    def test_fake(self):
        """Test with fake file"""

        # reuse this path to store a winapp2.ini file in
        (ini_h, self.ini_fn) = tempfile.mkstemp(
            suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        # a set of tests
        # this map explains what each position in the test tuple means
        # 0=line to write directly to winapp2.ini
        # 1=filename1 to place in fake environment (default=deleteme.log)
        # 2=auto-hide before cleaning
        # 3=dirname exists after cleaning
        # 4=filename1 exists after cleaning
        # 5=filename2 exists after cleaning
        # 6=deleteme.bak exists after cleaning
        # 7=auto-hide after cleaning
        tests = [
            # single file
            ('FileKey1=%s|deleteme.log', None,
                False, True, False, True, True, True),
            # single file, case matching should be insensitive
            ('FileKey1=%s|dEleteme.LOG', None,
                False, True, False, True, True, True),
            # special characters for XML
            ('FileKey1=%s|special_chars_&-\'.txt', 'special_chars_&-\'.txt',
             False, True, False, True, True, True),
            # *.log
            ('FileKey1=%s|*.LOG', None, False, True, False, True, True, True),
            # semicolon separates different file types
            ('FileKey1=%s|*.log;*.bak', None,
             False, True, False, True, False, True),
            # *.*
            ('FileKey1=%s|*.*', None, False, True, False, True, False, True),
            # recurse *.*
            ('FileKey1=%s|*.*|RECURSE', None, False,
             True, False, False, False, True),
            # remove self *.*, this removes the directory
            ('FileKey1=%s|*.*|REMOVESELF', None,
             False, False, False, False, False, True),
        ]

        # Add positive detection, where the detection believes the application is present,
        # to all the tests, which are also positive.
        new_tests = []
        for test in tests:
            for detect in (
                "\nDetectFile=%%APPDATA%%\\Microsoft",
                "\nDetectFile1=%%APPDATA%%\\Microsoft\nDetectFile2=%%APPDATA%%\\does_not_exist",
                "\nDetectFile1=%%APPDATA%%\\does_not_exist\nDetectFile2=%%APPDATA%%\\Microsoft",
                "\nDetect=HKCU\\Software\\Microsoft",
                "\nDetect1=HKCU\\Software\\Microsoft\nDetect2=HKCU\\Software\\does_not_exist",
                    "\nDetect1=HKCU\\Software\\does_not_exist\nDetect2=HKCU\\Software\\Microsoft"):
                new_ini = test[0] + detect
                new_test = [new_ini, ] + [x for x in test[1:]]
                new_tests.append(new_test)
        positive_tests = tests + new_tests

        # execute positive tests
        for test in positive_tests:
            print 'positive test: ', test
            (dirname, f1, f2, fbak) = self.setup_fake(test[1])
            cleaner = self.ini2cleaner(test[0] % dirname)
            self.assertEqual(test[2], cleaner.auto_hide())
            self.run_all(cleaner, False)
            self.run_all(cleaner, True)
            self.assertEqual(test[3], os.path.exists(dirname))
            self.assertEqual(test[4], os.path.exists(f1))
            self.assertEqual(test[5], os.path.exists(f2))
            self.assertEqual(test[6], os.path.exists(fbak))
            self.assertEqual(test[7], cleaner.auto_hide())
            shutil.rmtree(dirname, True)

        # negative tests where the application detect believes the application
        # is absent
        for test in tests:
            for detect in (
                "\nDetectFile=c:\\does_not_exist",
                # special characters for XML
                "\nDetectFile=c:\\does_not_exist_special_chars_&'",
                "\nDetectFile1=c:\\does_not_exist1\nDetectFile2=c:\\does_not_exist2",
                "\nDetect=HKCU\\Software\\does_not_exist",
                "\nDetect=HKCU\\Software\\does_not_exist_&'",
                    "\nDetect1=HKCU\\Software\\does_not_exist1\nDetect2=HKCU\\Software\\does_not_exist1"):
                new_ini = test[0] + detect
                t = [new_ini, ] + [x for x in test[1:]]
                print 'negative test', t
                # execute the test
                (dirname, f1, f2, fbak) = self.setup_fake()
                cleaner = self.ini2cleaner(t[0] % dirname, False)
                self.assertRaises(StopIteration, cleaner.next)

        # registry key, basic
        (dirname, f1, f2, fbak) = self.setup_fake()
        cleaner = self.ini2cleaner('RegKey1=%s' % keyfull)
        self.run_all(cleaner, False)
        self.assertTrue(detect_registry_key(keyfull))
        self.run_all(cleaner, True)
        self.assertFalse(detect_registry_key(keyfull))

        # check for parse error with ampersand
        (dirname, f1, f2, fbak) = self.setup_fake()
        cleaner = self.ini2cleaner(
            'RegKey1=HKCU\\Software\\PeanutButter&Jelly')
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)

    def test_excludekey(self):
        """Test for ExcludeKey"""

        # reuse this path to store a winapp2.ini file in
        (ini_h, self.ini_fn) = tempfile.mkstemp(suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        # setup the environment

        # tests
        # each tuple
        # 0 = body of winapp2.ini
        # 1 = deleteme.log should exist
        # 2 = deleteme.bak should exist

        # FIXME
        # multiple types of files
        # environment variable in path
        # glob in path
        tests = (
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=FILE|%(d)s|deleteme.log', True, False),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=FILE|%(d)s\deleteme.log', True, False),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s|*.*', True, True),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s', True, True),
            )

        for test in tests:
            (dirname, f1, f2, fbak) = self.setup_fake()
            cleaner = self.ini2cleaner(test[0] % { 'd': dirname })
            self.run_all(cleaner, True)
            self.assertEqual(test[1], os.path.exists(r'%s\deleteme.log' % dirname))
            self.assertEqual(test[2], os.path.exists(r'%s\deleteme.bak' % dirname))
            shutil.rmtree(dirname)


    def test_section2option(self):
        """Test for section2option()"""
        tests = (('  FOO2  ', 'foo2'),
                 ('A - B (C)', 'a_b_c'))
        for test in tests:
            self.assertEqual(section2option(test[0]), test[1])


def suite():
    return unittest.makeSuite(WinappTestCase)


if __name__ == '__main__':
    unittest.main()
