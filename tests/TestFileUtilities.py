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
Test case for module FileUtilities
"""

from __future__ import absolute_import, print_function

from tests import common
from bleachbit.FileUtilities import *
from bleachbit.Options import options
from bleachbit import expanduser, expandvars, logger

import json
import platform
import sys
import unittest





def test_ini_helper(self, execute):
    """Used to test .ini cleaning in TestAction and in TestFileUtilities"""

    # create test file
    (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-ini')
    os.write(fd, '#Test\n')
    os.write(fd, '[RecentsMRL]\n')
    os.write(
        fd, 'list=C:\\Users\\me\\Videos\\movie.mpg,C:\\Users\\me\\movie2.mpg\n\n')
    os.close(fd)
    self.assert_(os.path.exists(filename))
    size = os.path.getsize(filename)
    self.assertEqual(77, size)

    # section does not exist
    execute(filename, 'Recents', None)
    self.assertEqual(77, os.path.getsize(filename))

    # parameter does not exist
    execute(filename, 'RecentsMRL', 'files')
    self.assertEqual(77, os.path.getsize(filename))

    # parameter does exist
    execute(filename, 'RecentsMRL', 'list')
    self.assertEqual(14, os.path.getsize(filename))

    # section does exist
    execute(filename, 'RecentsMRL', None)
    self.assertEqual(0, os.path.getsize(filename))

    # clean up
    delete(filename)
    self.assert_(not os.path.exists(filename))


def test_json_helper(self, execute):
    """Used to test JSON cleaning in TestAction and in TestFileUtilities"""

    def load_js(js_fn):
        js_fd = open(js_fn, 'r')
        return json.load(js_fd)

    # create test file
    (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-json')
    os.write(fd, '{ "deleteme" : 1, "spareme" : { "deletemetoo" : 1 } }')
    os.close(fd)
    self.assert_(os.path.exists(filename))
    self.assertEqual(load_js(filename), {
                     'deleteme': 1, 'spareme': {'deletemetoo': 1}})

    # invalid key
    execute(filename, 'doesnotexist')
    self.assertEqual(load_js(filename), {
                     'deleteme': 1, 'spareme': {'deletemetoo': 1}})

    # invalid key
    execute(filename, 'deleteme/doesnotexist')
    self.assertEqual(load_js(filename), {
                     'deleteme': 1, 'spareme': {'deletemetoo': 1}})

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
    self.assert_(not os.path.exists(filename))


class FileUtilitiesTestCase(unittest.TestCase, common.AssertFile):

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
            self.assert_(abs(error) < 0.01,
                         "%d (%s) is %.2f%% different than %d" %
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
            self.assert_(os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assert_(os.path.isabs(filename))
            self.assert_(not os.path.isdir(filename))

        # test a constructed file in a constructed directory
        dirname = tempfile.mkdtemp(prefix='bleachbit-test-children')
        filename = os.path.join(dirname, "somefile")
        common.touch_file(filename)
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
            self.assert_(False)
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

        tests = [('.prefix', 'suffix'),  # simple
                 ("x".zfill(100), ".y".zfill(50)),  # long
                 (' ', 'begins_with_space'),
                 ("'", "'"),  # quotation mark
                 ("~`!@#$%^&()-_+=", "x"),  # non-alphanumeric characters
                 ("[]{};'.,", "x"),  # non-alphanumeric characters
                 (u'abcd', u'efgh'),  # simple Unicode
                 (u'J\xf8rgen', 'Scandinavian'),
                 (u'\u2014', 'em-dash'),  # LP#1454030
                 (hebrew, hebrew),
                 (katanana, katanana),
                 (umlauts, umlauts),
                 ('sigil', 'should$not-change')]
        if 'posix' == os.name:
            # Windows doesn't allow these characters but Unix systems do
            tests.append(('"', '*'))
            tests.append(('\t', '\\'))
            tests.append((':?', '<>|'))
            # Windows filenames cannot end with space or period
            tests.append((' ', ' '))
            tests.append(('.', '.'))
        for test in tests:
            # delete a file
            (fd, filename) = tempfile.mkstemp(
                prefix='bleachbit-test-delete-file' + test[0], suffix=test[1])
            self.assert_(os.path.exists(filename))
            for x in range(0, 4096):
                bytes_written = os.write(fd, "top secret")
                self.assertEqual(bytes_written, 10)
            os.close(fd)
            self.assert_(os.path.exists(filename))
            delete(filename, shred)
            self.assert_(not os.path.exists(filename))

            # delete an empty directory
            dirname = tempfile.mkdtemp(
                prefix='bleachbit-test-delete-dir' + test[0], suffix=test[1])
            self.assert_(os.path.exists(dirname))
            delete(dirname, shred)
            self.assert_(not os.path.exists(dirname))

        def symlink_helper(link_fn):
            if 'nt' == os.name:
                from win32com.shell import shell
                if not shell.IsUserAnAdmin():
                    self.skipTest('skipping symlink test because of insufficient privileges')

            # make regular file
            (fd, srcname) = tempfile.mkstemp(
                prefix='bleachbit-test-delete-regular')
            os.close(fd)

            # make symlink
            self.assert_(os.path.exists(srcname))
            linkname = tempfile.mktemp('bblink')
            self.assert_(not os.path.exists(linkname))
            link_fn(srcname, linkname)
            self.assert_(os.path.exists(linkname))
            self.assert_(os.path.lexists(linkname))

            # delete symlink
            delete(linkname, shred)
            self.assert_(os.path.exists(srcname))
            self.assert_(not os.path.lexists(linkname))

            # delete regular file
            delete(srcname, shred)
            self.assert_(not os.path.exists(srcname))

            #
            # test broken symlink
            #
            (fd, srcname) = tempfile.mkstemp(
                prefix='bleachbit-test-delete-sym')
            os.close(fd)
            self.assert_(os.path.lexists(srcname))
            link_fn(srcname, linkname)
            self.assert_(os.path.lexists(linkname))
            self.assert_(os.path.exists(linkname))

            # delete regular file first
            delete(srcname, shred)
            self.assert_(not os.path.exists(srcname))
            self.assertLExists(linkname)

            # clean up
            delete(linkname, shred)
            self.assert_(not os.path.exists(linkname))
            self.assert_(not os.path.lexists(linkname))

        if 'nt' == os.name and platform.uname()[3][0:3] > '5.1':
            # Windows XP = 5.1
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
        (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-0444')
        os.close(fd)
        os.chmod(filename, 0o444)
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test symlink
        symlink_helper(os.symlink)

        # test FIFO
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assert_(os.path.exists(filename))
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test directory
        path = tempfile.mkdtemp(prefix='bleachbit-test-delete-dir')
        self.assert_(os.path.exists(path))
        delete(path, shred)
        self.assert_(not os.path.exists(path))

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
        self.assert_(exists_in_path(filename))

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
        self.assertTrue(isinstance(expanded, unicode))

    def test_extended_path(self):
        """Unit test for extended_path() and extended_path_undo()"""
        if 'nt' == os.name:
            tests = (
                (r'c:\windows\notepad.exe', r'\\?\c:\windows\notepad.exe'),
                (r'c:\windows\notepad.exe', r'\\?\c:\windows\notepad.exe'),
                (r'\\?\c:\windows\notepad.exe', r'\\?\c:\windows\notepad.exe'),
                (r'\\server\share\windows\notepad.exe', r'\\?\unc\server\share\windows\notepad.exe'),
                (r'\\?\unc\server\share\windows\notepad.exe', r'\\?\unc\server\share\windows\notepad.exe')
            )
            tests_undo = (
                (r'\\?\c:\windows\notepad.exe', r'c:\windows\notepad.exe'),
                (r'c:\windows\notepad.exe', r'c:\windows\notepad.exe'),
                (r'\\?\unc\server\share\windows\notepad.exe', r'\\server\share\windows\notepad.exe'),
                (r'\\server\share\windows\notepad.exe',
                 r'\\server\share\windows\notepad.exe')
            )

        else:
            # unchanged
            tests = (('/home/foo', '/home/foo'),)
            tests_undo = tests
        for test in tests:
            self.assertEqual(extended_path(test[0]), test[1])
        for test in tests_undo:
            self.assertEqual(extended_path_undo(test[0]), test[1])

    def test_free_space(self):
        """Unit test for free_space()"""
        home = expanduser('~')
        result = free_space(home)
        self.assertNotEqual(result, None)
        self.assert_(result > -1)
        self.assert_(isinstance(result, (int, long)))

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
        dirname = tempfile.mkdtemp(prefix='bleachbit-test-getsize')

        def test_getsize_helper(fname):
            filename = os.path.join(dirname, fname)
            common.write_file(filename, "abcdefghij" * 12345)

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
            self.assert_(not os.path.exists(filename))

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
        (handle, filename) = tempfile.mkstemp(prefix='bleachbit-test-symlink')
        os.write(handle, "abcdefghij" * 12345)
        os.close(handle)
        linkname = '/tmp/bleachbitsymlinktest'
        if os.path.lexists(linkname):
            delete(linkname)
        os.symlink(filename, linkname)
        self.assert_(getsize(linkname) < 8192, "Symlink size is %d" %
                     getsize(filename))
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
        self.assert_(getsizedir(path) > 0)

    def test_globex(self):
        """Unit test for method globex()"""
        for path in globex('/bin/*', '/ls$'):
            self.assertEqual(path, '/bin/ls')

    def test_guess_overwrite_paths(self):
        """Unit test for guess_overwrite_paths()"""
        for path in guess_overwrite_paths():
            self.assert_(os.path.isdir(path), '%s is not a directory' % path)

    def test_human_to_bytes(self):
        """Unit test for human_to_bytes()"""
        self.assertRaises(ValueError, human_to_bytes, '', hformat='invalid')

        invalid = ['Bazillion kB',
                   '120XB',
                   '.12MB']
        for test in invalid:
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
                self.assertEqual(same_partition(home, drive),
                                 home_drive == this_drive)

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
        tmpdir = tempfile.mkdtemp(prefix='bleachbit-whitelist')
        realpath = os.path.join(tmpdir, 'real')
        linkpath = os.path.join(tmpdir, 'link')
        common.touch_file(realpath)
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

        # clean up
        import shutil
        shutil.rmtree(tmpdir)
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
        (handle, filename) = tempfile.mkstemp(prefix="bleachbit-test-wipe")
        os.write(handle, "abcdefghij" * 12345)
        os.close(handle)

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

        self.assert_(os.path.exists(filename))

        # test
        newname = wipe_name(filename)
        self.assert_(len(filename) > len(newname))
        self.assert_(not os.path.exists(filename))
        self.assert_(os.path.exists(newname))

        # clean
        os.remove(newname)
        self.assert_(not os.path.exists(newname))

    def test_wipe_name(self):
        """Unit test for wipe_name()"""

        # create test file with moderately long name
        (handle, filename) = tempfile.mkstemp(
            prefix="bleachbit-test-wipe" + "0" * 50)
        os.close(handle)
        self.wipe_name_helper(filename)

        # create file with short name in temporary directory with long name
        if 'posix' == os.name:
            dir0len = 210
            dir1len = 210
            filelen = 10
        if 'nt' == os.name:
            # In Windows, the maximum path length is 260 characters
            # http://msdn.microsoft.com/en-us/library/aa365247%28VS.85%29.aspx#maxpath
            dir0len = 100
            dir1len = 5
            filelen = 10

        dir0 = tempfile.mkdtemp(prefix="0" * dir0len)
        self.assert_(os.path.exists(dir0))

        dir1 = tempfile.mkdtemp(prefix="1" * dir1len, dir=dir0)
        self.assert_(os.path.exists(dir1))

        (handle, filename) = tempfile.mkstemp(
            dir=dir1, prefix="2" * filelen)
        os.close(handle)
        self.wipe_name_helper(filename)
        self.assert_(os.path.exists(dir0))
        self.assert_(os.path.exists(dir1))

        # wipe a directory name
        dir1new = wipe_name(dir1)
        self.assert_(len(dir1) > len(dir1new))
        self.assert_(not os.path.exists(dir1))
        self.assert_(os.path.exists(dir1new))
        os.rmdir(dir1new)

        # wipe the directory
        os.rmdir(dir0)
        self.assert_(not os.path.exists(dir0))

    def test_wipe_path(self):
        """Unit test for wipe_path()"""

        if None == os.getenv('ALLTESTS'):
            self.skipTest('warning: skipping long test test_wipe_path() because environment variable ALLTESTS not set')

        pathname = tempfile.gettempdir()
        for ret in wipe_path(pathname):
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
        conn.executemany(
            'insert into numbers (number) values ( ? ) ', number_generator())
        conn.commit()
        self.assert_(empty_size < getsize(path))
        conn.execute('delete from numbers')
        conn.commit()
        conn.close()

        vacuum_sqlite3(path)
        self.assertEqual(empty_size, getsize(path))

        delete(path)

    @unittest.skipIf('nt' == os.name, 'skipping on Windows')
    def test_OpenFiles(self):
        """Unit test for class OpenFiles"""

        (handle, filename) = tempfile.mkstemp(
            prefix='bleachbit-test-open-files')
        openfiles = OpenFiles()
        self.assertTrue(openfiles.is_open(filename),
                        "Expected is_open(%s) to return True)\n"
                        "openfiles.last_scan_time (ago)=%s\n"
                        "openfiles.files=%s" %
                        (filename,
                         time.time() - openfiles.last_scan_time,
                         openfiles.files))

        f = os.fdopen(handle)
        f.close()
        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

        os.unlink(filename)
        openfiles.scan()
        self.assertFalse(openfiles.is_open(filename))

    def test_open_files_lsof(self):
        self.assertEqual(list(open_files_lsof(lambda:
                                              'n/bar/foo\nn/foo/bar\nnoise'
                                              )), ['/bar/foo', '/foo/bar'])


def suite():
    return unittest.makeSuite(FileUtilitiesTestCase)


if __name__ == '__main__':
    unittest.main()
