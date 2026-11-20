# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module macos.build_dmg

Only the helpers that do not need macOS or Homebrew are tested here.
"""

# standard library
import os
import tempfile
import unittest

# local import
from bleachbit import IS_WINDOWS
from macos.build_dmg import (
    bundle_paths,
    customize_info_plist,
    find_bytecode,
    find_files_containing,
    loaders_cache_template,
    render_template,
    requirement_lines,
)
from tests import common


class MacosBuildTestCase(common.BleachbitTestCase):
    """Test case for module macos.build_dmg"""

    def test_render_template(self):
        """Unit test for render_template()"""
        self.assertEqual(
            render_template('<v>@VERSION@</v><v>@VERSION@</v>',
                            version='6.0.5'),
            '<v>6.0.5</v><v>6.0.5</v>')

    def test_customize_info_plist(self):
        """Unit test for customize_info_plist()"""
        original = {
            'CFBundleName': 'Python',
            'CFBundleLongVersionString': '3.12.15, (c) 2001 Python',
            'CFBundleDocumentTypes': [{'CFBundleTypeName': 'Python Script'}],
            'CFBundleExecutable': 'Python',
        }
        info = customize_info_plist(original, '6.0.5')
        self.assertEqual(info['CFBundleName'], 'BleachBit')
        self.assertEqual(info['CFBundleIdentifier'], 'org.bleachbit.BleachBit')
        self.assertEqual(info['CFBundleShortVersionString'], '6.0.5')
        self.assertEqual(info['CFBundleExecutable'], 'Python')
        self.assertNotIn('CFBundleLongVersionString', info)
        self.assertNotIn('CFBundleDocumentTypes', info)
        # the input is not modified
        self.assertEqual(original['CFBundleName'], 'Python')

    def test_loaders_cache_template(self):
        """Unit test for loaders_cache_template()"""
        cache = '"/x/Frameworks/lib/gdk-pixbuf-2.0/2.10.0/loaders/a.so"\n'
        self.assertEqual(
            loaders_cache_template(cache, '/x/Frameworks/lib'),
            '"@LIB@/gdk-pixbuf-2.0/2.10.0/loaders/a.so"\n')

    def test_find_files_containing(self):
        """Unit test for find_files_containing()"""
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'sub'))
            with open(os.path.join(root, 'sub', 'a.txt'), 'wb') as f:
                f.write(b'xx /opt/homebrew/lib xx')
            with open(os.path.join(root, 'b.bin'), 'wb') as f:
                f.write(b'\x00\x01 nothing here')
            try:
                os.symlink(os.path.join(root, 'b.bin'),
                           os.path.join(root, 'link'))
            except (OSError, NotImplementedError):
                pass  # not allowed to make symbolic links (Windows)
            found = find_files_containing(
                root, ['/opt/homebrew', '/Users/'])
        self.assertEqual(found['/opt/homebrew'],
                         [os.path.join('sub', 'a.txt')])
        self.assertEqual(found['/Users/'], [])

    def test_requirement_lines(self):
        """setuptools is not installed in the bundle"""
        lines = requirement_lines()
        self.assertTrue(lines)
        for line in lines:
            self.assertNotIn('#', line)
            self.assertFalse(line.lower().startswith('setuptools'), line)
        self.assertTrue(any(line.startswith('psutil') for line in lines))

    @unittest.skipIf(IS_WINDOWS, 'the expected paths are POSIX paths')
    def test_bundle_paths(self):
        """Unit test for bundle_paths()"""
        b = bundle_paths('/out/BleachBit.app')
        self.assertEqual(b.macos, '/out/BleachBit.app/Contents/MacOS')
        self.assertTrue(b.site_packages.endswith(
            'Versions/3.12/lib/python3.12/site-packages'))
        self.assertTrue(b.python_app.endswith(
            'Versions/3.12/Resources/Python.app'))

    def test_find_bytecode(self):
        """Unit test for find_bytecode()

        Regression test: the checks of the build used to run the bundled
        Python, which left compiled files with the path of the build.
        """
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'lib', '__pycache__'))
            os.makedirs(os.path.join(root, 'lib', 'sub', '__pycache__'))
            os.makedirs(os.path.join(root, 'clean'))
            self.assertEqual(
                find_bytecode(root),
                [os.path.join('lib', '__pycache__'),
                 os.path.join('lib', 'sub', '__pycache__')])
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(find_bytecode(root), [])
