# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
Check local CleanerML files as a security measure
"""

from __future__ import absolute_import, print_function

from bleachbit import _, _p
import bleachbit
from bleachbit.CleanerML import list_cleanerml_files
from bleachbit.Options import options

import hashlib
import logging
import os
import random
import sys


logger = logging.getLogger(__name__)

KNOWN = 1
CHANGED = 2
NEW = 3


def cleaner_change_dialog(changes, parent):
    """Present a dialog regarding the change of cleaner definitions"""

    def toggled(cell, path, model):
        """Callback for clicking the checkbox"""
        __iter = model.get_iter_from_string(path)
        value = not model.get_value(__iter, 0)
        model.set(__iter, 0, value)

    # TODO: move to GuiBasic
    from bleachbit.GuiBasic import Gtk
    from gi.repository import GObject

    dialog = Gtk.Dialog(title=_("Security warning"),
                        transient_for=parent,
                        modal=True, destroy_with_parent=True)
    dialog.set_default_size(600, 500)

    # create warning
    warnbox = Gtk.Box()
    image = Gtk.Image()
    image.set_from_icon_name("dialog-warning", Gtk.IconSize.DIALOG)
    warnbox.pack_start(image, False, True, 0)

    # TRANSLATORS: Cleaner definitions are XML data files that define
    # which files will be cleaned.
    label = Gtk.Label(
        label=_("These cleaner definitions are new or have changed. Malicious definitions can damage your system. If you do not trust these changes, delete the files or quit."))
    label.set_line_wrap(True)
    warnbox.pack_start(label, True, True, 0)
    dialog.vbox.pack_start(warnbox, False, True, 0)

    # create tree view
    liststore = Gtk.ListStore(GObject.TYPE_BOOLEAN, GObject.TYPE_STRING)
    treeview = Gtk.TreeView(model=liststore)

    renderer0 = Gtk.CellRendererToggle()
    renderer0.set_property('activatable', True)
    renderer0.connect('toggled', toggled, liststore)
    # TRANSLATORS: This is the column label (header) in the tree view for the
    # security dialog
    treeview.append_column(
        Gtk.TreeViewColumn(_p('column_label', 'Delete'), renderer0, active=0))
    renderer1 = Gtk.CellRendererText()
    # TRANSLATORS: This is the column label (header) in the tree view for the
    # security dialog
    treeview.append_column(
        Gtk.TreeViewColumn(_p('column_label', 'Filename'), renderer1, text=1))

    # populate tree view
    for change in changes:
        liststore.append([False, change[0]])

    # populate dialog with widgets
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.add(treeview)
    dialog.vbox.pack_start(scrolled_window, True, True, 0)

    dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
    dialog.add_button(Gtk.STOCK_QUIT, Gtk.ResponseType.CLOSE)

    # run dialog
    dialog.show_all()
    while True:
        if Gtk.ResponseType.ACCEPT != dialog.run():
            sys.exit(0)
        delete = []
        for row in liststore:
            b = row[0]
            path = row[1]
            if b:
                delete.append(path)
        if 0 == len(delete):
            # no files selected to delete
            break
        import GuiBasic
        if not GuiBasic.delete_confirmation_dialog(parent, mention_preview=False):
            # confirmation not accepted, so do not delete files
            continue
        for path in delete:
            logger.info("deleting unrecognized CleanerML '%s'", path)
            os.remove(path)
        break
    dialog.destroy()


def hashdigest(string):
    """Return hex digest of hash for a string"""

    # hashlib requires Python 2.5
    return hashlib.sha512(string).hexdigest()


class RecognizeCleanerML:

    """Check local CleanerML files as a security measure"""

    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        try:
            self.salt = options.get('hashsalt')
        except bleachbit.NoOptionError:
            self.salt = hashdigest(str(random.random()))
            options.set('hashsalt', self.salt)
        self.__scan()

    def __recognized(self, pathname):
        """Is pathname recognized?"""
        with open(pathname) as f:
            body = f.read()
        new_hash = hashdigest(self.salt + body)
        try:
            known_hash = options.get_hashpath(pathname)
        except bleachbit.NoOptionError:
            return NEW, new_hash
        if new_hash == known_hash:
            return KNOWN, new_hash
        return CHANGED, new_hash

    def __scan(self):
        """Look for files and act accordingly"""
        changes = []
        for pathname in sorted(list_cleanerml_files(local_only=True)):
            pathname = os.path.abspath(pathname)
            (status, myhash) = self.__recognized(pathname)
            if NEW == status or CHANGED == status:
                changes.append([pathname, status, myhash])
        if len(changes) > 0:
            cleaner_change_dialog(changes, self.parent_window)
            for change in changes:
                pathname = change[0]
                myhash = change[2]
                logger.info("remembering CleanerML file '%s'", pathname)
                if os.path.exists(pathname):
                    options.set_hashpath(pathname, myhash)
