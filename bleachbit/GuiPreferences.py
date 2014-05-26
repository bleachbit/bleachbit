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
Preferences dialog
"""


from gi.repository import Gtk
import os
import sys
import traceback

from Common import _, _p, online_update_notification_enabled
from Options import options
import GuiBasic

if 'nt' == os.name:
    import Windows
if 'posix' == os.name:
    import Unix


LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2


class PreferencesDialog:

    """Present the preferences dialog and save changes"""

    def __init__(self, parent):
        self.parent = parent
        self.dialog = Gtk.Dialog(title=_("Preferences"),
                                 transient_for=parent,
                                 modal=True,
                                 destroy_with_parent=True)
        self.dialog.set_default_size(300, 200)

        notebook = Gtk.Notebook()
        notebook.append_page(self.__general_page(), Gtk.Label(label=_("General")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_CUSTOM), Gtk.Label(label=_("Custom")))
        notebook.append_page(self.__drives_page(), Gtk.Label(label=_("Drives")))
        if 'posix' == os.name:
            notebook.append_page(
                self.__languages_page(), Gtk.Label(label=_("Languages")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_WHITELIST), Gtk.Label(label=_("Whitelist")))

        self.dialog.vbox.pack_start(notebook, True, True, 0)
        self.dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

    def __toggle_callback(self, cell, path):
        """Callback function to toggle option"""
        options.toggle(path)
        if online_update_notification_enabled:
            self.cb_beta.set_sensitive(options.get('check_online_updates'))
            if 'nt' == os.name:
                self.cb_winapp2.set_sensitive(
                    options.get('check_online_updates'))
        if 'auto_start' == path:
            if 'nt' == os.name:
                swc = Windows.start_with_computer
            if 'posix' == os.name:
                swc = Unix.start_with_computer
            try:
                swc(options.get(path))
            except:
                traceback.print_exc()
                dlg = Gtk.MessageDialog(self.parent,
                                        type=Gtk.MessageType.ERROR,
                                        buttons=Gtk.ButtonsType.OK,
                                        message_format=str(sys.exc_info()[1]))
                dlg.run()
                dlg.destroy()

    def __general_page(self):
        """Return a widget containing the general page"""

        if 'nt' == os.name:
            swcc = Windows.start_with_computer_check
        if 'posix' == os.name:
            swcc = Unix.start_with_computer_check

        options.set('auto_start', swcc())

        vbox = Gtk.VBox()

        if online_update_notification_enabled:
            cb_updates = Gtk.CheckButton.new_with_label(
                _("Check periodically for software updates via the Internet"))
            cb_updates.set_active(options.get('check_online_updates'))
            cb_updates.connect(
                'toggled', self.__toggle_callback, 'check_online_updates')
            cb_updates.set_tooltip_text(
                _("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update."))
            vbox.pack_start(cb_updates, False, True, 0)

            updates_box = Gtk.VBox()
            updates_box.set_border_width(10)

            self.cb_beta = Gtk.CheckButton.new_with_label(_("Check for new beta releases"))
            self.cb_beta.set_active(options.get('check_beta'))
            self.cb_beta.set_sensitive(options.get('check_online_updates'))
            self.cb_beta.connect(
                'toggled', self.__toggle_callback, 'check_beta')
            updates_box.pack_start(self.cb_beta, False, True, 0)

            if 'nt' == os.name:
                self.cb_winapp2 = Gtk.CheckButton.new_with_label(
                    _("Download and update cleaners from community (winapp2.ini)"))
                self.cb_winapp2.set_active(options.get('update_winapp2'))
                self.cb_winapp2.set_sensitive(
                    options.get('check_online_updates'))
                self.cb_winapp2.connect(
                    'toggled', self.__toggle_callback, 'update_winapp2')
                updates_box.pack_start(self.cb_winapp2, False, True, 0)

            vbox.pack_start(updates_box, False, True, 0)

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        cb_shred = Gtk.CheckButton.new_with_label(_("Overwrite files to hide contents"))
        cb_shred.set_active(options.get('shred'))
        cb_shred.connect('toggled', self.__toggle_callback, 'shred')
        cb_shred.set_tooltip_text(
            _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower."))
        vbox.pack_start(cb_shred, False, True, 0)

        cb_start = Gtk.CheckButton.new_with_label(_("Start BleachBit with computer"))
        cb_start.set_active(options.get('auto_start'))
        cb_start.connect('toggled', self.__toggle_callback, 'auto_start')
        vbox.pack_start(cb_start, False, True, 0)
        return vbox

    def __drives_page(self):
        """Return widget containing the drives page"""

        def add_drive_cb(button):
            """Callback for adding a drive"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                liststore.append([pathname])
                pathnames.append(pathname)
                options.set_list('shred_drives', pathnames)

        def remove_drive_cb(button):
            """Callback for removing a drive"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                # nothing selected
                return
            pathname = model[_iter][0]
            liststore.remove(_iter)
            pathnames.remove(pathname)
            options.set_list('shred_drives', pathnames)

        vbox = Gtk.VBox()

        # TRANSLATORS: 'free' means 'unallocated'
        notice = Gtk.Label(label=
            _("Choose a writable folder for each drive for which to overwrite free space."))
        notice.set_line_wrap(True)
        vbox.pack_start(notice, False, True, 0)

        liststore = Gtk.ListStore(str)

        pathnames = options.get_list('shred_drives')
        if pathnames:
            pathnames = sorted(pathnames)
        if not pathnames:
            pathnames = []
        for pathname in pathnames:
            liststore.append([pathname])
        treeview = Gtk.TreeView.new_with_model(liststore)
        crt = Gtk.CellRendererText()
        tvc = Gtk.TreeViewColumn(None, crt, text=0)
        treeview.append_column(tvc)

        vbox.pack_start(treeview, True, True, 0)

        # TRANSLATORS: In the preferences dialog, this button adds a path to
        # the list of paths
        button_add = Gtk.Button.new_with_label(_p('button', 'Add'))
        button_add.connect("clicked", add_drive_cb)
        # TRANSLATORS: In the preferences dialog, this button removes a path
        # from the list of paths
        button_remove = Gtk.Button.new_with_label(_p('button', 'Remove'))
        button_remove.connect("clicked", remove_drive_cb)

        button_box = Gtk.HButtonBox()
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.pack_start(button_add, True, True, 0)
        button_box.pack_start(button_remove, True, True, 0)
        vbox.pack_start(button_box, False, True, 0)

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

        vbox = Gtk.VBox()

        notice = Gtk.Label(label=
            _("All languages will be deleted except those checked."))
        vbox.pack_start(notice, True, True, 0)

        # populate data
        liststore = Gtk.ListStore('gboolean', str, str)
        for lang in Unix.locales.iterate_languages():
            preserve = options.get_language(lang)
            native = Unix.locales.native_name(lang)
            liststore.append([preserve, lang, native])

        # create treeview
        treeview = Gtk.TreeView.new_with_model(liststore)

        # create column views
        self.renderer0 = Gtk.CellRendererToggle()
        self.renderer0.set_property('activatable', True)
        self.renderer0.connect('toggled', preserve_toggled_cb, liststore)
        self.column0 = Gtk.TreeViewColumn(
            _("Preserve"), self.renderer0, active=0)
        treeview.append_column(self.column0)

        self.renderer1 = Gtk.CellRendererText()
        self.column1 = Gtk.TreeViewColumn(_("Code"), self.renderer1, text=1)
        treeview.append_column(self.column1)

        self.renderer2 = Gtk.CellRendererText()
        self.column2 = Gtk.TreeViewColumn(_("Name"), self.renderer2, text=2)
        treeview.append_column(self.column2)
        treeview.set_search_column(2)

        # finish
        swindow = Gtk.ScrolledWindow()
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow, False, True, 0)
        return vbox

    def __locations_page(self, page_type):
        """Return a widget containing a list of files and folders"""

        def add_whitelist_file_cb(button):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        print "warning: '%s' already exists in whitelist" % pathname
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_whitelist_paths(pathnames)

        def add_whitelist_folder_cb(button):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        print "warning: '%s' already exists in whitelist" % pathname
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_whitelist_paths(pathnames)

        def remove_whitelist_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                # nothing selected
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_whitelist_paths(pathnames)

        def add_custom_file_cb(button):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        print "warning: '%s' already exists in whitelist" % pathname
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_custom_paths(pathnames)

        def add_custom_folder_cb(button):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        print "warning: '%s' already exists in whitelist" % pathname
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_custom_paths(pathnames)

        def remove_custom_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                # nothing selected
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_custom_paths(pathnames)

        vbox = Gtk.VBox()

        # load data
        if LOCATIONS_WHITELIST == page_type:
            pathnames = options.get_whitelist_paths()
        elif LOCATIONS_CUSTOM == page_type:
            pathnames = options.get_custom_paths()
        liststore = Gtk.ListStore(str, str)
        for paths in pathnames:
            type_code = paths[0]
            type_str = None
            if type_code == 'file':
                type_str = _('File')
            elif type_code == 'folder':
                type_str = _('Folder')
            else:
                raise RuntimeError("Invalid type code: '%s'" % type_code)
            path = paths[1]
            liststore.append([type_str, path])

        if LOCATIONS_WHITELIST == page_type:
            # TRANSLATORS: "Paths" is used generically to refer to both files
            # and folders
            notice = Gtk.Label(label=
                _("Theses paths will not be deleted or modified."))
        elif LOCATIONS_CUSTOM == page_type:
            notice = Gtk.Label(label=
                _("These locations can be selected for deletion."))
        vbox.pack_start(notice, True, True, 0)

        # create treeview
        treeview = Gtk.TreeView.new_with_model(liststore)

        # create column views
        self.renderer0 = Gtk.CellRendererText()
        self.column0 = Gtk.TreeViewColumn(_("Type"), self.renderer0, text=0)
        treeview.append_column(self.column0)

        self.renderer1 = Gtk.CellRendererText()
        # TRANSLATORS: In the tree view "Path" is used generically to refer to a
        # file, a folder, or a pattern describing either
        self.column1 = Gtk.TreeViewColumn(_("Path"), self.renderer1, text=1)
        treeview.append_column(self.column1)
        treeview.set_search_column(1)

        # finish tree view
        swindow = Gtk.ScrolledWindow()
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow, False, True, 0)

        # buttons that modify the list
        button_add_file = Gtk.Button.new_with_label(_p('button', 'Add file'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_file.connect("clicked", add_whitelist_file_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_file.connect("clicked", add_custom_file_cb)

        button_add_folder = Gtk.Button.new_with_label(_p('button', 'Add folder'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_folder.connect("clicked", add_whitelist_folder_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_folder.connect("clicked", add_custom_folder_cb)

        button_remove = Gtk.Button.new_with_label(_p('button', 'Remove'))
        if LOCATIONS_WHITELIST == page_type:
            button_remove.connect("clicked", remove_whitelist_path_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_remove.connect("clicked", remove_custom_path_cb)

        button_box = Gtk.HButtonBox()
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.pack_start(button_add_file, True, True, 0)
        button_box.pack_start(button_add_folder, True, True, 0)
        button_box.pack_start(button_remove, True, True, 0)
        vbox.pack_start(button_box, False, True, 0)

        # return page
        return vbox

    def run(self):
        """Run the dialog"""
        self.dialog.show_all()
        self.dialog.run()
        self.dialog.destroy()
