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
Code that is commonly shared throughout BleachBit
"""

import gettext
import locale
import os
import re
import sys

from bleachbit import Log
from configparser import RawConfigParser, NoOptionError, SafeConfigParser

APP_VERSION = "3.9.0"
APP_NAME = "BleachBit"
APP_URL = "https://www.bleachbit.org"

socket_timeout = 10

if sys.version_info < (3,0,0):
    print('BleachBit no longer supports Python 2.x.')
    sys.exit(1)

if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
    stdout_encoding = 'utf-8'
else:
    stdout_encoding = sys.stdout.encoding
    if 'win32' == sys.platform:
        import win_unicode_console
        win_unicode_console.enable()

logger = Log.init_log()

# Setting below value to false disables update notification (useful
# for packages in repositories).
online_update_notification_enabled = True

#
# Paths
#

# Windows
bleachbit_exe_path = None
if hasattr(sys, 'frozen'):
    # running frozen in py2exe
    bleachbit_exe_path = os.path.dirname(sys.executable)
else:
    # __file__ is absolute path to __init__.py
    bleachbit_exe_path = os.path.dirname(os.path.dirname(__file__))

# license
license_filename = None
license_filenames = ('/usr/share/common-licenses/GPL-3',  # Debian, Ubuntu
                     # Microsoft Windows
                     os.path.join(bleachbit_exe_path, 'COPYING'),
                     '/usr/share/doc/bleachbit-' + APP_VERSION + '/COPYING',  # CentOS, Fedora, RHEL
                     '/usr/share/licenses/bleachbit/COPYING',  # Fedora 21+, RHEL 7+
                     '/usr/share/doc/packages/bleachbit/COPYING',  # OpenSUSE 11.1
                     '/usr/pkg/share/doc/bleachbit/COPYING',  # NetBSD 5
                     '/usr/share/licenses/common/GPL3/license.txt')  # Arch Linux
for lf in license_filenames:
    if os.path.exists(lf):
        license_filename = lf
        break

# configuration
portable_mode = False
options_dir = None
if 'posix' == os.name:
    options_dir = os.path.expanduser("~/.config/bleachbit")
elif 'nt' == os.name:
    if os.path.exists(os.path.join(bleachbit_exe_path, 'bleachbit.ini')):
        # portable mode
        portable_mode = True
        options_dir = bleachbit_exe_path
    else:
        # installed mode
        options_dir = os.path.expandvars(r"${APPDATA}\BleachBit")
options_file = os.path.join(options_dir, "bleachbit.ini")

# check whether the application is running from the source tree
if not portable_mode:
    e1 = os.path.exists(os.path.join(bleachbit_exe_path, '../cleaners'))
    e2 = os.path.exists(os.path.join(bleachbit_exe_path, '../Makefile'))
    e3 = os.path.exists(os.path.join(bleachbit_exe_path, '../COPYING'))
    portable_mode = all((e1, e2, e3))

# personal cleaners
personal_cleaners_dir = os.path.join(options_dir, "cleaners")

# system cleaners
if os.path.isdir(os.path.join(bleachbit_exe_path, 'cleaners')):
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')
elif sys.platform.startswith('linux') or sys.platform == 'darwin':
    system_cleaners_dir = '/usr/share/bleachbit/cleaners'
elif sys.platform == 'win32':
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')
elif sys.platform[:6] == 'netbsd':
    system_cleaners_dir = '/usr/pkg/share/bleachbit/cleaners'
elif sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
    system_cleaners_dir = '/usr/local/share/bleachbit/cleaners'
else:
    system_cleaners_dir = None
    logger.warning(
        'unknown system cleaners directory for platform %s ', sys.platform)

# local cleaners directory for running without installation (Windows or Linux)
local_cleaners_dir = None
if portable_mode:
    local_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')

#windows10 theme
windows_10_theme_exe_path = os.path.normpath(os.path.join(bleachbit_exe_path, 'themes/windows10/gtk.css'))
windows_10_theme_source_path = "themes/windows10/gtk.css"

# application icon
__icons = (
    '/usr/share/pixmaps/bleachbit.png',  # Linux
    '/usr/pkg/share/pixmaps/bleachbit.png',  # NetBSD
    '/usr/local/share/pixmaps/bleachbit.png',  # FreeBSD and OpenBSD
    os.path.normpath(os.path.join(bleachbit_exe_path,
                                  'share\\bleachbit.png')),  # Windows
    # When running from source (i.e., not installed).
    os.path.normpath(os.path.join(bleachbit_exe_path, 'bleachbit.png')),
)
appicon_path = None
for __icon in __icons:
    if os.path.exists(__icon):
        appicon_path = __icon

# menu
# This path works when running from source (cross platform) or when
# installed on Windows.
app_menu_filename = os.path.join(bleachbit_exe_path, 'data', 'app-menu.ui')
if not os.path.exists(app_menu_filename) and system_cleaners_dir:
    # This path works when installed on Linux.
    app_menu_filename = os.path.abspath(
        os.path.join(system_cleaners_dir, '../app-menu.ui'))
if not os.path.exists(app_menu_filename):
    logger.error('unknown location for app-menu.ui')

# locale directory
if os.path.exists("./locale/"):
    # local locale (personal)
    locale_dir = os.path.abspath("./locale/")
else:
    # system-wide installed locale
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        locale_dir = "/usr/share/locale/"
    elif sys.platform == 'win32':
        locale_dir = os.path.join(bleachbit_exe_path, 'share\\locale\\')
    elif sys.platform[:6] == 'netbsd':
        locale_dir = "/usr/pkg/share/locale/"
    elif (sys.platform.startswith('openbsd') or
          sys.platform.startswith('freebsd')):
        locale_dir = "/usr/local/share/locale/"



#
# gettext
#
try:
    (user_locale, encoding) = locale.getdefaultlocale()
except:
    logger.exception('error getting locale')
    user_locale = None
    encoding = None

if user_locale is None:
    user_locale = 'C'
    logger.warning("no default locale found.  Assuming '%s'", user_locale)

if 'win32' == sys.platform:
    os.environ['LANG'] = user_locale

try:
    if not os.path.exists(locale_dir):
        raise RuntimeError('translations not installed')
    t = gettext.translation('bleachbit', locale_dir)
    _ = t.gettext
except:
    def _(msg):
        """Dummy replacement for gettext"""
        return msg

try:
    locale.bindtextdomain('bleachbit', locale_dir)
except AttributeError:
    if sys.platform.startswith('win'):
        try:
            # We're on Windows; try and use libintl-8.dll instead
            import ctypes
            libintl = ctypes.cdll.LoadLibrary('libintl-8.dll')
        except OSError:
            # libintl-8.dll isn't available; give up
            pass
        else:
            # bindtextdomain can not handle Unicode
            libintl.bindtextdomain(b'bleachbit', locale_dir.encode('utf-8'))
            libintl.bind_textdomain_codeset(b'bleachbit', b'UTF-8')
except:
    logger.exception('error binding text domain')

try:
    ungettext = t.ungettext
except:
    def ungettext(singular, plural, n):
        """Dummy replacement for Unicode, plural gettext"""
        if 1 == n:
            return singular
        return plural


#
# pgettext
#

# Code released in the Public Domain. You can do whatever you want with this package.
# Originally written by Pierre Métras <pierre@alterna.tv> for the OLPC XO laptop.
#
# Original source: http://dev.laptop.org/git/activities/clock/plain/pgettext.py


# pgettext(msgctxt, msgid) from gettext is not supported in Python as of January 2017
# http://bugs.python.org/issue2504
# Meanwhile we get official support, we have to simulate it.
# See http://www.gnu.org/software/gettext/manual/gettext.html#Ambiguities for
# more information about pgettext.

# The separator between message context and message id.This value is the same as
# the one used in gettext.h, so PO files should be still valid when Python gettext
# module will include pgettext() function.
GETTEXT_CONTEXT_GLUE = "\004"


def pgettext(msgctxt, msgid):
    """A custom implementation of GNU pgettext().
    """
    if msgctxt is not None and msgctxt is not "":
        translation = _(msgctxt + GETTEXT_CONTEXT_GLUE + msgid)
        if translation.startswith(msgctxt + GETTEXT_CONTEXT_GLUE):
            return msgid
        else:
            return translation
    else:
        return _(msgid)


# Map our pgettext() custom function to _p()
_p = pgettext


#
# URLs
#
base_url = "https://update.bleachbit.org"
help_contents_url = "%s/help/%s" \
    % (base_url, APP_VERSION)
release_notes_url = "%s/release-notes/%s" \
    % (base_url, APP_VERSION)
update_check_url = "%s/update/%s" % (base_url, APP_VERSION)

# set up environment variables
if 'nt' == os.name:
    from bleachbit import Windows
    Windows.setup_environment()

if 'posix' == os.name:
    # XDG base directory specification
    envs = {
        'XDG_DATA_HOME': os.path.expanduser('~/.local/share'),
        'XDG_CONFIG_HOME': os.path.expanduser('~/.config'),
        'XDG_CACHE_HOME': os.path.expanduser('~/.cache')
    }
    for varname, value in envs.items():
        if not os.getenv(varname):
            os.environ[varname] = value
