#!/usr/bin/python3
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


import os
import mock

from windows.NsisUtilities import (_generate_add_remove_nsis_expressions,
                                   _walk_with_parent_directory_and_filepaths,
                                   write_nsis_expressions_to_files,
                                   _REBOOTOK_FILE_EXTENSIONS,
                                   _generate_delete_expressions)
from tests import common


@common.skipUnlessWindows
class NsisUtilitiesTestCase(common.BleachbitTestCase):
    """Test case for module NsisUtilities"""

    _os_walk_original = os.walk

    def setUp(self):
        # We need to sort the files in order to compare them correctly
        self._patcher = mock.patch('os.walk')
        self._patcher.start()
        os.walk.side_effect = self._walk_with_sorted_files

    def test_generate_add_remove_nsis_expressions(self):
        folder0, tree = self._generate_folder_tree()
        (expected_install_expression, expected_uninstall_expression,
         expected_install_separate_folder_expression,
         expected_uninstall_separate_folder_expression) = self._generate_nsis_expressions(tree)

        import windows
        with mock.patch.multiple(
                'windows.NsisUtilities',
                _DIRECTORY_TO_WALK=folder0,
                _DIRECTORY_PREFIX_FOR_NSIS='',
                _DIRECTORY_TO_SEPARATE=os.path.join(folder0, tree[-2][0])
        ):
            (actual_install_expression,
             actual_uninstall_expression) = _generate_add_remove_nsis_expressions(
                windows.NsisUtilities._DIRECTORY_TO_WALK,
                None,
                windows.NsisUtilities._DIRECTORY_TO_SEPARATE)
            (actual_install_separate_folder_expression,
             actual_uninstall_separate_folder_expression) = _generate_add_remove_nsis_expressions(
                windows.NsisUtilities._DIRECTORY_TO_SEPARATE,
                os.path.relpath(windows.NsisUtilities._DIRECTORY_TO_SEPARATE, windows.NsisUtilities._DIRECTORY_TO_WALK))

        self.assertEqual(self._sort_string_by_lines(expected_install_expression),
                         self._sort_string_by_lines(actual_install_expression))
        self.assertEqual(self._sort_string_by_lines(expected_uninstall_expression),
                         self._sort_string_by_lines(actual_uninstall_expression))
        self.assertEqual(self._sort_string_by_lines(expected_install_separate_folder_expression),
                         self._sort_string_by_lines(actual_install_separate_folder_expression))
        self.assertEqual(self._sort_string_by_lines(expected_uninstall_separate_folder_expression),
                         self._sort_string_by_lines(actual_uninstall_separate_folder_expression))

    def _generate_nsis_expressions(self, tree):
        expected_install_expression = '{}\n'.format(
            self._generate_setoutpath_expression('$INSTDIR', '.'))
        expected_uninstall_expression = self._generate_rmdir_expression(
            '$INSTDIR', '.')

        folder0_files = tree[0][1]
        file_names = tree[0][2]

        expected_install_expression += self._generate_install_file_expression(
            folder0_files)
        expected_install_expression += '\n'
        expected_uninstall_expression = '{}\n{}'.format(
            self._generate_delete_expressions('$INSTDIR', file_names),
            expected_uninstall_expression
        )
        expected_install_expression, expected_uninstall_expression = self._generate_nsis_expressions_helper(
            '$INSTDIR', tree[1:-2], expected_install_expression, expected_uninstall_expression)

        expected_install_separate_folder_expression = ''
        expected_uninstall_separate_folder_expression = ''
        (expected_install_separate_folder_expression,
         expected_uninstall_separate_folder_expression) = self._generate_nsis_expressions_helper(
            '$INSTDIR', tree[-2:], expected_install_separate_folder_expression,
            expected_uninstall_separate_folder_expression)

        return (expected_install_expression, expected_uninstall_expression,
                expected_install_separate_folder_expression, expected_uninstall_separate_folder_expression)

    def _generate_nsis_expressions_helper(self, target_dir, tree, expected_install_expression,
                                          expected_uninstall_expression):
        for relpath_folder, folder_files, file_names in tree:
            expected_install_expression += '{}\n'.format(
                self._generate_setoutpath_expression(target_dir, relpath_folder))
            if expected_uninstall_expression:
                expected_uninstall_expression = '{}\n{}'.format(
                    self._generate_rmdir_expression(
                        target_dir, relpath_folder),
                    expected_uninstall_expression
                )
            else:
                expected_uninstall_expression = self._generate_rmdir_expression(
                    target_dir, relpath_folder)
            if folder_files:
                expected_install_expression += '{}\n'.format(
                    self._generate_install_file_expression(folder_files))

                folder_path = r'{}\{}'.format(target_dir, relpath_folder)
                expected_uninstall_expression = '{}\n{}'.format(
                    self._generate_delete_expressions(folder_path, file_names),
                    expected_uninstall_expression
                )
        return expected_install_expression, expected_uninstall_expression

    def test_walk_with_parent_directory_and_filepaths(self):
        folder0, tree = self._generate_folder_tree()
        self.assertEqual(sorted(tree), sorted(
            list(_walk_with_parent_directory_and_filepaths(folder0))))

    def test_write_nsis_expressions_to_files(self):
        folder0, tree = self._generate_folder_tree()
        (expected_install_expression,
         expected_uninstall_expression,
         expected_install_separate_folder_expression,
         expected_uninstall_separate_folder_expression) = self._generate_nsis_expressions(tree)

        nsis_include_path = self.mkdtemp(prefix='NSIS_include')

        class NSISFilePathAndExpressions:
            def __init__(self, filename, nsis_expressions):
                self.filepath = os.path.join(nsis_include_path, filename)
                self.nsis_expressions = nsis_expressions

        files_to_install = NSISFilePathAndExpressions(
            'FilesToInstall.nsh', expected_install_expression)
        files_to_uninstall = NSISFilePathAndExpressions(
            'FilesToUninstall.nsh', expected_uninstall_expression)
        separate_folder_to_install = NSISFilePathAndExpressions(
            'LocaleToInstall.nsh', expected_install_separate_folder_expression)
        separate_folder_to_uninstall = NSISFilePathAndExpressions(
            'LocaleToUninstall.nsh', expected_uninstall_separate_folder_expression)

        nsis_files = [files_to_install, files_to_uninstall,
                      separate_folder_to_install, separate_folder_to_uninstall]

        with mock.patch.multiple(
                "windows.NsisUtilities",
                _DIRECTORY_TO_WALK=folder0,
                _DIRECTORY_PREFIX_FOR_NSIS='',
                _DIRECTORY_TO_SEPARATE=os.path.join(folder0, tree[-2][0]),
                _FILES_TO_INSTALL_PATH=files_to_install.filepath,
                _FILES_TO_UNINSTALL_PATH=files_to_uninstall.filepath,
                _LOCALE_TO_INSTALL_PATH=separate_folder_to_install.filepath,
                _LOCALE_TO_UNINSTALL_PATH=separate_folder_to_uninstall.filepath
        ):
            write_nsis_expressions_to_files()

        for nsis_file in nsis_files:
            self.assertExists(nsis_file.filepath)
            with open(nsis_file.filepath) as f:
                file_content = f.read()
                self.assertEqual(self._sort_string_by_lines(file_content),
                                 self._sort_string_by_lines(nsis_file.nsis_expressions))

    def test_generate_delete_expressions(self):
        file_names = ['aaa']
        file_names.extend(['{}.{}'.format('ddd', ext)
                           for ext in _REBOOTOK_FILE_EXTENSIONS])
        file_names.extend(['bbb', 'ccc'])
        folder_path = r'rrr\rr'
        exprected_delete_expressions = [
            r'Delete "rrr\rr\aaa"',
            r'Delete /REBOOTOK "rrr\rr\ddd.{}"'.format(
                _REBOOTOK_FILE_EXTENSIONS[0]),
            r'Delete /REBOOTOK "rrr\rr\ddd.{}"'.format(
                _REBOOTOK_FILE_EXTENSIONS[1]),
            r'Delete /REBOOTOK "rrr\rr\ddd.{}"'.format(
                _REBOOTOK_FILE_EXTENSIONS[2]),
            r'Delete "rrr\rr\bbb"',
            r'Delete "rrr\rr\ccc"',
        ]
        actual_delete_expressions = _generate_delete_expressions(
            file_names, folder_path)
        self.assertEqual(exprected_delete_expressions,
                         actual_delete_expressions)

    @classmethod
    def _walk_with_sorted_files(cls, top, topdown=True, onerror=None, followlinks=False):
        for root, dirs, files in cls._os_walk_original(top):
            yield root, dirs, sorted(files)

    def _generate_folder_tree(self):
        def create_files(number_of_files, in_folder, filename_prefix='', filename_suffixes=None):
            folder_files = []
            file_names = []
            for i in range(number_of_files):
                try:
                    suffix = '.{}'.format(filename_suffixes[i])
                except:
                    suffix = ''
                file_ = self.mkstemp(
                    dir=in_folder,
                    suffix=suffix,
                    prefix='{}{}'.format(filename_prefix, i)
                )
                folder_files.append(file_)
                file_names.append(os.path.basename(file_))
            return folder_files, file_names

        # make outermost folder with two files
        tree = []
        folder0 = self.mkdtemp(prefix='0')
        folder_files, file_names = create_files(
            len(_REBOOTOK_FILE_EXTENSIONS),
            folder0,
            filename_suffixes=_REBOOTOK_FILE_EXTENSIONS
        )
        tree.append(('.', folder_files, file_names))

        # make three subfolders with 0, 1 and 2 files in them respectively
        for i in range(3):
            folder = self.mkdtemp(dir=folder0, prefix=str(i))
            folder_files, file_names = create_files(i, folder, i)
            tree.append((os.path.relpath(folder, folder0),
                         folder_files, file_names))

        # in the last subfolder create a subfolder with files
        folder = self.mkdtemp(dir=folder, prefix='20')
        tree.append((os.path.relpath(folder, folder0), [], []))
        folder = self.mkdtemp(dir=folder, prefix='200')
        folder_files, file_names = create_files(3, folder, '200')
        tree.append((os.path.relpath(folder, folder0),
                     folder_files, file_names))

        return folder0, tree

    @classmethod
    def _sort_string_by_lines(cls, string):
        return sorted(string.split('\n'))

    @classmethod
    def _generate_install_file_expression(cls, files):
        files_as_strings = ' '.join(['"{}"'.format(file) for file in files])
        return 'File {}'.format(files_as_strings)

    @classmethod
    def _generate_delete_expressions(cls, folder, files):
        result = []
        for file in files:
            file_extension = os.path.splitext(file)[1][1:]
            reboot_ok = ''
            if file_extension in _REBOOTOK_FILE_EXTENSIONS:
                reboot_ok = '/REBOOTOK '
            result.append(r'Delete {}"{}\{}"'.format(reboot_ok, folder, file))
        return '\n'.join(result)

    @classmethod
    def _generate_setoutpath_expression(cls, dir, subdir):
        return cls._generate_dir_subdir_expression('SetOutPath', dir, subdir)

    @classmethod
    def _generate_rmdir_expression(cls, dir, subdir):
        return cls._generate_dir_subdir_expression('RMDir', dir, subdir)

    @classmethod
    def _generate_dir_subdir_expression(cls, command, dir, subdir):
        return r'{} "{}\{}"'.format(command, dir, subdir)

    def tearDown(self):
        self._patcher.stop()
