import os
import mock

from windows.NsisUtilities import _generate_add_remove_nsis_expressions, _walk_with_filepaths, generate_files_with_nsis_expressions
from tests import common


class NsisUtilitiesTestCase(common.BleachbitTestCase):
    """Test case for module NsisUtilities"""

    def test_generate_add_remove_nsis_expressions(self):
        expected_install_expression = 'SetOutPath "$INSTDIR\\."\nFile '
        expected_uninstall_expression = 'RMDir "$INSTDIR\\."'
        
        folder0, tree = self._generate_folder_tree()
        folder0_files = tree[0][1]

        expected_install_expression += ' '.join(['"{}"'.format(file) for file in folder0_files])
        expected_install_expression += '\n'

        expected_uninstall_expression = '\n'.join(['Delete "$INSTDIR\\{}"'.format(os.path.basename(file)) for file in folder0_files]) + '\n' + expected_uninstall_expression
        
        for relpath_folder, folder_files, _ in tree[1:]:
            expected_install_expression += 'SetOutPath "$INSTDIR\\{}"\n'.format(relpath_folder)
            expected_uninstall_expression = 'RMDir "$INSTDIR\\{}"\n'.format(relpath_folder) + expected_uninstall_expression
            if folder_files:
                expected_install_expression += 'File '
                expected_install_expression += ' '.join(['"{}"'.format(file) for file in folder_files])
                expected_install_expression += '\n'
                
                folder_path = '$INSTDIR\\{}'.format(relpath_folder)
                expected_uninstall_expression =  '\n'.join([r'Delete "{}\{}"'.format(folder_path, os.path.basename(file)) for file in folder_files]) + '\n' + expected_uninstall_expression

        with mock.patch("windows.NsisUtilities._DIRECTORY_TO_WALK", folder0):
            with mock.patch("windows.NsisUtilities._DIRECTORY_PREFIX_FOR_NSIS", ''):
                actual_install_expression, actual_uninstall_expression = _generate_add_remove_nsis_expressions()

        self.assertTrue(expected_install_expression == actual_install_expression)
        self.assertTrue(expected_uninstall_expression == actual_uninstall_expression)

    def test_walk_with_filepaths(self):
        folder0, tree = self._generate_folder_tree()
        self.assertTrue(tree == list(_walk_with_filepaths(folder0)))

    def _generate_folder_tree(self):
        tree = []
        folder0 = self.mkdtemp(prefix='0')
        folder0_files = []
        file_names = []
        for i in range(2):
            file_ = self.mkstemp(dir=folder0, prefix='{}'.format(i))
            folder0_files.append(file_)
            file_names.append(os.path.basename(file_))
        tree.append(('.', folder0_files, file_names))

        for i in range(3):
            prefix = '{}'.format(i)
            folder = self.mkdtemp(dir=folder0, prefix=prefix)
            folder_files = []
            file_names = []
            for j in range(i):
                file_ = self.mkstemp(dir=folder, prefix='{}{}'.format(i, j))
                folder_files.append(file_)
                file_names.append(os.path.basename(file_))
            tree.append((os.path.relpath(folder, folder0), folder_files, file_names))
        
        return folder0, tree
    
    def test_generate_files_with_nsis_expressions(self):
        folder0, tree = self._generate_folder_tree()
        nsis_include_path = self.mkdtemp(prefix='NSIS_include')
        nsis_files_to_install_path = os.path.join(nsis_include_path, 'FilesToInstall.nsh')
        nsis_files_to_uninstall_path = os.path.join(nsis_include_path, 'FilesToUninstall.nsh')
        with mock.patch("windows.NsisUtilities._DIRECTORY_TO_WALK", folder0):
            with mock.patch("windows.NsisUtilities._DIRECTORY_PREFIX_FOR_NSIS", ''):
                with mock.patch("windows.NsisUtilities._FILES_TO_INSTALL_PATH", nsis_files_to_install_path):
                    with mock.patch("windows.NsisUtilities._FILES_TO_UNINSTALL_PATH", nsis_files_to_uninstall_path):
                        generate_files_with_nsis_expressions()
                        
        self.assertExists(nsis_include_path)
        self.assertExists(nsis_files_to_install_path)
        self.assertExists(nsis_files_to_uninstall_path)
