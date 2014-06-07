# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Integration specific to Unix-like operating systems
"""


import glob
import os
import re
import shlex
import subprocess
import ConfigParser

from Common import _, autostart_path, launcher_path
import FileUtilities
import General

HAVE_GNOME_VFS = True
try:
    import gnomevfs
except:
    try:
        # this is the deprecated name
        import gnome.vfs
    except:
        HAVE_GNOME_VFS = False
    else:
        gnomevfs = gnome.vfs


def locale_to_language(locale):
    """Convert the locale code to a language code (generally ISO 639)"""
    if 'klingon' == locale:
        return locale
    pattern = "^([a-z]{2,3})([_-][a-zA-Z]{2,4})?(\.[a-zA-Z0-9-]*)?(@[a-zA-Z]*)?$"
    matches = re.findall(pattern, locale)
    if 1 > len(matches):
        raise ValueError("Invalid locale_code '%s'" % (locale,))
    return matches[0][0]


def locale_globex(globpath, regex):
    """List a path by glob, filter by regex, and return tuple
    in format (locale, pathname)"""
    for pathname in FileUtilities.globex(globpath, regex):
        match = re.search(regex, pathname)
        if None == match:
            continue
        locale_code = match.groups(0)[0]
        yield (locale_code, pathname)


class Locales:

    """Find languages and localization files"""

    __native_locale_names = \
        {'ar': 'العربية',
         'ast': 'Asturianu',
         'be': 'Беларуская мова',
         'bg': 'български език',
         'bn': 'বাংলা',
         'bs': 'босански',
         'ca': 'català',
         'cs': 'česky',
         'da': 'dansk',
         'de': 'Deutsch',
         'el': 'Ελληνικά',
         'en': 'English',
         'en_AU' : 'Australian English',
         'en_GB' : 'British English',
         'eo' : 'Esperanto',
         'es': 'Español',
         'et' : 'eesti',
         'fa' : 'فارسی',
         'fi': 'suomen kieli',
         'fo': 'føroyskt',
         'fr': 'Français',
         'gl' : 'galego',
         'he': 'עברית',
         'hi': 'हिन्दी',
         'hr': 'Hrvatski',
         'hu': 'Magyar',
         'hy': 'Հայերեն',
         'ia': 'Interlingua',
         'id': 'Indonesian',
         'it': 'Italiano',
         'iw': 'עברית',
         'ku': 'Kurdî',
         'ky': 'Кыргызча',
         'ja': '日本語',
         'jv': 'basa Jawa',
         'lt': 'lietuvių kalba',
         'ko': '한국어',
         'mr': 'मराठी',
         'ms': 'بهاس ملايو',
         'my': 'ဗမာစာ',
         'nb': 'Bokmål',
         'nds': 'Plattdüütsch',
         'nl': 'Nederlands',
         'no': 'Norsk',
         'pl': 'polski',
         'pt': 'Português',
         'ro': 'română',
         'ru': 'Pусский',
         'sk': 'slovenčina',
         'sl': 'slovenščina',
         'sr': 'Српски',
         'sv': 'svenska',
         'tr': 'Türkçe',
         'ug': 'Uyghur',
         'uk': 'Українська',
         'vi': 'Tiếng Việt',
         'zh': '中文'}

    __basedirs = [os.path.expanduser('~/.local/share/locale/'),
                  '/usr/local/share/locale/',
                  '/usr/share/apps/ksgmltools2/customization/',
                  '/usr/share/calendar',  # Ubuntu 8.10
                  '/usr/share/cups/locale',  # Ubuntu 8.10
                  '/usr/share/doc/kde/HTML/',
                  '/usr/share/doc/HTML/release-notes/',  # Fedora 10
                  '/usr/share/doc/thunar-data/html',
                  '/usr/share/gnucash/accounts',
                  '/usr/share/locale/',
                  '/usr/share/speedcrunch/books/',
                  '/usr/share/vim/vim72/'  # Ubuntu 10.10
                  ]

    __ignore = ['all_languages', 'C', 'l10n', 'locale.alias', 'default']

    ooosharedirs = ['/usr/lib/openoffice/share/',  # Ubuntu 8
                    '/usr/lib/openoffice/basis3.2/share/',  # Ubuntu 10.10
                    '/usr/lib/openoffice.org/basis3.0/share/',  # Fedora 10
                    '/opt/ooo-dev/basis3.0/share',  # Sun development snapshot
                    '/opt/openoffice.org/basis3.0/share/']  # Sun

    def __init__(self):
        self.__languages = []
        if os.path.exists('/usr/share/gnome/help'):
            for gapp in os.listdir('/usr/share/gnome/help'):
                if 'libs' == gapp:
                    continue
                dirname = os.path.join('/usr/share/gnome/help', gapp)
                self.__basedirs.append(dirname)

        for ooosharedir in self.ooosharedirs:
            suffixes = ['autotext/',
                        'config/soffice.cfg/global/accelerator/',
                        'registry/res/',
                        'samples/',
                        'template/',
                        'template/wizard/letter/',
                        'wordbook/']
            for suffix in suffixes:
                ooodir = os.path.join(ooosharedir, suffix)
                if os.path.exists(ooodir):
                    self.__basedirs.append(ooodir)
            ooomodules = os.path.join(
                ooosharedir, 'config/soffice.cfg/modules')
            if os.path.exists(ooomodules):
                for ooomodule in os.listdir(ooomodules):
                    dirname = os.path.join(
                        ooomodules, ooomodule + '/accelerator/')
                    self.__basedirs.append(dirname)

        self.__scanned = False
        self.__config = ConfigParser.RawConfigParser()
        self.__config_read = False

    def __scan(self):
        """Create a list of languages"""
        _locales = []
        for basedir in self.__basedirs:
            if os.path.exists(basedir):
                _locales += os.listdir(basedir)
        for locale in _locales:
            if locale in self.__ignore:
                continue
            try:
                lang = locale_to_language(locale)
            except:
                continue
            if not lang in self.__languages:
                self.__languages.append(lang)
        import Options
        selected_languages = Options.options.get_languages()
        if None != selected_languages:
            self.__languages += selected_languages
        self.__languages = sorted(set(self.__languages))
        self.__scanned = True

    def iterate_languages(self):
        """Return each language code (generally ISO 639)"""
        if not self.__scanned:
            self.__scan()
        for lang in self.__languages:
            yield lang

    def __localization_path(self, basedir, language_filter, dir_filter):
        """Return localization paths in a single directory tree"""
        if -1 != basedir.find('*'):
            for basedir2 in glob.iglob(basedir):
                for path in self.__localization_path(basedir2, language_filter, dir_filter):
                    yield path
            return
        if not os.path.exists(basedir):
            return
        for path in os.listdir(basedir):
            if None != dir_filter and dir_filter(path):
                continue
            locale_code = path
            try:
                language_code = locale_to_language(path)
            except:
                continue
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            locale_dirname = os.path.join(basedir, locale_code)
            for path in FileUtilities.children_in_directory(locale_dirname, True):
                yield path
            yield locale_dirname

    def localization_paths(self, language_filter):
        """Return paths containing localization files"""

        #
        # general
        #
        for basedir in self.__basedirs:
            dir_filter = lambda d: d in self.__ignore
            for path in self.__localization_path(basedir, language_filter, dir_filter):
                yield path

        #
        # the locale is the directory name
        #

        lps = []

        # CUPS, Fedora 10
        # /usr/share/cups/templates/es/jobs.tmpl
        lps += (('/usr/share/cups/templates/', lambda d: d.endswith('tmpl')), )

        # CUPS, Fedora 10
        # /usr/share/cups/www/es/images/button-add-printer.gif
        dir_filter = lambda d: d in ['cups.css', 'cups-printable.css',
                                     'favicon.ico', 'help', 'images', 'index.html', 'robots.txt']
        lps += (('/usr/share/cups/www/', dir_filter), )

        # CUPS, Ubuntu 8.10
        # /usr/share/cups/doc-root/es/images/button-add-printer.gif
        lps += (('/usr/share/cups/doc-root/', dir_filter), )

        # evolution
        # /usr/share/evolution/2.22/help/quickref/es/quickref.pdf
        lps += (('/usr/share/evolution/*/help/quickref/', dir_filter), )

        # Evolution, Ubuntu 10.10
        # /usr/share/evolution/2.30/default/es/mail
        lps += (('/usr/share/evolution/*.*/default/', dir_filter), )

        # foomatic
        dir_filter = lambda d: 2 != len(d)
        lps += (('/usr/share/foomatic/db/source/PPD/Kyocera/', dir_filter), )

        # man pages
        # /usr/share/man/es/man1/man.1.gz
        dir_filter = lambda d: d.startswith('man')
        lps += (('/usr/share/man/', dir_filter), )

        # process lps
        for lp in lps:
            for path in self.__localization_path(lp[0], language_filter, lp[1]):
                yield path

        #
        # locale_globex
        #
        globexs = []

        # /usr/share/i18n/locales/es_ES@euro
        globexs += (
            ('/usr/share/i18n/locales/??_*', 'locales/([a-z]{2}_[A-Z]{2})'), )
        # /usr/share/aptitude/aptitude-defaults.es
        globexs += (
            ('/usr/share/aptitude/aptitude-defaults*', '-defaults.([a-z]{2})'), )
        # /usr/share/ppd/splix/samsung/ml1740fr.ppd
        globexs += (('/usr/share/ppd/splix/*/*fr.ppd', '(fr).ppd$'), )
        # /usr/share/espeak-data/es_dict
        globexs += (
            ('/usr/share/espeak-data/*_dict', '/([a-z]{2,3})_dict$'), )
        # /usr/share/espeak-data/voices/en/en-n
        globexs += (
            ('/usr/share/espeak-data/voices/en/*', '/(en)-?[a-z]{0,2}$'), )
        # /usr/share/espeak-data/voices/es-la
        globexs += (
            ('/usr/share/espeak-data/voices/*', '/([a-z]{2,3}(-[a-z]{2})?)$'), )
        # /usr/share/espeak-data/voices/mb/mb-ro1-en, do not match mb-us*
        globexs += (
            ('/usr/share/espeak-data/voices/mb/mb-*', '/mb-([a-tv-z][a-z])[0-9](-[a-z]{2,3})?$'), )
        # /usr/share/hplip/data/localization/hplip_es.qm
        globexs += (
            ('/usr/share/hplip/data/localization/hplip_??.qm', '_([a-z]{2}).qm$'), )
        # /usr/share/myspell/dicts/hyph_es_ES.dic
        globexs += (
            ('/usr/share/myspell/dicts/hyph_??_??.dic', '([a-z]{2}_[A-Z]{2}).dic$'), )
        # /usr/share/omf/gedit/gedit-es.omf
        globexs += (('/usr/share/omf/*/*-*.omf', '-([a-z]{2}).omf$'), )
        # OpenOffice.org
        # /usr/lib/openoffice/share/autocorr/acor_es-ES.dat
        for ooosharedir in self.ooosharedirs:
            globexs += (
                (ooosharedir + '/autocorr/acor_*.dat', 'acor_([a-z]{2}(-[A-Z]{2})?).dat$'), )
        # TCL on Fedora 10a
        # /usr/share/tcl8.5/msgs/es.msg
        # /usr/share/tcl8.5/msgs/es_mx.msg
        globexs += (
            ('/usr/share/tcl*/msgs/?*.msg', '/([a-z]{2}(_[a-z]{2})?).msg$'), )

        # process reglobs
        for (globpath, regex) in globexs:
            for (locale_code, path) in locale_globex(globpath, regex):
                language_code = locale_to_language(locale_code)
                if 'mb' == language_code:  # not a real code but found in espeak Ubuntu 9.04
                    continue
                if None != language_filter and language_filter(locale_code, language_code):
                    continue
                yield path

    def native_name(self, language_code):
        """Return the name of the language in its own language"""
        if language_code in self.__native_locale_names:
            return self.__native_locale_names[language_code]
        if os.path.exists('/usr/share/locale/all_languages'):
            if not self.__config_read:
                # In Fedora 15, this file is provided by kdelibs-common
                self.__config.read('/usr/share/locale/all_languages')
                self.__config_read = True
            option = 'Name[%s]' % (language_code, )
            if self.__config.has_option(language_code, option):
                value = self.__config.get(language_code, option)
                # cache
                self.__native_locale_names[language_code] = value
                return value
        return None


def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', 'autoclean']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # Del cups-common 1.3.9-17ubuntu3 [1165kB]
        match = re.search("^Del .*\[([0-9.]+[a-zA-Z]{2})\]", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', '--yes', 'autoremove']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # After this operation, 74.7MB disk space will be freed.
        match = re.search(
            ", ([0-9.]+[a-zA-Z]{2}) disk space will be freed", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def __is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns boolean whether application deskop entry file is broken"""
    if not config.has_option('Desktop Entry', 'Exec'):
        print "info: is_broken_xdg_menu: missing required option 'Exec': '%s'" \
            % (desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not FileUtilities.exe_exists(exe):
        print "info: is_broken_xdg_menu: executable '%s' does not exist '%s'" \
            % (exe, desktop_pathname)
        return True
    if 'env' == exe:
        # Wine v1.0 creates .desktop files like this
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program
        # Files\\foo\\foo.exe"
        execs = shlex.split(config.get('Desktop Entry', 'Exec'))
        wineprefix = None
        del(execs[0])
        while True:
            if 0 <= execs[0].find("="):
                (name, value) = execs[0].split("=")
                if 'WINEPREFIX' == name:
                    wineprefix = value
                del(execs[0])
            else:
                break
        if not FileUtilities.exe_exists(execs[0]):
            print "info: is_broken_xdg_menu: executable '%s'" \
                "does not exist '%s'" % (execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                print "info: is_broken_xdg_menu: Windows executable" \
                    "'%s' does not exist '%s'" % \
                    (windows_exe, desktop_pathname)
                return True
    return False


def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = ConfigParser.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        print "info: is_broken_xdg_menu: missing required section " \
            "'Desktop Entry': '%s'" % (pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        print "info: is_broken_xdg_menu: missing required option 'Type': '%s'" % (pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
                not config.has_option('Desktop Entry', 'URL[$e]'):
            print "info: is_broken_xdg_menu: missing required option 'URL': '%s'" % (pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            print "info: is_broken_xdg_menu: missing required option 'MimeType': '%s'" % (pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if HAVE_GNOME_VFS and 0 == len(gnomevfs.mime_get_all_applications(mimetype)):
            print "info: is_broken_xdg_menu: MimeType '%s' not " \
                "registered '%s'" % (mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        print "Warning: unhandled type '%s': file '%s'" % (file_type, pathname)
        return False
    if __is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def is_running(exename):
    """Check whether exename is running"""
    for filename in glob.iglob("/proc/*/exe"):
        try:
            target = os.path.realpath(filename)
        except TypeError:
            # happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            continue
        except OSError:
            # 13 = permission denied
            continue
        if exename == os.path.basename(target):
            return True
    return False


def rotated_logs():
    """Yield a list of rotated (i.e., old) logs in /var/log/"""
    # Ubuntu 9.04
    # /var/log/dmesg.0
    # /var/log/dmesg.1.gz
    # Fedora 10
    # /var/log/messages-20090118
    globpaths = ('/var/log/*.[0-9]',
                 '/var/log/*/*.[0-9]',
                 '/var/log/*.gz',
                 '/var/log/*/*gz',
                 '/var/log/*/*.old',
                 '/var/log/*.old')
    for globpath in globpaths:
        for path in glob.iglob(globpath):
            yield path
    regex = '-[0-9]{8}$'
    globpaths = ('/var/log/*-*', '/var/log/*/*-*')
    for path in FileUtilities.globex(globpaths, regex):
        whitelist_re = '^/var/log/(removed_)?(packages|scripts)'
        if None == re.match(whitelist_re, path):  # for Slackware, Launchpad #367575
            yield path


def start_with_computer(enabled):
    """If enabled, create shortcut to start application with computer.
    If disabled, then delete the shortcut."""
    if not enabled:
        if os.path.lexists(autostart_path):
            FileUtilities.delete(autostart_path)
        return
    if os.path.lexists(autostart_path):
        return
    import shutil
    General.makedirs(os.path.dirname(autostart_path))
    shutil.copy(launcher_path, autostart_path)
    os.chmod(autostart_path, 0755)
    if General.sudo_mode():
        General.chownself(autostart_path)


def start_with_computer_check():
    """Return boolean whether BleachBit will start with the computer"""
    return os.path.lexists(autostart_path)


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":",
                                                "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\", "/")
    return os.path.join(wineprefix, windows_pathname)


def yum_clean():
    """Run 'yum clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/yum.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Yum"
        raise RuntimeError(msg)
    if not FileUtilities.exe_exists('yum'):
        raise RuntimeError(_('Executable not found: %s') % 'yum')
    old_size = FileUtilities.getsizedir('/var/cache/yum')
    args = ['yum', "--enablerepo=*", 'clean', 'all']
    p = subprocess.Popen(args, stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    non_blank_line = ""
    while True:
        line = p.stdout.readline().replace("\n", "")
        if len(line) > 2:
            non_blank_line = line
        if -1 != line.find('You need to be root'):
            # Seen before Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Cannot remove rpmdb file'):
            # Since first in Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Another app is currently holding'):
            print "debug: yum: '%s'" % line
            old_size = FileUtilities.getsizedir('/var/cache/yum')
        if "" == line and p.poll() != None:
            break
    print 'debug: yum process return code = %d' % p.returncode
    if p.returncode > 0:
        raise RuntimeError(non_blank_line)
    new_size = FileUtilities.getsizedir('/var/cache/yum')
    return old_size - new_size


locales = Locales()
