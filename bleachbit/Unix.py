# vim: ts=4:sw=4:expandtab
# -*- coding: UTF8 -*-

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


import os
import re


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


    def __init__(self):
        self.__languages = []
        self.__scan()
        pass


    def __scan(self):
        locales = os.listdir('/usr/share/locale')
        try:
            locales += os.listdir(os.path.expanduser('~/.local/share/locale/'))
        except:
            pass
        for locale in locales:
            if locale in ['all_languages', 'C', 'l10n', 'locale.alias']:
                continue
            lang = self.language_code(locale)
            if not lang in self.__languages:
                self.__languages.append(lang)
        self.__languages = sorted(self.__languages)


    def language_code(self, locale):
        """Convert the locale code to a language code"""
        matches = re.findall("^([a-z]{2,3})", locale)
        if 1 != len(matches):
            raise ValueError("Invalid locale_code '%s'" % (locale))
        return matches[0]


    def iterate_languages(self):
        """Return each language"""
        for lang in self.__languages:
            yield lang


    def native_name(self, language_code):
        if language_code in self.__native_locale_names:
            return self.__native_locale_names[language_code]
        return None


import unittest

class TestLocales(unittest.TestCase):
    """Unit tests for class Locale"""

    def setUp(self):
        """Initialize"""
        self.locales = Locales()


    def test_language_code(self):
        """Test method language_code()"""
        tests = [ ('en', 'en'),
            ('en_US', 'en'),
            ('en_US@piglatin', 'en'),
            ('en_US.utf8', 'en') ]
        for test in tests:
            self.assertEqual(self.locales.language_code(test[0]), test[1])


    def test_native_name(self):
        """Test method native_name()"""
        tests = [ ('en', 'English'),
            ('es', 'Español') ]
        for test in tests:
            self.assertEqual(self.locales.native_name(test[0]), test[1])


if __name__ == '__main__':
    unittest.main()

