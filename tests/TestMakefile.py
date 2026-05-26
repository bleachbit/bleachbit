# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


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

        sdist_cmd = [sys.executable, 'setup.py', 'sdist', '--formats=gztar']
        subprocess.check_call(sdist_cmd)
        pkg_fn = os.path.join('dist', ver_name+'.tar.gz')
        self.assertExists(pkg_fn)

        extract_dir = os.path.join(make_temp_dir, 'extract')
        os.mkdir(extract_dir)
        tar_cmd = ['tar', 'xzf', pkg_fn, '-C', extract_dir]
        subprocess.check_call(tar_cmd)
        extract_subdir = os.path.join(extract_dir, ver_name)
        self.assertExists(os.path.join(extract_subdir, 'Makefile'))
        self.assertExists(os.path.join(
            extract_subdir, 'cleaners', 'chromium.xml'))

    def test_exists(self):
        """This has a side effect of causing setUp() to run and emit a warning, if exes are missing"""
        mk_fn = os.path.join(self.base_dir, 'Makefile')
        self.assertExists(mk_fn)
