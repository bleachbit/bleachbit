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

from tests import common
from bleachbit import APP_VERSION, IS_WINDOWS
from bleachbit.FileUtilities import exe_exists
from bleachbit.General import get_executable, run_external


class MakefileTestCase(common.BleachbitTestCase):
    """Test case for Makefile"""

    def setUp(self):
        """Locate xgettext, make, and tar before running the test"""
        super().setUp()
        src_base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        self.src_base_dir = src_base_dir

        # appveyor.yml adds the MSYS2 bin directory to PATH before tests,
        # so the tools are found via exe_exists() (which searches PATH).
        # On Windows, exists_in_path() does not append .exe, so do it here.
        exe_suffix = '.exe' if IS_WINDOWS else ''

        tools = {
            'make_exe': ('make', 'make (not found in PATH)'),
            'xgettext_exe': ('xgettext', 'xgettext (run `apt install gettext` or equivalent)'),
            'tar_exe': ('tar', 'tar (not found in PATH)'),
        }

        missing = []
        for attr, (tool_name, error_msg) in tools.items():
            exe_name = tool_name + exe_suffix
            if exe_exists(exe_name):
                setattr(self, attr, exe_name)
            else:
                setattr(self, attr, None)
                missing.append(error_msg)

        if missing:
            if 'CI' in os.environ or not IS_WINDOWS:
                raise RuntimeError(
                    'Missing required build tools: ' + '; '.join(missing))
            self.skipTest(
                'Missing required build tools: ' + '; '.join(missing))

    def test_make_source(self):
        """Test Makefile for source distribution"""
        src_base_dir = self.src_base_dir
        os.chdir(src_base_dir)
        make_exe = self.make_exe
        tar_exe = self.tar_exe

        ver_name = 'bleachbit-' + APP_VERSION

        # clean up from any previous test
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        if os.path.exists(pkg_fn):
            os.remove(pkg_fn)
        self.assertNotExists(pkg_fn)

        # build source distribution
        sdist_cmd = [get_executable(), 'setup.py', 'sdist']
        (rc, _, stderr) = run_external(sdist_cmd)
        self.assertEqual(rc, 0, stderr)
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        self.assertExists(pkg_fn)

        # extract source distribution
        extract_dir = os.path.join(self.tempdir, 'extract')
        os.mkdir(extract_dir)
        tar_cmd = [tar_exe, 'xzf', pkg_fn, '-C', extract_dir]
        (rc, _, stderr) = run_external(tar_cmd)
        self.assertEqual(rc, 0, stderr)
        extract_subdir = os.path.join(extract_dir, ver_name)
        self.assertExists(os.path.join(extract_subdir, 'Makefile'))

        # delete Windows files using make
        canary_fn = os.path.join(
            extract_subdir, 'cleaners', 'windows_explorer.xml')
        self.assertExists(canary_fn)
        del_win_command = [make_exe, 'delete_windows_files']
        os.chdir(extract_subdir)
        (rc, _, stderr) = run_external(del_win_command)
        self.assertEqual(rc, 0, stderr)
        self.assertNotExists(canary_fn)

        # install using make
        install_tgt_dir = os.path.join(self.tempdir, 'install')
        install_command = [make_exe,
                           'install', 'DESTDIR=' + install_tgt_dir]
        os.chdir(extract_subdir)
        (rc, _, stderr) = run_external(install_command)
        self.assertEqual(rc, 0, f"make install failed with rc={rc}, stderr={stderr}")
        self.assertTrue(os.path.isdir(install_tgt_dir))
        self.assertExists(os.path.join(
            install_tgt_dir, 'usr/local/share/bleachbit/cleaners/chromium.xml'))
