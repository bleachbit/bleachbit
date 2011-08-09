#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2011 Andrew Ziem
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



import optparse
import os
import sys

from Cleaner import backends
from Common import _, APP_VERSION
import Options
import Worker



class CliCallback:
    """Command line's callback passed to Worker"""


    def __init__(self):
        """Initialize CliCallback"""
        import locale
        try:
            self.encoding = locale.getdefaultlocale()[1]
        except:
            self.encoding = None
        if not self.encoding:
            self.encoding = 'UTF8'


    def append_text(self, msg, tag = None):
        """Write text to the terminal"""
        # If the encoding is not explictly handled on a non-UTF-8
        # system, then special Latin-1 characters such as umlauts may
        # raise an exception as an encoding error.
        print msg.strip('\n').encode(self.encoding, 'replace')


    def update_progress_bar(self, status):
        """Not used"""
        pass


    def update_total_size(self, size):
        """Not used"""
        pass


    def worker_done(self, worker, really_delete):
        """Not used"""
        pass


def init_cleaners():
    """Prepare the cleaners for use"""
    import CleanerML
    CleanerML.load_cleaners()
    if 'nt' == os.name:
        import Winapp
        Winapp.load_cleaners()


def cleaners_list():
    """Yield each cleaner-option pair"""
    init_cleaners()
    for key in sorted(backends):
        c_id = backends[key].get_id()
        for (o_id, o_name) in backends[key].get_options():
            yield "%s.%s" % (c_id, o_id)


def list_cleaners():
    """Display available cleaners"""
    for cleaner in cleaners_list():
        print cleaner


def preview_or_clean(operations, really_clean):
    """Preview deletes and other changes"""
    cb = CliCallback()
    worker = Worker.Worker(cb, really_clean, operations).run()
    while worker.next():
        pass


def args_to_operations(args, preset):
    """Read arguments and return list of operations"""
    init_cleaners()
    operations = {}
    if preset:
        # restore presets from the GUI
        for key in sorted(backends):
            c_id = backends[key].get_id()
            for (o_id, o_name) in backends[key].get_options():
                if Options.options.get_tree(c_id, o_id):
                    args.append('.'.join([ c_id, o_id ]) )
    for arg in args:
        if 2 != len(arg.split('.')):
            print _("not a valid cleaner: %s") % arg
            continue
        (cleaner_id, option_id) = arg.split('.')
        # enable all options (for example, firefox.*)
        if '*' == option_id:
            if operations.has_key(cleaner_id):
                del operations[cleaner_id]
            operations[cleaner_id] = []
            for (option_id2, o_name) in backends[cleaner_id].get_options():
                operations[cleaner_id].append( option_id2 )
            continue
        # add the specified option
        if not operations.has_key(cleaner_id):
            operations[cleaner_id] = []
        if not option_id in operations[cleaner_id]:
            operations[cleaner_id].append( option_id )
    for (k, v) in operations.iteritems():
        operations[k] = sorted(v)
    return operations


def process_cmd_line():
    """Parse the command line and execute given commands."""
    # TRANSLATORS: This is the command line usage.  Don't translate
    # %prog, but do translate usage, options, cleaner, and option.
    # More information about the command line is here
    # http://bleachbit.sourceforge.net/documentation/command-line
    usage = _("usage: %prog [options] cleaner.option1 cleaner.option2")
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", "--list-cleaners", action = "store_true",
        help = _("list cleaners"))
    parser.add_option("-c", "--clean", action = "store_true",
        help = _("delete files and make other permanent changes"))
    parser.add_option("-d", "--delete", action = "store_true",
        help = _("depreciated alias for --clean"))
    parser.add_option("--sysinfo", action = "store_true",
        help = _("show system information"))
    parser.add_option("-p", "--preview", action = "store_true",
        help = _("preview files to be deleted and other changes"))
    parser.add_option("--preset", action="store_true",
        help = _("use options set in the graphical interface"))
    parser.add_option("-v", "--version", action = "store_true",
        help = _("output version information and exit"))
    parser.add_option('-o', '--overwrite', action = 'store_true',
        help = _('overwrite files to hide contents'))
    (options, args) = parser.parse_args()
    if options.version:
        print """
BleachBit version %s
Copyright (C) 2011 Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""" % APP_VERSION
        sys.exit(0)
    if options.list_cleaners:
        list_cleaners()
        sys.exit(0)
    if options.preview:
        operations = args_to_operations(args, options.preset)
        preview_or_clean(operations, False)
        sys.exit(0)
    if options.overwrite:
        Options.options.set('shred', True, commit = False)
    if options.delete or options.clean:
        operations = args_to_operations(args, options.preset)
        preview_or_clean(operations, True)
        sys.exit(0)
    if options.sysinfo:
        import Diagnostic
        print Diagnostic.diagnostic_info()
        sys.exit(0)
    parser.print_help()




if __name__ == '__main__':
    process_cmd_line()

