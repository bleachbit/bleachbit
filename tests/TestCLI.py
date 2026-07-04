# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module CLI
"""

# standard imports
import copy
import datetime
import io
import locale
import os
import random
import tempfile
from unittest.mock import MagicMock, patch

# first party imports
import bleachbit
from bleachbit.CLI import (
    CliCallback,
    args_to_operations,
    args_to_operations_list,
    cleaners_list,
    parse_cmd_line,
    preview_or_clean,
    process_cmd_line)
from bleachbit.General import get_executable, run_external
from bleachbit.GtkShim import HAVE_GTK
from bleachbit import FileUtilities, Options, IS_WINDOWS, IS_POSIX
from tests import common

RUN_EXTERNAL_TIMEOUT = 30


class CLITestCase(common.BleachbitTestCase):
    """Test case for module CLI"""

    def setUp(self):
        super(CLITestCase, self).setUp()
        Options.options.reset_overrides()
        Options.options.set_override("first_start", False)

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
        self.assertEqual(
            pos, -1, f"Traceback found in stderr when using args {args}:\n{output[2][pos:]}")

    def test_args_to_operations_list(self):
        """Unit test for args_to_operations_list()"""
        # --preset
        Options.init_configuration()
        o = args_to_operations_list(True, False)
        self.assertEqual(o, [])
        Options.options.set_tree('system', 'tmp', True)
        o = args_to_operations_list(True, False)
        self.assertEqual(o, ['system.tmp'])

        # --all-but-warning
        o = args_to_operations_list(False, True)
        self.assertIsInstance(o, list)
        self.assertTrue('google_chrome.cache' in o)
        self.assertTrue('system.tmp' in o)
        gui_available = IS_WINDOWS or HAVE_GTK
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
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tempdir) as f:
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
        original_locale = locale.getlocale(locale.LC_NUMERIC)
        old_lang = common.get_env('LANG')
        with common.set_temporary_env('LANG', 'blahfoo'):
            # tests are run from the parent directory
            args = [get_executable(), '-m', 'bleachbit.CLI', '--version']
            output = run_external(args, timeout=RUN_EXTERNAL_TIMEOUT)
            self.assertNotEqual(output[1].find('Copyright'), -1, str(output))
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
            # deepscan.* can be too slow
            if not c.startswith('system.') and not c.startswith('deepscan.')]
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
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                filename = self.mkstemp(prefix=prefix)
                filename = os.path.normcase(filename)

                deleted_paths = []
                crash = [False]

                def dummy_delete(path, shred=False, crash=crash,
                                   deleted_paths=deleted_paths):
                    try:
                        self.assertLExists(path)
                    except AssertionError:
                        # On busy systems, other temp files may disappear
                        # between scan and delete, so flag a crash only for the
                        # test file itself.
                        if os.path.normcase(path) == os.path.normcase(filename):
                            crash[0] = True
                    deleted_paths.append(os.path.normcase(path))

                with patch.object(FileUtilities, 'delete', side_effect=dummy_delete):
                    FileUtilities.delete(filename)
                    # File exists because delete() is mocked, so real
                    # delete() was not called.
                    self.assertExists(filename)
                    operations = args_to_operations(['system.tmp'], False, False)
                    preview_or_clean(operations, True, quiet=True)

                self.assertIn(filename, deleted_paths,
                              f"{filename} not found deleted")
                os.remove(filename)
                self.assertNotExists(filename)
                self.assertFalse(crash[0], "Crash detected during deletion")

    def test_append_text(self):
        """Unit test for CliCallback.append_text() with special strings"""
        cb = CliCallback(quiet=False)
        for test_str in common.SPECIAL_TEST_STRINGS:
            # Test that append_text handles special strings without crashing
            cb.append_text(test_str + "\n")
            # Test with newlines stripped (as implementation does)
            cb.append_text(f"prefix{test_str}suffix\n")
            # Test tag parameter (ignored but should not crash)
            cb.append_text(test_str + "\n", _tag="test_tag")

    def test_return_text(self):
        """Check for correct text in output"""
        # format of tests is: args, expected_output, clean_env, env

        tests = [
            [['--help'], 'Usage: ', False, None],
            [['--version'], 'BleachBit version', True, None],
            [['--sysinfo'], 'sys.version', False, None]
        ]
        if IS_POSIX:
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

    def test_process_cmd_line_mutually_exclusive(self):
        """Unit test for process_cmd_line() with mutually exclusive commands"""
        with patch('sys.argv', ['bleachbit', '--preview', '--clean']):
            with self.assertRaises(SystemExit) as cm:
                process_cmd_line()
            self.assertEqual(cm.exception.code, 1)

    def test_process_cmd_line_version(self):
        """Unit test for process_cmd_line() with --version"""
        with patch('sys.argv', ['bleachbit', '--version']):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as cm:
                    process_cmd_line()
                self.assertEqual(cm.exception.code, 0)
            self.assertIn('BleachBit version', mock_stdout.getvalue())

    def test_process_cmd_line_list_cleaners(self):
        """Unit test for process_cmd_line() with --list-cleaners"""
        with patch('bleachbit.CLI.list_cleaners') as mock_list:
            with patch('sys.argv', ['bleachbit', '--list-cleaners']):
                with self.assertRaises(SystemExit) as cm:
                    process_cmd_line()
                self.assertEqual(cm.exception.code, 0)
            mock_list.assert_called_once()

    def test_process_cmd_line_pot(self):
        """Unit test for process_cmd_line() with --pot"""
        with patch('bleachbit.CleanerML.create_pot') as mock_create_pot:
            with patch('sys.argv', ['bleachbit', '--pot']):
                with self.assertRaises(SystemExit) as cm:
                    process_cmd_line()
                self.assertEqual(cm.exception.code, 0)
            mock_create_pot.assert_called_once()

    def test_process_cmd_line_wipe_empty_space_no_args(self):
        """Unit test for process_cmd_line() --wipe-empty-space with no args"""
        with patch('sys.argv', ['bleachbit', '--wipe-empty-space']):
            with self.assertRaises(SystemExit) as cm:
                process_cmd_line()
            self.assertEqual(cm.exception.code, 1)

    def test_process_cmd_line_preview_no_operations(self):
        """Unit test for process_cmd_line() --preview with no operations"""
        with patch('sys.argv', ['bleachbit', '--preview']):
            with self.assertRaises(SystemExit) as cm:
                process_cmd_line()
            self.assertEqual(cm.exception.code, 1)

    def test_process_cmd_line_overwrite_warning(self):
        """Unit test for process_cmd_line() --overwrite warning with --preview"""
        with patch('bleachbit.CLI.preview_or_clean'):
            with patch('bleachbit.CLI.logger.warning') as mock_warning:
                with patch('sys.argv', ['bleachbit', '--preview', 'system.tmp', '--overwrite']):
                    with self.assertRaises(SystemExit) as cm:
                        process_cmd_line()
                    self.assertEqual(cm.exception.code, 0)
                mock_warning.assert_called_once()

    def test_process_cmd_line_overwrite_no_warning_with_clean(self):
        """Unit test for process_cmd_line() --overwrite without warning when used with --clean"""
        with patch('bleachbit.CLI.preview_or_clean'):
            with patch('bleachbit.CLI.logger.warning') as mock_warning:
                with patch('sys.argv', ['bleachbit', '--clean', 'system.tmp', '--overwrite']):
                    with self.assertRaises(SystemExit) as cm:
                        process_cmd_line()
                    self.assertEqual(cm.exception.code, 0)
                mock_warning.assert_not_called()

    def test_process_cmd_line_sysinfo(self):
        """Unit test for process_cmd_line() with --sysinfo"""
        with patch('bleachbit.CLI.SystemInformation.get_system_information',
                   return_value='test sysinfo'):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                with patch('sys.argv', ['bleachbit', '--sysinfo']):
                    with self.assertRaises(SystemExit) as cm:
                        process_cmd_line()
                    self.assertEqual(cm.exception.code, 0)
            self.assertIn('test sysinfo', mock_stdout.getvalue())

    def test_process_cmd_line_shred(self):
        """Unit test for process_cmd_line() with --shred"""
        with patch.dict('bleachbit.CLI.backends', clear=True):
            with patch('bleachbit.CLI.create_simple_cleaner', return_value=MagicMock()):
                with patch('bleachbit.CLI.preview_or_clean') as mock_preview:
                    with patch('sys.argv', ['bleachbit', '--shred', '/tmp/test-shred']):
                        with self.assertRaises(SystemExit) as cm:
                            process_cmd_line()
                        self.assertEqual(cm.exception.code, 0)
                    mock_preview.assert_called_once()

    def test_process_cmd_line_gui(self):
        """Unit test for process_cmd_line() with --gui"""
        mock_gui_module = MagicMock()
        mock_app = MagicMock()
        mock_app.run.return_value = 0
        mock_gui_module.Bleachbit.return_value = mock_app
        with patch.dict('sys.modules', {'bleachbit.GuiApplication': mock_gui_module}):
            with patch.object(bleachbit, 'GuiApplication', mock_gui_module, create=True):
                with patch('bleachbit.Bootstrap.check_wayland_and_root', return_value=False):
                    with patch('os.name', 'posix'):
                        with patch('sys.argv', ['bleachbit', '--gui']):
                            with self.assertRaises(SystemExit) as cm:
                                process_cmd_line()
                            self.assertEqual(cm.exception.code, 0)
        mock_gui_module.Bleachbit.assert_called_once_with(
            uac=False, shred_paths=[], auto_exit=None)
        mock_app.run.assert_called_once()

    def test_process_cmd_line_no_command(self):
        """Unit test for process_cmd_line() with no command"""
        # Reminder: When GUI is available and there are no arguments, then
        # process_cmd_line is not called.
        # process_cmd_line() is called when either GUI is not available or
        # there are arguments.
        with patch('sys.argv', ['bleachbit']):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                process_cmd_line()
            self.assertIn('bleachbit', mock_stdout.getvalue())

    def test_process_cmd_line_debug(self):
        """Unit test for process_cmd_line() with --debug"""
        with patch('bleachbit.CLI.preview_or_clean'):
            with patch('sys.argv', ['bleachbit', '--debug', '--preview', 'system.tmp']):
                with self.assertRaises(SystemExit) as cm:
                    process_cmd_line()
                self.assertEqual(cm.exception.code, 0)
            self.assertTrue(Options.options.has_override('debug'))

    def test_process_cmd_line_preset(self):
        """Unit test for process_cmd_line() with --preset"""
        # Preset branch only calls set_root_log_level when debug is enabled.
        Options.options.set_override('debug', True)
        with patch('bleachbit.CLI.preview_or_clean'):
            with patch('bleachbit.CLI.set_root_log_level') as mock_set_level:
                with patch('sys.argv', ['bleachbit', '--preview', '--preset', 'system.tmp']):
                    with self.assertRaises(SystemExit) as cm:
                        process_cmd_line()
                    self.assertEqual(cm.exception.code, 0)
                mock_set_level.assert_called_once()

    def test_process_cmd_line_debug_log(self):
        """Unit test for process_cmd_line() with --debug-log"""
        with patch('bleachbit.CLI.preview_or_clean'):
            with patch('bleachbit.CLI.SystemInformation.get_system_information',
                       return_value='test sysinfo'):
                with patch('bleachbit.CLI.logger.info') as mock_log_info:
                    with patch('sys.argv', ['bleachbit', '--debug-log', '/tmp/test.log',
                                            '--preview', 'system.tmp']):
                        with self.assertRaises(SystemExit) as cm:
                            process_cmd_line()
                        self.assertEqual(cm.exception.code, 0)
                    mock_log_info.assert_any_call('test sysinfo')

    def test_process_cmd_line_option_overrides(self):
        """Unit test for process_cmd_line() option overrides"""
        with patch('sys.argv', ['bleachbit', '--no-load-cleaners',
                                '--no-delete-confirmation']):
            with patch('sys.stdout', new_callable=io.StringIO):
                process_cmd_line()
            self.assertFalse(Options.options.get('load_cleaners'))
            self.assertFalse(Options.options.get('delete_confirmation'))

    def test_shred(self):
        """Unit test for --shred"""
        suffixes = ['', '.', '.txt']
        dirs = ['.', self.tempdir]
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
        if not IS_WINDOWS:
            env_configs.extend([
                ['env', '-i'],  # No environment variables
                ['env', '-i', 'XDG_SESSION_TYPE=wayland']  # Mimic Wayland
            ])
        for env_prefix in env_configs:
            args = env_prefix + [get_executable(), 'bleachbit.py', '--sysinfo']
            output = run_external(args, timeout=RUN_EXTERNAL_TIMEOUT)
            if IS_POSIX and os.environ.get('USER') == 'root' and \
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
