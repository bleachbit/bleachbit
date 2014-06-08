# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
import sys

if 'nt' == os.name:
    from win32com.shell import shell, shellcon

APP_VERSION = "1.2"
APP_NAME = "BleachBit"
APP_URL = "http://bleachbit.sourceforge.net"

print "info: starting %s version %s" % (APP_NAME, APP_VERSION)

socket_timeout = 10

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
        unicode(sys.executable, sys.getfilesystemencoding()))
else:
    # __file__ is absolute path to bleachbit/Common.py
    bleachbit_exe_path = os.path.dirname(
        unicode(__file__, sys.getfilesystemencoding()))

# license
license_filename = None
license_filenames = ('/usr/share/common-licenses/GPL-3',  # Debian, Ubuntu
                     os.path.join(
                         bleachbit_exe_path, 'COPYING'),  # Microsoft Windows
                     '/usr/share/doc/bleachbit-' + APP_VERSION +
                     '/COPYING',  # CentOS, Fedora, RHEL
                     '/usr/share/doc/packages/bleachbit/COPYING',
                     # OpenSUSE 11.1
                     '/usr/share/doc/bleachbit/COPYING',  # Mandriva
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
        options_dir = os.path.expandvars("${APPDATA}\\BleachBit")
options_file = os.path.join(options_dir, "bleachbit.ini")

# personal cleaners
personal_cleaners_dir = os.path.join(options_dir, "cleaners")

# system cleaners
if sys.platform.startswith('linux'):
    system_cleaners_dir = '/usr/share/bleachbit/cleaners'
elif sys.platform == 'win32':
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')
elif sys.platform[:6] == 'netbsd':
    system_cleaners_dir = '/usr/pkg/share/bleachbit/cleaners'
else:
    system_cleaners_dir = None
    print 'warning: unknown system cleaners directory for platform ', sys.platform

# local cleaners directory (for running from source tree)
local_cleaners_dir = os.path.normpath(
    os.path.join(bleachbit_exe_path, '../cleaners'))

# application icon
__icons = ('/usr/share/pixmaps/bleachbit.png',  # Linux
           os.path.join(bleachbit_exe_path, 'share\\bleachbit.png'),  # Windows
           '/usr/pkg/share/pixmaps/bleachbit.png',  # NetBSD
           os.path.normpath(os.path.join(bleachbit_exe_path, '../bleachbit.png')))  # local
appicon_path = None
for __icon in __icons:
    if os.path.exists(__icon):
        appicon_path = __icon


# locale directory
if os.path.exists("./locale/"):
    # local locale (personal)
    locale_dir = os.path.abspath("./locale/")
else:
    # system-wide installed locale
    if sys.platform.startswith('linux'):
        locale_dir = "/usr/share/locale/"
    elif sys.platform == 'win32':
        locale_dir = os.path.join(bleachbit_exe_path, 'share\\locale\\')
    elif sys.platform[:6] == 'netbsd':
        locale_dir = "/usr/pkg/share/locale/"


# launcher
launcher_path = '/usr/share/applications/bleachbit.desktop'
if 'posix' == os.name:
    autostart_path = os.path.expanduser(
        '~/.config/autostart/bleachbit.desktop')


#
# setup environment
#

# Windows XP doesn't define localappdata, but Windows Vista and 7 do
def environ(varname, csidl):
    try:
        os.environ[varname] = shell.SHGetSpecialFolderPath(None, csidl)
    except:
        traceback.print_exc()
        msg = 'Error setting environemnt variable "%s": %s ' % (
            varname, str(sys.exc_info()[1]))
        import GuiBasic
        GuiBasic.message_dialog(None, msg)
if 'nt' == os.name:
    environ('localappdata', shellcon.CSIDL_LOCAL_APPDATA)
    environ('documents', shellcon.CSIDL_DESKTOPDIRECTORY)


#
# gettext
#

try:
    user_locale = locale.getdefaultlocale()[0]
except:
    print 'warning: error getting locale: %s' % str(sys.exc_info()[1])
    user_locale = None

if None == user_locale:
    user_locale = 'C'
    print "warning: No default locale found.  Assuming '%s'" % user_locale

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


# pgettext(msgctxt, msgid) from gettext is not supported in Python implementation < v2.6.
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
_p = lambda msgctxt, msgid: pgettext(msgctxt, msgid)


#
# URLs
#


base_url = "http://bleachbit.sourceforge.net"
help_contents_url = "%s/link.php?version=%s&lang=%s&target=help" \
    % (base_url, APP_VERSION, user_locale)
release_notes_url = "%s/link.php?version=%s&lang=%s&target=release_notes" \
    % (base_url, APP_VERSION, user_locale)
update_check_url = "%s/communicate.php" % base_url
