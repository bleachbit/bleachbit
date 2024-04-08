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
Test case for Makefile
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests import common


has_make = True

try:
    subprocess.check_call(['make', '--version'])
except FileNotFoundError:
    has_make = False

skip_tests = not has_make
skip_msg = 'missing make'

make_temp_dir = tempfile.mkdtemp('bleachbit-makefile')


class MakefileTestCase(common.BleachbitTestCase):
    """Test case for Makefile"""

    def setUp(self):
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        os.chdir(self.base_dir)
        if skip_tests:
            import warnings
            warnings.warn(skip_msg)
            return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(make_temp_dir)

    @unittest.skipIf(skip_tests, skip_msg)
    def test_make(self):

        from bleachbit import APP_VERSION
        ver_name = 'bleachbit-'+APP_VERSION

        pkg_fn = os.path.join('dist', ver_name+'.tar.gz')
        if os.path.exists(pkg_fn):
            os.remove(pkg_fn)
        self.assertNotExists(pkg_fn)

        sdist_cmd = [sys.executable, 'setup.py', 'sdist']
        subprocess.check_call(sdist_cmd)
        pkg_fn = os.path.join('dist', ver_name+'.tar.gz')
        self.assertExists(pkg_fn)

        extract_dir = os.path.join(make_temp_dir, 'extract')
        os.mkdir(extract_dir)
        tar_cmd = ['tar', 'xzf', pkg_fn, '-C', extract_dir]
        subprocess.check_call(tar_cmd)
        extract_subdir = os.path.join(extract_dir, ver_name)
        self.assertExists(os.path.join(extract_subdir, 'Makefile'))

        canary_fn = os.path.join(
            extract_subdir, 'cleaners', 'windows_explorer.xml')
        self.assertExists(canary_fn)
        del_win_command = ['make', 'delete_windows_files']
        subprocess.check_call(del_win_command, cwd=extract_subdir)
        self.assertNotExists(canary_fn)

        install_tgt_dir = os.path.join(make_temp_dir, 'install')
        install_command = ['make', 'install', 'DESTDIR='+install_tgt_dir]
        subprocess.check_call(install_command, cwd=extract_subdir)
        self.assertTrue(os.path.isdir(install_tgt_dir))
        self.assertExists(os.path.join(
            install_tgt_dir, 'usr/local/share/bleachbit/cleaners/chromium.xml'))

    def test_exists(self):
        """This has a side effect of causing setUp() to run and emit a warning, if exes are missing"""
        mk_fn = os.path.join(self.base_dir, 'Makefile')
        self.assertExists(mk_fn)
