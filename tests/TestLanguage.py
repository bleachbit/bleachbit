# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


import ctypes
import locale
import os
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
        super().setUp()
        options.set('auto_detect_lang', False)
        options.set('forced_language', '')

    def tearDown(self):
        super().tearDown()
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
        self.assertGreater(len(slangs), 1)
        for slang in slangs:
            if slang in common.SKIP_ALIAS_CODES:
                continue
            self.assertIsLanguageCode(slang)
        self.assertIn('en_US', slangs)
        if len(get_supported_language_codes()) < 3:
            self.skipTest('missing translations')
        self.assertIn('es', slangs)

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
            if lang_id in common.SKIP_ALIAS_CODES:
                continue
            options.set('forced_language', lang_id)
            self.assertEqual(get_active_language_code(), lang_id)
            setup_translation()
            text = get_text('Preview')
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 0)

    @skipIfMissingPo
    def test_get_text_au(self):
        """Test Australian English

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


class SetupTranslationEnvironTestCase(common.BleachbitTestCase):
    """Test case for the LANGUAGE environment variable side effect
    of setup_translation()"""

    def setUp(self):
        super().setUp()
        self._language_env_backup = os.environ.get('LANGUAGE')
        # setup_translation() reassigns this plain module-level
        # global (used by every _()/get_text() call throughout the
        # whole codebase) as a real side effect of calling the real
        # gettext.translation() -- mocking that call prevents the
        # reassignment in the first place, but capture/restore the
        # global directly too as a second line of defense, since
        # this specific global is the actual, confirmed mechanism by
        # which an earlier, less careful version of this same test
        # leaked a real Italian translation into unrelated later
        # tests' own log messages for the rest of the test process.
        from bleachbit import Language as _language_module
        self._t_backup = _language_module.t

    def tearDown(self):
        from bleachbit import Language as _language_module
        _language_module.t = self._t_backup
        if self._language_env_backup is None:
            os.environ.pop('LANGUAGE', None)
        else:
            os.environ['LANGUAGE'] = self._language_env_backup
        super().tearDown()

    def test_setup_translation_sets_language_env_on_posix(self):
        """Regression test: GLib's g_get_language_names(), used
        by Gtk.Builder to translate .ui files such as the hamburger
        menu, reads LANGUAGE directly from the environment with
        top priority -- it does not consult locale.setlocale()'s C
        locale state at all, so without setting it, a
        Gtk.Builder-loaded menu stays frozen in whatever locale
        was in the environment at process launch (e.g. the real
        macOS AppleLocale system preference), never following a
        later in-app language change.

        Confirmed by hand on the real .app: without this, the
        hamburger menu stayed in Spanish through three different
        manually-selected languages and a full app restart, on a
        machine whose real System Settings > Language is Spanish;
        setting LANGUAGE made it follow the selected language
        immediately, without even restarting the app.

        Only LANGUAGE is checked here, deliberately not LANG/
        LC_ALL: an earlier version of this fix also set those,
        which crashed a subprocess Python interpreter started
        later with 'Fatal Python error:
        config_get_locale_encoding: ... nl_langinfo(CODESET)
        failed', since a bare code without an explicit encoding
        (required for GLib's own parsing of these variables
        specifically -- a '.UTF-8' suffix breaks it, verified by
        hand) is not a well-formed LC_ALL/LANG value for every
        other locale-aware consumer in the process.
        """
        os.environ.pop('LANGUAGE', None)
        with mock.patch('bleachbit.Language.get_active_language_code',
                        return_value='it_IT'), \
                mock.patch('bleachbit.Language.IS_POSIX', True), \
                mock.patch('bleachbit.Language.IS_WINDOWS', False), \
                mock.patch('locale.setlocale'), \
                mock.patch('gettext.translation'):
            setup_translation()
        self.assertEqual(os.environ.get('LANGUAGE'), 'it_IT')

    def test_setup_translation_does_not_set_lang_or_lc_all_on_posix(self):
        """LANG/LC_ALL must be left untouched on POSIX -- see the
        comment in setup_translation() and in the test above for
        why setting them crashed a subprocess Python interpreter.
        """
        lang_backup = os.environ.get('LANG')
        lc_all_backup = os.environ.get('LC_ALL')
        try:
            os.environ.pop('LANG', None)
            os.environ.pop('LC_ALL', None)
            with mock.patch('bleachbit.Language.get_active_language_code',
                            return_value='es_ES'), \
                    mock.patch('bleachbit.Language.IS_POSIX', True), \
                    mock.patch('bleachbit.Language.IS_WINDOWS', False), \
                    mock.patch('locale.setlocale'), \
                    mock.patch('gettext.translation'):
                setup_translation()
            self.assertIsNone(os.environ.get('LANG'))
            self.assertIsNone(os.environ.get('LC_ALL'))
        finally:
            if lang_backup is None:
                os.environ.pop('LANG', None)
            else:
                os.environ['LANG'] = lang_backup
            if lc_all_backup is None:
                os.environ.pop('LC_ALL', None)
            else:
                os.environ['LC_ALL'] = lc_all_backup


class WindowsGettextCacheTestCase(common.BleachbitTestCase):
    """Windows: libintl must reload .mo files after an in-process language change.

    Regression for https://github.com/bleachbit/bleachbit/issues/1801 :
    without incrementing _nl_msg_cat_cntr, dgettext/Gtk.Builder keep
    serving the first non-English catalog for the rest of the process.
    """

    @common.skipUnlessWindows
    @skipIfMissingPo
    def test_setup_translation_reloads_libintl_catalog(self):

        from bleachbit import Language as language_module
        from bleachbit.Windows import load_i18n_dll

        libintl = load_i18n_dll()
        if not libintl:
            self.skipTest('intl-8.dll not available')

        libintl.dgettext.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        libintl.dgettext.restype = ctypes.c_char_p
        msgid = b'_Shred Files'
        domain = b'bleachbit'

        with common.set_temporary_env('LANG', os.environ.get('LANG')), \
                common.set_temporary_env('LANGUAGE', os.environ.get('LANGUAGE')):
            t_backup = language_module.t
            try:
                translations = {}
                for lang in ('es', 'it', 'de', 'fr'):
                    with mock.patch(
                            'bleachbit.Language.get_active_language_code',
                            return_value=lang):
                        setup_translation()
                    translated = libintl.dgettext(domain, msgid)
                    self.assertIsNotNone(translated)
                    translations[lang] = translated.decode('utf-8')

                # Distinct languages must not all freeze on the first catalog.
                self.assertNotEqual(translations['es'], translations['it'])
                self.assertNotEqual(translations['es'], translations['de'])
                self.assertIn('archivos', translations['es'].lower())
                self.assertIn('dateien', translations['de'].lower())
            finally:
                language_module.t = t_backup
                # Restore process gettext state for later tests.
                setup_translation()
