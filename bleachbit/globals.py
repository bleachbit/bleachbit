# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit-project.appspot.com
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
import sys


APP_VERSION = "0.5.5"
APP_NAME = "BleachBit"
APP_URL = "http://bleachbit-project.appspot.com"

update_check_url = "http://bleachbit.sourceforge.net/communicate.php"

release_notes_url = "http://bleachbit.sourceforge.net/release_notes.php?version=" + str(APP_VERSION)

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
    bleachbit_exe_path = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

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
if not os.path.exists(license_filename) and sys.platform == 'win32':
    # Windows
    license_filename = os.path.join(bleachbit_exe_path, 'COPYING')

# configuration
options_dir = None
if sys.platform == 'linux2':
    options_dir = os.path.expanduser("~/.config/bleachbit/")
if sys.platform == 'win32':
    options_dir = os.path.expandvars("${APPDATA}\\BleachBit\\")
options_file = os.path.join(options_dir, "bleachbit.ini")

# personal cleaners
personal_cleaners_dir = os.path.join(options_dir, "cleaners")

# system cleaners
system_cleaners_dir = None
if sys.platform == 'linux2':
    system_cleaners_dir = '/usr/share/bleachbit/cleaners'
if sys.platform == 'win32':
    system_cleaners_dir = os.path.join(bleachbit_exe_path, 'share\\cleaners\\')

# application icon
if os.path.exists("bleachbit.png"):
    appicon_path = "bleachbit.png"
    print "debug: appicon_path = '%s'" % (appicon_path, )
else:
    if sys.platform == 'linux2':
        appicon_path = "/usr/share/pixmaps/bleachbit.png"
    if sys.platform == 'win32':
        appicon_path = os.path.join(bleachbit_exe_path, 'share\\bleachbit.png')

# locale directory
if os.path.exists("./locale/"):
    # local locale
    locale_dir = os.path.abspath("./locale/")
    print "debug: locale_dir = '%s'" % (locale_dir, )
else:
    # installed locale
    if sys.platform == 'linux2':
        locale_dir = "/usr/share/locale/"
    if sys.platform == 'win32':
        locale_dir = os.path.join(bleachbit_exe_path, 'share\\locale\\')


###
### gettext
###

try:
    gettext.bindtextdomain('bleachbit', locale_dir)
    gettext.textdomain('bleachbit')
    gettext.install('bleachbit', locale_dir, unicode=1)
except:
    print "Warning: gettext() failed so translations will be unvailable"
    def _(msg):
        """Dummy replacement for gettext"""
        return msg


###
### XML
###


def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError('Invalid boolean: %s' % value)


def getText(nodelist):
    """Return the text data in an XML node 
    http://docs.python.org/library/xml.dom.minidom.html"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


