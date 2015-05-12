# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
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
Test case for module FileUtilities
"""


import locale
import platform
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.append('.')
from bleachbit.FileUtilities import *
from bleachbit.Options import options

try:
    import json
except:
    import simplejson as json


def test_ini_helper(self, execute):
    """Used to test .ini cleaning in TestAction and in TestFileUtilities"""

    # create test file
    (fd, filename) = tempfile.mkstemp('bleachbit-test-ini')
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
    (fd, filename) = tempfile.mkstemp('bleachbit-test-json')
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


class FileUtilitiesTestCase(unittest.TestCase):

    """Test case for module FileUtilities"""

    def __touch(self, filename):
        """Create an empty file"""
        open(filename, "w")

    def test_bytes_to_human(self):
        """Unit test for class bytes_to_human"""

        if 'posix' == os.name:
            old_locale = locale.getlocale(locale.LC_NUMERIC)
            locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')

        # test one-way conversion for predefined values
        tests = [("-1B", bytes_to_human(-1)),
                 ("0", bytes_to_human(0)),
                 ("1B", bytes_to_human(1)),
                 ("1kB", bytes_to_human(1000)),
                 ("1.1kB", bytes_to_human(1110)),
                 ("1MB", bytes_to_human(1000 ** 2)),
                 ("1.3MB", bytes_to_human(1289748)),
                 ("1GB", bytes_to_human(1000 ** 3)),
                 ("1.32GB", bytes_to_human(1320702444)),
                 ("1TB", bytes_to_human(1000 ** 4))]

        for test in tests:
            self.assertEqual(test[0], test[1])

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
                print "Warning: exception when setlocale to de_DE.utf8"
            else:
                self.assertEqual("1,01GB", bytes_to_human(1000 ** 3 + 5812389))

        # clean up
        if 'posix' == os.name:
            locale.setlocale(locale.LC_NUMERIC, old_locale)

    def test_children_in_directory(self):
        """Unit test for function children_in_directory()"""

        # test an existing directory that usually exists
        dirname = os.path.expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assert_(isinstance(filename, str))
            self.assert_(os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assert_(isinstance(filename, str))
            self.assert_(os.path.isabs(filename))
            self.assert_(not os.path.isdir(filename))

        # test a constructed file in a constructed directory
        dirname = tempfile.mkdtemp()
        filename = os.path.join(dirname, "somefile")
        self.__touch(filename)
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
        print "testing test_clean_ini() with shred = False"
        options.set('shred', False, commit=False)
        test_ini_helper(self, clean_ini)

        print "testing test_clean_ini() with shred = True"
        options.set('shred', True, commit=False)
        test_ini_helper(self, clean_ini)

    def test_clean_json(self):
        """Unit test for clean_json()"""
        print "testing test_clean_json() with shred = False"
        options.set('shred', False, commit=False)
        test_json_helper(self, clean_json)

        print "testing test_clean_json() with shred = True"
        options.set('shred', True, commit=False)
        test_json_helper(self, clean_json)

    def test_delete(self):
        """Unit test for method delete()"""
        print "testing delete() with shred = False"
        self.delete_helper(shred=False)
        print "testing delete() with shred = True"
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

        tests = [('.suffix', 'prefix'),  # simple
                 ("x".zfill(100), ".y".zfill(50)),  # long
                 (" ", " "),  # space
                 ("'", "'"),  # quotation mark
                 ("~`!@#$%^&()-_+=", "x"),  # non-alphanumeric characters
                 ("[]{};',.", "x"),  # non-alphanumeric characters
                 (u'abcd', u'efgh'),  # simple Unicode
                 (u'J\xf8rgen', 'Scandinavian'),
                 (u'\u2014', 'em-dash'), #  LP#1454030
                 (hebrew, hebrew),
                 (katanana, katanana),
                 (umlauts, umlauts)]
        if 'posix' == os.name:
            # Windows doesn't allow these characters but Unix systems do
            tests.append(('"', '*'))
            tests.append(('\t', '\\'))
            tests.append((':?', '<>|'))
        for test in tests:
            # delete a file
            (fd, filename) = tempfile.mkstemp(
                prefix='bleachbit-delete-file' + test[0], suffix=test[1])
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
                suffix='bleachbit-delete-dir' + test[0], prefix=test[1])
            self.assert_(os.path.exists(dirname))
            delete(dirname, shred)
            self.assert_(not os.path.exists(dirname))

        def symlink_helper(link_fn):

            if 'nt' == os.name:
                from win32com.shell import shell
                if not shell.IsUserAnAdmin():
                    print 'WARNING: skipping symlink test because of insufficient privileges'
                    return

            # make regular file
            (fd, srcname) = tempfile.mkstemp('bbregular')
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
            (fd, srcname) = tempfile.mkstemp('bbregular')
            os.close(fd)
            self.assert_(os.path.lexists(srcname))
            link_fn(srcname, linkname)
            self.assert_(os.path.lexists(linkname))
            self.assert_(os.path.exists(linkname))

            # delete regular file first
            delete(srcname, shred)
            self.assert_(not os.path.exists(srcname))

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
                    print 'CreateSymbolicLinkA(%s, %s)' % (linkname, src)
                    print 'CreateSymolicLinkA() failed, error = %s' % ctypes.FormatError()
                    self.assertNotEqual(rc, 0)
            symlink_helper(win_symlink)

        # below this point, only posix
        if 'nt' == os.name:
            return

        # test file with mode 0444/-r--r--r--
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        os.chmod(filename, 0444)
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test symlink
        symlink_helper(os.symlink)

        # test fifo
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assert_(os.path.exists(filename))
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test directory
        path = tempfile.mkdtemp()
        self.assert_(os.path.exists(path))
        delete(path, shred)
        self.assert_(not os.path.exists(path))

    def test_ego_owner(self):
        """Unit test for ego_owner()"""
        if 'nt' == os.name:
            return
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

    def test_free_space(self):
        """Unit test for free_space()"""
        home = os.path.expanduser("~")
        result = free_space(home)
        self.assertNotEqual(result, None)
        self.assert_(result > -1)
        self.assert_(isinstance(result, (int, long)))

    def test_getsize(self):
        """Unit test for method getsize()"""
        def test_getsize_helper(filename):
            (handle, filename) = tempfile.mkstemp(filename)
            os.write(handle, "abcdefghij" * 12345)
            os.close(handle)

            if 'nt' == os.name:
                self.assertEqual(getsize(filename), 10 * 12345)
                # Expand the directory names, which are in the short format,
                # to test the case where the full path (including the directory)
                # is longer than 255 characters.
                import win32api
                lname = win32api.GetLongPathNameW(filename)
                self.assertEqual(getsize(lname), 10 * 12345)
            if 'posix' == os.name:
                output = subprocess.Popen(
                    ["du", "-h", filename], stdout=subprocess.PIPE).communicate()[0]
                output = output.replace("\n", "")
                du_size = output.split("\t")[0] + "B"
                print "output = '%s', size='%s'" % (output, du_size)
                du_bytes = human_to_bytes(du_size, 'du')
                print output, du_size, du_bytes
                self.assertEqual(getsize(filename), du_bytes)
            delete(filename)

        # create regular file
        test_getsize_helper('bleachbit-test-regular')

        # special characters
        test_getsize_helper(u'bleachbit-test-special-characters-∺ ∯')

        # em-dash (LP1454030)
        test_getsize_helper(u'bleachbit-test-em-dash-\u2014')

        # long
        test_getsize_helper(u'bleachbit-test-long' + 'x' * 200)

        if 'nt' == os.name:
            # the following tests do not apply to Windows
            return

        # create a symlink
        (handle, filename) = tempfile.mkstemp('bleachbit-test-symlink')
        os.write(handle, "abcdefghij" * 12345)
        os.close(handle)
        linkname = '/tmp/bleachbitsymlinktest'
        if os.path.lexists(linkname):
            delete(linkname)
        os.symlink(filename, linkname)
        self.assert_(getsize(linkname) < 8192, "Symlink size is %d" %
                     getsize(filename))
        delete(filename)

        # create sparse file
        (handle, filename) = tempfile.mkstemp("bleachbit-test-sparse")
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
            self.assert_(os.path.isdir(path))

    def test_listdir(self):
        """Unit test for listdir()"""
        for pathname in listdir(('/tmp', '~/.config/')):
            self.assert_(os.path.lexists(pathname),
                         "does not exist: %s" % pathname)

    def test_same_partition(self):
        """Unit test for same_partition()"""
        home = os.path.expanduser('~')
        self.assertTrue(same_partition(home, home))
        if 'posix' == os.name:
            self.assertFalse(same_partition(home, '/proc'))
        if 'nt' == os.name:
            home_drive = os.path.splitdrive(home)[0]
            from bleachbit.Windows import get_fixed_drives
            for drive in get_fixed_drives():
                this_drive = os.path.splitdrive(drive)[0]
                self.assertEqual(
                    same_partition(home, drive), home_drive == this_drive)

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

            # drives letters have the seperator at the end while most paths
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

    def test_wipe_contents(self):
        """Unit test for wipe_delete()"""

        # create test file
        (handle, filename) = tempfile.mkstemp("bleachbit-test-wipe")
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
        (handle, filename) = tempfile.mkstemp("bleachbit-test-wipe" + "0" * 50)
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

        dir0 = tempfile.mkdtemp(suffix="0" * dir0len)
        self.assert_(os.path.exists(dir0))

        dir1 = tempfile.mkdtemp(suffix="1" * dir1len, dir=dir0)
        self.assert_(os.path.exists(dir1))

        (handle, filename) = tempfile.mkstemp(
            dir=dir1, suffix="2" * filelen)
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
            print 'warning: skipping long test test_wipe_path() because environment variable ALLTESTS not set'
            return
        pathname = tempfile.gettempdir()
        for ret in wipe_path(pathname):
            # no idle handler
            pass

    def test_vacuum_sqlite3(self):
        """Unit test for method vacuum_sqlite3()"""

        try:
            import sqlite3
        except ImportError, e:
            if sys.version_info[0] == 2 and sys.version_info[1] < 5:
                print "Warning: Skipping test_vacuum_sqlite3() on old Python"
                return
            else:
                raise e

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

    def test_OpenFiles(self):
        """Unit test for class OpenFiles"""
        if 'nt' == os.name:
            return

        (handle, filename) = tempfile.mkstemp('bleachbit-test-open-files')
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


def suite():
    return unittest.makeSuite(FileUtilitiesTestCase)


if __name__ == '__main__':
    unittest.main()
