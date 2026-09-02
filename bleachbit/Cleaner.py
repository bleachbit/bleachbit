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
import os
import os.path
import re
import tempfile
import time

from bleachbit.Constant import EMPTY_SPACE_WARNING
from bleachbit.Language import get_text as _
from bleachbit.FileUtilities import children_in_directory
from bleachbit.Options import options
from bleachbit.PathUtils import path_equal
from bleachbit.Process import is_process_running
from bleachbit import Action, CleanerML, Command, FileUtilities, General, Memory
from bleachbit import IS_LINUX, IS_MAC, IS_POSIX, IS_WINDOWS
from bleachbit.GtkShim import gtk_may_be_available
from bleachbit.Wipe import wipe_path

if IS_POSIX:
    from bleachbit import Unix
elif IS_WINDOWS:
    from bleachbit import Windows
elif not (IS_POSIX or IS_WINDOWS):
    raise RuntimeError(f"Unknown OS '{os.name}'")


logger = logging.getLogger(__name__)

# a module-level variable for holding cleaners
backends = {}

# Putting the string here helps with translation.
# TRANSLATORS: The description of what certain cleaning options do.
DELETE_CACHE_DESCRIPTION = _("Delete the cache")

MENU_DIRS = ('~/.local/share/applications',
             '~/.config/autostart',
             '~/.gnome/apps/',
             '~/.gnome2/panel2.d/default/launchers',
             '~/.gnome2/vfolders/applications/',
             '~/.kde/share/apps/RecentDocuments/',
             '~/.kde/share/mimelnk',
             '~/.kde/share/mimelnk/application/ram.desktop',
             '~/.kde2/share/mimelnk/application/',
             '~/.kde2/share/applnk')


class Cleaner:

    """Base class for a cleaner"""

    def __init__(self, id_=None, name=None, description=None):
        self.actions = []
        self.id = id_
        self.description = description
        self.name = name
        self.options = {}
        self.running = []
        self.warnings = {}
        # Winapp2 cleaners clear this because their own detect() already ran
        self.auto_hide_supported = True
        self.keep_list_re = None
        # Lazily built {option_id: [action, ...]} index over self.actions.
        # Winapp2 cleaners aggregate thousands of actions, so scanning the
        # whole list per option (get_commands/get_deep_scan) is quadratic.
        self._actions_index = None
        self._actions_index_src = None
        self._sorted_option_keys = None

    def add_action(self, option_id, action):
        """Register 'action' (instance of class Action) to be executed
        for ''option_id'.  The actions must implement list_files and
        other_cleanup()"""
        self.actions.append((option_id, action))
        self._actions_index = None

    def _actions_for(self, option_id):
        """Return the actions registered for option_id, in insertion order."""
        # Rebuild when invalidated by add_action or when self.actions was
        # reassigned to a different list.
        if self._actions_index is None or self._actions_index_src is not self.actions:
            index = {}
            for oid, action in self.actions:
                index.setdefault(oid, []).append(action)
            self._actions_index = index
            self._actions_index_src = self.actions
        return self._actions_index.get(option_id, ())

    def add_option(self, option_id, name, description):
        """Register option (such as 'cache')"""
        self.options[option_id] = (name, description)
        self._sorted_option_keys = None

    def add_running(self, detection_type, pathname, same_user=False):
        """Add a way to detect this program is currently running"""
        self.running.append((detection_type, pathname, same_user))

    def auto_hide(self):
        """Return boolean whether it is OK to automatically hide this
        cleaner"""
        if not self.auto_hide_supported:
            return False
        for (option_id, __name) in self.get_options():
            try:
                for cmd in self.get_commands(option_id):
                    for _dummy in cmd.execute(False):
                        return False
                for _ds in self.get_deep_scan(option_id):
                    return False
            except Exception:
                logger.exception('exception in auto_hide(), cleaner=%s, option=%s',
                                 self.name, option_id)
        return True

    def get_commands(self, option_id):
        """Get list of Command instances for option 'option_id'"""
        for action in self._actions_for(option_id):
            yield from action.get_commands()
        if option_id not in self.options:
            raise RuntimeError(f"Unknown option '{option_id}'")

    def get_deep_scan(self, option_id):
        """Get dictionary used to build a deep scan"""
        for action in self._actions_for(option_id):
            try:
                yield from action.get_deep_scan()
            except StopIteration:
                return
        if option_id not in self.options:
            raise RuntimeError(f"Unknown option '{option_id}'")

    def get_description(self):
        """Brief description of the cleaner"""
        return self.description

    def get_id(self):
        """Return the unique name of this cleaner"""
        return self.id

    def get_name(self):
        """Return the human name of this cleaner"""
        return self.name

    def _get_sorted_option_keys(self):
        """Return option keys sorted once and cached until options change."""
        if self._sorted_option_keys is None:
            self._sorted_option_keys = sorted(self.options.keys())
        return self._sorted_option_keys

    def get_option_descriptions(self):
        """Yield the names and descriptions of each option in a 2-tuple"""
        for key in self._get_sorted_option_keys():
            yield (self.options[key][0], self.options[key][1])

    def get_options(self):
        """Return user-configurable options in 2-tuple (id, name)"""
        for key in self._get_sorted_option_keys():
            yield (key, self.options[key][0])

    def get_warning(self, option_id):
        """Return a warning as string."""
        return self.warnings.get(option_id)

    def is_process_running(self):
        """Return whether the process is currently running"""
        for (test, pathname, same_user) in self.running:
            if 'exe' == test:
                if is_process_running(pathname, same_user):
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
                raise RuntimeError(f"Unknown running-detection test '{test}'")
        return False

    def is_usable(self):
        """Return whether the cleaner is usable (has actions)"""
        return bool(self.actions)

    def set_warning(self, option_id, description):
        """Set a warning to be displayed when option is selected interactively"""
        self.warnings[option_id] = description


class System(Cleaner):

    """Clean the system in general"""

    def __init__(self):
        Cleaner.__init__(
            self,
            id_='system',
            # TRANSLATORS: Cleaner name shown in the list of applications.
            name=_("System"),
            # TRANSLATORS: Description of the System cleaner.
            description=_("The system in general"))

        #
        # options for Linux and BSD
        #
        if IS_POSIX:
            self.add_option(
                'desktop_entry',
                # TRANSLATORS: desktop entries are .desktop files in Linux that
                # make up the application menu (the menu that shows BleachBit,
                # Firefox, and others.  The .desktop files also associate file
                # types, so clicking on an .html file in Nautilus brings up
                # Firefox.
                # More information:
                # http://standards.freedesktop.org/menu-spec/latest/index.html#introduction
                _('Broken desktop files'),
                # TRANSLATORS: Description of the Broken desktop files cleaning option.
                _('Delete broken application menu entries and file associations'))
            self.add_option(
                'cache',
                # TRANSLATORS: Name of a cleaning option. Cache is a noun.
                _('Cache'),
                DELETE_CACHE_DESCRIPTION)
            self.add_option(
                'localizations',
                # TRANSLATORS: Localizations are files supporting specific
                # languages, so applications appear in Spanish, etc.
                _('Localizations'),
                # TRANSLATORS: Description of the Localizations cleaning option.
                _('Delete files for unwanted languages'))
            self.set_warning(
                'localizations',
                # TRANSLATORS: Warning for the Localizations cleaning option.
                _("Configure this option in the preferences."))
            self.add_option(
                'rotated_logs',
                # TRANSLATORS: 'Rotated logs' refers to old system log files.
                # Linux systems often have a scheduled job to rotate the logs
                # which means compress all except the newest log and then delete
                # the oldest log. You could translate this as 'old logs.'
                _('Rotated logs'),
                # TRANSLATORS: Description of the Rotated logs cleaning option.
                _('Delete old system logs'))
            self.add_option(
                'recent_documents',
                # TRANSLATORS: Name of a cleaning option for the history of recently used files.
                _('Recent documents list'),
                # TRANSLATORS: Description of the Recent documents list cleaning option.
                _('Delete the list of recently used documents'))
            self.add_option(
                'trash',
                # TRANSLATORS: Name of a cleaning option. Trash is a noun.
                _('Trash'),
                # TRANSLATORS: Description of the Trash cleaning option.
                _('Empty the trash'))

        #
        # options just for Linux
        #
        if IS_LINUX:
            self.add_option(
                'memory',
                # TRANSLATORS: Name of a cleaning option for system memory.
                _('Memory'),
                # TRANSLATORS: 'free' means 'unallocated'
                _('Wipe the swap and free memory'))
            self.set_warning(
                'memory',
                # TRANSLATORS: Warning for the experimental Memory cleaning option.
                _('This option is experimental and may cause system problems.'))

        #
        # options just for Microsoft Windows
        #
        has_dns_flush = IS_WINDOWS or (
            IS_LINUX and (
                FileUtilities.exe_exists(General.resolve_exe('resolvectl')) or
                FileUtilities.exe_exists(General.resolve_exe('systemd-resolve'))))
        if has_dns_flush:
            # TRANSLATORS: This is a label for the option to clear the system DNS cache.
            dns_cache_label = _('DNS cache')
            self.add_option('dns_cache', dns_cache_label,
                            _('Delete the cache'))

        if IS_WINDOWS:
            self.add_option(
                'logs',
                # TRANSLATORS: Name of a cleaning option for Windows log files.
                _('Logs'),
                # TRANSLATORS: Description of the Logs cleaning option.
                _('Delete the logs'))
            self.add_option(
                'memory_dump',
                # TRANSLATORS: Name of a cleaning option for Windows crash dump files.
                _('Memory dump'),
                # TRANSLATORS: Description of the Memory dump cleaning option.
                _('Delete the file'))
            self.add_option('muicache', 'MUICache', DELETE_CACHE_DESCRIPTION)
            # TRANSLATORS: Name of cleaning option. 'Prefetch' is Microsoft Windows jargon.
            self.add_option('prefetch', _('Prefetch'),
                            DELETE_CACHE_DESCRIPTION)
            self.add_option(
                'recycle_bin',
                # TRANSLATORS: Name of a cleaning option for the Windows recycle bin.
                _('Recycle bin'),
                # TRANSLATORS: Description of the Recycle bin cleaning option.
                _('Empty the recycle bin'))
            # TRANSLATORS: Name for cleaning option. 'Update' is an adjective to
            # describe the kind of uninstallers.
            updates_name = _('Update uninstallers')
            # TRANSLATORS: Description of cleaning option.
            updates_desc = _('Delete uninstallers for Microsoft updates including hotfixes, '
                             'service packs, and Internet Explorer updates')
            self.add_option('updates', updates_name, updates_desc)
            # TRANSLATORS: Warning shown when selecting an option.
            updates_warning = _('This option may prevent uninstalling '
                                'some updates.')
            self.set_warning('updates', updates_warning)

        #
        # options for GTK+
        #

        # The clipboard option is available wherever a clipboard can be
        # cleared: under GTK (POSIX) or natively on Windows.
        if gtk_may_be_available() or IS_WINDOWS:
            self.add_option(
                'clipboard',
                # TRANSLATORS: Name of a cleaning option. Clipboard is a noun.
                _('Clipboard'),
                # TRANSLATORS: Description of the Clipboard cleaning option.
                _('The desktop environment\'s clipboard used for copy and paste operations'))

        #
        # options common to all platforms
        #
        self.add_option(
            'custom',
            # TRANSLATORS: "Custom" is an option allowing the user to specify which
            # files and folders will be erased.
            _('Custom'),
            # TRANSLATORS: Description of the Custom cleaning option.
            _('Delete user-specified files and folders'))
        # TRANSLATORS: 'empty' means 'unallocated'
        self.add_option('empty_space', _('Empty space'),
                        # TRANSLATORS: 'empty' means 'unallocated'
                        _('Wipe empty space to hide deleted files'))
        self.set_warning('empty_space', EMPTY_SPACE_WARNING)
        self.add_option(
            'tmp',
            # TRANSLATORS: Name of a cleaning option for temporary files.
            _('Temporary files'),
            # TRANSLATORS: Description of the Temporary files cleaning option.
            _('Delete the temporary files'))

    def get_commands(self, option_id):
        # cache
        if IS_POSIX and 'cache' == option_id:
            dirnames = [os.path.expanduser("~/.cache/")]
            if IS_MAC:
                dirnames.insert(0, os.path.expanduser("~/Library/Caches/"))
            for dirname in dirnames:
                for filename in children_in_directory(dirname, True):
                    if not self.whitelisted(filename):
                        yield Command.Delete(filename)

        # custom
        if 'custom' == option_id:
            for (c_type, c_path) in options.get_custom_paths():
                if 'file' == c_type:
                    if os.path.lexists(c_path):
                        yield Command.Delete(c_path)
                elif 'folder' == c_type:
                    if os.path.lexists(c_path):
                        for path in children_in_directory(c_path, True):
                            yield Command.Delete(path)
                        yield Command.Delete(c_path)
                else:
                    raise RuntimeError(
                        f'custom folder has invalid type {c_type}')

        # menu
        if IS_POSIX and 'desktop_entry' == option_id:
            for path in MENU_DIRS:
                dirname = os.path.expanduser(path)
                for filename in children_in_directory(dirname, False):
                    # pylint: disable=possibly-used-before-assignment
                    if filename.endswith('.desktop') and Unix.is_broken_xdg_desktop(filename):
                        yield Command.Delete(filename)

        # unwanted locales
        if IS_POSIX and 'localizations' == option_id:
            for path in Unix.locales.localization_paths(locales_to_keep=options.get_languages()):
                # A symlinked locale directory points at a locale that may be
                # on the keep list, so delete the link without its contents.
                if FileUtilities.is_normal_directory(path):
                    for f in FileUtilities.children_in_directory(path, True):
                        yield Command.Delete(f)
                yield Command.Delete(path)

        # Windows logs
        if IS_WINDOWS and 'logs' == option_id:
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
                '%WindowsSystem%\\TZLog.log',
                '%WindowsSystem%\\config\\systemprofile\\Application Data\\Microsoft\\Internet Explorer\\brndlog.bak',
                '%WindowsSystem%\\config\\systemprofile\\Application Data\\Microsoft\\Internet Explorer\\brndlog.txt',
                '%WindowsSystem%\\LogFiles\\AIT\\AitEventLog.etl.???',
                '%WindowsSystem%\\LogFiles\\Firewall\\pfirewall.log*',
                '%WindowsSystem%\\LogFiles\\Scm\\SCM.EVM*',
                '%WindowsSystem%\\LogFiles\\WMI\\Terminal*.etl',
                '%WindowsSystem%\\LogFiles\\WMI\\RTBackup\\EtwRT.*etl',
                '%WindowsSystem%\\wbem\\Logs\\*.lo_',
                '%WindowsSystem%\\wbem\\Logs\\*.log', )

            for path in paths:
                for expanded in Windows.expand_windows_system_vars(path):
                    expanded = os.path.expandvars(expanded)
                    for globbed in glob.iglob(expanded):
                        yield Command.Delete(globbed)

        # memory
        if IS_LINUX and 'memory' == option_id:
            yield Command.Function(None, Memory.wipe_memory, _('Memory'))

        # memory dump
        # how to manually create this file
        # http://www.pctools.com/guides/registry/detail/856/
        if IS_WINDOWS and 'memory_dump' == option_id:
            fname = os.path.expandvars('$windir\\memory.dmp')
            if os.path.exists(fname):
                yield Command.Delete(fname)
            for fname in glob.iglob(os.path.expandvars('$windir\\Minidump\\*.dmp')):
                yield Command.Delete(fname)

        # most recently used documents list
        if IS_POSIX and 'recent_documents' == option_id:
            ru_fn = os.path.expanduser("~/.recently-used")
            if os.path.lexists(ru_fn):
                yield Command.Delete(ru_fn)
            # GNOME 2.26 (as seen on Ubuntu 9.04) will retain the list
            # in memory if it is simply deleted, so it must be shredded
            # (or at least truncated).
            #
            # GNOME 2.28.1 (Ubuntu 9.10) and 2.30 (10.04) do not re-read
            # the file after truncation, but do re-read it after
            # shredding.
            #
            # https://bugzilla.gnome.org/show_bug.cgi?id=591404

            def gtk_purge_items():
                """Purge GTK items"""
                from bleachbit.GtkShim import require_gtk  # pylint: disable=import-outside-toplevel
                require_gtk()
                from bleachbit.GtkShim import Gtk  # pylint: disable=import-outside-toplevel
                Gtk.RecentManager().get_default().purge_items()
                yield 0

            xbel_pathnames = [
                '~/.recently-used.xbel',
                '~/.local/share/recently-used.xbel*',
                '~/snap/*/*/.local/share/recently-used.xbel']
            for path1 in xbel_pathnames:
                for path2 in glob.iglob(os.path.expanduser(path1)):
                    if os.path.lexists(path2):
                        yield Command.Shred(path2)
            if gtk_may_be_available():
                # Use the Function to skip when in preview mode
                yield Command.Function(None, gtk_purge_items, _('Recent documents list'))

        if IS_POSIX and 'rotated_logs' == option_id:
            for path in Unix.rotated_logs():
                yield Command.Delete(path)

        # temporary files
        if IS_POSIX and 'tmp' == option_id:
            dirnames = ['/tmp', '/var/tmp']
            for dirname in dirnames:
                for path in children_in_directory(dirname, True):
                    is_open = FileUtilities.openfiles.is_open(path)
                    ok = not is_open and os.path.isfile(path) and \
                        not os.path.islink(path) and \
                        FileUtilities.ego_owner(path) and \
                        not self.whitelisted(path)
                    if ok:
                        yield Command.Delete(path)

        # temporary files
        if IS_WINDOWS and 'tmp' == option_id:
            dirnames = [os.path.expandvars(
                r'%temp%'), os.path.expandvars("%windir%\\temp\\")]
            # whitelist the folder %TEMP%\Low but not its contents
            # https://bugs.launchpad.net/bleachbit/+bug/1421726
            # Do not delete recent D-Bus nonce files because it allows
            # starting more than once instance of this application.
            gdbus_nonce_re = re.compile(r'gdbus-nonce-file-[0-9A-Za-z]+$',
                                        re.IGNORECASE)
            gdbus_nonce_max_age_seconds = 7 * 24 * 60 * 60  # 7 days
            for dirname in dirnames:
                low = os.path.join(dirname, 'low')
                for filename in children_in_directory(dirname, True):
                    if path_equal(low, filename, case_sensitive=False):
                        continue
                    if gdbus_nonce_re.match(os.path.basename(filename)):
                        try:
                            age = time.time() - os.stat(filename).st_mtime
                        except OSError:
                            continue
                        if age < gdbus_nonce_max_age_seconds:
                            continue
                    yield Command.Delete(filename)

        # trash
        if IS_POSIX and 'trash' == option_id:
            yield from Unix.get_trash_paths()

        # clipboard
        if 'clipboard' == option_id and (gtk_may_be_available() or IS_WINDOWS):
            if IS_WINDOWS and not gtk_may_be_available():
                # Works with TUI or wxPython
                def func_clear_clipboard():
                    """Command function to clear clipboard (Windows native)"""
                    Windows.clear_clipboard()
                    return 0
            else:
                def func_clear_clipboard():
                    """Command function to clear clipboard"""
                    # GuiUtil is GTK-specific
                    from bleachbit.GtkShim import require_gtk  # pylint: disable=import-outside-toplevel
                    require_gtk()
                    import bleachbit.GuiUtil
                    bleachbit.GuiUtil.clear_clipboard()
                    return 0
            yield Command.Function(None, func_clear_clipboard, _('Clipboard'))

        # wipe empty space
        if 'empty_space' == option_id and (shred_drives := options.get_list('shred_drives')):
            for pathname in shred_drives:
                # TRANSLATORS: 'Empty' means 'unallocated.'
                # %s expands to a path such as C:\ or /tmp/
                display = _("Wipe empty space in %s") % pathname

                def wipe_path_func(path=pathname):
                    # Yield control to GTK idle because this process
                    # is very slow.  Also display progress.
                    yield from wipe_path(path, idle=True)
                    yield 0
                yield Command.Function(None, wipe_path_func, display)

        # MUICache
        if IS_WINDOWS and 'muicache' == option_id:
            keys = (
                'HKCU\\Software\\Microsoft\\Windows\\ShellNoRoam\\MUICache',
                'HKCU\\Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache')
            for key in keys:
                yield Command.Winreg(key, None)

        # prefetch
        if IS_WINDOWS and 'prefetch' == option_id:
            for path in glob.iglob(os.path.expandvars('$windir\\Prefetch\\*.pf')):
                yield Command.Delete(path)

        # recycle bin
        if IS_WINDOWS and 'recycle_bin' == option_id:
            # This method allows shredding
            recycled_any = False
            # pylint: disable=possibly-used-before-assignment
            for path in Windows.get_recycle_bin():
                recycled_any = True
                yield Command.Delete(path)

            # Windows 10 refreshes the recycle bin icon when the user
            # opens the recycle bin folder.

            # This is a hack to refresh the icon.
            def empty_recycle_bin_func():
                tmpdir = tempfile.mkdtemp()
                Windows.move_to_recycle_bin(tmpdir)
                try:
                    Windows.empty_recycle_bin(None, True)
                except Exception:
                    logger.info(
                        'error in empty_recycle_bin()', exc_info=True)
                yield 0
            # Using the Function Command prevents emptying the recycle bin
            # when in preview mode.
            if recycled_any:
                yield Command.Function(None, empty_recycle_bin_func, _('Empty the recycle bin'))

        # DNS cache
        if 'dns_cache' == option_id:
            if IS_WINDOWS:
                yield Command.Function(None, Windows.flush_dns, _('DNS cache'))
            elif IS_LINUX:
                yield Command.Function(None, Unix.flush_dns, _('DNS cache'))

        # Windows Updates
        if IS_WINDOWS and 'updates' == option_id:
            yield from Windows.delete_updates()

    def init_whitelist(self):
        """Initialize the keep list (formerly whitelist) only once for performance"""
        regexes = [
            r'^/tmp/\.X0-lock$',
            r'^/tmp/\.truecrypt_aux_mnt.*/(control|volume)$',
            r'^/tmp/\.vbox-[^/]+-ipc/lock$',
            r'^/tmp/\.wine-[0-9]+/server-.*/lock$',
            '^/tmp/fsa/',  # fsarchiver
            '^/tmp/gconfd-[^/]+/lock/ior$',
            '^/tmp/kde-',
            '^/tmp/kdesudo-',
            '^/tmp/ksocket-',
            r'^/tmp/orbit-[^/]+/bonobo-activation-register[a-z0-9-]*\.lock$',
            '^/tmp/orbit-[^/]+/bonobo-activation-server-[a-z0-9-]*ior$',
            '^/tmp/pulse-[^/]+/pid$',
            '^/tmp/xauth',
            '^/var/tmp/kdecache-',
            '^' + os.path.expanduser(r'~/\.cache/wallpaper/'),
            # Flatpak mount point
            '^' + os.path.expanduser(r'~/\.cache/doc($|/)'),
            # Clean Firefox cache from Firefox cleaner (LP#1295826)
            '^' + os.path.expanduser(r'~/\.cache/mozilla/'),
            # Clean Google Chrome cache from Google Chrome cleaner (LP#656104)
            '^' + os.path.expanduser(r'~/\.cache/google-chrome/'),
            '^' + os.path.expanduser(r'~/\.cache/gnome-control-center/'),
            # Clean Evolution cache from Evolution cleaner (GitHub #249)
            '^' + os.path.expanduser(r'~/\.cache/evolution/'),
            # iBus Pinyin
            # https://bugs.launchpad.net/bleachbit/+bug/1538919
            '^' + os.path.expanduser(r'~/\.cache/ibus/'),
            # Linux Bluetooth daemon obexd directory is typically empty, so be careful
            # not to delete the empty directory.
            '^' + os.path.expanduser(r'~/\.cache/obexd($|/)'),
            # KDE/Plasma cache files
            # https://github.com/bleachbit/bleachbit/issues/1853
            '^' + os.path.expanduser(r'~/\.cache/kwin($|/)'),  # folder
            # folder
            '^' + os.path.expanduser(r'~/\.cache/mesa_shader_cache($|/)'),
            '^' + os.path.expanduser(r'~/\.cache/plasmashell($|/)'),  # folder
            '^' + os.path.expanduser(r'~/\.cache/icon-cache\.kcache$'),  # file
            # file
            r'^' + os.path.expanduser(r'~/\.cache/plasma_theme_.*\.kcache$'),
            '^' + os.path.expanduser(r'~/\.cache/drkonqi($|/)'),  # folder
            # folder
            '^' + os.path.expanduser(r'~/\.cache/mesa_shader_cache_db($|/)'),
            # folder
            '^' + os.path.expanduser(r'~/\.cache/qtshadercache-[^/]+($|/)'),
            # file
            '^' + os.path.expanduser(r'~/\.cache/plasma_theme_default\.kcache$')]

        self.keep_list_re = re.compile(
            '|'.join(f'(?:{regex})' for regex in regexes))

    def whitelisted(self, pathname):
        """Return boolean whether file is keep listed (formerly whitelisted)"""
        if IS_WINDOWS:
            # Whitelist is specific to POSIX
            return False
        if self.keep_list_re is None:
            self.init_whitelist()
        return self.keep_list_re.match(pathname) is not None


def register_cleaners(cb_progress=lambda x: None, cb_done=lambda: None, allow_local=True):
    """Register all known cleaners: system, CleanerML, and Winapp2"""
    # wipe out any registrations
    # Because this is a global variable, cannot use backends = {}
    backends.clear()

    # initialize "hard coded" (non-CleanerML) backends
    backends["system"] = System()

    if not options.get("load_cleaners"):
        cb_done()
        yield False
        return

    # register CleanerML cleaners
    # TRANSLATORS: Progress message shown typically on startup.
    # 'Native' refers to the .xml cleaners designed for this application,
    # as contrasted to Winapp2.ini, which is native to another application.
    # 'Loading' is a present participle.
    # To indicate an ongoing operation, include the ellipsis as literal
    # Unicode (…) or as Unicode escape (\u2026).
    cb_progress(_('Loading native cleaners\u2026'))
    yield from CleanerML.load_cleaners(cb_progress, allow_local=allow_local)

    # register Winapp2.ini cleaners
    if IS_WINDOWS:
        # TRANSLATORS: Progress message shown typically on startup.
        # 'Importing' is a present participle.
        # To indicate an ongoing operation, include the ellipsis as literal
        # Unicode (…) or as Unicode escape (\u2026).
        cb_progress(_('Importing cleaners from Winapp2.ini\u2026'))
        # pylint: disable=import-outside-toplevel
        from bleachbit import Winapp
        yield from Winapp.load_cleaners(cb_progress)

    cb_done()

    yield False  # end the iteration


def simpler_cleaner_process_path(path):
    """Process a path for create_simple_cleaner

    Returns the absolute path to shred or None if invalid.

    Invalid:
        - not a string
        - empty string
        - path resolves to CWD or its parent

    Not checked: path existence or type of path
    """
    if not isinstance(path, str):
        raise RuntimeError(
            f'expected path as string but got {str(path)}')
    if not path.strip():
        logger.warning('Refusing to clean an empty path')
        return None
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    else:
        path = os.path.normpath(path)
    cwd = os.getcwd()
    cwd_parent = os.path.dirname(cwd)
    if path in (cwd, cwd_parent):
        logger.warning(
            'Refusing to shred working directory or its parent: %s', path)
        return None
    return path


class CustomFileAction(Action.ActionProvider):
    """Custom file action"""
    # At module level because the metaclass registers every subclass globally
    action_key = '__customfileaction'

    def __init__(self, paths):
        Action.ActionProvider.__init__(self, None)
        self.paths = paths

    def get_commands(self):
        for path in self.paths:
            path = simpler_cleaner_process_path(path)
            if not path:
                continue
            if os.path.isdir(path):
                for child in children_in_directory(path, True):
                    yield Command.Shred(child)
            yield Command.Shred(path)


def create_simple_cleaner(paths):
    """Shred arbitrary files (used in CLI and GUI)"""
    cleaner = Cleaner()
    cleaner.add_option(option_id='files', name='', description='')
    cleaner.name = _("System")  # shows up in progress bar
    cleaner.add_action('files', CustomFileAction(paths))
    return cleaner


class CustomWipeAction(Action.ActionProvider):
    """Custom wipe action"""
    action_key = '__customwipeaction'

    def __init__(self, path):
        Action.ActionProvider.__init__(self, None)
        self.path = path
        # TRANSLATORS: %s is the path of the drive whose empty space will be wiped.
        self.display = _("Wipe empty space %s") % path

    def get_commands(self):
        def wipe_path_func():
            yield from wipe_path(self.path, idle=True)
            yield 0
        yield Command.Function(None, wipe_path_func, self.display)


def create_wipe_empty_space_cleaner(path):
    """Wipe empty space of arbitrary paths (used in GUI)"""
    cleaner = Cleaner()
    cleaner.add_option(
        option_id='empty_space', name='', description='')
    cleaner.name = ''
    cleaner.add_action('empty_space', CustomWipeAction(path))
    return cleaner
