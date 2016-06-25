# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://www.bleachbit.org
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
import logging
import os
import re
import shlex
import subprocess
import ConfigParser

from Common import _, autostart_path
import Common
import FileUtilities
import General


class Locales:

    """Find languages and localization files"""

    localepattern = r"(?P<locale>[a-z]{2,3})(?:[_-][a-zA-Z]{2,4})?(?:\.[a-zA-Z0-9-]*)?(?:@[a-zA-Z]*)?"

    native_locale_names = \
        {'aa': 'Afaraf',
         'ab': 'аҧсуа бызшәа',
         'ach': 'Acoli',
         'ae': 'avesta',
         'af': 'Afrikaans',
         'ak': 'Akan',
         'am': 'አማርኛ',
         'an': 'aragonés',
         'ang': 'Old English',
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
         'dv': 'ދިވެހި',
         'dz': 'རྫོང་ཁ',
         'ee': 'Eʋegbe',
         'el': 'Ελληνικά',
         'en': 'English',
         'en_AU': 'Australian English',
         'en_CA': 'Canadian English',
         'en_GB': 'British English',
         'eo': 'Esperanto',
         'es': 'Español',
         'et': 'eesti',
         'eu': 'euskara',
         'fa': 'فارسی',
         'ff': 'Fulfulde',
         'fi': 'suomen kieli',
         'fj': 'vosa Vakaviti',
         'fo': 'føroyskt',
         'fr': 'Français',
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
         'ig': 'Asụsụ Igbo',
         'ii': 'ꆈꌠ꒿',
         'ik': 'Iñupiaq',
         'io': 'Ido',
         'is': 'Íslenska',
         'it': 'Italiano',
         'iu': 'ᐃᓄᒃᑎᑐᑦ',
         'iw': 'עברית',
         'ja': '日本語',
         'jv': 'basa Jawa',
         'ka': 'ქართული',
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

    _paths = []

    def __init__(self):
        pass

    def add_xml(self, xml_node):
        self._paths.append(xml_node)

    def localization_paths(self, locales_to_keep):
        if not locales_to_keep:
            raise RuntimeError('Found no locales to keep')
        purgeable_locales = frozenset((locale for locale in Locales.native_locale_names.keys()
                                       if locale not in locales_to_keep))

        for xml_node in self._paths:
            for (locale, path) in Locales.handle_path('', xml_node):
                if locale in purgeable_locales:
                    yield path

    @staticmethod
    def handle_path(path, xmldata):
        """Extracts paths and filters from the supplied xml tree and yields matching files"""

        if xmldata.ELEMENT_NODE != xmldata.nodeType:
            return
        if not xmldata.nodeName in ['path', 'regexfilter']:
            raise RuntimeError(
                "Invalid node '%s', expected '<path>' or '<regexfilter>'" % xmldata.nodeName)
        location = xmldata.getAttribute('location') or '.'
        if '.' != location:
            path = path + location
        if not path.endswith('/'):
            path += '/'

        if not os.path.isdir(path):
            return

        pre = None
        post = None
        if 'regexfilter' == xmldata.nodeName:
            pre = xmldata.getAttribute('prefix') or ''
            post = xmldata.getAttribute('postfix') or ''
        if 'path' == xmldata.nodeName:
            userfilter = xmldata.getAttribute('filter')
            if not userfilter and not xmldata.hasChildNodes():
                userfilter = '*'
            if userfilter:
                if 1 != userfilter.count('*'):
                    raise RuntimeError(
                        "Filter string '%s' must contain the placeholder * exactly once" % userfilter)

                # we can't use re.escape, because it escapes too much
                (pre, post) = (re.sub(r'([\[\]()^$.])', r'\\\1', p)
                               for p in userfilter.split('*'))
            # handle child nodes
            for child in xmldata.childNodes:
                for (locale, subpath) in Locales.handle_path(path, child):
                    yield (locale, subpath)
        if pre is not None and post is not None:
            try:
                re.compile(pre)
                re.compile(post)
            except Exception as errormsg:
                raise RuntimeError(
                    "Malformed regex '%s' or '%s': %s" % (pre, post, errormsg))
            regex = re.compile('^' + pre + Locales.localepattern + post + '$')
            for subpath in os.listdir(path):
                match = regex.match(subpath)
                if match is not None:
                    yield (match.group("locale"), path + subpath)


def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', 'autoclean']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # Del cups-common 1.3.9-17ubuntu3 [1165kB]
        match = re.search("^Del .*\[([0-9.]+[a-zA-Z]{2})\]", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', '--yes', 'autoremove']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # After this operation, 74.7MB disk space will be freed.
        match = re.search(
            r", ([0-9.]+[a-zA-Z]{2}) disk space will be freed", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def __is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns boolean whether application deskop entry file is broken"""
    if not config.has_option('Desktop Entry', 'Exec'):
        print "info: is_broken_xdg_menu: missing required option 'Exec': '%s'" \
            % (desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not FileUtilities.exe_exists(exe):
        print "info: is_broken_xdg_menu: executable '%s' does not exist '%s'" \
            % (exe, desktop_pathname)
        return True
    if 'env' == exe:
        # Wine v1.0 creates .desktop files like this
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program
        # Files\\foo\\foo.exe"
        execs = shlex.split(config.get('Desktop Entry', 'Exec'))
        wineprefix = None
        del execs[0]
        while True:
            if 0 <= execs[0].find("="):
                (name, value) = execs[0].split("=")
                if 'WINEPREFIX' == name:
                    wineprefix = value
                del execs[0]
            else:
                break
        if not FileUtilities.exe_exists(execs[0]):
            print "info: is_broken_xdg_menu: executable '%s'" \
                "does not exist '%s'" % (execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                print "info: is_broken_xdg_menu: Windows executable" \
                    "'%s' does not exist '%s'" % \
                    (windows_exe, desktop_pathname)
                return True
    return False


def is_unregistered_mime(mimetype):
    """Returns True if the MIME type is known to be unregistered. If
    registered or unknown, conservatively returns False."""
    try:
        import gio
        if 0 == len(gio.app_info_get_all_for_type(mimetype)):
            return True
    except:
        logger = logging.getLogger(__name__)
        logger.warning(
            'error calling gio.app_info_get_all_for_type(%s)' % mimetype)
    return False


def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = ConfigParser.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        print "info: is_broken_xdg_menu: missing required section " \
            "'Desktop Entry': '%s'" % (pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        print "info: is_broken_xdg_menu: missing required option 'Type': '%s'" % (pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
                not config.has_option('Desktop Entry', 'URL[$e]'):
            print "info: is_broken_xdg_menu: missing required option 'URL': '%s'" % (pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            print "info: is_broken_xdg_menu: missing required option 'MimeType': '%s'" % (pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if is_unregistered_mime(mimetype):
            print "info: is_broken_xdg_menu: MimeType '%s' not " \
                "registered '%s'" % (mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        print "Warning: unhandled type '%s': file '%s'" % (file_type, pathname)
        return False
    if __is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def is_running(exename):
    """Check whether exename is running"""
    for filename in glob.iglob("/proc/*/exe"):
        try:
            target = os.path.realpath(filename)
        except TypeError:
            # happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            continue
        except OSError:
            # 13 = permission denied
            continue
        if exename == os.path.basename(target):
            return True
    return False


def rotated_logs():
    """Yield a list of rotated (i.e., old) logs in /var/log/"""
    # Ubuntu 9.04
    # /var/log/dmesg.0
    # /var/log/dmesg.1.gz
    # Fedora 10
    # /var/log/messages-20090118
    globpaths = ('/var/log/*.[0-9]',
                 '/var/log/*/*.[0-9]',
                 '/var/log/*.gz',
                 '/var/log/*/*gz',
                 '/var/log/*/*.old',
                 '/var/log/*.old')
    for globpath in globpaths:
        for path in glob.iglob(globpath):
            yield path
    regex = '-[0-9]{8}$'
    globpaths = ('/var/log/*-*', '/var/log/*/*-*')
    for path in FileUtilities.globex(globpaths, regex):
        whitelist_re = '^/var/log/(removed_)?(packages|scripts)'
        if None == re.match(whitelist_re, path):  # for Slackware, Launchpad #367575
            yield path


def start_with_computer(enabled):
    """If enabled, create shortcut to start application with computer.
    If disabled, then delete the shortcut."""
    if not enabled:
        # User requests to not automatically start BleachBit
        if os.path.lexists(autostart_path):
            # Delete the shortcut
            FileUtilities.delete(autostart_path)
        return
    # User requests to automatically start BleachBit
    if os.path.lexists(autostart_path):
        # Already automatic, so exit
        return
    if not os.path.exists(Common.launcher_path):
        print 'ERROR: does not exist: ', Common.launcher_path
        return
    import shutil
    General.makedirs(os.path.dirname(autostart_path))
    shutil.copy(Common.launcher_path, autostart_path)
    os.chmod(autostart_path, 0755)
    if General.sudo_mode():
        General.chownself(autostart_path)


def start_with_computer_check():
    """Return boolean whether BleachBit will start with the computer"""
    return os.path.lexists(autostart_path)


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":",
                                                "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\", "/")
    return os.path.join(wineprefix, windows_pathname)


def yum_clean():
    """Run 'yum clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/yum.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Yum"
        raise RuntimeError(msg)
    if not FileUtilities.exe_exists('yum'):
        raise RuntimeError(_('Executable not found: %s') % 'yum')
    old_size = FileUtilities.getsizedir('/var/cache/yum')
    args = ['yum', "--enablerepo=*", 'clean', 'all']
    p = subprocess.Popen(args, stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    non_blank_line = ""
    while True:
        line = p.stdout.readline().replace("\n", "")
        if len(line) > 2:
            non_blank_line = line
        if -1 != line.find('You need to be root'):
            # Seen before Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Cannot remove rpmdb file'):
            # Since first in Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Another app is currently holding'):
            print "debug: yum: '%s'" % line
            old_size = FileUtilities.getsizedir('/var/cache/yum')
        if "" == line and p.poll() != None:
            break
    print 'debug: yum process return code = %d' % p.returncode
    if p.returncode > 0:
        raise RuntimeError(non_blank_line)
    new_size = FileUtilities.getsizedir('/var/cache/yum')
    return old_size - new_size


locales = Locales()
