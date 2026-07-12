# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module DeepScan
"""

# standard imports
import os
import shutil
import unittest
from unittest import mock

# first party imports
from tests import common
from tests import TestCleaner
from tests.common import SPECIAL_TEST_STRINGS
from bleachbit import IS_MAC, IS_WINDOWS, FS_CASE_SENSITIVE
from bleachbit.Options import options
from bleachbit.DeepScan import DeepScan, Search, normalized_walk


class DeepScanTestCase(common.BleachbitTestCase):
    """Test Case for module DeepScan"""

    def _test_encoding(self, fn):
        """Test encoding"""

        fullpath = self.write_file(fn + ".bak")

        # Add Unicode paths to encourage a crash.
        subdir = os.path.join(self.tempdir, 'ɡælɪk.dir')
        os.mkdir(subdir)
        subfile = os.path.join(subdir, 'ɡælɪk.file')
        common.touch_file(subfile)

        searches = {self.tempdir: []}
        searches[self.tempdir].append(
            Search(command='delete', regex=r'\.[Bb][Aa][Kk]$'))
        ds = DeepScan(searches)
        found = False
        for cmd in ds.scan():
            if cmd == True:
                # True is used to yield to GTK+, but it is not
                # needed in this test.
                continue
            self.assertExists(cmd.path)
            if cmd.path == fullpath:
                found = True
        self.assertTrue(found, "Did not find '%s'" % fullpath)

        os.unlink(fullpath)
        self.assertNotExists(fullpath)

        shutil.rmtree(subdir)

    def test_encoding(self):
        """Test encoding"""
        for test in SPECIAL_TEST_STRINGS:
            self._test_encoding(test)

    def test_DeepScan(self):
        """Unit test for class DeepScan.  Preview real files."""
        path = os.path.expanduser('~')
        searches = {path: []}
        for regex in ('^Makefile$', '~$', 'bak$', '^Thumbs.db$', '^Thumbs.db:encryptable$'):
            searches[path].append(Search(command='delete', regex=regex))
        ds = DeepScan(searches)
        for cmd in ds.scan():
            if True == cmd:
                # it's yielding control to the GTK idle loop
                continue
            self.assertLExists(cmd.path)

    def test_skip_whitelisted_directory(self):
        """DeepScan should not search whitelisted directories."""
        # Reminder: each test case gets a new options directory,
        # so we do not need to restore the old keep list (whitelist).
        keep_dir = self.mkdir('keep')
        search_dir = self.mkdir('search')
        keep_file = self.write_file(os.path.join(keep_dir, 'skip.bbtestbak'))
        search_file = self.write_file(os.path.join(search_dir, 'find.bbtestbak'))

        options.set_whitelist_paths([('folder', keep_dir)])
        searches = {
            self.tempdir: [
                Search(command='delete', regex=r'\.bbtestbak$')
            ]
        }
        paths = [
            cmd.path
            for cmd in DeepScan(searches).scan()
            if cmd is not True
        ]
        self.assertNotIn(keep_file, paths)
        self.assertIn(search_file, paths)

    def _get_compiled_search(self, wholeregex_substr):
        """Return the CompiledSearch for the deepscan action whose
        wholeregex contains the given substring (e.g. 'node_modules',
        'venv')."""
        import xml.etree.ElementTree as ET
        from bleachbit.DeepScan import CompiledSearch

        xml_path = os.path.join(
            os.path.dirname(__file__), '..', 'cleaners', 'deepscan.xml')
        root = ET.parse(xml_path).getroot()
        wholeregex = None
        nwholeregex = None
        for action in root.iter('action'):
            if action.get('wholeregex') and wholeregex_substr in action.get('wholeregex'):
                wholeregex = action.get('wholeregex')
                nwholeregex = action.get('nwholeregex')
                break
        self.assertIsNotNone(wholeregex)
        self.assertIsNotNone(nwholeregex)
        return CompiledSearch(Search(command='delete', wholeregex=wholeregex, nwholeregex=nwholeregex))

    def test_node_modules_excludes_dot_dirs(self):
        """node_modules option should exclude system/cache/editor directories."""
        cs = self._get_compiled_search('node_modules')
        excluded = [
            ('/home/neo/.nvm/versions/node/v22.22.3/lib/node_modules/corepack', 'README.md'),
            ('/home/trinity/.vscode/extensions/ms-python.python-2026.4.0-linux-x64/out/client/node_modules', 'sudo-prompt.js'),
            ('/home/morpheus/.npm/_npx/15b07286cbcc3329/node_modules',
             '.package-lock.json'),
            ('/home/smith/.cache/typescript/5.9/node_modules', '.package-lock.json'),
            (r'C:\Users\glados\.windsurf\extensions\ms-python.python-2026.4.0-universal\out\client\node_modules', 'unicode.js'),
            (r'C:\Users\glados\.cursor\projects\empty-window\canvases\node_modules', 'cursor.js'),
            (r'C:\Users\glados\AppData\Local\Programs\myapp\node_modules', 'file.js'),
            (r'C:\Users\glados\AppData\Local\ApertureScience\MainframeCore\node_modules\central-processing', 'index.js'),
            (r'C:\Users\Alice\AppData\Local\Programs\BeeperTexts\resources\app.asar.unpacked\node_modules\@beeper',
             'beeper_client_sdk_napi_binding.node'),
            (r'C:\Users\bob\AppData\Local\Programs\Microsoft VS Code\7e7950df89\resources\app',
             'node_modules.asar'),
            (r'C:\Users\mallory\AppData\Local\Programs\Microsoft VS Code\fcf604774b\resources\app',
             'node_modules.asar'),
            ('/home/trent/projects/important/node_modules_backup', 'README.md'),
            ('/home/trent/projects/important', 'node_modules.asar'),
            (r'C:\Users\charlie\Documents\important', 'node_modules.asar'),
            (r'C:\Users\charlie\Documents\important\node_modules_backup', 'aes.js'),
        ]
        for dirpath, filename in excluded:
            with self.subTest(dirpath=dirpath, filename=filename):
                self.assertIsNone(
                    cs.match(dirpath, filename),
                    f"Should exclude {dirpath}/{filename}")

    def test_node_modules_matches_ordinary_dirs(self):
        """node_modules option should match ordinary user project directories."""
        cs = self._get_compiled_search('node_modules')
        matched = [
            ('/home/sfalken/games/wopr/node_modules/joshua/ai', 'core.js'),
            (r'C:\Users\esnowden\Documents\nsa\prism\node_modules\crypto-js', 'aes.js'),
            (r'C:\Users\chunkylover53\Documents\work-from-home\node_modules\click-button-automator\node_modules\is-buffer', 'index.js'),
            ('/home/chunkylover53/Downloads/donut-radar/node_modules/react-dom', 'bar.js'),
        ]
        for dirpath, filename in matched:
            with self.subTest(dirpath=dirpath, filename=filename):
                self.assertIsNotNone(
                    cs.match(dirpath, filename),
                    f"Should match {dirpath}/{filename}")

    def test_venv_excludes_system_and_editor_dirs(self):
        """venv option should exclude system/cache/editor directories and non-venv paths."""
        cs = self._get_compiled_search('venv')
        excluded = [
            # venv cannot be directly under home
            ('/home/username/.venv', 'pyvenv.cfg'),
            # Python standard library venv module (not a virtual environment)
            ('/home/username/.local/share/uv/python/cpython-3.12.11-linux-x86_64-gnu/lib/python3.12/venv',
             '__init__.py'),
            ('/home/username/.pyenv/versions/3.12.7/lib/python3.12/venv', '__init__.py'),
            # pipx-managed venvs (managed by pipx, like npm cache)
            ('/home/username/.local/share/pipx/venvs/duplicity', 'pyvenv.cfg'),
            # typeshed stubs bundled with editor extensions
            ('/home/username/.vscode/extensions/ms-python.python-2026.4.0-linux-x64/python_files/lib/jedilsp/jedi/third_party/typeshed/stdlib/3/venv',
             '__init__.pyi'),
            # pyenv build patches
            ('/home/username/.pyenv/plugins/python-build/share/python-build/patches/3.5.2/Python-3.5.2',
             'venv.patch'),
            # Windows: editor extensions and AppData
            (r'C:\Users\glados\.vscode\extensions\ms-python.python-2026.4.0-universal\python_files\lib\jedilsp\jedi\third_party\typeshed\stdlib\3\venv',
             '__init__.pyi'),
            (r'C:\Users\glados\AppData\Local\ApertureScience\MainframeCore\venv', 'pyvenv.cfg'),
            # Files/directories that contain venv (but not a venv directory)
            ('/home/aturing/npl/ace_project/tools/', 'bootstrap_ace_venv.sh'),
            ('/home/vonneumann/edvac/logs/', 'venv_build.log'),
            ('/home/aturing/npl/ace_project/venv_tools/',
             'requirements_numerics.txt'),
            (r'C:\Users\charlie\Documents\important\venv_backup', 'pyvenv.cfg'),
            # .venv bundled inside an AppData\Local application directory
            (r'C:\Users\charlie\AppData\Local\AnkiProgramFiles\.venv\Lib\site-packages\PyQt6',
             'QtCore.pyd'),
            # Python standard library venv module under uv-managed Python (Windows)
            (r'C:\Users\charlie\AppData\Roaming\uv\python\cpython-3.13.5-windows-x86_64-none\Lib\venv',
             '__main__.py'),
        ]
        if IS_WINDOWS:
            # Windows is case insensitive
            # venv cannot be directly under home
            excluded.append((r'c:\users\username\.VENV', 'pyvenv.cfg'))
        for dirpath, filename in excluded:
            with self.subTest(dirpath=dirpath, filename=filename):
                self.assertIsNone(
                    cs.match(dirpath, filename),
                    f"Should exclude {dirpath}/{filename}")

    def test_venv_matches_ordinary_dirs(self):
        """venv option should match ordinary user project virtual environments."""
        cs = self._get_compiled_search('venv')
        matched = [
            ('/home/genisys/t800/.venv/yolo-v666', 'pyvenv.cfg'),
            ('/home/stark/jarvis/venv/yolo14', 'pyvenv.cfg'),
            (r'C:\Users\esnowden\Documents\nsa\prism\venv', 'pyvenv.cfg'),
        ]
        if IS_WINDOWS:
            # case insensitive
            matched.append(
                (r'C:\USERS\esnowden\Documents\nsa\prism\.VENV', 'pyvenv.cfg'))
            matched.append(
                (r'c:\USERS\pinky\world_domination\VENV\site-packages\hypnosisis', '__init__.py'))
        for dirpath, filename in matched:
            with self.subTest(dirpath=dirpath, filename=filename):
                self.assertIsNotNone(
                    cs.match(dirpath, filename),
                    f"Should match {dirpath}/{filename}")

    def _test_delete(self, command):
        """Delete files in a test environment"""

        # make some files
        f_del = self.write_file('foo.txt.bbtestbak')
        f_keep = self.write_file('foo.txt')
        subdir = os.path.join(self.tempdir, 'sub')
        os.mkdir(subdir)
        f_del2 = self.write_file(os.path.join(subdir, 'bar.ini.bbtestbak'))
        f_del3 = self.write_file(os.path.join(subdir, 'bar.ini.bbtestBAK'))

        # sanity check
        self.assertExists(f_del)
        self.assertExists(f_keep)
        self.assertExists(f_del2)

        # run deep scan
        def run_deep_scan(regex):
            astr = '<action command="{}" search="deep" cache="false" path="{}" {}/>'.format(
                command, self.tempdir, regex)
            cleaner = TestCleaner.action_to_cleaner(astr)
            from bleachbit.Worker import backends, Worker
            backends['test'] = cleaner
            operations = {'test': ['option1']}
            from bleachbit import CLI
            ui = CLI.CliCallback()
            worker = Worker(ui, True, operations)
            list(worker.run())
            del backends['test']

        # validate results
        run_deep_scan(r'regex="\.bbtestbak$" wholeregex="sub.*\.bbtestbak$"')
        self.assertExists(f_del)
        self.assertExists(f_keep)
        self.assertFalse(os.path.exists(f_del2))
        if FS_CASE_SENSITIVE:
            self.assertExists(f_del3)
        else:
            self.assertFalse(os.path.exists(f_del3))

        # validate results
        run_deep_scan(r'regex="\.bbtestbak$"')
        self.assertFalse(os.path.exists(f_del))
        self.assertExists(f_keep)

        # cleanup
        os.unlink(f_keep)
        if FS_CASE_SENSITIVE:
            os.unlink(f_del3)
        os.rmdir(subdir)

    def test_delete(self):
        self._test_delete('delete')

    def test_shred(self):
        self._test_delete('shred')

    @unittest.skipUnless(IS_MAC, 'Not on Darwin')
    def test_normalized_walk_darwin(self):

        with mock.patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/foo', ('bar',), ['ba\u0300z']),
                ('/foo/bar', (), ['spam', 'eggs']),
            ]
            with mock.patch('platform.system') as mock_platform_system:
                mock_platform_system.return_value = 'Darwin'
                self.assertEqual(list(normalized_walk('.')), [
                    ('/foo', ('bar',), ['b\u00e0z']),
                    ('/foo/bar', (), ['spam', 'eggs']),
                ])

        with mock.patch('os.walk') as mock_walk:
            expected = [
                ('/foo', ('bar',), ['baz']),
                ('/foo/bar', (), ['spam', 'eggs']),
            ]
            mock_walk.return_value = expected
            self.assertEqual(list(normalized_walk('.')), expected)
