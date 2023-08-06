# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2023 Andrew Ziem
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
Run all test suites
"""

import os
import unittest
import sys
import tempfile
import shutil


if __name__ == '__main__':
    testdir = tempfile.mkdtemp(prefix='TestAll '+__name__)
    os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = testdir
    
    print("""You should use the unittest discovery, it's much nicer:
    python -m unittest discover -p Test*.py                       # run all tests
    python -m unittest tests.TestCLI                              # run only the CLI tests
    python -m unittest tests.TestCLI.CLITestCase.test_encoding    # run only a single test""")
    suite = unittest.defaultTestLoader.discover(
        os.getcwd(), pattern='Test*.py')
    success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    
    del os.environ['BLEACHBIT_TEST_OPTIONS_DIR']
    if os.path.exists(testdir):
        shutil.rmtree(testdir)
    
    sys.exit(success == False)
