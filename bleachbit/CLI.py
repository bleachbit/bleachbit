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
import os
import sys
import unittest

from CleanerBackend import backends
import Common
import General



class CliCallback:
    """Command line's callback passed to Worker"""


    def append_text(self, msg, tag = None):
        """Write text to the terminal"""
        print msg.strip('\n')


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


def cleaners_list():
    """Yield each cleaner-option pair"""
    init_cleaners()
    cleaners = []
    for key in sorted(backends):
        c_name = backends[key].get_name()
        c_id = backends[key].get_id()
        for (o_id, o_name, o_value) in backends[key].get_options():
            yield "%s.%s" % (c_id, o_id)


def list_cleaners():
    """Display available cleaners"""
    for cleaner in cleaners_list():
        print cleaner


def preview_or_delete(operations, really_delete):
    """Preview deletes and other changes"""
    import Worker
    cb = CliCallback()
    worker = Worker.Worker(cb, really_delete, operations).run()
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
        default = False
        # enable all options (for example, firefox.*)
        if '*' == option_id:
            default = True
            if operations.has_key(cleaner_id):
                del operations[cleaner_id]
        # default to false
        if not operations.has_key(cleaner_id):
            operations[cleaner_id] = []
            for (option_id2, o_name, o_value) in backends[cleaner_id].get_options():
                operations[cleaner_id].append( [ option_id2, default ] )
        if '*' == option_id:
            continue
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
    # TRANSLATORS: This is the command line usage.  Don't translate
    # %prog, but do translate usage, options, cleaner, and option.
    # More information about the command line is here
    # http://bleachbit.sourceforge.net/documentation/command-line
    usage = _("usage: %prog [options] cleaner.option1 cleaner.option2")
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", "--list-cleaners", action = "store_true",
        help = _("list cleaners"))
    parser.add_option("-d", "--delete", action = "store_true",
        help = _("delete files and make other permanent changes"))
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
        preview_or_delete(operations, False)
        sys.exit(0)
    if options.delete:
        operations = args_to_operations(args)
        preview_or_delete(operations, True)
        sys.exit(0)
    parser.print_help()




class TestCLI(unittest.TestCase):
    """Unit test for module CLI"""


    def test_cleaners_list(self):
        """Unit test for cleaners_list()"""
        for cleaner in cleaners_list():
            self.assert_ (type(cleaner) is str or type(cleaner) is unicode)


    def test_init_cleaners(self):
        """Unit test for init_cleaners()"""
        init_cleaners()


    def test_invalid_locale(self):
        """Unit test for invalid locales"""
        os.environ['LANG'] = 'blahfoo'
        # tests are run from the parent directory
        path = os.path.join('bleachbit', 'CLI.py')
        args = [sys.executable, path, '--version']
        output = General.run_external(args)
        self.assertNotEqual(output[1].find('Copyright'), -1, str(output))


    def test_preview(self):
        """Unit test for --preview option"""
        args_list = []
        path = os.path.join('bleachbit', 'CLI.py')
        big_args = [sys.executable, path, '--preview', ]
        for cleaner in cleaners_list():
            args_list.append([sys.executable, path, '--preview', cleaner])
            big_args.append(cleaner)
        args_list.append(big_args)

        for args in args_list:
            devnull = open(os.devnull, 'w')
            output = General.run_external(args, stdout = devnull)
            devnull.close()
            pos = output[2].find('Traceback (most recent call last)')
            if pos > -1:
                print output[2]
            self.assertEqual(pos, -1)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'tests':
        print 'info: running CLI unit tests'
        del sys.argv[1]
        unittest.main()
    else:
        process_cmd_line()

