# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2024 Andrew Ziem
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


from bleachbit.Language import get_supported_language_codes, native_locale_names, setup_translation, get_text
from tests import common


class LanguageTestCase(common.BleachbitTestCase):

    """Test case for module Language"""

    def test_get_supported_language_codes(self):
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
        from bleachbit.Options import options
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