# vim: ts=4:sw=4:expandtab
# coding=utf-8

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Test case for module Cleaner
"""

import logging
import unittest
from xml.dom.minidom import parseString

from bleachbit.Action import ActionProvider
from bleachbit.Cleaner import *

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


class CleanerTestCase(common.BleachbitTestCase):

    def test_add_action(self):
        """Unit test for Cleaner.add_action()"""
        self.actions = []
        if 'nt' == os.name:
            self.actions += [
                '<action command="delete" search="file" path="$WINDIR\\explorer.exe"/>',
                '<action command="delete" search="glob" path="$WINDIR\\system32\\*.dll"/>',
                '<action command="delete" search="walk.files" path="$WINDIR\\system32\\"/>',
                '<action command="delete" search="walk.all" path="$WINDIR\\system32\\"/>']
        elif 'posix' == os.name:
            print(__file__)
            self.actions += [
                '<action command="delete" search="file" path="%s"/>' % __file__,
                '<action command="delete" search="glob" path="/bin/*sh"/>',
                '<action command="delete" search="walk.files" path="/bin/"/>',
                '<action command="delete" search="walk.all" path="/var/log/"/>']
        else:
            raise AssertionError('Unknown OS.')
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
        # make sure trash and tmp don't return the same results
        if 'nt' == os.name:
            return

        def get_files(option_id):
            ret = []
            list(register_cleaners())
            for cmd in backends['system'].get_commands(option_id):
                result = next(cmd.execute(False))
                ret.append(result['path'])
            return ret
        trash_paths = get_files('trash')
        tmp_paths = get_files('tmp')
        for tmp_path in tmp_paths:
            self.assertNotIn(tmp_path, trash_paths)

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
        list(register_cleaners())
        list(register_cleaners())

    @common.skipIfWindows # FIXME later: reevaluate
    @common.skipUnlessDestructive
    def test_system_recent_documents(self):
        """Clean recent documents in GTK"""
        mgr = Gtk.RecentManager().get_default()
        fn = self.mkstemp(suffix='.txt')
        self.assertExists(fn)
        from gi.repository import Gio, GLib
        uri = Gio.File.new_for_path(fn).get_uri()
        self.assertTrue(mgr.add_item(uri))
        GLib.idle_add(Gtk.main_quit)
        Gtk.main()  # process the addition
        GLib.idle_add(Gtk.main_quit)
        self.assertGreater(len(mgr.get_items()), 0)
        self.assertTrue(mgr.has_item(uri))

        list(register_cleaners())
        for cmd in backends['system'].get_commands('recent_documents'):
            for result in cmd.execute(really_delete=True):
                common.validate_result(self, result, True)

        self.assertEqual(len(mgr.get_items()), 0)

    @common.skipIfWindows
    def test_whitelist(self):
        tests = [
            ('/tmp/.truecrypt_aux_mnt1/control', True),
            ('/tmp/.truecrypt_aux_mnt1/volume', True),
            ('/tmp/.vbox-foo-ipc/lock', True),
            ('/tmp/.wine-500/server-806-102400f/lock', True),
            ('/tmp/gconfd-foo/lock/ior', True),
            ('/tmp/ksocket-foo/Arts_SoundServerV2', True),
            ('/tmp/ksocket-foo/secret-cookie', True),
            ('/tmp/orbit-foo/bonobo-activation-server-ior', True),
            ('/tmp/orbit-foo/bonobo-activation-register.lock', True),
            ('/tmp/orbit-foo/bonobo-activation-server-a9cd6cc4973af098918b154c4957a93f-ior',
             True),
            ('/tmp/orbit-foo/bonobo-activation-register-a9cd6cc4973af098918b154c4957a93f.lock',
             True),
            ('/tmp/pulse-foo/pid', True),
            ('/tmp/tmpsDOBFd', False),
            (os.path.expanduser('~/.cache/obexd'), True),
            (os.path.expanduser('~/.cache/obexd/'), True),
            (os.path.expanduser('~/.cache/obexd/foo'), True),
            (os.path.expanduser('~/.cache/obex'), False),
            (os.path.expanduser('~/.cache/obexd-foo'), False)
        ]
        list(register_cleaners())
        for test in tests:
            self.assertEqual(
                backends['system'].whitelisted(test[0]), test[1], test[0])
        # Make sure directory ~/.cache/obexd is ignored
        # https://github.com/bleachbit/bleachbit/issues/572
        obexd_dir = os.path.expanduser('~/.cache/obexd')
        if not os.path.exists(obexd_dir):
            os.makedirs(obexd_dir)
        obexd_fn = os.path.join(obexd_dir, 'bleachbit-test')
        common.touch_file(obexd_fn)
        found_canary = False
        for cmd in backends['system'].get_commands('cache'):
            for _result in cmd.execute(really_delete=False):
                self.assertNotEqual(cmd.path, obexd_fn)
                self.assertFalse('/.cache/obexd/' in cmd.path)
        from bleachbit.FileUtilities import delete
        delete(obexd_fn, ignore_missing=True)
