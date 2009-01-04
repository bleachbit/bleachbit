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

import gettext
import os

APP_VERSION = "0.2.1"
APP_NAME = "BleachBit"

# Debian, Ubuntu
license_filename = "/usr/share/common-licenses/GPL-3"
if not os.path.exists(license_filename):
    # openSUSE 1.11
    license_filename = "/usr/share/doc/packages/bleachbit/COPYING"
if not os.path.exists(license_filename):
    # Mandriva
    license_filename = "/usr/share/doc/bleachbit/COPYING"
if not os.path.exists(license_filename):
    # CentOS, Fedora, RHEL
    license_filename = "/usr/share/doc/bleachbit-" + APP_VERSION + "/COPYING"

options_dir = os.path.expanduser("~/.config/bleachbit/")
options_file = os.path.join(options_dir, "bleachbit.ini")

update_url = "http://bleachbit.sourceforge.net/communicate.php"

socket_timeout = 10

# Setting below value to false disables update notification (useful
# for packages in repositories).
online_update_notification_enabled = True

# application icon
if os.path.exists("bleachbit.png"):
    appicon_path = "bleachbit.png"
    print "debug: appicon_path = '%s'" % (appicon_path, )
else:
    appicon_path = "/usr/share/pixmaps/bleachbit.png"

# locale directory
if os.path.exists("./locale/"):
    # local locale
    locale_dir = os.path.abspath("./locale/")
    print "debug: locale_dir = '%s'" % (locale_dir, )
else:
    # installed locale
    locale_dir = "/usr/share/locale/"

try:
    gettext.bindtextdomain('bleachbit', locale_dir)
    gettext.textdomain('bleachbit')
    gettext.install('bleachbit', locale_dir, unicode=1)
except:
    print "Warning: gettext() failed so translations will be unvailable"
    def _(str):
        """Dummy replacement for gettext"""
        return str

