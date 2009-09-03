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
import gtk
import os
import sys
import traceback

import FileUtilities
from CleanerBackend import backends

if 'nt' == os.name:
    import Windows
else:
    class WindowsError(Exception):
        """Dummy class for non-Windows systems"""
        def __str__(self):
            return 'this is a dummy class for non-Windows systems'



class Worker:
    """Perform the preview or delete operations"""
    def __init__(self, ui, really_delete, operations):
        """Create a Worker

        ui: an instance with methods
            append_text()
            update_progress_bar()
            update_total_size()
        really_delete: (boolean) preview or make real changes?
        operations: dictionary where operation-id is the key and
            operation-id are values
        """
        self.ui = ui
        self.really_delete = really_delete
        self.operations = operations
        self.total_bytes = 0
        if 0 == len(self.operations):
            raise("No work to do")




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


    def clean_operation(self, operation):
        """Perform a single cleaning operation"""
        operation_options = self.operations[operation]
        print "debug: clean_operation('%s'), options = '%s'" % (operation, operation_options)
        if self.really_delete and backends[operation].is_running():
            # TRANSLATORS: %s expands to a name such as 'Firefox' or 'System'.
            err = _("%s cannot be cleaned because it is currently running.  Close it, and try again.") \
                % backends[operation].get_name()
            self.ui.append_text(err + "\n", 'error')
            return
        if operation_options:
            for (option, value) in operation_options:
                backends[operation].set_option(option, value)

        # standard operation
        import time
        start_time = time.time()
        try:
            for pathname in backends[operation].list_files():
                try:
                    self.clean_pathname(pathname)
                except:
                    self.print_exception(operation)

                if time.time() - start_time >= 0.25:
                    if self.really_delete:
                        self.ui.update_total_size(self.total_bytes)
                    # return control to PyGTK idle loop
                    yield True
                    start_time = time.time()
        except:
            self.print_exception(operation)

        # special operation
        try:
            for ret in backends[operation].other_cleanup(self.really_delete):
                if None == ret:
                    return
                if self.really_delete:
                    self.total_bytes += ret[0]
                    line = "* " + FileUtilities.bytes_to_human(ret[0]) + " " + ret[1] + "\n"
                    if self.really_delete:
                        self.ui.update_total_size(self.total_bytes)
                else:
                    line = _("Special operation: ") + ret + "\n"
                self.ui.append_text(line)
                if self.really_delete:
                    self.ui.update_total_size(self.total_bytes)
                yield True
        except:
            self.print_exception(operation)


    def clean_pathname(self, pathname):
        """Clean a single pathname"""
        try:
            size_bytes = FileUtilities.getsize(pathname)
        except:
            self.print_exception(operation)

        tag = None
        error = False
        try:
            if self.really_delete:
                FileUtilities.delete(pathname)
        except WindowsError, e:
            # WindowsError: [Error 145] The directory is not empty:
            # 'C:\\Documents and Settings\\username\\Local Settings\\Temp\\NAILogs'
            # Error 145 may happen if the files are scheduled for deletion
            # during reboot.
            if 145 == e.winerror:
                print "info: directory '%s' is not empty" % (pathname)
            # WindowsError: [Error 32] The process cannot access the file because it is being
            # used by another process: u'C:\\Documents and Settings\\username\\Cookies\\index.dat'
            elif 32 != e.winerror:
                raise
            try:
                Windows.delete_locked_file(pathname)
            except:
                error = True
            else:
                size_text = FileUtilities.bytes_to_human(size_bytes)
                # TRANSLATORS: This indicates the file will be deleted
                # when Windows reboots.  The special keyword %(size)s
                # changes to a size such as 320.1KB.
                line = _("Marked for deletion: %(size)s %(pathname)s") % \
                    { 'size' : size_text, 'pathname' : pathname }
                line += "\n"
        except:
            error = True
        else:
            size_text = FileUtilities.bytes_to_human(size_bytes)
            line = "%s %s\n" % (size_text, pathname)

        if error:
            traceback.print_exc()
            line = "%s %s\n" % (str(sys.exc_info()[1]), pathname)
            tag = 'error'
        else:
            self.total_bytes += size_bytes

        self.ui.append_text(line, tag)


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

        self.finish()
        yield False


    def finish(self):
        """Finish the cleaning process."""

        line = "\n%s%s" % ( _("Total size: "), FileUtilities.bytes_to_human(self.total_bytes))
        self.ui.append_text(line)
        if self.really_delete:
            self.ui.update_total_size(self.total_bytes)
        self.ui.worker_done()


