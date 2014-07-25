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
import xml.dom.minidom
import os.path
import re


def locale_to_language(locale):
    """Convert the locale code to a language code (generally ISO 639)"""
    if 'klingon' == locale:
        return locale
    match = locale_to_language.pattern.match(locale)
    if match is None:
        raise ValueError("Invalid locale_code '%s'" % locale)
    return match.group(1)

locale_to_language.pattern = re.compile('^([a-z]{2,3})([_-][a-zA-Z]{2,4})?(\.[a-zA-Z0-9-]*)?(@[a-zA-Z]*)?$')


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
         'en_AU': 'Australian English',
         'en_GB': 'British English',
         'eo': 'Esperanto',
         'es': 'Español',
         'et': 'eesti',
         'fa': 'فارسی',
         'fi': 'suomen kieli',
         'fo': 'føroyskt',
         'fr': 'Français',
         'gl': 'galego',
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

    purgable_locales = []

    def __init__(self):
        pass

    def set_locales_to_keep(self, locales_to_keep):
        if not locales_to_keep:
            raise RuntimeError('Found no locales to keep')
        self.purgable_locales = frozenset((locale for locale in self.__native_locale_names.keys()
                                           if locale not in locales_to_keep))


def handle_path(path, xmldata):
    if xmldata.ELEMENT_NODE != xmldata.nodeType:
        return
    if 'path' != xmldata.nodeName:
        raise RuntimeError("Invalid node '%s', expected 'path'" % xmldata.nodeName)
    location = xmldata.getAttribute('location')
    if '' == location:
        raise RuntimeError("Path node without location attribute")
    path = path + location
    if not path.endswith('/'):
        path += '/'

    if not os.path.isdir(path):
        return

    userfilter = xmldata.getAttribute('filter')
    if not userfilter and not xmldata.hasChildNodes():
        userfilter = '*'

    if userfilter:
        if 1 != userfilter.count('*'):
            raise RuntimeError("Filter string '%s' must contain the placeholder * exactly once" % userfilter)
        (prefixlen, postfixlen) = [len(part) for part in userfilter.split('*')]
        postfixlen = -postfixlen if 0 != postfixlen else None

        for subpath in glob.iglob(path+userfilter):
            try:
                filename = os.path.split(subpath)[1]
                locale = locale_to_language(filename[prefixlen:postfixlen])
            except ValueError:
                continue
            yield (locale, subpath)

    for child in xmldata.childNodes:
        for subpath in handle_path(path, child):
            yield subpath


infile = xml.dom.minidom.parse('test.xml')
for c in infile.childNodes[0].childNodes:
    for p in handle_path('', c):
        print p