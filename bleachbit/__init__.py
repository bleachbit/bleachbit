# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Code that is commonly shared throughout BleachBit
"""

import os
import re
import sys
from configparser import NoOptionError, RawConfigParser  # used in other files

from bleachbit import Log

APP_VERSION = "6.0.1"
APP_NAME = "BleachBit"
APP_URL = "https://www.bleachbit.org"
APP_COPYRIGHT = "Copyright (C) 2008-2026 Andrew Ziem"

socket_timeout = 10

if sys.version_info < (3, 8, 0):
    print('BleachBit requires Python version 3.8 or later')
    sys.exit(1)

if hasattr(sys, 'frozen'):
    stdout_encoding = 'utf-8'
else:
    stdout_encoding = sys.stdout.encoding

logger = Log.init_log()

# Setting below value to false disables update notification (useful
# for packages in repositories).
online_update_notification_enabled = True

#
# Platform
#

# platform
IS_WINDOWS = os.name == 'nt'
IS_POSIX = os.name == 'posix'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'
IS_BSD = sys.platform.startswith(('freebsd', 'openbsd', 'netbsd'))
IS_NETBSD = sys.platform[:6] == 'netbsd'
ARCH_BITS = 64 if sys.maxsize > 2**32 else 32

# file system attributes
FS_CASE_SENSITIVE = not (IS_WINDOWS or IS_MAC)
FS_SCAN_RE_FLAGS = 0 if FS_CASE_SENSITIVE else re.IGNORECASE


#
# Paths
#

# Windows
bleachbit_exe_path = None
if hasattr(sys, 'frozen'):
    # running frozen in py2exe
    bleachbit_exe_path = os.path.dirname(sys.executable)
    bleachbit_package_path = bleachbit_exe_path
else:
    # __file__ is absolute path to __init__.py
    bleachbit_package_path = os.path.dirname(__file__)
    bleachbit_exe_path = os.path.dirname(bleachbit_package_path)

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


def _home_dir():
    """Return home directory with fallback for missing HOME and passwd entry."""
    home = os.getenv('HOME')
    if home:
        return home
    # expanduser() falls back to a lookup in passwd database.
    home = os.path.expanduser('~')
    if home != '~':
        return home
    return '/tmp'


# configuration
portable_mode = False
options_dir = None
if IS_POSIX:
    options_dir = os.path.join(_home_dir(), ".config/bleachbit")
elif IS_WINDOWS:
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
_exe_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')
_package_cleaners_dir = os.path.join(bleachbit_package_path, 'cleaners')
if os.path.isdir(_exe_cleaners_dir) and not portable_mode:
    system_cleaners_dir = _exe_cleaners_dir
elif os.path.isdir(_package_cleaners_dir) and not portable_mode:
    # AppImage
    system_cleaners_dir = _package_cleaners_dir
elif IS_LINUX or IS_MAC:
    system_cleaners_dir = '/usr/share/bleachbit/cleaners'
elif IS_WINDOWS:
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')
elif IS_NETBSD:
    system_cleaners_dir = '/usr/pkg/share/bleachbit/cleaners'
elif IS_BSD:
    system_cleaners_dir = '/usr/local/share/bleachbit/cleaners'
else:
    system_cleaners_dir = None
    logger.warning(
        'unknown system cleaners directory for platform %s ', sys.platform)

# local cleaners directory for running without installation (Windows or Linux)
local_cleaners_dir = None
if portable_mode:
    local_cleaners_dir = os.path.join(bleachbit_exe_path, 'cleaners')


def get_share_dirs():
    """Return ordered list of directories to search for shared data files."""
    if hasattr(sys, 'frozen'):
        # frozen in py2exe
        base_dirs = [
            os.path.join(bleachbit_exe_path, 'share'),
            bleachbit_exe_path,
        ]
    else:
        # installed .deb or .rpm has `__file__` = "/usr/share/bleachbit/__init__.py",
        # so that dirname() is "/usr/share/bleachbit"
        package_dir = bleachbit_package_path
        # When running from source, share directory is `../share/` from `__init__.py`.
        repo_root = os.path.normpath(os.path.join(package_dir, '..'))
        base_dirs = [
            os.path.join(package_dir, 'share'),
            os.path.join(repo_root, 'share')
        ]
    if system_cleaners_dir:
        # One directory up from the system cleaners directory.
        # This works when installed, like under `/usr/share`.
        base_dirs.append(os.path.dirname(system_cleaners_dir))
    # Remove duplicates while preserving the order.
    seen = set()
    unique_dirs = []
    for base_dir in base_dirs:
        if base_dir in seen:
            continue
        seen.add(base_dir)
        unique_dirs.append(base_dir)
    return unique_dirs


def get_share_path(filename):
    """Return path to a shared data file if it exists, else None."""
    for base_dir in get_share_dirs():
        candidate = os.path.normpath(os.path.join(base_dir, filename))
        if os.path.exists(candidate):
            return candidate
    logger.error('unknown location for %s', filename)
    return None


# windows10 theme
windows10_theme_path = os.path.normpath(
    os.path.join(bleachbit_exe_path, 'themes/windows10'))

# application icon
__icons = (
    # AppImage
    os.path.normpath(os.path.join(bleachbit_exe_path,
                                  'pixmaps/bleachbit.png')),
    # Linux
    '/usr/share/pixmaps/bleachbit.png',
    # NetBSD
    '/usr/pkg/share/pixmaps/bleachbit.png',
    # FreeBSD and OpenBSD
    os.path.normpath(os.path.join(bleachbit_exe_path,
                                  'share\\bleachbit.png')),  # Windows
    # When running from source (i.e., not installed).
    os.path.normpath(os.path.join(bleachbit_exe_path, 'bleachbit.png')),
)
appicon_path = None
for __icon in __icons:
    if os.path.exists(__icon):
        appicon_path = __icon

# locale directory
_exe_locale_dir = os.path.join(bleachbit_exe_path, 'locale')
if os.path.exists("./locale/"):
    # local locale (personal)
    locale_dir = os.path.abspath("./locale/")
elif os.path.exists(_exe_locale_dir):
    # AppImage
    locale_dir = _exe_locale_dir
# system-wide installed locale
elif sys.platform in ('linux', 'darwin'):
    locale_dir = "/usr/share/locale/"
elif sys.platform == "win32":
    locale_dir = os.path.join(bleachbit_exe_path, "share\\locale\\")
elif sys.platform[:6] == "netbsd":
    locale_dir = "/usr/pkg/share/locale/"
elif sys.platform.startswith("openbsd") or sys.platform.startswith("freebsd"):
    locale_dir = "/usr/local/share/locale/"


#
# URLs
#
base_url = "https://update.bleachbit.org"
help_contents_url = "https://www.bleachbit.org/help"
update_check_url = f"{base_url}/update/{APP_VERSION}"
