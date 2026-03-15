
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
Show system information
"""

# standard library
import logging
import locale
import os
import platform
import re
import sys
from collections import OrderedDict

# local
import bleachbit
from bleachbit.General import get_executable, get_real_uid

logger = logging.getLogger(__name__)


def get_gtk_info():
    """Get dictionary of information about GTK"""
    # pylint: disable=import-outside-toplevel
    from bleachbit.GtkShim import gi, Gtk, HAVE_GTK, get_gtk_unavailable_reason

    info = {}
    if gi is None:
        logger.debug('gi module not available')
        return info

    if not hasattr(gi, 'version_info'):
        logger.debug('gi.version_info not available')
    else:
        info['gi.version'] = gi.__version__

    if not HAVE_GTK:
        logger.debug('GTK not available: %s', get_gtk_unavailable_reason())
        return info

    settings = Gtk.Settings.get_default()
    if not settings:
        logger.debug('GTK settings not found')
        return info

    info['GTK version'] = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
    info['GTK theme'] = settings.get_property('gtk-theme-name')
    info['GTK icon theme'] = settings.get_property('gtk-icon-theme-name')
    info['GTK prefer dark theme'] = settings.get_property(
        'gtk-application-prefer-dark-theme')

    return info


def _get_home_dirs_to_anonymize():
    """Return home directories that should be anonymized."""
    home_dirs = []
    home_dir = os.path.expanduser('~') or ''
    home_dirs.append(home_dir)

    if os.name == 'posix':
        real_home_dir = ''
        try:
            # reminder: pwd is not available on Windows
            import pwd  # pylint: disable=import-outside-toplevel
            real_home_dir = pwd.getpwuid(get_real_uid()).pw_dir
        except (ImportError, KeyError, RuntimeError, ValueError):
            pass
        home_dirs.append(real_home_dir)

    # Filter out root directories and duplicates
    filtered_dirs = []
    for d in home_dirs:
        if not d:
            continue
        if d in ('/', '/root'):
            continue
        if d not in filtered_dirs:
            filtered_dirs.append(d)

    return filtered_dirs


def anonymize_system_information(text):
    """Anonymize non-generic username in system information text.

    root is not anonymized.
    """
    home_dirs = _get_home_dirs_to_anonymize()
    home_token = '~' if os.name == 'posix' else '%userprofile%'

    def mask_user_line(line):
        """Mask username for environment variables"""
        if not (line.startswith('os.getenv(LOGNAME)') or line.startswith('os.getenv(USER)')):
            return line
        key, _, value = line.partition(' = ')
        if value and value != 'None' and value.strip() != 'root':
            # replace specific non-root username with *non-root*
            return f'{key} = *non-root*'
        return line

    anonymized_lines = []
    for line in text.split('\n'):
        for home_dir in home_dirs:
            if os.name == 'nt':
                # Windows paths are case-insensitive
                line = re.sub(re.escape(home_dir), home_token,
                              line, flags=re.IGNORECASE)
            else:
                line = line.replace(home_dir, home_token)
        anonymized_lines.append(mask_user_line(line))

    return '\n'.join(anonymized_lines)


def get_version(four_parts=False):
    """Return version information as a string.

    CI builds will have an integer build number.

    If four_parts is True, always return a four-part version string.
    If False, return three or four parts, depending on available information.
    """
    build_number_env = os.getenv('APPVEYOR_BUILD_NUMBER')
    build_number_src = None
    try:
        # pylint: disable=import-outside-toplevel
        from bleachbit.Revision import build_number as build_number_import
        build_number_src = build_number_import
    except ImportError:
        pass

    build_number = build_number_src or build_number_env
    if not build_number:
        if not four_parts:
            return bleachbit.APP_VERSION
        return f'{bleachbit.APP_VERSION}.0'
    assert build_number.isdigit()
    return f'{bleachbit.APP_VERSION}.{build_number}'


def get_system_information():
    """Return system information as a string."""
    info = OrderedDict()

    # Application and library versions
    info['BleachBit version'] = get_version()

    try:
        # CI builds and Linux tarball will have a revision.
        # pylint: disable=import-outside-toplevel
        from bleachbit.Revision import revision
        info['Git revision'] = revision
    except ImportError:
        pass

    info.update(get_gtk_info())

    # Variables defined in __init__.py
    info['local_cleaners_dir'] = bleachbit.local_cleaners_dir
    info['locale_dir'] = bleachbit.locale_dir
    info['options_dir'] = bleachbit.options_dir
    info['personal_cleaners_dir'] = bleachbit.personal_cleaners_dir
    info['system_cleaners_dir'] = bleachbit.system_cleaners_dir

    # System environment information
    info['locale.getlocale'] = str(locale.getlocale())

    # Environment variables
    if 'posix' == os.name:
        envs = ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID')
    elif 'nt' == os.name:
        envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
                'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    else:
        envs = ()

    for env in envs:
        info[f'os.getenv({env})'] = os.getenv(env)

    info['os.path.expanduser(~")'] = os.path.expanduser('~')

    # Mac Version Name - Dictionary
    macosx_dict = {'5': 'Leopard', '6': 'Snow Leopard', '7': 'Lion', '8': 'Mountain Lion',
                   '9': 'Mavericks', '10': 'Yosemite', '11': 'El Capitan', '12': 'Sierra'}

    if sys.platform == 'linux':
        from bleachbit.Unix import get_distribution_name_version
        info['get_distribution_name_version()'] = get_distribution_name_version()
    elif sys.platform.startswith('darwin'):
        if hasattr(platform, 'mac_ver'):
            mac_version = platform.mac_ver()[0]
            version_minor = mac_version.split('.')[1]
            if version_minor in macosx_dict:
                info['platform.mac_ver()'] = f'{mac_version} ({macosx_dict[version_minor]})'
    else:
        info['platform.uname().version'] = platform.uname().version

    # System information
    info['sys.argv'] = sys.argv
    info['sys.executable'] = get_executable()
    info['sys.version'] = sys.version
    if 'nt' == os.name:
        from win32com.shell import shell
        info['IsUserAnAdmin()'] = shell.IsUserAnAdmin()
    info['__file__'] = __file__

    # Render the information as a string
    return '\n'.join(f'{key} = {value}' for key, value in info.items())
