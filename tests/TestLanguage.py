# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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


from bleachbit.Language import get_active_language_code,\
    get_supported_language_codes, \
    get_text, \
    native_locale_names, \
    setup_translation
from bleachbit.Options import options
from tests import common


class LanguageTestCase(common.BleachbitTestCase):

    """Test case for module Language"""

    def setUp(self):
        super(LanguageTestCase, self).setUp()
        options.set('auto_detect_lang', False)
        options.set('forced_language', '')

    def test_get_active_language_code(self):
        """Test get_active_language_code()"""
        lang_id = get_active_language_code()
        self.assertIsInstance(lang_id, str)
        self.assertTrue(lang_id in native_locale_names)
        self.assertTrue(lang_id in get_supported_language_codes())

    def test_get_supported_language_codes(self):
        """Test get_supported_language_codes()"""
        slangs = get_supported_language_codes()
        self.assertTrue(isinstance(slangs, list))
        self.assertTrue(len(slangs) > 1)
        for slang in slangs:
            self.assertIsInstance(slang, str)
            self.assertTrue(slang in native_locale_names)
        self.assertTrue('en_US' in slangs)
        self.assertTrue('es' in slangs)

    def test_switch_language_twice(self):
        """English should still work after switching twice"""
        
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        setup_translation()
        self.assertEqual(get_text('Preview'), 'Preview')

        options.set('auto_detect_lang', False)
        options.set('forced_language', 'es')
        setup_translation()
        self.assertEqual(get_text('Preview'), 'Vista previa')

        options.set('forced_language', 'en')
        setup_translation()
        self.assertEqual(get_text('Preview'), 'Preview')

    def test_get_text_all(self):
        """Test get_text across all languages"""
        for lang_id in get_supported_language_codes():
            options.set('forced_language', lang_id)
            self.assertEqual(get_active_language_code(), lang_id)
            setup_translation()
            text = get_text('Preview')
            self.assertIsInstance(text, str)
            self.assertTrue(len(text) > 0)

    def test_get_text_au(self):
        """Test Austrlian English
        
        It should not get confused with American English.
        """
        options.set('forced_language', 'en_AU')
        self.assertEqual(get_active_language_code(), 'en_AU')
        setup_translation()
        self.assertEqual(get_text('Localizations'), 'Localisations')

    def test_get_text_fallback(self):
        """Language code x_Y should fall back to x"""
        for lang_id in ('es', 'es_XX', 'es_ES', 'es_ES.UTF-8', 'es_1235'):
            options.set('forced_language', lang_id)
            self.assertEqual(get_active_language_code(), lang_id)
            setup_translation()
            self.assertEqual(get_text('Preview'), 'Vista previa')
        