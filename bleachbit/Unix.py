# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Integration specific to Unix-like operating systems
"""

import configparser
import glob
import logging
import os
import platform
import posixpath
import re
import shlex
import subprocess

import bleachbit
from bleachbit import FileUtilities, General
from bleachbit.FileUtilities import children_in_directory, exe_exists
from bleachbit.Language import get_text as _, native_locale_names
from bleachbit.VFS import RealVFS

logger = logging.getLogger(__name__)

# Cache for snapd_is_active() to avoid repeated systemctl calls.
_snapd_is_active_cache = None

try:
    Pattern = re.Pattern
except AttributeError:
    Pattern = re._pattern_type


JOURNALD_REGEX = r'^Vacuuming done, freed ([\d.]+[BKMGT]?) of archived journals (on disk|from [\w/]+).$'

_real_vfs = RealVFS()


class LocaleCleanerPath:
    """This represents a path with either a specific folder name or a folder name pattern.
    It also may contain several compiled regex patterns for localization items (folders or files)
    and additional LocaleCleanerPaths that get traversed when asked to supply a list of localization
    items"""

    def __init__(self, location, vfs=None):
        if location is None:
            raise RuntimeError("location is none")
        self.pattern = location
        self.children = []
        self._vfs = vfs

    def _get_vfs(self):
        return self._vfs if self._vfs is not None else _real_vfs

    def add_child(self, child):
        """Adds a child LocaleCleanerPath"""
        if isinstance(child, LocaleCleanerPath) and child._vfs is None:
            child._vfs = self._vfs
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
        vfs = self._get_vfs()
        if isinstance(self.pattern, Pattern):
            # posixpath is easy way to test also from Windows.
            return (posixpath.join(basepath, p) for p in vfs.listdir(basepath)
                    if self.pattern.match(p) and vfs.isdir(posixpath.join(basepath, p)))
        path = posixpath.join(basepath, self.pattern)
        return [path] if vfs.isdir(path) else []

    def get_localizations(self, basepath):
        """Returns all localization items for this object and all descendant objects"""
        vfs = self._get_vfs()
        for path in self.get_subpaths(basepath):
            for child in self.children:
                if isinstance(child, LocaleCleanerPath):
                    yield from child.get_localizations(path)
                elif isinstance(child, Pattern):
                    for element in vfs.listdir(path):
                        match = child.match(element)
                        if match is not None:
                            yield (match.group('locale'),
                                   match.group('specifier'),
                                   posixpath.join(path, element))


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
        r'(?P<encoding>[-._](?:(?:ISO|iso|UTF|utf|us-ascii)[\d-]+|(?:euc|EUC)[A-Z]+))?'

    def __init__(self, vfs=None):
        self._paths = LocaleCleanerPath(location='/', vfs=vfs)

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
    exec_val = config.get('Desktop Entry', 'Exec')
    try:
        exec_parts = shlex.split(exec_val)
    except ValueError as e:
        # Malformed quoting in the Exec value. Per the XDG Desktop Entry
        # spec this is undefined behavior; be conservative and keep the
        # file rather than risk deleting a working launcher.
        logger.warning(
            "is_broken_xdg_menu: cannot parse 'Exec' key (%s) in '%s'", e, desktop_pathname)
        return False
    if not exec_parts:
        logger.info(
            "is_broken_xdg_menu: empty 'Exec' value in '%s'", desktop_pathname)
        return True
    exe = exec_parts[0]
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
        execs = list(exec_parts)
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
        # Arch Linux omits VERSION_ID, so fall back to BUILD_ID.
        # Ubuntu has VERSION_ID but not BUILD_ID.
        dist_version_id = release.get('VERSION_ID') or release.get('BUILD_ID')
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
        # Arch Linux returns id='arch' and version=''.
        dist_version = distro.version()
        if dist_version:
            return distro.id() + ' ' + dist_version
    except ImportError:
        return None
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
    if 'ID' in os_release:
        dist_name = os_release['ID']
        # ArchLinux has BUILD_ID='rolling' but not VERSION_ID.
        # Ubuntu has VERSION_ID like '26.04' but does not have BUILD_ID.
        dist_version = os_release.get('VERSION_ID') or os_release.get('BUILD_ID')
        if dist_version:
            return f"{dist_name} {dist_version}"
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


def get_mount_points():
    """Return read-write mount points that may have trash"""
    try:
        import psutil # pylint: disable=import-outside-toplevel
    except ImportError:
        logger.warning('install psutil for better trash detection')
        return []
    mount_points = []
    try:
        for partition in psutil.disk_partitions():
            mountpoint = partition.mountpoint
            if re.match(r'^/(proc|sys|dev|run|boot)', mountpoint):
                continue
            if 'ro' in partition.opts.split(','):
                continue
            mount_points.append(mountpoint)
    except (OSError, psutil.Error) as e:
        logger.warning("Error getting mount points: %s", e)
    return mount_points

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


def get_trash_paths():
    """Iterate over all trash on POSIX systems"""
    # Import here to avoid a circular import.
    # pylint: disable=import-outside-toplevel
    from bleachbit import Command
    # macOS-style flat trash (non-recursive)
    dirname = os.path.expanduser("~/.Trash")
    for filename in children_in_directory(dirname, False):
        yield Command.Delete(filename)
    # Freedesktop trash spec directories
    # https://specifications.freedesktop.org/trash-spec/trashspec-1.0.html
    home_trash = os.path.join(
        os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')),
        'Trash')
    fallback_trash = os.path.expanduser('~/.local/share/Trash')
    trash_dirs = [home_trash]
    if home_trash != fallback_trash:
        trash_dirs.append(fallback_trash)
    # Snap apps store trash under ~/snap/<app>/<revision>/.local/share/Trash
    for d in glob.glob(os.path.expanduser("~/snap/*/*/.local/share/Trash")):
        # Do not follow revision symlinks. For example, current -> 238 would match twice.
        rev_dir = os.path.dirname(os.path.dirname(os.path.dirname(d)))
        if not os.path.islink(rev_dir):
            trash_dirs.append(d)
    # Per-mountpoint trash (method 1: .Trash/$uid, method 2: .Trash-$uid)
    uid = os.getuid()
    for mountpoint in get_mount_points():
        trash_dirs.append(os.path.join(mountpoint, '.Trash', str(uid)))
        trash_dirs.append(os.path.join(mountpoint, f'.Trash-{uid}'))
    # Deduplicate while preserving order
    seen = set()
    for trash_dir in trash_dirs:
        real_path = os.path.realpath(trash_dir)
        if real_path in seen:
            continue
        seen.add(real_path)
        for subdir in ('files', 'info', 'expunged'):
            dirname = os.path.join(trash_dir, subdir)
            for filename in children_in_directory(dirname, True):
                yield Command.Delete(filename)

def is_unregistered_mime(mimetype):
    """Returns True if the MIME type is known to be unregistered. If
    registered or unknown, conservatively returns False."""
    try:
        from bleachbit.GtkShim import Gio  # pylint: disable=import-outside-toplevel
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
    if not config.has_option('Desktop Entry', 'Name'):
        logger.info(
            "is_broken_xdg_menu: missing required option 'Name': '%s'", pathname)
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
    if 'application' == file_type:
        return _is_broken_xdg_desktop_application(config, pathname)
    logger.warning("unhandled type '%s': file '%s'", file_type, pathname)
    return False


def rotated_logs():
    """Yield a list of rotated (i.e., old) logs in /var/log/

    See:
    https://bugs.launchpad.net/bleachbit/+bug/367575
    https://github.com/bleachbit/bleachbit/issues/1744
    """
    keep_lists = [re.compile(r'/var/log/(removed_)?(packages|scripts)'),
                  re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')]
    positive_re = re.compile(r'(\.(\d+|bz2|gz|xz|old)|\-\d{8}?)')

    for path in bleachbit.FileUtilities.children_in_directory('/var/log'):
        if bleachbit.FileUtilities.whitelisted(path):
            continue
        if any(keep_list.search(path) for keep_list in keep_lists):
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
        return run_cleaner_cmd('apt-get', ['autoclean'], r'^Del .*\[([\d.]+ ?[a-zA-Z]{2})\]', ['^E: '])
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
    try:
        run_cleaner_cmd('yum', args, '^unused regex$', invalid)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(str(part) for part in e.cmd)}':\n{e.output}") from e
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
    try:
        run_cleaner_cmd('dnf', args, '^unused regex$', invalid)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error calling '{' '.join(str(part) for part in e.cmd)}':\n{e.output}") from e
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
    cregex = re.compile(
        r"==> finished: ([\d.]+) packages removed \(([\d.]+\s+[BkMG]) freed\)")
    match = cregex.search(stdout)
    if match:
        return parse_size(match.group(2))
    return 0


def snap_parse_list(stdout):
    """Parse output of `snap list --all`"""
    disabled_snaps = []
    lines = stdout.strip().split('\n')
    if not lines:
        return disabled_snaps
    # Example output: "No snaps are installed yet. Try 'snap install hello-world'."
    raw_header = lines[0]
    header = raw_header.lower()
    if 'no snaps' in header and 'install' in header:
        return disabled_snaps
    if "name" not in header or "rev" not in header or "notes" not in header:
        logger.warning(
            "Unexpected 'snap list --all' output; returning 0. First line: %r", raw_header)
        return disabled_snaps
    for line in lines[1:]:  # Skip header line
        parts = line.split()
        if len(parts) >= 4 and 'disabled' in line:
            snapname = parts[0]
            revision = parts[2]
            disabled_snaps.append((snapname, revision))
    return disabled_snaps


def snapd_is_active():
    """Return True if snap is installed and snapd is active.

    The result is cached in a module-level variable to avoid repeated
    systemctl calls during a single BleachBit run.
    """
    global _snapd_is_active_cache  # pylint: disable=global-statement
    if _snapd_is_active_cache is not None:
        return _snapd_is_active_cache
    if not exe_exists('snap'):
        _snapd_is_active_cache = False
        return False
    if not exe_exists('systemctl'):
        _snapd_is_active_cache = False
        return False
    # When snap is installed but snapd is inactive, then `snap list --all`
    # or `snap version` may have a long delay, so we check the service status first.
    try:
        (rc, _stdout, _stderr) = General.run_external(
            ['systemctl', 'is-active', '--quiet', 'snapd.socket'],
            timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning(
            'systemctl is-active snapd.socket timed out: it seems snap is installed but snapd is inactive')
        _snapd_is_active_cache = False
        return False
    except (FileNotFoundError, OSError) as exc:
        logger.warning('systemctl is-active snapd.socket failed: %s', exc)
        _snapd_is_active_cache = False
        return False
    _snapd_is_active_cache = rc == 0
    return _snapd_is_active_cache


def clear_snapd_cache():
    """Clear the snapd_is_active() cache."""
    global _snapd_is_active_cache  # pylint: disable=global-statement
    _snapd_is_active_cache = None


def snap_disabled_full(really_delete):
    """Remove disabled snaps"""
    assert isinstance(really_delete, bool)
    if not snapd_is_active():
        raise RuntimeError('snap not found or snapd is not active')

    # Get list of all snaps.
    cmd = ['snap', 'list', '--all']
    try:
        (rc, stdout, stderr) = General.run_external(
            cmd, clean_env=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            'snap list --all timed out after 15 seconds; is snapd running?') from exc
    if rc > 0:
        raise RuntimeError(f'snap list raised error {rc}: {stderr}')

    # Parse output to find disabled snaps.
    disabled_snaps = snap_parse_list(stdout)
    if not disabled_snaps:
        return 0

    # Remove disabled snaps.
    total_freed = 0
    for snapname, revision in disabled_snaps:
        # `snap info` returns info only about active snaps.
        # Instead, get size from the snap file directly.
        snap_file = f'/var/lib/snapd/snaps/{snapname}_{revision}.snap'
        if os.path.exists(snap_file):
            snap_size = os.path.getsize(snap_file)
            logger.debug('Found snap file: %s, size: %s',
                         snap_file, f"{snap_size:,}")
        else:
            logger.warning('Could not find snap file: %s', snap_file)
            snap_size = 0

        # Remove the snap revision
        if really_delete:
            # Consider there may be a slow system with a large snap.
            remove_cmd = ['snap', 'remove', snapname, f'--revision={revision}']
            try:
                (rc, _, remove_stderr) = General.run_external(
                    remove_cmd, clean_env=True, timeout=60)
            except subprocess.TimeoutExpired:
                logger.error(
                    'Timeout removing snap %s revision %s', snapname, revision)
                break
            if rc > 0:
                logger.error(
                    'Failed to remove snap %s revision %s: %s', snapname, revision, remove_stderr)
                break
            total_freed += snap_size
            logger.debug(
                'Removed snap %s revision %s, freed %s bytes', snapname, revision, snap_size)
        else:
            total_freed += snap_size

    return total_freed


def snap_disabled_clean():
    """Remove disabled snaps"""
    return snap_disabled_full(True)


def snap_disabled_preview():
    """Preview snaps that would be removed"""
    return snap_disabled_full(False)


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
    """Return True if root is not allowed to X session.

    This function is called only with root on Wayland.
    """
    assert os.name == 'posix'
    try:
        result = General.run_external(['xhost'], clean_env=False)
        xhost_returned_error = result[0] == 1
        return xhost_returned_error
    except (FileNotFoundError, OSError) as exc:
        logger.debug(
            'xhost check failed (%s); assuming root is not allowed to X session', exc)
        return True


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


def flush_dns():
    """Flush the DNS resolver cache

    Returns 0 on success.
    Raises RuntimeError on failure.
    """
    if exe_exists('resolvectl'):
        args = ['resolvectl', 'flush-caches']
    elif exe_exists('systemd-resolve'):
        args = ['systemd-resolve', '--flush-caches']
    else:
        raise RuntimeError('Neither resolvectl nor systemd-resolve found')
    (rc, stdout, stderr) = General.run_external(args)
    if 0 != rc:
        # If service is not found, then there may be nothing to flush.
        if 'Unit dbus-org.freedesktop.resolve1.service not found' in stderr:
            logger.warning(stderr)
            return 0
        raise RuntimeError(
            f'Command: {args}\nReturn code: {rc}\nStdout: {stdout}\nStderr: {stderr}')
    return 0


locales = Locales()
