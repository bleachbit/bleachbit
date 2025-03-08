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

import gettext
import os
import logging
import sys

logger = logging.getLogger(__name__)


native_locale_names = \
    {'aa': 'Afaraf',
     'ab': 'аҧсуа бызшәа',
     'ace': 'بهسا اچيه',
     'ach': 'Acoli',
     'ae': 'avesta',
     'af': 'Afrikaans',
     'ak': 'Akan',
     'am': 'አማርኛ',
     'an': 'aragonés',
     'ang': 'Old English',
     'anp': 'Angika',
     'ar': 'العربية',
     'as': 'অসমীয়া',
     'ast': 'Asturianu',
     'av': 'авар мацӀ',
     'ay': 'aymar aru',
     'az': 'azərbaycan dili',
     'ba': 'башҡорт теле',
     'bal': 'Baluchi',
     'be': 'Беларуская мова',
     'bg': 'български език',
     'bh': 'भोजपुरी',
     'bi': 'Bislama',
     'bm': 'bamanankan',
     'bn': 'বাংলা',
     'bo': 'བོད་ཡིག',
     'br': 'brezhoneg',
     'brx': 'Bodo (India)',
     'bs': 'босански',
     'byn': 'Bilin',
     'ca': 'català',
     'ce': 'нохчийн мотт',
     'cgg': 'Chiga',
     'ch': 'Chamoru',
     'ckb': 'Central Kurdish',
     'co': 'corsu',
     'cr': 'ᓀᐦᐃᔭᐍᐏᐣ',
     'crh': 'Crimean Tatar',
     'cs': 'česky',
     'csb': 'Cashubian',
     'cu': 'ѩзыкъ словѣньскъ',
     'cv': 'чӑваш чӗлхи',
     'cy': 'Cymraeg',
     'da': 'dansk',
     'de': 'Deutsch',
     'doi': 'डोगरी; ڈوگرى',
     'dv': 'ދިވެހި',
     'dz': 'རྫོང་ཁ',
     'ee': 'Eʋegbe',
     'el': 'Ελληνικά', # modern Greek
     'en': 'English',
     'en_AU': 'Australian English',
     'en_CA': 'Canadian English',
     'en_GB': 'British English',
     'en_US': 'United States English',
     'eo': 'Esperanto',
     'es': 'Español',
     'es_419': 'Latin American Spanish',
     'et': 'eesti',
     'eu': 'euskara',
     'fa': 'فارسی',
     'ff': 'Fulfulde',
     'fi': 'suomen kieli',
     'fil': 'Wikang Filipino',
     'fin': 'suomen kieli',
     'fj': 'vosa Vakaviti',
     'fo': 'føroyskt',
     'fr': 'Français',
     'frp': 'Arpitan',
     'fur': 'Frilian',
     'fy': 'Frysk',
     'ga': 'Gaeilge',
     'gd': 'Gàidhlig',
     'gez': 'Geez',
     'gl': 'galego',
     'gn': 'Avañeẽ',
     'grc': 'Ἑλληνική', # ancient Greek
     'gu': 'Gujarati',
     'gv': 'Gaelg',
     'ha': 'هَوُسَ',
     'haw': 'Hawaiian',
     'he': 'עברית',
     'hi': 'हिन्दी',
     'hne': 'Chhattisgarhi',
     'ho': 'Hiri Motu',
     'hr': 'Hrvatski',
     'hsb': 'Upper Sorbian',
     'ht': 'Kreyòl ayisyen',
     'hu': 'Magyar',
     'hy': 'Հայերեն',
     'hz': 'Otjiherero',
     'ia': 'Interlingua',
     'id': 'Indonesian',
     'ie': 'Interlingue',
     'ig': 'Asụsụ Igbo',
     'ii': 'ꆈꌠ꒿',
     'ik': 'Iñupiaq',
     'ilo': 'Ilokano',
     'ina': 'Interlingua',
     'io': 'Ido',
     'is': 'Íslenska',
     'it': 'Italiano',
     'iu': 'ᐃᓄᒃᑎᑐᑦ',
     'iw': 'עברית',
     'ja': '日本語',
     'jv': 'basa Jawa',
     'ka': 'ქართული',
     'kab': 'Tazwawt',
     'kac': 'Jingpho',
     'kg': 'Kikongo',
     'ki': 'Gĩkũyũ',
     'kj': 'Kuanyama',
     'kk': 'қазақ тілі',
     'kl': 'kalaallisut',
     'km': 'ខ្មែរ',
     'kn': 'ಕನ್ನಡ',
     'ko': '한국어',
     'kok': 'Konkani',
     'kr': 'Kanuri',
     'ks': 'कश्मीरी',
     'ku': 'Kurdî',
     'kv': 'коми кыв',
     'kw': 'Kernewek',
     'ky': 'Кыргызча',
     'la': 'latine',
     'lb': 'Lëtzebuergesch',
     'lg': 'Luganda',
     'li': 'Limburgs',
     'ln': 'Lingála',
     'lo': 'ພາສາລາວ',
     'lt': 'lietuvių kalba',
     'lu': 'Tshiluba',
     'lv': 'latviešu valoda',
     'mai': 'Maithili',
     'mg': 'fiteny malagasy',
     'mh': 'Kajin M̧ajeļ',
     'mhr': 'Eastern Mari',
     'mi': 'te reo Māori',
     'mk': 'македонски јазик',
     'ml': 'മലയാളം',
     'mn': 'монгол',
     'mni': 'Manipuri',
     'mr': 'मराठी',
     'ms': 'بهاس ملايو',
     'mt': 'Malti',
     'my': 'ဗမာစာ',
     'na': 'Ekakairũ Naoero',
     'nb': 'Bokmål',
     'nd': 'isiNdebele',
     'nds': 'Plattdüütsch',
     'ne': 'नेपाली',
     'ng': 'Owambo',
     'nl': 'Nederlands',
     'nn': 'Norsk nynorsk',
     'no': 'Norsk',
     'nr': 'isiNdebele',
     'nso': 'Pedi',
     'nv': 'Diné bizaad',
     'ny': 'chiCheŵa',
     'oc': 'occitan',
     'oj': 'ᐊᓂᔑᓈᐯᒧᐎᓐ',
     'om': 'Afaan Oromoo',
     'or': 'ଓଡ଼ିଆ',
     'os': 'ирон æвзаг',
     'pa': 'ਪੰਜਾਬੀ',
     'pap': 'Papiamentu',
     'pau': 'a tekoi er a Belau',
     'pi': 'पाऴि',
     'pl': 'polski',
     'ps': 'پښتو',
     'pt': 'Português',
     'pt_BR': 'Português do Brasil',
     'qu': 'Runa Simi',
     'rm': 'rumantsch grischun',
     'rn': 'Ikirundi',
     'ro': 'română',
     'ru': 'Pусский',
     'rw': 'Ikinyarwanda',
     'sa': 'संस्कृतम्',
     'sat': 'ᱥᱟᱱᱛᱟᱲᱤ',
     'sc': 'sardu',
     'sd': 'सिन्धी',
     'se': 'Davvisámegiella',
     'sg': 'yângâ tî sängö',
     'shn': 'Shan',
     'si': 'සිංහල',
     'sk': 'slovenčina',
     'sl': 'slovenščina',
     'sm': 'gagana faa Samoa',
     'sn': 'chiShona',
     'so': 'Soomaaliga',
     'sq': 'Shqip',
     'sr': 'Српски',
     'ss': 'SiSwati',
     'st': 'Sesotho',
     'su': 'Basa Sunda',
     'sv': 'svenska',
     'sw': 'Kiswahili',
     'ta': 'தமிழ்',
     'te': 'తెలుగు',
     'tet': 'Tetum',
     'tg': 'тоҷикӣ',
     'th': 'ไทย',
     'ti': 'ትግርኛ',
     'tig': 'Tigre',
     'tk': 'Türkmen',
     'tl': 'ᜏᜒᜃᜅ᜔ ᜆᜄᜎᜓᜄ᜔',
     'tn': 'Setswana',
     'to': 'faka Tonga',
     'tr': 'Türkçe',
     'ts': 'Xitsonga',
     'tt': 'татар теле',
     'tw': 'Twi',
     'ty': 'Reo Tahiti',
     'ug': 'Uyghur',
     'uk': 'Українська',
     'ur': 'اردو',
     'uz': 'Ўзбек',
     've': 'Tshivenḓa',
     'vi': 'Tiếng Việt',
     'vo': 'Volapük',
     'wa': 'walon',
     'wae': 'Walser',
     'wal': 'Wolaytta',
     'wo': 'Wollof',
     'xh': 'isiXhosa',
     'yi': 'ייִדיש',
     'yo': 'Yorùbá',
     'za': 'Saɯ cueŋƅ',
     'zh': '中文',
     'zh_CN': '中文',
     'zh_TW': '中文',
     'zu': 'isiZulu'}


def get_supported_language_codes():
    """Return list of supported languages as language codes

    Supported means a translation may be available.
    """
    supported_langs = []
    # Use local import to avoid circular import.
    from bleachbit import locale_dir
    # The locale_dir may not exist, especially on Windows.
    if not os.path.isdir(locale_dir):
        return ['en_US', 'en']
    lang_codes = sorted(set(os.listdir(locale_dir)+['en_US', 'en']))
    for lang in lang_codes:
        if lang in ('en', 'en_US'):
            supported_langs.append(lang)
            continue
        if os.path.isdir(os.path.join(locale_dir, lang)):
            try:
                translation = gettext.translation(
                    'bleachbit', locale_dir, languages=[lang])
                if translation:
                    supported_langs.append(lang)
            except FileNotFoundError:
                pass
    return supported_langs


def get_supported_language_code_name_dict():
    """Return dictionary of supported languages as language codes and names

    Supported means a translation is available.
    """
    supported_langs = {}
    for lang in get_supported_language_codes():
        supported_langs[lang] = native_locale_names.get(lang, None)
    return supported_langs


def get_active_language_code():
    """Return the language ID to use for translations

    The language ID is a code like: en, en_US, nds, C

    There may be an underscore or no underscore. The first part may
    contain two or three letters.

    There will not be a dot like `en_US.UTF-8`.
    """
    try:
        from bleachbit.Options import options
    except ImportError:
        logger.error("Failed to get language options")
    else:
        if not options.get('auto_detect_lang') and options.has_option('forced_language') and options.get('forced_language'):
            return options.get('forced_language')
    import locale
    # locale.getdefaultlocale() will be removed in Python 3.15, so
    # use getlocale() instead.
    # However, on Windows, getlocale() may return values like
    # 'English_United States' instead of RFC1766 codes.
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        lcid = kernel32.GetUserDefaultLCID()
        # Convert Windows LCID (e.g., 1033) to RFC1766 (e.g., en-US).
        user_locale = locale.windows_locale.get(lcid, '')
    else:
        user_locale = locale.getlocale()[0]

    if not user_locale:
        user_locale = 'C'
        logger.warning("no default locale found.  Assuming '%s'", user_locale)

    if '.' in user_locale:
        # This should never happen.
        logger.warning('locale contains a dot: %s', user_locale)
        user_locale = user_locale.split('.')[0]

    assert isinstance(user_locale, str)
    assert len(
        user_locale) >= 2 or user_locale == 'C', f"user_locale: {user_locale}"

    return user_locale


def setup_translation():
    """Do a one-time setup of translations"""
    global attempted_setup_translation, t
    attempted_setup_translation = True
    # Use local import to avoid circular import.
    from bleachbit import locale_dir
    user_locale = get_active_language_code()
    logger.debug(f"user_locale: {user_locale}, locale_dir: {locale_dir}")
    assert isinstance(user_locale, str)
    assert isinstance(locale_dir, str), f"locale_dir: {locale_dir}"
    if 'win32' == sys.platform and user_locale:
        os.environ['LANG'] = user_locale
    text_domain = 'bleachbit'
    try:
        t = gettext.translation(
            domain=text_domain, localedir=locale_dir, languages=[user_locale], fallback=True)
    except FileNotFoundError as e:
        logger.error(
            "Error in setup_translation() with language code %s: %s", user_locale, e)
        t = None
        return
    import locale
    if hasattr(locale, 'bindtextdomain'):
        locale.bindtextdomain(text_domain, locale_dir)
        locale.textdomain(text_domain)
    elif 'nt' == os.name:
        from bleachbit.Windows import load_i18n_dll
        libintl = load_i18n_dll()
        if not libintl:
            logger.error(
                'The internationalization library is not available.')
        assert isinstance(text_domain, str)
        encoded_domain = text_domain.encode('utf-8')
        # wbindtextdomain(char, wchar): first parameter is encoded
        libintl.libintl_wbindtextdomain(encoded_domain, locale_dir)
        libintl.textdomain(encoded_domain)
        libintl.bind_textdomain_codeset(encoded_domain, b'UTF-8')

        # Log for debugging
        logger.debug(
            f"Windows translation domain set to: {text_domain}, dir: {locale_dir}")
    else:
        logger.error('The function bindtextdomain() is not available.')

    # locale.setlocale() on Linux will throw an exception if the locale is not
    # available, so find the best matching locale. When set, Gtk.Builder is
    # translated.
    # On Windows, locale.setlocale() accepts any values without raising an exception.
    if os.name == 'posix':
        from bleachbit.Unix import find_best_locale
        setlocale_local = find_best_locale(user_locale)
        if 'C' == setlocale_local and not user_locale == 'C':
            logger.warning('locale %s is not available. You may wish to run sudo local-gen to generate it.', user_locale)
        try:
            locale.setlocale(locale.LC_ALL, setlocale_local)
        except locale.Error as e:
            logger.error('locale.setlocale(%s): %s:', setlocale_local, e)


def get_text(str):
    """Return translated string

    The name has an underscore to avoid conflicting with gettext module.
    """
    global attempted_setup_translation, t
    if not attempted_setup_translation:
        setup_translation()
    if not t:
        return str
    return t.gettext(str)


def nget_text(singular, plural, n):
    """Return translated string with plural variant"""
    global t
    if not t:
        if 1 == n:
            return singular
        return plural
    return t.ngettext(singular, plural, n)


def pget_text(msgctxt, msgid):
    """Return translated string with context

    Example context is button
    """
    global t
    if not t:
        return msgid
    return t.pgettext(msgctxt, msgid)


attempted_setup_translation = False
t = None
