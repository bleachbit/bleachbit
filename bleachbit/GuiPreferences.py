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

from bleachbit import GuiBasic
from bleachbit import online_update_notification_enabled
from bleachbit import ProtectedPath
from bleachbit.GtkShim import Gtk, GLib
from bleachbit.GuiCookie import CookieManagerDialog
from bleachbit.Language import get_active_language_code, get_supported_language_code_name_dict, setup_translation
from bleachbit.Language import get_text as _, pget_text as _p
from bleachbit.Options import options

import logging
import os

logger = logging.getLogger(__name__)

LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2
EXPERT_MODE_DESCRIPTION = _(
    'Expert mode enables advanced features and relaxes guardrails. '
    'Use extra caution in expert mode.')


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

        self.cookie_manager_dialog = None
        self._locations_notice_css_provider = None

        # Add InfoBar for non-blocking messages
        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect('response', self._on_infobar_response)
        self.infobar_label = Gtk.Label()
        self.infobar_label.set_line_wrap(True)
        self.infobar.get_content_area().add(self.infobar_label)
        self.dialog.get_content_area().pack_start(self.infobar, False, False, 0)
        self._infobar_timeout_id = None

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
            LOCATIONS_WHITELIST), Gtk.Label(label=_("Keep list")))

        # pack_start parameters: child, expand (reserve space), fill (actually fill it), padding
        self.dialog.get_content_area().pack_start(notebook, True, True, 0)
        self.dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        self.refresh_operations = False

    def _create_checkbox(self, label, option_id, vbox=None, tooltip=None,
                         requires_option=None, store_as_attr=None):
        """Helper to create a checkbox with common patterns.

        Args:
            label: The checkbox label text
            option_id: The option ID to connect to
            vbox: Optional vbox to pack the checkbox into
            tooltip: Optional tooltip text
            requires_option: Optional option ID that must be enabled for sensitivity
            store_as_attr: Optional attribute name to store checkbox as self.{name}

        Returns:
            The created Gtk.CheckButton
        """
        cb = Gtk.CheckButton(label=label)
        cb.set_active(options.get(option_id))
        cb.connect('toggled', self.__toggle_callback, option_id)

        if tooltip:
            cb.set_tooltip_text(tooltip)

        if requires_option is not None and not options.get(requires_option):
            cb.set_sensitive(False)
        elif options.has_override(option_id):
            cb.set_sensitive(False)

        if store_as_attr:
            setattr(self, store_as_attr, cb)

        if vbox is None:
            vbox = self.general_vbox
        vbox.pack_start(cb, False, True, 0)

        return cb

    def __del__(self):
        """Destructor called when the dialog is closing"""
        if self.refresh_operations:
            # refresh the list of cleaners
            self.cb_refresh_operations()

    def _on_infobar_response(self, infobar, response_id):
        """Handle InfoBar close button click"""
        if self._infobar_timeout_id:
            GLib.source_remove(self._infobar_timeout_id)
            self._infobar_timeout_id = None
        self.infobar.hide()

    def _hide_infobar(self):
        """Hide the InfoBar (used for auto-dismiss timeout)"""
        self._infobar_timeout_id = None
        self.infobar.hide()
        return False  # Remove from GLib timeout

    def show_infobar(self, message, message_type=Gtk.MessageType.ERROR):
        """Show a non-blocking InfoBar message that auto-dismisses

        Args:
            message: The message to display
            message_type: Gtk.MessageType (ERROR, WARNING, INFO, etc.)
        """
        # Cancel any existing timeout
        if self._infobar_timeout_id:
            GLib.source_remove(self._infobar_timeout_id)
            self._infobar_timeout_id = None
        self.infobar_label.set_text(message)
        self.infobar.set_message_type(message_type)
        self.infobar.show_all()
        self._infobar_timeout_id = GLib.timeout_add_seconds(
            15, self._hide_infobar)

    def __on_expert_mode_toggled(self, cb):
        """Callback for expert mode checkbox"""
        new_value = cb.get_active()
        if new_value:
            from bleachbit.GuiBasic import warning_confirm_dialog
            confirmed, remember_choice = warning_confirm_dialog(
                self.dialog,
                _('Expert mode'),
                EXPERT_MODE_DESCRIPTION,
                show_checkbox=False
            )
            if not confirmed:
                cb.set_active(False)
                return
        options.set('expert_mode', new_value)
        self.reset_warnings_button.set_sensitive(new_value)
        if hasattr(self, 'cb_delete_confirmation'):
            self.cb_delete_confirmation.set_sensitive(new_value)
        if hasattr(self, 'cb_refresh_operations') and self.cb_refresh_operations:
            self.refresh_operations = True

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
            logger.debug("Toggling dark mode to %s", options.get('dark_mode'))
            if not os.name == 'nt':
                self.show_infobar(
                    _("Some GTK themes support do not support both light and dark modes."), Gtk.MessageType.WARNING)
            if 'nt' == os.name and options.get('win10_theme'):
                self.cb_set_windows10_theme()

            settings = self.dialog.get_settings()
            if settings:
                settings.set_property(
                    'gtk-application-prefer-dark-theme', options.get('dark_mode'))
            else:
                logger.warning("Could not get GTK settings to apply dark mode")
        if 'win10_theme' == path:
            self.cb_set_windows10_theme()
        if 'debug' == path:
            from bleachbit.Log import set_root_log_level
            set_root_log_level(options.get('debug'))
        if 'kde_shred_menu_option' == path:
            from bleachbit.DesktopMenuOptions import install_kde_service_menu_file
            install_kde_service_menu_file()

    def __reset_warning_preferences(self, _button):
        """Reset saved warning confirmations."""
        options.clear_warning_preferences()
        self.show_infobar(
            _("Warning confirmations reset."),
            Gtk.MessageType.INFO)

    def __create_update_widgets(self, vbox):
        """Create and configure update-related checkboxes."""
        if not online_update_notification_enabled:
            return
        self._create_checkbox(
            _("Check periodically for software updates via the Internet"),
            'check_online_updates',
            tooltip=_("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update."))

        updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        updates_box.set_border_width(10)

        self._create_checkbox(
            _("Check for new beta releases"),
            'check_beta',
            vbox=updates_box,
            requires_option='check_online_updates',
            store_as_attr='cb_beta')

        if 'nt' == os.name:
            self._create_checkbox(
                _("Download and update cleaners from community (winapp2.ini)"),
                'update_winapp2',
                vbox=updates_box,
                requires_option='check_online_updates',
                store_as_attr='cb_winapp2')
        vbox.pack_start(updates_box, False, True, 0)

    def __create_language_widgets(self, vbox):
        """Create and configure language selection widgets."""
        lang_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        is_auto_detect = options.get("auto_detect_lang")
        self.cb_auto_lang = Gtk.CheckButton(label=_("Auto-detect language"))
        self.cb_auto_lang.set_active(is_auto_detect)
        self.cb_auto_lang.set_tooltip_text(
            _("Automatically detect the system language"))
        lang_box.pack_start(self.cb_auto_lang, False, True, 0)

        self.lang_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lang_label = Gtk.Label(label=_("Language:"))
        lang_label.set_margin_start(20)  # Add some indentation
        self.lang_select_box.pack_start(lang_label, False, True, 5)

        self.lang_combo = Gtk.ComboBoxText()
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
            if native:
                self.lang_combo.append_text(f"{native} ({lang_code})")
            else:
                self.lang_combo.append_text(lang_code)
            if lang_code == current_lang_code:
                active_language_idx = lang_idx
            lang_idx += 1
        if active_language_idx is not None:
            self.lang_combo.set_active(active_language_idx)
        # set_wrap_width() prevents infinite space to scroll up.
        # https://github.com/bleachbit/bleachbit/issues/1764
        self.lang_combo.set_wrap_width(1)
        self.lang_select_box.pack_start(self.lang_combo, False, True, 0)
        lang_box.pack_start(self.lang_select_box, False, True, 0)

        vbox.pack_start(lang_box, False, True, 0)
        self.lang_select_box.set_sensitive(not is_auto_detect)
        self.cb_auto_lang.connect('toggled', self.on_auto_detect_toggled)
        self.lang_combo.connect('changed', self.on_lang_changed)

    def on_lang_changed(self, widget):
        """Callback for when the language combobox is changed."""
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
        # TRANSLATORS: Shown after changing language in preferences
        self.show_infobar(
            _("Restart BleachBit for full effect."),
            Gtk.MessageType.INFO)

    def on_auto_detect_toggled(self, widget):
        """Callback for when the auto-detect language checkbox is toggled."""
        self.__toggle_callback(None, 'auto_detect_lang')
        is_auto_detect = options.get("auto_detect_lang")
        self.lang_select_box.set_sensitive(not is_auto_detect)
        if is_auto_detect:
            options.set("forced_language", "", section="bleachbit")
        setup_translation()
        self.refresh_operations = True
        # TRANSLATORS: Shown after changing language in preferences
        self.show_infobar(
            _("Restart BleachBit for full effect."),
            Gtk.MessageType.INFO)

    def __create_general_checkboxes(self, vbox):
        """Create and configure general checkboxes."""
        # TRANSLATORS: This means to hide cleaners which would do
        # nothing.  For example, if Firefox were never used on
        # this system, this option would hide Firefox to simplify
        # the list of cleaners.
        self._create_checkbox(
            _("Hide irrelevant cleaners"),
            'auto_hide')

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        self._create_checkbox(
            _("Overwrite contents of files to prevent recovery"),
            'shred',
            tooltip=_("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower."))

        self._create_checkbox(
            _("Exit after cleaning"),
            'exit_done')

        self._create_checkbox(
            _("Confirm before delete"),
            'delete_confirmation',
            requires_option='expert_mode',
            store_as_attr='cb_delete_confirmation')

        self.reset_warnings_button = Gtk.Button.new_with_label(
            label=_("Reset warning confirmations"))
        self.reset_warnings_button.set_halign(Gtk.Align.START)
        self.reset_warnings_button.set_margin_top(6)
        self.reset_warnings_button.connect(
            'clicked', self.__reset_warning_preferences)
        self.reset_warnings_button.set_sensitive(options.get('expert_mode'))
        vbox.pack_start(self.reset_warnings_button, False, True, 0)

        self._create_checkbox(
            _("Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)"),
            "units_iec")

    def __general_page(self):
        """Return a widget containing the general page"""

        self.general_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.__create_update_widgets(self.general_vbox)

        self.__create_general_checkboxes(self.general_vbox)

        self._create_checkbox(
            _("Remember window geometry"),
            'remember_geometry')

        self._create_checkbox(
            _("Show debug messages"),
            'debug')

        if 'nt' != os.name:
            self._create_checkbox(
                _("Add the shred context menu to KDE Plasma"),
                'kde_shred_menu_option')

        self._create_checkbox(
            _("Dark mode"),
            'dark_mode')

        if 'nt' == os.name:
            self._create_checkbox(
                _("Windows 10 theme"),
                'win10_theme')

        self.__create_language_widgets(self.general_vbox)

        self._create_checkbox(
            _("Expert mode"),
            'expert_mode',
            tooltip=EXPERT_MODE_DESCRIPTION,
            store_as_attr='cb_expert')
        self.cb_expert.connect('toggled', self.__on_expert_mode_toggled)

        return self.general_vbox

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

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # TRANSLATORS: 'empty' means 'unallocated'
        notice = Gtk.Label(label=_(
            "Choose a writable folder for each drive for which to wipe empty space."))
        notice.set_line_wrap(True)
        notice.set_xalign(0.0)
        notice.set_margin_start(12)
        notice.set_margin_end(12)
        vbox.pack_start(notice, False, True, 0)

        notice2 = Gtk.Label(label=_(
            "Wiping empty space removes traces of files that were deleted without shredding, but it will not free additional disk space. The process can take a very long time and may temporarily slow your computer. It is not necessary if your drive is protected with full-disk encryption. The method works best on traditional hard drives. On solid-state drives, it is less reliable, and frequent use contributes to wear."))
        notice2.set_line_wrap(True)
        notice2.set_xalign(0.0)
        notice2.set_margin_start(12)
        notice2.set_margin_end(12)
        vbox.pack_start(notice2, False, True, 0)

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
        vbox.pack_start(swindow, True, True, 0)
        return vbox

    def _check_path_exists(self, pathname, page_type):
        """Check if a path exists in either keep lists or custom lists
        Returns True if path exists, False otherwise"""
        whitelist_paths = options.get_whitelist_paths()
        custom_paths = options.get_custom_paths()

        # Check in whitelist
        for path in whitelist_paths:
            if pathname == path[1]:
                msg = _("This path already exists in the keep list.")
                self.show_infobar(msg, Gtk.MessageType.ERROR)
                return True

        # Check in custom
        for path in custom_paths:
            if pathname == path[1]:
                msg = _("This path already exists in the custom list.")
                self.show_infobar(msg, Gtk.MessageType.ERROR)
                return True

        return False

    def _check_protected_path(self, pathname):
        """Check if path is protected and warn user if so.

        Returns True if it's safe to proceed, False if user cancelled.
        """
        logger.debug("Checking protected path: %s", pathname)
        match_info = ProtectedPath.check_protected_path(pathname)
        if match_info is None:
            return True

        if not options.get('expert_mode'):
            self.show_infobar(
                _("This path is protected. To bypass protection, enable expert mode."),
                Gtk.MessageType.WARNING)
            return False

        # Check if user already confirmed this path
        normalized = ProtectedPath._normalize_for_comparison(
            pathname, match_info['case_sensitive'])
        warning_key = 'protected_path:' + normalized
        if options.get_warning_preference(warning_key):
            return True

        # Calculate impact
        # FIXME later: this can be very slow with many objects
        logger.debug("Checking protected path impact: %s", pathname)
        impact = ProtectedPath.calculate_impact(pathname)

        # Generate warning message
        warning_msg = ProtectedPath.get_warning_message(pathname, impact)

        # Show warning dialog
        confirmed, remember = GuiBasic.warning_confirm_dialog(
            self.dialog,
            _("Protected Path"),
            warning_msg
        )

        if confirmed and remember:
            options.remember_warning_preference(warning_key)

        return confirmed

    def _add_path(self, pathname, path_type, page_type, liststore, pathnames):
        """Common function to add a path to either whitelist or custom list"""
        if self._check_path_exists(pathname, page_type):
            return

        # Check for protected paths when adding to custom (delete) list
        if page_type == LOCATIONS_CUSTOM:
            if not self._check_protected_path(pathname):
                return

        type_str = _('File') if path_type == 'file' else _('Folder')
        liststore.append([type_str, pathname])
        pathnames.append([path_type, pathname])

        if page_type == LOCATIONS_WHITELIST:
            options.set_whitelist_paths(pathnames)
        else:
            options.set_custom_paths(pathnames)

        # TRANSLATORS: %s is a file or folder path that was just added
        self.show_infobar(_("Added: %s") % pathname,
                          Gtk.MessageType.INFO)

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
                # TRANSLATORS: %s is a file or folder path that was just removed
                self.show_infobar(_("Removed: %s") % pathname,
                                  Gtk.MessageType.INFO)
                break

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
            button_cookie_manager = Gtk.Button.new_with_label(
                label=_("Manage cookies to keep..."))
            button_cookie_manager.set_halign(Gtk.Align.START)
            button_cookie_manager.set_margin_bottom(6)
            button_cookie_manager.connect(
                "clicked", self.__on_manage_cookies_clicked)
            vbox.pack_start(button_cookie_manager, False, False, 0)

        if not self._locations_notice_css_provider:
            self._locations_notice_css_provider = Gtk.CssProvider()
            self._locations_notice_css_provider.load_from_data(b"""
                .bb-locations-notice-whitelist {
                    background-color: rgba(46, 139, 87, 0.12);
                    border-radius: 6px;
                    padding: 6px;
                }
                .bb-locations-notice-custom {
                    background-color: rgba(210, 120, 0, 0.12);
                    border-radius: 6px;
                    padding: 6px;
                }
            """)

        if LOCATIONS_WHITELIST == page_type:
            # TRANSLATORS: "Paths" is used generically to refer to both files
            # and folders
            notice_text = _("These paths will not be deleted or modified.")
            notice_icon = "emblem-readonly"
            notice_class = "bb-locations-notice-whitelist"
        elif LOCATIONS_CUSTOM == page_type:
            notice_text = _("These locations can be selected for deletion.")
            notice_icon = "edit-delete"
            notice_class = "bb-locations-notice-custom"

        notice_label = Gtk.Label(label=notice_text)
        notice_label.set_line_wrap(True)
        notice_label.set_xalign(0.0)

        notice_image = Gtk.Image.new_from_icon_name(
            notice_icon, Gtk.IconSize.MENU)
        notice_image.set_valign(Gtk.Align.START)

        notice_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        notice_box.pack_start(notice_image, False, False, 0)
        notice_box.pack_start(notice_label, True, True, 0)

        notice_frame = Gtk.EventBox()
        notice_frame.set_visible_window(True)
        notice_frame.add(notice_box)
        notice_frame.set_margin_bottom(6)
        notice_frame.set_margin_top(6)
        style_context = notice_frame.get_style_context()
        style_context.add_provider(
            self._locations_notice_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        style_context.add_class(notice_class)
        vbox.pack_start(notice_frame, False, False, 0)

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

        vbox.pack_start(swindow, True, True, 0)

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

    def __on_manage_cookies_clicked(self, _button):
        """Open the cookie manager dialog, reusing an existing window if open."""
        if self.cookie_manager_dialog:
            self.cookie_manager_dialog.present()
            return

        # Temporarily lift modality on the preferences dialog and disable it
        self.dialog.set_modal(False)
        self.dialog.set_sensitive(False)

        self.cookie_manager_dialog = CookieManagerDialog()
        self.cookie_manager_dialog.set_modal(True)

        if isinstance(self.cookie_manager_dialog, Gtk.Window):
            self.cookie_manager_dialog.set_transient_for(self.dialog)
            self.cookie_manager_dialog.set_destroy_with_parent(True)

        self.cookie_manager_dialog.connect(
            "destroy", self.__on_cookie_manager_destroyed)
        self.cookie_manager_dialog.show_all()

    def __on_cookie_manager_destroyed(self, _widget):
        """Reset reference when cookie manager window closes."""
        self.cookie_manager_dialog = None
        # Restore preferences dialog modality and interactivity
        self.dialog.set_sensitive(True)
        self.dialog.set_modal(True)

    def run(self):
        """Run the dialog"""
        self.dialog.show_all()
        self.infobar.hide()
        self.dialog.run()
        self.dialog.destroy()
