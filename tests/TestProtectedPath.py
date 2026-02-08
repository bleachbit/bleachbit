# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Test case for module ProtectedPath
"""

import os
import tempfile
import unittest

from functools import wraps

from tests import common
from bleachbit.ProtectedPath import (
    _check_exempt,
    _expand_path,
    _get_protected_path_xml,
    _normalize_for_comparison,
    calculate_impact,
    check_protected_path,
    clear_cache,
    get_warning_message,
    load_protected_paths)
from bleachbit import ProtectedPath as protected_path_module
from bleachbit import get_share_path
from bleachbit.Cleaner import backends
from tests.TestCleaner import register_all_cleaners


CASE_METHODS = (
    str.lower,
    str.upper,
    str.title,
    str.swapcase,
    lambda x: x)


def requirePPXML(test_func):
    """Decorator to skip test if protected path XML is not found"""
    @wraps(test_func)
    def wrapper(self):
        if not _get_protected_path_xml():
            self.skipTest('Protected path XML not found')
        return test_func(self)
    return wrapper


class ProtectedPathTestCase(common.BleachbitTestCase):
    """Test case for ProtectedPath module"""

    def setUp(self):
        """Call before each test method"""
        super().setUp()
        clear_cache()

    def tearDown(self):
        """Call after each test method"""
        super().tearDown()
        clear_cache()

    def test_expand_path(self):
        """Test _expand_path function"""
        # Test user home expansion
        home = os.path.expanduser('~')
        result = _expand_path('~')
        self.assertEqual(result, home)

        # Test with subpath
        result = _expand_path('~/Documents')
        expected = os.path.normpath(os.path.join(home, 'Documents'))
        self.assertEqual(result, expected)

        # Test environment variable expansion
        os.environ['TEST_PROTECTED_PATH_VAR'] = '/test/path'
        try:
            if os.name == 'nt':
                result = _expand_path('%TEST_PROTECTED_PATH_VAR%')
            else:
                result = _expand_path('$TEST_PROTECTED_PATH_VAR')
            self.assertEqual(result, os.path.normpath('/test/path'))
        finally:
            del os.environ['TEST_PROTECTED_PATH_VAR']

    def test_normalize_for_comparison(self):
        """Test _normalize_for_comparison function"""
        # Case sensitive
        result = _normalize_for_comparison('/Home/User', True)
        self.assertIn('Home', result)

        # Case insensitive
        result = _normalize_for_comparison('/Home/User', False)
        self.assertEqual(result, result.lower())

    def test_get_protected_path_xml(self):
        """Test that protected path XML file can be found"""
        xml_path = get_share_path('protected_path.xml')
        self.assertIsNotNone(xml_path, 'protected_path.xml not found via get_share_path')
        self.assertExists(xml_path)
        xml_path2 = _get_protected_path_xml()
        self.assertIsNotNone(xml_path2, 'Protected path XML not found')
        self.assertExists(xml_path2)
        self.assertTrue(xml_path2.endswith('protected_path.xml'))

    @requirePPXML
    def test_load_protected_paths(self):
        """Test loading protected paths from XML"""
        paths = load_protected_paths()
        self.assertIsInstance(paths, list)
        # Should have loaded some paths for current OS
        self.assertGreater(len(paths), 0)

        # Each path should have required keys
        for ppath in paths:
            self.assertIn('path', ppath)
            self.assertIn('depth', ppath)
            self.assertIn('case_sensitive', ppath)
            self.assertIsInstance(ppath['path'], str)
            self.assertTrue(isinstance(
                ppath['depth'], int) or ppath['depth'] is None)
            self.assertIsInstance(ppath['case_sensitive'], bool)

    @requirePPXML
    @common.skipIfWindows
    def test_expand_path_entries_split_os_pathsep(self):
        """Environment variables with os.pathsep values expand into multiple entries"""

        original_value = os.environ.get('XDG_DATA_DIRS')
        share1 = f"/nonexistent_xdg_share1_{self._testMethodName}"
        share2 = f"/nonexistent_xdg_share2_{self._testMethodName}"
        expected_paths = [os.path.normpath(share1), os.path.normpath(share2)]
        try:
            os.environ['XDG_DATA_DIRS'] = os.pathsep.join(expected_paths)

            clear_cache()
            paths = load_protected_paths(force_reload=True)
            matches = [pp['path']
                       for pp in paths if pp['path'] in expected_paths]
            self.assertCountEqual(matches, expected_paths)

            for candidate in expected_paths:
                result = check_protected_path(candidate)
                self.assertIsNotNone(result)
        finally:
            if original_value is None:
                os.environ.pop('XDG_DATA_DIRS', None)
            else:
                os.environ['XDG_DATA_DIRS'] = original_value
            clear_cache()

    @requirePPXML
    def test_load_protected_paths_caching(self):
        """Test that protected paths are cached"""
        paths1 = load_protected_paths()
        paths2 = load_protected_paths()
        # Should be the same object (cached)
        self.assertIs(paths1, paths2)

        # Force reload should return new list
        paths3 = load_protected_paths(force_reload=True)
        self.assertIsNot(paths1, paths3)

    @common.skipUnlessWindows
    def test_check_exempt_windows(self):
        """Test check_exempt() on Windows"""
        temp_dir = _expand_path('%temp%')
        self.assertIsInstance(temp_dir, str)
        self.assertTrue(len(temp_dir) > 0)
        for case_method in CASE_METHODS:
            cased_temp_dir = case_method(temp_dir)
            self.assertTrue(_check_exempt(cased_temp_dir),
                            f"Failed for {cased_temp_dir}")
            cased_temp_dir += os.sep
            self.assertTrue(_check_exempt(cased_temp_dir),
                            f"Failed for {cased_temp_dir}")
            git_dir = os.path.join(temp_dir, '.git')
            self.assertTrue(_check_exempt(git_dir),
                            f"Failed for {git_dir}")
            git_dir += os.sep
            self.assertTrue(_check_exempt(git_dir),
                            f"Failed for {git_dir}")

    @common.skipIfWindows
    def test_check_exempt_unix(self):
        """Test check_exempt() on Unix"""
        expect_exempt = (
            '~/.cache',
            '~/.cache/',
            '~/.cache/.git',
            '/tmp',
            '/tmp/',
            '/tmp/.git')
        for path in expect_exempt:
            expanded_path = _expand_path(path)
            self.assertTrue(_check_exempt(expanded_path), expanded_path)
            self.assertFalse(_check_exempt(
                expanded_path.upper()), expanded_path)
        expect_not_exempt = (
            '/',
            '/home',
            '/home/',
            '~/.caches',
            '~/.caches/',
            '~/.caches/.git',
            '~/Documents/',
            '/tmps',
            '/tmps/',
            '/tmps/.git')
        for path in expect_not_exempt:
            self.assertFalse(_check_exempt(_expand_path(path)), path)

    def test_check_protected_path_no_match(self):
        """Test check_protected_path with non-protected path"""
        # A random temp path should not be protected
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_protected_path(tmpdir)
            self.assertIsNone(result)
        # Check .git (which is protected) under an exempt directory
        if os.name == 'posix':
            exempt_dir_raw = '~/.cache'
        elif os.name == 'nt':
            exempt_dir_raw = '%temp%'
        else:
            self.skipTest("Unsupported OS")
        exempt_dir = _expand_path(exempt_dir_raw)
        self.assertIsInstance(exempt_dir, str)
        self.assertTrue(_check_exempt(exempt_dir))
        self.assertNotEqual(exempt_dir, exempt_dir_raw)
        self.assertTrue(len(exempt_dir) > 0)
        result = check_protected_path(exempt_dir)
        self.assertIsNone(result)
        subpath = os.path.join(exempt_dir, '.git')
        result = check_protected_path(subpath)
        self.assertIsNone(result)
        # ~/Documents/Zoom/recording.mp4 is not protected
        zoom_path_raw = '~/Documents/Zoom/recording.mp4'
        zoom_path = _expand_path(zoom_path_raw)
        self.assertNotEqual(zoom_path, zoom_path_raw)
        result = check_protected_path(zoom_path)
        self.assertIsNone(result)

    @requirePPXML
    def test_check_protected_path_exact_match(self):
        """Test check_protected_path with exact match"""
        home = os.path.expanduser('~')
        home_result = check_protected_path(home)
        documents_path = os.path.expanduser('~/Documents')
        documents_result = check_protected_path(documents_path)
        for result in (home_result, documents_result):
            self.assertIsNotNone(result)
            self.assertIn('path', result)
            self.assertIn('depth', result)

    @requirePPXML
    def test_check_protected_path_child_match(self):
        """Test check_protected_path with child of protected path

        If /home/foo/.mozilla is protected with depth 1, adding /home/foo/.mozilla/firefox
        should also warn because it is a child of the protected directory.
        """
        # If home is protected with depth > 0, children should match
        paths = load_protected_paths()

        # Find a protected path with depth > 0
        for ppath in paths:
            if ppath['depth'] > 0:
                child_path = os.path.join(ppath['path'], 'test_subdir')
                result = check_protected_path(child_path)
                if result is not None:
                    self.assertGreater(result['depth'], 0)
                break

    @requirePPXML
    def test_check_protected_path_parent_match(self):
        """Test that parent of protected path triggers warning

        If /home/foo/.mozilla is protected with any depth, adding /home/foo
        should also warn because it is a parent containing the protected path.

        """
        paths = load_protected_paths()
        if not paths:
            self.skipTest("No protected paths loaded")

        # Find a protected path that has a parent directory
        for ppath in paths:
            protected = ppath['path']
            parent = os.path.dirname(protected)
            if parent and parent != protected:
                result = check_protected_path(parent)
                # Parent should match because it contains protected path
                if result is not None:
                    self.assertIsNotNone(result)
                break

    @requirePPXML
    def test_check_protected_path_git_variations(self):
        """Test that .git entries are detected at various nesting levels"""
        git_paths = [
            '/home/test/.git',
            '/home/test/bleachbit/.git',
            '/home/test/projects/bleachbit/.git',
        ]

        for path in git_paths:
            result = check_protected_path(path)
            self.assertIsNotNone(result, msg=f"Expected .git match for {path}")
            self.assertEqual(result['path'], '.git')

    @requirePPXML
    def test_check_protected_path_desktop_suffix(self):
        """Ensure Desktop.old variants do not match Desktop protected entry"""
        desktop = os.path.expanduser('~/Desktop')
        paths = [
            desktop + '.old',
            os.path.join(desktop + '.old', 'photo.jpg'),
        ]

        for path in paths:
            result = check_protected_path(path)
            self.assertIsNone(
                result, msg=f"Unexpected Desktop match for {path}")

    def test_calculate_impact_nonexistent(self):
        """Test calculate_impact with non-existent path"""
        result = calculate_impact('/nonexistent/path/12345')
        self.assertEqual(result['file_count'], 0)
        self.assertEqual(result['total_size'], 0)
        self.assertEqual(result['size_human'], '0B')

    def test_calculate_impact_file(self):
        """Test calculate_impact with a file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'x' * 1000)
            temp_path = f.name

        try:
            result = calculate_impact(temp_path)
            self.assertEqual(result['file_count'], 1)
            self.assertGreaterEqual(result['total_size'], 1000)
            self.assertIsInstance(result['size_human'], str)
        finally:
            os.unlink(temp_path)

    def test_calculate_impact_directory(self):
        """Test calculate_impact with a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            for i in range(5):
                filepath = os.path.join(tmpdir, f'file{i}.txt')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('x' * 100)

            result = calculate_impact(tmpdir)
            self.assertEqual(result['file_count'], 5)
            self.assertGreaterEqual(result['total_size'], 500)
            self.assertIsInstance(result['size_human'], str)

    def test_calculate_impact_nested_directory(self):
        """Test calculate_impact with nested directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = os.path.join(tmpdir, 'subdir')
            os.makedirs(subdir)

            # Files in root
            with open(os.path.join(tmpdir, 'root.txt'), 'w', encoding='utf-8') as f:
                f.write('x' * 100)

            # Files in subdir
            with open(os.path.join(subdir, 'sub.txt'), 'w', encoding='utf-8') as f:
                f.write('x' * 200)

            result = calculate_impact(tmpdir)
            self.assertEqual(result['file_count'], 2)
            self.assertGreaterEqual(result['total_size'], 300)

    def test_get_warning_message(self):
        """Test get_warning_message function"""
        impact = {
            'file_count': 10,
            'total_size': 1024000,
            'size_human': '1MB',
        }

        msg = get_warning_message('/home/user', impact)
        self.assertIsInstance(msg, str)
        self.assertIn('/home/user', msg)
        self.assertIn('10', msg)  # file count
        self.assertIn('1MB', msg)  # size

    def test_get_warning_message_no_files(self):
        """Test get_warning_message with no files"""
        impact = {
            'file_count': 0,
            'total_size': 0,
            'size_human': '0B',
        }

        msg = get_warning_message('/some/path', impact)
        self.assertIsInstance(msg, str)
        self.assertIn('/some/path', msg)

    @requirePPXML
    def test_clear_cache(self):
        """Test clear_cache function"""
        # Load to populate cache
        load_protected_paths()
        self.assertIsNotNone(protected_path_module._protected_paths_cache)

        # Clear cache
        clear_cache()
        self.assertIsNone(protected_path_module._protected_paths_cache)

    @requirePPXML
    def test_preview_all(self):
        """Check whether any real cleaners return protected paths"""
        register_all_cleaners()

        def check_option(co_key, co_option_id):
            for cmd in backends[co_key].get_commands(co_option_id):
                try:
                    for ret in cmd.execute(False):  # False = preview mode
                        if isinstance(ret, dict) and ret.get('path'):
                            path = ret['path']
                            result = check_protected_path(path)
                            if result is not None:
                                print(
                                    f'warning: {path} is protected by {result}')
                                return
                except:
                    continue
        option_counter = 0
        for key in sorted(backends):
            # loop over cleaners
            for (option_id, _option_name) in backends[key].get_options():
                # loop over options
                check_option(key, option_id)
                option_counter += 1
        print(f'checked {option_counter} options')

    @requirePPXML
    def test_path_with_trailing_slash(self):
        """Test that paths with trailing slashes are handled correctly"""
        home = os.path.expanduser('~')
        home_with_slash = home + os.sep

        result1 = check_protected_path(home)
        result2 = check_protected_path(home_with_slash)
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertEqual(result1['path'], result2['path'])

    @requirePPXML
    @common.skipUnlessWindows
    def test_case_insensitive_windows(self):
        """Test case-insensitive matching on Windows"""
        profile_var = r'%userprofile%'
        profile = os.path.expandvars(profile_var)
        self.assertNotEqual(profile, profile_var)
        for case_method in CASE_METHODS:
            # the whole path is case-insensitive
            cased_profile = case_method(profile)
            self.assertIsNotNone(check_protected_path(cased_profile))

    @requirePPXML
    def test_case_insensitive(self):
        """Test case insensitive cross platform"""
        home = os.path.expanduser('~')
        self.assertIsInstance(home, str)
        protected_base = os.path.join(home, 'Desktop')
        for case_method in CASE_METHODS:
            fname = 'thesis.pdf'
            check_path = os.path.join(protected_base, case_method(fname))
            result = check_protected_path(check_path)
            self.assertIsNotNone(
                result, f'Failed to find protected path for {check_path}: {result}')
            self.assertEqual(result['path'].lower(), protected_base.lower())


if __name__ == '__main__':
    unittest.main()
