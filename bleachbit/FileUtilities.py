# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2008 Andrew Ziem
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



import ConfigParser
import datetime
import glob
import os
import os.path
import stat
import sys
import subprocess

if not "iglob" in dir(glob):
    glob.iglob = glob.glob

class OpenFiles:
    """Cached way to determine whether a file is open by active process"""
    def __init__(self):
        self.last_scan_time = None
        self.files = []

    def file_qualifies(self, filename):
        """Return boolean wehether filename qualifies to enter cache (check against blacklist)"""
        return not filename.startswith("/dev") and not filename.startswith("/proc")

    def scan(self):
        """Update cache"""
        self.last_scan_time = datetime.datetime.now()
        self.files = []
        for filename in glob.iglob("/proc/*/fd/*"):
            try:
                target = os.path.realpath(filename)
            except TypeError:
                # happens, for example, when link points to '/etc/password\x00 (deleted)'
                continue
            if self.file_qualifies(target):
                self.files.append(target)

    def is_open(self, filename):
        """Return boolean whether filename is open by running process"""
        if None == self.last_scan_time or (datetime.datetime.now() - 
            self.last_scan_time).seconds > 10:
            self.scan()
        return filename in self.files


def ego_owner(filename):
    """Return whether current user owns the file"""
    return os.stat(filename).st_uid == os.getuid()


def delete_file_directory(path):
    """Delete path that is either file or directory"""
    print "debug: removing '%s'" % (path,)
    if is_file(path):
        delete_file(path)
    else:
        os.rmdir(path)


def delete_file(filename):
    """Remove a single file (enhanced for optional shredding)"""
    if False: # fixme get user setting
        args = ["shred", filename]
        ret = subprocess.check_call(args)
        if 0 != ret:
            raise Exception("shred subprocess returned non-zero error code " % (ret,))
    os.remove(filename)


def delete_files(files):
    """Remove a list of files/directories and return (bytes deleted, number of files/directories deleted)"""
    n_files = 0 # number of files
    bytes = 0
    for filename in files:
        bytes += size_of_file(filename)
        n_files += 1
        delete_file(filename)
    return (bytes, n_files)


def list_children_in_directory(directory):
    """List subdirectories and files in directory"""
    ret = []
    for root, dirs, files in os.walk(directory, topdown=False): 
        for name in files:
            ret.append(os.path.join(root, name))
        for dir_ in dirs:
            ret.append(os.path.join(root, dir_))
    return ret


def children_in_directory(top, list_directories = False):
    """Iterate files and, optionally, subdirectories in directory"""
    for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def list_files_in_directory(dirname):
    """Return a list of each file in dirname"""
    ret = []
    for root, dirs, files in os.walk(dirname):
        for name in files:
            ret.append(os.path.join(root, name))
    return ret


def bytes_to_human(bytes):
    """Display a file size in human terms (megabytes, etc.)"""
    if bytes >= 1024*1024*1024*1024:
        return str(bytes/(1024*1024*1024*1024)) + "TB"
    if bytes >= 1024*1024*1024:
        return str(bytes/(1024*1024*1024)) + "GB"
    if bytes >= 1024*1024:
        return str(bytes/(1024*1024)) + "MB"
    if bytes >= 1024:
        return str(bytes/1024) + "KB"
    return str(bytes) + "B"

def list_files_with_size(files):
    """Given a list of files, return string each one and its size"""
    ret = ""
    total_size = 0
    for filename in files:
        try:
            size = os.stat(filename).st_size
            ret += bytes_to_human(size) + " " + filename + "\n"
            total_size += size
        except:
            ret += str(sys.exc_info()[1]) + " " + filename + "\n"
    ret += bytes_to_human(total_size) + " total"
    return ret


def size_of_file(filename):
    """Return the size of a file or directory"""
    return os.stat(filename).st_size


def sum_size_of_files(files):
    """Given a list of files, return the size in bytes of all the files"""
    bytes = 0
    for filename in files:
        bytes += size_of_file(filename)
    return bytes


def is_file(filename):
    """Return boolean whether f is a file"""
    mode = os.lstat(filename).st_mode
    return stat.S_ISREG(mode)


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    for dirname in os.getenv('PATH').split(":"):
        if os.path.exists(os.path.join(dirname, filename)):
            return True
    return False

def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = ConfigParser.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        print "debug: is_broken_xdg_menu: missing required section 'Desktop Entry': '%s'" % (pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        print "debug: is_broken_xdg_menu: missing required option 'Type': '%s'" % (pathname)
        return True
    type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == type:
        if not config.has_option('Desktop Entry', 'URL') and \
            not config.has_option('Desktop Entry', 'URL[$e]'):
            print "debug: is_broken_xdg_menu: missing required option 'URL': '%s'" % (pathname)
            return True
        return False
    if 'application' != type:
        print "Warning: unhandled type '%s': file '%s'" % (type, pathname)
        return False
    if not config.has_option('Desktop Entry', 'Exec'):
        print "debug: is_broken_xdg_menu: missing required option 'Exec': '%s'" % (pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if os.path.isabs(exe):
        if not os.path.exists(exe):
            print "debug: is_broken_xdg_menu: exe '%s' does not exist '%s'" % (exe, pathname)
            return True
    else:
        if not exists_in_path(exe):
            print "debug: is_broken_xdg_menu: exe '%s' does not exist in path: '%s'" % (exe, pathname)
            return True
    return False


openfiles = OpenFiles()



import unittest

class TestFileUtilities(unittest.TestCase):
    """Unit test for module FileUtilities"""

    def test_list_files_in_directory(self):
        """Unit test for function list_files_in_directory()"""
        home = os.path.expanduser("~/Desktop")
        files = list_files_in_directory(home)
        for filename in files:
            self.assert_(is_file(filename))


    def test_sum_size_of_files(self):
        """Unit test for function sum_size_of_files()"""
        home = os.path.expanduser("~/Desktop")
        files = list_files_in_directory(home)
        size = sum_size_of_files(files)
        self.assert_(size >= 0)


    def test_children_in_directory(self): 
        """Unit test for function children_in_directory()"""
        dirname = os.path.expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assert_ (type(filename) is str)
        for filename in children_in_directory(dirname, False):
            self.assert_ (type(filename) is str)


    def test_bytes_to_human(self):
        """Unit test for class bytes_to_human"""
        tests = [ ("1B", bytes_to_human(1)),
                  ("1KB", bytes_to_human(1024)),
                  ("1MB", bytes_to_human(1024*1024)),
                  ("1GB", bytes_to_human(1024*1024*1024)), 
                  ("1TB", bytes_to_human(1024*1024*1024*1024)) ]

        for test in tests:
            self.assertEqual(test[0], test[1])

    def test_is_broken_xdg_desktop(self):
        """Unit test for is_broken_xdg_desktop()"""
        menu_dirs = [ '/usr/share/applications', \
            '/usr/share/autostart', \
            '/usr/share/gnome/autostart', \
            '/usr/share/gnome/apps', \
            '/usr/share/applnk-redhat/', \
            '/usr/local/share/applications/' ]
        for dirname in menu_dirs:
            for filename in filter(lambda fn: fn.endswith(".desktop"), \
                children_in_directory(dirname, False)):
                    self.assert_(type(is_broken_xdg_desktop(filename) is bool))


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

