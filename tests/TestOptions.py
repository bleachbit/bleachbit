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
Test case for module Options
"""

import errno
import os
from unittest import mock

from tests import common
import bleachbit.Options
from bleachbit.Options import _option_index
from bleachbit.Log import is_debugging_enabled_via_cli


class FakeTimer:
    """Fake timer to replace threading.Timer"""
    instances = []

    def __init__(self, interval, function, args=(), kwargs=None):
        """Init the fake timer"""
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        self.daemon = False
        self.started = False
        self.cancelled = False
        self.__class__.instances.append(self)

    def cancel(self):
        """Cancel the fake timer."""
        self.cancelled = True

    def fire(self):
        """Fire the fake timer."""
        if not self.cancelled:
            self.function(*self.args, **self.kwargs)

    def start(self):
        """Start the fake timer."""
        self.started = True


class OptionsTestCase(common.BleachbitTestCase):
    """Test case for class Options"""

    def _write_seed_options_file(self):
        """Write a seed options file for testing"""
        with open(bleachbit.options_file, 'w', encoding='utf-8-sig') as handle:
            handle.write(f'''[bleachbit]
version={bleachbit.APP_VERSION}
shred=False
check_online_updates=True
[hashpath]
[list/shred_drives]
''')

    def test_option_index(self):
        """Unit test for _option_index"""
        self.assertEqual(_option_index('0'), 0)
        self.assertEqual(_option_index('3'), 3)
        self.assertEqual(_option_index('1_type'), 1)
        self.assertEqual(_option_index('2_path'), 2)

    def test_Options(self):
        """Unit test for class Options"""
        o = bleachbit.Options.options
        value = o.get("check_online_updates")

        # toggle a boolean
        o.toggle('check_online_updates')
        self.assertEqual(not value, o.get("check_online_updates"))

        # restore original boolean
        o.set("check_online_updates", value)
        self.assertEqual(value, o.get("check_online_updates"))

        # test delayed commit
        shred = o.get("shred")
        o.set("shred", not shred)
        self.assertEqual(not shred, o.get("shred"))

        o.restore()  # abandon uncommitted changes
        self.assertEqual(shred, o.get("shred"))

        o.set("shred", shred)
        o.close()  # commit
        self.assertEqual(shred, o.get("shred"))

        # try a list
        list_values = ['a', 'b', 'c']
        o.set_list("list_test", list_values)
        self.assertEqual(list_values, o.get_list("list_test"))

        # these should always be set
        for bkey in bleachbit.Options.boolean_keys:
            self.assertIsInstance(o.get(bkey), bool)

        # language
        value = o.get_language('en')
        self.assertIsInstance(value, bool)
        o.set_language('en', True)
        self.assertTrue(o.get_language('en'))
        o.set_language('en', False)
        self.assertFalse(o.get_language('en'))
        o.set_language('en', value)

        # tree
        o.set_tree("parent", "child", True)
        self.assertTrue(o.get_tree("parent", "child"))
        o.set_tree("parent", "child", False)
        self.assertFalse(o.get_tree("parent", "child"))
        o.config.remove_option("tree", "parent.child")
        self.assertFalse(o.get_tree("parent", "child"))

    def test_keep_list(self):
        """Test for get_whitelist_paths() / set_whitelist_paths()"""
        o = bleachbit.Options.options
        # FIXME: finish renaming whitelist to keep list
        self.assertIsInstance(o.get_whitelist_paths(), list)
        keep_list = [('file', '/home/foo'), ('folder', '/home'),
                     ('file', '/home/unicode/кодирование')]
        old_keep_list = o.get_whitelist_paths()
        o.config.remove_section('whitelist/paths')
        self.assertIsInstance(o.get_whitelist_paths(), list)
        self.assertEqual(o.get_whitelist_paths(), [])
        o.set_whitelist_paths(keep_list)
        self.assertIsInstance(o.get_whitelist_paths(), list)
        self.assertEqual(set(keep_list), set(o.get_whitelist_paths()))
        o.set_whitelist_paths(old_keep_list)
        o.close()
        self.assertEqual(set(old_keep_list), set(o.get_whitelist_paths()))

    def test_init_configuration(self):
        """Test for init_configuration()"""
        if os.path.exists(bleachbit.options_file):
            os.remove(bleachbit.options_file)
        self.assertNotExists(bleachbit.options_file)
        bleachbit.Options.init_configuration()
        self.assertExists(bleachbit.options_file)

    def test_is_corrupt(self):
        """Test is_corrupt()"""
        def _test_is_corrupt(contents, expect_is_corrupt):
            with open(bleachbit.options_file, 'w', encoding='utf-8-sig') as f:
                f.write(contents)
            o = bleachbit.Options.Options()
            self.assertEqual(o.is_corrupt(), expect_is_corrupt)

        # test blank
        _test_is_corrupt('', False)
        _test_is_corrupt('[bleachbit]\n', False)

        # test valid but non-standard boolean
        _test_is_corrupt('[bleachbit]\nshred=f\n', False)

        # test invalid boolean
        # https://github.com/bleachbit/bleachbit/issues/560#issuecomment-497361700
        _test_is_corrupt("[bleachbit]\nshred=['True']\n", True)
        os.remove(bleachbit.options_file)

    def test_purge(self):
        """Test purging"""
        # By default ConfigParser stores keys (the filenames) as lowercase.
        # This needs special consideration when combined with purging.
        o1 = bleachbit.Options.Options()
        pathname = self.write_file('foo.xml')
        myhash = '0ABCD'
        o1.set_hashpath(pathname, myhash)
        o1.close()
        self.assertEqual(myhash, o1.get_hashpath(pathname))
        if 'nt' == os.name:
            # check case sensitivity
            self.assertEqual(myhash, o1.get_hashpath(pathname.upper()))

        # reopen
        o2 = bleachbit.Options.Options()
        # write something, which triggers the purge
        o2.set('dummypath', 'dummyvalue', 'hashpath')
        o2.commit()
        # verify the path was not purged
        self.assertTrue(os.path.exists(pathname))
        self.assertEqual(myhash, o2.get_hashpath(pathname))

        # delete the path
        os.remove(pathname)
        # close and reopen
        o2.close()
        o3 = bleachbit.Options.Options()
        # write something, which triggers the purge
        o3.set('dummypath', 'dummyvalue', 'hashpath')
        o3.commit()
        # verify the path was purged
        self.assertIsNone(o3.get_hashpath(pathname))
        o3.close()

    def test_abbreviations(self):
        """Test non-standard, abbreviated booleans T and F"""

        # set values
        o = bleachbit.Options.options
        if not o.config.has_section('test'):
            o.config.add_section('test')
        o.config.set('test', 'test_t_upper', 'T')
        o.config.set('test', 'test_f_upper', 'F')
        o.config.set('test', 'test_t_lower', 't')
        o.config.set('test', 'test_f_lower', 'f')

        # read
        self.assertEqual(o.config.getboolean('test', 'test_t_upper'), True)
        self.assertEqual(o.config.getboolean('test', 'test_t_lower'), True)
        self.assertEqual(o.config.getboolean('test', 'test_f_upper'), False)
        self.assertEqual(o.config.getboolean('test', 'test_f_lower'), False)

        # clean up
        del o

    def test_percent(self):
        """Test that the percent sign can be used without quoting the string"""
        # https://github.com/bleachbit/bleachbit/issues/205

        opt = bleachbit.Options.options.config
        if not opt.has_section('test'):
            opt.add_section('test')
        opt.set('test', 'filename', '/var/log/samba/log.%m')

        # read
        self.assertEqual(opt.get('test', 'filename'), '/var/log/samba/log.%m')

        # clean up
        del opt

    def test_error_disk_full(self):
        """Test graceful degradation when disk is full"""
        disk_full_error = OSError('No space left on device')
        disk_full_error.errno = errno.ENOSPC
        o = bleachbit.Options.Options()
        with mock.patch('builtins.open', side_effect=disk_full_error):
            with self.assertLogs(level='ERROR') as log_context:
                o.set('test_key', 'test_value')
                o.commit()
        self.assertIn('Disk was full', log_context.output[0])
        self.assertIn(bleachbit.options_file, log_context.output[0])
        self.assertEqual(o.get('test_key'), 'test_value')

    def test_error_permission(self):
        """Test graceful degradation with permission errors"""
        permission_error = PermissionError('Permission denied')
        permission_error.errno = errno.EACCES
        o = bleachbit.Options.Options()
        with mock.patch('builtins.open', side_effect=permission_error):
            with self.assertLogs(level='ERROR') as log_context:
                o.set('test_key', 'test_value')
                o.commit()
        self.assertIn('Permission denied', log_context.output[0])
        self.assertIn(bleachbit.options_file, log_context.output[0])
        self.assertEqual(o.get('test_key'), 'test_value')

    def test_warning(self):
        """Test warning preferences"""
        o = bleachbit.Options.options
        self.assertFalse(o.get_warning_preference('test_key'))
        o.remember_warning_preference('test_key')
        self.assertTrue(o.get_warning_preference('test_key'))
        o.close()

    def test_overrides(self):
        """Test CLI override functionality"""
        o = bleachbit.Options.options

        debug_default = is_debugging_enabled_via_cli()

        # Check defaults which are assumed in later tests.
        self.assertFalse(o.get('shred'))
        self.assertEqual(o.get('debug'), debug_default)
        self.assertTrue(o.get('delete_confirmation'))

        # Test basic override
        o.set_override('shred', True)
        self.assertTrue(o.get('shred'))

        # Test that override takes precedence over get
        o.set('shred', False)
        self.assertTrue(o.get('shred'))  # override should still return True

        # Test multiple overrides
        o.set_override('debug', True)
        o.set_override('delete_confirmation', False)
        self.assertTrue(o.get('debug'))
        self.assertFalse(o.get('delete_confirmation'))

        # Test that flush doesn't write overridden values
        # First set persistent values different from overrides
        o.set('shred', False)
        o.set('debug', False)
        o.set('delete_confirmation', True)
        o.commit()

        # Verify overrides still work after flush
        self.assertTrue(o.get('shred'))
        self.assertTrue(o.get('debug'))
        self.assertFalse(o.get('delete_confirmation'))

        # Create new instance to verify persistent values were written correctly
        o2 = bleachbit.Options.Options()
        self.assertFalse(o2.get('shred'))
        self.assertEqual(o2.get('debug'), debug_default)
        self.assertTrue(o2.get('delete_confirmation'))
        o2.close()

    def test_override_does_not_persist(self):
        """Test that overrides don't persist after process restart"""
        o = bleachbit.Options.options

        # Set an override
        o.set_override('shred', True)
        self.assertTrue(o.get('shred'))

        # Create new instance (simulating process restart)
        o2 = bleachbit.Options.Options()
        # Override should not exist in new instance
        self.assertNotIn(('bleachbit', 'shred'), o2.overrides)
        o2.close()

        # Clean up
        o.reset_overrides()

    def test_override_with_sections(self):
        """Test overrides work with different sections"""
        o = bleachbit.Options.options

        # Test override in non-default section
        if not o.config.has_section('test_section'):
            o.config.add_section('test_section')
        o.config.set('test_section', 'test_key', 'original_value')

        o.set_override('test_key', 'override_value', section='test_section')
        self.assertEqual(
            o.get('test_key', section='test_section'), 'override_value')

        # Verify flush doesn't write override
        o.commit()
        o2 = bleachbit.Options.Options()
        self.assertEqual(
            o2.get('test_key', section='test_section'), 'original_value')
        o2.close()

        # Clean up
        o.reset_overrides()
        if o.config.has_section('test_section'):
            o.config.remove_section('test_section')

    def test_flush_mechanisms_timer_and_close(self):
        """Test that changes flush correctly via timer fire or explicit close()."""
        with mock.patch('bleachbit.Options.threading.Timer', FakeTimer):
            for commit_method in ['timer', 'close']:
                with self.subTest(commit=commit_method):
                    self._write_seed_options_file()
                    o = bleachbit.Options.Options()

                    def assert_pending_changes_uncommitted(instance):
                        self.assertFalse(instance.get('shred'))
                        self.assertIsNone(instance.get_list('list_test'))
                        self.assertEqual([], instance.get_whitelist_paths())
                        self.assertEqual([], instance.get_custom_paths())
                        self.assertFalse(instance.get_language('zz'))
                        self.assertFalse(instance.get_tree('system', 'cache'))
                        self.assertFalse(
                            instance.get_warning_preference('warn_key'))

                    # Ensure initial state has no pending changes
                    assert_pending_changes_uncommitted(o)

                    # Guard against premature flush
                    with mock.patch('builtins.open', side_effect=AssertionError('unexpected flush')):
                        o.set('shred', True)
                        o.set_list('list_test', ['a', 'b'])
                        o.set_whitelist_paths([('file', '/tmp/a')])
                        o.set_custom_paths([('folder', '/tmp/b')])
                        o.set_language('zz', True)
                        o.set_tree('system', 'cache', True)
                        o.remember_warning_preference('warn_key')

                    pending_timer = FakeTimer.instances[-1]
                    self.assertTrue(pending_timer.started)

                    # Verify uncommitted changes are invisible to new instance
                    o2 = bleachbit.Options.Options()
                    assert_pending_changes_uncommitted(o2)
                    o2.close()

                    # Commit via the specific mechanism being tested
                    if commit_method == 'timer':
                        pending_timer.fire()
                    else:
                        o.close()

                    # Verify all changes persisted
                    o3 = bleachbit.Options.Options()
                    self.assertTrue(o3.get('shred'))
                    self.assertEqual(['a', 'b'], o3.get_list('list_test'))
                    self.assertEqual([('file', '/tmp/a')],
                                     o3.get_whitelist_paths())
                    self.assertEqual([('folder', '/tmp/b')],
                                     o3.get_custom_paths())
                    self.assertTrue(o3.get_language('zz'))
                    self.assertTrue(o3.get_tree('system', 'cache'))
                    self.assertTrue(o3.get_warning_preference('warn_key'))
                    o3.close()

                    if commit_method == 'timer':
                        o.close()

                    # Clean up for next iteration
                    self.tearDown()
                    self.setUp()

    def test_close_unregisters_atexit_and_is_idempotent(self):
        """Test close() unregisters its atexit callback and only flushes once."""
        self._write_seed_options_file()
        with mock.patch('bleachbit.Options.atexit.unregister') as mock_unregister:
            o = bleachbit.Options.Options()
            with mock.patch.object(o, '_Options__flush') as mock_flush:
                o.close()
                o.close()

            mock_flush.assert_called_once_with(force=False)
            mock_unregister.assert_called_once()
