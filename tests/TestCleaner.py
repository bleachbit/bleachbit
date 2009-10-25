# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Test case for module Cleaner
"""


import sys
import tempfile
import types
import unittest
from xml.dom.minidom import parseString

sys.path.append('.')
from bleachbit.Action import ActionProvider
from bleachbit.Cleaner import *



class TestCleaner(unittest.TestCase):


    @staticmethod
    def action_to_cleaner(action_str):
        """Given an action XML fragment, return a cleaner"""
        return TestCleaner.actions_to_cleaner( [action_str] )

    @staticmethod
    def actions_to_cleaner(action_strs):
        """Given multiple action XML fragments, return one cleaner"""

        cleaner = Cleaner()
        count = 1
        for action_str in action_strs:
            dom = parseString(action_str)
            action_node = dom.childNodes[0]
            command = action_node.getAttribute('command')
            provider = None
            for actionplugin in ActionProvider.plugins:
                if actionplugin.action_key == command:
                    provider = actionplugin(action_node)
            cleaner.add_action('option%d' % count, provider)
            cleaner.add_option('option%d' % count, 'name%d' % count, 'description%d' % count)
            count = count + 1
        return cleaner

    def test_add_action(self):
        """Unit test for Cleaner.add_action()"""
        self.actions = []
        if 'nt' == os.name:
            self.actions.append('<action command="delete" search="file" path="$WINDIR\\notepad.exe"/>')
            self.actions.append('<action command="delete" search="glob" path="$WINDIR\\system32\\*.dll"/>')
            self.actions.append( \
                '<action command="delete" search="walk.files" path="$WINDIR\\system\\"/>')
            self.actions.append( \
                '<action command="delete" search="walk.all" path="$WINDIR\\system32\\"/>')
        elif 'posix' == os.name:
            self.actions.append('<action command="delete" search="file" path="%s"/>' % __file__)
            self.actions.append('<action command="delete" search="glob" path="/usr/sbin/*sh"/>')
            self.actions.append('<action command="delete" search="walk.files" path="/usr/sbin/"/>')
            self.actions.append('<action command="delete" search="walk.all" path="/var/log/"/>')

        self.assert_(len(self.actions) > 0)

        for action_str in self.actions:
            cleaner = self.action_to_cleaner(action_str)
            count = 0
            for cmd in cleaner.get_commands('option1'):
                for result in cmd.execute(False):
                    self.assertEqual(result['n_deleted'], 1)
                    pathname = result['path']
                    self.assert_(os.path.lexists(pathname), \
                        "Does not exist: '%s'" % pathname)
                    count += 1
                    self.validate_result(self, result)
            self.assert_(count > 0, "No files found for %s" % action_str)
        # should yield nothing
        cleaner.add_option('option2', 'name2', 'description2')
        for cmd in cleaner.get_commands('option2'):
            print cmd
            self.assert_(False, 'option2 should yield nothing')
        # should fail
        self.assertRaises(RuntimeError, cleaner.get_commands('option3').next)


    def test_auto_hide(self):
        for key in sorted(backends):
            self.assert_ (type(backends[key].auto_hide()) is bool)


    def test_create_simple_cleaner(self):
        """Unit test for method create_simple_cleaner"""
        (fd, filename1) = tempfile.mkstemp('bleachbit-test')
        os.close(fd)
        (fd, filename2) = tempfile.mkstemp('bleachbit-test')
        os.close(fd)
        self.assert_(os.path.exists(filename1))
        self.assert_(os.path.exists(filename2))
        cleaner = create_simple_cleaner( [ filename1, filename2 ] )
        for cmd in cleaner.get_commands('files'):
            # preview
            for result in cmd.execute(False):
                self.validate_result(self, result)
            # delete
            for result in cmd.execute(True):
                pass

        self.assert_(not os.path.exists(filename1))
        self.assert_(not os.path.exists(filename2))


    def test_get_name(self):
        for key in sorted(backends):
            self.assert_ (type(backends[key].get_name()) is str)


    def test_get_descrption(self):
        for key in sorted(backends):
            for desc in backends[key].get_description():
                self.assert_ (type(desc) is str)


    def test_get_options(self):
        for key in sorted(backends):
            for (test_id, name) in backends[key].get_options():
                self.assert_ (type(test_id) is str)
                self.assert_ (type(name) is str)


    def test_get_commands(self):
        for key in sorted(backends):
            print "debug: test_get_commands: key='%s'" % (key, )
            for (option_id, __name) in backends[key].get_options():
                for cmd in backends[key].get_commands(option_id):
                    for result in cmd.execute(really_delete = False):
                        if result != True:
                            break
                        self.validate_result(self, result)
        # make sure trash and tmp don't return the same results
        if 'nt' == os.name:
            return
        def get_files(option_id):
            ret = []
            for cmd in backends['system'].get_commands(option_id):
                result = cmd.execute(False).next()
                ret.append(result['path'])
            return ret
        trash_paths = get_files('trash')
        tmp_paths = get_files('tmp')
        for tmp_path in tmp_paths:
            self.assert_(tmp_path not in trash_paths)


    def test_no_files_exist(self):
        """Verify only existing files are returned"""
        _exists = os.path.exists
        _iglob = glob.iglob
        _lexists = os.path.lexists
        _oswalk = os.walk
        glob.iglob = lambda path: []
        os.path.exists = lambda path: False
        os.path.lexists = lambda path: False
        os.walk = lambda top, topdown = False: []
        for key in sorted(backends):
            for (option_id, __name) in backends[key].get_options():
                for cmd in backends[key].get_commands(option_id):
                    for result in cmd.execute(really_delete = False):
                        if result != True:
                            break
                        msg = "Expected no files to be deleted but got '%s'" % str(result)
                        self.assert_(not isinstance(cmd, Command.Delete), msg)
                        self.validate_result(self, result)
        glob.iglob = _iglob
        os.path.exists = _exists
        os.path.lexists = _lexists
        os.walk = _oswalk


    def test_whitelist(self):
        tests = [ \
            ('/tmp/.truecrypt_aux_mnt1/control', True), \
            ('/tmp/.truecrypt_aux_mnt1/volume', True), \
            ('/tmp/.vbox-foo-ipc/lock', True), \
            ('/tmp/.wine-500/server-806-102400f/lock', True), \
            ('/tmp/gconfd-foo/lock/ior', True), \
            ('/tmp/ksocket-foo/Arts_SoundServerV2', True), \
            ('/tmp/ksocket-foo/secret-cookie', True), \
            ('/tmp/orbit-foo/bonobo-activation-server-ior', True), \
            ('/tmp/orbit-foo/bonobo-activation-register.lock', True), \
            ('/tmp/orbit-foo/bonobo-activation-server-a9cd6cc4973af098918b154c4957a93f-ior', True), \
            ('/tmp/orbit-foo/bonobo-activation-register-a9cd6cc4973af098918b154c4957a93f.lock', True), \
            ('/tmp/pulse-foo/pid', True), \
            ('/tmp/tmpsDOBFd', False) \
            ]
        for test in tests:
            self.assertEqual(backends['system'].whitelisted(test[0]), test[1], test[0])


    @staticmethod
    def validate_result(self, result):
        """Validate the command returned valid results"""
        self.assert_(type(result) is dict, "result is a %s" % type(result))
        # label
        self.assert_(isinstance(result['label'], (str, unicode)))
        self.assert_(len(result['label'].strip()) > 0)
        # n_*
        self.assert_(isinstance(result['n_deleted'], (int, long)))
        self.assert_(result['n_deleted'] >= 0)
        self.assert_(result['n_deleted'] <= 1)
        self.assertEqual(result['n_special'] + result['n_deleted'], 1)
        # size
        self.assert_(isinstance(result['size'], (int, long, types.NoneType)), \
            "size is %s" % str(result['size']))
        # path
        filename = result['path']
        self.assert_(isinstance(filename, (str, unicode, types.NoneType)), \
            "Filename is invalid: '%s' (type %s)" % (str(filename), type(filename)))
        if isinstance(filename, (str, unicode)) and \
            not filename[0:2] == 'HK':
            self.assert_ (os.path.lexists(filename), \
                "Path does not exist: '%s'" % (filename))



if __name__ == '__main__':
    unittest.main()

