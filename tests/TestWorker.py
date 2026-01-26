# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for module Worker
"""

import os
import tempfile

from tests import TestCleaner, common
from tests.TestFileUtilities import _open_blocking_handle
from bleachbit import CLI, Command
from bleachbit.Action import ActionProvider
from bleachbit.Cleaner import backends
from bleachbit.Worker import Worker

if os.name == 'nt':
    import win32con
    import win32file


class AccessDeniedActionAction(ActionProvider):
    action_key = 'access.denied'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # access denied, should fail and continue
        def accessdenied():
            import errno
            raise OSError(
                errno.EACCES, 'Permission denied: c:\\access\\denied', 'c:\\access\\denied')
        yield Command.Function(None, accessdenied, 'Test access denied')

        # real file, should succeed
        yield Command.Delete(self.pathname)


class DoesNotExistAction(ActionProvider):
    action_key = 'does.not.exist'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # non-existent file, should fail and continue
        if os.name == 'nt':
            yield Command.Delete(r"c:\does\not\exist")
        else:
            yield Command.Delete("/does/not/exist")

        # real file, should succeed
        yield Command.Delete(self.pathname)


class FunctionGeneratorAction(ActionProvider):
    action_key = 'function.generator'

    def __init__(self, action_element):
        self.pathname = action_element.getAttribute('path')

    def get_commands(self):
        # function generator without path, should succeed
        def funcgenerator():
            yield 10
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
        # Open the file with a blocking handle that allows read/write but blocks delete.
        # This causes delete() to truncate and mark for deletion. Windows only.
        share_mode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
        handle = _open_blocking_handle(self.pathname, share_mode)
        from bleachbit.FileUtilities import getsize
        # Without admin privileges, this delete fails.
        yield Command.Delete(self.pathname)
        assert (os.path.exists(self.pathname))
        fsize = getsize(self.pathname)
        if not fsize == 0:  # File should be truncated to 0 bytes
            raise RuntimeError('Locked file has size %dB (not 0B)' % fsize)
        win32file.CloseHandle(handle)

        # Now that the file is not locked, admin privileges
        # are not required to delete it.
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


class WorkerTestCase(common.BleachbitTestCase):

    """Test case for module Worker"""

    def action_test_helper(self, command, special_expected, errors_expected,
                           bytes_expected_posix, count_deleted_posix,
                           bytes_expected_nt, count_deleted_nt):
        ui = CLI.CliCallback()
        (fd, filename) = tempfile.mkstemp(
            prefix='bleachbit-test-worker', dir=self.tempdir)
        os.write(fd, b'123')
        os.close(fd)
        self.assertExists(filename)
        astr = '<action command="%s" path="%s"/>' % (command, filename)
        cleaner = TestCleaner.action_to_cleaner(astr)
        backends['test'] = cleaner
        operations = {'test': ['option1']}
        worker = Worker(ui, True, operations)
        run = worker.run()
        while next(run):
            pass
        del backends['test']
        self.assertNotExists(filename, "Path still exists '%s'" % filename)
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
        with self.assertLogs(level='ERROR') as log_context:
            self.action_test_helper('access.denied', 0, 1, 4096, 1, 3, 1)
            if os.name == 'nt':
                self.assertIn('Access denied: c:\\access\\denied',
                              log_context.output[0])
                self.assertNotIn('\\\\', log_context.output[0])

    def test_DoesNotExist(self):
        """Test Worker using Action.DoesNotExistAction"""
        with self.assertLogs(level='ERROR') as log_context:
            self.action_test_helper('does.not.exist', 0, 1, 4096, 1, 3, 1)
            if os.name == 'nt':
                # Make sure there is a simple messages without double backslashes.
                self.assertIn(
                    'File not found: c:\\does\\not\\exist', log_context.output[0])
                self.assertNotIn('\\\\', log_context.output[0])

    def test_FunctionGenerator(self):
        """Test Worker using Action.FunctionGenerator"""
        self.action_test_helper('function.generator', 1,
                                0, 4096 + 10, 1, 3 + 10, 1)

    def test_FunctionPath(self):
        """Test Worker using Action.FunctionPathAction"""
        self.action_test_helper('function.path', 1, 0, 4096, 1, 3, 1)

    def test_FunctionPlain(self):
        """Test Worker using Action.FunctionPlainAction"""
        self.action_test_helper('function.plain', 1, 0, 4096 + 5, 1, 3 + 5, 1)

    def test_InvalidEncoding(self):
        """Test Worker using Action.InvalidEncodingAction"""
        self.action_test_helper('invalid.encoding', 0, 0, 4096, 2, 3, 2)

    @common.skipUnlessWindows
    def test_Locked(self):
        """Test Worker using Action.LockedAction"""
        from win32com.shell import shell
        if shell.IsUserAnAdmin():
            # If an admin, the first attempt, with locking, will mark for
            # delete (3 bytes), and the second attempt will actually delete
            # it (0 bytes, already truncated).
            errors_expected = 0
            bytes_expected = 3 + 0
            total_deleted = 2
        else:
            # If not an admin, the first attempt (locked) truncates (to 0B) and fails,
            # then the second attempt (unlocked) deletes the 0-byte file.
            errors_expected = 1
            bytes_expected = 0
            total_deleted = 1
        self.action_test_helper(
            'locked', 0, errors_expected, None, None, bytes_expected, total_deleted)

    def test_RuntimeError(self):
        """Test Worker using Action.RuntimeErrorAction. It is normal to see a traceback.

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
        list(bleachbit.CleanerML.load_cleaners())

        # DeepScan itself is tested elsewhere, so replace it here
        import bleachbit.DeepScan
        SaveDeepScan = bleachbit.DeepScan.DeepScan
        self.scanned = 0
        parent = self

        class MyDeepScan:
            def __init__(self, searches):
                for (path, searches) in searches.items():
                    parent.assertEqual(path, os.path.expanduser('~'))
                    for s in searches:
                        parent.assertIn(
                            s.regex, ['^Thumbs\\.db$', '^Thumbs\\.db:encryptable$'])

            def scan(self):
                parent.scanned += 1
                yield True

        bleachbit.DeepScan.DeepScan = MyDeepScan

        # test
        operations = {'deepscan': ['thumbs_db']}
        ui = CLI.CliCallback()
        worker = Worker(ui, False, operations).run()
        while next(worker):
            pass
        self.assertEqual(1, self.scanned)

        # clean up
        bleachbit.DeepScan.DeepScan = SaveDeepScan

    def test_multiple_options(self):
        """Test one cleaner with two options"""
        ui = CLI.CliCallback()
        filename1 = self.mkstemp(prefix='bleachbit-test-worker')
        filename2 = self.mkstemp(prefix='bleachbit-test-worker')

        astr1 = '<action command="delete" search="file" path="%s"/>' % filename1
        astr2 = '<action command="delete" search="file" path="%s"/>' % filename2
        cleaner = TestCleaner.actions_to_cleaner([astr1, astr2])
        backends['test'] = cleaner
        operations = {'test': ['option1', 'option2']}
        worker = Worker(ui, True, operations)
        run = worker.run()
        while next(run):
            pass
        del backends['test']
        self.assertNotExists(filename1)
        self.assertNotExists(filename2)
        self.assertEqual(worker.total_special, 0)
        self.assertEqual(worker.total_errors, 0)
        self.assertEqual(worker.total_deleted, 2)
