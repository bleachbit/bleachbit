# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
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
Test case for module Worker
"""



import sys
import tempfile
import unittest

sys.path.append('.')
import TestCleaner
from bleachbit import CLI
from bleachbit.Worker import *



class TestWorker(unittest.TestCase):
    """Unit test for module Worker"""

    def test_TestActionProvider(self):
        """Test Worker using Action.TestActionProvider"""
        ui = CLI.CliCallback()
        (fd, filename) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, '123')
        os.close(fd)
        self.assert_(os.path.exists(filename))
        astr = '<action command="test" path="%s"/>' % filename
        cleaner = TestCleaner.TestCleaner.action_to_cleaner(astr)
        backends['test'] = cleaner
        operations = { 'test' : [ 'option1' ] }
        w = Worker(ui, True, operations)
        run = w.run()
        while run.next():
            pass
        self.assert_(not os.path.exists(filename), \
            "Path still exists '%s'" % filename)
        self.assertEqual(w.total_special, 3)
        self.assertEqual(w.total_errors, 2)
        if 'posix' == os.name:
            self.assertEqual(w.total_bytes, 4096+10+10)
            self.assertEqual(w.total_deleted, 3)
        elif 'nt' == os.name:
            self.assertEqual(w.total_bytes, 3+3+10+10)
            self.assertEqual(w.total_deleted, 4)


    def test_multiple_options(self):
        """Test one cleaner with two options"""
        ui = CLI.CliCallback()
        (fd, filename1) = tempfile.mkstemp('bleachbit-test')
        os.close(fd)
        self.assert_(os.path.exists(filename1))
        (fd, filename2) = tempfile.mkstemp('bleachbit-test')
        os.close(fd)
        self.assert_(os.path.exists(filename2))

        astr1 = '<action command="delete" search="file" path="%s"/>' % filename1
        astr2 = '<action command="delete" search="file" path="%s"/>' % filename2
        cleaner = TestCleaner.TestCleaner.actions_to_cleaner([astr1, astr2])
        backends['test'] = cleaner
        operations = { 'test' : [ 'option1', 'option2' ] }
        w = Worker(ui, True, operations)
        run = w.run()
        while run.next():
            pass
        self.assert_(not os.path.exists(filename1), \
            "Path still exists '%s'" % filename1)
        self.assert_(not os.path.exists(filename2), \
            "Path still exists '%s'" % filename2)
        self.assertEqual(w.total_special, 0)
        self.assertEqual(w.total_errors, 0)
        self.assertEqual(w.total_deleted, 2)



if __name__ == '__main__':
    unittest.main()

