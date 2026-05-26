# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Code that is commonly shared throughout BleachBit
"""


import gettext
import locale
import os
import sys
import warnings

from bleachbit import Log
from bleachbit.Constant import (
    APP_NAME,
    APP_URL,
    APP_VERSION,
    BASE_URL as base_url,
    FS_SCAN_RE_FLAGS as fs_scan_re_flags,
    GETTEXT_CONTEXT_GLUE,
    HELP_CONTENTS_URL as help_contents_url,
    ONLINE_UPDATE_NOTIFICATION_ENABLED as online_update_notification_enabled,
    RELEASE_NOTES_URL as release_notes_url,
    SOCKET_TIMEOUT as socket_timeout,
    UPDATE_CHECK_URL as update_check_url,
)
from configparser import RawConfigParser, NoOptionError # used in other files

import win_unicode_console

if sys.version_info < (3, 4, 4):
    print('This version requires Python 3.4.4.')
    sys.exit(1)

if not os.name == 'nt':
    print('This version requires Windows.')
    sys.exit(1)

if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
    stdout_encoding = 'utf-8'
else:
    stdout_encoding = sys.stdout.encoding
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        win_unicode_console.enable()

logger = Log.init_log()

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
license_filenames = (
    os.path.join(bleachbit_exe_path, 'COPYING'),
)
for lf in license_filenames:
    if os.path.exists(lf):
        license_filename = lf
        break

# configuration
portable_mode = False
options_dir = None
os.environ.pop('FONTCONFIG_FILE', None)
if os.path.exists(os.path.join(bleachbit_exe_path, 'bleachbit.ini')):
    # portable mode
    portable_mode = True
    options_dir = bleachbit_exe_path
else:
    # installed mode
    options_dir = os.path.expandvars(r"${APPDATA}\BleachBit")

try:
    options_dir = os.environ['BLEACHBIT_TEST_OPTIONS_DIR']
except KeyError:
    pass

options_file = os.path.join(options_dir, "bleachbit.ini")

# check whether the application is running from the source tree
if not portable_mode:
    paths = (
        '../cleaners',
        '../Makefile',
        '../COPYING')
    existing = (
        os.path.exists(os.path.join(bleachbit_exe_path, path))
        for path in paths)
    portable_mode = all(existing)

# personal cleaners
personal_cleaners_dir = os.path.join(options_dir, "cleaners")

# system cleaners
# On Windows in portable mode, the bleachbit_exe_path is equal to
# options_dir, so be careful that system_cleaner_dir is not set to
# personal_cleaners_dir.
if os.path.isdir(os.path.join(bleachbit_exe_path, 'cleaners')) and not portable_mode:
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')
else:
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')

# local cleaners directory for running without installation
local_cleaners_dir = None
if portable_mode:
    local_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')

# windows10 theme
windows10_theme_path = os.path.normpath(os.path.join(bleachbit_exe_path, 'themes/windows10'))

# application icon
__icons = (
    os.path.normpath(os.path.join(bleachbit_exe_path,
                                  'share\\bleachbit.png')),
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
if not os.path.exists(app_menu_filename):
    logger.error('unknown location for app-menu.ui')

# locale directory
if os.path.exists("./locale/"):
    # local locale (personal)
    locale_dir = os.path.abspath("./locale/")
else:
    locale_dir = os.path.join(bleachbit_exe_path, "share\\locale\\")



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

# Windows-only
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
    ngettext = t.ngettext
except:
    def ngettext(singular, plural, n):
        """Dummy replacement for plural gettext"""
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
# This issue was fixed in Python 3.8, but we need to support older versions.
# Meanwhile we get official support, we have to simulate it.
# See http://www.gnu.org/software/gettext/manual/gettext.html#Ambiguities for
# more information about pgettext.


def pgettext(msgctxt, msgid):
    """A custom implementation of GNU pgettext().
    """
    if msgctxt is None or msgctxt == "":
        return _(msgid)
    translation = _(msgctxt + GETTEXT_CONTEXT_GLUE + msgid)
    if translation.startswith(msgctxt + GETTEXT_CONTEXT_GLUE):
        return msgid
    else:
        return translation


# Map our pgettext() custom function to _p()
_p = pgettext

# set up environment variables
from bleachbit import Windows
Windows.setup_environment()

#
# Exceptions
#


# Python 3.6 is the first with this exception
if hasattr(sys.modules['builtins'], 'ModuleNotFoundError'):
    ModuleNotFoundError = sys.modules['builtins'].ModuleNotFoundError
else:
    class ModuleNotFoundError(Exception):
        pass
