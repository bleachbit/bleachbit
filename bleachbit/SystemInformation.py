# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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

import locale
import os
import platform
import sys

import bleachbit

if 'nt' == os.name:
    from win32com.shell import shell


def get_system_information():
    """Return system information as a string"""
    # this section is for application and library versions
    s = f"BleachBit version {bleachbit.APP_VERSION}"

    try:
        # Linux tarball will have a revision but not build_number
        from bleachbit.Revision import revision
        s += f'\nGit revision {revision}'
    except:
        pass
    try:
        from bleachbit.Revision import build_number
        s += f'\nBuild number {build_number}'
    except:
        pass
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        s += '\nGTK version {0}.{1}.{2}'.format(
            Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        s += f"\nGTK theme = {Gtk.Settings.get_default().get_property('gtk-theme-name')}"
        s += f"\nGTK icon theme = {Gtk.Settings.get_default().get_property('gtk-icon-theme-name')}"
        s += f"\nGTK prefer dark theme = {Gtk.Settings.get_default().get_property('gtk-application-prefer-dark-theme')}"
    except:
        pass
    import sqlite3
    s += f"\nSQLite version {sqlite3.sqlite_version}"

    # this section is for variables defined in __init__.py
    s += f"\nlocal_cleaners_dir = {bleachbit.local_cleaners_dir}"
    s += f"\nlocale_dir = {bleachbit.locale_dir}"
    s += f"\noptions_dir = {bleachbit.options_dir}"
    s += f"\npersonal_cleaners_dir = {bleachbit.personal_cleaners_dir}"
    s += f"\nsystem_cleaners_dir = {bleachbit.system_cleaners_dir}"

    # this section is for information about the system environment
    s += f"\nlocale.getdefaultlocale = {str(locale.getdefaultlocale())}"
    if 'posix' == os.name:
        envs = ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID')
    elif 'nt' == os.name:
        envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
                'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    for env in envs:
        s += f"\nos.getenv('{env}') = {os.getenv(env)}"
    s += f"\nos.path.expanduser('~') = {os.path.expanduser('~')}"
    if sys.platform.startswith('linux'):
        s += f"\nplatform.linux_distribution() = {str(platform.linux_distribution())}"

    # Mac Version Name - Dictionary
    macosx_dict = {'5': 'Leopard', '6': 'Snow Leopard', '7': 'Lion', '8': 'Mountain Lion',
                   '9': 'Mavericks', '10': 'Yosemite', '11': 'El Capitan', '12': 'Sierra'}

    if sys.platform.startswith('darwin'):
        if hasattr(platform, 'mac_ver'):
            for key in macosx_dict:
                if (platform.mac_ver()[0].split('.')[1] == key):
                    s += "\nplatform.mac_ver() = %s" % str(
                        platform.mac_ver()[0] + " (" + macosx_dict[key] + ")")
        else:
            s += f"\nplatform.dist() = {str(platform.linux_distribution(full_distribution_name=0))}"

    if 'nt' == os.name:
        s += f"\nplatform.win32_ver[1]() = {platform.win32_ver()[1]}"
    s += f"\nplatform.platform = {platform.platform()}"
    s += f"\nplatform.version = {platform.version()}"
    s += f"\nsys.argv = {sys.argv}"
    s += f"\nsys.executable = {sys.executable}"
    s += f"\nsys.version = {sys.version}"
    if 'nt' == os.name:
        s += f"\nwin32com.shell.shell.IsUserAnAdmin() = {shell.IsUserAnAdmin()}"
    s += f"\n__file__ = {__file__}"

    return s
