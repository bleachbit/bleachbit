# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Cleaner
"""

import glob
import logging
import os
import shutil
from xml.dom.minidom import parseString

import bleachbit
from bleachbit.Action import ActionProvider, Command
from bleachbit.Cleaner import Cleaner, backends, create_simple_cleaner, register_cleaners
from tests.TestWinapp import get_winapp2

from tests import common

logger = logging.getLogger('bleachbit')


def action_to_cleaner(action_str):
    """Given an action XML fragment, return a cleaner"""
    return actions_to_cleaner([action_str])


def actions_to_cleaner(action_strs):
    """Given multiple action XML fragments, return one cleaner"""

    cleaner = Cleaner()
    for count, action_str in enumerate(action_strs, start=1):
        dom = parseString(action_str)
        action_node = dom.childNodes[0]
        command = action_node.getAttribute('command')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(action_node)
        cleaner.add_action('option%d' % count, provider)
        cleaner.add_option('option%d' % count, 'name%d' %
                           count, 'description%d' % count)
    return cleaner


def register_all_cleaners():
    """Register all cleaners for testing

    _patch_options_paths() changes the options directory during testing
    to a clean directory, so by default it will not have Winapp2.ini.
    """
    os.makedirs(bleachbit.personal_cleaners_dir, exist_ok=True)
    print("personal_cleaners_dir: %s" % bleachbit.personal_cleaners_dir)
    shutil.copyfile(
        get_winapp2(),
            os.path.join(bleachbit.personal_cleaners_dir, 'winapp2.ini'),
        )
    if not backends:
        list(register_cleaners())
    assert len(backends) > 1


class CleanerTestCase(common.BleachbitTestCase):

    def test_add_action(self):
        """Unit test for Cleaner.add_action()"""
        self.actions = [
            '<action command="delete" search="file" path="$WINDIR\\explorer.exe"/>',
            '<action command="delete" search="glob" path="$WINDIR\\system32\\*.dll"/>',
            '<action command="delete" search="walk.files" path="$WINDIR\\system32\\"/>',
            '<action command="delete" search="walk.all" path="$WINDIR\\system32\\"/>']
        self.assertGreater(len(self.actions), 0)

        for action_str in self.actions:
            cleaner = action_to_cleaner(action_str)
            count = 0
            for cmd in cleaner.get_commands('option1'):
                for result in cmd.execute(False):
                    self.assertEqual(result['n_deleted'], 1)
                    pathname = result['path']
                    self.assertLExists(
                        pathname, "Does not exist: '%s'" % pathname)
                    count += 1
                    common.validate_result(self, result)
            self.assertGreater(count, 0, "No files found for %s" % action_str)
        # should yield nothing
        cleaner.add_option('option2', 'name2', 'description2')
        for cmd in cleaner.get_commands('option2'):
            print(cmd)
            raise AssertionError('option2 should yield nothing')
        # should fail
        self.assertRaises(
            RuntimeError, cleaner.get_commands('option3').__next__)

    def test_auto_hide(self):
        for key in sorted(backends):
            self.assertIsInstance(backends[key].auto_hide(), bool)

    def test_create_simple_cleaner(self):
        """Unit test for method create_simple_cleaner"""
        dirname = self.mkdtemp(prefix='bleachbit-test-create-simple-cleaner')
        filename1 = os.path.join(dirname, '1')
        common.touch_file(filename1)
        # test Cyrillic for https://bugs.launchpad.net/bleachbit/+bug/1541808
        filename2 = os.path.join(dirname, 'чистый')
        common.touch_file(filename2)
        targets = [filename1, filename2, dirname]
        cleaner = create_simple_cleaner(targets)
        for cmd in cleaner.get_commands('files'):
            # preview
            for result in cmd.execute(False):
                common.validate_result(self, result)
            # delete
            list(cmd.execute(True))

        for target in targets:
            self.assertNotExists(target)

    def test_create_simple_cleaner_nonexistent(self):
        """Unit test for create_simple_cleaner with non-existent paths

        Non-existent paths should be skipped without error.
        https://github.com/bleachbit/bleachbit/issues/831
        """
        # Use a path that does not exist
        non_existent_path = os.path.join(self.mkdtemp(), 'does_not_exist')
        self.assertNotExists(non_existent_path)
        cleaner = create_simple_cleaner([non_existent_path])
        # Should yield no commands for non-existent path
        commands = list(cleaner.get_commands('files'))
        self.assertEqual(len(commands), 0, "Non-existent path should not yield commands")
        # Mix of existing and non-existing paths
        dirname = self.mkdtemp(prefix='bleachbit-test-create-simple-cleaner-mixed')
        filename = os.path.join(dirname, 'testfile')
        common.touch_file(filename)
        non_existent_path2 = os.path.join(dirname, 'does_not_exist')
        targets = [non_existent_path, filename, non_existent_path2]
        cleaner2 = create_simple_cleaner(targets)
        commands = list(cleaner2.get_commands('files'))
        # Should yield exactly one command for the existing file
        self.assertEqual(len(commands), 1, "Should yield command only for existing file")
        # Clean up
        os.remove(filename)
        os.rmdir(dirname)

    def test_get_name(self):
        for key in sorted(backends):
            self.assertIsString(backends[key].get_name())

    def test_get_description(self):
        for key in sorted(backends):
            self.assertIsString(key)
            self.assertIsInstance(backends[key], Cleaner)
            desc = backends[key].get_description()
            if desc is not None:
                self.assertIsString(
                    desc, "description for '%s' is '%s'" % (key, desc))

    def test_get_options(self):
        for key in sorted(backends):
            for (test_id, name) in backends[key].get_options():
                self.assertIsString(
                    test_id, '%s.%s is not a string' % (key, test_id))
                self.assertIsString(name)

    def test_get_commands(self):
        for key in sorted(backends):
            logger.debug("test_get_commands: key='%s'", key)
            for (option_id, __name) in backends[key].get_options():
                for cmd in backends[key].get_commands(option_id):
                    for result in cmd.execute(really_delete=False):
                        if result != True:
                            break
                        common.validate_result(self, result)

    def test_no_files_exist(self):
        """Verify only existing files are returned"""
        _exists = os.path.exists
        _iglob = glob.iglob
        _lexists = os.path.lexists
        _oswalk = os.walk
        try:
            glob.iglob = lambda path, root_dir=None, dir_fd=None, recursive=False: []
            os.path.exists = lambda path: False
            os.path.lexists = lambda path: False
            os.walk = lambda top, topdown = True, onerror = None, followlinks = False: []
            for key in sorted(backends):
                for (option_id, __name) in backends[key].get_options():
                    for cmd in backends[key].get_commands(option_id):
                        for result in cmd.execute(really_delete=False):
                            if result != True:
                                break
                            msg = "Expected no files to be deleted but got '%s'" % str(
                                result)
                            self.assertNotIsInstance(cmd, Command.Delete, msg)
                            common.validate_result(self, result)
        finally:
            glob.iglob = _iglob
            os.path.exists = _exists
            os.path.lexists = _lexists
            os.walk = _oswalk

    def test_register_cleaners(self):
        """Unit test for register_cleaners"""
        register_all_cleaners()
        register_all_cleaners()
        backends.clear()
        register_all_cleaners()
