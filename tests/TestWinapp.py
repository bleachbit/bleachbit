# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Test cases for module Winapp
"""

import os
import shutil
import tempfile
from unittest import mock

from tests import common
from bleachbit.Winapp import Winapp, detectos, detect_file, section2option
from bleachbit.Windows import detect_registry_key, parse_windows_build
from bleachbit import logger


def create_sub_key(sub_key):
    """Create a registry key"""
    import winreg
    hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key)
    hkey.Close()


KEYFULL = 'HKCU\\Software\\BleachBit\\DeleteThisKey'


def get_winapp2():
    """Download and cache winapp2.ini.  Return local filename."""
    url = "https://rawgit.com/bleachbit/winapp2.ini/master/Winapp2-BleachBit.ini"
    tmpdir = None
    if os.name == 'posix':
        tmpdir = '/tmp'
    if os.name == 'nt':
        tmpdir = os.getenv('TMP')
    fname = os.path.join(tmpdir, 'bleachbit_test_winapp2.ini')
    if os.path.exists(fname):
        import time
        import stat
        age_seconds = time.time() - os.stat(fname)[stat.ST_MTIME]
        if age_seconds > (24 * 36 * 36):
            logger.info('deleting stale file %s ', fname)
            os.remove(fname)
    if not os.path.exists(fname):
        with open(fname, 'w', encoding='utf-8') as fobj:
            import urllib.request
            txt = urllib.request.urlopen(url).read()
            fobj.write(txt.decode('utf-8'))
    return fname


class WinappTestCase(common.BleachbitTestCase):
    """Test cases for Winapp"""

    def run_all(self, cleaner, really_delete):
        """Test all the cleaner options"""
        for (option_id, __name) in cleaner.get_options():
            for cmd in cleaner.get_commands(option_id):
                for result in cmd.execute(really_delete):
                    common.validate_result(self, result, really_delete)

    @common.skipUnlessWindows
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
                 # must be 6.2 or 6.3
                 ('6.2|6.3', '6.0', False),
                 ('6.2|6.3', '6.1', False),
                 ('6.2|6.3', '6.2', True),
                 ('6.2|6.3', '6.3', True),
                 ('6.2|6.3', '10.0', False),
                 # 10.0 is the minimum
                 ('10.0|', '5.1', False),
                 ('10.0|', '10.0', True))
        for (req, mock, expected_return) in tests:
            mock = parse_windows_build(mock)
            actual_return = detectos(req, mock)
            self.assertEqual(expected_return, actual_return,
                             'detectos(%s, %s)==%s instead of %s' % (req, mock,
                                                                     actual_return, expected_return))

    @common.skipUnlessWindows
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
        if os.getenv('ProgramW6432'):
            dir_64 = os.listdir(os.getenv('ProgramFiles'))
            dir_32 = os.listdir(os.getenv('ProgramW6432'))
            dir_32_unique = set(dir_32) - set(dir_64)
            if dir_32 and not dir_32_unique and 8 * struct.calcsize('P') == 32:
                raise RuntimeError(
                    'Test expects objects in %ProgramW6432% not in %ProgramFiles%')
            for pathname in dir_32_unique:
                tests.append(('%%ProgramFiles%%\\%s' % pathname, True))
        else:
            logger.info(
                'skipping %ProgramW6432% tests because WoW64 not detected')
        for (pathname, expected_return) in tests:
            actual_return = detect_file(pathname)
            msg = 'detect_file(%s) returned %s' % (pathname, actual_return)
            self.assertEqual(expected_return, actual_return, msg)

    def setup_fake(self, f1_filename=None):
        """Setup the test environment"""
        subkey = 'Software\\BleachBit\\DeleteThisKey\\AndThisKey'

        # put ampersand in directory name to test
        # https://github.com/bleachbit/bleachbit/issues/308
        dirname = tempfile.mkdtemp(prefix='bleachbit-test-winapp&')
        fname1 = os.path.join(dirname, f1_filename or 'deleteme.log')
        open(fname1, 'w').close()

        dirname2 = os.path.join(dirname, 'sub')
        os.mkdir(dirname2)
        fname2 = os.path.join(dirname2, 'deleteme.log')
        open(fname2, 'w').close()

        fbak = os.path.join(dirname, 'deleteme.bak')
        open(fbak, 'w').close()

        self.assertExists(fname1)
        self.assertExists(fname2)
        self.assertExists(fbak)

        create_sub_key(subkey)

        self.assertTrue(detect_registry_key(KEYFULL))
        self.assertTrue(detect_registry_key('HKCU\\%s' % subkey))

        return dirname, fname1, fname2, fbak

    def ini2cleaner(self, body, do_next=True):
        """Write a minimal Winapp2.ini"""
        ini = open(self.ini_fn, 'w')
        ini.write('[someapp]\n')
        ini.write('LangSecRef=3021\n')
        ini.write(body)
        ini.write('\n')
        ini.close()
        self.assertExists(self.ini_fn)
        if do_next:
            return next(Winapp(self.ini_fn).get_cleaners())
        else:
            return Winapp(self.ini_fn).get_cleaners()

    @common.skipUnlessWindows
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
        # 4=filename1 (.\deleteme.log) exists after cleaning
        # 5=sub\deleteme.log exists after cleaning
        # 6=.\deleteme.bak exists after cleaning
        tests = [
            # single file
            ('FileKey1=%s|deleteme.log', None,
                False, True, False, True, True),
            # single file, case matching should be insensitive
            ('FileKey1=%s|dEleteme.LOG', None,
                False, True, False, True, True),
            # special characters for XML
            ('FileKey1=%s|special_chars_&-\'.txt', 'special_chars_&-\'.txt',
             False, True, False, True, True),
            # *.log
            ('FileKey1=%s|*.LOG', None, False, True, False, True, True),
            # semicolon separates different file types
            ('FileKey1=%s|*.log;*.bak', None,
             False, True, False, True, False),
            # *.*
            ('FileKey1=%s|*.*', None, False, True, False, True, False),
            # recurse *.*
            ('FileKey1=%s|*.*|RECURSE', None, False,
             True, False, False, False),
            # recurse *.log
            ('FileKey1=%s|*.log|RECURSE', None, False,
             True, False, False, True),
            # remove self *.*, this removes the directory
            ('FileKey1=%s|*.*|REMOVESELF', None,
             False, False, False, False, False),
        ]

        # Add positive detection, where the detection believes the application is present,
        # to all the tests, which are also positive.
        new_tests = []
        for test in tests:
            for detect in (
                "\nDetectFile=%%APPDATA%%\\Microsoft",
                "\nSpecialDetect=DET_WINDOWS",
                "\nDetectFile1=%%APPDATA%%\\Microsoft\nDetectFile2=%%APPDATA%%\\does_not_exist",
                "\nDetectFile1=%%APPDATA%%\\does_not_exist\nDetectFile2=%%APPDATA%%\\Microsoft",
                "\nDetect=HKCU\\Software\\Microsoft",
                # Below checks that a space is OK in the registry key
                "\nDetect=HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
                # Below checks Detect# where one of two keys exist.
                "\nDetect1=HKCU\\Software\\Microsoft\nDetect2=HKCU\\Software\\does_not_exist",
                "\nDetect1=HKCU\\Software\\does_not_exist\nDetect2=HKCU\\Software\\Microsoft",
                # Below checks Detect with DetectFile where one exists
                "\nDetect=HKCU\\Software\\Microsoft\nDetectFile=%%APPDATA%%\\does_not_exist",
                    "\nDetect=HKCU\\Software\\does_not_exist\nDetectFile=%%APPDATA%%\\Microsoft"):
                new_ini = test[0] + detect
                new_test = [new_ini, ] + [x for x in test[1:]]
                new_tests.append(new_test)
        positive_tests = tests + new_tests

        # execute positive tests
        for test in positive_tests:
            print('positive test: ', test)
            self.assertEqual(len(test), 7)
            (dirname, fname1, fname2, fbak) = self.setup_fake(test[1])
            cleaner = self.ini2cleaner(test[0] % dirname)
            self.assertEqual(test[2], cleaner.auto_hide())
            self.run_all(cleaner, False)
            self.run_all(cleaner, True)
            self.assertCondExists(test[3], dirname)
            self.assertCondExists(test[4], fname1)
            self.assertCondExists(test[5], fname2)
            self.assertCondExists(test[6], fbak)
            shutil.rmtree(dirname, True)

        # negative tests where the application detect believes the application
        # is absent
        for test in tests:
            for detect in (
                "\nDetectFile=c:\\does_not_exist",
                "\nSpecialDetect=DET_SPACE_QUEST",
                # special characters for XML
                "\nDetectFile=c:\\does_not_exist_special_chars_&'",
                "\nDetectFile1=c:\\does_not_exist1\nDetectFile2=c:\\does_not_exist2",
                "\nDetect=HKCU\\Software\\does_not_exist",
                "\nDetect=HKCU\\Software\\does_not_exist_&'",
                    "\nDetect1=HKCU\\Software\\does_not_exist1\nDetect2=HKCU\\Software\\does_not_exist1"):
                new_ini = test[0] + detect
                test_full = [new_ini, ] + [x for x in test[1:]]
                print('negative test', test_full)
                # execute the test
                (dirname, fname1, fname2, fbak) = self.setup_fake()
                cleaner = self.ini2cleaner(test_full[0] % dirname, False)
                self.assertRaises(StopIteration, cleaner.__next__)
                shutil.rmtree(dirname, True)

        # registry key, basic
        (dirname, fname1, fname2, fbak) = self.setup_fake()
        cleaner = self.ini2cleaner('RegKey1=%s' % KEYFULL)
        self.run_all(cleaner, False)
        self.assertTrue(detect_registry_key(KEYFULL))
        self.run_all(cleaner, True)
        self.assertFalse(detect_registry_key(KEYFULL))
        shutil.rmtree(dirname, True)

        # check for parse error with ampersand
        (dirname, fname1, fname2, fbak) = self.setup_fake()
        cleaner = self.ini2cleaner(
            'RegKey1=HKCU\\Software\\PeanutButter&Jelly')
        self.run_all(cleaner, False)
        self.run_all(cleaner, True)
        shutil.rmtree(dirname, True)

    @common.skipUnlessWindows
    def test_excludekey(self):
        """Test for ExcludeKey"""

        # reuse this path to store a winapp2.ini file in
        (ini_h, self.ini_fn) = tempfile.mkstemp(
            suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        # tests
        # each tuple
        # 0 = body of winapp2.ini
        # 1 = .\deleteme.log should exist
        # 2 = .\deleteme.bak should exist
        # 3 = sub\deleteme.log should exist

        tests = (
            # delete everything in single directory (no children) without
            # exclusions
            ('FileKey1=%(d)s|deleteme.*', False, False, True),
            # delete everything in single directory using environment variable
            ('FileKey1=%%bbtestdir%%|deleteme.*', False, False, True),
            # delete everything in parent and child directories without
            # exclusions
            ('FileKey1=%(d)s|deleteme.*|RECURSE', False, False, False),
            # don't delete files containing the described file name
            ('FileKey1=%(d)s|eteme.*|RECURSE', True, True, True),
            # delete a pattern sub folder included
            ('FileKey1=%(d)s|*eteme.*|RECURSE', False, False, False),
            # delete a pattern sub folder not included
            ('FileKey1=%(d)s|*eteme.*', False, False, True),
            # exclude log delimited by pipe
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=FILE|%(d)s|deleteme.log',
             True, False, True),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=FILE|%(d)s\|deleteme.log',
             True, False, True),
            # delete / exclude patterns with different complexity
            ('FileKey1=%(d)s|*eteme.*\nExcludeKey1=FILE|%(d)s|deleteme.log',
             True, False, True),
            ('FileKey1=%(d)s|*eteme.*\nExcludeKey1=FILE|%(d)s\|deleteme.log',
             True, False, True),
            ('FileKey1=%(d)s|*ete*.*\nExcludeKey1=PATH|%(d)s|*ete*.lo?',
             True, False, True),
            ('FileKey1=%(d)s|*eteme*\nExcludeKey1=PATH|%(d)s|*notexist.*',
             False, False, True),
            ('FileKey1=%(d)s|*eteme.log\nExcludeKey1=PATH|%(d)s|do*.log',
             False, True, True),
            # semicolon separates different file types
            ('FileKey1=%(d)s|*.log;*.bak|RECURSE\nExcludeKey1=PATH|%(d)s|*.log',
             True, False, True),
            # exclude log without pipe delimiter
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=FILE|%(d)s\deleteme.log',
             True, False, True),
            # exclude everything in folder
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s|*.*',
             True, True, True),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s\|*.*',
             True, True, True),
            ('FileKey1=%(d)s|deleteme.*|RECURSE\nExcludeKey1=PATH|%(d)s|*.*',
             True, True, True),
            ('FileKey1=%(d)s|*.*|RECURSE\nExcludeKey1=PATH|%(d)s|*.*',
             True, True, True),
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s',
             True, True, True),
            # exclude everything in folder using environment variable
            # use double %% to escape
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%%bbtestdir%%|*.*',
             True, True, True),
            # exclude sub-folder
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s\sub',
             False, False, True),
            # exclude multiple file types that do not exist
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s|*.exe;*.dll',
             False, False, True),
            # exclude multiple file types that do exist, so dlete nothing
            ('FileKey1=%(d)s|deleteme.*\nExcludeKey1=PATH|%(d)s|*.bak;*.log',
             True, True, True),
            ('FileKey1=%(d)s|deleteme.*|RECURSE\nExcludeKey1=PATH|%(d)s|*.bak;*.log',
             True, True, True),
            # multiple ExcludeKey, neither of which should do anything
            ('FileKey1=%(d)s|deleteme.*|RECURSE\nExcludeKey1=PATH|c:\\doesnotexist|*.*\nExcludeKey2=PATH|c:\\alsodoesnotexist|*.*',
             False, False, False),
            # multiple ExcludeKey, the first should work
            ('FileKey1=%(d)s|deleteme.*|RECURSE\nExcludeKey1=PATH|%(d)s|*.log\nExcludeKey2=PATH|c:\\alsodoesnotexist\|*.*',
             True, False, True),
            # multiple ExcludeKey, both should work
            ('FileKey1=%(d)s|deleteme.*|RECURSE\nExcludeKey1=PATH|%(d)s|*.log\nExcludeKey2=PATH|%(d)s|*.bak',
             True, True, True),
            # glob should exclude the directory called 'sub'
            ('FileKey1=%(d)s|*.*\nExcludeKey1=PATH|%(d)s\s*',
             False, False, True),
        )

        for test in tests:
            msg = '\nTest:\n%s' % test[0]
            # setup
            (dirname, _fname1, _fname2, _fbak) = self.setup_fake()
            self.assertExists(r'%s\deleteme.log' % dirname, msg)
            self.assertExists(r'%s\deleteme.bak' % dirname, msg)
            self.assertExists(r'%s\sub\deleteme.log' % dirname, msg)
            # set environment variable for testing
            os.environ['bbtestdir'] = dirname
            self.assertExists(r'$bbtestdir\deleteme.log', msg)
            # delete files
            cleaner = self.ini2cleaner(test[0] % {'d': dirname})
            self.run_all(cleaner, True)
            # test
            self.assertCondExists(test[1], r'%s\deleteme.log' % dirname, msg)
            self.assertCondExists(test[2], r'%s\deleteme.bak' % dirname, msg)
            self.assertCondExists(
                test[3], r'%s\sub\deleteme.log' % dirname, msg)

            # cleanup
            shutil.rmtree(dirname, True)

    @common.skipUnlessWindows
    def test_filekey_with_path_including_systemdrive(self):
        (ini_h, self.ini_fn) = tempfile.mkstemp(
            suffix='.ini', prefix='winapp2')
        os.close(ini_h)
        # lexists(r'C:filename') returns False
        # FindFilesW(r'C:filename') throws an exception
        # So assert that we use r'C:\filename'.
        # We need this test because winapp2.ini supports such paths and
        # giving r'C:filename' as argument to lexists or FindFilesW
        # causes a hard to detect issue, which has been detected because
        # lexists('C:filename') returns True when called through PyCharm.
        # Also test_remote is supposed to run cleaners that contain
        # such paths but it doesn't assert if those cleaners actually
        # clean their targets.

        filename = os.path.join('C:\\', 'deleteme.txt')
        open(filename, 'w').close()
        self.assertExists(filename)

        with mock.patch('os.path.lexists') as mock_lexists:
            cleaner = self.ini2cleaner('FileKey1=%SystemDrive%|deleteme.txt')
            self.run_all(cleaner, True)
            mock_lexists.assert_any_call(r'C:\deleteme.txt')

        self.assertNotExists(filename)

    @common.skipUnlessWindows
    def test_removeself(self):
        """Test for the removeself option"""

        # indexes for test
        # position 0: FileKey statement
        # position 1: whether the file `dir_c\subdir\foo.log` should exist after operation is complete
        # position 2: path of top-folder which should have been deleted
        tests = (
            # Refer to directory directly (i.e., without a glob).
            (r'FileKey1=%s\dir_c|*.*|REMOVESELF' % self.tempdir, False, r'%s\dir_c' % self.tempdir),
            # Refer to file that exists. This is invalid, so nothing happens.
            (r'FileKey1=%s\dir_c\submarine_sandwich.log|*.*|REMOVESELF' %
             self.tempdir, True, ''),
            (r'FileKey1=%s\dir_c\submarine*|*.*|REMOVESELF' % self.tempdir, True, ''),
            # Refer to path that does not exist, so nothing happens.
            (r'FileKey1=%s\dir_c\doesnotexist.log|*.*|REMOVESELF' %
             self.tempdir, True, ''),
            # Refer by glob to both a file and directory (which both start with `sub`).
            # This should affect only the directory.
            (r'FileKey1=%s\dir_a\sub*|*.*|REMOVESELF' % self.tempdir, True, r'%s\dir_a\subdir' % self.tempdir),
            # glob in middle of directory path with whole directory entry
            (r'FileKey1=%s\*c\subdir|*.*|REMOVESELF' % self.tempdir, False, r'%s\dir_c\subdir' % self.tempdir),
            (r'FileKey1=%s\*doesnotexist\subdir|*.*|REMOVESELF' % self.tempdir, True, ''),
            # glob at end of path
            (r'FileKey1=%s\dir_c\sub*|*.*|REMOVESELF' % self.tempdir, False, r'%s\dir_c\subdir' % self.tempdir),
            (r'FileKey1=%s\dir_c\doesnotexist*|*.*|REMOVESELF' % self.tempdir, True, '')
        )

        (ini_h, self.ini_fn) = tempfile.mkstemp(
            suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        for filekey, c_log_expected, top_log_expected in tests:
            for letter in ('a', 'b', 'c'):
                # Make three directories, each with a `foo.log` file.
                fn = os.path.join(self.tempdir, 'dir_' +
                                  letter, 'subdir', 'foo.log')
                common.touch_file(fn)

            # In dir_a, place a file one level up from `foo.log`.
            # Notice the glob `dir_a\sub*` will match both a directory and file.
            fn2 = os.path.join(self.tempdir, 'dir_a', 'submarine_sandwich.log')
            common.touch_file(fn2)

            cleaner = self.ini2cleaner(filekey)
            self.assertExists(fn, filekey)
            self.assertExists(fn2, filekey)
            if top_log_expected:
                self.assertExists(top_log_expected, filekey)
            self.run_all(cleaner, True)
            if c_log_expected:
                self.assertExists(fn, filekey)
            else:
                self.assertNotExists(fn, filekey)
            if top_log_expected != '':
                self.assertNotExists(top_log_expected, filekey)
            self.assertExists(fn2, filekey)
            if top_log_expected:
                self.assertNotExists(top_log_expected, filekey)

    def test_section2option(self):
        """Test for section2option()"""
        tests = (('  FOO2  ', 'foo2'),
                 ('A - B (C)', 'a_b_c'))
        for test in tests:
            self.assertEqual(section2option(test[0]), test[1])

    def test_many_patterns(self):
        """Test a cleaner like Steam Installers and related performance improvement

        https://github.com/bleachbit/bleachbit/issues/325
        """

        # set up environment
        file_count = 1000
        dir_count = 10
        print('Making %d files in each of %d directories.' %
              (file_count, dir_count))
        tmp_dir = tempfile.mkdtemp()
        for i_d in range(1, dir_count+1):
            sub_dir = os.path.join(tmp_dir, 'dir%d' % i_d)
            for i_f in range(1, file_count+1):
                tmp_fn = os.path.join(sub_dir, 'file%d' % i_f)
                common.touch_file(tmp_fn)

        (ini_h, self.ini_fn) = tempfile.mkstemp(
            suffix='.ini', prefix='winapp2')
        os.close(ini_h)

        import string
        searches = ';'.join(
            ['*.%s' % letter for letter in string.ascii_letters[0:26]])
        cleaner = self.ini2cleaner(
            'FileKey1=%s|%s|RECURSE' % (tmp_dir, searches))

        # preview
        import time
        t0 = time.time()
        self.run_all(cleaner, False)
        t1 = time.time()
        print('Elapsed time in preview: %.4f seconds ' % (t1-t0))

        # delete
        self.run_all(cleaner, False)

        # clean up
        shutil.rmtree(tmp_dir)
