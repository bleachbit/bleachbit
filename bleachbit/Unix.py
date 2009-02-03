# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Integration specific to Unix-like operating systems
"""


import glob
import os
import re
import ConfigParser

import FileUtilities

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
    matches = re.findall("^([a-z]{2,3})([_-][a-zA-Z]{2,4})?(\.[a-zA-Z0-9-]*)?(@[a-zA-Z]*)?$", locale)
    if 1 > len(matches):
        raise ValueError("Invalid locale_code '%s'" % (locale,))
    return matches[0][0]


class Locales:
    """Find languages and localization files"""

    __native_locale_names = \
    { 'ar' : 'العربية', \
        'bg' : 'български език', \
        'bn' : 'বাংলা', \
        'cs' : 'česky', \
        'da' : 'dansk', \
        'de' : 'Deutsch', \
        'el' : 'Ελληνικά', \
        'en' : 'English', \
        'es' : 'Español', \
        'fi' : 'suomen kieli', \
        'fr' : 'Français', \
        'hi' : 'हिन्दी', \
        'hr' : 'Hrvatski', \
        'hu' : 'Magyar', \
        'it' : 'Italiano', \
        'iw' : 'עברית', \
        'ja' : '日本語', \
        'jv' : 'basa Jawa', \
        'ko' : '한국어', \
        'mr' : 'मराठी', \
        'nl' : 'Nederlands', \
        'no' : 'Norsk', \
        'pl' : 'polski', \
        'pt' : 'Português', \
        'ro' : 'română', \
        'ru' : 'Pусский', \
        'sk' : 'slovenčina', \
        'sv' : 'svenska', \
        'tr' : 'Türkçe', \
        'uk' : 'Українська', \
        'vi' : 'Tiếng Việt', \
        'zh' : '中文' }

    __basedirs = [ os.path.expanduser('~/.local/share/locale/'),
                '/usr/local/share/locale/',
                '/usr/share/apps/ksgmltools2/customization/',
                '/usr/share/doc/kde/HTML/',
                '/usr/share/doc/HTML/release-notes/', # Fedora 10
                '/usr/share/doc/thunar-data/html',
                '/usr/share/gnucash/accounts',
                '/usr/share/kde4/apps/ksgmltools2/customization',
                '/usr/share/locale/',
                '/usr/share/speedcrunch/books/' ] 

    __ignore = ['all_languages', 'C', 'l10n', 'locale.alias', 'default']


    def __init__(self):
        self.__languages = []
        if os.path.exists('/usr/share/gnome/help'):
            for gapp in os.listdir('/usr/share/gnome/help'):
                if 'libs' == gapp:
                    continue
                dirname = os.path.join('/usr/share/gnome/help', gapp)
                self.__basedirs.append(dirname)


        ooosharedirs = [ '/usr/lib/openoffice/share/', # Ubuntu 8
            '/usr/lib/openoffice.org/basis3.0/share/', # Fedora 10
            '/opt/ooo-dev/basis3.0/share', # Sun development snapshot
            '/opt/openoffice.org/basis3.0/share/' ] # Sun

        for ooosharedir in ooosharedirs:
            suffixes = [ 'autotext/',
                'config/soffice.cfg/global/accelerator/',
                'registry/res/',
                'samples/',
                'template/',
                'template/wizard/letter/',
                'wordbook/' ]
            for suffix in suffixes:
                ooodir = os.path.join(ooosharedir, suffix)
                if os.path.exists(ooodir):
                    self.__basedirs.append(ooodir)
            ooomodules = os.path.join(ooosharedir, 'config/soffice.cfg/modules')
            if os.path.exists(ooomodules):
                for ooomodule in os.listdir(ooomodules):
                    dirname = os.path.join(ooomodules, ooomodule + '/accelerator/')
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
                print "Warning: invalid path '%s' where expecting a locale" % locale
                continue
            if not lang in self.__languages:
                self.__languages.append(lang)
        self.__languages = sorted(self.__languages)
        self.__scanned = True


    def iterate_languages(self):
        """Return each language code (generally ISO 639)"""
        if False == self.__scanned:
            self.__scan()
        for lang in self.__languages:
            yield lang


    def __localization_path(self, basedir, language_filter, dir_filter):
        """Return localization paths in a single directory tree"""
        if not os.path.exists(basedir):
            return
        for path in os.listdir(basedir):
            if None != dir_filter and dir_filter(path):
                continue
            locale_code = path
            try:
                language_code = locale_to_language(path)
            except:
                 print "Warning: invalid path '%s' where expecting a locale" % path
                 continue
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            locale_dirname = os.path.join(basedir, locale_code)
            for path in FileUtilities.children_in_directory(locale_dirname, True):
                yield path
            yield locale_dirname


    def localization_paths(self, language_filter):
        """Return paths containing localization files"""

        # general
        for basedir in self.__basedirs:
            dir_filter = lambda d: d in self.__ignore
            for path in self.__localization_path(basedir, language_filter, dir_filter):
                yield path

        # CUPS
        # example: /usr/share/cups/templates/es/jobs.tmpl
        dir_filter = lambda d: d.endswith('tmpl')
        for path in self.__localization_path('/usr/share/cups/templates/', language_filter, dir_filter):
            yield path
        # Fedora 10
        #   example: /usr/share/cups/www/es/images/button-add-printer.gif
        dir_filter = lambda d: d in ['cups.css', 'cups-printable.css', 'favicon.ico', 'help', 'images', 'index.html', 'robots.txt']
        for path in self.__localization_path('/usr/share/cups/www/', language_filter, dir_filter):
            yield path
        # Ubuntu 8.10
        #   example: /usr/share/cups/doc-root/es/images/button-add-printer.gif
        for path in self.__localization_path('/usr/share/cups/doc-root/', language_filter, dir_filter):
            yield path

        # foomatic
        dir_filter = lambda d: 2 != len(d)
        for path in self.__localization_path('/usr/share/foomatic/db/source/PPD/Kyocera/', language_filter, dir_filter):
            yield path

        # glibc-common
        # example: /usr/share/i18n/locales/es_ES@euro
        for path in glob.iglob('/usr/share/i18n/locales/*_*'):
            locale_code = os.path.basename(path)
            if locale_code.startswith('iso14') or locale_code.startswith('translit'):
                continue
            language_code = locale_to_language(locale_code)
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            yield path

        # man pages
        # example: /usr/share/man/es/man1/man.1.gz
        dir_filter = lambda d: d.startswith('man')
        for path in self.__localization_path('/usr/share/man/', language_filter, dir_filter):
            yield path

        # OMF
        # example: /usr/share/omf/gedit/gedit-es.omf
        for path in glob.iglob('/usr/share/omf/*/*-*.omf'):
            locale_code = path[path.rfind("-") + 1 : path.rfind(".") ]
            if 'C' == locale_code:
                continue
            try:
                language_code = locale_to_language(locale_code)
            except:
                print "Warning: OMF path '%s' does not look like a locale" % path
                continue
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            yield path

        # TCL
        # example: /usr/share/tcl8.5/msgs/es_mx.msg
        for path in glob.glob('/usr/share/tcl*/msgs/*.msg'): 
            locale_code = os.path.splitext(os.path.basename(path))[0]
            language_code = locale_to_language(locale_code)
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            yield path


    def native_name(self, language_code):
        """Return the name of the language in its own language"""
        if language_code in self.__native_locale_names:
            return self.__native_locale_names[language_code]
        if os.path.exists('/usr/share/locale/all_languages'):
            if not self.__config_read:
                self.__config.read('/usr/share/locale/all_languages')
                self.__config_read = True
            option = 'Name[%s]' % (language_code, )
            if self.__config.has_option(language_code, option):
                value = self.__config.get(language_code, option)
                # cache
                self.__native_locale_names[language_code] = value
                return value
        return None


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
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program Files\\foo\\foo.exe"
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


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":", \
        "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\","/")
    return os.path.join(wineprefix, windows_pathname)


locales = Locales()


import unittest

class TestUnix(unittest.TestCase):
    """Unit tests for module Unix"""

    def setUp(self):
        """Initialize unit tests"""
        self.locales = Locales()


    def test_is_broken_xdg_desktop(self):
        """Unit test for is_broken_xdg_desktop()"""
        menu_dirs = [ '/usr/share/applications', \
            '/usr/share/autostart', \
            '/usr/share/gnome/autostart', \
            '/usr/share/gnome/apps', \
            '/usr/share/mimelnk', \
            '/usr/share/applnk-redhat/', \
            '/usr/local/share/applications/' ]
        for dirname in menu_dirs:
            for filename in [fn for fn in FileUtilities.children_in_directory(dirname, False) \
                if fn.endswith('.desktop')]:
                self.assert_(type(is_broken_xdg_desktop(filename) is bool))


    def iterate_languages(self):
        """Unit test for the method iterate_languages()"""
        for language in self.locales.iterate_languages():
            self.assert_(type(language) is str)
            self.assert_(len(str) > 0)
            self.assert_(len(str) < 9)


    def test_locale_to_language(self):
        """Test method locale_to_language()"""
        tests = [ ('en', 'en'),
            ('en_US', 'en'),
            ('en_US@piglatin', 'en'),
            ('en_US.utf8', 'en'),
            ('klingon', 'klingon'),
            ('pl.ISO8859-2', 'pl'),
            ('sr_Latn', 'sr'),
            ('zh_TW.Big5', 'zh') ]
        for test in tests:
            self.assertEqual(locale_to_language(test[0]), test[1])

        self.assertRaises(ValueError, locale_to_language, 'default')
        self.assertRaises(ValueError, locale_to_language, 'C')
        self.assertRaises(ValueError, locale_to_language, 'English')


    def test_localization_paths(self):
        """Test method localization_paths()"""
        for path in locales.localization_paths(lambda x, y: False):
            self.assert_(os.path.lexists(path))


    def test_native_name(self):
        """Test method native_name()"""
        tests = [ ('en', 'English'),
            ('es', 'Español') ]
        for test in tests:
            self.assertEqual(self.locales.native_name(test[0]), test[1])


    def test_wine_to_linux_path(self):
        """Unit test for wine_to_linux_path()"""
        tests = [ ("/home/foo/.wine", \
            "C:\\Program Files\\NSIS\\NSIS.exe", \
            "/home/foo/.wine/drive_c/Program Files/NSIS/NSIS.exe") ]
        for test in tests:
            self.assertEqual(wine_to_linux_path(test[0], test[1]), test[2])


if __name__ == '__main__':
    unittest.main()

