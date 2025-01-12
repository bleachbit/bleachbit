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
     'el': 'Ελληνικά',
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

    Supported means a translation is available.
    """
    supported_langs = []
    # Use local import to avoid circular import.
    from bleachbit import locale_dir
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
        supported_langs[lang] = native_locale_names[lang]
    return supported_langs


def get_active_language_code():
    """Return the language ID to use for translations"""
    from bleachbit.Options import options
    if not options.get('auto_detect_lang') and options.has_option('forced_language') and options.get('forced_language'):
        return options.get('forced_language')
    import locale
    try:
        (user_locale, _encoding) = locale.getlocale()
    except:
        logger.exception('error getting locale')
        user_locale = None

    if user_locale is None:
        user_locale = 'C'
        logger.warning("no default locale found.  Assuming '%s'", user_locale)
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
    try:
        t = gettext.translation(
            domain='bleachbit', localedir=locale_dir, languages=[user_locale])
    except FileNotFoundError:
        logger.debug("locale directory '%s' does not exist", locale_dir)
        t = None
        return
    import locale
    locale.bindtextdomain('bleachbit', locale_dir)
    # fixme: test importance of libintl-8.dll


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
