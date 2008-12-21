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
                return not filename.startswith("/dev") and not filename.startswith("/proc")

        def scan(self):
                self.last_scan_time = datetime.datetime.now()
                self.files = []
                for file in glob.iglob("/proc/*/fd/*"):
                        real_name = os.path.realpath(file)
                        if self.file_qualifies(real_name):
                                self.files.append(real_name)
                                #print "debug: OpenFiles '%s'" % (real_name,)
                        
        def is_open(self, filename):
                if None == self.last_scan_time or (datetime.datetime.now() - self.last_scan_time).seconds > 10:
                        self.scan()
                return filename in self.files
                
                

def ego_owner(file):
        """Return whether current user owns the file"""
        return os.stat(file).st_uid == os.getuid()
             

def delete_file_directory(path):
        """Delete path that is either file or directory"""
        print "debug: removing '%s'" % (path,)
        if is_file(path):
            delete_file(path)
        else:
            os.rmdir(path)

def delete_file(file):
        """Remove a single file (enhanced for optional shredding)"""
        # fixme directory
        if False: # fixme get user setting
                args = ["shred", file]
                rc = subprocess.check_call(args)
                if 0 != rc:
                        raise Exception("shred subprocess returned non-zero error code " + str(rc))
        os.remove(file)

def delete_files(files):
        """Remove a list of files/directories and return (bytes deleted, number of files/directories deleted)"""
        n_files = 0 # number of files
        bytes = 0
        for file in files:
                bytes += size_of_file(file)
                n_files +1 
                delete_file(file)
        return (bytes, n_files)


def list_children_in_directory(dir):
        """List subdirectories and files in directory"""
        r=[]
        for root, dirs, files in os.walk(dir, topdown=False): 
                for name in files: 
                        r.append(os.path.join(root,name))
                for dir in dirs:
                        r.append(os.path.join(root,dir))
        return r


def children_in_directory(top, list_directories = False):
        """Iterate files and, optionally, subdirectories in directory"""
        for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
                if list_directories:
                        for dirname in dirnames:
                                yield os.path.join(dirpath, dirname)
                for filename in filenames:
                        yield os.path.join(dirpath, filename)      

def list_files_in_directory(dir):
	r=[]
	for root, dirs, files in os.walk(dir): 
		for name in files: 
			r.append(os.path.join(root,name))
	return r

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
        """Given a list of files, return each one as text with its size"""
        r = ""
        total_size = 0
	for file in files:
                try:
                        size =  os.stat(file).st_size
        		r += bytes_to_human(size) + " " + file + "\n"
                        total_size += size
                except:
                        r += str(sys.exc_info()[1]) + " " + file + "\n"
        r += bytes_to_human(total_size) + " total"
	return r

def size_of_file(file):
        """Return the size of a file or directory"""
        return os.stat(file).st_size

def sum_size_of_files(files):
	"""Given a list of files, return the size in bytes of all the files"""
	s = 0
	for file in files:
		s += size_of_file(file)
	return s

def is_file(f):
	mode = os.lstat(f).st_mode
	return stat.S_ISREG(mode)



openfiles = OpenFiles()



import unittest

class TestUtilities(unittest.TestCase):
	def test_list_files_in_directory(self):
		home = os.path.expanduser("~/Desktop")
		files = list_files_in_directory(home)
		for file in files:
			self.assert_(is_file(file))

	def test_sum_size_of_files(self):
		home = os.path.expanduser("~/Desktop")
		files = list_files_in_directory(home)
		size = sum_size_of_files(files)
		self.assert_(size >= 0)

        def test_children_in_directory(self): 
                dir = os.path.expanduser("~/.config")
                for file in children_in_directory(dir, True):
                        self.assert_ (type(file) is str)
                for file in children_in_directory(dir, False):
                        self.assert_ (type(file) is str)


        def test_bytes_to_human(self):
                tests = [ ("1B", bytes_to_human(1)),
                          ("1KB", bytes_to_human(1024)),
                          ("1MB", bytes_to_human(1024*1024)),
                          ("1GB", bytes_to_human(1024*1024*1024)), 
                          ("1TB", bytes_to_human(1024*1024*1024*1024)) ]

                for test in tests:
                        self.assertEqual(test[0], test[1])

        def test_OpenFiles(self):
                import tempfile

                openfiles = OpenFiles()
                (fd, filename) = tempfile.mkstemp()
                self.assertEqual(openfiles.is_open(filename), True)

                f = os.fdopen(fd)
                f.close()
                openfiles.scan()
                self.assertEqual(openfiles.is_open(filename), False)

                os.unlink(filename)
                openfiles.scan()
                self.assertEqual(openfiles.is_open(filename), False)


if __name__ == '__main__':
        unittest.main()

