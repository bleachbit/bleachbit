# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Code that is commonly shared throughout BleachBit
"""


import gettext
import locale
import os
import sys
import traceback


APP_VERSION = "0.7.1"
APP_NAME = "BleachBit"
APP_URL = "http://bleachbit.sourceforge.net"

print "info: starting %s version %s" % (APP_NAME, APP_VERSION)

socket_timeout = 10

# Setting below value to false disables update notification (useful
# for packages in repositories).
online_update_notification_enabled = True

###
### Paths
###

# Windows
bleachbit_exe_path = None
if hasattr(sys, 'frozen'):
    # running frozen in py2exe
    bleachbit_exe_path = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
    # __file__ is absolute path to bleachbit/Common.py
    bleachbit_exe_path = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

# license
license_filename = None
license_filenames = ('/usr/share/common-licenses/GPL-3', # Debian, Ubuntu
    os.path.join(bleachbit_exe_path, 'COPYING'), # Microsoft Windows
    '/usr/share/doc/bleachbit-' + APP_VERSION + '/COPYING', # CentOS, Fedora, RHEL
    '/usr/share/doc/packages/bleachbit/COPYING', # OpenSUSE 11.1
    '/usr/share/doc/bleachbit/COPYING', # Mandriva
    '/usr/pkg/share/doc/bleachbit/COPYING' ) # NetBSD 5
for lf in license_filenames:
    if os.path.exists(lf):
        license_filename = lf
        break
if None == license_filename:
    print 'warning: cannot find GPLv3 license text file'

# configuration
options_dir = None
if 'posix' == os.name:
    options_dir = os.path.expanduser("~/.config/bleachbit")
elif 'nt' == os.name:
    if os.path.exists(os.path.join(bleachbit_exe_path, 'bleachbit.ini')):
        # portable mode
        options_dir = bleachbit_exe_path
    else:
        # installed mode
        options_dir = os.path.expandvars("${APPDATA}\\BleachBit")
options_file = os.path.join(options_dir, "bleachbit.ini")

# personal cleaners
personal_cleaners_dir = os.path.join(options_dir, "cleaners")

# system cleaners
system_cleaners_dir = None
if sys.platform == 'linux2':
    system_cleaners_dir = '/usr/share/bleachbit/cleaners'
elif sys.platform == 'win32':
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')
elif sys.platform[:6] == 'netbsd':
    system_cleaners_dir = '/usr/pkg/share/bleachbit/cleaners'

# local cleaners directory (for running from source tree)
local_cleaners_dir =  os.path.normpath(os.path.join(bleachbit_exe_path, '../cleaners'))

# application icon
__icons = ( '/usr/share/pixmaps/bleachbit.png', # Linux
    os.path.join(bleachbit_exe_path, 'share\\bleachbit.png'), # Windows
    '/usr/pkg/share/pixmaps/bleachbit.png', # NetBSD
    os.path.normpath(os.path.join(bleachbit_exe_path, '../bleachbit.png'))) # local
appicon_path = None
for __icon in __icons:
    if os.path.exists(__icon):
        appicon_path = __icon
print "debug: appicon_path = '%s'" % (appicon_path, )


# locale directory
if os.path.exists("./locale/"):
    # local locale (personal)
    locale_dir = os.path.abspath("./locale/")
    print "debug: locale_dir = '%s'" % (locale_dir, )
else:
    # system-wide installed locale
    if sys.platform == 'linux2':
        locale_dir = "/usr/share/locale/"
    elif sys.platform == 'win32':
        locale_dir = os.path.join(bleachbit_exe_path, 'share\\locale\\')
    elif sys.platform[:6] == 'netbsd':
        locale_dir = "/usr/pkg/share/locale/"


# launcher
launcher_path = '/usr/share/applications/bleachbit.desktop'
if 'posix' == os.name:
    autostart_path = os.path.expanduser('~/.config/autostart/bleachbit.desktop')
if 'nt' == os.name:
    from win32com.shell import shell, shellcon
    autostart_path = os.path.join(shell.SHGetSpecialFolderPath(None, shellcon.CSIDL_STARTUP), 'bleachbit.lnk')


###
### gettext
###

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
    t = gettext.translation('bleachbit', locale_dir)
    _ = t.ugettext
except:
    if 'C' != user_locale and 'en' != user_locale[0:2]:
        traceback.print_exc()
        print "warning: gettext() failed so translations will be unavailable"
    def _(msg):
        """Dummy replacement for gettext"""
        return msg

###
### URLs
###


base_url = "http://bleachbit.sourceforge.net"
help_contents_url = "%s/link.php?version=%s&lang=%s&target=help" \
    % ( base_url, APP_VERSION, user_locale )
release_notes_url = "%s/link.php?version=%s&lang=%s&target=release_notes" \
    % ( base_url, APP_VERSION, user_locale )
update_check_url = "%s/communicate.php" % base_url

