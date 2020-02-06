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

from __future__ import absolute_import

import gettext
import locale
import os
import re
import sys

from bleachbit import Log

#
# Config Parser got renamed in Python 3
#
if sys.version_info >= (3, 0):
    from configparser import RawConfigParser, NoOptionError, SafeConfigParser
else:
    from ConfigParser import RawConfigParser, NoOptionError, SafeConfigParser


APP_VERSION = "3.1.0"
APP_NAME = "BleachBit"
APP_URL = "https://www.bleachbit.org"

socket_timeout = 10

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
    bleachbit_exe_path = os.path.dirname(
        sys.executable.decode(sys.getfilesystemencoding()))
else:
    # __file__ is absolute path to __init__.py
    bleachbit_exe_path = os.path.dirname(os.path.dirname(
        __file__.decode(sys.getfilesystemencoding())))

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


# os.path.expandvars does not work well with non-ascii Windows paths.
# This is a unicode-compatible reimplementation of that function.
# Note that if there are errors in the encoding it returns just expanded str.
def expandvars(var):
    """Expand environment variables.

    Return the argument with environment variables expanded. Substrings of the
    form $name or ${name} or %name% are replaced by the value of environment
    variable name."""
    if isinstance(var, str):
        try:
            final = var.decode('utf-8')
        except UnicodeDecodeError:
            # Keep a string which won't be expanded under Windows 7.
            final = var
    else:
        final = var

    if 'posix' == os.name:
        final = os.path.expandvars(final)
    elif 'nt' == os.name:
        import _winreg
        if final.startswith('${'):
            final = re.sub(r'\$\{(.*?)\}(?=$|\\)',
                           lambda x: '%%%s%%' % x.group(1),
                           final)
        elif final.startswith('$'):
            final = re.sub(r'\$(.*?)(?=$|\\)',
                           lambda x: '%%%s%%' % x.group(1),
                           final)
        try:
            final = _winreg.ExpandEnvironmentStrings(final)
        except TypeError:
            # An error occurs when filename contains invalid
            # char and we return string instead of unicode.
            # This can happen on win7.
            pass

    return final

# Windows paths have to be unicode, but os.path.expanduser does not support it.
# This is a unicode-compatible reimplementation of that function.


def expanduser(path):
    """Expand the path with the home directory.

    Return the argument with an initial component of "~" replaced by
    that user's home directory.
    """
    if isinstance(path, str):
        final = path.decode('utf-8')
    else:
        final = path

    # If does not begin with tilde, do not alter.
    if len(path) == 0 or not '~' == path[0]:
        return final

    if 'posix' == os.name:
        final = os.path.expanduser(final)
    elif 'nt' == os.name:
        found = False
        for env in [u'%USERPROFILE%', u'%HOME%']:
            if env in os.environ:
                home = expandvars(env)
                found = True
                break
        if not found:
            h_drive = expandvars(u'%HOMEDRIVE%')
            h_path = expandvars(u'%HOMEPATH%')
            home = os.path.join(h_drive, h_path)
        final = final.replace('~user/', '')
        final = final.replace('~/', '')
        final = final.replace('~\\', '')
        final = final.replace('~', '')
        final = os.path.join(home, final)
    return final


# configuration
portable_mode = False
options_dir = None
if 'posix' == os.name:
    options_dir = expanduser("~/.config/bleachbit")
elif 'nt' == os.name:
    if os.path.exists(os.path.join(bleachbit_exe_path, 'bleachbit.ini')):
        # portable mode
        portable_mode = True
        options_dir = bleachbit_exe_path
    else:
        # installed mode
        options_dir = expandvars(r"${APPDATA}\BleachBit")
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
FSE = sys.getfilesystemencoding()
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
    _ = t.ugettext
except:
    def _(msg):
        """Dummy replacement for ugettext"""
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
            if isinstance(locale_dir, unicode):
                path = locale_dir.encode('utf-8')
            else:
                path = locale_dir
            libintl.bindtextdomain('bleachbit', path)
            libintl.bind_textdomain_codeset('bleachbit', 'UTF-8')
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
# string decoding
#
# In Python 2, some strings such as Python exceptions may be localized
# and byte encoded.  This decodes them into Unicode.
# See <https://bugs.launchpad.net/bleachbit/+bug/1416640>.
#
def decode_str(s):
    """Decode a string into Unicode using the default encoding"""
    if isinstance(s, Exception):
        # for convenience
        return decode_str(s.message)
    try:
        return s.decode(encoding)
    except:
        return s.decode('ascii', 'replace')

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
    for varname, value in envs.iteritems():
        if not os.getenv(varname):
            os.environ[varname] = value
