
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
import sys

# local
import bleachbit
from bleachbit.General import get_executable

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
    from collections import OrderedDict
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

    import sqlite3
    info['SQLite version'] = sqlite3.sqlite_version

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
