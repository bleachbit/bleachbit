# vim: ts=4:sw=4:expandtab

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
Test cases for module Winapp
"""



import os
import sys
import unittest

import TestWindows

sys.path.append('.')
from bleachbit.Winapp import Winapp, section2option

import common

if 'nt' == os.name:
    import _winreg
else:
    def fake_detect_registry_key(f):
        return True
    import bleachbit.Windows
    bleachbit.Windows.detect_registry_key = fake_detect_registry_key




def get_winapp2():
    """Download and cache winapp2.ini.  Return local filename."""
    url = "http://www.winapp2.com/Winapp2.ini"
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


    def test_fake(self):
        """Test with fake file"""

        ini_fn = None
        keyfull = 'HKCU\\Software\\BleachBit\\DeleteThisKey'
        subkey = 'Software\\BleachBit\\DeleteThisKey\\AndThisKey'

        def setup_fake():
            """Setup the test environment"""
            dirname = tempfile.mkdtemp(suffix='bleachbit_test_winapp')
            f1 = os.path.join(dirname, 'deleteme.log')
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

            hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, subkey )
            hkey.Close()

            self.assertTrue(TestWindows.registry_key_exists(keyfull))
            self.assertTrue(TestWindows.registry_key_exists('HKCU\\%s' % subkey))

            return (dirname, f1, f2, fbak)


        def ini2cleaner(filekey, do_next = True):
            ini = file(ini_fn, 'w')
            ini.write('[someapp]\n')
            ini.write('LangSecRef=3021\n')
            ini.write(filekey)
            ini.write('\n')
            ini.close()
            self.assertTrue(os.path.exists(ini_fn))
            if do_next:
                return Winapp(ini_fn).get_cleaners().next()
            else:
                return Winapp(ini_fn).get_cleaners()

        # reuse this path to store a winapp2.ini file in
        import tempfile
        (ini_h, ini_fn) = tempfile.mkstemp(suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        # a set of tests
        tests = [
            # single file    
            ( 'FileKey1=%s|deleteme.log', False, True, False, True, True, True ),
            # *.log
            ( 'FileKey1=%s|*.LOG', False, True, False, True, True, True ),
            # semicolon separates different file types
            ( 'FileKey1=%s|*.log;*.bak', False, True, False, True, False, True ),
            # *.*
            ( 'FileKey1=%s|*.*', False, True, False, True, False, True ),
            # recurse *.*
            ( 'FileKey1=%s|*.*|RECURSE', False, True, False, False, False, True ),
            # remove self *.*, this removes the directory
            ( 'FileKey1=%s|*.*|REMOVESELF', False, False, False, False, False, True ),
            ]

        # Add positive detection, where the detection believes the application is present,
        # to all the tests, which are also positive.
        new_tests = []
        for test in tests:
            for detect in ( \
                "\nDetectFile=%%APPDATA%%\\Microsoft", \
                "\nDetectFile1=%%APPDATA%%\\Microsoft\nDetectFile2=%%APPDATA%%\\does_not_exist", \
                "\nDetectFile1=%%APPDATA%%\\does_not_exist\nDetectFile2=%%APPDATA%%\\Microsoft", \
                "\nDetect=HKCU\\Software\\Microsoft", \
                "\nDetect1=HKCU\\Software\\Microsoft\nDetect2=HKCU\\Software\\does_not_exist", \
                "\nDetect1=HKCU\\Software\\does_not_exist\nDetect2=HKCU\\Software\\Microsoft"):
                new_ini = test[0] + detect
                new_test = [new_ini, ] + [x for x in test[1:]]
                new_tests.append(new_test)
        positive_tests = tests + new_tests    

        # execute positive tests
        for test in positive_tests:
            print 'positive test: ', test
            (dirname, f1, f2, fbak) = setup_fake()
            cleaner = ini2cleaner(test[0] % dirname)
            self.assertEqual(test[1], cleaner.auto_hide())
            self.run_all(cleaner, False)
            self.run_all(cleaner, True)
            self.assertEqual(test[2], os.path.exists(dirname))
            self.assertEqual(test[3], os.path.exists(f1))
            self.assertEqual(test[4], os.path.exists(f2))
            self.assertEqual(test[5], os.path.exists(fbak))
            self.assertEqual(test[6], cleaner.auto_hide())

        # negative tests where the application detect believes the application is absent
        for test in tests:
            for detect in ( \
                "\nDetectFile=c:\\does_not_exist", \
                "\nDetectFile1=c:\\does_not_exist1\nDetectFile2=c:\\does_not_exist2", \
                "\nDetect=HKCU\\Software\\does_not_exist", \
                "\nDetect1=HKCU\\Software\\does_not_exist1\nDetect2=HKCU\\Software\\does_not_exist1"):
                new_ini = test[0] + detect
                t = [new_ini, ] + [x for x in test[1:]]
                print 'negative test', t
                # execute the test
                (dirname, f1, f2, fbak) = setup_fake()
                cleaner = ini2cleaner(t[0] % dirname, False)
                self.assertRaises(StopIteration, cleaner.next)

        # registry key, basic
        (dirname, f1, f2, fbak) = setup_fake()
        cleaner = ini2cleaner('RegKey1=%s' % keyfull)
        self.run_all(cleaner, False)
        self.assertTrue(TestWindows.registry_key_exists(keyfull))
        self.run_all(cleaner, True)
        self.assertFalse(TestWindows.registry_key_exists(keyfull))

        # check for parse error with ampersand
        (dirname, f1, f2, fbak) = setup_fake()
        cleaner = ini2cleaner('RegKey1=HKCU\\Software\\PeanutButter&Jelly')
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)


    def test_section2option(self):
        """Test for section2option()"""
        tests = ( ('  FOO2  ', 'foo2'), \
            ('A - B (C)', 'a_b_c') )
        for test in tests:
            self.assertEqual(section2option(test[0]), test[1])


def suite():
    return unittest.makeSuite(WinappTestCase)


if __name__ == '__main__':
    unittest.main()

