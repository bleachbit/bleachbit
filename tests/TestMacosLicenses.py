# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module macos.licenses

Only the functions that do not need Homebrew are tested here.
"""

# standard library
import os
import tempfile
import unittest

# local import
from bleachbit import IS_WINDOWS
from macos.licenses import (
    formula_of,
    formulas_of,
    license_files,
    mirrored_sources,
    python_packages,
    render_notice,
    write_notices,
)
from tests import common


def touch(path, text=''):
    """Create a file, and the directories above it"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


class MacosLicensesTestCase(common.BleachbitTestCase):
    """Test case for module macos.licenses"""

    @unittest.skipIf(IS_WINDOWS, 'needs symbolic links')
    def test_formula_of(self):
        """Unit test for formula_of() and formulas_of()"""
        with tempfile.TemporaryDirectory() as root:
            cellar = os.path.join(root, 'Cellar')
            real = os.path.join(cellar, 'glib', '2.90.1_1',
                                'lib', 'libx.dylib')
            touch(real)
            linked = os.path.join(root, 'lib', 'libx.dylib')
            os.makedirs(os.path.dirname(linked))
            os.symlink(real, linked)
            outside = os.path.join(root, 'other', 'liby.dylib')
            touch(outside)
            self.assertEqual(formula_of(linked, cellar), 'glib')
            self.assertEqual(formula_of(real, cellar), 'glib')
            self.assertIsNone(formula_of(outside, cellar))
            self.assertEqual(
                formulas_of([linked, outside, os.path.join(root, 'none')],
                            cellar),
                ['glib'])

    def test_license_files(self):
        """Unit test for license_files()"""
        with tempfile.TemporaryDirectory() as root:
            for name in ('COPYING', 'COPYING.LIB', 'LICENSE.md', 'README'):
                touch(os.path.join(root, name))
            os.makedirs(os.path.join(root, 'LICENSES'))
            self.assertEqual(
                [os.path.basename(p) for p in license_files(root)],
                ['COPYING', 'COPYING.LIB', 'LICENSE.md'])
            self.assertEqual(license_files(os.path.join(root, 'none')), [])

    def test_mirrored_sources(self):
        """Unit test for mirrored_sources()"""
        with tempfile.TemporaryDirectory() as root:
            for name in ('b.xml', 'a.xml', 'c.compiled'):
                touch(os.path.join(root, name))
            self.assertEqual(
                mirrored_sources(root, '/brew/schemas', '.xml'),
                [os.path.join('/brew/schemas', 'a.xml'),
                 os.path.join('/brew/schemas', 'b.xml')])

    def test_python_packages(self):
        """Unit test for python_packages()"""
        with tempfile.TemporaryDirectory() as root:
            touch(os.path.join(root, 'foo-1.0.dist-info', 'METADATA'),
                  'Metadata-Version: 2.4\nName: foo\nVersion: 1.0\n'
                  'License-Expression: MIT\n\nLong description\n')
            touch(os.path.join(root, 'bar-2.0.dist-info', 'METADATA'),
                  'Metadata-Version: 2.1\nName: bar\nVersion: 2.0\n\n')
            self.assertEqual(
                python_packages(root),
                [{'name': 'bar', 'version': '2.0', 'license': None},
                 {'name': 'foo', 'version': '1.0', 'license': 'MIT'}])

    def test_render_notice(self):
        """Unit test for render_notice()"""
        entries = [
            {'name': 'cairo', 'version': '1.18.6',
             'license': 'LGPL-2.1-only OR MPL-1.1',
             'homepage': 'https://cairographics.org/',
             'source': 'https://cairographics.org/releases/cairo.tar.xz',
             'files': ['/x/COPYING', '/x/COPYING-LGPL-2.1']},
            {'name': 'glib', 'version': '2.90.1_1', 'license': None,
             'homepage': None, 'source': None, 'files': []},
        ]
        packages = [{'name': 'requests', 'version': '2.34.2',
                     'license': 'Apache-2.0'}]
        text = render_notice('6.0.5', entries, packages)
        self.assertIn('BleachBit 6.0.5 for macOS', text)
        self.assertIn('cairo 1.18.6', text)
        self.assertIn('LGPL-2.1-only OR MPL-1.1', text)
        self.assertIn('https://cairographics.org/releases/cairo.tar.xz', text)
        self.assertIn('License files: COPYING, COPYING-LGPL-2.1', text)
        # no license file: say so, and do not invent a license
        self.assertIn('glib 2.90.1_1', text)
        self.assertIn('License:  unknown', text)
        self.assertIn('Homebrew does not install them', text)
        self.assertIn('requests 2.34.2', text)
        self.assertIn('Apache-2.0', text)
        self.assertTrue(text.endswith('\n'))

    def test_write_notices(self):
        """Unit test for write_notices()"""
        with tempfile.TemporaryDirectory() as root:
            source = os.path.join(root, 'brew', 'COPYING')
            touch(source, 'license text')
            resources = os.path.join(root, 'Resources')
            os.makedirs(resources)
            entries = [
                {'name': 'gtk+3', 'version': '3.24.52_1',
                 'license': 'LGPL-2.0-or-later', 'homepage': 'https://gtk.org',
                 'source': 'https://example.org/gtk.tar.xz',
                 'files': [source]},
                {'name': 'glib', 'version': '1', 'license': None,
                 'homepage': None, 'source': None, 'files': []},
            ]
            notices = write_notices(resources, '6.0.5', entries, [])
            self.assertTrue(os.path.exists(notices))
            with open(os.path.join(resources, 'licenses', 'gtk+3',
                                   'COPYING'), encoding='utf-8') as f:
                self.assertEqual(f.read(), 'license text')
            # a package without license files gets no directory
            self.assertFalse(os.path.exists(
                os.path.join(resources, 'licenses', 'glib')))
