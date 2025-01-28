# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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
Preferences dialog
"""

from bleachbit import online_update_notification_enabled
from bleachbit.Options import options
from bleachbit import GuiBasic
from bleachbit.Language import get_active_language_code, get_supported_language_code_name_dict, setup_translation
from bleachbit.Language import get_text as _, pget_text as _p

from gi.repository import Gtk
import logging
import os

logger = logging.getLogger(__name__)

LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2


class PreferencesDialog:

    """Present the preferences dialog and save changes"""

    def __init__(self, parent, cb_refresh_operations, cb_set_windows10_theme):
        self.cb_refresh_operations = cb_refresh_operations
        self.cb_set_windows10_theme = cb_set_windows10_theme

        self.parent = parent
        self.dialog = Gtk.Dialog(title=_("Preferences"),
                                 transient_for=parent,
                                 modal=True,
                                 destroy_with_parent=True)
        self.dialog.set_default_size(300, 200)

        notebook = Gtk.Notebook()
        notebook.append_page(self.__general_page(),
                             Gtk.Label(label=_("General")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_CUSTOM), Gtk.Label(label=_("Custom")))
        notebook.append_page(self.__drives_page(),
                             Gtk.Label(label=_("Drives")))
        if 'posix' == os.name:
            notebook.append_page(self.__languages_page(),
                                 Gtk.Label(label=_("Languages")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_WHITELIST), Gtk.Label(label=_("Whitelist")))

        # pack_start parameters: child, expand (reserve space), fill (actually fill it), padding
        self.dialog.get_content_area().pack_start(notebook, True, True, 0)
        self.dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        self.refresh_operations = False

    def __del__(self):
        """Destructor called when the dialog is closing"""
        if self.refresh_operations:
            # refresh the list of cleaners
            self.cb_refresh_operations()

    def __toggle_callback(self, cell, path):
        """Callback function to toggle option"""
        options.toggle(path)
        if online_update_notification_enabled:
            self.cb_beta.set_sensitive(options.get('check_online_updates'))
            if 'nt' == os.name:
                self.cb_winapp2.set_sensitive(
                    options.get('check_online_updates'))
        if 'auto_hide' == path:
            self.refresh_operations = True
        if 'dark_mode' == path:
            if 'nt' == os.name and options.get('win10_theme'):
                self.cb_set_windows10_theme()
            Gtk.Settings.get_default().set_property(
                'gtk-application-prefer-dark-theme', options.get('dark_mode'))
        if 'win10_theme' == path:
            self.cb_set_windows10_theme()
        if 'debug' == path:
            from bleachbit.Log import set_root_log_level
            set_root_log_level(options.get('debug'))
        if 'kde_shred_menu_option' == path:
            from bleachbit.DesktopMenuOptions import install_kde_service_menu_file
            install_kde_service_menu_file()

    def __general_page(self):
        """Return a widget containing the general page"""

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        if online_update_notification_enabled:
            cb_updates = Gtk.CheckButton.new_with_label(
                _("Check periodically for software updates via the Internet"))
            cb_updates.set_active(options.get('check_online_updates'))
            cb_updates.connect(
                'toggled', self.__toggle_callback, 'check_online_updates')
            cb_updates.set_tooltip_text(
                _("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update."))
            vbox.pack_start(cb_updates, False, True, 0)

            updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            updates_box.set_border_width(10)

            self.cb_beta = Gtk.CheckButton.new_with_label(
                label=_("Check for new beta releases"))
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

        # TRANSLATORS: This means to hide cleaners which would do
        # nothing.  For example, if Firefox were never used on
        # this system, this option would hide Firefox to simplify
        # the list of cleaners.
        cb_auto_hide = Gtk.CheckButton.new_with_label(
            label=_("Hide irrelevant cleaners"))
        cb_auto_hide.set_active(options.get('auto_hide'))
        cb_auto_hide.connect('toggled', self.__toggle_callback, 'auto_hide')
        vbox.pack_start(cb_auto_hide, False, True, 0)

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        cb_shred = Gtk.CheckButton(
            label=_("Overwrite contents of files to prevent recovery"))
        cb_shred.set_active(options.get('shred'))
        cb_shred.connect('toggled', self.__toggle_callback, 'shred')
        cb_shred.set_tooltip_text(
            _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower."))
        vbox.pack_start(cb_shred, False, True, 0)

        # Close the application after cleaning is complete.
        cb_exit = Gtk.CheckButton.new_with_label(
            label=_("Exit after cleaning"))
        cb_exit.set_active(options.get('exit_done'))
        cb_exit.connect('toggled', self.__toggle_callback, 'exit_done')
        vbox.pack_start(cb_exit, False, True, 0)

        # Disable delete confirmation message.
        cb_popup = Gtk.CheckButton(label=_("Confirm before delete"))
        cb_popup.set_active(options.get('delete_confirmation'))
        cb_popup.connect(
            'toggled', self.__toggle_callback, 'delete_confirmation')
        vbox.pack_start(cb_popup, False, True, 0)

        # Use base 1000 over 1024?
        cb_units_iec = Gtk.CheckButton(
            label=_("Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)"))
        cb_units_iec.set_active(options.get("units_iec"))
        cb_units_iec.connect('toggled', self.__toggle_callback, 'units_iec')
        vbox.pack_start(cb_units_iec, False, True, 0)

        # Language auto-detection
        lang_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cb_auto_lang = Gtk.CheckButton(
            label=_("Auto-detect language"))
        is_auto_detect = options.get("auto_detect_lang")
        cb_auto_lang.set_active(is_auto_detect)
        cb_auto_lang.set_tooltip_text(
            _("Automatically detect the system language"))
        lang_box.pack_start(cb_auto_lang, False, True, 0)

        # Language selection dropdown
        lang_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lang_label = Gtk.Label(label=_("Language:"))
        lang_label.set_margin_start(20)  # Add some indentation
        lang_select_box.pack_start(lang_label, False, True, 5)

        lang_combo = Gtk.ComboBoxText()
        current_lang_code = get_active_language_code()
        # Add available languages
        lang_idx = 0
        active_language_idx = None
        try:
            supported_langs = get_supported_language_code_name_dict().items()
        except:
            logger.error("Failed to get list of supported languages")
            supported_langs = [('en_us', 'English')]

        for lang_code, native in supported_langs:
            lang_combo.append_text(f"{native} ({lang_code})")
            if lang_code == current_lang_code:
                active_language_idx = lang_idx
            lang_idx += 1
        # set_wrap_width() prevents infinite space to scroll up.
        # https://github.com/bleachbit/bleachbit/issues/1764
        lang_combo.set_wrap_width(1)
        if active_language_idx:
            lang_combo.set_active(active_language_idx)

        def on_lang_changed(widget):
            text = widget.get_active_text()
            # Extract language code from the format "Native Name (lang_code)"
            lang_code = text.split("(")[-1].rstrip(")")
            if lang_code:
                options.set("forced_language", lang_code, section="bleachbit")
            else:
                logger.warning(
                    "No language code found in combobox for text %s", text)
            setup_translation()
            self.refresh_operations = True

        def on_auto_detect_toggled(widget):
            self.__toggle_callback(None, 'auto_detect_lang')
            is_auto_detect = options.get("auto_detect_lang")
            lang_select_box.set_sensitive(not is_auto_detect)
            if is_auto_detect:
                options.set("forced_language", "", section="bleachbit")
            setup_translation()
            self.refresh_operations = True

        lang_combo.connect('changed', on_lang_changed)
        cb_auto_lang.connect('toggled', on_auto_detect_toggled)

        lang_select_box.pack_start(lang_combo, True, True, 5)
        lang_select_box.set_sensitive(not is_auto_detect)

        lang_box.pack_start(lang_select_box, False, True, 0)
        vbox.pack_start(lang_box, False, True, 0)

        if 'nt' == os.name:
            # Dark theme
            cb_win10_theme = Gtk.CheckButton(_("Windows 10 theme"))
            cb_win10_theme.set_active(options.get("win10_theme"))
            cb_win10_theme.connect(
                'toggled', self.__toggle_callback, 'win10_theme')
            vbox.pack_start(cb_win10_theme, False, True, 0)

        # Dark theme
        self.cb_dark_mode = Gtk.CheckButton(label=_("Dark mode"))
        self.cb_dark_mode.set_active(options.get("dark_mode"))
        self.cb_dark_mode.connect('toggled', self.__toggle_callback, 'dark_mode')
        vbox.pack_start(self.cb_dark_mode, False, True, 0)

        # Remember window geometry (position and size)
        self.cb_geom = Gtk.CheckButton(label=_("Remember window geometry"))
        self.cb_geom.set_active(options.get("remember_geometry"))
        self.cb_geom.connect('toggled', self.__toggle_callback, 'remember_geometry')
        vbox.pack_start(self.cb_geom, False, True, 0)

        # Debug logging
        cb_debug = Gtk.CheckButton(label=_("Show debug messages"))
        cb_debug.set_active(options.get("debug"))
        cb_debug.connect('toggled', self.__toggle_callback, 'debug')
        vbox.pack_start(cb_debug, False, True, 0)

        # KDE context menu shred option
        if 'nt' != os.name:
            cb_kde_shred_menu_option = Gtk.CheckButton(label=_("Add the shred context menu to KDE Plasma"))
            cb_kde_shred_menu_option.set_active(options.get("kde_shred_menu_option"))
            cb_kde_shred_menu_option.connect('toggled', self.__toggle_callback, 'kde_shred_menu_option')
            vbox.pack_start(cb_kde_shred_menu_option, False, True, 0)

        return vbox

    def __drives_page(self):
        """Return widget containing the drives page"""

        def add_drive_cb(button):
            """Callback for adding a drive"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(
                self.parent, title, multiple=False, stock_button=Gtk.STOCK_ADD)
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

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # TRANSLATORS: 'free' means 'unallocated'
        notice = Gtk.Label(label=_(
            "Choose a writable folder for each drive for which to overwrite free space."))
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
        button_add = Gtk.Button.new_with_label(label=_p('button', 'Add'))
        button_add.connect("clicked", add_drive_cb)
        # TRANSLATORS: In the preferences dialog, this button removes a path
        # from the list of paths
        button_remove = Gtk.Button.new_with_label(label=_p('button', 'Remove'))
        button_remove.connect("clicked", remove_drive_cb)

        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
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

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        notice = Gtk.Label(
            label=_("All languages will be deleted except those checked."))
        vbox.pack_start(notice, False, False, 0)

        # populate data
        liststore = Gtk.ListStore('gboolean', str, str)
        for lang, native in get_supported_language_code_name_dict().items():
            liststore.append([(options.get_language(lang)), lang, native])

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
        swindow.set_overlay_scrolling(False)
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow, False, True, 0)
        return vbox

    def _check_path_exists(self, pathname, page_type):
        """Check if a path exists in either whitelist or custom lists
        Returns True if path exists, False otherwise"""
        whitelist_paths = options.get_whitelist_paths()
        custom_paths = options.get_custom_paths()

        # Check in whitelist
        for path in whitelist_paths:
            if pathname == path[1]:
                msg = _("This path already exists in the whitelist.")
                GuiBasic.message_dialog(self.dialog,
                                        msg,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _('Error'))
                return True

        # Check in custom
        for path in custom_paths:
            if pathname == path[1]:
                msg = _("This path already exists in the custom list.")
                GuiBasic.message_dialog(self.dialog,
                                        msg,
                                        Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.OK,
                                        _('Error'))
                return True

        return False

    def _add_path(self, pathname, path_type, page_type, liststore, pathnames):
        """Common function to add a path to either whitelist or custom list"""
        if self._check_path_exists(pathname, page_type):
            return

        type_str = _('File') if path_type == 'file' else _('Folder')
        liststore.append([type_str, pathname])
        pathnames.append([path_type, pathname])

        if page_type == LOCATIONS_WHITELIST:
            options.set_whitelist_paths(pathnames)
        else:
            options.set_custom_paths(pathnames)

    def _remove_path(self, treeview, liststore, pathnames, page_type):
        """Common function to remove a path from either whitelist or custom list"""
        treeselection = treeview.get_selection()
        (model, _iter) = treeselection.get_selected()
        if None == _iter:
            return
        pathname = model[_iter][1]
        liststore.remove(_iter)
        for this_pathname in pathnames:
            if this_pathname[1] == pathname:
                pathnames.remove(this_pathname)
                if page_type == LOCATIONS_WHITELIST:
                    options.set_whitelist_paths(pathnames)
                else:
                    options.set_custom_paths(pathnames)

    def __locations_page(self, page_type):
        """Return a widget containing a list of files and folders"""

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

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
            notice = Gtk.Label(
                label=_("These paths will not be deleted or modified."))
        elif LOCATIONS_CUSTOM == page_type:
            notice = Gtk.Label(
                label=_("These locations can be selected for deletion."))
        vbox.pack_start(notice, False, False, 0)

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
        swindow.set_overlay_scrolling(False)
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)

        vbox.pack_start(swindow, False, True, 0)

        # buttons that modify the list
        def add_file_cb(button):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                self._add_path(pathname, 'file', page_type,
                               liststore, pathnames)

        def add_folder_cb(button):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                self._add_path(pathname, 'folder', page_type,
                               liststore, pathnames)

        def remove_path_cb(button):
            """Callback for removing a path"""
            self._remove_path(treeview, liststore, pathnames, page_type)

        button_add_file = Gtk.Button.new_with_label(
            label=_p('button', 'Add file'))
        button_add_file.connect("clicked", add_file_cb)

        button_add_folder = Gtk.Button.new_with_label(
            label=_p('button', 'Add folder'))
        button_add_folder.connect("clicked", add_folder_cb)

        button_remove = Gtk.Button.new_with_label(label=_p('button', 'Remove'))
        button_remove.connect("clicked", remove_path_cb)

        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
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
