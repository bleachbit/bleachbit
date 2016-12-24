#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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
import sys
import unittest

import TestAction
import TestCLI
import TestCleaner
import TestCleanerML
import TestCommand
import TestCommon
import TestDiagnostic
import TestDeepScan
import TestFileUtilities
import TestGeneral
import TestMemory
import TestOptions
import TestRecognizeCleanerML
import TestSpecial
import TestUpdate
import TestWorker


suites = [TestAction.suite(),
          TestCleanerML.suite(),
          TestCleaner.suite(),
          TestCLI.suite(),
          TestCommand.suite(),
          TestCommon.suite(),
          TestDeepScan.suite(),
          TestDiagnostic.suite(),
          TestFileUtilities.suite(),
          TestGeneral.suite(),
          TestMemory.suite(),
          TestOptions.suite(),
          TestRecognizeCleanerML.suite(),
          TestSpecial.suite(),
          TestUpdate.suite(),
          TestWorker.suite()
          ]

if 'posix' == os.name and sys.version_info >= (2,7,0):
    import TestUnix
    suites.append(TestUnix.suite())

if 'nt' == os.name:
    import TestWinapp
    import TestWindows
    suites.append(TestWinapp.suite())
    suites.append(TestWindows.suite())


def suite():
    """Combine all the suites into one large suite"""
    suite_ = unittest.TestSuite()
    map(suite_.addTest, suites)
    return suite_

if __name__ == '__main__':
    success = unittest.TextTestRunner(verbosity=2).run(suite()).wasSuccessful()
    sys.exit(success == False)
