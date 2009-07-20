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
Perform (or assist with) cleaning operations.
"""

from gettext import gettext as _
import glob
import gtk
import os.path
import re
import subprocess
import sys
import traceback
import xml.dom.minidom

import FileUtilities

if 'linux2' == sys.platform:
    import Unix

if 'win32' == sys.platform:
    import Windows

from FileUtilities import children_in_directory
import globals
from Options import options


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
        for ''option_id'"""
        self.actions += ( (option_id, action), )

    def add_option(self, option_id, name, description):
        self.options[option_id] = ( name, False, description )

    def add_running(self, type, pathname):
        """Add a way to detect this program is currently running"""
        self.running += ( (type, pathname), )

    def auto_hide(self):
        """Return boolean whether it is OK to automatically hide this
        cleaner"""
        ret = True
        for (option_id, __name, __value) in self.get_options():
            self.set_option(option_id, True)
        try:
            for pathname in self.list_files():
                ret = False
                break
            if ret:
                for pathname in self.other_cleanup(really_delete = False):
                    ret = False
                    break
        except:
            traceback.print_exc()
        for (option_id, __name, __value) in self.get_options():
            self.set_option(option_id, False)
        return ret

    def available(self):
        """Is the cleaner available?"""
        return True

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
                yield ((self.options[key][0], self.options[key][2]))

    def get_options(self):
        """Return user-configurable options in 3-tuple (id, name, enabled)"""
        r = []
        if self.options:
            for key in sorted(self.options.keys()):
                r.append((key, self.options[key][0], self.options[key][1]))
        return r

    def get_warning(self, option_id):
        """Return a warning as string."""
        if option_id in self.warnings:
            return self.warnings[option_id]
        else:
            return None

    def is_running(self):
        """Return whether the program is currently running"""
        for running in self.running:
            type = running[0]
            pathname = running[1]
            if 'exe' == type and sys.platform == 'linux2':
                if Unix.is_running(pathname):
                    print "debug: process '%s' is runnning" % pathname
                    return True
            elif 'exe' == type and sys.platform == 'win32':
                if pathname in Windows.enumerate_processes():
                    print "debug: process '%s' is runnning" % pathname
                    return True
            elif 'pathname' == type:
                expanded = os.path.expanduser(os.path.expandvars(pathname))
                for globbed in glob.iglob(expanded):
                    if os.path.exists(globbed):
                        print "debug: file '%s' exists indicating '%s' is running" % (globbed, self.name)
                        return True
            else:
                raise RuntimeError("Unknown running-detection type '%s'" % type)
        return False

    def is_usable(self):
        """Return whether the cleaner is usable (has actions)"""
        return len(self.actions) > 0

    def list_files(self):
        """Iterate files that would be removed"""
        for action in self.actions:
            option_id = action[0]
            if self.options[option_id][1]:
                for pathname in action[1].list_files():
                    yield pathname

    def other_cleanup(self, really_delete):
        """Perform an operation more specialized than removing a file"""
        for action in self.actions:
            option_id = action[0]
            if self.options[option_id][1]:
                for pathname in action[1].other_cleanup(really_delete):
                    yield pathname

    def set_option(self, option_id, value):
        """Enable or disable an option"""
        assert self.options.has_key(option_id)
        self.options[option_id] = (self.options[option_id][0], \
            value, self.options[option_id][2])

    def set_warning(self, option_id, description):
        """Set a warning to be displayed when option is selected interactively"""
        self.warnings[option_id] = description


class Firefox(Cleaner):
    """Mozilla Firefox"""

    def __init__(self):
        Cleaner.__init__(self)
        self.add_option('cache', _('Cache'), _('Delete the web cache, which reduces time to display revisited pages'))
        self.add_option('cookies', _('Cookies'), _('Delete cookies, which contain information such as web site prefereneces, authentication, and tracking identification'))
        self.add_option('download_history', _('Download history'), _('List of files downloaded'))
        self.add_option('forms', _('Form history'), _('A history of forms entered in web sites and in the Search bar'))
        self.add_option('session_restore', _('Session restore'), _('Loads the initial session after the browser closes or crashes'))
        self.add_option('passwords', _('Passwords'), _('A database of usernames and passwords as well as a list of sites that should not store passwords'))
        self.add_option('places', _('Places'), _('A database of URLs including bookmarks, favicons, and a history of visited web sites'))
        self.set_warning('places', _('Deleting Places deletes bookmarks.'))
        self.add_option('url_history', _('URL history'), _('List of visited web pages'))
        # TRANSLATORS: Vacuum is a verb.  You could translate the words
        # 'compact' or 'optimize' instead.
        self.add_option('vacuum', _('Vacuum'), _('Clean database fragmentation to reduce space and improve speed without removing any data'))

        if sys.platform == 'linux2':
            self.profile_dir = "~/.mozilla/firefox*/*/"
            self.add_running('exe', 'firefox')
            self.add_running('exe', 'firefox-bin')
            self.add_running('pathname', self.profile_dir + 'lock')
        if sys.platform == 'win32':
            self.profile_dir = "$USERPROFILE\\Application Data\\Mozilla\\Firefox\\Profiles\\*\\"
            self.add_running('exe', 'firefox.exe')
            self.add_running('pathname', self.profile_dir + 'parent.lock')

    def get_description(self):
        return _("Web browser")

    def get_id(self):
        return 'firefox'

    def get_name(self):
        return "Firefox"

    def list_files(self):
        # browser cache
        cache_base = None
        if sys.platform == 'linux2':
            cache_base = self.profile_dir
        if sys.platform == 'win32':
            cache_base = "$USERPROFILE\\Local Settings\\Application Data\\Mozilla\\Firefox\\Profiles\\*"
        if self.options["cache"][1]:
            dirs = FileUtilities.expand_glob_join(cache_base, "Cache*")
            dirs += FileUtilities.expand_glob_join(cache_base, "OfflineCache")
            for dirname in dirs:
                for filename in children_in_directory(dirname, False):
                    yield filename
        files = []
        # cookies
        if self.options["cookies"][1]:
            files += FileUtilities.expand_glob_join(self.profile_dir, "cookies.txt")
            files += FileUtilities.expand_glob_join(self.profile_dir, "cookies.sqlite")
        # download history
        if self.options["download_history"][1]:
            # Firefox version 1
            files += FileUtilities.expand_glob_join(self.profile_dir, "downloads.rdf")
            # Firefox version 3
            files += FileUtilities.expand_glob_join(self.profile_dir, "downloads.sqlite")
        # forms
        if self.options["forms"][1]:
            files += FileUtilities.expand_glob_join(self.profile_dir, "formhistory.dat")
            files += FileUtilities.expand_glob_join(self.profile_dir, "formhistory.sqlite")
        # passwords
        if self.options["passwords"][1]:
            files += FileUtilities.expand_glob_join(self.profile_dir, "signons.txt")
            files += FileUtilities.expand_glob_join(self.profile_dir, "signons[2-3].txt")
        # places database
        if self.options["places"][1]:
            # Firefox version 3
            files += FileUtilities.expand_glob_join(self.profile_dir, "places.sqlite")
            files += FileUtilities.expand_glob_join(self.profile_dir, "places.sqlite-journal")
            files += FileUtilities.expand_glob_join(self.profile_dir, "bookmarkbackups/*ookmark*json")
            # see also option 'url_history'
        # session restore
        if self.options["session_restore"][1]:
            files += FileUtilities.expand_glob_join(self.profile_dir, "sessionstore.js")
        # URL history
        if self.options["url_history"][1]:
            # Firefox version 1
            files += FileUtilities.expand_glob_join(self.profile_dir, "history.dat")
            # see also function other_cleanup()
        # finish
        for filename in files:
            yield filename


    def delete_url_history(self, path):
        """Delete URL history in Firefox 3 places.sqlite"""

        # delete the URLs in moz_places
        places_suffix = "where id in (select " \
            "moz_places.id from moz_places " \
            "left join moz_inputhistory on moz_inputhistory.place_id = moz_places.id " \
            "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
            "where moz_inputhistory.input is null " \
            "and moz_bookmarks.id is null); "

        cmds = ""

        if options.get('shred'):
            shred_places_cmd = "update moz_places " \
                "set url = randomblob(length(url)), " \
                "rev_host = randomblob(length(rev_host)), " \
                "title = randomblob(length(title))" + places_suffix
            cmds += shred_places_cmd
            shred_places_cmd = "update moz_places " \
                "set url = zeroblob(length(url)), " \
                "rev_host = zeroblob(length(rev_host)), " \
                "title = zeroblob(length(title))" + places_suffix
            cmds += shred_places_cmd


        delete_places_cmd = "delete from moz_places " + places_suffix
        cmds += delete_places_cmd

        # delete any orphaned annotations in moz_annos
        annos_suffix =  "where id in (select moz_annos.id " \
            "from moz_annos " \
            "left join moz_places " \
            "on moz_annos.place_id = moz_places.id " \
            "where moz_places.id is null); "

        if options.get('shred'):
            shred_annos_cmd = "update moz_annos " \
                "set content = randomblob(length(content)) " \
                + annos_suffix
            cmds += shred_annos_cmd
            shred_annos_cmd = "update moz_annos " \
                "set content = zeroblob(length(content)) " \
                + annos_suffix
            cmds += shred_annos_cmd

        delete_annos_cmd = "delete from moz_annos " + annos_suffix
        cmds += delete_annos_cmd

        # delete any orphaned favicons
        fav_suffix = "where id not in (select favicon_id " \
            "from moz_places ); "

        if options.get('shred'):
            shred_fav_cmd = "update moz_favicons " \
                "set url = randomblob(length(url)), " \
                "data = randomblob(length(data)) " \
                +  fav_suffix
            cmds += shred_fav_cmd
            shred_fav_cmd = "update moz_favicons " \
                "set url = zeroblob(length(url)), " \
                "data = zeroblob(length(data)) " \
                +  fav_suffix
            cmds += shred_fav_cmd


        delete_fav_cmd = "delete from moz_favicons " + fav_suffix
        cmds += delete_fav_cmd

        # delete any orphaned history visits
        cmds += "delete from moz_historyvisits where place_id not " \
            "in (select id from moz_places); "

        # execute the commands
        FileUtilities.execute_sqlite3(path, cmds)


    def other_cleanup(self, really_delete = False):
        # URL history
        if self.options['url_history'][1] and not self.options["places"][1]:
            for path in FileUtilities.expand_glob_join(self.profile_dir, "places.sqlite"):
                if really_delete:
                    oldsize = os.path.getsize(path)
                    self.delete_url_history(path)
                    newsize = os.path.getsize(path)
                    yield (oldsize - newsize, path)
                else:
                    yield path

        # vacuum
        if self.options['vacuum'][1]:
            for path in FileUtilities.expand_glob_join(self.profile_dir, "*.sqlite"):
                if really_delete:
                    oldsize = os.path.getsize(path)
                    FileUtilities.vacuum_sqlite3(path)
                    newsize = os.path.getsize(path)
                    yield (oldsize - newsize, path)
                else:
                    yield path


class KDE(Cleaner):
    """KDE"""

    def __init__(self):
        Cleaner.__init__(self)
        self.add_option('cache', _('Cache'), _('Delete the cache'))
        self.add_option('tmp', _('Temporary files'), _('Delete the temporary files'))

    def get_description(self):
        return _("KDE desktop environment")

    def get_id(self):
        return 'kde'

    def get_name(self):
        return "KDE"

    def list_files(self):
        # cache
        if self.options["cache"][1]:
            dirs = glob.glob(os.path.expanduser("~/.kde/cache-*/"))
            for dirname in dirs:
                for filename in children_in_directory(dirname, False):
                    yield filename
        # temporary
        if self.options["tmp"][1]:
            dirs = glob.glob(os.path.expanduser("~/.kde/tmp-*/"))
            for dirname in dirs:
                for path in children_in_directory(dirname, False):
                    yield path


class OpenOfficeOrg(Cleaner):
    """Delete OpenOffice.org cache"""

    def __init__(self):
        Cleaner.__init__(self)
        self.options = {}
        self.add_option('cache', _('Cache'), _('Delete the cache'))
        self.add_option('recent_documents', _('Most recently used'), _("Delete the list of recently used documents"))

        # reference: http://katana.oooninja.com/w/editions_of_openoffice.org
        if sys.platform == 'linux2':
            self.prefixes = [ "~/.ooo-2.0", "~/.openoffice.org2", "~/.openoffice.org2.0", "~/.openoffice.org/3" ]
            self.prefixes += [ "~/.ooo-dev3" ]
        if sys.platform == 'win32':
            self.prefixes = [ "$APPDATA\\OpenOffice.org\\3", "$APPDATA\\OpenOffice.org2" ]

    def get_description(self):
        return _("Office suite")

    def get_id(self):
        return 'openofficeorg'

    def get_name(self):
        return "OpenOffice.org"

    def list_files(self):
        if self.options["recent_documents"][1]:
             for prefix in self.prefixes:
                for path in FileUtilities.expand_glob_join(prefix, "user/registry/data/org/openoffice/Office/Histories.xcu"):
                    if os.path.lexists(path):
                        yield path
                for path in FileUtilities.expand_glob_join(prefix, "user/registry/cache/org.openoffice.Office.Histories.dat"):
                    if os.path.lexists(path):
                        yield path


        if self.options["recent_documents"][1] and not self.options["cache"][1]:
            for prefix in self.prefixes:
                for path in FileUtilities.expand_glob_join(prefix, "user/registry/cache/org.openoffice.Office.Common.dat"):
                    if os.path.lexists(path):
                        yield path

        if not self.options["cache"][1]:
            return
        dirs = []
        for prefix in self.prefixes:
            dirs += FileUtilities.expand_glob_join(prefix, "user/registry/cache/")
        for dirname in dirs:
            for filename in children_in_directory(dirname, False):
                yield filename

    def erase_history(self, path):
        """Erase the history node (most recently used documents)"""
        dom1 = xml.dom.minidom.parse(path)
        for node in dom1.getElementsByTagName("node"):
            if node.hasAttribute("oor:name"):
                if "History" == node.getAttribute("oor:name"):
                    node.parentNode.removeChild(node)
                    node.unlink()
                    break
        dom1.writexml(open(path, "w"))

    def other_cleanup(self, really_delete = False):
        if not self.options["recent_documents"][1]:
            return
        for prefix in self.prefixes:
            for path in FileUtilities.expand_glob_join(prefix, "user/registry/data/org/openoffice/Office/Common.xcu"):
                if os.path.lexists(path):
                    if really_delete:
                        oldsize = os.path.getsize(path)
                        self.erase_history(path)
                        newsize = os.path.getsize(path)
                        yield (oldsize - newsize, path)
                    else:
                        yield path


class rpmbuild(Cleaner):
    """Delete the rpmbuild build directory"""

    def get_description(self):
        return _("Delete the files in the rpmbuild build directory")

    def get_id(self):
        return 'rpmbuild'

    def get_name(self):
        return "rpmbuild"

    def list_files(self):
        dirnames = set([ os.path.expanduser("~/rpmbuild/BUILD/") ])
        try:
            args = ["rpm", "--eval", "%_topdir"]
            dirname = subprocess.Popen(args, stdout=subprocess.PIPE).\
                communicate()[0]
        except:
            print "warning: exception '%s' running '%s'" % \
                (str(sys.exc_info()[1]), " ".join(args))
        else:
            dirnames.add(dirname + "/BUILD")
        for dirname in dirnames:
            for filename in children_in_directory(dirname, True):
                yield filename


class System(Cleaner):
    """System in general"""

    def __init__(self):
        Cleaner.__init__(self)
        if sys.platform == 'linux2':
            # TRANSLATORS: desktop entries are .desktop files in Linux tha
            # make up the application menu (the menu that shows BleachBit,
            # Firefox, and others.  The .desktop files also associate file
            # types, so clicking on an .html file in Nautilus brings up
            # Firefox.
            # More information: http://standards.freedesktop.org/menu-spec/latest/index.html#introduction
            self.add_option('desktop_entry', _('Broken desktop files'), _('Delete broken application menu entries and file associations'))
            self.add_option('cache', _('Cache'), _('Delete the cache'))
            # TRANSLATORS: Localizations are files supporting specific
            # languages, so applications appear in Spanish, etc.
            self.add_option('localizations', _('Localizations'), _('Delete files for unwanted languages'))
            # TRANSLATORS: 'Rotated logs' refers to old system log files.
            # Linux systems often have a scheduled job to rotate the logs
            # which means compress all except the newest log and then delete
            # the oldest log.  You could translate this 'old logs.'
            self.add_option('rotated_logs', _('Rotated logs'), _('Delete old system logs'))
            self.add_option('recent_documents', _('Recent documents list'), _('Delete the list of recently used documents'))
            self.add_option('trash', _('Trash'), _('Empty the trash'))
            # TRANSLATORS: Yum is a software program (similar to APT)
            # that manages packages on CentOS, Fedora, and Red Hat.
            self.add_option('yum', _('Yum clean'), _("Delete the cache"))
        if sys.platform == 'win32':
            self.add_option('mru', _('Most recently used'), _('Delete the list of recently used documents'))
        self.add_option('clipboard', _('Clipboard'), _('The desktop environment\'s clipboard used for copy and paste operations'))
        self.add_option('recycle_bin', _('Recyle bin'), _('Empty the recycle bin'))
        self.add_option('tmp', _('Temporary files'), _('Delete the temporary files'))

    def get_description(self):
        return _("The system in general")

    def get_id(self):
        return 'system'

    def get_name(self):
        return _("System")

    def list_files(self):
        # cache
        if sys.platform == 'linux2' and self.options["cache"][1]:
            dirname = os.path.expanduser("~/.cache/")
            for filename in children_in_directory(dirname, True):
                yield filename

        # menu
        menu_dirs = [ '~/.local/share/applications', \
            '~/.config/autostart', \
            '~/.gnome/apps/', \
            '~/.gnome2/panel2.d/default/launchers', \
            '~/.gnome2/vfolders/applications/', \
            '~/.kde/share/apps/RecentDocuments/', \
            '~/.kde/share/mimelnk', \
            '~/.kde/share/mimelnk/application/ram.desktop', \
            '~/.kde2/share/mimelnk/application/', \
            '~/.kde2/share/applnk' ]

        if sys.platform == 'linux2' and self.options["desktop_entry"][1]:
            for dirname in menu_dirs:
                for filename in [fn for fn in children_in_directory(dirname, False) \
                    if fn.endswith('.desktop') ]:
                    if Unix.is_broken_xdg_desktop(filename):
                        yield filename

        # unwanted locales
        if sys.platform == 'linux2' and self.options["localizations"][1]:
            callback = lambda locale, language: options.get_language(language)
            for path in Unix.locales.localization_paths(callback):
                yield path

        # most recently used documents list
        files = []
        if sys.platform == 'linux2' and self.options["recent_documents"][1]:
            files += [ os.path.expanduser("~/.recently-used") ]
            files += [ os.path.expanduser("~/.recently-used.xbel") ]

        # fixme http://www.freedesktop.org/wiki/Specifications/desktop-bookmark-spec

        if sys.platform == 'linux2' and self.options["rotated_logs"][1]:
            for path in Unix.rotated_logs():
                yield path


        # temporary
        if sys.platform == 'linux2' and self.options["tmp"][1]:
            dirnames = [ '/tmp', '/var/tmp' ]
            for dirname in dirnames:
                for path in children_in_directory(dirname, True):
                    is_open = FileUtilities.openfiles.is_open(path)
                    ok = not is_open and os.path.isfile(path) and \
                        not os.path.islink(path) and \
                        FileUtilities.ego_owner(path) and \
                        not self.whitelisted(path)
                    if ok:
                        yield path

        if sys.platform == 'win32' and self.options["tmp"][1]:
            dirname = os.path.expandvars("$USERPROFILE\\Local Settings\\Temp\\")
            for filename in children_in_directory(dirname, True):
                yield filename
            dirname = os.path.expandvars("$windir\\temp\\")
            for filename in children_in_directory(dirname, True):
                yield filename


        # trash
        if sys.platform == 'linux2' and self.options["trash"][1]:
            dirname = os.path.expanduser("~/.Trash")
            for filename in children_in_directory(dirname, False):
                yield filename
            # fixme http://www.ramendik.ru/docs/trashspec.html
            # http://standards.freedesktop.org/basedir-spec/basedir-spec-0.6.html
            # ~/.local/share/Trash
            # * GNOME 2.22, Fedora 9
            # * KDE 4.1.3, Ubuntu 8.10
            dirname = os.path.expanduser("~/.local/share/Trash/files")
            for filename in children_in_directory(dirname, True):
                yield filename
            dirname = os.path.expanduser("~/.local/share/Trash/info")
            for filename in children_in_directory(dirname, True):
                yield filename
            dirname = os.path.expanduser("~/.local/share/Trash/expunged")
            # desrt@irc.gimpnet.org tells me that the trash
            # backend puts files in here temporary, but in some situations
            # the files are stuck.
            for filename in children_in_directory(dirname, True):
                yield filename


        # finish
        for filename in files:
            if os.path.lexists(filename):
                yield filename

    def other_cleanup(self, really_delete):
        if self.options["clipboard"][1]:
            if really_delete:
                gtk.gdk.threads_enter()
                clipboard = gtk.clipboard_get()
                clipboard.set_text("")
                gtk.gdk.threads_leave()
                yield (0, _("Clipboard"))
            else:
                yield _("Clipboard")

        if sys.platform == 'win32' and self.options['mru'][1]:

                # reference: http://support.microsoft.com/kb/142298
                keys = ( \
                    # search assistant
                    'HKCU\Software\Microsoft\Search Assistant\ACMru',
                    # common open dialog
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedMRU',
                    # Windows Vista/7
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU',
                    # common save as dialog
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSaveMRU',
                    # Windows Vista/7
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU',
                    # find files command
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Doc Find Spec MRU',
                    # find Computer command
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FindComputerMRU',
                    # map network drives
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Map Network Drive MRU',
                    # printer ports
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\PrnPortsMRU',
                    # recent documents in start menu
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs',
                    # run command
                    'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU' )
                for key in keys:
                    ret = Windows.delete_registry_key(key, really_delete)
                    if not ret:
                        # nothing to delete or nothing was deleted
                        continue
                    if really_delete:
                        yield (0, key)
                    else:
                        yield key


        if sys.platform == 'win32' and self.options['recycle_bin'][1]:
            for ret in Windows.empty_recycle_bin(really_delete):
                yield ret


        if sys.platform == 'linux2' and self.options["yum"][1]:
            if really_delete:
                bytes = Unix.yum_clean()
                yield (bytes, _("Yum clean"))
            else:
                yield _("Yum clean")


    def whitelisted(self, pathname):
        """Return boolean whether file is whitelisted"""
        regexes = [
            '^/tmp/.truecrypt_aux_mnt.*/(control|volume)$',
            '^/tmp/.vbox-[^/]+-ipc/lock$',
            '^/tmp/.wine-[0-9]+/server-.*/lock$',
            '^/tmp/.X0-lock$',
            '^/tmp/gconfd-[^/]+/lock/ior$',
            '^/tmp/ksocket-[^/]+/(Arts_SoundServerV2|secret-cookie)$',
            '^/tmp/orbit-[^/]+/bonobo-activation-register[a-z0-9-]*.lock$',
            '^/tmp/orbit-[^/]+/bonobo-activation-server-[a-z0-9-]*ior$',
            '^/tmp/pulse-[^/]+/pid$' ]
        for regex in regexes:
            if None != re.match(regex, pathname):
                return True
        return False


backends = {}
backends["firefox"] = Firefox()
if sys.platform == 'linux2':
    backends["kde"] = KDE()
backends["openofficeorg"] = OpenOfficeOrg()
if sys.platform == 'linux2':
    backends["rpmbuild"] = rpmbuild()
backends["system"] = System()


import unittest

class TestCleanerBackend(unittest.TestCase):

    def test_auto_hide(self):
        for key in sorted(backends):
            self.assert_ (type(backends[key].auto_hide()) is bool)

    def test_get_name(self):
        for key in sorted(backends):
            self.assert_ (type(backends[key].get_name()) is str)

    def test_get_descrption(self):
        for key in sorted(backends):
            for desc in backends[key].get_description():
                self.assert_ (type(desc) is str)

    def test_get_options(self):
        for key in sorted(backends):
            for (test_id, name, value) in backends[key].get_options():
                self.assert_ (type(test_id) is str)
                self.assert_ (type(name) is str)
                self.assert_ (type(value) is bool)

    def test_list_files(self):
        for key in sorted(backends):
            print "debug: test_list_files: key='%s'" % (key, )
            for (option_id, __name, __value) in backends[key].get_options():
                backends[key].set_option(option_id, True)
            for filename in backends[key].list_files():
                self.assert_ (type(filename) is str)
                self.assert_ (os.path.lexists(filename), \
                    "In backend '%s' path does not exist: '%s' \
                    " % (key, filename))

    def test_other_cleanup(self):
        """Test the method other_cleanup()"""
        for key in sorted(backends):
            for (cleaner_id, __name, __value) in backends[key].get_options():
                backends[key].set_option(cleaner_id, True)
            for description in backends[key].other_cleanup(False):
                self.assert_(type(description) is str or None == description)

    def test_whitelist(self):
        tests = [ \
            ('/tmp/.truecrypt_aux_mnt1/control', True), \
            ('/tmp/.truecrypt_aux_mnt1/volume', True), \
            ('/tmp/.vbox-foo-ipc/lock', True), \
            ('/tmp/.wine-500/server-806-102400f/lock', True), \
            ('/tmp/gconfd-foo/lock/ior', True), \
            ('/tmp/ksocket-foo/Arts_SoundServerV2', True), \
            ('/tmp/ksocket-foo/secret-cookie', True), \
            ('/tmp/orbit-foo/bonobo-activation-server-ior', True), \
            ('/tmp/orbit-foo/bonobo-activation-register.lock', True), \
            ('/tmp/orbit-foo/bonobo-activation-server-a9cd6cc4973af098918b154c4957a93f-ior', True), \
            ('/tmp/orbit-foo/bonobo-activation-register-a9cd6cc4973af098918b154c4957a93f.lock', True), \
            ('/tmp/pulse-foo/pid', True), \
            ('/tmp/tmpsDOBFd', False) \
            ]
        for test in tests:
            self.assertEqual(backends['system'].whitelisted(test[0]), test[1], test[0])

if __name__ == '__main__':
    unittest.main()

