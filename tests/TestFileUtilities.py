# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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
Test case for module FileUtilities
"""

from __future__ import absolute_import, print_function

from tests import common
from bleachbit.FileUtilities import *
from bleachbit.Options import options
from bleachbit import expanduser, expandvars, logger

import json
import sys
import unittest


def test_ini_helper(self, execute):
    """Used to test .ini cleaning in TestAction and in TestFileUtilities"""

    teststr = b'#Test\n[RecentsMRL]\nlist=C:\\Users\\me\\Videos\\movie.mpg,C:\\Users\\me\\movie2.mpg\n\n'
    # create test file
    filename = self.write_file('bleachbit-test-ini', teststr)
    self.assertExists(filename)
    size = os.path.getsize(filename)
    self.assertEqual(len(teststr), size)

    # section does not exist
    execute(filename, 'Recents', None)
    self.assertEqual(len(teststr), os.path.getsize(filename))

    # parameter does not exist
    execute(filename, 'RecentsMRL', 'files')
    self.assertEqual(len(teststr), os.path.getsize(filename))

    # parameter does exist
    execute(filename, 'RecentsMRL', 'list')
    self.assertEqual(14, os.path.getsize(filename))

    # section does exist
    execute(filename, 'RecentsMRL', None)
    self.assertEqual(0, os.path.getsize(filename))

    # clean up
    delete(filename)
    self.assertNotExists(filename)


def test_json_helper(self, execute):
    """Used to test JSON cleaning in TestAction and in TestFileUtilities"""

    def load_js(js_fn):
        with open(js_fn, 'r') as js_fd:
            return json.load(js_fd)

    expected = {'deleteme': 1, 'spareme': {'deletemetoo': 1}}

    # create test file
    (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-json', dir=self.tempdir)
    os.write(fd, '{ "deleteme" : 1, "spareme" : { "deletemetoo" : 1 } }')
    os.close(fd)
    self.assertExists(filename)
    self.assertEqual(load_js(filename), expected)

    # invalid key
    execute(filename, 'doesnotexist')
    self.assertEqual(load_js(filename), expected)

    # invalid key
    execute(filename, 'deleteme/doesnotexist')
    self.assertEqual(load_js(filename), expected)

    # valid key
    execute(filename, 'deleteme')
    self.assertEqual(load_js(filename), {'spareme': {'deletemetoo': 1}})

    # valid key
    execute(filename, 'spareme/deletemetoo')
    self.assertEqual(load_js(filename), {'spareme': {}})

    # valid key
    execute(filename, 'spareme')
    self.assertEqual(load_js(filename), {})

    # clean up
    delete(filename)
    self.assertNotExists(filename)


class FileUtilitiesTestCase(common.BleachbitTestCase):
    """Test case for module FileUtilities"""

    def test_bytes_to_human(self):
        """Unit test for class bytes_to_human"""

        if 'posix' == os.name:
            old_locale = locale.getlocale(locale.LC_NUMERIC)
            locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')

        # test one-way conversion for predefined values
        # each test is a tuple in the format: (bytes, SI, EIC)
        tests = ((-1, '-1B', '-1B'),
                 (0, '0', '0'),
                 (1, '1B', '1B'),
                 (1000, '1kB', '1000B'),
                 (1024, '1kB', '1KiB'),
                 (1110, '1.1kB', '1.1KiB'),
                 (1000**2, '1MB', '976.6KiB'),
                 (1024**2, '1MB', '1MiB'),
                 (1289748, '1.3MB', '1.2MiB'),
                 (1000**3, '1GB', '953.7MiB'),
                 (1024**3, '1.07GB', '1GiB'),
                 (1320702444, '1.32GB', '1.23GiB'),
                 (1000**4, '1TB', '931.32GiB'),
                 (1024**4, '1.1TB', '1TiB'),
                 (1000**5, '1PB', '909.49TiB'),
                 (1024**5, '1.13PB', '1PiB'))

        options.set('units_iec', True)
        for test in tests:
            iec = bytes_to_human(test[0])
            self.assertEqual(test[2], iec,
                             'bytes_to_human(%d) IEC = %s but expected %s' % (test[0], iec, test[2]))

        options.set('units_iec', False)
        for test in tests:
            si = bytes_to_human(test[0])
            self.assertEqual(test[1], si,
                             'bytes_to_human(%d) SI = %s but expected %s' % (test[0], si, test[1]))

        # test roundtrip conversion for random values
        import random
        for n in range(0, 1000):
            bytes1 = random.randrange(0, 1000 ** 4)
            human = bytes_to_human(bytes1)
            bytes2 = human_to_bytes(human)
            error = abs(float(bytes2 - bytes1) / bytes1)
            self.assertLess(abs(error), 0.01, "%d (%s) is %.2f%% different than %d" %
                            (bytes1, human, error * 100, bytes2))

        # test localization
        if hasattr(locale, 'format_string'):
            try:
                locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
            except:
                logger.warning('exception when setlocale to de_DE.utf8')
            else:
                self.assertEqual("1,01GB", bytes_to_human(1000 ** 3 + 5812389))

        # clean up
        if 'posix' == os.name:
            locale.setlocale(locale.LC_NUMERIC, old_locale)

    def test_children_in_directory(self):
        """Unit test for function children_in_directory()"""

        # test an existing directory that usually exists
        dirname = expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assertTrue(os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assertTrue(os.path.isabs(filename))
            self.assertFalse(os.path.isdir(filename))

        # test a constructed file in a constructed directory
        dirname = self.mkdtemp(prefix='bleachbit-test-children')
        filename = self.mkstemp(prefix="somefile", dir=dirname)
        for loopfilename in children_in_directory(dirname, True):
            self.assertEqual(loopfilename, filename)
        for loopfilename in children_in_directory(dirname, False):
            self.assertEqual(loopfilename, filename)
        os.remove(filename)

        # test subdirectory
        subdirname = os.path.join(dirname, "subdir")
        os.mkdir(subdirname)
        for filename in children_in_directory(dirname, True):
            self.assertEqual(filename, subdirname)
        for filename in children_in_directory(dirname, False):
            raise AssertionError('Found a file that shouldn\'t have been found: ' + filename)
        os.rmdir(subdirname)

        os.rmdir(dirname)

    def test_clean_ini(self):
        """Unit test for clean_ini()"""
        print("testing test_clean_ini() with shred = False")
        options.set('shred', False, commit=False)
        test_ini_helper(self, clean_ini)

        print("testing test_clean_ini() with shred = True")
        options.set('shred', True, commit=False)
        test_ini_helper(self, clean_ini)

    def test_clean_json(self):
        """Unit test for clean_json()"""
        print("testing test_clean_json() with shred = False")
        options.set('shred', False, commit=False)
        test_json_helper(self, clean_json)

        print("testing test_clean_json() with shred = True")
        options.set('shred', True, commit=False)
        test_json_helper(self, clean_json)

    def test_delete(self):
        """Unit test for method delete()"""
        print("testing delete() with shred = False")
        self.delete_helper(shred=False)
        print("testing delete() with shred = True")
        self.delete_helper(shred=True)
        # exercise ignore_missing
        delete('does-not-exist', ignore_missing=True)
        self.assertRaises(OSError, delete, 'does-not-exist')

    def delete_helper(self, shred):
        """Called by test_delete() with shred = False and = True"""

        # test deleting with various kinds of filenames
        hebrew = u"עִבְרִית"
        katanana = u"アメリカ"
        umlauts = u"ÄäǞǟËëḦḧÏïḮḯÖöȪȫṎṏT̈ẗÜüǕǖǗǘǙǚǛǜṲṳṺṻẄẅẌẍŸÿ"

        tests = ['.prefixandsuffix',  # simple
                 "x".zfill(150),  # long
                 ' begins_with_space',
                 "''",  # quotation mark
                 "~`!@#$%^&()-_+=x",  # non-alphanumeric characters
                 "[]{};'.,x",  # non-alphanumeric characters
                 u'abcdefgh',  # simple Unicode
                 u'J\xf8rgen Scandinavian',
                 u'\u2014em-dash',  # LP#1454030
                 hebrew,
                 katanana,
                 umlauts,
                 'sigil-should$not-change']
        if 'posix' == os.name:
            # Windows doesn't allow these characters but Unix systems do
            tests += ['"*', '\t\\', ':?<>|',
                      ' ', '.file.'] # Windows filenames cannot end with space or period
        for test in tests:
            # create the file
            filename = self.write_file(test, "top secret")
            # delete the file
            delete(filename, shred)
            self.assertNotExists(filename)

            # delete an empty directory
            dirname = self.mkdtemp(prefix=test)
            self.assertExists(dirname)
            delete(dirname, shred)
            self.assertNotExists(dirname)

        def symlink_helper(link_fn):
            if 'nt' == os.name:
                from win32com.shell import shell
                if not shell.IsUserAnAdmin():
                    self.skipTest('skipping symlink test because of insufficient privileges')

            # make regular file
            srcname = self.mkstemp(prefix='bleachbit-test-delete-regular')

            # make symlink
            self.assertExists(srcname)
            linkname = tempfile.mktemp('bblink')
            self.assertNotExists(linkname)
            link_fn(srcname, linkname)
            self.assertExists(linkname)
            self.assertLExists(linkname)

            # delete symlink
            delete(linkname, shred)
            self.assertExists(srcname)
            self.assertNotLExists(linkname)

            # delete regular file
            delete(srcname, shred)
            self.assertNotExists(srcname)

            #
            # test broken symlink
            #
            srcname = self.mkstemp(prefix='bleachbit-test-delete-sym')
            self.assertLExists(srcname)
            link_fn(srcname, linkname)
            self.assertLExists(linkname)
            self.assertExists(linkname)

            # delete regular file first
            delete(srcname, shred)
            self.assertNotExists(srcname)
            self.assertLExists(linkname)

            # clean up
            delete(linkname, shred)
            self.assertNotExists(linkname)
            self.assertNotLExists(linkname)

        windows_xp_or_newer = False
        if 'nt' == os.name:
            from bleachbit.Windows import parse_windows_build
            # Windows XP = 5.1
            windows_xp_or_newer = parse_windows_build() > 5.1

        if windows_xp_or_newer:
            # test symlinks
            import ctypes
            kern = ctypes.windll.LoadLibrary("kernel32.dll")

            def win_symlink(src, linkname):
                rc = kern.CreateSymbolicLinkA(linkname, src, 0)
                if rc == 0:
                    print('CreateSymbolicLinkA(%s, %s)' % (linkname, src))
                    print('CreateSymolicLinkA() failed, error = %s' % ctypes.FormatError())
                    self.assertNotEqual(rc, 0)
            symlink_helper(win_symlink)

        # below this point, only posix
        if 'nt' == os.name:
            return

        # test file with mode 0444/-r--r--r--
        filename = self.write_file('bleachbit-test-0444')
        os.chmod(filename, 0o444)
        delete(filename, shred)
        self.assertNotExists(filename)

        # test symlink
        symlink_helper(os.symlink)

        # test FIFO
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assertExists(filename)
        delete(filename, shred)
        self.assertNotExists(filename)

        # test directory
        path = self.mkdtemp(prefix='bleachbit-test-delete-dir')
        self.assertExists(path)
        delete(path, shred)
        self.assertNotExists(path)

    @unittest.skipIf('nt' != os.name, 'skipping on non-Windows')
    def test_delete_locked(self):
        """Unit test for delete() with locked file"""
        # set up
        def test_delete_locked_setup():
            (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-worker')
            os.write(fd, '123')
            os.close(fd)
            self.assertExists(filename)
            self.assertEqual(3, getsize(filename))
            return filename

        # File is open but not opened exclusive, so expect that the
        # file is truncated but not deleted.
        # O_EXCL = fail if file exists (i.e., not an exclusive lock)
        filename = test_delete_locked_setup()
        f = os.open(filename, os.O_WRONLY | os.O_EXCL)
        self.assertExists(filename)
        self.assertEqual(3, getsize(filename))
        with self.assertRaises(WindowsError):
            delete(filename)
        os.close(f)
        self.assertExists(filename)
        self.assertEqual(0, getsize(filename))
        delete(filename)
        self.assertNotExists(filename)

        # File is open with exclusive lock, so expect the file is neither
        # deleted nor truncated.
        filename = test_delete_locked_setup()
        from subprocess import call
        call('start notepad.exe>>{}'.format(filename), shell=True)
        self.assertExists(filename)
        self.assertEqual(3, getsize(filename))
        with self.assertRaises(WindowsError):
            delete(filename)
        call('taskkill /f /im notepad.exe')
        self.assertExists(filename)
        self.assertEqual(3, getsize(filename))
        delete(filename)
        self.assertNotExists(filename)

    @unittest.skipIf('nt' == os.name, 'skipping on Windows')
    def test_ego_owner(self):
        """Unit test for ego_owner()"""
        self.assertEqual(ego_owner('/bin/ls'), os.getuid() == 0)

    def test_exists_in_path(self):
        """Unit test for exists_in_path()"""
        filename = 'ls'
        if 'nt' == os.name:
            filename = 'cmd.exe'
        self.assertTrue(exists_in_path(filename))

    def test_exe_exists(self):
        """Unit test for exe_exists()"""
        tests = [("/bin/sh", True),
                 ("sh", True),
                 ("doesnotexist", False),
                 ("/bin/doesnotexist", False)]
        if 'nt' == os.name:
            tests = [('c:\\windows\\system32\\cmd.exe', True),
                     ('cmd.exe', True),
                     ('doesnotexist', False),
                     ('c:\\windows\\doesnotexist.exe', False)]
        for test in tests:
            self.assertEqual(exe_exists(test[0]), test[1])

    def test_expand_glob_join(self):
        """Unit test for expand_glob_join()"""
        if 'posix' == os.name:
            expand_glob_join('/bin', '*sh')
        if 'nt' == os.name:
            expand_glob_join('c:\windows', '*.exe')

    def test_expandvars(self):
        """Unit test for expandvars()."""
        expanded = expandvars('$HOME')
        self.assertIsUnicodeString(expanded)

    def test_extended_path(self):
        """Unit test for extended_path() and extended_path_undo()"""
        if 'nt' == os.name:
            tests = [
                (r'c:\windows\notepad.exe', r'\\?\c:\windows\notepad.exe'),
                (r'\\server\share\windows\notepad.exe', r'\\?\unc\server\share\windows\notepad.exe'),
            ]
        else:
            # unchanged
            tests = (('/home/foo', '/home/foo'),)
        for short, extended in tests:
            # already extended path shouldn't be changed
            self.assertEqual(extended_path(extended), extended)
            # does the conversion work both ways?
            self.assertEqual(extended_path(short), extended)
            self.assertEqual(extended_path_undo(extended), short)
            # unextended paths shouldn't be shortened any more
            self.assertEqual(extended_path_undo(short), short)

    def test_free_space(self):
        """Unit test for free_space()"""
        home = expanduser('~')
        result = free_space(home)
        self.assertNotEqual(result, None)
        self.assertGreater(result, -1)
        self.assertIsInteger(result)

        # compare to WMIC
        if 'nt' != os.name:
            return
        args = ['wmic',  'LogicalDisk', 'get', 'DeviceID,', 'FreeSpace']
        from bleachbit.General import run_external
        (rc, stdout, stderr) = run_external(args)
        if rc:
            print('error calling WMIC\nargs=%s\nstderr=%s' % (args, stderr))
            return
        import re
        for line in stdout.split('\n'):
            line = line.strip()
            if not re.match('([A-Z]):\s+(\d+)', line):
                continue
            drive, bytes_free = re.split('\s+', line)
            print('Checking free space for %s' % drive)
            bytes_free = int(bytes_free)
            free = free_space(unicode(drive))
            self.assertEqual(bytes_free, free)

    def test_getsize(self):
        """Unit test for method getsize()"""
        dirname = self.mkdtemp(prefix='bleachbit-test-getsize')

        def test_getsize_helper(fname):
            filename = self.write_file(os.path.join(dirname, fname), "abcdefghij" * 12345)

            if 'nt' == os.name:
                self.assertEqual(getsize(filename), 10 * 12345)
                # Expand the directory names, which are in the short format,
                # to test the case where the full path (including the directory)
                # is longer than 255 characters.
                import win32api
                lname = win32api.GetLongPathNameW(extended_path(filename))
                self.assertEqual(getsize(lname), 10 * 12345)
                # this function returns a byte string instead of Unicode
                counter = 0
                for child in children_in_directory(dirname, False):
                    self.assertEqual(getsize(child), 10 * 12345)
                    counter += 1
                self.assertEqual(counter, 1)
            if 'posix' == os.name:
                output = subprocess.Popen(
                    ["du", "-h", filename], stdout=subprocess.PIPE).communicate()[0]
                output = output.replace("\n", "")
                du_size = output.split("\t")[0] + "B"
                print("output = '%s', size='%s'" % (output, du_size))
                du_bytes = human_to_bytes(du_size, 'du')
                print(output, du_size, du_bytes)
                self.assertEqual(getsize(filename), du_bytes)
            delete(filename)
            self.assertNotExists(filename)

        # create regular file
        test_getsize_helper('bleachbit-test-regular')

        # special characters
        test_getsize_helper(u'bleachbit-test-special-characters-∺ ∯')

        # em-dash (LP1454030)
        test_getsize_helper(u'bleachbit-test-em-dash-\u2014')

        # long
        test_getsize_helper(u'bleachbit-test-long' + 'x' * 200)

        # delete the empty directory
        delete(dirname)

        if 'nt' == os.name:
            # the following tests do not apply to Windows
            return

        # create a symlink
        filename = self.write_file('bleachbit-test-symlink', 'abcdefghij' * 12345)
        linkname = os.path.join(self.tempdir, 'bleachbitsymlinktest')
        if os.path.lexists(linkname):
            delete(linkname)
        os.symlink(filename, linkname)
        self.assertLess(getsize(linkname), 8192, "Symlink size is %d" % getsize(filename))
        delete(filename)

        if 'darwin' == sys.platform:
            # MacOS's HFS+ filesystem doesn't support sparse files
            return

        # create sparse file
        (handle, filename) = tempfile.mkstemp(prefix="bleachbit-test-sparse")
        os.ftruncate(handle, 1000 ** 2)
        os.close(handle)
        self.assertEqual(getsize(filename), 0)
        delete(filename)

    def test_getsizedir(self):
        """Unit test for getsizedir()"""
        path = '/bin'
        if 'nt' == os.name:
            path = 'c:\\windows\\system32'
        self.assertGreater(getsizedir(path), 0)

    def test_globex(self):
        """Unit test for method globex()"""
        for path in globex('/bin/*', '/ls$'):
            self.assertEqual(path, '/bin/ls')

    def test_guess_overwrite_paths(self):
        """Unit test for guess_overwrite_paths()"""
        for path in guess_overwrite_paths():
            self.assertTrue(os.path.isdir(path), '%s is not a directory' % path)

    def test_human_to_bytes(self):
        """Unit test for human_to_bytes()"""
        self.assertRaises(ValueError, human_to_bytes, '', hformat='invalid')

        for test in ['Bazillion kB', '120XB', '.12MB']:
            self.assertRaises(ValueError, human_to_bytes, test)

        valid = {'1kB': 1000,
                 '1.1MB': 1100000,
                 '12B': 12,
                 '1.0M': 1000*1000,
                 '1TB': 1000**4,
                 '1000': 1000}
        for test, result in valid.items():
            self.assertEqual(human_to_bytes(test), result)

        self.assertEqual(human_to_bytes('1 MB', 'du'), 1024*1024)

    def test_listdir(self):
        """Unit test for listdir()"""
        if 'posix' == os.name:
            dir1 = '/tmp'
            dir2 = expanduser('~/.config')
        if 'nt' == os.name:
            dir1 = expandvars(r'%windir%\fonts')
            dir2 = expandvars(r'%userprofile%\desktop')
        # If these directories do not exist, the test results are not valid.
        self.assertExists(dir1)
        self.assertExists(dir2)
        # Every path found in dir1 and dir2 should be found in (dir1, dir2).
        paths1 = set(listdir(dir1))
        paths2 = set(listdir(dir2))
        paths12 = set(listdir((dir1,dir2)))
        self.assertTrue(paths1 < paths12)
        self.assertTrue(paths2 < paths12)
        # The individual calls should be equivalent to a combined call.
        self.assertSetEqual(paths1.union(paths2), paths12)
        # The directories should not be empty.
        self.assertGreater(len(paths1), 0)
        self.assertGreater(len(paths2), 0)
        # Every path found should exist.
        for pathname in paths12:
            self.assertLExists(pathname)

    def test_same_partition(self):
        """Unit test for same_partition()"""
        home = expanduser('~')
        self.assertTrue(same_partition(home, home))
        if 'posix' == os.name:
            self.assertFalse(same_partition(home, '/dev'))
        if 'nt' == os.name:
            home_drive = os.path.splitdrive(home)[0]
            from bleachbit.Windows import get_fixed_drives
            for drive in get_fixed_drives():
                this_drive = os.path.splitdrive(drive)[0]
                self.assertEqual(same_partition(home, drive), home_drive == this_drive)

    def test_whitelisted(self):
        """Unit test for whitelisted()"""
        # setup
        old_whitelist = options.get_whitelist_paths()
        whitelist = [('file', '/home/foo'), ('folder', '/home/folder')]
        options.set_whitelist_paths(whitelist)
        self.assertEqual(set(whitelist), set(options.get_whitelist_paths()))

        # test
        self.assertFalse(whitelisted(''))
        self.assertFalse(whitelisted('/'))

        self.assertFalse(whitelisted('/home/foo2'))
        self.assertFalse(whitelisted('/home/fo'))
        self.assertTrue(whitelisted('/home/foo'))

        self.assertTrue(whitelisted('/home/folder'))
        if 'posix' == os.name:
            self.assertTrue(whitelisted('/home/folder/'))
            self.assertTrue(whitelisted('/home/folder/file'))
        self.assertFalse(whitelisted('/home/fold'))
        self.assertFalse(whitelisted('/home/folder2'))

        if 'nt' == os.name:
            whitelist = [('folder', 'D:\\'), (
                'file', 'c:\\windows\\foo.log'), ('folder', 'e:\\users')]
            options.set_whitelist_paths(whitelist)
            self.assertTrue(whitelisted('e:\\users'))
            self.assertTrue(whitelisted('e:\\users\\'))
            self.assertTrue(whitelisted('e:\\users\\foo.log'))
            self.assertFalse(whitelisted('e:\\users2'))
            # case insensitivity
            self.assertTrue(whitelisted('C:\\WINDOWS\\FOO.LOG'))
            self.assertTrue(whitelisted('D:\\USERS'))

            # drives letters have the separator at the end while most paths
            # don't
            self.assertTrue(whitelisted('D:\\FOLDER\\FOO.LOG'))

        # test blank
        options.set_whitelist_paths([])
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

        options.config.remove_section('whitelist/paths')
        self.assertFalse(whitelisted('/home/foo'))
        self.assertFalse(whitelisted('/home/folder'))
        self.assertFalse(whitelisted('/home/folder/file'))

        # clean up
        options.set_whitelist_paths(old_whitelist)
        self.assertEqual(
            set(old_whitelist), set(options.get_whitelist_paths()))

    @unittest.skipUnless('posix' == os.name, 'skipping on non-POSIX platform')
    def test_whitelisted_posix_symlink(self):
        """Symlink test for whitelisted_posix()"""
        # setup
        old_whitelist = options.get_whitelist_paths()
        tmpdir = os.path.join(self.tempdir, 'bleachbit-whitelist')
        os.mkdir(tmpdir)
        realpath = self.write_file('real')
        linkpath = os.path.join(tmpdir, 'link')
        os.symlink(realpath, linkpath)
        self.assertExists(realpath)
        self.assertExists(linkpath)

        # test 1: the real path is whitelisted
        whitelist = [('file', realpath)]
        options.set_whitelist_paths(whitelist)
        self.assertFalse(whitelisted(tmpdir))
        self.assertTrue(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        # test 2: the link is whitelisted
        whitelist = [('file', linkpath)]
        options.set_whitelist_paths(whitelist)
        self.assertFalse(whitelisted(tmpdir))
        self.assertFalse(whitelisted(realpath))
        self.assertTrue(whitelisted(linkpath))

        options.set_whitelist_paths(old_whitelist)

    def test_whitelisted_speed(self):
        """Benchmark the speed of whitelisted()

        It is called frequently, so the speed is important."""
        d = '/usr/bin'
        whitelist = [('file', '/home/foo'), ('folder', '/home/folder')]
        if 'nt' == os.name:
            d = expandvars('%windir%\system32')
            whitelist = [('file', r'c:\\filename'), ('folder', r'c:\\folder')]
        reps = 20
        paths = [p for p in children_in_directory(d, True)]
        paths = paths[:1000]  # truncate
        self.assertGreater(len(paths), 10)
        old_whitelist = options.get_whitelist_paths()
        options.set_whitelist_paths(whitelist)

        t0 = time.time()
        for i in xrange(0, reps):
            for p in paths:
                _ = whitelisted(p)
        t1 = time.time()
        logger.info('whitelisted() with {} repetitions and {} paths took {:.3g} seconds '.format(
            reps, len(paths), t1 - t0))

        options.set_whitelist_paths(old_whitelist)

    def test_wipe_contents(self):
        """Unit test for wipe_delete()"""

        # create test file
        filename = self.write_file('bleachbit-test-wipe', 'abcdefghij' * 12345)

        # wipe it
        wipe_contents(filename)

        # check it
        f = open(filename, 'rb')
        while True:
            byte = f.read(1)
            if "" == byte:
                break
            self.assertEqual(byte, chr(0))
        f.close()

        # clean up
        os.remove(filename)

    def wipe_name_helper(self, filename):
        """Helper for test_wipe_name()"""

        self.assertExists(filename)

        # test
        newname = wipe_name(filename)
        self.assertGreater(len(filename), len(newname))
        self.assertNotExists(filename)
        self.assertExists(newname)

        # clean
        os.remove(newname)
        self.assertNotExists(newname)

    def test_wipe_name(self):
        """Unit test for wipe_name()"""

        # create test file with moderately long name
        filename = self.write_file('bleachbit-test-wipe' + '0' * 50)
        self.wipe_name_helper(filename)

        # create file with short name in temporary directory with long name
        if 'nt' == os.name:
            # In Windows, the maximum path length is 260 characters
            # http://msdn.microsoft.com/en-us/library/aa365247%28VS.85%29.aspx#maxpath
            dir0len = 100
            dir1len = 5
        else:
            dir0len = 210
            dir1len = 210
        filelen = 10

        dir0 = self.mkdtemp(prefix="0" * dir0len)
        self.assertExists(dir0)

        dir1 = self.mkdtemp(prefix="1" * dir1len, dir=dir0)
        self.assertExists(dir1)

        filename = self.write_file(os.path.join(dir1, '2' * filelen))
        self.wipe_name_helper(filename)
        self.assertExists(dir0)
        self.assertExists(dir1)

        # wipe a directory name
        dir1new = wipe_name(dir1)
        self.assertGreater(len(dir1), len(dir1new))
        self.assertNotExists(dir1)
        self.assertExists(dir1new)
        os.rmdir(dir1new)

        # wipe the directory
        os.rmdir(dir0)
        self.assertNotExists(dir0)

    @unittest.skipUnless(os.getenv('ALLTESTS') is not None,
                         'warning: skipping long test test_wipe_path() because environment variable ALLTESTS not set')
    def test_wipe_path(self):
        """Unit test for wipe_path()"""

        for ret in wipe_path(self.tempdir):
            # no idle handler
            pass

    def test_vacuum_sqlite3(self):
        """Unit test for method vacuum_sqlite3()"""
        import sqlite3

        path = os.path.abspath('bleachbit.tmp.sqlite3')
        if os.path.lexists(path):
            delete(path)

        conn = sqlite3.connect(path)
        conn.execute('create table numbers (number)')
        conn.commit()
        empty_size = getsize(path)

        def number_generator():
            for x in range(1, 10000):
                yield (x, )
        conn.executemany('insert into numbers (number) values ( ? ) ', number_generator())
        conn.commit()
        self.assertLess(empty_size, getsize(path))
        conn.execute('delete from numbers')
        conn.commit()
        conn.close()

        vacuum_sqlite3(path)
        self.assertEqual(empty_size, getsize(path))

        delete(path)

    @unittest.skipIf('nt' == os.name, 'skipping on Windows')
    def test_OpenFiles(self):
        """Unit test for class OpenFiles"""

        filename = os.path.join(self.tempdir, 'bleachbit-test-open-files')
        f = open(filename, 'w')
        openfiles = OpenFiles()
        self.assertTrue(openfiles.is_open(filename),
                        "Expected is_open(%s) to return True)\n"
                        "openfiles.last_scan_time (ago)=%s\n"
                        "openfiles.files=%s" %
                        (filename,
                         time.time() - openfiles.last_scan_time,
                         openfiles.files))

        f.close()
        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

        os.unlink(filename)
        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

    def test_open_files_lsof(self):
        self.assertEqual(list(open_files_lsof(lambda: 'n/bar/foo\nn/foo/bar\nnoise')), ['/bar/foo', '/foo/bar'])
