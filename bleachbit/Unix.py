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

import FileUtilities

class Locales:

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
                '/usr/share/locale/' ]

    __ignore = ['all_languages', 'C', 'l10n', 'locale.alias', 'default']


    def __init__(self):
        self.__languages = []
        if os.path.exists('/usr/share/gnome/help'):
            for gapp in os.listdir('/usr/share/gnome/help'):
                dirname = os.path.join('/usr/share/gnome/help', gapp)
                self.__basedirs.append(dirname)
        self.__scan()
        pass


    def __scan(self):
        locales = []
        for basedir in self.__basedirs:
            if os.path.exists(basedir):
                locales += os.listdir(basedir)
        for locale in locales:
            if locale in self.__ignore:
                continue
            lang = self.language_code(locale)
            if not lang in self.__languages:
                self.__languages.append(lang)
        self.__languages = sorted(self.__languages)


    def language_code(self, locale):
        """Convert the locale code to a language code"""
        if 'klingon' == locale:
            return locale
        matches = re.findall("^([a-z]{2,3})([_-][a-zA-Z]{2,4})?(\.[a-zA-Z0-9-]*)?(@[a-zA-Z]*)?$", locale)
        if 1 > len(matches):
            raise ValueError("Invalid locale_code '%s'" % (locale,))
        return matches[0][0]


    def iterate_languages(self):
        """Return each language code"""
        for lang in self.__languages:
            yield lang


    def __localization_path(self, basedir, language_filter, dir_filter):
        """Process a single directory tree"""
        for path in os.listdir(basedir):
            if None != dir_filter and dir_filter(path):
                continue
            locale_code = path
            language_code = self.language_code(path)
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
        # example: /usr/share/cups/www/es/images/button-add-printer.gif
        dir_filter = lambda d: d in ['cups.css', 'cups-printable.css', 'favicon.ico', 'help', 'images', 'index.html', 'robots.txt']
        for path in self.__localization_path('/usr/share/cups/www/', language_filter, dir_filter):
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
            language_code = self.language_code(locale_code)
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
            language_code = self.language_code(locale_code)
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            yield path

        # TCL
        # example: /usr/share/tcl8.5/msgs/es_mx.msg
        for path in glob.glob('/usr/share/tcl*/msgs/*.msg'): 
            locale_code = os.path.splitext(os.path.basename(path))[0]
            language_code = self.language_code(locale_code)
            if None != language_filter and language_filter(locale_code, language_code):
                continue
            yield path




    def native_name(self, language_code):
        if language_code in self.__native_locale_names:
            return self.__native_locale_names[language_code]
        return None


locales = Locales()


import unittest

class TestLocales(unittest.TestCase):
    """Unit tests for class Locale"""

    def setUp(self):
        """Initialize"""
        self.locales = Locales()


    def iterate_languages(self):
        for language in self.locales.iterate_languages():
            self.assert_(type(language) is str)

    def test_language_code(self):
        """Test method language_code()"""
        tests = [ ('en', 'en'),
            ('en_US', 'en'),
            ('en_US@piglatin', 'en'),
            ('en_US.utf8', 'en'),
            ('klingon', 'klingon'),
            ('pl.ISO8859-2', 'pl'),
            ('sr_Latn', 'sr'),
            ('zh_TW.Big5', 'zh') ]
        for test in tests:
            self.assertEqual(self.locales.language_code(test[0]), test[1])

        self.assertRaises(ValueError, self.locales.language_code, 'default')
        self.assertRaises(ValueError, self.locales.language_code, 'C')
        self.assertRaises(ValueError, self.locales.language_code, 'English')


    def test_localization_paths(self):
        """Test method localization_paths()"""
        for path in locales.localization_paths(lambda x, y: False):
            print "debug: ", path


    def test_native_name(self):
        """Test method native_name()"""
        tests = [ ('en', 'English'),
            ('es', 'Español') ]
        for test in tests:
            self.assertEqual(self.locales.native_name(test[0]), test[1])


if __name__ == '__main__':
    unittest.main()

