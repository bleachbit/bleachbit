import os


# We need both constants bellow because NSIS script needs a prefix in the paths included in order to access them.
_DIRECTORY_TO_WALK = 'dist'
_DIRECTORY_PREFIX_FOR_NSIS = '..\\'
_FILES_TO_INSTALL_PATH = r'windows\NsisInclude\FilesToInstall.nsh'
_FILES_TO_UNINSTALL_PATH = r'windows\NsisInclude\FilesToUninstall.nsh'


def generate_files_with_nsis_expressions():
    """Generates pair of files containing NSIS expressions for add and remove files."""
    install_expressions, uninstall_expressions = _generate_add_remove_nsis_expressions()
    nsisexpressions_filename = [(install_expressions, _FILES_TO_INSTALL_PATH), (uninstall_expressions, _FILES_TO_UNINSTALL_PATH)]
    for nsis_expressions, filename in nsisexpressions_filename:
        with open(filename, 'w') as f:
            f.write(nsis_expressions)


def _generate_add_remove_nsis_expressions():
    """Generates NSIS expressions for copy and delete the files and folders from given folder."""  
    install_expressions = ''
    uninstall_expressions = ''
    for relative_folder_path, full_filepaths, file_names in _walk_with_filepaths(_DIRECTORY_TO_WALK):
        install_expressions += 'SetOutPath "$INSTDIR\\{}"\n'.format(relative_folder_path)
        uninstall_expressions = 'RMDir "$INSTDIR\\{}"'.format(relative_folder_path) + '\n' + uninstall_expressions
        if full_filepaths:
            install_expressions += 'File '
            install_expressions += ' '.join(['"{}{}"'.format(_DIRECTORY_PREFIX_FOR_NSIS, filepath) for filepath in full_filepaths])
            install_expressions += '\n'
            
            folder_path = '$INSTDIR' if relative_folder_path == '.' else '$INSTDIR\\{}'.format(relative_folder_path)
            uninstall_expressions = '\n'.join(['Delete "{}\\{}"'.format(folder_path, file_name) for file_name in file_names]) + '\n' + uninstall_expressions
    
    return install_expressions, uninstall_expressions[:-1]


def _walk_with_filepaths(directory_path):
    for root, dirs, files in os.walk(directory_path):
        filepaths = [os.path.join(root, file) for file in files]
        yield (os.path.relpath(root, directory_path), filepaths, files)
