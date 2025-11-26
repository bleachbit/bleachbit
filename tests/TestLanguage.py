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


import locale
import unittest
from unittest import mock

from bleachbit.Language import get_active_language_code, \
    get_supported_language_codes, \
    get_text, \
    setup_translation, \
    get_supported_language_code_name_dict
from bleachbit.Options import options
from tests import common


def skipIfMissingPo(f):
    """Skip unit test if missing translations"""
    lang_count = len(get_supported_language_codes())
    return unittest.skipIf(lang_count < 3, 'missing translations: run `make -C po local`')(f)


class LanguageTestCase(common.BleachbitTestCase):

    """Test case for module Language"""

    def setUp(self):
        super(LanguageTestCase, self).setUp()
        options.set('auto_detect_lang', False)
        options.set('forced_language', '')

    def tearDown(self):
        # reset
        options.set('forced_language', 'en')
        setup_translation()

    def test_get_active_language_code(self):
        """Test get_active_language_code()"""
        lang_id = get_active_language_code()
        self.assertIsLanguageCode(lang_id)

    def test_get_supported_language_codes(self):
        """Test get_supported_language_codes()"""
        slangs = get_supported_language_codes()
        self.assertTrue(isinstance(slangs, list))
        self.assertTrue(len(slangs) > 1)
        for slang in slangs:
            self.assertIsLanguageCode(slang)
        self.assertTrue('en_US' in slangs)
        if len(get_supported_language_codes()) < 3:
            self.skipTest('missing translations')
        self.assertTrue('es' in slangs)

    def test_get_supported_language_code_name_dict_unknown_code(self):
        with mock.patch('bleachbit.Language.get_supported_language_codes', return_value=['en', 'es', 'foo@bar']):
            supported_langs = get_supported_language_code_name_dict()
            self.assertIn('en', supported_langs)
            self.assertIn('es', supported_langs)
            self.assertIn('foo@bar', supported_langs)

    @skipIfMissingPo
    def test_switch_language_twice(self):
        """English should still work after switching twice"""

        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        setup_translation()
        self.assertEqual(get_text('Preview'), 'Preview')

        options.set('auto_detect_lang', False)
        options.set('forced_language', 'es')
        setup_translation()
        self.assertIn(get_text('Preview'), ('Vista previa', 'Previsualizar'))

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

    @skipIfMissingPo
    def test_get_text_au(self):
        """Test Austrlian English

        It should not get confused with American English.
        """
        options.set('forced_language', 'en_AU')
        self.assertEqual(get_active_language_code(), 'en_AU')
        setup_translation()
        self.assertEqual(get_text('Localizations'), 'Localisations')

    @skipIfMissingPo
    def test_get_text_fallback(self):
        """Language code x_Y should fall back to x"""
        for lang_id in ('es', 'es_XX', 'es_ES', 'es_ES.UTF-8', 'es_1235'):
            options.set('forced_language', lang_id)
            self.assertEqual(get_active_language_code(), lang_id)
            setup_translation()
            self.assertIn(get_text('Preview'),
                          ('Vista previa', 'Previsualizar'))

    def test_options_import_failure(self):
        """Test handling of failed Options import in language detection"""
        with mock.patch.dict('sys.modules', {'bleachbit.Options': None}):
            with self.assertLogs(level='ERROR') as log_context:
                result = get_active_language_code()
            self.assertIn("Failed to get language options",
                          log_context.output[0])

        self.assertIn(result, [locale.getlocale()[0], 'C', 'en', 'en_US'])
