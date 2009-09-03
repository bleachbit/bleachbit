#!/usr/bin/env python
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
Preferences dialog
"""


import gtk
import os
import sys

from Common import online_update_notification_enabled
from Options import options



class PreferencesDialog:
    """Present the preferences dialog and save changes"""

    def __init__(self, parent, cb_refresh_operations):
        self.cb_refresh_operations = cb_refresh_operations

        self.parent = parent
        self.dialog = gtk.Dialog(title = _("Preferences"), \
            parent = parent, \
            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        self.dialog.set_default_size(300, 200)

        self.tooltips = gtk.Tooltips()
        self.tooltips.enable()

        notebook = gtk.Notebook()
        notebook.append_page(self.__general_page(), gtk.Label(_("General")))
        notebook.append_page(self.__drives_page(), gtk.Label(_("Drives")))
        if 'posix' == os.name:
            notebook.append_page(self.__languages_page(), gtk.Label(_("Languages")))

        self.dialog.vbox.pack_start(notebook, False)
        self.dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)


    def __general_page(self):
        """Return a widget containing the general page"""

        def toggle_callback(cell, path):
            """Callback function to toggle option b"""
            options.toggle(path)
            if 'auto_hide' == path:
                self.cb_refresh_operations()

        vbox = gtk.VBox()

        if online_update_notification_enabled:
            cb_updates = gtk.CheckButton(_("Check periodically for software updates via the Internet"))
            cb_updates.set_active(options.get('check_online_updates'))
            cb_updates.connect('toggled', toggle_callback, 'check_online_updates')
            self.tooltips.set_tip(cb_updates, _("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update."))
            vbox.pack_start(cb_updates, False)

        # TRANSLATORS: This means to hide cleaners which would do
        # nothing.  For example, if Firefox were never used on
        # this system, this option would hide Firefox to simplify
        # the list of cleaners.
        cb_auto_hide = gtk.CheckButton(_("Hide irrelevant cleaners"))
        cb_auto_hide.set_active(options.get('auto_hide'))
        cb_auto_hide.connect('toggled', toggle_callback, 'auto_hide')
        vbox.pack_start(cb_auto_hide, False)

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        cb_shred = gtk.CheckButton(_("Overwrite files to hide contents"))
        cb_shred.set_active(options.get('shred'))
        cb_shred.connect('toggled', toggle_callback, 'shred')
        self.tooltips.set_tip(cb_shred, _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower."))
        vbox.pack_start(cb_shred, False)


        return vbox

    def __drives_page(self):
        """Return widget containing the drives page"""

        def add_drive_cb(button):
            """Callback for adding a drive"""
            chooser = gtk.FileChooserDialog( parent = self.parent, \
                title = _("Choose a folder"),
                buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, \
                gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT), \
                action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

            resp = chooser.run()
            pathname = chooser.get_filename()
            chooser.hide()
            chooser.destroy()
            if gtk.RESPONSE_ACCEPT == resp:
                liststore.append([pathname])
                pathnames.append(pathname)
                options.set_list('shred_drives', pathnames)


        def remove_drive_cb(button):
            """Callback for removing a drive"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            pathname = model[0][0]
            liststore.remove(_iter)
            pathnames.remove(pathname)
            options.set_list('shred_drives', pathnames)


        vbox = gtk.VBox()

        notice = gtk.Label(_("Choose a writable directory for each drive for which to overwrite free space."))
        vbox.pack_start(notice, False)

        liststore = gtk.ListStore(str)

        pathnames = options.get_list('shred_drives')
        if pathnames:
            pathnames = sorted(pathnames)
        if not pathnames:
            pathnames = []
        for pathname in pathnames:
            liststore.append([pathname])
        treeview = gtk.TreeView(model = liststore)
        crt = gtk.CellRendererText()
        tvc = gtk.TreeViewColumn(None, crt, text = 0)
        treeview.append_column(tvc)

        vbox.pack_start(treeview)

        button_add = gtk.Button(_("Add"))
        button_add.connect("clicked", add_drive_cb)
        button_remove = gtk.Button(_("Remove"))
        button_remove.connect("clicked", remove_drive_cb)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        button_box.pack_start(button_add)
        button_box.pack_start(button_remove)
        vbox.pack_start(button_box, False)

        return vbox


    def __languages_page(self):
        """Return widget containing the languages page"""

        def preserve_toggled_cb(cell, path, liststore):
            """Callback for toggling the 'preserve' column"""
            __iter = liststore.get_iter_from_string(path)
            value = not liststore.get_value(__iter, 0)
            liststore.set(__iter, 0, value)
            langid = liststore[path][1]
            options.set_language(langid, value)

        vbox = gtk.VBox()

        notice = gtk.Label(_("All languages will be deleted except those checked."))
        vbox.pack_start(notice)

        # populate data
        import Unix
        liststore = gtk.ListStore('gboolean', str, str)
        for lang in Unix.locales.iterate_languages():
            preserve = options.get_language(lang)
            native = Unix.locales.native_name(lang)
            liststore.append( [ preserve, lang, native ] )

        # create treeview
        treeview = gtk.TreeView(liststore)

        # create column views
        self.renderer0 = gtk.CellRendererToggle()
        self.renderer0.set_property('activatable', True)
        self.renderer0.connect('toggled', preserve_toggled_cb, liststore)
        self.column0 = gtk.TreeViewColumn(_("Preserve"), self.renderer0, active=0)
        treeview.append_column(self.column0)

        self.renderer1 = gtk.CellRendererText()
        self.column1 = gtk.TreeViewColumn(_("Code"), self.renderer1, text=1)
        treeview.append_column(self.column1)

        self.renderer2 = gtk.CellRendererText()
        self.column2 = gtk.TreeViewColumn(_("Name"), self.renderer2, text=2)
        treeview.append_column(self.column2)
        treeview.set_search_column(2)

        # finish
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow, False)
        return vbox


    def run(self):
        """Run the dialog"""
        self.dialog.show_all()
        self.dialog.run()
        self.dialog.destroy()

