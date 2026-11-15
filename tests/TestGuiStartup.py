# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module GuiStartup
"""

# These tests reach into internals on purpose.
# pylint: disable=protected-access

import os
import shutil
import stat
import subprocess
from unittest import mock

from bleachbit import IS_WINDOWS
import bleachbit
from bleachbit import GuiStartup
from bleachbit.Cleaner import register_cleaners
from bleachbit.GuiStartup import _has_selected_warning_option, _get_posix_permission_issues, _get_windows_permission_issues
from bleachbit.Options import options
from tests import common


class StubOptions:
    """Minimal stand-in for bleachbit.Options for testing."""

    def __init__(self, *, first_start=True, shred=False, old_version=None):
        """Seed stub with values."""
        self.values = {'first_start': first_start, 'shred': shred}
        self._old_version = old_version

    def get(self, key):
        """Return stored option value."""
        return self.values.get(key)

    def set(self, key, value):
        """Set a option value."""
        self.values[key] = value

    # pylint: disable-next=unused-argument
    def get_tree(self, parent, child):
        """Return whether a tree option is selected."""
        return False


class GuiStartupTestCase(common.BleachbitTestCase):
    """Tests for GuiStartup helper logic."""

    def test_first_start_message_clears_flag(self):
        """Ensure first-start hint is emitted and flag gets cleared."""
        stub_options = StubOptions()

        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False):
            messages = GuiStartup.get_startup_messages(auto_exit=False)

        self.assertTrue(
            any('Access the application menu' in msg for msg, _ in messages))
        self.assertFalse(stub_options.get('first_start'))

    def test_outdated_build_notice_when_check_disabled(self):
        """An old build warns when the online update check is disabled"""
        stub_options = StubOptions()
        stub_options.values['check_online_updates'] = False
        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False), \
                mock.patch('bleachbit.SystemInformation.get_outdated_build_notice',
                           return_value='OUTDATED BUILD NOTICE'):
            messages = GuiStartup.get_startup_messages(auto_exit=False)
        self.assertIn(('OUTDATED BUILD NOTICE', False), messages)

    def test_outdated_build_notice_when_check_enabled(self):
        """An old build does not warn while the online check is pending"""
        stub_options = StubOptions()
        stub_options.values['check_online_updates'] = True
        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False), \
                mock.patch('bleachbit.online_update_notification_enabled', True), \
                mock.patch('bleachbit.SystemInformation.get_outdated_build_notice',
                           return_value='OUTDATED BUILD NOTICE'):
            messages = GuiStartup.get_startup_messages(auto_exit=False)
        self.assertNotIn(('OUTDATED BUILD NOTICE', False), messages)

    def test_outdated_build_notice_when_auto_exit(self):
        """--exit skips the online check, so an old build still warns"""
        stub_options = StubOptions()
        stub_options.values['check_online_updates'] = True
        with mock.patch.object(GuiStartup, 'options', stub_options), \
                mock.patch.object(GuiStartup, 'unset_sslkeylogfile', return_value=False), \
                mock.patch('bleachbit.online_update_notification_enabled', True), \
                mock.patch('bleachbit.SystemInformation.get_outdated_build_notice',
                           return_value='OUTDATED BUILD NOTICE'):
            messages = GuiStartup.get_startup_messages(auto_exit=True)
        self.assertIn(('OUTDATED BUILD NOTICE', False), messages)

    def test_has_selected_warning_option(self):
        """Test the function _has_selected_warning_option()"""
        # Register cleaners to populate backends
        list(register_cleaners())
        # Each test case starts with fresh options, so with
        # nothing selected, it should return False.
        self.assertFalse(_has_selected_warning_option())
        # Enable a safe option.
        options.set_tree('system', 'tmp', True)
        self.assertFalse(_has_selected_warning_option())
        # Enable an option with a warning.
        options.set_tree('system', 'empty_space', True)
        self.assertTrue(_has_selected_warning_option())
        # Clean up
        options.set_tree('system', 'tmp', False)
        options.set_tree('system', 'empty_space', False)

    def test_missing_requests(self):
        """Missing requests should be reported but not crash GuiStartup."""
        with common.mock_missing_package(
                'requests',
                clear_prefixes=('bleachbit.Network', 'bleachbit.Update', 'bleachbit.GuiStartup')):
            # `import x.y as Y` is deliberate: mock_missing_package drops the
            # submodule from sys.modules but leaves the parent attribute, so
            # `from x import Y` would hand back the stale module.
            # pylint: disable=consider-using-from-import
            # pylint: disable=reimported
            # pylint: disable-next=redefined-outer-name
            import bleachbit.GuiStartup as GuiStartup
            missing = GuiStartup._get_missing_dependencies()
            self.assertIn('requests', missing)

    @common.skipIfWindows
    def test_is_config_writable(self):
        """Test read-only configuration file"""
        o = bleachbit.Options.Options()
        o.close()
        self.assertExists(bleachbit.options_file)

        if common.have_root():
            # root bypasses file permission checks, so use chattr +i
            subprocess.run(
                ['chattr', '+i', bleachbit.options_file], check=True)
        else:
            os.chmod(bleachbit.options_file, stat.S_IRUSR |
                     stat.S_IRGRP | stat.S_IROTH)
        try:
            issues = GuiStartup._get_config_permission_issues()
        finally:
            if common.have_root():
                subprocess.run(
                    ['chattr', '-i', bleachbit.options_file], check=True)
            os.unlink(bleachbit.options_file)

        self.assertNotExists(bleachbit.options_file)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('Write error' in issue for issue in issues),
                        f"Expected 'Write error' in issues: {issues}")

    def test_config_permission_issues_normal(self):
        """Test that a normal writable config file reports no issues."""
        o = bleachbit.Options.Options()
        o.close()
        self.assertExists(bleachbit.options_file)
        issues = GuiStartup._get_config_permission_issues()
        os.unlink(bleachbit.options_file)
        self.assertNotExists(bleachbit.options_file)
        self.assertFalse(issues)

    def test_config_permission_nonissue_missing_file(self):
        """A missing config file must not be reported as an error.

        Unlike another test, this scenario has an options directory
        that allows creating the missing config file.
        """
        if os.path.exists(bleachbit.options_file):
            os.unlink(bleachbit.options_file)
        self.assertNotExists(bleachbit.options_file)
        issues = GuiStartup._get_config_permission_issues()
        self.assertFalse(issues)
        # Options creates the file itself, with its own mode and owner
        self.assertNotExists(bleachbit.options_file)

    @common.also_with_sudo
    def test_config_permission_nonissue_missing_dir(self):
        """A missing options directory (fresh profile) is created without error."""
        new_dir = os.path.join(self.mkdtemp(), 'a', 'bleachbit')
        new_file = os.path.join(new_dir, 'bleachbit.ini')
        with mock.patch('bleachbit.options_dir', new_dir), \
                mock.patch('bleachbit.options_file', new_file):
            self.assertFalse(GuiStartup._get_config_permission_issues())
        self.assertExists(new_dir)
        self.assertNotExists(new_file)
        if not IS_WINDOWS:
            real_uid = bleachbit.General.get_real_uid()
            self.assertEqual(os.stat(new_dir).st_uid, real_uid)

    @common.skipIfWindows
    def test_config_permission_missing_file_sudo(self):
        """In sudo mode, a missing config is neither created nor chowned"""
        new_dir = self.mkdtemp()
        new_file = os.path.join(new_dir, 'bleachbit.ini')
        with mock.patch('bleachbit.options_dir', new_dir), \
                mock.patch('bleachbit.options_file', new_file), \
                mock.patch('bleachbit.General.sudo_mode', return_value=True), \
                mock.patch('bleachbit.General.chownself') as mock_chown:
            self.assertFalse(GuiStartup._get_config_permission_issues())
            mock_chown.assert_not_called()
        self.assertNotExists(new_file)
        self.assertEqual([], os.listdir(new_dir))

    @common.skipIfWindows
    def test_config_permission_issue_symlinked_file(self):
        """A symlinked config is reported and its target is not created"""
        options_dir = self.mkdtemp()
        options_file = os.path.join(options_dir, 'bleachbit.ini')
        target = os.path.join(options_dir, 'elsewhere')
        os.symlink(target, options_file)
        with mock.patch('bleachbit.options_dir', options_dir), \
                mock.patch('bleachbit.options_file', options_file):
            issues = GuiStartup._get_config_permission_issues()
        self.assertIsInstance(issues, list)
        self.assertTrue(any('Write error' in issue for issue in issues),
                        f"Expected 'Write error' in issues: {issues}")
        self.assertNotExists(target)

    @common.skipIfWindows
    def test_config_permission_issue_missing_dir_non_writeable_parent(self):
        """Missing options dir under a non-writable parent reports an error."""
        non_writable_parent = self.mkdir('not_writeable_parent')
        missing_dir = os.path.join(non_writable_parent, 'bleachbit')
        missing_file = os.path.join(missing_dir, 'bleachbit.ini')
        use_chattr = common.have_root()
        try:
            if use_chattr:
                subprocess.run(
                    ['chattr', '+i', non_writable_parent], check=True)
            else:
                os.chmod(non_writable_parent, stat.S_IRUSR | stat.S_IXUSR)
            with mock.patch('bleachbit.options_dir', missing_dir), \
                    mock.patch('bleachbit.options_file', missing_file):
                issues = GuiStartup._get_config_permission_issues()
        finally:
            if use_chattr:
                subprocess.run(
                    ['chattr', '-i', non_writable_parent], check=True)
            else:
                os.chmod(non_writable_parent, stat.S_IRWXU)
            shutil.rmtree(non_writable_parent)
        self.assertNotExists(missing_dir)
        self.assertIsInstance(issues, list)
        self.assertTrue(
            any('Cannot create directory' in issue for issue in issues),
            f"Expected 'Cannot create directory' in issues: {issues}")
        self.assertIn(
            f'Nearest existing parent directory: {non_writable_parent}', issues)
        self.assertTrue(
            any(issue.startswith('Current user:') for issue in issues),
            f"Expected 'Current user:' in issues: {issues}")

    @common.skipIfWindows
    def test_config_permission_issue_non_writeable_options_dir(self):
        """Config does not exist and options dir is not writeable"""
        non_writable_dir = self.mkdir('not_writeable_options')
        non_writable_file = os.path.join(non_writable_dir, 'bleachbit.ini')
        use_chattr = common.have_root()
        try:
            if use_chattr:
                # Root bypasses chmod, so use chattr +i instead
                subprocess.run(['chattr', '+i', non_writable_dir], check=True)
            else:
                os.chmod(non_writable_dir, stat.S_IRUSR | stat.S_IXUSR)
            self.assertNotExists(non_writable_file)
            with mock.patch('bleachbit.options_dir', non_writable_dir), \
                    mock.patch('bleachbit.options_file', non_writable_file):
                issues = GuiStartup._get_config_permission_issues()
        finally:
            if use_chattr:
                subprocess.run(['chattr', '-i', non_writable_dir], check=True)
            else:
                os.chmod(non_writable_dir, stat.S_IRWXU)
            shutil.rmtree(non_writable_dir)
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('Write error' in issue for issue in issues),
                        f"Expected 'Write error' in issues: {issues}")

    @common.skipIfWindows
    def test_config_permission_nonissue_non_writeable_options_dir(self):
        """A writable config in a read-only options dir can still be saved"""
        read_only_dir = self.mkdtemp(prefix='read_only_options')
        options_file = os.path.join(read_only_dir, 'bleachbit.ini')
        common.touch_file(options_file)
        os.chmod(read_only_dir, stat.S_IRUSR | stat.S_IXUSR)
        try:
            with mock.patch('bleachbit.options_dir', read_only_dir), \
                    mock.patch('bleachbit.options_file', options_file):
                issues = GuiStartup._get_config_permission_issues()
        finally:
            os.chmod(read_only_dir, stat.S_IRWXU)
            shutil.rmtree(read_only_dir)
        self.assertFalse(issues)

    @common.also_with_sudo
    def test_permission_issues_normal_file(self):
        """Test ownership check on a normal file owned by the user."""
        path = self.write_file('check_me')
        fstat = os.stat(path)
        if IS_WINDOWS:
            has_error, lines = _get_windows_permission_issues(path)
        else:
            has_error, lines = _get_posix_permission_issues(fstat, path)
        self.assertFalse(has_error)
        self.assertTrue(any('File owner:' in line for line in lines))
        self.assertTrue(any('Current user:' in line for line in lines))

    @common.skipUnlessWindows
    def test_get_windows_user_info(self):
        """Test _get_windows_user_info function."""
        current_sid, current_name, group_sids = GuiStartup._get_windows_user_info()
        self.assertIsNotNone(current_sid)
        self.assertIsNotNone(current_name)
        self.assertIsNotNone(group_sids)
        self.assertIsInstance(current_sid, str)
        self.assertIsInstance(current_name, str)
        self.assertIsInstance(group_sids, set)
        self.assertEqual(current_name, os.environ.get('USERNAME', ''))

    @common.skipUnlessWindows
    def test_get_windows_file_owner(self):
        """Test _get_windows_file_owner function."""
        owner_sid_str, owner_name = GuiStartup._get_windows_file_owner(
            self.tempdir)
        self.assertIsNotNone(owner_sid_str)
        self.assertIsNotNone(owner_name)
        self.assertIsInstance(owner_sid_str, str)
        self.assertIsInstance(owner_name, str)
        # Elevated processes get Administrators as the owner, others get the
        # user, so accept either, like _get_windows_permission_issues does.
        current_sid, _name, group_sids = GuiStartup._get_windows_user_info()
        self.assertIn(owner_sid_str, {current_sid} | group_sids)

    @common.skipUnlessWindows
    def test_lookup_account_name_or_sid_unresolvable(self):
        """An unresolvable SID falls back to its string form (issue #2271).

        Reproduces the dual-boot / shared NTFS scenario where
        ``LookupAccountSid`` fails because the SID belongs to an
        account from the other Windows installation. The helper must
        not raise; it should return the SID string so the ownership
        comparison can still proceed by SID.
        """
        import win32security
        bogus = 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        sid = win32security.ConvertStringSidToSid(bogus)
        name, _ = GuiStartup._lookup_account_name_or_sid(sid)
        self.assertEqual(name, bogus)

    @common.skipUnlessWindows
    def test_config_permission_issue_protected_dacl(self):
        """A 0o700 config directory (issue #2401) is flagged until repaired."""
        import win32security  # pylint: disable=import-outside-toplevel
        protected_dir = os.path.join(self.tempdir, 'protected_options')
        os.mkdir(protected_dir, 0o700)
        self.addCleanup(shutil.rmtree, protected_dir, ignore_errors=True)
        protected_file = os.path.join(protected_dir, 'bleachbit.ini')
        self.write_file(protected_file, b'[bleachbit]\n')
        with mock.patch('bleachbit.options_dir', protected_dir), \
                mock.patch('bleachbit.options_file', protected_file), \
                mock.patch('bleachbit.Windows.shell.IsUserAnAdmin', return_value=False):
            # Owned by the current user, so it works and is not flagged.
            # When elevated the owner is Administrators, so read it from the file.
            owner_sid = win32security.GetFileSecurity(
                protected_dir, win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()
            with mock.patch('bleachbit.Windows._current_user_sid', return_value=owner_sid):
                self.assertFalse(GuiStartup._get_config_permission_issues())

            # Simulate an elevated first run: the owner is not the user
            other_sid = win32security.ConvertStringSidToSid('S-1-5-32-545')
            with mock.patch('bleachbit.Windows._current_user_sid', return_value=other_sid):
                issues = GuiStartup._get_config_permission_issues()
                self.assertIsInstance(issues, list)
                self.assertTrue(
                    any('issue #2401' in issue for issue in issues),
                    f'Expected issue #2401 in issues: {issues}')
                with mock.patch('bleachbit.portable_mode', True):
                    self.assertFalse(
                        GuiStartup._get_config_permission_issues())
                with mock.patch('bleachbit.Windows.shell.IsUserAnAdmin', return_value=True):
                    self.assertFalse(
                        GuiStartup._get_config_permission_issues())
                bleachbit.Windows.fix_appdata_acl(protected_dir)
                self.assertFalse(GuiStartup._get_config_permission_issues())
