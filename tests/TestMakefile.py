# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
Test case for Makefile
"""

import os
import subprocess

from tests import common
from bleachbit import APP_VERSION
from bleachbit.FileUtilities import exe_exists
from bleachbit.General import get_executable


class MakefileTestCase(common.BleachbitTestCase):
    """Test case for Makefile"""

    def setUp(self):
        """Call before each test method"""
        src_base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        os.chdir(src_base_dir)
        # appveyor.yml defines %make%
        for exe in ('make', os.getenv('make')):
            if exe and exe_exists(exe):
                self.make_exe = exe
                return
        self.skipTest('make not found in PATH or in $make')

    def test_make(self):
        """Test Makefile"""
        ver_name = 'bleachbit-' + APP_VERSION

        # clean up from any previous test
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        if os.path.exists(pkg_fn):
            os.remove(pkg_fn)
        self.assertNotExists(pkg_fn)

        # build source distribution
        sdist_cmd = [get_executable(), 'setup.py', 'sdist']
        subprocess.check_call(sdist_cmd)
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        self.assertExists(pkg_fn)

        # extract source distribution
        extract_dir = os.path.join(self.tempdir, 'extract')
        os.mkdir(extract_dir)
        tar_cmd = ['tar', 'xzf', pkg_fn, '-C', extract_dir]
        subprocess.check_call(tar_cmd)
        extract_subdir = os.path.join(extract_dir, ver_name)
        self.assertExists(os.path.join(extract_subdir, 'Makefile'))

        # delete Windows files using make
        canary_fn = os.path.join(
            extract_subdir, 'cleaners', 'windows_explorer.xml')
        self.assertExists(canary_fn)
        del_win_command = [self.make_exe, 'delete_windows_files']
        subprocess.check_call(del_win_command, cwd=extract_subdir)
        self.assertNotExists(canary_fn)

        # install using make
        install_tgt_dir = os.path.join(self.tempdir, 'install')
        install_command = [self.make_exe,
                           'install', 'DESTDIR=' + install_tgt_dir]
        subprocess.check_call(install_command, cwd=extract_subdir)
        self.assertTrue(os.path.isdir(install_tgt_dir))
        self.assertExists(os.path.join(
            install_tgt_dir, 'usr/local/share/bleachbit/cleaners/chromium.xml'))
