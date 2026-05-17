# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Perform (or assist with) cleaning operations.
"""

import glob
import logging
import os.path
import warnings

from bleachbit import _, Command, FileUtilities, Special, Windows
from bleachbit.FileUtilities import children_in_directory
from bleachbit.Options import options

# Suppress GTK warning messages while running in CLI #34
warnings.simplefilter("ignore", Warning)
try:
    from bleachbit.GuiBasic import Gtk, Gdk
    HAVE_GTK = Gdk.get_default_root_window() is not None
except (ImportError, RuntimeError, ValueError):
    # ImportError happens when GTK is not installed.
    # RuntimeError can happen when X is not available (e.g., cron, ssh).
    # ValueError seen on BleachBit 3.0 with GTK 3 (GitHub issue 685)
    HAVE_GTK = False


# a module-level variable for holding cleaners
backends = {}


class Cleaner:

    """Base class for a cleaner"""

    def __init__(self):
        self.actions = []
        self.id = None
        self.description = None
        self.name = None
        self.options = {}
        self.running = []
        self.warnings = {}

    def add_action(self, option_id, action):
        """Register 'action' (instance of class Action) to be executed
        for ''option_id'.  The actions must implement list_files and
        other_cleanup()"""
        self.actions.append((option_id, action))

    def add_option(self, option_id, name, description):
        """Register option (such as 'cache')"""
        self.options[option_id] = (name, description)

    def add_running(self, detection_type, pathname):
        """Add a way to detect this program is currently running"""
        self.running.append((detection_type, pathname))

    def auto_hide(self):
        """Return boolean whether it is OK to automatically hide this
        cleaner"""
        for (option_id, __name) in self.get_options():
            try:
                for cmd in self.get_commands(option_id):
                    for _dummy in cmd.execute(False):
                        return False
                for _ds in self.get_deep_scan(option_id):
                    return False
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception('exception in auto_hide(), cleaner=%s, option=%s',
                                 self.name, option_id)
        return True

    def get_commands(self, option_id):
        """Get list of Command instances for option 'option_id'"""
        for action in self.actions:
            if option_id == action[0]:
                yield from action[1].get_commands()
        if option_id not in self.options:
            raise RuntimeError("Unknown option '%s'" % option_id)

    def get_deep_scan(self, option_id):
        """Get dictionary used to build a deep scan"""
        for action in self.actions:
            if option_id == action[0]:
                try:
                    yield from action[1].get_deep_scan()
                except StopIteration:
                    return
        if option_id not in self.options:
            raise RuntimeError("Unknown option '%s'" % option_id)

    def get_description(self):
        """Brief description of the cleaner"""
        return self.description

    def get_id(self):
        """Return the unique name of this cleaner"""
        return self.id

    def get_name(self):
        """Return the human name of this cleaner"""
        return self.name

    def get_option_descriptions(self):
        """Yield the names and descriptions of each option in a 2-tuple"""
        if self.options:
            for key in sorted(self.options.keys()):
                yield (self.options[key][0], self.options[key][1])

    def get_options(self):
        """Return user-configurable options in 2-tuple (id, name)"""
        if self.options:
            for key in sorted(self.options.keys()):
                yield (key, self.options[key][0])

    def get_warning(self, option_id):
        """Return a warning as string."""
        if option_id in self.warnings:
            return self.warnings[option_id]
        return None

    def is_running(self):
        """Return whether the program is currently running"""
        logger = logging.getLogger(__name__)
        for running in self.running:
            test = running[0]
            pathname = running[1]
            if 'exe' == test:
                if Windows.is_process_running(pathname):
                    logger.debug("process '%s' is running", pathname)
                    return True
            elif 'pathname' == test:
                expanded = os.path.expanduser(os.path.expandvars(pathname))
                for globbed in glob.iglob(expanded):
                    if os.path.exists(globbed):
                        logger.debug(
                            "file '%s' exists indicating '%s' is running", globbed, self.name)
                        return True
            else:
                raise RuntimeError(
                    "Unknown running-detection test '%s'" % test)
        return False

    def is_usable(self):
        """Return whether the cleaner is usable (has actions)"""
        return len(self.actions) > 0

    def set_warning(self, option_id, description):
        """Set a warning to be displayed when option is selected interactively"""
        self.warnings[option_id] = description


class OpenOfficeOrg(Cleaner):

    """Delete OpenOffice.org cache"""

    def __init__(self):
        Cleaner.__init__(self)
        self.options = {}
        self.add_option('cache', _('Cache'), _('Delete the cache'))
        self.add_option('recent_documents', _('Most recently used'), _(
            "Delete the list of recently used documents"))
        self.id = 'openofficeorg'
        self.name = 'OpenOffice.org'
        self.description = _("Office suite")

        # reference: http://katana.oooninja.com/w/editions_of_openoffice.org
        self.prefixes = [
            "$APPDATA\\OpenOffice.org\\3", "$APPDATA\\OpenOffice.org2"]

    def get_commands(self, option_id):
        # paths for which to run expand_glob_join
        egj = []
        if 'recent_documents' == option_id:
            egj.append(
                "user/registry/data/org/openoffice/Office/Histories.xcu")
            egj.append(
                "user/registry/cache/org.openoffice.Office.Histories.dat")

        if 'recent_documents' == option_id and not 'cache' == option_id:
            egj.append("user/registry/cache/org.openoffice.Office.Common.dat")

        for egj_ in egj:
            for prefix in self.prefixes:
                for path in FileUtilities.expand_glob_join(prefix, egj_):
                    path = os.path.normpath(path)
                    if os.path.lexists(path):
                        yield Command.Delete(path)

        if 'cache' == option_id:
            dirs = []
            for prefix in self.prefixes:
                dirs += FileUtilities.expand_glob_join(
                    prefix, "user/registry/cache/")
            for dirname in dirs:
                dirname = os.path.normpath(dirname)
                for filename in children_in_directory(dirname, False):
                    yield Command.Delete(filename)

        if 'recent_documents' == option_id:
            for prefix in self.prefixes:
                for path in FileUtilities.expand_glob_join(prefix, "user/registry/data/org/openoffice/Office/Common.xcu"):
                    if os.path.lexists(path):
                        yield Command.Function(path,
                                               Special.delete_ooo_history,
                                               _('Delete the usage history'))
                # ~/.openoffice.org/3/user/registrymodifications.xcu
                #       Apache OpenOffice.org 3.4.1 from openoffice.org on Ubuntu 13.04
                # %AppData%\OpenOffice.org\3\user\registrymodifications.xcu
                # Apache OpenOffice.org 3.4.1 from openoffice.org on Windows XP
                for path in FileUtilities.expand_glob_join(prefix, "user/registrymodifications.xcu"):
                    if os.path.lexists(path):
                        yield Command.Function(path,
                                               Special.delete_office_registrymodifications,
                                               _('Delete the usage history'))


class System(Cleaner):

    """Clean the system in general"""

    def __init__(self):
        Cleaner.__init__(self)

        self.add_option('logs', _('Logs'), _('Delete the logs'))
        self.add_option(
            'memory_dump', _('Memory dump'), _('Delete the file'))
        self.add_option('muicache', 'MUICache', _('Delete the cache'))
        # TRANSLATORS: Prefetch is Microsoft Windows jargon.
        self.add_option('prefetch', _('Prefetch'), _('Delete the cache'))
        self.add_option(
            'recycle_bin', _('Recycle bin'), _('Empty the recycle bin'))
        # TRANSLATORS: 'Update' is a noun, and 'Update uninstallers' is an option to delete
        # the uninstallers for software updates.
        self.add_option('updates', _('Update uninstallers'), _(
            'Delete uninstallers for Microsoft updates including hotfixes, service packs, and Internet Explorer updates'))

        #
        # options for GTK+
        #

        if HAVE_GTK:
            self.add_option('clipboard', _('Clipboard'), _(
                'The desktop environment\'s clipboard used for copy and paste operations'))

        #
        # options common to all platforms
        #
        # TRANSLATORS: "Custom" is an option allowing the user to specify which
        # files and folders will be erased.
        self.add_option('custom', _('Custom'), _(
            'Delete user-specified files and folders'))
        # TRANSLATORS: 'free' means 'unallocated'
        self.add_option('free_disk_space', _('Free disk space'),
                        # TRANSLATORS: 'free' means 'unallocated'
                        _('Overwrite free disk space to hide deleted files'))
        self.set_warning('free_disk_space', _('This option is very slow.'))
        self.add_option(
            'tmp', _('Temporary files'), _('Delete the temporary files'))

        self.description = _("The system in general")
        self.id = 'system'
        self.name = _("System")

    def get_commands(self, option_id):
        # custom
        if 'custom' == option_id:
            for (c_type, c_path) in options.get_custom_paths():
                if not os.path.lexists(c_path):
                    # Skip non-existent paths to avoid errors
                    # https://github.com/bleachbit/bleachbit/issues/831
                    continue
                if 'file' == c_type:
                    yield Command.Delete(c_path)
                elif 'folder' == c_type:
                    for path in children_in_directory(c_path, True):
                        yield Command.Delete(path)
                    yield Command.Delete(c_path)
                else:
                    raise RuntimeError(
                        'custom folder has invalid type %s' % c_type)

        # Windows logs
        if 'logs' == option_id:
            paths = (
                '$ALLUSERSPROFILE\\Application Data\\Microsoft\\Dr Watson\\*.log',
                '$ALLUSERSPROFILE\\Application Data\\Microsoft\\Dr Watson\\user.dmp',
                '$LocalAppData\\Microsoft\\Windows\\WER\\ReportArchive\\*\\*',
                '$LocalAppData\\Microsoft\\Windows\\WER\\ReportQueue\\*\\*',
                '$programdata\\Microsoft\\Windows\\WER\\ReportArchive\\*\\*',
                '$programdata\\Microsoft\\Windows\\WER\\ReportQueue\\*\\*',
                '$localappdata\\Microsoft\\Internet Explorer\\brndlog.bak',
                '$localappdata\\Microsoft\\Internet Explorer\\brndlog.txt',
                '$windir\\*.log',
                '$windir\\imsins.BAK',
                '$windir\\OEWABLog.txt',
                '$windir\\SchedLgU.txt',
                '$windir\\ntbtlog.txt',
                '$windir\\setuplog.txt',
                '$windir\\REGLOCS.OLD',
                '$windir\\Debug\\*.log',
                '$windir\\Debug\\Setup\\UpdSh.log',
                '$windir\\Debug\\UserMode\\*.log',
                '$windir\\Debug\\UserMode\\ChkAcc.bak',
                '$windir\\Debug\\UserMode\\userenv.bak',
                '$windir\\Microsoft.NET\\Framework\\*\\*.log',
                '$windir\\pchealth\\helpctr\\Logs\\hcupdate.log',
                '$windir\\security\\logs\\*.log',
                '$windir\\security\\logs\\*.old',
                '$windir\\SoftwareDistribution\\*.log',
                '$windir\\SoftwareDistribution\\DataStore\\Logs\\*',
                '$windir\\system32\\TZLog.log',
                '$windir\\system32\\config\\systemprofile\\Application Data\\Microsoft\\Internet Explorer\\brndlog.bak',
                '$windir\\system32\\config\\systemprofile\\Application Data\\Microsoft\\Internet Explorer\\brndlog.txt',
                '$windir\\system32\\LogFiles\\AIT\\AitEventLog.etl.???',
                '$windir\\system32\\LogFiles\\Firewall\\pfirewall.log*',
                '$windir\\system32\\LogFiles\\Scm\\SCM.EVM*',
                '$windir\\system32\\LogFiles\\WMI\\Terminal*.etl',
                '$windir\\system32\\LogFiles\\WMI\\RTBackup\\EtwRT.*etl',
                '$windir\\system32\\wbem\\Logs\\*.lo_',
                '$windir\\system32\\wbem\\Logs\\*.log', )

            for path in paths:
                expanded = os.path.expandvars(path)
                for globbed in glob.iglob(expanded):
                    yield Command.Delete(globbed)

        # memory dump
        # how to manually create this file
        # http://www.pctools.com/guides/registry/detail/856/
        if 'memory_dump' == option_id:
            fname = os.path.expandvars('$windir\\memory.dmp')
            if os.path.exists(fname):
                yield Command.Delete(fname)
            for fname in glob.iglob(os.path.expandvars('$windir\\Minidump\\*.dmp')):
                yield Command.Delete(fname)

        # temporary files
        if 'tmp' == option_id:
            dirnames = [os.path.expandvars(r'%temp%'), os.path.expandvars("%windir%\\temp\\")]
            # whitelist the folder %TEMP%\Low but not its contents
            # https://bugs.launchpad.net/bleachbit/+bug/1421726
            for dirname in dirnames:
                low = os.path.join(dirname, 'low').lower()
                for filename in children_in_directory(dirname, True):
                    if not low == filename.lower():
                        yield Command.Delete(filename)

        # clipboard
        if HAVE_GTK and 'clipboard' == option_id:
            def clear_clipboard():
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(' ', 1)
                clipboard.clear()
                return 0
            yield Command.Function(None, clear_clipboard, _('Clipboard'))

        # overwrite free space
        shred_drives = options.get_list('shred_drives')
        if 'free_disk_space' == option_id and shred_drives:
            for pathname in shred_drives:
                # TRANSLATORS: 'Free' means 'unallocated.'
                # %s expands to a path such as C:\ or /tmp/
                display = _("Overwrite free disk space %s") % pathname

                def wipe_path_func():
                    # Yield control to GTK idle because this process
                    # is very slow.  Also display progress.
                    yield from FileUtilities.wipe_path(pathname, idle=True)
                    yield 0
                yield Command.Function(None, wipe_path_func, display)

        # MUICache
        if 'muicache' == option_id:
            keys = (
                'HKCU\\Software\\Microsoft\\Windows\\ShellNoRoam\\MUICache',
                'HKCU\\Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache')
            for key in keys:
                yield Command.Winreg(key, None)

        # prefetch
        if 'prefetch' == option_id:
            for path in glob.iglob(os.path.expandvars('$windir\\Prefetch\\*.pf')):
                yield Command.Delete(path)

        # recycle bin
        if 'recycle_bin' == option_id:
            # This method allows shredding
            recycled_any = False
            for path in Windows.get_recycle_bin():
                recycled_any = True
                yield Command.Delete(path)

            # Windows 10 refreshes the recycle bin icon when the user
            # opens the recycle bin folder.

            # This is a hack to refresh the icon.
            def empty_recycle_bin_func():
                import tempfile
                tmpdir = tempfile.mkdtemp()
                Windows.move_to_recycle_bin(tmpdir)
                try:
                    Windows.empty_recycle_bin(None, True)
                except:
                    logging.getLogger(__name__).info(
                        'error in empty_recycle_bin()', exc_info=True)
                yield 0
            # Using the Function Command prevents emptying the recycle bin
            # when in preview mode.
            if recycled_any:
                yield Command.Function(None, empty_recycle_bin_func, _('Empty the recycle bin'))

        # Windows Updates
        if 'updates' == option_id:
            for wu in Windows.delete_updates():
                yield wu


def register_cleaners(cb_progress=lambda x: None, cb_done=lambda: None):
    """Register all known cleaners: system, CleanerML, and Winapp2"""
    global backends

    # wipe out any registrations
    # Because this is a global variable, cannot use backends = {}
    backends.clear()

    # initialize "hard coded" (non-CleanerML) backends
    backends["openofficeorg"] = OpenOfficeOrg()
    backends["system"] = System()

    # register CleanerML cleaners
    from bleachbit import CleanerML
    cb_progress(_('Loading native cleaners.'))
    yield from CleanerML.load_cleaners(cb_progress)

    # register Winapp2.ini cleaners
    cb_progress(_('Importing cleaners from Winapp2.ini.'))
    from bleachbit import Winapp
    yield from Winapp.load_cleaners(cb_progress)

    cb_done()

    yield False  # end the iteration


def create_simple_cleaner(paths):
    """Shred arbitrary files (used in CLI and GUI)"""
    cleaner = Cleaner()
    cleaner.add_option(option_id='files', name='', description='')
    cleaner.name = _("System")  # shows up in progress bar

    from bleachbit import Action

    class CustomFileAction(Action.ActionProvider):
        action_key = '__customfileaction'

        def get_commands(self):
            for path in paths:
                if not isinstance(path, (str)):
                    raise RuntimeError(
                        'expected path as string but got %s' % str(path))
                if not os.path.isabs(path):
                    path = os.path.abspath(path)
                if not os.path.lexists(path):
                    # Skip non-existent paths to avoid errors
                    # https://github.com/bleachbit/bleachbit/issues/831
                    continue
                if os.path.isdir(path):
                    for child in children_in_directory(path, True):
                        yield Command.Shred(child)
                yield Command.Shred(path)
    provider = CustomFileAction(None)
    cleaner.add_action('files', provider)
    return cleaner


def create_wipe_cleaner(path):
    """Wipe free disk space of arbitrary paths (used in GUI)"""
    cleaner = Cleaner()
    cleaner.add_option(
        option_id='free_disk_space', name='', description='')
    cleaner.name = ''

    # create a temporary cleaner object
    display = _("Overwrite free disk space %s") % path

    def wipe_path_func():
        yield from FileUtilities.wipe_path(path, idle=True)
        yield 0

    from bleachbit import Action

    class CustomWipeAction(Action.ActionProvider):
        action_key = '__customwipeaction'

        def get_commands(self):
            yield Command.Function(None, wipe_path_func, display)
    provider = CustomWipeAction(None)
    cleaner.add_action('free_disk_space', provider)
    return cleaner
