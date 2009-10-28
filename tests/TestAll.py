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
Run all test suites
"""



import os
import unittest

import TestAction
import TestCLI
import TestCleaner
import TestCleanerML
import TestCommand
import TestDeepScan
import TestFileUtilities
import TestGeneral
import TestMemory
import TestOptions
import TestRecognizeCleanerML
import TestUnix
import TestUpdate
import TestWindows
import TestWorker


suites = [ TestAction.suite(),
           TestCleanerML.suite(),
           TestCleaner.suite(),
           TestCLI.suite(),
           TestCommand.suite(),
           TestDeepScan.suite(),
           TestFileUtilities.suite(),
           TestGeneral.suite(),
           TestMemory.suite(),
           TestOptions.suite(),
           TestRecognizeCleanerML.suite(),
           TestUpdate.suite(),
           TestWorker.suite() ]

if 'posix' == os.name:
    suites.append(TestUnix.suite())

if 'nt' == os.name:
    suites.append(TestWindows.suite)

def suite():
    """Combine all the suites into one large suite"""
    suite_ = unittest.TestSuite()
    map(suite_.addTest, suites)
    return suite_


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())

