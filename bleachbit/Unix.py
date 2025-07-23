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


"""
Integration specific to Unix-like operating systems
"""

import configparser
import glob
import logging
import os
import platform
import re
import shlex
import subprocess
import sys

import bleachbit
from bleachbit import FileUtilities, General
from bleachbit.General import get_real_uid, get_real_username
from bleachbit.FileUtilities import exe_exists
from bleachbit.Language import get_text as _, native_locale_names

logger = logging.getLogger(__name__)

try:
    Pattern = re.Pattern
except AttributeError:
    Pattern = re._pattern_type


JOURNALD_REGEX = r'^Vacuuming done, freed ([\d.]+[BKMGT]?) of archived journals (on disk|from [\w/]+).$'


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
        r"""Adds a filter consisting of a prefix and a postfix
        (e.g. 'foobar_' and '\.qm' to match 'foobar_en_US.utf-8.qm)"""
        try:
            regex = re.compile('^' + pre + Locales.localepattern + post + '$')
        except Exception as errormsg:
            raise RuntimeError(
                f"Malformed regex '{pre}' or '{post}': {errormsg}") from errormsg
        self.add_child(regex)

    def get_subpaths(self, basepath):
        """Returns direct subpaths for this object, i.e. either the named subfolder or all
        subfolders matching the pattern"""
        if isinstance(self.pattern, Pattern):
            return (os.path.join(basepath, p) for p in os.listdir(basepath)
                    if self.pattern.match(p) and os.path.isdir(os.path.join(basepath, p)))
        path = os.path.join(basepath, self.pattern)
        return [path] if os.path.isdir(path) else []

    def get_localizations(self, basepath):
        """Returns all localization items for this object and all descendant objects"""
        for path in self.get_subpaths(basepath):
            for child in self.children:
                if isinstance(child, LocaleCleanerPath):
                    yield from child.get_localizations(path)
                elif isinstance(child, Pattern):
                    for element in os.listdir(path):
                        match = child.match(element)
                        if match is not None:
                            yield (match.group('locale'),
                                   match.group('specifier'),
                                   os.path.join(path, element))


class Locales:
    """Find languages and localization files"""

    # The regular expression to match locale strings and extract the langcode.
    # See test_locale_regex() in tests/TestUnix.py for examples
    # This doesn't match all possible valid locale strings to avoid
    # matching filenames you might want to keep, e.g. the regex
    # to match jp.eucJP might also match jp.importantfileextension
    localepattern =\
        r'(?P<locale>[a-z]{2,3})' \
        r'(?P<specifier>[_-][A-Z]{2,4})?(?:\.[\w]+[\d-]+|@\w+)?' \
        r'(?P<encoding>[.-_](?:(?:ISO|iso|UTF|utf|us-ascii)[\d-]+|(?:euc|EUC)[A-Z]+))?'

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
                    raise RuntimeError(
                        'directoryregex may not contain slashes.')
                pattern = re.compile(pattern)
                parent = parent.add_child(LocaleCleanerPath(pattern))

            # a combination of directoryregex and filter could be too much
            else:
                if xml_node.hasAttribute("location"):
                    # if there's a filter attribute, it should apply to this path
                    parent = parent.add_child(LocaleCleanerPath(
                        xml_node.getAttribute('location')))

                if xml_node.hasAttribute('filter'):
                    userfilter = xml_node.getAttribute('filter')
                    if 1 != userfilter.count('*'):
                        raise RuntimeError(
                            f"Filter string '{userfilter}' must contain the placeholder * exactly once")

                    # we can't use re.escape, because it escapes too much
                    (pre, post) = (re.sub(r'([\[\]()^$.])', r'\\\1', p)
                                   for p in userfilter.split('*'))
                    parent.add_path_filter(pre, post)
        else:
            raise RuntimeError(
                f"Invalid node '{xml_node.nodeName}', expected '<path>' or '<regexfilter>'")

        # handle child nodes
        for child_xml in xml_node.childNodes:
            self.add_xml(child_xml, parent)

    def localization_paths(self, locales_to_keep):
        """Returns all localization items matching the previously added xml configuration"""
        purgeable_locales = get_purgeable_locales(locales_to_keep)

        for (locale, specifier, path) in self._paths.get_localizations('/'):
            specific = locale + (specifier or '')
            if specific in purgeable_locales or \
                    (locale in purgeable_locales and specific not in locales_to_keep):
                yield path


def _is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns whether application .desktop file is critically broken

    This function tests only .desktop files with Type=Application.
    """
    if not config.has_option('Desktop Entry', 'Exec'):
        logger.info(
            "is_broken_xdg_menu: missing required option 'Exec' in '%s'", desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not os.path.isabs(exe) and not os.environ.get('PATH'):
        raise RuntimeError(
            f"Cannot find executable '{exe}' because PATH environment variable is not set")
    if not FileUtilities.exe_exists(exe):
        logger.info(
            "is_broken_xdg_menu: executable '%s' does not exist in '%s'", exe, desktop_pathname)
        return True
    if 'env' == exe:
        # Wine v1.0 creates .desktop files like this
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program
        # Files\\foo\\foo.exe"
        exec_val = config.get('Desktop Entry', 'Exec')
        try:
            execs = shlex.split(exec_val)
        except ValueError as e:
            logger.info(
                "is_broken_xdg_menu: error splitting 'Exec' key '%s' in '%s'", e, desktop_pathname)
            return True
        wineprefix = None
        del execs[0]
        while True:
            if execs[0].find("=") < 0:
                break
            (name, value) = execs[0].split("=")
            if name == 'WINEPREFIX':
                wineprefix = value
            del execs[0]
        if not FileUtilities.exe_exists(execs[0]):
            logger.info(
                "is_broken_xdg_menu: executable '%s' does not exist in '%s'", execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                logger.info("is_broken_xdg_menu: Windows executable '%s' does not exist in '%s'",
                            windows_exe, desktop_pathname)
                return True
    return False


def find_available_locales():
    """Returns a list of available locales using locale -a"""
    rc, stdout, stderr = General.run_external(['locale', '-a'])
    if rc == 0:
        return stdout.strip().split('\n')

    logger.warning("Failed to get available locales: %s", stderr)
    return []


def find_best_locale(user_locale):
    """Find closest match to available locales"""
    assert isinstance(user_locale, str)
    if not user_locale:
        return 'C'
    if user_locale in ('C', 'C.utf8', 'POSIX'):
        return user_locale
    available_locales = find_available_locales()

    # If requesting a language like 'es' and current locale is compatible
    # like 'es_MX', then return that.
    # Import here for mock patch.
    import locale  # pylint: disable=import-outside-toplevel
    current_locale = locale.getlocale()[0]
    if current_locale and current_locale.startswith(user_locale.split('.')[0]):
        return '.'.join(locale.getlocale())

    # Check for exact match.
    if user_locale in available_locales:
        return user_locale

    # Next, match like 'en' to 'en_US.utf8' (if available) because
    # of preference for UTF-8.
    for avail_locale in available_locales:
        if avail_locale.startswith(user_locale) and avail_locale.endswith('.utf8'):
            return avail_locale

    # Next, match like 'en' to 'en_US' or 'en_US.iso88591'.
    for avail_locale in available_locales:
        if avail_locale.startswith(user_locale):
            return avail_locale

    return 'C'


def get_distribution_name_version_platform_freedesktop():
    """Returns the name and version of the distribution using
    platform.freedesktop_os_release()

    Example return value: 'ubuntu 24.10' or None

    Python 3.10 added platform.freedesktop_os_release().
    """
    if hasattr(platform, 'freedesktop_os_release'):
        try:
            release = platform.freedesktop_os_release()
        except FileNotFoundError:
            return None
        dist_id = release.get('ID')
        dist_version_id = release.get('VERSION_ID')
        if dist_id and dist_version_id:
            return f"{dist_id} {dist_version_id}"
    return None


def get_distribution_name_version_distro():
    """Returns the name and version of the distribution using the distro
    package

    Example return value: 'ubuntu 24.10' or None

    distro is a third-party package recommended here:
    https://docs.python.org/3.7/library/platform.html
    """
    try:
        # Import here in case of ImportError.
        import distro  # pylint: disable=import-outside-toplevel
        # example 'ubuntu 24.10'
        return distro.id() + ' ' + distro.version()
    except ImportError:
        return None


def get_distribution_name_version_os_release():
    """Returns the name and version of the distribution using /etc/os-release

    Example return value: 'ubuntu 24.10' or None
    """
    if not os.path.exists('/etc/os-release'):
        return None
    try:
        with open('/etc/os-release', 'r', encoding='utf-8') as f:
            os_release = {}
            for line in f:
                if '=' in line:
                    key, value = line.rstrip().split('=', 1)
                    os_release[key] = value.strip('"\'')
    except Exception as e:
        logger.debug("Error reading /etc/os-release: %s", e)
        return None
    if 'ID' in os_release and 'VERSION_ID' in os_release:
        dist_name = os_release['ID']
        return f"{dist_name} {os_release['VERSION_ID']}"
    return None


def get_distribution_name_version():
    """Returns the name and version of the distribution

    Depending on system capabilities, return value may be:
    * 'ubuntu 24.10'
    * 'Linux 6.12.3 (unknown distribution)'
    * 'Linux (unknown version and distribution)'

    Python 3.7 had platform.linux_distribution(), but it
    was removed in Python 3.8.
    """
    ret = get_distribution_name_version_platform_freedesktop()
    if ret:
        return ret
    ret = get_distribution_name_version_distro()
    if ret:
        return ret
    ret = get_distribution_name_version_os_release()
    if ret:
        return ret
    try:
        linux_version = platform.release()
        # example '6.12.3-061203-generic'
        linux_version = linux_version.split('-')[0]
        return f"Linux {linux_version} (unknown distribution)"
    except Exception as e1:
        logger.debug("Error calling platform.release(): %s", e1)
        try:
            linux_version = os.uname().release
            # example '6.12.3-061203-generic'
            linux_version = linux_version.split('-')[0]
            return f"Linux {linux_version} (unknown distribution)"
        except Exception as e2:
            logger.debug("Error calling os.uname(): %s", e2)
    return "Linux (unknown version and distribution)"


def get_purgeable_locales(locales_to_keep):
    """Returns all locales to be purged"""
    if not locales_to_keep:
        raise RuntimeError('Found no locales to keep')

    assert isinstance(locales_to_keep, list)

    # Start with all locales as potentially purgeable
    purgeable_locales = set(native_locale_names.keys())

    # Remove the locales we want to keep
    for keep in locales_to_keep:
        purgeable_locales.discard(keep)
        # If keeping a variant (e.g. 'en_US'), also keep the base locale (e.g. 'en')
        if '_' in keep:
            purgeable_locales.discard(keep[:keep.find('_')])
        # If keeping a base locale (e.g. 'en'), also keep all its variants (e.g. 'en_US')
        if '_' not in keep:
            purgeable_locales = {locale for locale in purgeable_locales
                                 if not locale.startswith(keep + '_')}

    return frozenset(purgeable_locales)


def is_unregistered_mime(mimetype):
    """Returns True if the MIME type is known to be unregistered. If
    registered or unknown, conservatively returns False."""
    try:
        from gi.repository import Gio  # pylint: disable=import-outside-toplevel
        if 0 == len(Gio.app_info_get_all_for_type(mimetype)):
            return True
    except ImportError:
        logger.warning(
            'error calling gio.app_info_get_all_for_type(%s)', mimetype)
    return False


def is_broken_xdg_desktop(pathname):
    """Returns whether the given XDG .desktop file is critically broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = bleachbit.RawConfigParser()
    try:
        config.read(pathname)
    except UnicodeDecodeError:
        logger.info(
            "is_broken_xdg_menu: cannot decode file: '%s'", pathname)
        return True
    except (configparser.Error) as e:
        logger.info(
            "is_broken_xdg_menu: %s: '%s'", e, pathname)
        return True
    if not config.has_section('Desktop Entry'):
        logger.info(
            "is_broken_xdg_menu: missing required section 'Desktop Entry': '%s'", pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        logger.info(
            "is_broken_xdg_menu: missing required option 'Type': '%s'", pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
                not config.has_option('Desktop Entry', 'URL[$e]'):
            logger.info(
                "is_broken_xdg_menu: missing required option 'URL': '%s'", pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            logger.info(
                "is_broken_xdg_menu: missing required option 'MimeType': '%s'", pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if is_unregistered_mime(mimetype):
            logger.info(
                "is_broken_xdg_menu: MimeType '%s' not registered '%s'", mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        logger.warning("unhandled type '%s': file '%s'", file_type, pathname)
        return False
    if _is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def is_process_running_ps_aux(exename, require_same_user):
    """Check whether exename is running by calling 'ps aux -c'

    exename: name of the executable
    require_same_user: if True, ignore processes run by other users

    When running under sudo, this uses the non-root username.
    """
    ps_out = subprocess.check_output(["ps", "aux", "-c"],
                                     universal_newlines=True)
    first_line = ps_out.split('\n', maxsplit=1)[0].strip()
    if "USER" not in first_line or "COMMAND" not in first_line:
        raise RuntimeError("Unexpected ps header format")

    for line in ps_out.split("\n")[1:]:
        parts = line.split()
        if len(parts) < 11:
            continue
        process_user = parts[0]
        process_cmd = parts[10]
        if process_cmd != exename:
            continue
        if not require_same_user or process_user == get_real_username():
            return True
    return False


def is_process_running_linux(exename, require_same_user):
    """Check whether exename is running

    The exename is checked two different ways.

    When running under sudo, this uses the non-root user ID.
    """
    for filename in glob.iglob("/proc/*/exe"):
        does_exe_match = False
        try:
            target = os.path.realpath(filename)
        except TypeError:
            # happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            pass
        except OSError:
            # 13 = permission denied
            pass
        else:
            # Google Chrome 74 on Ubuntu 19.04 shows up as
            # /opt/google/chrome/chrome (deleted)
            found_exename = os.path.basename(target).replace(' (deleted)', '')
            does_exe_match = exename == found_exename

        if not does_exe_match:
            with open(os.path.join(os.path.dirname(filename), 'stat'), 'r', encoding='utf-8') as stat_file:
                proc_name = stat_file.read().split()[1].strip('()')
                if proc_name == exename:
                    does_exe_match = True
                else:
                    continue

        if not require_same_user:
            return True

        try:
            uid = os.stat(os.path.dirname(filename)).st_uid
        except OSError:
            # permission denied means not the same user
            continue
        # In case of sudo, use the regular user's ID.
        if uid == get_real_uid():
            return True
    return False


def is_process_running(exename, require_same_user):
    """Check whether exename is running

    exename: name of the executable
    require_same_user: if True, ignore processes run by other users

    """
    if sys.platform == 'linux':
        return is_process_running_linux(exename, require_same_user)
    if sys.platform == 'darwin' or sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
        return is_process_running_ps_aux(exename, require_same_user)
    raise RuntimeError('unsupported platform for is_process_running()')


def rotated_logs():
    """Yield a list of rotated (i.e., old) logs in /var/log/

    See:
    https://bugs.launchpad.net/bleachbit/+bug/367575
    https://github.com/bleachbit/bleachbit/issues/1744
    """
    whitelists = [re.compile(r'/var/log/(removed_)?(packages|scripts)'),
                  re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')]
    positive_re = re.compile(r'(\.(\d+|bz2|gz|xz|old)|\-\d{8}?)')

    for path in bleachbit.FileUtilities.children_in_directory('/var/log'):
        whitelist_match = False
        for whitelist in whitelists:
            if whitelist.search(path) or bleachbit.FileUtilities.whitelisted(path):
                whitelist_match = True
                break
        if whitelist_match:
            continue
        if positive_re.search(path):
            yield path


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
    error_line_regexes = [re.compile(regex)
                          for regex in error_line_regexes or []]

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
    try:
        return run_cleaner_cmd('journalctl', ['--vacuum-size=1'], JOURNALD_REGEX)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(e.cmd)}':\n{e.output}") from e


def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes) of freed space"""

    args = ['--yes', 'autoremove']
    # After this operation, 74.7MB disk space will be freed.
    # After this operation, 44.0 kB disk space will be freed.
    freed_space_regex = r'.*, ([\d.]+ ?[a-zA-Z]{2}) disk space will be freed.'
    try:
        return run_cleaner_cmd('apt-get', args, freed_space_regex, ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(e.cmd)}':\n{e.output}") from e


def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes) of freed space"""
    try:
        return run_cleaner_cmd('apt-get', ['autoclean'], r'^Del .*\[([\d.]+[a-zA-Z]{2})}]', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(e.cmd)}':\n{e.output}") from e


def apt_clean():
    """Run 'apt-get clean' and return the size in bytes of freed space"""
    old_size = get_apt_size()
    try:
        run_cleaner_cmd('apt-get', ['clean'], '^unused regex$', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(e.cmd)}':\n{e.output}") from e
    new_size = get_apt_size()
    return old_size - new_size


def get_apt_size():
    """Return the size of the apt cache (in bytes)"""
    (_rc, stdout, _stderr) = General.run_external(['apt-get', '-s', 'clean'])
    paths = re.findall(r'/[/a-z\.\*]+', stdout)
    return get_globs_size(paths)


def get_globs_size(paths):
    """Get the cumulative size (in bytes) of a list of globs"""
    total_size = 0
    for path in paths:
        for p in glob.iglob(path):
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


def dnf_clean():
    """Run 'dnf clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/dnf.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Dnf"
        raise RuntimeError(msg)

    old_size = FileUtilities.getsizedir('/var/cache/dnf')
    args = ['--enablerepo=*', 'clean', 'all']
    invalid = ['You need to be root', 'Cannot remove rpmdb file']
    run_cleaner_cmd('dnf', args, '^unused regex$', invalid)
    new_size = FileUtilities.getsizedir('/var/cache/dnf')

    return old_size - new_size


units = {"B": 1, "k": 10**3, "M": 10**6, "G": 10**9}


def parse_size(size):
    """Parse the size returned by dnf"""
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * units[unit])


def dnf_autoremove():
    """Run 'dnf autoremove' and return size in bytes recovered."""
    if os.path.exists('/var/run/dnf.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Dnf"
        raise RuntimeError(msg)
    cmd = ['dnf', '-y', 'autoremove']
    (rc, stdout, stderr) = General.run_external(cmd)
    freed_bytes = 0
    allout = stdout + stderr
    if 'Error: This command has to be run under the root user.' in allout:
        raise RuntimeError('dnf autoremove requires root permissions')
    if rc > 0:
        raise RuntimeError(f'dnf autoremove raised error {rc}: {stderr}')

    cregex = re.compile(r"Freed space: ([\d.]+[\s]+[BkMG])")
    match = cregex.search(allout)
    if match:
        freed_bytes = parse_size(match.group(1))
    logger.debug(
        'dnf_autoremove >> total freed bytes: %s', freed_bytes)
    return freed_bytes


def pacman_cache():
    """Clean cache in pacman"""
    if os.path.exists('/var/lib/pacman/db.lck'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "pacman"
        raise RuntimeError(msg)
    if not exe_exists('paccache'):
        raise RuntimeError('paccache not found')
    cmd = ['paccache', '-rk0']
    (rc, stdout, stderr) = General.run_external(cmd)
    if rc > 0:
        raise RuntimeError(f'paccache raised error {rc}: {stderr}')
    # parse line like this: "==> finished: 3 packages removed (42.31 MiB freed)"
    cregex = re.compile(r"==> finished: ([\d.]+) packages removed \(([\d.]+[\s]+[BkMG]) freed)")
    match = cregex.search(stdout)
    if match:
        return parse_size(match.group(2))
    return 0


def has_gui():
    """Return True if the GUI is available"""
    assert os.name == 'posix'
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        return False
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        return True
    except ImportError:
        return False


def is_unix_display_protocol_wayland():
    """Return True if the display protocol is Wayland."""
    assert os.name == 'posix'
    if 'XDG_SESSION_TYPE' in os.environ:
        if os.environ['XDG_SESSION_TYPE'] == 'wayland':
            return True
        # If not wayland, then x11, mir, etc.
        return False
    if 'WAYLAND_DISPLAY' in os.environ:
        return True
    # Ubuntu 24.10 showed "ubuntu-xorg".
    # openSUSE Tumbleweed and Fedora 41 showed "gnome".
    # Fedora 41 also showed "plasma".
    if os.environ.get('DESKTOP_SESSION') in ('ubuntu-xorg', 'gnome', 'plasma'):
        return False
    # Wayland (Ubuntu 23.10) sets DISPLAY=:0 like x11, so do not check DISPLAY.
    try:
        (rc, stdout, _stderr) = General.run_external(['loginctl'])
    except FileNotFoundError:
        return False
    if rc != 0:
        logger.warning('logintctl returned rc %s', rc)
        return False
    try:
        session = stdout.split('\n')[1].strip().split(' ')[0]
    except (IndexError, ValueError):
        logger.warning('unexpected output from loginctl: %s', stdout)
        return False
    if not session.isdigit():
        logger.warning('unexpected session loginctl: %s', session)
        return False
    result = General.run_external(
        ['loginctl', 'show-session', session, '-p', 'Type'])
    return 'wayland' in result[1].lower()


def root_is_not_allowed_to_X_session():
    assert os.name == 'posix'
    result = General.run_external(['xhost'], clean_env=False)
    xhost_returned_error = result[0] == 1
    return xhost_returned_error


def is_display_protocol_wayland_and_root_not_allowed():
    """Return True if the display protocol is Wayland and root is not allowed to X session"""
    try:
        is_wayland = bleachbit.Unix.is_unix_display_protocol_wayland()
    except Exception as e:
        logger.exception(e)
        return False
    return (
        is_wayland and
        os.environ.get('USER') == 'root' and
        bleachbit.Unix.root_is_not_allowed_to_X_session()
    )


locales = Locales()
