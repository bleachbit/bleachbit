# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Unit tests for bleachbit.PathUtils."""

import os
import unittest
from unittest import mock

from bleachbit import IS_MAC, IS_WINDOWS
from bleachbit.FileUtilities import whitelisted_windows
from bleachbit.PathUtils import (
    expand_path,
    expand_path_entries,
    normalize_path,
    path_equal,
    path_has_relative_suffix,
    path_startswith,
)
from bleachbit.ProtectedPath import check_protected_path
from tests import common


class PathUtilsTestCase(unittest.TestCase):
    """Tests for the PathUtils helper functions."""

    def test_path_equal_case_sensitivity(self):
        """Verify path_equal honors the case_sensitive flag."""
        self.assertTrue(path_equal(
            '/Home/Foo', '/Home/Foo', case_sensitive=True))
        self.assertFalse(path_equal(
            '/Home/Foo', '/home/foo', case_sensitive=True))
        self.assertTrue(path_equal(
            '/Home/Foo', '/home/foo', case_sensitive=False))

    def test_path_equal_does_not_normalize(self):
        """Verify path_equal compares paths without normalization."""
        self.assertFalse(path_equal('/home/foo', '/home/foo/'))
        self.assertFalse(path_equal('/home/foo', '/home/./foo'))

    def test_path_startswith_component_boundaries(self):
        """Verify path_startswith respects component boundaries."""
        self.assertTrue(path_startswith('/home/folder/file', '/home/folder'))
        self.assertFalse(path_startswith('/home/folder', '/home/folder'))
        self.assertFalse(path_startswith('/home/folder2', '/home/folder'))
        self.assertFalse(path_startswith('/home/folder/file', '/home/folder/'))
        self.assertTrue(path_startswith('/home/folder/', '/home/folder'))
        self.assertFalse(path_startswith('/home/folder', '/'))
        self.assertFalse(path_startswith(
            r'D:\folder', 'D:\\', case_sensitive=False))

    def test_normalize_path(self):
        """Verify normalize_path collapses segments and applies case rules."""
        self.assertEqual(normalize_path('/home/foo/../bar', case_sensitive=True),
                         os.path.normpath('/home/bar'))
        self.assertEqual(normalize_path('/Home/Foo', case_sensitive=False),
                         os.path.normpath('/home/foo'))

    def test_expand_path(self):
        """Verify expand_path resolves environment placeholders and normalizes."""
        variable = 'TEST_PATH_UTILS_PATH'
        placeholder = f'%{variable}%' if IS_WINDOWS else f'${variable}'
        value = os.path.join(os.sep, 'pathutils', 'expanded')
        with common.set_temporary_env(variable, value):
            self.assertEqual(
                expand_path(os.path.join(placeholder, '.', 'child')),
                os.path.join(value, 'child'))
        self.assertEqual(expand_path(''), '')

    def test_expand_path_entries(self):
        """Verify expand_path_entries splits list-style environment values."""
        variable = 'TEST_PATH_UTILS_ENTRIES'
        placeholder = f'%{variable}%' if IS_WINDOWS else f'${variable}'
        first = os.path.join(os.sep, 'pathutils-first')
        second = os.path.join(os.sep, 'pathutils-second')
        with common.set_temporary_env(variable, os.pathsep.join((first, '', second))):
            self.assertEqual(expand_path_entries(placeholder), (first, second))
            self.assertEqual(
                expand_path_entries(os.path.join(placeholder, 'child')),
                (os.path.normpath(
                    os.pathsep.join((first, '', second)) + os.sep + 'child'),))

    def test_path_has_relative_suffix(self):
        """Verify path_has_relative_suffix matches suffix components only."""
        self.assertTrue(path_has_relative_suffix('/home/user/.git', '.git'))
        self.assertTrue(path_has_relative_suffix('.git', '.git'))
        self.assertFalse(path_has_relative_suffix(
            '/home/user/not-git', '.git'))
        self.assertFalse(path_has_relative_suffix(
            '/home/user/.gitignore', '.git'))
        self.assertTrue(path_has_relative_suffix(
            '/home/user/.GIT', '.git', case_sensitive=False))

    @unittest.skipUnless(IS_WINDOWS, 'Windows treats backslash as separator')
    def test_path_startswith_windows_separators(self):
        """Verify path_startswith handles backslash and mixed separators."""
        self.assertTrue(path_startswith(r'D:\folder\file', r'D:\folder'))
        self.assertTrue(path_startswith(r'D:\folder/file', r'D:\folder'))
        self.assertTrue(path_startswith('D:/folder/file', 'D:/folder'))
        self.assertFalse(path_startswith(r'D:\folder2', r'D:\folder'))
        self.assertFalse(path_startswith(r'D:\folder', r'D:\folder'))

    @unittest.skipUnless(IS_WINDOWS, 'Windows treats backslash as separator')
    def test_path_has_relative_suffix_windows_separators(self):
        """Verify path_has_relative_suffix handles backslash separators."""
        self.assertTrue(path_has_relative_suffix(r'D:\folder\.git', '.git'))
        self.assertTrue(path_has_relative_suffix(r'D:\folder\.git', r'.git'))
        self.assertFalse(path_has_relative_suffix(
            r'D:\folder\not-git', '.git'))
        self.assertFalse(path_has_relative_suffix(
            r'D:\folder\.gitignore', '.git'))

    def test_whitelisted_windows_drive_root_matches_descendants(self):
        """Verify a whitelisted drive root protects its descendants."""
        with mock.patch(
                'bleachbit.Options.options.get_whitelist_paths',
                return_value=[('folder', 'D:\\')]):
            self.assertTrue(whitelisted_windows('d:\\'))
            self.assertTrue(whitelisted_windows(r'D:\folder\file'))
            self.assertFalse(whitelisted_windows(r'D:folder\file'))
            self.assertFalse(whitelisted_windows(r'E:\folder\file'))

    @unittest.skipUnless(IS_MAC, 'macOS-specific protected-path behavior')
    def test_protected_path_matching_is_case_sensitive_on_macos(self):
        """Verify protected-path matching is case-sensitive on macOS."""
        protected = '/PathUtilsProtected/CaseSensitive'
        definition = {
            'path': protected,
            'depth': 0,
            'case_sensitive': not IS_WINDOWS,
        }
        with mock.patch(
                'bleachbit.ProtectedPath.load_protected_paths',
                return_value=[definition]):
            self.assertEqual(check_protected_path(protected), definition)
            self.assertIsNone(check_protected_path(protected.swapcase()))
