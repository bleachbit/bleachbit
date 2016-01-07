# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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
Test case for module Diagnostic
"""

import sys
import unittest

import common

sys.path.append('.')
from bleachbit.Diagnostic import diagnostic_info


class DiagnosticTestCase(unittest.TestCase):

    """Test Case for module Diagnostic"""

    def test_diagnostic_info(self):
        """Test diagnostic_info"""
        # at least it does not crash
        ret = diagnostic_info()
        self.assert_(isinstance(ret, (str,unicode)))

def suite():
    return unittest.makeSuite(DiagnosticTestCase)


if __name__ == '__main__':
    unittest.main()
