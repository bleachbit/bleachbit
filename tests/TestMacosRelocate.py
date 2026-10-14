# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module macos.relocate

The parsers work on text, so these tests run on every operating system.
"""

# standard library
import os
import shutil
import subprocess
import tempfile
import unittest

# local import
from bleachbit import IS_MAC, IS_WINDOWS
from macos.relocate import (
    Relocator,
    bundle_install_name,
    external_ids,
    install_ids,
    parse_otool_dependencies,
    parse_otool_ids,
    parse_otool_rpaths,
)
from tests import common

SINGLE = """/b/lib/libgtk-3.0.dylib:
\t@rpath/libgtk-3.0.dylib (compatibility version 2409.0.0, current version 2409.33.0)
\t/opt/homebrew/opt/glib/lib/libglib-2.0.0.dylib (compatibility version 8801.0.0, current version 8801.6.0)
\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
"""

FAT = """/b/lib/libffi.8.dylib (architecture x86_64):
\t/opt/homebrew/opt/libffi/lib/libffi.8.dylib (compatibility version 10.0.0, current version 10.0.0)
\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
/b/lib/libffi.8.dylib (architecture arm64):
\t/opt/homebrew/opt/libffi/lib/libffi.8.dylib (compatibility version 10.0.0, current version 10.0.0)
\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
"""

RPATHS = """Load command 12
          cmd LC_RPATH
      cmdsize 48
         path /opt/homebrew/lib (offset 12)
Load command 13
          cmd LC_RPATH
      cmdsize 32
         path @loader_path/../lib (offset 12)
"""


class MacosRelocateTestCase(common.BleachbitTestCase):
    """Test case for module macos.relocate"""

    def test_parse_otool_dependencies(self):
        """Unit test for parse_otool_dependencies()"""
        own = {'@rpath/libgtk-3.0.dylib'}
        self.assertEqual(
            parse_otool_dependencies(SINGLE, own),
            ['/opt/homebrew/opt/glib/lib/libglib-2.0.0.dylib',
             '/usr/lib/libSystem.B.dylib'])

    def test_parse_otool_dependencies_fat(self):
        """The architecture header lines of a universal binary are not dependencies

        Regression test: the headers ended up in the list, so the build
        tried to relocate a library named like `file (architecture arm64):`.
        """
        deps = parse_otool_dependencies(FAT)
        self.assertNotIn('/b/lib/libffi.8.dylib', deps)
        for dep in deps:
            self.assertFalse(dep.endswith(':'), dep)
            self.assertNotIn('architecture', dep)

    def test_parse_otool_ids_fat(self):
        """Unit test for parse_otool_ids() with a universal binary"""
        text = ('/b/lib/libffi.8.dylib (architecture x86_64):\n'
                '@rpath/libffi.8.dylib\n'
                '/b/lib/libffi.8.dylib (architecture arm64):\n'
                '@rpath/libffi.8.dylib\n')
        self.assertEqual(parse_otool_ids(text), {'@rpath/libffi.8.dylib'})

    def test_parse_otool_rpaths(self):
        """Unit test for parse_otool_rpaths()"""
        self.assertEqual(parse_otool_rpaths(RPATHS),
                         ['/opt/homebrew/lib', '@loader_path/../lib'])
        self.assertEqual(parse_otool_rpaths(''), [])

    def test_external_ids(self):
        """Unit test for external_ids()"""
        ids = {'/opt/homebrew/opt/gtk+3/lib/libgtk-3.0.dylib',
               '@rpath/libfoo.dylib'}
        self.assertEqual(
            external_ids(ids, ('/opt/homebrew', '/Users/')),
            ['/opt/homebrew/opt/gtk+3/lib/libgtk-3.0.dylib'])
        self.assertEqual(external_ids(set(), ('/opt/homebrew',)), [])

    @unittest.skipIf(IS_WINDOWS, 'the expected paths are POSIX paths')
    def test_bundle_install_name(self):
        """Unit test for bundle_install_name()"""
        frameworks = '/b/Contents/Frameworks'
        self.assertEqual(
            bundle_install_name(frameworks + '/lib/libx.dylib',
                                frameworks + '/lib', frameworks),
            '@rpath/libx.dylib')
        self.assertEqual(
            bundle_install_name(
                frameworks + '/Python.framework/Versions/3.12/Python',
                frameworks + '/lib', frameworks),
            '@rpath/Python.framework/Versions/3.12/Python')


@unittest.skipUnless(IS_MAC and shutil.which('clang'),
                     'needs macOS and clang')
class MacosRelocateInstallNameTestCase(common.BleachbitTestCase):
    """Test case for the install names of the libraries in a bundle"""

    def test_install_name_of_copied_library(self):
        """A library that keeps the install name of Homebrew is a problem

        Regression test: libgtk-3.0.dylib, which is copied because a
        typelib names it, kept /opt/homebrew/... as its install name and
        the check did not report it.
        """
        with tempfile.TemporaryDirectory() as root:
            app = os.path.join(root, 'Test.app')
            libdir = os.path.join(app, 'Contents', 'Frameworks', 'lib')
            os.makedirs(libdir)
            source = os.path.join(root, 'x.c')
            with open(source, 'w', encoding='utf-8') as f:
                f.write('int x(void) { return 1; }\n')
            lib = os.path.join(libdir, 'libx.dylib')
            subprocess.run(
                ['clang', '-dynamiclib', '-o', lib, source,
                 '-install_name', '/opt/homebrew/opt/x/lib/libx.dylib'],
                check=True, capture_output=True)
            relocator = Relocator(app, '/opt/homebrew')
            self.assertTrue(
                any('install name' in p for p in relocator.problems()))
            self.assertEqual(relocator.fix_install_names(), 1)
            self.assertEqual(relocator.problems(), [])
            self.assertEqual(install_ids(lib), {'@rpath/libx.dylib'})
