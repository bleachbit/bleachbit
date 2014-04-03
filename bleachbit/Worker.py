# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Perform the preview or delete operations
"""


import math
import os
import sys
import traceback

import DeepScan
import FileUtilities
from Cleaner import backends
from Common import _, ungettext


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
        assert(isinstance(operations, dict))
        self.operations = operations
        self.total_bytes = 0
        self.total_deleted = 0
        self.total_errors = 0
        self.total_special = 0  # special operations
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
            % {'operation': operation, 'msg': str(sys.exc_info()[1])}
        print err
        traceback.print_exc()
        self.ui.append_text(err + "\n", 'error')
        self.total_errors += 1

    def execute(self, cmd):
        """Execute or preview the command"""
        ret = None
        try:
            for ret in cmd.execute(self.really_delete):
                if True == ret or isinstance(ret, tuple):
                    # Temporarily pass control to the GTK idle loop,
                    # allow user to abort, and
                    # display progress (if applicable).
                    yield ret
        except SystemExit:
            pass
        except Exception, e:
            # 2 = does not exist
            # 13 = permission denied
            from errno import ENOENT, EACCES
            if not (isinstance(e, OSError) and e.errno in (ENOENT, EACCES)):
                traceback.print_exc()
            line = "%s\n" % (str(sys.exc_info()[1]))
            self.total_errors += 1
            self.ui.append_text(line, 'error')
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
            path = path.decode('utf8', 'replace')  # for invalid encoding
            line = u"%s %s %s\n" % (ret['label'], size, path)
            self.total_deleted += ret['n_deleted']
            self.total_special += ret['n_special']
            self.ui.append_text(line)

    def clean_operation(self, operation):
        """Perform a single cleaning operation"""
        operation_options = self.operations[operation]
        assert(isinstance(operation_options, list))
        print "debug: clean_operation('%s'), options = '%s'" % (operation, operation_options)

        if not operation_options:
            raise StopIteration

        if self.really_delete and backends[operation].is_running():
            # TRANSLATORS: %s expands to a name such as 'Firefox' or 'System'.
            err = _("%s cannot be cleaned because it is currently running.  Close it, and try again.") \
                % backends[operation].get_name()
            self.ui.append_text(err + "\n", 'error')
            self.total_errors += 1
            return
        import time
        self.yield_time = time.time()

        for option_id in operation_options:
            assert(isinstance(option_id, (str, unicode)))
            # normal scan
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
            # deep scan
            for ds in backends[operation].get_deep_scan(option_id):
                if '' == ds['path']:
                    ds['path'] = os.path.expanduser('~')
                if 'delete' != ds['command']:
                    raise NotImplementedError(
                        'Deep scan only supports deleting now')
                if not self.deepscans.has_key(ds['path']):
                    self.deepscans[ds['path']] = []
                self.deepscans[ds['path']].append(ds)

    def run_delayed_op(self, operation, option_id):
        """Run one delayed operation"""
        self.ui.update_progress_bar(0.0)
        if 'free_disk_space' == option_id:
            # TRANSLATORS: 'free' means 'unallocated'
            msg = _("Please wait.  Wiping free disk space.")
        elif 'memory' == option_id:
            msg = _("Please wait.  Cleaning %s.") % _("Memory")
        else:
            raise RuntimeError("Unexpected option_id in delayed ops")
        self.ui.update_progress_bar(msg)
        for cmd in backends[operation].get_commands(option_id):
            old_phase = None
            for ret in self.execute(cmd):
                if isinstance(ret, tuple):
                    # Display progress (for free disk space)
                    phase = ret[
                        0]  # 1=wipe free disk space, 2=wipe inodes, 3=clean up inodes files
                    percent_done = ret[1]
                    eta_seconds = ret[2]
                    self.ui.update_progress_bar(percent_done)
                    if phase == 2:
                        msg = _('Please wait. Wiping file system metadata.')
                    elif phase == 3:
                        msg = _(
                            'Please wait. Cleaning up after wiping file system metadata.')
                    if isinstance(eta_seconds, int):
                        eta_mins = math.ceil(eta_seconds / 60)
                        msg2 = ungettext("About %d minute remaining.",
                                         "About %d minutes remaining.", eta_mins) \
                            % eta_mins
                        self.ui.update_progress_bar(msg + ' ' + msg2)
                    else:
                        self.ui.update_progress_bar(msg)
                if True == ret or isinstance(ret, tuple):
                    # Return control to PyGTK idle loop to keep
                    # it responding and allow the user to abort.
                    yield True

    def run(self):
        """Perform the main cleaning process which has these phases
        1. General cleaning
        2. Deep scan
        3. Memory
        4. Free disk space"""
        self.deepscans = {}
        # prioritize
        self.delayed_ops = []
        for operation in self.operations:
            delayables = ['free_disk_space', 'memory']
            for delayable in delayables:
                if operation not in ('system', '_gui'):
                    continue
                if delayable in self.operations[operation]:
                    i = self.operations[operation].index(delayable)
                    del self.operations[operation][i]
                    priority = 99
                    if 'free_disk_space' == delayable:
                        priority = 100
                    new_op = (priority, {operation: [delayable]})
                    self.delayed_ops.append(new_op)

        # standard operations
        for dummy in self.run_operations(self.operations):
            # yield to GTK+ idle loop
            yield True

        # run deep scan
        if self.deepscans:
            for dummy in self.run_deep_scan():
                yield dummy

        # delayed operations
        for op in sorted(self.delayed_ops):
            operation = op[1].keys()[0]
            for option_id in op[1].values()[0]:
                for ret in self.run_delayed_op(operation, option_id):
                    # yield to GTK+ idle loop
                    yield True

        # print final stats
        bytes_delete = FileUtilities.bytes_to_human(self.total_bytes)
        if self.really_delete:
            # TRANSLATORS: This refers to disk space that was
            # really recovered (in other words, not a preview)
            line = _("Disk space recovered: %s") % bytes_delete
        else:
            # TRANSLATORS: This refers to a preview (no real
            # changes were made yet)
            line = _("Disk space to be recovered: %s") % bytes_delete
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
            line = _("Special operations: %d") % self.total_special
            self.ui.append_text("\n%s" % line)
        if self.total_errors > 0:
            line = _("Errors: %d") % self.total_errors
            self.ui.append_text("\n%s" % line, 'error')

        if self.really_delete:
            self.ui.update_total_size(self.total_bytes)
        self.ui.worker_done(self, self.really_delete)

        yield False

    def run_deep_scan(self):
        """Run deep scans"""
        print 'debug: deepscans=', self.deepscans
        # TRANSLATORS: The "deep scan" feature searches over broad
        # areas of the file system such as the user's whole home directory
        # or all the system executables.
        self.ui.update_progress_bar(_("Please wait.  Running deep scan."))
        yield True  # allow GTK to update the screen
        ds = DeepScan.DeepScan()
        for (path, dsdict) in self.deepscans.iteritems():
            print 'debug: deepscan path=', path
            print 'debug: deepscan dict=', dsdict
            for dsdict2 in dsdict:
                ds.add_search(path, dsdict2['regex'])

        for path in ds.scan():
            if True == path:
                yield True
                continue
            # fixme: support non-delete commands
            import Command
            cmd = Command.Delete(path)
            for ret in self.execute(cmd):
                yield True

    def run_operations(self, my_operations):
        """Run a set of operations (general, memory, free disk space)"""
        count = 0
        for operation in my_operations:
            self.ui.update_progress_bar(1.0 * count / len(my_operations))
            name = backends[operation].get_name()
            if self.really_delete:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Cleaning %s.") % name
            else:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Previewing %s.") % name
            self.ui.update_progress_bar(msg)
            yield True  # show the progress bar message now
            try:
                for dummy in self.clean_operation(operation):
                    yield True
            except:
                self.print_exception(operation)

            count += 1
