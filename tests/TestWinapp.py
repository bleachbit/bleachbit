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

sys.path.append('.')
from bleachbit.Winapp import Winapp, section2option

import common

if not 'nt' == os.name:
    def fake_detect_registry_key(f):
        return True
    import bleachbit.Windows
    bleachbit.Windows.detect_registry_key = fake_detect_registry_key




def get_winapp2():
    """Download and cache winapp2.ini.  Return local filename."""
    url = "http://content.thewebatom.net/files/winapp2.ini"
    tmpdir = None
    if 'posix' == os.name:
        tmpdir = '/tmp'
    if 'nt' == os.name:
        tmpdir = os.getenv('TMP')
    fn = os.path.join(tmpdir, 'thewebatom_winapp2.ini')
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
        def ini2cleaner(filekey):
            ini = file(ini_fn, 'w')
            ini.write('[someapp]\n')
            ini.write('LangSecRef=3021\n')
            ini.write(filekey)
            ini.close()
            return Winapp(ini_fn).get_cleaners().next()

        # single file
        import tempfile
        dirname = tempfile.mkdtemp()
        ini_fn = os.path.join(dirname, 'w.ini')
        f1 = os.path.join(dirname, 'deleteme.log')
        file(f1, 'w').write('')
        cleaner = ini2cleaner('FileKey1=%s|deleteme.log\n' % dirname)
        self.assert_(not cleaner.auto_hide())
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(f1))
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(dirname))
        self.assert_(cleaner.auto_hide())

        # *.log
        file(f1, 'w').write('')
        cleaner = ini2cleaner('FileKey1=%s|*.LOG' % dirname)
        self.assert_(not cleaner.auto_hide())
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(f1))
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(dirname))
        self.assert_(cleaner.auto_hide())

        # *.*
        file(f1, 'w').write('')
        cleaner = ini2cleaner('FileKey1=%s|*.*' % dirname)
        self.assert_(not cleaner.auto_hide())
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(f1))
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        self.assert_(not os.path.exists(ini_fn))
        self.assert_(os.path.exists(dirname))
        self.assert_(cleaner.auto_hide())

        # recurse *.*
        dirname2 = os.path.join(dirname, 'sub')
        os.mkdir(dirname2)
        f2 = os.path.join(dirname2, 'deleteme.log')
        file(f2, 'w').write('')
        cleaner = ini2cleaner('FileKey1=%s|*.*|RECURSE' % dirname)
        self.assert_(not cleaner.auto_hide())
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(f2))
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        self.assert_(not os.path.exists(ini_fn))
        self.assert_(os.path.exists(dirname))
        self.assert_(cleaner.auto_hide())

        # remove self *.*
        f2 = os.path.join(dirname2, 'deleteme.log')
        file(f2, 'w').write('')
        cleaner = ini2cleaner('FileKey1=%s|*.*|REMOVESELF' % dirname)
        self.assert_(not cleaner.auto_hide())
        self.assert_(os.path.exists(ini_fn))
        self.assert_(os.path.exists(f2))
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        self.assert_(not os.path.exists(ini_fn))
        self.assert_(not os.path.exists(dirname))
        self.assert_(cleaner.auto_hide())


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

