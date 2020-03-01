# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
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
Show diagnostic information
"""

import bleachbit

import locale
import os
import platform
import sys

if 'nt' == os.name:
    from win32com.shell import shell


def diagnostic_info():
    """Return diagnostic information as a string"""
    # this section is for application and library versions
    s = "BleachBit version %s" % bleachbit.APP_VERSION

    try:
        # Linux tarball will have a revision but not build_number
        from bleachbit.Revision import revision
        s += '\nGit revision %s' % revision
    except:
        pass
    try:
        from bleachbit.Revision import build_number
        s += '\nBuild number %s' % build_number
    except:
        pass
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        s += '\nGTK version {0}.{1}.{2}'.format(
            Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        s += '\nGTK theme = %s' % Gtk.Settings.get_default().get_property('gtk-theme-name')
        s += '\nGTK icon theme = %s' % Gtk.Settings.get_default().get_property('gtk-icon-theme-name')
        s += '\nGTK prefer dark theme = %s' % Gtk.Settings.get_default().get_property('gtk-application-prefer-dark-theme')
    except:
        pass
    import sqlite3
    s += "\nSQLite version %s" % sqlite3.sqlite_version

    # this section is for variables defined in __init__.py
    s += "\nlocal_cleaners_dir = %s" % bleachbit.local_cleaners_dir
    s += "\nlocale_dir = %s" % bleachbit.locale_dir
    s += "\noptions_dir = %s" % bleachbit.options_dir
    s += "\npersonal_cleaners_dir = %s" % bleachbit.personal_cleaners_dir
    s += "\nsystem_cleaners_dir = %s" % bleachbit.system_cleaners_dir

    # this section is for information about the system environment
    s += "\nlocale.getdefaultlocale = %s" % str(locale.getdefaultlocale())
    if 'posix' == os.name:
        envs = ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID')
    if 'nt' == os.name:
        envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
                'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    for env in envs:
        s += "\nos.getenv('%s') = %s" % (env, os.getenv(env))
    s += "\nos.path.expanduser('~') = %s" % os.path.expanduser('~')
    if sys.platform.startswith('linux'):
        if hasattr(platform, 'linux_distribution'):
            s += "\nplatform.linux_distribution() = %s" % str(
                platform.linux_distribution())
        else:
            s += "\nplatform.dist() = %s" % str(platform.dist())

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
            s += "\nplatform.dist() = %s" % str(platform.dist())

    if 'nt' == os.name:
        s += "\nplatform.win32_ver[1]() = %s" % platform.win32_ver()[1]
    s += "\nplatform.platform = %s" % platform.platform()
    s += "\nplatform.version = %s" % platform.version()
    s += "\nsys.argv = %s" % sys.argv
    s += "\nsys.executable = %s" % sys.executable
    s += "\nsys.version = %s" % sys.version
    if 'nt' == os.name:
        s += "\nwin32com.shell.shell.IsUserAnAdmin() = %s" % shell.IsUserAnAdmin(
        )
    s += "\n__file__ = %s" % __file__

    return s
