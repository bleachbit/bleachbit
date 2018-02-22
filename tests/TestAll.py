#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

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
Run all test suites
"""

from __future__ import absolute_import, print_function

import os
import unittest
import sys

if __name__ == '__main__':
    print("""You should use the unittest discovery, it's much nicer:
    python2 -m unittest discover -p Test*.py                       # run all tests
    python2 -m unittest tests.TestCLI                              # run only the CLI tests
    python2 -m unittest tests.TestCLI.CLITestCase.test_encoding    # run only a single test""")
    suite = unittest.defaultTestLoader.discover(os.getcwd(), pattern='Test*.py')
    success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    sys.exit(success == False)
