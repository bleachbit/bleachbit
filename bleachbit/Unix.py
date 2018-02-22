# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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


"""
Integration specific to Unix-like operating systems
"""

from __future__ import absolute_import, print_function

import bleachbit
from bleachbit import FileUtilities, General
from bleachbit import _

import glob
import logging
import os
import re
import shlex
import subprocess
import sys

logger = logging.getLogger(__name__)


class LocaleCleanerPath:
    """This represents a path with either a specific folder name or a folder name pattern.
    It also may contain several compiled regex patterns for localization items (folders or files)
    and additional LocaleCleanerPaths that get traversed when asked to supply a list of localization
    items"""

    def __init__(self, location):
        if location is None:
            raise RuntimeError("location is none")
        self.pattern = location
        self.children = []

    def add_child(self, child):
        """Adds a child LocaleCleanerPath"""
        self.children.append(child)
        return child

    def add_path_filter(self, pre, post):
        """Adds a filter consisting of a prefix and a postfix
        (e.g. 'foobar_' and '\.qm' to match 'foobar_en_US.utf-8.qm)"""
        try:
            regex = re.compile('^' + pre + Locales.localepattern + post + '$')
        except Exception as errormsg:
            raise RuntimeError("Malformed regex '%s' or '%s': %s" % (pre, post, errormsg))
        self.add_child(regex)

    def get_subpaths(self, basepath):
        """Returns direct subpaths for this object, i.e. either the named subfolder or all
        subfolders matching the pattern"""
        if isinstance(self.pattern, re._pattern_type):
            return (os.path.join(basepath, p) for p in os.listdir(basepath)
                    if self.pattern.match(p) and os.path.isdir(os.path.join(basepath, p)))
        else:
            path = os.path.join(basepath, self.pattern)
            return [path] if os.path.isdir(path) else []

    def get_localizations(self, basepath):
        """Returns all localization items for this object and all descendant objects"""
        for path in self.get_subpaths(basepath):
            for child in self.children:
                if isinstance(child, LocaleCleanerPath):
                    for res in child.get_localizations(path):
                        yield res
                elif isinstance(child, re._pattern_type):
                    for element in os.listdir(path):
                        match = child.match(element)
                        if match is not None:
                            yield (match.group('locale'), os.path.join(path, element))


class Locales:
    """Find languages and localization files"""

    # The regular expression to match locale strings and extract the langcode.
    # See test_locale_regex() in tests/TestUnix.py for examples
    # This doesn't match all possible valid locale strings to avoid
    # matching filenames you might want to keep, e.g. the regex
    # to match jp.eucJP might also match jp.importantfileextension
    localepattern =\
        r'(?P<locale>[a-z]{2,3})' \
        r'(?:[_-][A-Z]{2,4}(?:\.[\w]+[\d-]+|@\w+)?)?' \
        r'(?P<encoding>[.-_](?:(?:ISO|iso|UTF|utf)[\d-]+|(?:euc|EUC)[A-Z]+))?'

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

    def __init__(self):
        self._paths = LocaleCleanerPath(location='/')

    def add_xml(self, xml_node, parent=None):
        """Parses the xml data and adds nodes to the LocaleCleanerPath-tree"""

        if parent is None:
            parent = self._paths
        if xml_node.ELEMENT_NODE != xml_node.nodeType:
            return

        # if a pattern is supplied, we recurse into all matching subdirectories
        if 'regexfilter' == xml_node.nodeName:
            pre = xml_node.getAttribute('prefix') or ''
            post = xml_node.getAttribute('postfix') or ''
            parent.add_path_filter(pre, post)
        elif 'path' == xml_node.nodeName:
            if xml_node.hasAttribute('directoryregex'):
                pattern = xml_node.getAttribute('directoryregex')
                if '/' in pattern:
                    raise RuntimeError('directoryregex may not contain slashes.')
                pattern = re.compile(pattern)
                parent = parent.add_child(LocaleCleanerPath(pattern))

            # a combination of directoryregex and filter could be too much
            else:
                if xml_node.hasAttribute("location"):
                    # if there's a filter attribute, it should apply to this path
                    parent = parent.add_child(LocaleCleanerPath(xml_node.getAttribute('location')))

                if xml_node.hasAttribute('filter'):
                    userfilter = xml_node.getAttribute('filter')
                    if 1 != userfilter.count('*'):
                        raise RuntimeError(
                            "Filter string '%s' must contain the placeholder * exactly once" % userfilter)

                    # we can't use re.escape, because it escapes too much
                    (pre, post) = (re.sub(r'([\[\]()^$.])', r'\\\1', p)
                                   for p in userfilter.split('*'))
                    parent.add_path_filter(pre, post)
        else:
            raise RuntimeError(
                "Invalid node '%s', expected '<path>' or '<regexfilter>'" % xml_node.nodeName)

        # handle child nodes
        for child_xml in xml_node.childNodes:
            self.add_xml(child_xml, parent)

    def localization_paths(self, locales_to_keep):
        """Returns all localization items matching the previously added xml configuration"""
        if not locales_to_keep:
            raise RuntimeError('Found no locales to keep')
        purgeable_locales = frozenset((locale for locale in Locales.native_locale_names.keys()
                                       if locale not in locales_to_keep))

        for (locale, path) in self._paths.get_localizations('/'):
            if locale in purgeable_locales:
                yield path


def __is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns boolean whether application deskop entry file is broken"""
    if not config.has_option('Desktop Entry', 'Exec'):
        logger.info("is_broken_xdg_menu: missing required option 'Exec': '%s'", desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not FileUtilities.exe_exists(exe):
        logger.info("is_broken_xdg_menu: executable '%s' does not exist '%s'", exe, desktop_pathname)
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
            logger.info("is_broken_xdg_menu: executable '%s' does not exist '%s'", execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                logger.info("is_broken_xdg_menu: Windows executable '%s' does not exist '%s'",
                            windows_exe, desktop_pathname)
                return True
    return False


def is_unregistered_mime(mimetype):
    """Returns True if the MIME type is known to be unregistered. If
    registered or unknown, conservatively returns False."""
    try:
        from gi.repository import Gio
        if 0 == len(Gio.app_info_get_all_for_type(mimetype)):
            return True
    except ImportError:
        logger.warning('error calling gio.app_info_get_all_for_type(%s)', mimetype)
    return False


def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = bleachbit.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        logger.info("is_broken_xdg_menu: missing required section 'Desktop Entry': '%s'", pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        logger.info("is_broken_xdg_menu: missing required option 'Type': '%s'", pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
                not config.has_option('Desktop Entry', 'URL[$e]'):
            logger.info("is_broken_xdg_menu: missing required option 'URL': '%s'", pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            logger.info("is_broken_xdg_menu: missing required option 'MimeType': '%s'", pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if is_unregistered_mime(mimetype):
            logger.info("is_broken_xdg_menu: MimeType '%s' not registered '%s'", mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        logger.warning("unhandled type '%s': file '%s'", file_type, pathname)
        return False
    if __is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def is_running_darwin(exename, run_ps=None):
    if run_ps is None:
        def run_ps():
            subprocess.check_output(["ps", "aux", "-c"])
    try:
        processess = (re.split(r"\s+", p, 10)[10] for p in run_ps().split("\n") if p != "")
        next(processess)  # drop the header
        return exename in processess
    except IndexError:
        raise RuntimeError("Unexpected output from ps")


def is_running_linux(exename):
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


def is_running(exename):
    """Check whether exename is running"""
    if sys.platform.startswith('linux'):
        return is_running_linux(exename)
    elif 'darwin' == sys.platform:
        return is_running_darwin(exename)
    else:
        raise RuntimeError('unsupported platform for physical_free()')


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
        if re.match(whitelist_re, path) is None:  # for Slackware, Launchpad #367575
            yield path


def start_with_computer(enabled):
    """If enabled, create shortcut to start application with computer.
    If disabled, then delete the shortcut."""
    if not enabled:
        # User requests to not automatically start BleachBit
        if os.path.lexists(bleachbit.autostart_path):
            # Delete the shortcut
            FileUtilities.delete(bleachbit.autostart_path)
        return
    # User requests to automatically start BleachBit
    if os.path.lexists(bleachbit.autostart_path):
        # Already automatic, so exit
        return
    if not os.path.exists(bleachbit.launcher_path):
        logger.error('%s does not exist: ', bleachbit.launcher_path)
        return
    autostart_dir = os.path.dirname(bleachbit.autostart_path)
    if not os.path.exists(autostart_dir):
        General.makedirs(autostart_dir)
    import shutil
    shutil.copy(bleachbit.launcher_path, bleachbit.autostart_path)
    os.chmod(bleachbit.autostart_path, 0o755)
    if General.sudo_mode():
        General.chownself(bleachbit.autostart_path)


def start_with_computer_check():
    """Return boolean whether BleachBit will start with the computer"""
    return os.path.lexists(bleachbit.autostart_path)


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":",
                                                "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\", "/")
    return os.path.join(wineprefix, windows_pathname)


def run_cleaner_cmd(cmd, args, freed_space_regex=r'[\d.]+[kMGTE]?B?', error_line_regexes=None):
    """Runs a specified command and returns how much space was (reportedly) freed.
    The subprocess shouldn't need any user input and the user should have the
    necessary rights.
    freed_space_regex gets applied to every output line, if the re matches,
    add values captured by the single group in the regex"""
    if not FileUtilities.exe_exists(cmd):
        raise RuntimeError(_('Executable not found: %s') % cmd)
    freed_space_regex = re.compile(freed_space_regex)
    error_line_regexes = [re.compile(regex) for regex in error_line_regexes or []]

    env = {'LC_ALL': 'C', 'PATH': os.getenv('PATH')}
    output = subprocess.check_output([cmd] + args, stderr=subprocess.STDOUT,
                                     universal_newlines=True, env=env)
    freed_space = 0
    for line in output.split('\n'):
        m = freed_space_regex.match(line)
        if m is not None:
            freed_space += FileUtilities.human_to_bytes(m.group(1))
        for error_re in error_line_regexes:
            if error_re.search(line):
                raise RuntimeError('Invalid output from %s: %s' % (cmd, line))

    return freed_space


def journald_clean():
    """Clean the system journals"""
    freed_space_regex = '^Vacuuming done, freed ([\d.]+[KMGT]?) of archived journals on disk.$'
    return run_cleaner_cmd('journalctl', ['--vacuum-size=1'], freed_space_regex)


def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes) of freed space"""

    args = ['--yes', 'autoremove']
    # After this operation, 74.7MB disk space will be freed.
    freed_space_regex = r', ([\d.]+[a-zA-Z]{2}) disk space will be freed'
    try:
        return run_cleaner_cmd('apt-get', args, freed_space_regex, ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" % (' '.join(e.cmd), e.output))


def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes) of freed space"""
    try:
        return run_cleaner_cmd('apt-get', ['autoclean'], r'^Del .*\[([\d.]+[a-zA-Z]{2})}]', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" % (' '.join(e.cmd), e.output))


def apt_clean():
    """Run 'apt-get clean' and return the size in bytes of freed space"""
    old_size = get_apt_size()
    try:
        run_cleaner_cmd('apt-get', ['clean'], '^unused regex$', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" %
                           (' '.join(e.cmd), e.output))
    new_size = get_apt_size()
    return old_size - new_size


def get_apt_size():
    """Return the size of the apt cache (in bytes)"""
    (rc, stdout, stderr) = General.run_external(['apt-get', '-s', 'clean'])
    paths = re.findall('/[/a-z\.\*]+', stdout)
    return get_globs_size(paths)


def get_globs_size(paths):
    """Get the cumulative size (in bytes) of a list of globs"""
    total_size = 0
    for path in paths:
        from glob import iglob
        for p in iglob(path):
            total_size += FileUtilities.getsize(p)
    return total_size


def yum_clean():
    """Run 'yum clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/yum.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Yum"
        raise RuntimeError(msg)

    old_size = FileUtilities.getsizedir('/var/cache/yum')
    args = ['--enablerepo=*', 'clean', 'all']
    invalid = ['You need to be root', 'Cannot remove rpmdb file']
    run_cleaner_cmd('yum', args, '^unused regex$', invalid)
    new_size = FileUtilities.getsizedir('/var/cache/yum')
    return old_size - new_size


locales = Locales()
