# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module GUI
"""

from __future__ import absolute_import

import os
import unittest

try:
    import gtk
    from bleachbit.GUI import GUI
    HAVE_GTK = True
except ImportError:
    HAVE_GTK = False

from tests import common

IS_APPVEYOR = os.getenv('APPVEYOR') is not None


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module')
@unittest.skipIf(IS_APPVEYOR, 'test not yet supported on AppVeyor')
class GUITestCase(common.BleachbitTestCase):
    """Test case for module GUI"""

    def test_GUI(self):
        """Unit test for class GUI"""
        # there should be no crashes
        gui = GUI()
        gui.update_total_size(0)
        gui.update_total_size(1000)
        gui.update_progress_bar(0.0)
        gui.update_progress_bar(1.0)
        gui.update_progress_bar("status")
