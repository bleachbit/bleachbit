# vim: ts=4:sw=4:expandtab

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
Test case for module CLI
"""

from bleachbit.CLI import (
    args_to_operations,
    args_to_operations_list,
    cleaners_list,
    parse_cmd_line,
    preview_or_clean)
from bleachbit.General import get_executable, run_external
from bleachbit.GtkShim import HAVE_GTK
from bleachbit import FileUtilities
from tests import common

import copy
import datetime
import os
import tempfile

RUN_EXTERNAL_TIMEOUT = 30


class CLITestCase(common.BleachbitTestCase):
    """Test case for module CLI"""

    def setUp(self):
        super(CLITestCase, self).setUp()

    def _test_preview(self, args, redirect_stdout=True, env=None):
        """Helper to test preview"""
        # Use devnull because in some cases the buffer will be too large,
        # and the other alternative, the screen, is not desirable.
        with open(os.devnull, 'w') as stdout:
            if not redirect_stdout:
                stdout = None
            output = run_external(args, stdout=stdout,
                                  env=env, timeout=RUN_EXTERNAL_TIMEOUT)
        self.assertEqual(output[0], 0, "Return code = %d, stderr='%s'"
                         % (output[0], output[2]))
        pos = output[2].find('Traceback (most recent call last)')
        if pos > -1:
            print("Saw the following error when using args '%s':\n %s" %
                  (args, output[2]))
        self.assertEqual(pos, -1)

    def test_args_to_operations_list(self):
        """Unit test for args_to_operations_list()"""
        # --preset
        import bleachbit.Options
        bleachbit.Options.init_configuration()
        o = args_to_operations_list(True, False)
        self.assertEqual(o, [])
        bleachbit.Options.options.set_tree('system', 'tmp', True)
        o = args_to_operations_list(True, False)
        self.assertEqual(o, ['system.tmp'])

        # --all-but-warning
        o = args_to_operations_list(False, True)
        self.assertIsInstance(o, list)
        self.assertTrue('google_chrome.cache' in o)
        self.assertTrue('system.tmp' in o)
        gui_available = os.name == 'nt' or HAVE_GTK
        self.assertEqual(gui_available, 'system.clipboard' in o)
        self.assertFalse('system.empty_space' in o)
        self.assertFalse('system.memory' in o)

    def test_args_to_operations(self):
        """Unit test for args_to_operations()"""
        # test explicit cleaners (without --preset or --all-but-warning)
        tests = (
            (['adobe_reader.*'], [],
             {'adobe_reader': ['cache', 'mru', 'tmp']}),
            (['adobe_reader.mru'], [], {'adobe_reader': ['mru']}),
            (['adobe_reader.*'], ['adobe_reader.cache'],
             {'adobe_reader': ['mru', 'tmp']}))
        for test_args, excludes, expected in tests:
            o = args_to_operations(test_args, False, False, excludes)
            self.assertIsInstance(o, dict)
            self.assertEqual(o, expected)

        # Test failure on wildcard
        with self.assertRaises(SystemExit) as cm:
            args_to_operations(
                ['adobe_reader.mru'], False, False, ['adobe_reader.*'])
        self.assertEqual(cm.exception.code, 1)

    def test_parse_cmd_line_except(self):
        """Unit test for parse_cmd_line() --except handling"""
        tests = (
            (['--clean', 'firefox.*', 'chromium.*',
              '--except', 'firefox.passwords,chromium.passwords'],
             ['firefox.*', 'chromium.*'],
             ['firefox.passwords', 'chromium.passwords']),
            (['--clean', 'firefox.*', 'chromium.*',
              '--except', 'firefox.passwords',
              '--except', 'chromium.passwords'],
             ['firefox.*', 'chromium.*'],
             ['firefox.passwords', 'chromium.passwords']),
            (['--clean', 'chromium.*',
              '--except', 'firefox.passwords',
              'firefox.*',
              '--except', 'chromium.passwords'],
             ['chromium.*', 'firefox.*'],
             ['firefox.passwords', 'chromium.passwords']))
        for argv, expected_args, expected_excludes in tests:
            _parser, options, args, excludes = parse_cmd_line(argv)
            self.assertTrue(options.clean)
            self.assertEqual(expected_args, args)
            self.assertEqual(expected_excludes, excludes)

    def test_cleaners_list(self):
        """Unit test for cleaners_list()"""
        for cleaner in cleaners_list():
            self.assertIsString(cleaner)

    def test_debug_log(self):
        """Unit test for --debug-log option"""

        # These texts are required in the log file.
        file_required_texts = [
            'DEBUG - Debug log file initialized',
            'ERROR - Failed to clean',
            'KeyError',
            'doesnot'
        ]

        # These texts are forbidden in stderr.
        stderror_forbidden_texts = [
            'bleachbit.CLI',
            'bleachbit.CleanerML',
            'ERROR',
            'DEBUG',
            datetime.datetime.now().strftime('%Y-%m-%d')
        ]

        for delimiter in (' ', '='):
            # delete_on_close=False is helpful but requires Python 3.12.
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.close()
                log_path = f.name

                # 'bleachbit.py' is used instead of '-m bleachbit.CLI'
                args = [get_executable(), 'bleachbit.py', '--preview', 'doesnot.exist',
                        '--debug'] + f'--debug-log{delimiter}{log_path}'.split(delimiter)
                (rc, _stdout, stderr) = run_external(
                    args, stdout=None, timeout=RUN_EXTERNAL_TIMEOUT)
                self.assertEqual(0, rc, f"rc={rc}, stderr={stderr}")
                self.assertExists(log_path)
                with open(log_path, 'r', encoding='utf-8') as log_file:
                    log_content = log_file.read()

                self.assertEqual(1, stderr.count('Traceback'))
                self.assertEqual(1, log_content.count(
                    'Traceback'), log_content)

                for stderr_forbidden_text in stderror_forbidden_texts:
                    self.assertNotIn(stderr_forbidden_text, stderr,
                                     f"The text '{stderr_forbidden_text}' was found in stderr")

                for required_text in file_required_texts:
                    self.assertIn(required_text, log_content,
                                  f"The text '{required_text}' was not found in the log file")
            os.remove(log_path)
            self.assertNotExists(log_path)

    @common.skipIfWindows
    def test_encoding(self):
        """Unit test for encoding"""

        filename = self.write_file(
            '/tmp/bleachbit-test-cli-encoding-\xe4\xf6\xfc~')
        # not assertExists because it doesn't cope with invalid encodings
        self.assertTrue(os.path.exists(filename))

        env = copy.deepcopy(os.environ)
        env['LANG'] = 'en_US'  # not UTF-8
        args = [get_executable(), '-m', 'bleachbit.CLI', '-p', 'system.tmp']
        # If Python pipes stdout to file or devnull, the test may give
        # a false negative.  It must print stdout to terminal.
        self._test_preview(args, redirect_stdout=False, env=env)

        os.remove(filename)
        self.assertNotExists(filename)

    def test_invalid_locale(self):
        """Unit test for invalid locales"""
        import locale
        original_locale = locale.getlocale(locale.LC_NUMERIC)
        old_lang = common.get_env('LANG')
        common.put_env('LANG', 'blahfoo')
        # tests are run from the parent directory
        args = [get_executable(), '-m', 'bleachbit.CLI', '--version']
        output = run_external(args, timeout=RUN_EXTERNAL_TIMEOUT)
        self.assertNotEqual(output[1].find('Copyright'), -1, str(output))
        common.put_env('LANG', old_lang)
        self.assertEqual(common.get_env('LANG'), old_lang)
        self.assertEqual(locale.getlocale(locale.LC_NUMERIC), original_locale)

    def test_preview(self):
        """Unit test for --preview option"""
        env = copy.deepcopy(os.environ)
        # the language and encoding affect the test results
        env['LANG'] = 'en_US.UTF-8'
        env['PYTHONIOENCODING'] = 'utf-8:backslashreplace'
        args_list = []
        module = 'bleachbit.CLI'
        big_args = [get_executable(), '-m', module, '--preview', ]
        # The full list can take a long time and generally does not improve the testing,
        # so test a subset.
        full_cleaners_list = list(cleaners_list())
        system_cleaners = [
            c for c in full_cleaners_list if c.startswith('system.')]
        if 'system.clipboard' in system_cleaners:
            # Fix error on GitHub Actions
            # FIXME: do conditional removal
            system_cleaners.remove('system.clipboard')
        non_system_cleaners = [
            c for c in full_cleaners_list
            # vim_swap_root walks / and can be very slow
            if not c.startswith('system.') and c != 'deepscan.vim_swap_root']
        import random
        sample_cleaners = random.sample(non_system_cleaners, 5)
        for cleaner in (system_cleaners + sample_cleaners):
            args_list.append(
                [get_executable(), '-m', module, '--preview', cleaner])
            big_args.append(cleaner)
        args_list.append(big_args)
        for args in args_list:
            self._test_preview(args, env=env)

    def test_delete(self):
        """Unit test for --delete option"""
        prefixes = [
            'bleachbit-test-cli-delete',
            '\x8b\x8b-bad-encoding'
        ]
        for i in range(len(prefixes)):

            filename = self.mkstemp(prefix=prefixes[i])
            if 'nt' == os.name:
                filename = os.path.normcase(filename)
            # replace delete function for testing
            save_delete = FileUtilities.delete

            deleted_paths = []
            crash = [False]

            def dummy_delete(path, shred=False):
                try:
                    self.assertExists(path)
                except:
                    crash[0] = True

                deleted_paths.append(os.path.normcase(path))

            FileUtilities.delete = dummy_delete
            FileUtilities.delete(filename)
            self.assertExists(filename)
            operations = args_to_operations(['system.tmp'], False, False)
            preview_or_clean(operations, True, quiet=True)
            FileUtilities.delete = save_delete
            self.assertIn(filename, deleted_paths,
                          "%s not found deleted" % filename)
            os.remove(filename)
            self.assertNotExists(filename)
            self.assertFalse(crash[0])

    def test_return_text(self):
        """Check for correct text in output"""
        # format of tests is: args, expected_output, clean_env, env

        tests = [
            [['--help'], 'Usage: ', False, None],
            [['--version'], 'BleachBit version', True, None],
            [['--sysinfo'], 'sys.version', False, None]
        ]
        if os.name == 'posix':
            # GUI is not available with clean environment on POSIX.
            tests.append([['--help'], 'Usage: ', True, None])
            # Force detection of Wayland
            wayland_env = os.environ.copy()
            wayland_env['XDG_SESSION_TYPE'] = 'wayland'
            tests.append([['--sysinfo'], 'sys.version', False, wayland_env])

        for args, expected_output, clean_env, env in tests:
            launcher_output = {}
            for i, launcher in enumerate([['bleachbit.py'], ['-m', 'bleachbit.CLI']]):
                direct_args = [get_executable(),] + launcher + args
                output = run_external(
                    direct_args, env=env, clean_env=clean_env, timeout=RUN_EXTERNAL_TIMEOUT)
                self.assertEqual(output[0], 0, output)
                self.assertIn(expected_output, output[1])
                modified_output_str = output[1].replace(
                    'CLI.py', 'bleachbit.py')
                launcher_output[i] = [line for line in modified_output_str.split(
                    '\n') if not line.startswith("sys.argv")]
            self.assertEqual(launcher_output[0], launcher_output[1])

    def test_shred(self):
        """Unit test for --shred"""
        suffixes = ['', '.', '.txt']
        dirs = ['.', None]
        for dir_ in dirs:
            for suffix in suffixes:
                (fd, filename) = tempfile.mkstemp(
                    prefix='bleachbit-test-cli-shred', suffix=suffix, dir=dir_)
                os.close(fd)
                if '.' == dir_:
                    filename = os.path.basename(filename)
                # not assertExists because something strange happens on Windows
                self.assertTrue(os.path.exists(filename))
                args = [get_executable(), '-m',
                        'bleachbit.CLI', '--shred', filename]
                output = run_external(args, timeout=RUN_EXTERNAL_TIMEOUT)
                self.assertEqual(output[0], 0)
                self.assertNotExists(filename)

    @common.also_with_sudo
    def test_sysinfo(self):
        """Unit test for --sysinfo

        By not using `-m bleachbit.CLI`, this exercises `./bleachbit.py`.
        """
        env_configs = [[]]
        if os.name != 'nt':
            env_configs.extend([
                ['env', '-i'],  # No environment variables
                ['env', '-i', 'XDG_SESSION_TYPE=wayland']  # Mimic Wayland
            ])
        for env_prefix in env_configs:
            args = env_prefix + [get_executable(), 'bleachbit.py', '--sysinfo']
            output = run_external(args, timeout=RUN_EXTERNAL_TIMEOUT)
            if os.name == 'posix' and os.environ.get('USER') == 'root' and \
                    output[0] == 1:
                continue
            self.assertEqual(output[0], 0, output)
            self.assertIn('sys.version', output[1])
            # FIXME: verify that there is not a message like
            # (bleachbit.py:1234): Gdk-CRITICAL **: 23:05:08.581: gdk_screen_get_root_window: assertion 'GDK_IS_SCREEN (screen)' failed

    @common.skipUnlessWindows
    def test_gui_exit(self):
        """Unit test for --gui --exit, only for Windows"""
        args = (get_executable(), '-m',
                'bleachbit.CLI', '--gui', '--exit')
        (rc, _stdout, stderr) = run_external(
            args, timeout=RUN_EXTERNAL_TIMEOUT)
        self.assertNotIn('no such option', stderr)
        self.assertNotIn('Usage: CLI.py', stderr)
        self.assertEqual(rc, 0)
        # Is the application still running?
        opened_windows_titles = common.get_opened_windows_titles()
        self.assertFalse('BleachBit' in opened_windows_titles)
