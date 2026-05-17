# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Show system information
"""

import locale
import os
import platform
import sqlite3
import sys

from win32com.shell import shell

import bleachbit


def get_system_information():
    """Return system information as a string"""
    # this section is for application and library versions
    s = "BleachBit version %s" % bleachbit.APP_VERSION

    try:
        from bleachbit.Revision import revision
        s += '\nGit revision %s' % revision
    except ImportError:
        pass
    try:
        from bleachbit.Revision import build_number
        s += '\nBuild number %s' % build_number
    except ImportError:
        pass
    try:
        import gi  # pylint: disable=import-error
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk  # pylint: disable=import-error
        s += '\nGTK version {0}.{1}.{2}'.format(
            Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        s += '\nGTK theme = %s' % Gtk.Settings.get_default().get_property('gtk-theme-name')
        s += '\nGTK icon theme = %s' % Gtk.Settings.get_default().get_property('gtk-icon-theme-name')
        s += '\nGTK prefer dark theme = %s' % Gtk.Settings.get_default().get_property('gtk-application-prefer-dark-theme')
    except ImportError:
        pass

    s += "\nSQLite version %s" % sqlite3.sqlite_version

    # this section is for variables defined in __init__.py
    s += "\nlocal_cleaners_dir = %s" % bleachbit.local_cleaners_dir
    s += "\nlocale_dir = %s" % bleachbit.locale_dir
    s += "\noptions_dir = %s" % bleachbit.options_dir
    s += "\npersonal_cleaners_dir = %s" % bleachbit.personal_cleaners_dir
    s += "\nsystem_cleaners_dir = %s" % bleachbit.system_cleaners_dir

    # this section is for information about the system environment
    s += "\nlocale.getdefaultlocale = %s" % str(locale.getdefaultlocale())
    envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
            'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    for env in envs:
        s += "\nos.getenv('%s') = %s" % (env, os.getenv(env))
    s += "\nos.path.expanduser('~') = %s" % os.path.expanduser('~')
    s += "\nplatform.win32_ver[1]() = %s" % platform.win32_ver()[1]
    s += "\nplatform.platform = %s" % platform.platform()
    s += "\nplatform.version = %s" % platform.version()
    s += "\nsys.argv = %s" % sys.argv
    s += "\nsys.executable = %s" % sys.executable
    s += "\nsys.version = %s" % sys.version
    s += "\nwin32com.shell.shell.IsUserAnAdmin() = %s" % shell.IsUserAnAdmin()
    s += "\n__file__ = %s" % __file__

    return s
