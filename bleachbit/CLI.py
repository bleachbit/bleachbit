#!/usr/bin/env python
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
Command line interface
"""



from gettext import gettext as _
import optparse
import sys

from CleanerBackend import backends
import Common


class CliCallback:
    def append_text(self, msg, tag = None):
        print msg.strip('\n')

    def update_progress_bar(self, status):
        # not used
        pass

    def update_total_size(self, size):
        # not used
        pass

    def worker_done(self, worker, really_delete):
        # not used
        pass


def init_cleaners():
    """Prepare the cleaners for use"""
    import CleanerML
    CleanerML.load_cleaners()


def list_cleaners():
    """List available cleaners"""
    init_cleaners()
    for key in sorted(backends):
        c_name = backends[key].get_name()
        c_id = backends[key].get_id()
        for (o_id, o_name, o_value) in backends[key].get_options():
            print "%s.%s" % (c_id, o_id)


def preview(operations):
    """Preview deletes and other changes"""
    import Worker
    cb = CliCallback()
    worker = Worker.Worker(cb, False, operations).run()
    while worker.next():
        pass


def args_to_operations(args):
    """Read arguments and return list of operations"""
    init_cleaners()
    operations = {}
    for arg in args:
        if 2 != len(arg.split('.')):
            print _("not a valid cleaner: %s") % arg
            continue
        (cleaner_id, option_id) = arg.split('.')
        # default to false
        if not operations.has_key(cleaner_id):
            operations[cleaner_id] = []
            for option in backends[cleaner_id].get_options():
                operations[cleaner_id].append( [ option_id, False ] )
        # change the specified option
        for option in operations[cleaner_id]:
            try:
                operations[cleaner_id].remove( [ option_id, False ] )
            except ValueError:
                pass
            try:
                operations[cleaner_id].remove( [ option_id, True ] ) # prevent duplicates
            except ValueError:
                pass
            operations[cleaner_id].append( [ option_id, True ] )
    return operations


def process_cmd_line():
    """Parse the command line and execute given commands."""
    parser = optparse.OptionParser()
    parser.add_option("-l", "--list-cleaners", action = "store_true",
        help = _("list cleaners"))
    parser.add_option("-p", "--preview", action = "store_true",
        help = _("preview files to be deleted and other changes"))
    parser.add_option("-v", "--version", action = "store_true",
        help = _("output version information and exit"))
    (options, args) = parser.parse_args()
    if options.version:
        print """
BleachBit version %s
Copyright (C) 2009 Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""" % Common.APP_VERSION
        sys.exit(0)
    if options.list_cleaners:
        list_cleaners()
        sys.exit(0)
    if options.preview:
        operations = args_to_operations(args)
        preview(operations)


if __name__ == '__main__':
    process_cmd_line()

