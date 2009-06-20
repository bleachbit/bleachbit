# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
File-related utilities
"""


import datetime
import glob
import locale
import os
import os.path
import re
import stat
import subprocess
import sys



if not "iglob" in dir(glob):
    glob.iglob = glob.glob

from Options import options


class OpenFiles:
    """Cached way to determine whether a file is open by active process"""
    def __init__(self):
        self.last_scan_time = None
        self.files = []

    def file_qualifies(self, filename):
        """Return boolean wehether filename qualifies to enter cache (check \
        against blacklist)"""
        return not filename.startswith("/dev") and \
            not filename.startswith("/proc")

    def scan(self):
        """Update cache"""
        self.last_scan_time = datetime.datetime.now()
        self.files = []
        for filename in glob.iglob("/proc/*/fd/*"):
            try:
                target = os.path.realpath(filename)
            except TypeError:
                # happens, for example, when link points to
                # '/etc/password\x00 (deleted)'
                continue
            if self.file_qualifies(target):
                self.files.append(target)

    def is_open(self, filename):
        """Return boolean whether filename is open by running process"""
        if None == self.last_scan_time or (datetime.datetime.now() - 
            self.last_scan_time).seconds > 10:
            self.scan()
        return filename in self.files


def bytes_to_human(bytes):
    """Display a file size in human terms (megabytes, etc.)"""

    storage_multipliers = { 1024**5 : 'PB', 1024**4 : 'TB', \
        1024**3 : 'GB', 1024**2: 'MB', 1024: 'KB', 1 : 'B' }

    if 0 == bytes:
        return "0"

    if bytes >= 1024**3:
        decimals = 2
    elif bytes >= 1024:
        decimals = 1
    else:
        decimals = 0

    for key in sorted(storage_multipliers.keys(), reverse = True):
        if bytes >= key:
            abbrev = (1.0 * bytes) / key
            suf = storage_multipliers[key]
            format = "%." + str(decimals) + "f" + suf
            if hasattr(locale, 'format_string'):
                return locale.format_string(format, abbrev)
            else:
                return locale.format(format, abbrev)

    if bytes < 0:
        return "-" + bytes_to_human(abs(bytes))


def children_in_directory(top, list_directories = False):
    """Iterate files and, optionally, subdirectories in directory"""
    if type(top) is tuple:
        for top_ in top:
            for pathname in children_in_directory(top_, list_directories):
                yield pathname
        return
    for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def delete(path, shred = False):
    """Delete path that is either file, directory, link or FIFO"""
    print "info: removing '%s'" % (path,)
    mode = os.lstat(path)[stat.ST_MODE]
    if stat.S_ISFIFO(mode) or stat.S_ISLNK(mode):
        os.remove(path)
    elif stat.S_ISDIR(mode):
        os.rmdir(path)
    elif stat.S_ISREG(mode):
        if options.get('shred') or shred:
            wipe_contents(path)
        os.remove(path)
    else:
        raise Exception("Unsupported special file type")


def ego_owner(filename):
    """Return whether current user owns the file"""
    return os.lstat(filename).st_uid == os.getuid()


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    delimiter = ':'
    if sys.platform == 'win32':
        delimiter = ';'
    for dirname in os.getenv('PATH').split(delimiter):
        if os.path.exists(os.path.join(dirname, filename)):
            return True
    return False


def exe_exists(pathname):
    """Returns boolean whether executable exists"""
    if os.path.isabs(pathname):
        if not os.path.exists(pathname):
            return False
    else:
        if not exists_in_path(pathname):
            return False
    return True


def execute_sqlite3(path, cmds):
    """Execute 'cmds' on SQLite database 'path'"""
    try:
        import sqlite3
    except ImportError, exc:
        import sys
        if sys.version_info[0] == 2 and sys.version_info[1] < 5:
            raise RuntimeError(_("Cannot import Python module sqlite3: Python 2.5 or later is required."))
        else:
            raise exc
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    for cmd in cmds.split(';'):
        try:
            cursor.execute(cmd)
        except sqlite3.OperationalError, exc:
            raise sqlite3.OperationalError('%s: %s' % (exc, path))
    cursor.close()
    conn.commit()
    conn.close()


def expand_glob_join(pathname1, pathname2):
    """Join pathname1 and pathname1, expand pathname, glob, and return as list"""
    ret = []
    pathname3 = os.path.expanduser(os.path.expandvars(os.path.join(pathname1, pathname2)))
    for pathname4 in glob.iglob(pathname3):
       ret.append(pathname4)
    return ret


def getsize(path):
    """Return the actual file size considering spare files
       and symlinks"""
    if sys.platform == 'linux2':
        __stat = os.lstat(path)
        return __stat.st_blocks * 512
    return os.path.getsize(path)


def getsizedir(path):
    """Return the size of the contents of a directory"""
    total_bytes = 0
    for node in children_in_directory(path, list_directories = False):
        total_bytes += getsize(node)
    return total_bytes


def globex(pathname, regex):
    """Yield a list of files with pathname and filter by regex"""
    if type(pathname) is tuple:
        for singleglob in pathname:
            for path in globex(singleglob, regex):
                yield path
    else:
        for path in glob.iglob(pathname):
            if re.search(regex, path):
                yield path


def human_to_bytes(string):
    """Convert a string like 10.2GB into bytes"""
    multiplier = { 'B' : 1, 'KB': 1024, 'MB': 1024**2, \
        'GB': 1024**3, 'TB': 1024**4 }
    matches = re.findall("^([0-9]*)(\.[0-9]{1,2})?([KMGT]{0,1}B)$", string)
    if 2 > len(matches[0]):
        raise ValueError("Invalid input for '%s'" % (string))
    return int(float(matches[0][0]+matches[0][1]) * multiplier[matches[0][2]])


def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if type(directory) is tuple:
        for dir in directory:
            for pathname in listdir(dir):
                yield pathname
        return
    dir = os.path.expanduser(directory)
    if not os.path.lexists(dir):
        return
    for filename in os.listdir(dir):
        yield os.path.join(dir, filename)


def wipe_contents(path):
    """Wipe files contents

    http://en.wikipedia.org/wiki/Data_remanence
    2006 NIST Special Publication 800-88 (p. 7): "Studies have
    shown that most of today's media can be effectively cleared
    by one overwrite"
    """
    size = getsize(path)
    try:
        f = open(path, 'wb')
    except IOError, e:
        if 13 == e.errno: # permission denied
            os.chmod(path, 0200) # user write only
            f = open(path, 'wb')
        else:
            raise
    blanks =  chr(0) * 4096
    while size > 0:
        f.write(blanks)
        size -= 4096
    f.flush()
    f.truncate(0)
    f.flush()
    f.close()


def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')


openfiles = OpenFiles()


import unittest

class TestFileUtilities(unittest.TestCase):
    """Unit test for module FileUtilities"""

    def __touch(self, filename):
        """Create an empty file"""
        f = open(filename, "w")


    def test_bytes_to_human(self):
        """Unit test for class bytes_to_human"""

        if sys.platform == 'linux2':
            old_locale = locale.getlocale(locale.LC_NUMERIC)
            locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')

        # test one-way conversion for predefined values
        tests = [ ("-1B", bytes_to_human(-1)),
                  ("0", bytes_to_human(0)),
                  ("1B", bytes_to_human(1)),
                  ("1.0KB", bytes_to_human(1024)),
                  ("1.0MB", bytes_to_human(1024**2)),
                  ("1.00GB", bytes_to_human(1024**3)),
                  ("1.00TB", bytes_to_human(1024**4)) ]

        for test in tests:
            self.assertEqual(test[0], test[1])

        # test roundtrip conversion for random values
        import random
        for n in range(0, 1000):
            bytes = random.randrange(0, 1024**4)
            human = bytes_to_human(bytes)
            bytes2 = human_to_bytes(human)
            error =  abs(float(bytes2 - bytes) / bytes)
            self.assert_(abs(error) < 0.01, \
                "%d (%s) is %.2f%% different than %d" % \
                (bytes, human, error * 100, bytes2))

        # test localization
        if hasattr(locale, 'format_string'):
            try:
                locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
            except:
                print "Warning: exception when setlocale to de_DE.utf8"
            else:
                self.assertEqual("1,00TB", bytes_to_human(1024**4))

        # clean up
        if sys.platform == 'linux2':
            locale.setlocale(locale.LC_NUMERIC, old_locale)


    def test_children_in_directory(self): 
        """Unit test for function children_in_directory()"""
        import tempfile

        # test an existing directory that usually exists
        dirname = os.path.expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assert_ (type(filename) is str)
            self.assert_ (os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assert_ (type(filename) is str)
            self.assert_ (os.path.isabs(filename))
            self.assert_ (not os.path.isdir(filename))

        # test a constructed file in a constructed directory
        dirname = tempfile.mkdtemp()
        filename = os.path.join(dirname, "somefile")
        self.__touch(filename)
        for loopfilename in children_in_directory(dirname, True):
            self.assertEqual (loopfilename, filename)
        for loopfilename in children_in_directory(dirname, False):
            self.assertEqual (loopfilename, filename)
        os.remove(filename)

        # test subdirectory
        subdirname = os.path.join(dirname, "subdir")
        os.mkdir(subdirname)
        for filename in children_in_directory(dirname, True):
            self.assertEqual (filename, subdirname)
        for filename in children_in_directory(dirname, False):
            self.assert_ (False)
        os.rmdir(subdirname)

        os.rmdir(dirname)


    def test_delete(self):
        """Unit test for method delete()"""
        print "testing delete() with shred = False"
        self.delete_helper(shred = False)
        print "testing delete() with shred = True"
        self.delete_helper(shred = True)


    def delete_helper(self, shred):
        """Called by test_delete() with shred = False and = True"""

        import tempfile

        hebrew = "עִבְרִית"
        katanana = "アメリカ"
        umlauts = "ÄäǞǟËëḦḧÏïḮḯÖöȪȫṎṏT̈ẗÜüǕǖǗǘǙǚǛǜṲṳṺṻẄẅẌẍŸÿ"

        tests = [ ('.suffix', 'prefix'), # simple
                  ("\t", "\t"), # tab
                  ("~`!@#$%^&*()-_+=", "x"), # non-alphanumeric characters
                  ("[]{};':,.?<>\|", "x"), # non-alphanumeric characters
                  ("x".zfill(100), ".y".zfill(100)), # long
                  (" ", " "), # space
                  ('"', "'"), # quotation marks
                  (u'a', u'a'), # simple unicode
                  (hebrew, hebrew),
                  (katanana, katanana),
                  (umlauts, umlauts) ]
        for test in tests:
            (fd, filename) = tempfile.mkstemp(test[0], 'bleachbit-test' + test[1])
            self.assert_(os.path.exists(filename))
            for x in range(0, 4096/5):
                bytes = os.write(fd, "top secret")
                self.assertEqual(bytes, 10)
            os.close(fd)
            self.assert_(os.path.exists(filename))
            delete(filename, shred)
            self.assert_(not os.path.exists(filename))

        if sys.platform == 'win32':
            return

        # test file with mode 0444/-r--r--r--
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        os.chmod(filename, 0444)
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test symlink
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        self.assert_(os.path.exists(filename))
        linkname = '/tmp/bleachbitsymlinktest'
        if os.path.lexists(linkname):
            delete(linkname, shred)
        self.assert_(not os.path.lexists(linkname))
        os.symlink(filename, linkname)
        self.assert_(os.path.lexists(linkname))
        delete(linkname, shred)
        self.assert_(os.path.exists(filename))
        self.assert_(not os.path.lexists(linkname))
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))

        # test broken symlink
        os.symlink(filename, linkname)
        self.assert_(os.path.lexists(linkname))
        self.assert_(not os.path.exists(linkname))
        delete(linkname, shred)
        self.assert_(not os.path.exists(linkname))

        # test fifo
        args = ["mkfifo", filename]
        ret = subprocess.call(args)
        self.assertEqual(ret, 0)
        self.assert_(os.path.exists(filename))
        delete(filename, shred)
        self.assert_(not os.path.exists(filename))


    def test_ego_owner(self):
        """Unit test for ego_owner()"""
        self.assertEqual(ego_owner('/bin/ls'), os.getuid() == 0)


    def test_exists_in_path(self):
        """Unit test for exists_in_path()"""
        filename = 'ls'
        if sys.platform == 'win32':
            filename = 'cmd.exe'
        self.assert_(exists_in_path(filename))


    def test_exe_exists(self):
        """Unit test for exe_exists()"""
        tests = [ ("/bin/sh", True), \
            ("sh", True), \
            ("doesnotexist", False), \
            ("/bin/doesnotexist", False) ]
        if sys.platform == 'win32':
            tests = [ ('c:\\windows\\system32\\cmd.exe', True), \
                      ('cmd.exe', True),
                      ('doesnotexist', False),
                      ('c:\\windows\\doesnotexist.exe', False) ]
        for test in tests:
            self.assertEqual(exe_exists(test[0]), test[1])


    def test_expand_glob_join(self):
        if sys.platform == 'linux2':
            expand_glob_join('/bin', '*sh')
        if sys.platform == 'win32':
            expand_glob_join('c:\windows', '*.exe')


    def test_getsize(self):
        """Unit test for method getsize()"""
        import tempfile

        # create regular file
        (handle, filename) = tempfile.mkstemp("regulartest")
        os.write(handle, "abcdefghij" * 12345)
        os.close(handle)

        if sys.platform == 'win32':
            self.assertEqual(getsize(filename), 10 * 12345)
            return

        output = subprocess.Popen(["du", "-h", filename], stdout=subprocess.PIPE).communicate()[0]
        output = output.replace("\n", "")
        du_size = output.split("\t")[0] + "B"
        print "output = '%s', size='%s'" % (output, du_size)
        du_bytes = human_to_bytes(du_size)
        print output, du_size, du_bytes
        self.assertEqual(getsize(filename), du_bytes)

        # create a symlink
        linkname = '/tmp/bleachbitsymlinktest'
        os.symlink(filename, linkname)
        self.assert_(getsize(linkname) < 8192, "Symlink size is %d" % getsize(filename))
        delete(filename)

        # create sparse file
        (handle, filename) = tempfile.mkstemp("sparsetest")
        os.ftruncate(handle, 1024**2)
        os.close(handle)
        self.assertEqual(getsize(filename), 0)
        delete(filename)


    def test_getsizedir(self):
        """Unit test for getsizedir()"""
        path = '/bin'
        if sys.platform == 'win32':
            path = 'c:\\windows\\system32'
        self.assert_(getsizedir(path) > 0)



    def test_globex(self):
        """Unit test for method globex()"""
        for path in globex('/bin/*', '/ls$'):
            self.assertEqual(path, '/bin/ls')


    def test_listdir(self):
        """Unit test for listdir()"""
        for pathname in listdir(('/tmp','~/.config/')):
            self.assert_(os.path.lexists(pathname), \
                "does not exist: %s" % pathname)


    def test_wipe_contents(self):
        """Unit test for wipe_delete()"""

        # create test file
        import tempfile
        (handle, filename) = tempfile.mkstemp("wipetest")
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


    def test_vacuum_sqlite3(self):
        """Unit test for method vacuum_sqlite3()"""

        try:
            import sqlite3
        except ImportError, e:
            import sys
            if sys.version_info[0] == 2 and sys.version_info[1] < 5:
                print "Warning: Skipping test_vacuum_sqlite3() on old Python"
                return
            else:
                raise e

        path = 'bleachbit.tmp.sqlite3'
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
        self.assert_( empty_size < getsize(path))
        conn.execute('delete from numbers')
        conn.commit()
        conn.close()

        vacuum_sqlite3(path)
        self.assertEqual(empty_size , getsize(path))

        delete(path)


    def test_OpenFiles(self):
        """Unit test for class OpenFiles"""
        import tempfile

        (handle, filename) = tempfile.mkstemp()
        self.assertEqual(openfiles.is_open(filename), True)

        f = os.fdopen(handle)
        f.close()
        openfiles.scan()
        self.assertEqual(openfiles.is_open(filename), False)

        os.unlink(filename)
        openfiles.scan()
        self.assertEqual(openfiles.is_open(filename), False)


if __name__ == '__main__':
    unittest.main()

