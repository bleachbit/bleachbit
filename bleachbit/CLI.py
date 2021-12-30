#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Command line interface
"""

from bleachbit.Cleaner import backends, create_simple_cleaner, register_cleaners
from bleachbit import _, APP_VERSION
from bleachbit import SystemInformation, Options, Worker

import logging
import optparse
import os
import sys

logger = logging.getLogger(__name__)


class CliCallback:
    """Command line's callback passed to Worker"""

    def __init__(self, quiet=False):
        self.quiet = quiet

    def append_text(self, msg, tag=None):
        """Write text to the terminal"""
        if not self.quiet:
            print(msg.strip('\n'))

    def update_progress_bar(self, status):
        """Not used"""
        pass

    def update_total_size(self, size):
        """Not used"""
        pass

    def update_item_size(self, op, opid, size):
        """Not used"""
        pass

    def worker_done(self, worker, really_delete):
        """Not used"""
        pass


def cleaners_list():
    """Yield each cleaner-option pair"""
    list(register_cleaners())
    for key in sorted(backends):
        c_id = backends[key].get_id()
        for (o_id, _o_name) in backends[key].get_options():
            yield "%s.%s" % (c_id, o_id)


def list_cleaners():
    """Display available cleaners"""
    for cleaner in cleaners_list():
        print (cleaner)


def preview_or_clean(operations, really_clean, quiet=False):
    """Preview deletes and other changes"""
    cb = CliCallback(quiet)
    worker = Worker.Worker(cb, really_clean, operations).run()
    while next(worker):
        pass


def args_to_operations_list(preset, all_but_warning):
    """For --preset and --all-but-warning return list of operations as list

    Example return: ['google_chrome.cache', 'system.tmp']
    """
    args = []
    if not backends:
        list(register_cleaners())
    assert(len(backends) > 1)
    for key in sorted(backends):
        c_id = backends[key].get_id()
        for (o_id, _o_name) in backends[key].get_options():
            # restore presets from the GUI
            if preset and Options.options.get_tree(c_id, o_id):
                args.append('.'.join([c_id, o_id]))
            elif all_but_warning and not backends[c_id].get_warning(o_id):
                args.append('.'.join([c_id, o_id]))
    return args


def args_to_operations(args, preset, all_but_warning):
    """Read arguments and return list of operations as dictionary"""
    list(register_cleaners())
    operations = {}
    if not args:
        args = []
    args = set(args + args_to_operations_list(preset, all_but_warning))
    for arg in args:
        if 2 != len(arg.split('.')):
            logger.warning(_("not a valid cleaner: %s"), arg)
            continue
        (cleaner_id, option_id) = arg.split('.')
        # enable all options (for example, firefox.*)
        if '*' == option_id:
            if cleaner_id in operations:
                del operations[cleaner_id]
            operations[cleaner_id] = [
                option_id2
                for (option_id2, _o_name) in backends[cleaner_id].get_options()
            ]
            continue
        # add the specified option
        if cleaner_id not in operations:
            operations[cleaner_id] = []
        if option_id not in operations[cleaner_id]:
            operations[cleaner_id].append(option_id)
    for (k, v) in operations.items():
        operations[k] = sorted(v)
    return operations


def process_cmd_line():
    """Parse the command line and execute given commands."""
    # TRANSLATORS: This is the command line usage.  Don't translate
    # %prog, but do translate options, cleaner, and option.
    # Don't translate and add "usage:" - it gets added by Python.
    # More information about the command line is here
    # https://www.bleachbit.org/documentation/command-line
    usage = _("usage: %prog [options] cleaner.option1 cleaner.option2")
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", "--list-cleaners", action="store_true",
                      help=_("list cleaners"))
    parser.add_option("-c", "--clean", action="store_true",
                      # TRANSLATORS: predefined cleaners are for applications, such as Firefox and Flash.
                      # This is different than cleaning an arbitrary file, such as a
                      # spreadsheet on the desktop.
                      help=_("run cleaners to delete files and make other permanent changes"))
    parser.add_option(
        '--debug', help=_("set log level to verbose"), action="store_true")
    parser.add_option('--debug-log', help=_("log debug messages to file"))
    parser.add_option("-s", "--shred", action="store_true",
                      help=_("shred specific files or folders"))
    parser.add_option("--sysinfo", action="store_true",
                      help=_("show system information"))
    parser.add_option("--gui", action="store_true",
                      help=_("launch the graphical interface"))
    parser.add_option('--exit', action='store_true',
                      help=optparse.SUPPRESS_HELP)

    if 'nt' == os.name:
        uac_help = _("do not prompt for administrator privileges")
    else:
        uac_help = optparse.SUPPRESS_HELP
    parser.add_option("--no-uac", action="store_true", help=uac_help)
    parser.add_option("-p", "--preview", action="store_true",
                      help=_("preview files to be deleted and other changes"))
    parser.add_option('--pot', action='store_true',
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("--preset", action="store_true",
                      help=_("use options set in the graphical interface"))
    parser.add_option("--all-but-warning", action="store_true",
                      help=_("enable all options that do not have a warning"))
    if 'nt' == os.name:
        parser.add_option("--update-winapp2", action="store_true",
                          help=_("update winapp2.ini, if a new version is available"))
    parser.add_option("-w", "--wipe-free-space", action="store_true",
                      help=_("wipe free space in the given paths"))
    parser.add_option("-v", "--version", action="store_true",
                      help=_("output version information and exit"))
    parser.add_option('-o', '--overwrite', action='store_true',
                      help=_('overwrite files to hide contents'))

    def expand_context_menu_option(option, opt, value, parser):
        setattr(parser.values, 'gui', True)
        setattr(parser.values, 'exit', True)

    parser.add_option("--context-menu", action="callback", callback=expand_context_menu_option)

    (options, args) = parser.parse_args()

    cmd_list = (options.list_cleaners, options.wipe_free_space,
                options.preview, options.clean)
    cmd_count = sum(x is True for x in cmd_list)
    if cmd_count > 1:
        logger.error(
            _('Specify only one of these commands: --list-cleaners, --wipe-free-space, --preview, --clean'))
        sys.exit(1)

    did_something = False
    if options.debug:
        # set in __init__ so it takes effect earlier
        pass
    if options.debug_log:
        logger.addHandler(logging.FileHandler(options.debug_log))
        logger.info(SystemInformation.get_system_information())
    if options.version:
        print("""
BleachBit version %s
Copyright (C) 2008-2021 Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""" % APP_VERSION)
        sys.exit(0)
    if 'nt' == os.name and options.update_winapp2:
        from bleachbit import Update
        logger.info(_("Checking online for updates to winapp2.ini"))
        Update.check_updates(False, True,
                             lambda x: sys.stdout.write("%s\n" % x),
                             lambda: None)
        # updates can be combined with --list-cleaners, --preview, --clean
        did_something = True
    if options.list_cleaners:
        list_cleaners()
        sys.exit(0)
    if options.pot:
        from bleachbit.CleanerML import create_pot
        create_pot()
        sys.exit(0)
    if options.wipe_free_space:
        if len(args) < 1:
            logger.error(_("No directories given for --wipe-free-space"))
            sys.exit(1)
        for wipe_path in args:
            if not os.path.isdir(wipe_path):
                logger.error(
                    _("Path to wipe must be an existing directory: %s"), wipe_path)
                sys.exit(1)
        logger.info(_("Wiping free space can take a long time."))
        for wipe_path in args:
            logger.info('Wiping free space in path: %s', wipe_path)
            import bleachbit.FileUtilities
            for _ret in bleachbit.FileUtilities.wipe_path(wipe_path):
                pass
        sys.exit(0)
    if options.preview or options.clean:
        operations = args_to_operations(
            args, options.preset, options.all_but_warning)
        if not operations:
            logger.error(_("No work to do. Specify options."))
            sys.exit(1)
    if options.preview:
        preview_or_clean(operations, False)
        sys.exit(0)
    if options.overwrite:
        if not options.clean or options.shred:
            logger.warning(
                _("--overwrite is intended only for use with --clean"))
        Options.options.set('shred', True, commit=False)
    if options.clean:
        preview_or_clean(operations, True)
        sys.exit(0)
    if options.gui:
        import bleachbit.GUI
        app = bleachbit.GUI.Bleachbit(
            uac=not options.no_uac, shred_paths=args, auto_exit=options.exit)
        sys.exit(app.run())
    if options.shred:
        # delete arbitrary files without GUI
        # create a temporary cleaner object
        backends['_gui'] = create_simple_cleaner(args)
        operations = {'_gui': ['files']}
        preview_or_clean(operations, True)
        sys.exit(0)
    if options.sysinfo:
        print(SystemInformation.get_system_information())
        sys.exit(0)
    if not did_something:
        parser.print_help()


if __name__ == '__main__':
    process_cmd_line()
