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
import shlex
import stat
import subprocess

HAVE_GNOME_VFS = True
try:
    import gnomevfs
except:
    try:
        # this is the deprecated name
        import gnome.vfs
    except:
        HAVE_GNOME_VFS = False
    else:
        gnomevfs = gnome.vfs

if not "iglob" in dir(glob):
    glob.iglob = glob.glob


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
    if bytes >= 1024*1024*1024*1024:
        return str(bytes/(1024*1024*1024*1024)) + "TB"
    if bytes >= 1024*1024*1024:
        return str(bytes/(1024*1024*1024)) + "GB"
    if bytes >= 1024*1024:
        return str(bytes/(1024*1024)) + "MB"
    if bytes >= 1024:
        return str(bytes/1024) + "KB"
    return str(bytes) + "B"


def children_in_directory(top, list_directories = False):
    """Iterate files and, optionally, subdirectories in directory"""
    for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def delete_file(filename):
    """Remove a single file (enhanced for optional shredding)"""
    if False: # fixme get user setting
        args = ["shred", filename]
        ret = subprocess.check_call(args)
        if 0 != ret:
            raise Exception("shred subprocess returned non-zero error code " % (ret,))
    os.remove(filename)


def delete_file_directory(path):
    """Delete path that is either file or directory"""
    print "info: removing '%s'" % (path,)
    if os.path.isdir(path):
        os.rmdir(path)
    else:
        delete_file(path)


def ego_owner(filename):
    """Return whether current user owns the file"""
    return os.stat(filename).st_uid == os.getuid()


def exists_in_path(filename):
    """Returns boolean whether the filename exists in the path"""
    for dirname in os.getenv('PATH').split(":"):
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


def __is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns boolean whether application deskop entry file is broken"""
    if not config.has_option('Desktop Entry', 'Exec'):
        print "info: is_broken_xdg_menu: missing required option 'Exec': '%s'" \
            % (desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not exe_exists(exe):
        print "info: is_broken_xdg_menu: executable '%s' does not exist '%s'" \
            % (exe, desktop_pathname)
        return True
    if 'env' == exe:
        # Wine v1.0 creates .desktop files like this
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program Files\\foo\\foo.exe"
        execs = shlex.split(config.get('Desktop Entry', 'Exec'))
        wineprefix = None
        del(execs[0])
        while True:
            if 0 <= execs[0].find("="):
                (name, value) = execs[0].split("=")
                if 'WINEPREFIX' == name:
                    wineprefix = value
                del(execs[0])
            else:
                break
        if not exe_exists(execs[0]):
            print "info: is_broken_xdg_menu: executable '%s' does not exist '%s'" % (execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                print "info: is_broken_xdg_menu: Windows executable '%s' does not exist '%s'" % (windows_exe, desktop_pathname)
                return True
    return False


def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = ConfigParser.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        print "info: is_broken_xdg_menu: missing required section 'Desktop Entry': '%s'" % (pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        print "info: is_broken_xdg_menu: missing required option 'Type': '%s'" % (pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
            not config.has_option('Desktop Entry', 'URL[$e]'):
            print "info: is_broken_xdg_menu: missing required option 'URL': '%s'" % (pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            print "info: is_broken_xdg_menu: missing required option 'MimeType': '%s'" % (pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if HAVE_GNOME_VFS and 0 == len(gnomevfs.mime_get_all_applications(mimetype)):
            print "info: is_broken_xdg_menu: MimeType '%s' not registered '%s'" % (mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        print "Warning: unhandled type '%s': file '%s'" % (file_type, pathname)
        return False
    if __is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":", \
        "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\","/")
    return os.path.join(wineprefix, windows_pathname)


openfiles = OpenFiles()


import unittest

class TestFileUtilities(unittest.TestCase):
    """Unit test for module FileUtilities"""

    def __touch(self, filename):
        """Create an empty file"""
        f = open(filename, "w")


    def test_bytes_to_human(self):
        """Unit test for class bytes_to_human"""
        tests = [ ("1B", bytes_to_human(1)),
                  ("1KB", bytes_to_human(1024)),
                  ("1MB", bytes_to_human(1024*1024)),
                  ("1GB", bytes_to_human(1024*1024*1024)), 
                  ("1TB", bytes_to_human(1024*1024*1024*1024)) ]

        for test in tests:
            self.assertEqual(test[0], test[1])


    def test_children_in_directory(self): 
        """Unit test for function children_in_directory()"""
        import tempfile

        dirname = os.path.expanduser("~/.config")
        for filename in children_in_directory(dirname, True):
            self.assert_ (type(filename) is str)
            self.assert_ (os.path.isabs(filename))
        for filename in children_in_directory(dirname, False):
            self.assert_ (type(filename) is str)
            self.assert_ (os.path.isabs(filename))
            self.assert_ (not os.path.isdir(filename))

        dirname = tempfile.mkdtemp()
        foo = os.path.join(dirname, "foo")
        self.__touch(foo)
        for filename in children_in_directory(dirname, True):
            self.assert_ (filename, foo)
        for filename in children_in_directory(dirname, False):
            self.assert_ (filename, foo)
        os.remove(foo)

        foobar = os.path.join(dirname, "foobar")
        os.mkdir(foobar)
        for filename in children_in_directory(dirname, True):
            self.assert_ (filename, foobar)
        for filename in children_in_directory(dirname, False):
            self.assert_ (False)
        os.rmdir(foobar)

        os.rmdir(dirname)



    def test_exe_exists(self):
        """Unit test for exe_exists()"""
        tests = [ ("/bin/sh", True), \
            ("sh", True), \
            ("doesnotexist", False), \
            ("/bin/doesnotexist", False) ]
        for test in tests:
            self.assertEqual(exe_exists(test[0]), test[1])


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
            for filename in filter(lambda fn: fn.endswith(".desktop"), \
                children_in_directory(dirname, False)):
                self.assert_(type(is_broken_xdg_desktop(filename) is bool))


    def test_wine_to_linux_path(self):
        """Unit test for wine_to_linux_path()"""
        tests = [ ("/home/foo/.wine", \
            "C:\\Program Files\\NSIS\\NSIS.exe", \
            "/home/foo/.wine/drive_c/Program Files/NSIS/NSIS.exe") ]
        for test in tests:
            self.assertEqual(wine_to_linux_path(test[0], test[1]), test[2])


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

