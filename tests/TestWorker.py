# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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
Test case for module Worker
"""


import sys
import tempfile
import unittest

sys.path.append('.')
import TestCleaner
from bleachbit import CLI, Command
from bleachbit.Action import ActionProvider
from bleachbit.Worker import *
from bleachbit.Common import expanduser


class AccessDeniedActionAction(ActionProvider):

    action_key = 'access.denied'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # access denied, should fail and continue
        def accessdenied():
            import errno
            raise OSError(errno.EACCES, 'Permission denied: /foo/bar')
        yield Command.Function(None, accessdenied, 'Test access denied')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class DoesNotExistAction(ActionProvider):

    action_key = 'does.not.exist'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # non-existent file, should fail and continue
        yield Command.Delete("doesnotexist")

        # real file, should succeed
        yield Command.Delete(self.pathname)


class FunctionGeneratorAction(ActionProvider):

    action_key = 'function.generator'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # function generator without path, should succeed
        def funcgenerator():
            yield long(10)
        yield Command.Function(None, funcgenerator, 'funcgenerator')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class FunctionPathAction(ActionProvider):

    action_key = 'function.path'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # function with path, should succeed
        def pathfunc(path):
            pass
        # self.pathname must exist because it checks the file size
        yield Command.Function(self.pathname, pathfunc, 'pathfunc')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class InvalidEncodingAction(ActionProvider):

    action_key = 'invalid.encoding'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # file with invalid encoding
        import tempfile
        (fd, filename) = tempfile.mkstemp('invalid-encoding-\xe4\xf6\xfc~')
        os.close(fd)
        yield Command.Delete(filename)

        # real file, should succeed
        yield Command.Delete(self.pathname)


class FunctionPlainAction(ActionProvider):

    action_key = 'function.plain'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # plain function without path, should succeed
        def intfunc():
            return int(5)
        yield Command.Function(None, intfunc, 'intfunc')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class LockedAction(ActionProvider):

    action_key = 'locked'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # Lock the file on Windows.  It should be marked for deletion.
        f = os.open(self.pathname, os.O_RDWR | os.O_EXCL)
        yield Command.Delete(self.pathname)
        assert(os.path.exists(self.pathname))
        os.close(f)

        # real file, should succeed
        yield Command.Delete(self.pathname)


class RuntimeErrorAction(ActionProvider):

    action_key = 'runtime'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # runtime exception, should fail and continue
        def runtime():
            raise RuntimeError('This is a test exception')

        yield Command.Function(None, runtime, 'Test runtime exception')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class TruncateTestAction(ActionProvider):

    action_key = 'truncate.test'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # truncate real file
        yield Command.Truncate(self.pathname)

        # real file, should succeed
        yield Command.Delete(self.pathname)


class WorkerTestCase(unittest.TestCase):

    """Test case for module Worker"""

    def action_test_helper(self, command, special_expected, errors_expected,
                           bytes_expected_posix, count_deleted_posix,
                           bytes_expected_nt, count_deleted_nt):
        ui = CLI.CliCallback()
        (fd, filename) = tempfile.mkstemp(prefix='bleachbit-test-worker')
        os.write(fd, '123')
        os.close(fd)
        self.assert_(os.path.exists(filename))
        astr = '<action command="%s" path="%s"/>' % (command, filename)
        cleaner = TestCleaner.action_to_cleaner(astr)
        backends['test'] = cleaner
        operations = {'test': ['option1']}
        worker = Worker(ui, True, operations)
        run = worker.run()
        while run.next():
            pass
        self.assert_(not os.path.exists(filename),
                     "Path still exists '%s'" % filename)
        self.assertEqual(worker.total_special, special_expected,
                         'For command %s expecting %s special operations but observed %d'
                         % (command, special_expected, worker.total_special))
        self.assertEqual(worker.total_errors, errors_expected,
                         'For command %s expecting %d errors but observed %d'
                         % (command, errors_expected, worker.total_errors))
        if 'posix' == os.name:
            self.assertEqual(worker.total_bytes, bytes_expected_posix)
            self.assertEqual(worker.total_deleted, count_deleted_posix)
        elif 'nt' == os.name:
            self.assertEqual(worker.total_bytes, bytes_expected_nt)
            self.assertEqual(worker.total_deleted, count_deleted_nt)

    def test_AccessDenied(self):
        """Test Worker using Action.AccessDeniedAction"""
        self.action_test_helper('access.denied', 0, 1, 4096, 1, 3, 1)

    def test_DoesNotExist(self):
        """Test Worker using Action.DoesNotExistAction"""
        self.action_test_helper('does.not.exist', 0, 1, 4096, 1, 3, 1)

    def test_FunctionGenerator(self):
        """Test Worker using Action.FunctionGenerator"""
        self.action_test_helper(
            'function.generator', 1, 0, 4096 + 10, 1, 3 + 10, 1)

    def test_FunctionPath(self):
        """Test Worker using Action.FunctionPathAction"""
        self.action_test_helper('function.path', 1, 0, 4096, 1, 3, 1)

    def test_FunctionPlain(self):
        """Test Worker using Action.FunctionPlainAction"""
        self.action_test_helper('function.plain', 1, 0, 4096 + 5, 1, 3 + 5, 1)

    def test_InvalidEncoding(self):
        """Test Worker using Action.InvalidEncodingAction"""
        self.action_test_helper('invalid.encoding', 0, 0, 4096, 2, 3, 2)

    def test_Locked(self):
        """Test Worker using Action.LockedAction"""
        if not 'nt' == os.name:
            return
        self.action_test_helper('locked', 0, 0, None, None, 3 + 0, 2)

    def test_RuntimeError(self):
        """Test Worker using Action.RuntimeErrorAction
        The Worker module handles these differently than
        access denied exceptions
        """
        self.action_test_helper('runtime', 0, 1, 4096, 1, 3, 1)

    def test_Truncate(self):
        """Test Worker using Action.TruncateTestAction
        """
        self.action_test_helper('truncate.test', 0, 0, 4096, 2, 3, 2)

    def test_deep_scan(self):
        """Test for deep scan"""

        # load cleaners from XML
        import bleachbit.CleanerML
        bleachbit.CleanerML.load_cleaners()

        # DeepScan itself is tested elsewhere, so replace it here
        import bleachbit.DeepScan
        SaveDeepScan = bleachbit.DeepScan.DeepScan
        self.scanned = 0
        self_assertequal = self.assertEqual
        self_assert = self.assert_

        def increment_count():
            self.scanned = self.scanned + 1

        class MyDeepScan:

            def add_search(self, dirname, regex):
                self_assertequal(dirname, expanduser('~'))
                self_assert(
                    regex in ('^Thumbs\\.db$', '^Thumbs\\.db:encryptable$'))

            def scan(self):
                increment_count()
                yield True
        bleachbit.DeepScan.DeepScan = MyDeepScan

        # test
        operations = {'deepscan': ['thumbs_db']}
        ui = CLI.CliCallback()
        worker = Worker(ui, False, operations).run()
        while worker.next():
            pass
        self.assertEqual(1, self.scanned)

        # clean up
        bleachbit.DeepScan.DeepScan = SaveDeepScan

    def test_multiple_options(self):
        """Test one cleaner with two options"""
        ui = CLI.CliCallback()
        (fd, filename1) = tempfile.mkstemp(prefix='bleachbit-test-worker')
        os.close(fd)
        self.assert_(os.path.exists(filename1))
        (fd, filename2) = tempfile.mkstemp(prefix='bleachbit-test-worker')
        os.close(fd)
        self.assert_(os.path.exists(filename2))

        astr1 = '<action command="delete" search="file" path="%s"/>' % filename1
        astr2 = '<action command="delete" search="file" path="%s"/>' % filename2
        cleaner = TestCleaner.actions_to_cleaner([astr1, astr2])
        backends['test'] = cleaner
        operations = {'test': ['option1', 'option2']}
        worker = Worker(ui, True, operations)
        run = worker.run()
        while run.next():
            pass
        self.assert_(not os.path.exists(filename1),
                     "Path still exists '%s'" % filename1)
        self.assert_(not os.path.exists(filename2),
                     "Path still exists '%s'" % filename2)
        self.assertEqual(worker.total_special, 0)
        self.assertEqual(worker.total_errors, 0)
        self.assertEqual(worker.total_deleted, 2)


def suite():
    return unittest.makeSuite(WorkerTestCase)


if __name__ == '__main__':
    unittest.main()
