# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
from bleachbit import APP_VERSION
from bleachbit import SystemInformation, Options, Worker
from bleachbit.Language import get_text as _
from bleachbit.Log import set_root_log_level

import logging
import optparse
import os
import sys

logger = logging.getLogger(__name__)


class CliCallback:
    """Command line's callback passed to Worker"""

    def __init__(self, quiet=False):
        self.quiet = quiet

    def append_text(self, msg, _tag=None):
        """Write text to the terminal"""
        if not self.quiet:
            print(msg.strip('\n'))

    def update_progress_bar(self, status):
        """Not used"""

    def update_total_size(self, size):
        """Not used"""

    def update_item_size(self, op, opid, size):
        """Not used"""

    def worker_done(self, worker, really_delete):
        """Not used"""


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
        print(cleaner)


def preview_or_clean(operations, really_clean, quiet=False):
    """Preview deletes and other changes"""
    cb = CliCallback(quiet)
    worker = Worker.Worker(cb, really_clean, operations).run()
    try:
        while next(worker):
            pass
    except StopIteration:
        pass
    except Exception:
        logger.exception('Failed to clean')


def args_to_operations_list(preset, all_but_warning):
    """For --preset and --all-but-warning return list of operations as list

    Example return: ['google_chrome.cache', 'system.tmp']
    """
    args = []
    if not backends:
        list(register_cleaners())
    assert len(backends) > 1
    for key in sorted(backends):
        c_id = backends[key].get_id()
        for (o_id, _o_name) in backends[key].get_options():
            # restore presets from the GUI
            if preset and Options.options.get_tree(c_id, o_id):
                args.append('.'.join([c_id, o_id]))
            elif all_but_warning and not backends[c_id].get_warning(o_id):
                args.append('.'.join([c_id, o_id]))
    return args


def args_to_operations(args, preset, all_but_warning, excludes=None):
    """Convert command-line arguments to a dictionary of operations

    Args:
        args: List of cleaner.option strings (e.g., ['system.tmp', 'firefox.cache'])
        preset: Boolean indicating whether to use saved preset operations
        all_but_warning: Boolean indicating whether to include all non-warning operations
        excludes: Optional list of cleaner.option strings to remove from operations

    Returns:
        Dictionary mapping cleaner IDs to lists of option IDs
        Example: {'system': ['tmp'], 'firefox': ['cache']}
    """
    list(register_cleaners())
    operations = {}
    if not args:
        args = []

    if excludes is None:
        excludes = []
    positive_args = set(
        args + args_to_operations_list(preset, all_but_warning))

    def fix_deprecated(cid, oid):
        if 'system' == cid and 'free_disk_space' == oid:
            logger.info(
                "Change 'system.free_disk_space' (deprecated) to 'system.empty_space'")
            return 'empty_space'
        return oid

    for arg in positive_args:
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
        # backwards compatibility
        option_id = fix_deprecated(cleaner_id, option_id)
        # add the specified option
        if cleaner_id not in operations:
            # initialize list of options for this cleaner
            operations[cleaner_id] = []
        if option_id not in operations[cleaner_id]:
            # add option to list
            operations[cleaner_id].append(option_id)

    for arg in excludes:
        if '*' in arg or '?' in arg:
            logger.error(
                _("Wildcard characters are not allowed in --except: %s"), arg)
            # Exit to avoid over-cleaning.
            sys.exit(1)
        if 2 != len(arg.split('.')):
            logger.error(_("not a valid cleaner: %s"), arg)
            # Exit to avoid over-cleaning.
            sys.exit(1)
        (cleaner_id, option_id) = arg.split('.')
        option_id = fix_deprecated(cleaner_id, option_id)
        if cleaner_id in operations and option_id in operations[cleaner_id]:
            operations[cleaner_id].remove(option_id)
            if not operations[cleaner_id]:
                del operations[cleaner_id]

    for (k, v) in operations.items():
        operations[k] = sorted(v)
    return operations


def _split_excludes(values):
    excludes = []
    for value in values:
        if value is None:
            continue
        excludes.extend(item.strip()
                        for item in value.split(',') if item.strip())
    return excludes


def parse_cmd_line(argv=None):
    """Parse the command line and return parser, options, args, and excludes."""

    # TRANSLATORS: This is the command line usage.  Don't translate
    # %prog, but do translate options, cleaner, and option.
    # Don't translate and add "usage:" - it gets added by Python.
    # More information about the command line is here
    # https://www.bleachbit.org/documentation/command-line
    usage = _("usage: %prog [options] cleaner.option1 [cleaner.option2 ...]")
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", "--list-cleaners", action="store_true",
                      help=_("list cleaners"))
    parser.add_option("-p", "--preview", action="store_true",
                      help=_("preview files to be deleted and other changes"))
    parser.add_option("-c", "--clean", action="store_true",
                      # TRANSLATORS: predefined cleaners are for applications, such as Firefox and Flash.
                      # This is different than cleaning an arbitrary file, such as a
                      # spreadsheet on the desktop.
                      help=_("run cleaners to delete files and make other permanent changes"))
    parser.add_option("-s", "--shred", action="store_true",
                      help=_("shred specific files or folders"))
    parser.add_option("-w", "--wipe-empty-space", "--wipe-free-space",
                      action="store_true", dest="wipe_empty_space",
                      help=_("wipe empty space in the given paths"))
    parser.add_option('-o', '--overwrite', action='store_true',
                      help=_('overwrite files to hide contents'))
    parser.add_option("--gui", action="store_true",
                      help=_("launch the graphical interface"))
    parser.add_option("--preset", action="store_true",
                      help=_("use options set in the graphical interface"))
    parser.add_option("--all-but-warning", action="store_true",
                      help=_("enable all options that do not have a warning"))
    parser.add_option("--except", dest="excludes", action="append", default=[],
                      help=_("exclude cleaner options (can be repeated, comma-separated)"))
    parser.add_option(
        '--debug', help=_("set log level to verbose"), action="store_true")
    parser.add_option('--debug-log', help=_("log debug messages to file"))
    parser.add_option("--sysinfo", action="store_true",
                      help=_("show system information"))
    parser.add_option("-v", "--version", action="store_true",
                      help=_("output version information and exit"))

    if 'nt' == os.name:
        uac_help = _("do not prompt for administrator privileges")
    else:
        uac_help = optparse.SUPPRESS_HELP
    parser.add_option("--no-uac", action="store_true", help=uac_help)
    if 'nt' == os.name:
        parser.add_option('--uac-sid-token', help=optparse.SUPPRESS_HELP)
    parser.add_option('--pot', action='store_true',
                      help=optparse.SUPPRESS_HELP)
    if 'nt' == os.name:
        parser.add_option("--update-winapp2", action="store_true",
                          help=_("update winapp2.ini, if a new version is available"))

    # added for testing py2exe build
    # https://github.com/bleachbit/bleachbit/commit/befe244efee9b2d4859c6b6c31f8bedfd4d85aad#diff-b578cd35e15095f69822ebe497bf8691da1b587d6cc5f5ec252ff4f186dbed56
    parser.add_option('--exit', action='store_true',
                      help=optparse.SUPPRESS_HELP)

    # some workaround for context menu added here
    # https://github.com/bleachbit/bleachbit/commit/b09625925149c98a6c79e278c35d5995e7526993
    def expand_context_menu_option(_option, _opt, _value, parser):
        setattr(parser.values, 'gui', True)
        setattr(parser.values, 'exit', True)
    parser.add_option("--context-menu", action="callback", callback=expand_context_menu_option,
                      help=optparse.SUPPRESS_HELP)

    (options, args) = parser.parse_args(args=argv)
    excludes = _split_excludes(options.excludes)
    return parser, options, args, excludes


def process_cmd_line():
    """Parse the command line and execute given commands."""

    parser, options, args, excludes = parse_cmd_line()

    cmd_list = (options.list_cleaners,
                options.clean,
                options.preview,
                options.shred,
                options.wipe_empty_space)
    cmd_count = sum(x is True for x in cmd_list)
    if cmd_count > 1:
        logger.error(
            _('Specify only one of these commands: --list-cleaners, --wipe-empty-space, --preview, --clean, --shred'))
        sys.exit(1)

    did_something = False
    if options.debug:
        # set in __init__ so it takes effect earlier
        pass
    elif options.preset:
        # but if --preset is given, check if GUI option sets debug
        if Options.options.get('debug'):
            set_root_log_level(Options.options.get('debug'))
            logger.debug("Debugging is enabled in GUI settings.")
    if options.debug_log:
        # File handler is already set up in Log.py init_log() function
        # Just add system information to the log
        logger.info(SystemInformation.get_system_information())
    if options.version:
        print("""
BleachBit version %s
Copyright (C) 2008-2025 Andrew Ziem.  All rights reserved.
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
    if options.wipe_empty_space:
        if len(args) < 1:
            logger.error(_("No directories given for --wipe-empty-space"))
            sys.exit(1)
        logger.info(_("Wiping empty space can take a long time."))
        for wipe_path in args:
            logger.info(_("Wipe empty space in %s"), wipe_path)
            import bleachbit.FileUtilities
            for _ret in bleachbit.FileUtilities.wipe_path(wipe_path):
                pass
        sys.exit(0)
    if options.preview or options.clean:
        operations = args_to_operations(
            args, options.preset, options.all_but_warning, excludes)
        if not operations:
            logger.error(_("No work to do. Specify options."))
            sys.exit(1)
    if options.overwrite:
        if not options.clean or options.shred:
            logger.warning(
                _("--overwrite is intended only for use with --clean"))
        Options.options.set('shred', True, commit=False)
    if options.clean or options.preview:
        preview_or_clean(operations, options.clean)
        sys.exit(0)
    if options.gui:
        import bleachbit.GuiApplication
        app = bleachbit.GuiApplication.Bleachbit(
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
