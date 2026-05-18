# -*- coding: future_fstrings -*-
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
    s = f"BleachBit version {bleachbit.APP_VERSION}"

    try:
        from bleachbit.Revision import revision
        s += f'\nGit revision {revision}'
    except ImportError:
        pass
    try:
        from bleachbit.Revision import build_number
        s += f'\nBuild number {build_number}'
    except ImportError:
        pass
    try:
        import gi  # pylint: disable=import-error
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk  # pylint: disable=import-error
        s += f'\nGTK version {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}'
        s += f'\nGTK theme = {Gtk.Settings.get_default().get_property("gtk-theme-name")}'
        s += f'\nGTK icon theme = {Gtk.Settings.get_default().get_property("gtk-icon-theme-name")}'
        s += f'\nGTK prefer dark theme = {Gtk.Settings.get_default().get_property("gtk-application-prefer-dark-theme")}'
    except ImportError:
        pass

    s += f"\nSQLite version {sqlite3.sqlite_version}"

    # this section is for variables defined in __init__.py
    s += f"\nlocal_cleaners_dir = {bleachbit.local_cleaners_dir}"
    s += f"\nlocale_dir = {bleachbit.locale_dir}"
    s += f"\noptions_dir = {bleachbit.options_dir}"
    s += f"\npersonal_cleaners_dir = {bleachbit.personal_cleaners_dir}"
    s += f"\nsystem_cleaners_dir = {bleachbit.system_cleaners_dir}"

    # this section is for information about the system environment
    s += f"\nlocale.getdefaultlocale = {str(locale.getdefaultlocale())}"
    envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
            'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    for env in envs:
        s += f"\nos.getenv('{env}') = {os.getenv(env)}"
    s += f"\nos.path.expanduser('~') = {os.path.expanduser('~')}"
    s += f"\nplatform.win32_ver[1]() = {platform.win32_ver()[1]}"
    s += f"\nplatform.platform = {platform.platform()}"
    s += f"\nplatform.version = {platform.version()}"
    s += f"\nsys.argv = {sys.argv}"
    s += f"\nsys.executable = {sys.executable}"
    s += f"\nsys.version = {sys.version}"
    s += f"\nwin32com.shell.shell.IsUserAnAdmin() = {shell.IsUserAnAdmin()}"
    s += f"\n__file__ = {__file__}"

    return s
