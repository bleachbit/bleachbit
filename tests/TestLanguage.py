# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


import contextlib
import ctypes
import os
import unittest
from unittest import mock

from bleachbit.Language import _UNSET, \
    find_supported_language_code, \
    get_active_language_code, \
    get_supported_language_codes, \
    get_text, \
    LocaleCode, \
    normalize_locale_code, \
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

    def test_find_supported_language_code(self):
        """Test find_supported_language_code()

        The detected language code may differ from the supported code:
        Windows may return a hyphen like 'en-US' or a region like
        'hi_IN' while only 'hi' is supported.

        https://github.com/bleachbit/bleachbit/issues/1799
        https://github.com/bleachbit/bleachbit/issues/1800
        """
        supported = ['en', 'en_US', 'es', 'hi', 'pt_BR']
        # Exact match.
        self.assertEqual(
            find_supported_language_code('en_US', supported), 'en_US')
        self.assertEqual(
            find_supported_language_code('es', supported), 'es')
        # Hyphen instead of underscore.
        self.assertEqual(
            find_supported_language_code('en-US', supported), 'en_US')
        # Region falls back to primary language subtag.
        self.assertEqual(
            find_supported_language_code('hi_IN', supported), 'hi')
        self.assertEqual(
            find_supported_language_code('es_419', supported), 'es')
        # Primary language subtag falls back to a regional variant.
        self.assertEqual(
            find_supported_language_code('pt', supported), 'pt_BR')
        self.assertEqual(
            find_supported_language_code('en_GB', supported), 'en')
        # Case-insensitive match.
        self.assertEqual(
            find_supported_language_code('EN-us', supported), 'en_US')
        # Strip codeset and modifier.
        self.assertEqual(
            find_supported_language_code('de_DE.UTF-8', ['de_DE']), 'de_DE')
        self.assertEqual(
            find_supported_language_code('de@euro', ['de']), 'de')
        self.assertEqual(
            find_supported_language_code('sr_RS@latin', ['sr']), 'sr')
        # Regional variant prefers the same or script-implied region:
        # 'zh_Hant', 'zh_HK', and 'zh_MO' are Traditional Chinese.
        supported_zh = ['zh_CN', 'zh_TW']
        self.assertEqual(
            find_supported_language_code('zh_Hant_TW', supported_zh), 'zh_TW')
        self.assertEqual(
            find_supported_language_code('zh_Hant', supported_zh), 'zh_TW')
        self.assertEqual(
            find_supported_language_code('zh_HK', supported_zh), 'zh_TW')
        self.assertEqual(
            find_supported_language_code('zh_MO', supported_zh), 'zh_TW')
        self.assertEqual(
            find_supported_language_code('zh_Hans', supported_zh), 'zh_CN')
        self.assertEqual(
            find_supported_language_code('zh', supported_zh), 'zh_CN')
        # No match.
        self.assertIsNone(find_supported_language_code('de', supported))
        self.assertIsNone(find_supported_language_code('C', supported))
        self.assertIsNone(find_supported_language_code('', supported))
        self.assertIsNone(find_supported_language_code('.UTF-8', supported))
        self.assertIsNone(find_supported_language_code('en', []))

    def test_normalize_locale_code(self):
        """Test normalize_locale_code()"""
        tests = [
            ('ca@valencia', 'ca'),
            ('de_DE.utf8@euro', 'de_DE'),
            ('en_US.UTF-8', 'en_US'),
            ('en-US', 'en_US'),
            ('ko_KR.eucKR', 'ko_KR'),
            ('sr_RS@latin', 'sr_RS'),
            ('zh-Hant-TW', 'zh_Hant_TW'),
            ('C.UTF-8', 'C'),
            ('.UTF-8', ''),
            ('@', ''),
            ('@euro', ''),
        ]
        same_cases = ['en_US', 'en_001', 'es_419', 'it_CARES', 'C', '']
        tests.extend((c, c) for c in same_cases)
        for raw, expected in tests:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_locale_code(raw), expected)

    def test_localecode_parse(self):
        """Test LocaleCode parsing, including @ before . for locale.alias"""
        tests = [
            # raw, language, territory, encoding, modifier
            ('en', 'en', None, None, None),
            ('de-CH', 'de', 'CH', None, None),
            ('es_419', 'es', '419', None, None),
            ('de_DE.utf8@euro', 'de', 'DE', 'utf8', 'euro'),
            ('en_US@piglatin', 'en', 'US', None, 'piglatin'),
            ('C.UTF-8', 'C', None, 'UTF-8', None),
            ('en@boldquot.header', 'en', None, None, 'boldquot.header'),
        ]
        for raw, language, territory, encoding, modifier in tests:
            with self.subTest(raw=raw):
                loc = LocaleCode(raw)
                self.assertEqual(loc.language, language)
                self.assertEqual(loc.territory, territory)
                self.assertEqual(loc.encoding, encoding)
                self.assertEqual(loc.modifier, modifier)
                self.assertEqual(str(loc), raw)

    def test_localecode_is_utf8(self):
        """Test LocaleCode.is_utf8"""
        for raw in ('en_US.utf8', 'en_US.UTF-8', 'de_DE.utf8@euro',
                    'C.utf8', 'C.UTF-8'):
            with self.subTest(raw=raw):
                self.assertTrue(LocaleCode(raw).is_utf8)
        for raw in ('de_DE.iso88591', 'de_DE', 'sr_RS@latin', 'en_US',
                    'nb_NO.ISO-8859-1'):
            with self.subTest(raw=raw):
                self.assertFalse(LocaleCode(raw).is_utf8)

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
            self.assertEqual(get_active_language_code(),
                             normalize_locale_code(lang_id))
            setup_translation()
            self.assertIn(get_text('Preview'),
                          ('Vista previa', 'Previsualizar'))

    @contextlib.contextmanager
    def cleared_env(self, **env):
        """Run with exactly the given environment variables; all
        others are cleared."""
        with mock.patch.dict(os.environ, env, clear=True):
            yield

    @common.skipIfWindows
    def test_get_active_language_code_posix_env_not_setlocale(self):
        """The environment wins over the locale set by setlocale()."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        with self.cleared_env(LANG='en_US.UTF-8'), \
                mock.patch('locale.getlocale',
                           return_value=('es_ES', 'UTF-8')):
            self.assertEqual(get_active_language_code(), 'en_US')

    @common.skipUnlessLinux
    def test_get_active_language_code_posix_env_unset(self):
        """With no locale env vars, fall back to locale.getlocale()."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        with self.cleared_env(), \
                mock.patch('bleachbit.Language._locale_fallback', _UNSET), \
                mock.patch('locale.getlocale',
                           return_value=('fr_FR', 'UTF-8')):
            self.assertEqual(get_active_language_code(), 'fr_FR')

    @common.skipIfWindows
    def test_get_active_language_code_posix_env_strips_codeset(self):
        """Strip the codeset ('.UTF-8') and modifier ('@latin')."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        for raw, expected in (('de_DE.UTF-8', 'de_DE'),
                              ('de_DE@euro', 'de_DE'),
                              ('sr_RS.UTF-8@latin', 'sr_RS'),
                              ('C.UTF-8', 'C')):
            with self.subTest(raw=raw), \
                    self.cleared_env(LANG=raw):
                self.assertEqual(get_active_language_code(), expected)

    @common.skipIfWindows
    def test_get_active_language_code_posix_env_precedence(self):
        """LC_ALL wins over LC_MESSAGES, which wins over LANG, and an
        empty value counts as unset."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        with self.subTest('all set'), \
                self.cleared_env(LC_ALL='es_ES.UTF-8',
                                 LC_MESSAGES='fr_FR.UTF-8',
                                 LANG='en_US.UTF-8'):
            self.assertEqual(get_active_language_code(), 'es_ES')
        with self.subTest('empty LC_ALL'), \
                self.cleared_env(LC_ALL='', LANG='en_US.UTF-8'):
            self.assertEqual(get_active_language_code(), 'en_US')
        with self.subTest('malformed LC_ALL skipped'), \
                self.cleared_env(LC_ALL='x', LANG='en_US.UTF-8'):
            self.assertEqual(get_active_language_code(), 'en_US')
        with self.subTest('malformed LANG'), \
                self.cleared_env(LANG='x'):
            self.assertEqual(get_active_language_code(), 'C')

    @common.skipUnlessLinux
    def test_get_active_language_code_locale_fallback_cached(self):
        """The fallback is captured once, not re-read after setlocale()."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        with self.cleared_env(), \
                mock.patch('bleachbit.Language._locale_fallback', _UNSET), \
                mock.patch('locale.getlocale',
                           side_effect=[('fr_FR', 'UTF-8'),
                                        ('es_ES', 'UTF-8')]) as getlocale:
            # Second call returns the captured value despite the changed locale.
            self.assertEqual(get_active_language_code(), 'fr_FR')
            self.assertEqual(get_active_language_code(), 'fr_FR')
            self.assertEqual(getlocale.call_count, 1)

    @common.skipUnlessLinux
    def test_get_active_language_code_getlocale_valueerror(self):
        """An unparseable getlocale() result falls back to 'C'."""
        options.set('auto_detect_lang', True)
        options.set('forced_language', '')
        with self.cleared_env(), \
                mock.patch('bleachbit.Language._locale_fallback', _UNSET), \
                mock.patch('locale.getlocale', side_effect=ValueError):
            self.assertEqual(get_active_language_code(), 'C')

    def test_options_import_failure(self):
        """Test handling of failed Options import in language detection"""
        with mock.patch.dict('sys.modules', {'bleachbit.Options': None}):
            with self.assertLogs(level='ERROR') as log_context:
                result = get_active_language_code()
            self.assertIn("Failed to get language options",
                          log_context.output[0])

        self.assertIsLanguageCode(result)


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

    def test_setup_translation_bumps_generation(self):
        """Each setup_translation() call bumps translation_generation"""
        from bleachbit import Language as _language_module
        before = _language_module.translation_generation
        setup_translation()
        self.assertEqual(_language_module.translation_generation, before + 1)

    @common.skipIfWindows
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
                mock.patch('locale.setlocale'), \
                mock.patch('gettext.find', return_value='bleachbit.mo'), \
                mock.patch('gettext.translation'), \
                mock.patch('bleachbit.Unix.find_best_locale',
                           return_value='it_IT'):
            setup_translation()
        self.assertEqual(os.environ.get('LANGUAGE'), 'it_IT')

    @common.skipIfWindows
    def test_setup_translation_regional_variant(self):
        """zh_HK uses the shipped zh_TW catalog"""
        locale_dir = os.path.join(self.tempdir, 'locale')
        mo_dir = os.path.join(locale_dir, 'zh_TW', 'LC_MESSAGES')
        os.makedirs(mo_dir)
        with open(os.path.join(mo_dir, 'bleachbit.mo'), 'wb'):
            pass
        with mock.patch('bleachbit.locale_dir', locale_dir), \
                mock.patch('bleachbit.Language.get_active_language_code',
                           return_value='zh_HK'), \
                mock.patch('locale.setlocale'), \
                mock.patch('locale.bindtextdomain', create=True), \
                mock.patch('locale.textdomain', create=True), \
                mock.patch('gettext.translation') as mock_translation, \
                mock.patch('bleachbit.Unix.find_best_locale',
                           return_value='zh_HK'):
            setup_translation()
        self.assertEqual(mock_translation.call_args.kwargs['languages'],
                         ['zh_TW'])
        self.assertEqual(os.environ.get('LANGUAGE'), 'zh_TW')

    @common.skipUnlessLinux
    def test_setup_translation_captures_locale_before_setlocale(self):
        """A language forced at startup must not poison auto-detection.

        setup_translation() returns early on a forced language without
        calling get_active_language_code()'s fallback, so it must capture
        the system locale before setlocale() changes what getlocale() sees.
        """
        options.set('auto_detect_lang', False)
        options.set('forced_language', 'es')
        with mock.patch('bleachbit.Language._locale_fallback', _UNSET), \
                mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch('locale.setlocale'), \
                mock.patch('gettext.translation'), \
                mock.patch('bleachbit.Unix.find_best_locale',
                           return_value='es_ES'):
            with mock.patch('locale.getlocale',
                            return_value=('fr_FR', 'UTF-8')):
                setup_translation()
            # Re-enable auto-detection; getlocale() now reports the forced
            # language, but detection must still see the captured one.
            options.set('auto_detect_lang', True)
            options.set('forced_language', '')
            with mock.patch('locale.getlocale',
                            return_value=('es_ES', 'UTF-8')):
                self.assertEqual(get_active_language_code(), 'fr_FR')

    @common.skipIfWindows
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
                    mock.patch('locale.setlocale'), \
                    mock.patch('gettext.translation'), \
                    mock.patch('bleachbit.Unix.find_best_locale',
                               return_value='es_ES'):
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
                    translations[lang] = translated.decode('utf-8')

                # Distinct languages must not all freeze on the first catalog.
                self.assertNotEqual(translations['es'], translations['it'])
                self.assertNotEqual(translations['es'], translations['de'])
                self.assertNotEqual(translations['es'], translations['fr'])
                self.assertIn('archivos', translations['es'].lower())
                self.assertIn('dateien', translations['de'].lower())
            finally:
                language_module.t = t_backup
                # Restore process gettext state for later tests, after the
                # environment variables have been restored to their
                # pre-test values.
                setup_translation()
