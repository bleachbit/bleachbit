# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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


import Common
import locale
import os
import platform
import sys

if 'nt' == os.name:
    from win32com.shell import shell


def diagnostic_info():
    """Return diagnostic information as a string"""
    s = "BleachBit version %s" % Common.APP_VERSION
    try:
        import gtk
        s += '\nGTK version %s' % '.'.join([str(x) for x in gtk.gtk_version])
    except:
        pass
    s += "\nlocal_cleaners_dir = %s" % Common.local_cleaners_dir
    s += "\nlocale_dir = %s" % Common.locale_dir
    s += "\noptions_dir = %s" % Common.options_dir.decode(Common.FSE)
    s += "\npersonal_cleaners_dir = %s" % Common.personal_cleaners_dir.decode(Common.FSE)
    s += "\nsystem_cleaners_dir = %s" % Common.system_cleaners_dir
    s += "\nlocale.getdefaultlocale = %s" % str(locale.getdefaultlocale())
    if 'posix' == os.name:
        envs = ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID')
    if 'nt' == os.name:
        envs = ('APPDATA', 'LocalAppData', 'LocalAppDataLow', 'Music',
                'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    for env in envs:
        if os.getenv(env):
            s += "\nos.getenv('%s') = %s" % (env, os.getenv(env).decode(Common.FSE))
        else:
            s += "\nos.getenv('%s') = %s" % (env, os.getenv(env))
    s += "\nos.path.expanduser('~') = %s" % Common.expanduser('~').decode(Common.FSE)
    if sys.platform.startswith('linux'):
        if hasattr(platform, 'linux_distribution'):
            s += "\nplatform.linux_distribution() = %s" % str(
                platform.linux_distribution())
        else:
            s += "\nplatform.dist() = %s" % str(platform.dist())
            
    # Mac Version Name - Dictonary "masosx_dict"
    macosx_dict = {'5':'Lepoard','6':'Snow Lepoard','7':'Lion','8':'Mountain Lion','9':'Mavericks','10':'Yosemite','11':'El Capitan','12':'Sierra'}

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
