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
Check local CleanerML files as a security measure
"""

import hashlib
import os
import random
import ConfigParser

import pygtk
pygtk.require('2.0')
import gtk

from CleanerML import list_cleanerml_files
from Options import options

KNOWN = 1
CHANGED = 2
NEW = 3


def cleaner_change_dialog(pathname, status, parent):
    """Present a dialog regarding the change of a cleaner definition"""
    dialog = gtk.Dialog(title = "BleachBit", parent = parent, \
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
    hbox = gtk.HBox(homogeneous = False, spacing = 10)
    icon = gtk.Image()
    icon.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icon, False)
    if CHANGED == status:
        msg = _("The following cleaner definition file has changed.  Malicious definitions can damage your computer.")
    elif NEW == status:
        msg = _("The following cleaner definition file is new.  Malicious definitions can damage your computer.")
    else:
        raise RuntimeError('Invalid status code %s' % status)
    msg += "\n\n" + pathname
    question = gtk.Label(msg)
    question.set_line_wrap(True)
    hbox.pack_start(question, False)
    dialog.vbox.pack_start(hbox, False)
    dialog.vbox.set_spacing(10)
    dialog.add_button(gtk.STOCK_ADD, True)
    dialog.add_button(gtk.STOCK_DELETE, False)
    dialog.set_default_response(False)
    dialog.show_all()
    ret = dialog.run()
    dialog.destroy()
    return ret


class RecognizeCleanerML:
    """Check local CleanerML files as a security measure"""
    def __init__(self, parent_window = None):
        self.parent_window = parent_window
        try:
            self.salt = options.get('hashsalt')
        except ConfigParser.NoOptionError, e:
            self.salt = hashlib.sha512(str(random.random())).hexdigest()
            options.set('hashsalt', self.salt)
        self.new_hash = None
        self.__scan()


    def __recognized(self, pathname):
        """Is pathname recognized?"""
        body = file(pathname).read()
        self.new_hash = hashlib.sha512(self.salt + body).hexdigest()
        try:
            known_hash = options.get(pathname, 'hashpath')
        except ConfigParser.NoOptionError, e:
            return NEW
        if self.new_hash == known_hash:
            return KNOWN
        return CHANGED


    def __scan(self):
        """Look for files and act accordingly"""
        for pathname in list_cleanerml_files(local_only = True):
            pathname = os.path.abspath(pathname)
            status = self.__recognized(pathname)
            if NEW == status or CHANGED == status:
                ret = cleaner_change_dialog(pathname, status, \
                    self.parent_window)
                if not ret:
                    print "info: deleting cleaner definition '%s'" % \
                        pathname
                    os.remove(pathname)
                else:
                    options.set(pathname, self.new_hash, 'hashpath')
