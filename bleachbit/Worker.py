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
Perform the preview or delete operations
"""


from gettext import gettext as _
import os
import sys
import traceback
import unittest

import FileUtilities
from Cleaner import backends

if 'nt' == os.name:
    import Windows
else:
    from General import WindowsError



class Worker:
    """Perform the preview or delete operations"""
    def __init__(self, ui, really_delete, operations):
        """Create a Worker

        ui: an instance with methods
            append_text()
            update_progress_bar()
            update_total_size()
            worker_done()
        really_delete: (boolean) preview or make real changes?
        operations: dictionary where operation-id is the key and
            operation-id are values
        """
        self.ui = ui
        self.really_delete = really_delete
        self.operations = operations
        self.total_bytes = 0
        self.total_deleted = 0
        self.total_errors = 0
        self.total_special = 0 # special operations
        self.yield_time = None
        if 0 == len(self.operations):
            raise RuntimeError("No work to do")


    def print_exception(self, operation):
        """Display exception"""
        # TRANSLATORS: This indicates an error.  The special keyword
        # %(operation)s will be replaced by 'firefox' or 'opera' or
        # some other cleaner ID.  The special keyword %(msg)s will be
        # replaced by a message such as 'Permission denied.'
        err = _("Exception while running operation '%(operation)s': '%(msg)s'") \
            %  { 'operation': operation, 'msg' : str(sys.exc_info()[1]) }
        print err
        traceback.print_exc()
        self.ui.append_text(err + "\n", 'error')
        self.total_errors += 1


    def execute(self, cmd):
        """Execute or preview the command"""
        ret = None
        line = None
        tag = None
        try:
            for ret in cmd.execute(self.really_delete):
                if True == ret:
                    # temporarily pass control to the GTK idle loop
                    yield True
        except Exception, e:
            # 2 = does not exist
            # 13 = permission denied
            if not (isinstance(e, OSError) and e.errno in (2, 13)):
                traceback.print_exc()
            line = "%s\n" % (str(sys.exc_info()[1]))
            tag = 'error'
            self.total_errors += 1
        else:
            if None == ret:
                return
            if isinstance(ret['size'], (int, long)):
                size = FileUtilities.bytes_to_human(ret['size'])
                self.total_bytes += ret['size']
            else:
                size = "?B"
            if ret['path']:
                path = ret['path']
            else:
                path = ''
            line = "%s %s %s\n" % (ret['label'], size, path)
            self.total_deleted += ret['n_deleted']
            self.total_special += ret['n_special']

        self.ui.append_text(line, tag)


    def clean_operation(self, operation):
        """Perform a single cleaning operation"""
        operation_options = self.operations[operation]
        print "debug: clean_operation('%s'), options = '%s'" % (operation, operation_options)
        if self.really_delete and backends[operation].is_running():
            # TRANSLATORS: %s expands to a name such as 'Firefox' or 'System'.
            err = _("%s cannot be cleaned because it is currently running.  Close it, and try again.") \
                % backends[operation].get_name()
            self.ui.append_text(err + "\n", 'error')
            self.total_errors += 1
            return
        import time
        self.yield_time = time.time()

        if operation_options:
            for (option_id, value) in operation_options:
                # fixme: remove the values (true/false)
                if not value:
                    # option is disabled, so skip it
                    continue
                for cmd in backends[operation].get_commands(option_id):
                    for ret in self.execute(cmd):
                        if True == ret:
                            # Return control to PyGTK idle loop to keep
                            # it responding allow the user to abort
                            self.yield_time = time.time()
                            yield True
                    if time.time() - self.yield_time > 0.25:
                        if self.really_delete:
                            self.ui.update_total_size(self.total_bytes)
                        yield True
                        self.yield_time = time.time()


    def run(self):
        """Perform the main cleaning process"""
        count = 0
        for operation in self.operations:
            self.ui.update_progress_bar(1.0 * count / len(self.operations))
            name = backends[operation].get_name()
            if self.really_delete:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Cleaning %s.") % name
            else:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Previewing %s.") % name
            self.ui.update_progress_bar(msg)
            for dummy in self.clean_operation(operation):
                yield True
            count += 1

        # print final stats
        bytes_delete = FileUtilities.bytes_to_human(self.total_bytes)
        if self.really_delete:
            # TRANSLATORS: This refers to disk space that was
            # really recovered (in other words, not a preview)
            line =  _("Disk space recovered: %s") % bytes_delete
        else:
            # TRANSLATORS: This refers to a preview (no real
            # changes were made yet)
            line =  _("Disk space to be recovered: %s") % bytes_delete
        self.ui.append_text("\n%s" % line)
        if self.really_delete:
            # TRANSLATORS: This refers to the number of files really
            # deleted (in other words, not a preview).
            line = _("Files deleted: %d") % self.total_deleted
        else:
            # TRANSLATORS: This refers to the number of files that
            # would be deleted (in other words, simply a preview).
            line = _("Files to be deleted: %d") % self.total_deleted
        self.ui.append_text("\n%s" % line)
        if self.total_special > 0:
            line =  _("Special operations: %d") % self.total_special
            self.ui.append_text("\n%s" % line)
        if self.total_errors > 0:
            line = _("Errors: %d") % self.total_errors
            self.ui.append_text("\n%s" % line, 'error')

        if self.really_delete:
            self.ui.update_total_size(self.total_bytes)
        self.ui.worker_done(self, self.really_delete)

        yield False


class TestWorker(unittest.TestCase):
    """Unit test for module Worker"""

    def test_TestActionProvider(self):
        """Test Worker using Action.TestActionProvider"""
        import CLI
        import Cleaner
        import tempfile
        ui = CLI.CliCallback()
        (fd, filename) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, '123')
        os.close(fd)
        self.assert_(os.path.exists(filename))
        astr = '<action command="test">%s</action>' % filename
        cleaner = Cleaner.TestCleaner.action_to_cleaner(astr)
        backends['test'] = cleaner
        operations = { 'test' : [ ('option1', True ) ] }
        w = Worker(ui, True, operations)
        run = w.run()
        while run.next():
            pass
        self.assert_(not os.path.exists(filename))
        self.assertEqual(w.total_special, 3)
        self.assertEqual(w.total_errors, 2)
        if 'posix' == os.name:
            self.assertEqual(w.total_bytes, 4096+10+10)
            self.assertEqual(w.total_deleted, 2)
        elif 'nt' == os.name:
            self.assertEqual(w.total_bytes, 3+3+10+10)
            self.assertEqual(w.total_deleted, 3)


if __name__ == '__main__':
    unittest.main()

