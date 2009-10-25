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

from Cleaner import backends
import Common
import General



class CliCallback:
    """Command line's callback passed to Worker"""


    def __init__(self):
        """Initialize CliCallback"""
        import locale
        self.encoding = locale.getdefaultlocale()[1]
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


def cleaners_list():
    """Yield each cleaner-option pair"""
    init_cleaners()
    cleaners = []
    for key in sorted(backends):
        c_name = backends[key].get_name()
        c_id = backends[key].get_id()
        for (o_id, o_name) in backends[key].get_options():
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
    parser.add_option("-d", "--delete", action = "store_true",
        help = _("delete files and make other permanent changes"))
    parser.add_option("-p", "--preview", action = "store_true",
        help = _("preview files to be deleted and other changes"))
    parser.add_option("-v", "--version", action = "store_true",
        help = _("output version information and exit"))
    parser.add_option('-o', '--overwrite', action = 'store_true',
        help = _('overwrite files to hide contents'))
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
    if options.overwrite:
        import Options
        Options.options.set('shred', True, commit = False)
    if options.delete:
        operations = args_to_operations(args)
        preview_or_delete(operations, True)
        sys.exit(0)
    parser.print_help()



class TestCLI(unittest.TestCase):
    """Unit test for module CLI"""


    def _test_preview(self, args, stdout = None, env = None):
        """Helper to test preview"""
        # Use devnull because in some cases the buffer will be too large,
        # and the other alternative, the screen, is not desirable.
        if stdout:
            stdout_ = None
        else:
            stdout_ = open(os.devnull, 'w')
        output = General.run_external(args, stdout = stdout_, env = env)
        if not stdout:
            stdout_.close()
        self.assertEqual(output[0], 0)
        print output
        pos = output[2].find('Traceback (most recent call last)')
        if pos > -1:
            print "Saw the following error when using args '%s':\n %s" \
                % (args, output[2])
        self.assertEqual(pos, -1)


    def test_args_to_operations(self):
        """Unit test for args_to_operations()"""
        tests = ( ( ['adobe_reader.*'], {'adobe_reader' : [ u'cache', u'mru', u'tmp' ] } ),
            ( ['adobe_reader.mru'], {'adobe_reader' : [ u'mru' ] } ) )
        for test in tests:
            o = args_to_operations(test[0])
            self.assertEqual(o, test[1])


    def test_cleaners_list(self):
        """Unit test for cleaners_list()"""
        for cleaner in cleaners_list():
            self.assert_ (type(cleaner) is str or type(cleaner) is unicode)


    def test_init_cleaners(self):
        """Unit test for init_cleaners()"""
        init_cleaners()


    def test_encoding(self):
        """Unit test for encoding"""
        if 'posix' != os.name:
            return

        import tempfile
        (fd, filename) = tempfile.mkstemp(prefix = 'encoding-\xe4\xf6\xfc~', dir = '/tmp')
        os.close(fd)
        self.assert_(os.path.exists(filename))

        import copy
        env = copy.deepcopy(os.environ)
        env['LANG'] = 'en_US' # not UTF-8
        path = os.path.join('bleachbit', 'CLI.py')
        args = [sys.executable, path, '-p', 'system.tmp']
        # If Python pipes stdout to file or devnull, the test may give
        # a false negative.  It must print stdout to terminal.
        self._test_preview(args, stdout = True, env = env)

        os.remove(filename)
        self.assert_(not os.path.exists(filename))


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
            self._test_preview(args)


    def test_delete(self):
        """Unit test for --delete option"""
        import tempfile
        import FileUtilities
        (fd, filename) = tempfile.mkstemp('bleachbit-test')
        os.close(fd)
        # replace delete function for testing
        save_delete = FileUtilities.delete
        deleted_paths = []
        def dummy_delete(path, shred = False):
            deleted_paths.append(path)
        FileUtilities.delete = dummy_delete
        operations = args_to_operations(['system.tmp'])
        preview_or_delete(operations, True)
        FileUtilities.delete = save_delete
        self.assert_(filename in deleted_paths)
        os.remove(filename)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'tests':
        print 'info: running CLI unit tests'
        del sys.argv[1]
        unittest.main()
    else:
        process_cmd_line()

