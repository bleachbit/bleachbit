# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2008 Andrew Ziem
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

import os

APP_VERSION = "0.1.1"
APP_NAME = "BleachBit"

license_filename = "/usr/share/doc/bleachbit-" + APP_VERSION + "/COPYING"

options_dir = os.path.expanduser("~/.config/bleachbit/")
options_file = os.path.join(options_dir, "bleachbit.ini")

update_url = "http://bleachbit.sourceforge.net/communicate.php"

socket_timeout = 10

# Setting below value to false disables update notification (useful
# for packages in repositories).
online_update_notification_enabled = True
