# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2008 Andrew Ziem
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



import gettext
gettext.install("bleachbit")
import glob
import os.path
import re
import xml.dom.minidom

import FileUtilities


class Cleaner:
    """Base class for a cleaner"""

    def __init__(self):
        self.options = None

    def available(self):
        """Is the cleaner available?"""
        return True

    def get_description(self):
        """Brief description"""
        return ""

    def get_id(self):
        """Return the unique name of this cleaner"""
        return None

    def get_name(self):
        """Return the human name of this cleaner"""
        return None

    def get_options(self):
        """Return user-configurable options in 3-tuple (id, name, value)"""
        r = []
        if self.options:
            for key in sorted(self.options.keys()):
                r.append((key, self.options[key][0], self.options[key][1]))                
        return r

    def list_files(self):
        """Iterate files that would be removed"""

    def run(self):
        """Execute the cleaning operation and iterate (bytes deleted, size of file)"""
        for file in self.list_files(self):
            size = FileUtilities.size_of_file.file(file)
            FileUtilities.delete_file(file)
            yield (size, file)

    def set_option(self, option, value):
        assert self.options.has_key(option)
        print "debug: set_option: '%s' = '%s'" % (option, value)
        self.options[option] = (self.options[option][0], value)


class Bash(Cleaner):
    """Clear the Bash history"""

    def get_description(self):
        return 'Clear the Bash history'

    def get_id(self):
        return 'bash'

    def get_name(self):
        return "Bash"

    def list_files(self):
        yield os.path.expanduser("~/.bash_history")

class Beagle(Cleaner):
    """Beagle"""

    def get_description(self):
        return _("Clear Beagle indexes and logs")

    def get_id(self):
        return 'beagle'

    def get_name(self):
        return "Beagle"

    def list_files(self):
        dirs = [ "~/.beagle/Indexes", "~/.beagle/Log", "~/.beagle/TextCache" ]
        for dirname in dirs:
            dirname = os.path.expanduser(dirname)
            for filename in FileUtilities.children_in_directory(dirname, False):
                yield filename



class Epihany(Cleaner):
    """Epiphany"""

    def __init__(self):
        self.options = {}
        self.options["cache"] = ( _("Cache"), False ) 
        self.options["cookies"] = ( _("Cookies"), False )
        self.options["download_history"] = ( _("Download history"), False)
        self.options["places"] = ( _("Places"), False)
        self.options["signons"] = ( _("Sign ons"), False)

    def get_description(self):
        return _("Clear Epiphany's cache, cookies, download list, places, and sign ons.")

    def get_id(self):
        return 'epiphany'

    def get_name(self):
        return "Epiphany"

    def list_files(self):
        files = []
        # browser cache
        if self.options["cache"][1]:
            dirs = glob.glob(os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/Cache/"))
            dirs += glob.glob(os.path.expanduser("~/.gnome2/epiphany/favicon_cache/"))
            for dirname in dirs:
                for filename in FileUtilities.children_in_directory(dirname, False):
                    yield filename
            files += [ os.path.expanduser("~/.gnome2/epiphany/ephy-favicon-cache.xml") ]

        # cookies
        if self.options["cookies"][1]:
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/cookies.txt") ]
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/cookies.sqlite") ]
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/cookies.sqlite-journal") ]

        # places database
        if self.options["places"][1]:
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/places.sqlite") ]
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/places.sqlite-journal") ]
            files += [ os.path.expanduser("~/.gnome2/epiphany/ephy-history.xml") ]

        # sign ons
        if self.options["signons"][1]:
            files += [ os.path.expanduser("~/.gnome2/epiphany/mozilla/epiphany/signons3.txt") ]

        for file in files:
            if os.path.exists(file):
                yield file


class Firefox(Cleaner):
    """Mozilla Firefox"""

    def __init__(self):
        self.options = {}
        self.options["cache"] = ( _("Cache"), False ) 
        self.options["cookies"] = ( _("Cookies"), False )
        self.options["download_history"] = ( _("Download history"), False)
        self.options["forms"] = ( _("Form history"), False)
        self.options["places"] = ( _("Places"), False)
        self.options["signons"] = ( _("Sign ons"), False)
        self.profile_dir = "~/.mozilla/firefox/*/"

    def get_description(self):
        return _("Clear Mozilla Firefox's cache, cookies, download list, forms, and places database.  The places database contains URLs including bookmarks and visited URLs.")

    def get_id(self):
        return 'firefox'

    def get_name(self):
        return "Firefox"

    def list_files(self):
        # browser cache
        if self.options["cache"][1]:
            dirs = glob.glob(os.path.expanduser(self.profile_dir + "/Cache/"))
            for dir in dirs:
                for file in FileUtilities.children_in_directory(dir, False):
                    yield file
        files = []
        # cookies
        if self.options["cookies"][1]:
            files += glob.glob(os.path.expanduser(self.profile_dir + "/cookies.txt"))
            files += glob.glob(os.path.expanduser(self.profile_dir + "/cookies.sqlite"))
        # download history
        if self.options["download_history"][1]:
            # Firefox version 1
            files += glob.glob(os.path.expanduser(self.profile_dir + "/downloads.rdf"))
            # Firefox version 3
            files += glob.glob(os.path.expanduser(self.profile_dir + "/downloads.sqlite"))
        # forms
        if self.options["forms"][1]:
            files += glob.glob(os.path.expanduser(self.profile_dir + "/formhistory.sqlite"))
            files += glob.glob(os.path.expanduser(self.profile_dir + "/formhistory.dat"))
        # places database
        if self.options["places"][1]:
            # Firefox version 1
            files += glob.glob(os.path.expanduser(self.profile_dir + "/history.dat"))
            # Firefox version 3
            files += glob.glob(os.path.expanduser(self.profile_dir + "/places.sqlite"))
            files += glob.glob(os.path.expanduser(self.profile_dir + "/places.sqlite-journal"))
        # sign ons
        if self.options["signons"][1]:
            files += glob.glob(os.path.expanduser(self.profile_dir + "/signons.txt"))
            files += glob.glob(os.path.expanduser(self.profile_dir + "/signons[2-3].txt"))
        for file in files:
            yield file

class Flash(Cleaner):
    """Adobe Flash"""

    def get_description(self):
        return _("Clear Adobe Flash's cache and settings")

    def get_id(self):
        return 'flash'

    def get_name(self):
        return "Flash"

    def list_files(self):
        dir = os.path.expanduser("~/.macromedia/Flash_Player/macromedia.com/support/flashplayer/sys")
        for file in FileUtilities.children_in_directory(dir, True):
            yield file


class System(Cleaner):
    """Freedesktop (XDG)"""

    def __init__(self):
        self.options = {}
        self.options["cache"] = ( _("Cache"), False ) 
        self.options["recent"] = ( _("Recent documents list"), False )

    def get_description(self):
        return _("Clear system cache and recently used documents.  These locations are specified by XDG specifications and are used by some applications on modern Linux systems.")

    def get_id(self):
        return 'system'

    def get_name(self):
        return _("System")

    def list_files(self):
        # cache
        if self.options["cache"][1]:
            dir = os.path.expanduser("~/.cache/")
            for file in FileUtilities.children_in_directory(dir, True):
                yield file

        # most recently used documents list
        files = []
        if self.options["recent"][1]:
            files += [ os.path.expanduser("~/.recently-used") ]

        # fixme http://www.freedesktop.org/wiki/Specifications/desktop-bookmark-spec
        for file in files:
            if os.path.exists(file):
                yield file



class Java(Cleaner):
    """Clear the Java cache"""

    def get_description(self):
        return _("Clear Java's cache")

    def get_id(self):
        return 'java'

    def get_name(self):
        return "Java"

    def list_files(self):
        dir = os.path.expanduser("~/.java/deployment/cache")
        for file in FileUtilities.children_in_directory(dir, False):
            yield file


class KDE(Cleaner):
    """KDE"""

    def __init__(self):
        self.options = {}
        self.options["cache"] = ( _("Cache"), False ) 
        self.options["tmp"] = ( _("Cookies"), False )

    def get_description(self):
        return _("Clear KDE cache and temporary directories.  These are shared by applications including Konqueror.")

    def get_id(self):
        return 'kde'

    def get_name(self):
        return "KDE"

    def list_files(self):
        # cache
        if self.options["cache"][1]:
            dirs = glob.glob(os.path.expanduser("~/.kde/cache-*/"))
            for dir in dirs:
                for file in FileUtilities.children_in_directory(dir, False):
                    yield file
        # temporary
        if self.options["tmp"][1]:
            dirs = glob.glob(os.path.expanduser("~/.kde/tmp-*/"))
            for dir in dirs:
                for file in FileUtilities.children_in_directory(dir, False):
                    yield file

class OpenOfficeOrg(Cleaner):
    """Clear OpenOffice.org cache"""

    def __init__(self):
        Cleaner.__init__(self)
        self.prefixes = [ "~/.ooo-2.0", "~/.openoffice.org2", "~/.openoffice.org2.0", "~/.openoffice.org/3" ]
        self.prefixes += [ "~/.ooo-dev3" ]

    def get_description(self):
        return _("Clear OpenOffice.org's registry cache and UNO package cache")

    def get_id(self):
        return 'openofficeorg'

    def get_name(self):
        return "OpenOffice.org"

    def list_files(self):
        # reference: http://katana.oooninja.com/w/editions_of_openoffice.org
        dirs = []
        for prefix in self.prefixes:
            dirs.append(os.path.join(os.path.expanduser(prefix), "user/uno_packages/cache/"))
            dirs.append(os.path.join(os.path.expanduser(prefix), "user/registry/cache/"))
        for dir in dirs:
            d = os.path.expanduser(dir)
            for file in FileUtilities.children_in_directory(d, False):
                yield file

    def erase_history(self, path):
        """Erase the history node (most recently used documents"""
        dom1 = xml.dom.minidom.parse(path)
        for node in dom1.getElementsByTagName("node"):
            if node.hasAttribute("oor:name"):
                if "History" == node.getAttribute("oor:name"):
                    node.parentNode.removeChild(node)
                    node.unlink()
                    break
        dom1.writexml(open(path, "w"))

    def other_cleanup(self):
        for prefix in self.prefixes:
            path = os.path.join(os.path.expanduser(prefix), "user/registry/data/org/openoffice/Office/Common.xcu")
            os.path.exists(path) and self.erase_history(path)


class Opera(Cleaner):
    """Opera"""

    def __init__(self):
        self.options = {}
        self.options["cache"] = ( _("Cache"), False ) 
        self.options["cookies"] = ( _("Cookies"), False )
        self.profile_dir = "~/.opera/"

    def get_description(self):
        return _("Clear Opera cache and cookies.")

    def get_id(self):
        return 'opera'

    def get_name(self):
        return "Opera"

    def list_files(self):
        # browser cache
        if self.options["cache"][1]:
            dir = os.path.expanduser(self.profile_dir + "cache4/")
            for file in FileUtilities.children_in_directory(dir, False):
                yield file

        files = []

        # cookies
        if self.options["cookies"][1]:
            files += [os.path.expanduser(self.profile_dir + "cookies4.dat")]

        for file in files:
            if os.path.exists(file):
                yield file


class realplayer(Cleaner):
    """RealPlayer by RealNetworks"""

    def get_description(self):
        return _("Clear the RealPlayer cookies")

    def get_id(self):
        return 'realplayer'

    def get_name(self):
        return "RealPlayer"

    def list_files(self):
        yield os.path.expanduser("~/.config/real/rpcookies.txt")



class rpmbuild(Cleaner):
    """Clear the rpmbuild build directory"""

    def get_description(self):
        return _("Clear the rpmbuild build directory")

    def get_id(self):
        return 'rpmbuild'

    def get_name(self):
        return "rpmbuild"

    def list_files(self):
        dir = os.path.expanduser("~/rpmbuild/BUILD/")
        for file in FileUtilities.children_in_directory(dir, True):
            yield file


class Thumbnails(Cleaner):
    """Clear the thumbnails folder"""

    def get_description(self):
        return _("Clear the thumbnails folder")

    def get_id(self):
        return 'thumbnails'

    def get_name(self):
        return "Thumbnails"

    def list_files(self):
        dir = os.path.expanduser("~/.thumbnails")
        for file in FileUtilities.children_in_directory(dir, False):
            yield file


class tmp(Cleaner):
    """Delete certain files in /tmp/"""

    def get_description(self):
        return _("Delete user-owned, unopened, regular files in /tmp/'")

    def get_id(self):
        return 'tmp'

    def get_name(self):
        return "tmp"

    def whitelisted(self, pathname):
        """Return boolean whether file is whitelisted"""
        regexes = ['/tmp/pulse-[^/]+/pid',
            '/tmp/gconfd-[^/]+/lock/ior',
            '/tmp/orbit-[^/]+/bonobo-activation-register.lock',
            '/tmp/orbit-[^/]+/bonobo-activation-server-ior',
            '/tmp/.X0-lock' ]
        for regex in regexes:
            if None != re.match(regex, pathname):
                return True
        return False


    def list_files(self):
        for pathname in FileUtilities.children_in_directory("/tmp/", True):
            is_open = FileUtilities.openfiles.is_open(pathname)
            ok = not is_open and os.path.isfile(pathname) and \
                not os.path.islink(pathname) and \
                FileUtilities.ego_owner(pathname) and \
                not self.whitelisted(pathname)
            if ok:
                yield pathname

class Trash(Cleaner):
    """Clear the trash folder"""

    def get_description(self):
        return _("Clear the trash folder")

    def get_id(self):
        return 'trash'

    def get_name(self):
        return "Trash"

    def list_files(self):
        dir = os.path.expanduser("~/.Trash")
        for file in FileUtilities.children_in_directory(dir, False):
            yield file
        # fixme http://www.ramendik.ru/docs/trashspec.html
        # http://standards.freedesktop.org/basedir-spec/basedir-spec-0.6.html
        # GNOME 2.22, Fedora 9 ~/.local/share/Trash
        dir = os.path.expanduser("~/.local/share/Trash")
        for file in FileUtilities.children_in_directory(dir, False):
            yield file


class XChat(Cleaner):
    """Clear XChat logs and scrollback"""

    def available(self):
        return True

    def get_id(self):
        return 'xchat'

    def get_description(self):
        return 'Clear XChat logs and scrollback'

    def get_name(self):
        return "XChat"

    def list_files(self):
        dirs = ["~/.xchat2/scrollback/", "~/.xchat2/logs/"]
        for dir in dirs:
            d = os.path.expanduser(dir)
            for file in FileUtilities.children_in_directory(d, False):
                yield file

backends = {}
backends["bash"] = Bash()
backends["beagle"] = Beagle()
backends["epiphany"] = Epihany()
backends["firefox"] = Firefox()
backends["flash"] = Flash()
backends["java"] = Java()
backends["kde"] = KDE()
backends["openofficeorg"] = OpenOfficeOrg()
backends["opera"] = Opera()
backends["realplayer"] = realplayer()
backends["rpmbuild"] = rpmbuild()
backends["system"] = System()
backends["thumbnails"] = Thumbnails()
backends["tmp"] = tmp()
backends["trash"] = Trash()
backends["xchat"] = XChat()


import unittest

class TestUtilities(unittest.TestCase):
    def test_get_name(self):
        for key in sorted(backends):
            for name in backends[key].get_name():
                self.assert_ (type(name) is str)

    def test_get_descrption(self):
        for key in sorted(backends):
            for desc in backends[key].get_description():
                self.assert_ (type(desc) is str)

    def test_get_options(self):
        for key in sorted(backends):
            for (id, name, value) in backends[key].get_options():
                self.assert_ (type(id) is str)
                self.assert_ (type(name) is str)
                self.assert_ (type(value) is bool)

    def test_list_files(self):
        for key in sorted(backends):
            print "debug: test_list_files: key='%s'" % (key, )
            for (cleaner_id, __name, __value) in backends[key].get_options():
                backends[key].set_option(cleaner_id, True)
            for file in backends[key].list_files():
                self.assert_ (type(file) is str)
                self.assert_ (os.path.exists(file), "In backend '%s' path does not exist: '%s' " % (key, file))


if __name__ == '__main__':
    unittest.main()

