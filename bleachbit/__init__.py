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
from configparser import RawConfigParser, NoOptionError # used in other files

from bleachbit.Constant import (
    APP_NAME,
    APP_URL,
    APP_VERSION,
    BASE_URL,
    FS_SCAN_RE_FLAGS,
    GETTEXT_CONTEXT_GLUE,
    HELP_CONTENTS_URL,
    RELEASE_NOTES_URL,
    SOCKET_TIMEOUT,
    UPDATE_CHECK_URL,
)


from bleachbit import Log


if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
    STDOUT_ENCODING = 'utf-8'
else:
    STDOUT_ENCODING = sys.stdout.encoding
    # win_unicode_console is enabled in bootstrap() in bleachbit.py.


logger = Log.init_log()

#
# Paths
#

# Windows
BLEACHBIT_EXE_PATH = None
if hasattr(sys, 'frozen'):
    # running frozen in py2exe
    BLEACHBIT_EXE_PATH = os.path.dirname(sys.executable)
else:
    # __file__ is absolute path to __init__.py
    BLEACHBIT_EXE_PATH = os.path.dirname(os.path.dirname(__file__))

# license
LICENSE_FILENAME = os.path.join(BLEACHBIT_EXE_PATH, 'COPYING')

# configuration
PORTABLE_MODE = False
OPTIONS_DIR = None
if os.path.exists(os.path.join(BLEACHBIT_EXE_PATH, 'bleachbit.ini')):
    # portable mode
    PORTABLE_MODE = True
    OPTIONS_DIR = BLEACHBIT_EXE_PATH
else:
    # installed mode
    OPTIONS_DIR = os.path.expandvars(r"${APPDATA}\BleachBit")

try:
    OPTIONS_DIR = os.environ['BLEACHBIT_TEST_OPTIONS_DIR']
except KeyError:
    pass

OPTIONS_FILE = os.path.join(OPTIONS_DIR, "bleachbit.ini")

# check whether the application is running from the source tree
if not PORTABLE_MODE:
    paths = (
        '../cleaners',
        '../Makefile',
        '../COPYING')
    existing = (
        os.path.exists(os.path.join(BLEACHBIT_EXE_PATH, path))
        for path in paths)
    PORTABLE_MODE = all(existing)

# personal cleaners
PERSONAL_CLEANERS_DIR = os.path.join(OPTIONS_DIR, "cleaners")

# system cleaners
# On Windows in portable mode, the BLEACHBIT_EXE_PATH is equal to
# options_dir, so be careful that system_cleaner_dir is not set to
# personal_cleaners_dir.
if os.path.isdir(os.path.join(BLEACHBIT_EXE_PATH, 'cleaners')) and not PORTABLE_MODE:
    SYSTEM_CLEANERS_DIR = os.path.join(BLEACHBIT_EXE_PATH, 'cleaners')
else:
    SYSTEM_CLEANERS_DIR = os.path.join(BLEACHBIT_EXE_PATH, 'share\\cleaners\\')

# local cleaners directory for running without installation
LOCAL_CLEANERS_DIR = None
if PORTABLE_MODE:
    LOCAL_CLEANERS_DIR = os.path.join(BLEACHBIT_EXE_PATH, 'cleaners')

# windows10 theme
WINDOWS10_THEME_PATH = os.path.normpath(
    os.path.join(BLEACHBIT_EXE_PATH, 'themes/windows10'))

# application icon
__icons = (
    os.path.normpath(os.path.join(BLEACHBIT_EXE_PATH,
                                  'share\\bleachbit.png')),
    # When running from source (i.e., not installed).
    os.path.normpath(os.path.join(BLEACHBIT_EXE_PATH, 'bleachbit.png')),
)
APPICON_PATH = None
for __icon in __icons:
    if os.path.exists(__icon):
        APPICON_PATH = __icon

# menu
# This path works when running from source (cross platform) or when
# installed on Windows.
APP_MENU_FILENAME = os.path.join(BLEACHBIT_EXE_PATH, 'data', 'app-menu.ui')
if not os.path.exists(APP_MENU_FILENAME):
    logger.error('unknown location for app-menu.ui')

# locale directory
if os.path.exists("./locale/"):
    # local locale (personal)
    LOCALE_DIR = os.path.abspath("./locale/")
else:
    LOCALE_DIR = os.path.join(BLEACHBIT_EXE_PATH, "share\\locale\\")


#
# gettext
#
try:
    (USER_LOCALE, encoding) = locale.getdefaultlocale()
except:
    logger.exception('error getting locale')
    USER_LOCALE = None
    encoding = None

if USER_LOCALE is None:
    USER_LOCALE = 'C'
    logger.warning("no default locale found.  Assuming '%s'", USER_LOCALE)

# Windows-only
os.environ['LANG'] = USER_LOCALE

try:
    if not os.path.exists(LOCALE_DIR):
        raise RuntimeError('translations not installed')
    t = gettext.translation('bleachbit', LOCALE_DIR)
    _ = t.gettext
except:
    def _(msg):
        """Dummy replacement for gettext"""
        return msg

try:
    locale.bindtextdomain('bleachbit', LOCALE_DIR)
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
        libintl.bindtextdomain(b'bleachbit', LOCALE_DIR.encode('utf-8'))
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

#
# Exceptions
#


# Python 3.6 is the first with this exception
if hasattr(sys.modules['builtins'], 'ModuleNotFoundError'):
    ModuleNotFoundError = sys.modules['builtins'].ModuleNotFoundError
else:
    class ModuleNotFoundError(Exception):
        pass
