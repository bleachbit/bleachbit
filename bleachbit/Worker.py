# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
import sys
import traceback

import gtk

import FileUtilities
from CleanerBackend import backends


class Worker:
    """Perform the preview or delete operations"""
    def __init__(self, gui, really_delete):
        self.gui = gui
        self.really_delete = really_delete
        self.operations = gui.get_selected_operations()
        if 0 == len(self.operations):
            dialog = gtk.MessageDialog(gui.window, gtk.DIALOG_MODAL \
                | gtk.DIALOG_DESTROY_WITH_PARENT, \
                gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, \
                _("You must select an operation"))
            dialog.run()
            dialog.destroy()
            raise RuntimeError('No operation selected')
        gui.set_sensitive(False)
        gui.textbuffer.set_text("")
        self.__iter = gui.textbuffer.get_iter_at_offset(0)
        gui.progressbar.show()
        self.total_bytes = 0


    def clean_operation(self, operation):
        """Perform a single cleaning operation"""
        operation_options = self.gui.get_operation_options(operation)
        print "debug: clean_operation('%s'), options = '%s'" % (operation, operation_options)
        if operation_options:
            for (option, value) in operation_options:
                backends[operation].set_option(option, value)

        # standard operation
        import time
        start_time = time.time()
        try:
            for pathname in backends[operation].list_files():
                self.clean_pathname(pathname)
                if time.time() - start_time >= 0.25:
                    yield True
                    start_time = time.time()
        except:
            # Translators: This indicates an error.  The first %s
            # may be 'firefox' (for example) and the second something
            # like 'Permission denied'
            err = _("Exception while running operation '%s': '%s'") \
                % (operation, str(sys.exc_info()[1]))
            print err
            traceback.print_exc()
            self.gui.append_text(err + "\n", 'error', self.__iter)

        # special operation
        try:
            for ret in backends[operation].other_cleanup(self.really_delete):
                if None == ret:
                    return
                if self.really_delete:
                    self.total_bytes += ret[0]
                    line = "* " + FileUtilities.bytes_to_human(ret[0]) + " " + ret[1] + "\n"
                else:
                    line = _("Special operation: ") + ret + "\n"
                self.gui.textbuffer.insert(self.__iter, line)
                yield True
        except:
            err = _("Exception while running operation '%s': '%s'") \
                % (operation, str(sys.exc_info()[1]))
            print err
            traceback.print_exc()
            self.gui.append_text(err + "\n", 'error', self.__iter)


    def clean_pathname(self, pathname):
        """Clean a single pathname"""
        try:
            bytes = FileUtilities.getsize(pathname)
        except:
            traceback.print_exc()
            line = str(sys.exc_info()[1]) + " " + pathname + "\n"
            print line
            self.gui.append_text(line, 'error', self.__iter)
        else:
            tag = None
            try:
                if self.really_delete:
                    FileUtilities.delete(pathname)
            except:
                traceback.print_exc()
                line = str(sys.exc_info()[1]) + " " + pathname + "\n"
                tag = 'error'
            else:
                self.total_bytes += bytes
                line = FileUtilities.bytes_to_human(bytes) + " " + pathname + "\n"
            self.gui.append_text(line, tag, self.__iter)


    def run(self):
        """Perform the main cleaning process"""
        count = 0
        for operation in self.operations:
            self.gui.progressbar.set_fraction(1.0 * count / len(self.operations))
            if self.really_delete:
                self.gui.progressbar.set_text(_("Please wait.  Scanning and deleting: ") \
                    + operation)
            else:
                self.gui.progressbar.set_text(_("Please wait.  Scanning: ") + operation)
            for dummy in self.clean_operation(operation):
                yield True
            count += 1

        self.finish()
        yield False


    def finish(self):
        """Finish the cleaning process.  Restore the previous GUI state."""
        self.gui.progressbar.set_text("")
        self.gui.progressbar.set_fraction(1)
        self.gui.progressbar.set_text(_("Done."))
        self.gui.textbuffer.insert(self.__iter, "\n" + _("Total size: ") \
             + FileUtilities.bytes_to_human(self.total_bytes))
        self.gui.set_sensitive(True)

