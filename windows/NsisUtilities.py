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


_DIRECTORY_TO_WALK = 'dist'
_DIRECTORY_TO_SEPARATE = r'dist\share\locale'
# NSIS script needs a prefix in the paths included in order to access them.
_DIRECTORY_PREFIX_FOR_NSIS = '..\\'
_FILES_TO_INSTALL_PATH = r'windows\NsisInclude\FilesToInstall.nsh'
_FILES_TO_UNINSTALL_PATH = r'windows\NsisInclude\FilesToUninstall.nsh'
_LOCALE_TO_INSTALL_PATH = r'windows\NsisInclude\LocaleToInstall.nsh'
_LOCALE_TO_UNINSTALL_PATH = r'windows\NsisInclude\LocaleToUninstall.nsh'
_REBOOTOK_FILE_EXTENSIONS = ['exe', 'pyd', 'dll']


def write_nsis_expressions_to_files():
    """Generates files containing NSIS expressions for add and remove files."""
    (install_expressions,
     uninstall_expressions) = _generate_add_remove_nsis_expressions(
         _DIRECTORY_TO_WALK, directory_to_separate=_DIRECTORY_TO_SEPARATE
    )
    (install_locale_expressions,
     uninstall_locale_expressions) = _generate_add_remove_nsis_expressions(
         _DIRECTORY_TO_SEPARATE, parent_directory=os.path.relpath(
             _DIRECTORY_TO_SEPARATE, _DIRECTORY_TO_WALK)
    )
    nsisexpressions_filename = [
        (install_expressions, _FILES_TO_INSTALL_PATH),
        (uninstall_expressions, _FILES_TO_UNINSTALL_PATH),
        (install_locale_expressions, _LOCALE_TO_INSTALL_PATH),
        (uninstall_locale_expressions, _LOCALE_TO_UNINSTALL_PATH),
    ]
    for nsis_expressions, filename in nsisexpressions_filename:
        with open(filename, 'w') as f:
            f.write(nsis_expressions)


def _generate_add_remove_nsis_expressions(directory_to_walk, parent_directory=None, directory_to_separate=None):
    """Generates NSIS expressions for copy and delete the files and folders from given folder."""
    install_expressions = ''
    uninstall_expressions = ''
    for relative_folder_path, full_filepaths, file_names in _walk_with_parent_directory_and_filepaths(directory_to_walk, directory_to_separate, parent_directory):

        install_expressions += 'SetOutPath "$INSTDIR\\{}"\n'.format(
            relative_folder_path)
        uninstall_expressions = 'RMDir "$INSTDIR\\{}"'.format(
            relative_folder_path) + '\n' + uninstall_expressions
        if full_filepaths:
            install_expressions += 'File '
            install_expressions += ' '.join(
                ['"{}{}"'.format(_DIRECTORY_PREFIX_FOR_NSIS, filepath)
                 for filepath in full_filepaths]
            )
            install_expressions += '\n'

            folder_path = '$INSTDIR' if relative_folder_path == '.' else '$INSTDIR\\{}'.format(
                relative_folder_path)
            delete_expressions = _generate_delete_expressions(
                file_names, folder_path)
            uninstall_expressions = '\n'.join(
                delete_expressions) + '\n' + uninstall_expressions

    return install_expressions, uninstall_expressions[:-1]


def _generate_delete_expressions(file_names, folder_path):
    delete_expressions = []
    for file_name in file_names:
        file_extension = os.path.splitext(file_name)[1][1:]
        reboot_ok = '/REBOOTOK ' if file_extension in _REBOOTOK_FILE_EXTENSIONS else ''
        delete_expressions.append(r'Delete {}"{}\{}"'.format(
            reboot_ok, folder_path, file_name))
    return delete_expressions


def _walk_with_parent_directory_and_filepaths(directory_to_walk, directory_to_separate=None, parent_directory=None):
    for root, _dirs, files in os.walk(directory_to_walk):
        if directory_to_separate is not None and root.startswith(directory_to_separate):
            continue
        filepaths = [os.path.join(root, file) for file in files]
        if parent_directory is not None:
            rel_directory_path = os.path.relpath(root, directory_to_walk)
            if rel_directory_path == '.':
                yield (parent_directory, filepaths, files)
            else:
                yield (
                    os.path.join(parent_directory,
                                 rel_directory_path), filepaths, files
                )
        else:
            yield (
                os.path.relpath(root, directory_to_walk), filepaths, files
            )
