#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
GTK graphical user interface
"""

from bleachbit import GuiBasic
from bleachbit import Cleaner, FileUtilities
from bleachbit import _, APP_NAME, appicon_path, portable_mode, windows10_theme_path
from bleachbit.Options import options
from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.Cleaner import backends, register_cleaners
import bleachbit
from gi.repository import Gtk, Gdk, GObject, GLib, Gio

import glob
import logging
import os
import sys
import threading
import time

import gi
gi.require_version('Gtk', '3.0')


if os.name == 'nt':
    from bleachbit import Windows

logger = logging.getLogger(__name__)


def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    return wrapper


def notify_gi(msg):
    """Show a pop-up notification.

    The Windows pygy-aio installer does not include notify, so this is just for Linux.
    """
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
    if Notify.init(APP_NAME):
        notify = Notify.Notification.new('BleachBit', msg, 'bleachbit')
        notify.set_hint("desktop-entry", GLib.Variant('s', 'bleachbit'))
        notify.show()
        notify.set_timeout(10000)


def notify_plyer(msg):
    """Show a pop-up notification.

    Linux distributions do not include plyer, so this is just for Windows.
    """
    from bleachbit import bleachbit_exe_path

    # On Windows 10,  PNG does not work.
    __icon_fns = (
        os.path.normpath(os.path.join(bleachbit_exe_path,
                                      'share\\bleachbit.ico')),
        os.path.normpath(os.path.join(bleachbit_exe_path,
                                      'windows\\bleachbit.ico')))

    icon_fn = None
    for __icon_fn in __icon_fns:
        if os.path.exists(__icon_fn):
            icon_fn = __icon_fn
            break

    from plyer import notification
    notification.notify(
        title=APP_NAME,
        message=msg,
        app_name=APP_NAME,  # not shown on Windows 10
        app_icon=icon_fn,
    )


def notify(msg):
    """Show a popup-notification"""
    import importlib
    if importlib.util.find_spec('plyer'):
        # On Windows, use Plyer.
        notify_plyer(msg)
        return
    # On Linux, use GTK Notify.
    notify_gi(msg)


class Bleachbit(Gtk.Application):
    _window = None
    _shred_paths = None
    _auto_exit = False

    def __init__(self, uac=True, shred_paths=None, auto_exit=False):

        application_id_suffix = self._init_windows_misc(auto_exit, shred_paths, uac)
        application_id = '{}{}'.format('org.gnome.Bleachbit', application_id_suffix)
        Gtk.Application.__init__(
            self, application_id=application_id, flags=Gio.ApplicationFlags.FLAGS_NONE)
        GObject.threads_init()

        if auto_exit:
            # This is used for automated testing of whether the GUI can start.
            # It is called from assert_execute_console() in windows/setup_py2exe.py
            self._auto_exit = True        

        if shred_paths:
            self._shred_paths = shred_paths

        if os.name == 'nt':
            # clean up nonce files https://github.com/bleachbit/bleachbit/issues/858
            import atexit
            atexit.register(Windows.cleanup_nonce)

            # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
            # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
            # https://www.bleachbit.org/forum/074-fails-errors
            try:
                import sqlite3
            except ImportError:
                logger.exception(
                    _("Error loading the SQLite module: the antivirus software may be blocking it."))

    def _init_windows_misc(self, auto_exit, shred_paths, uac):
        application_id_suffix = ''
        is_context_menu_executed = auto_exit and shred_paths
        if os.name == 'nt':
            if Windows.elevate_privileges(uac):
                # privileges escalated in other process
                sys.exit(0)

            if is_context_menu_executed:
                # When we have a running application and executing the Windows
                # context menu command we start a new process with new application_id.
                # That is because the command line arguments of the context menu command
                # are not passed to the already running instance.
                application_id_suffix = 'ContextMenuShred'
        return application_id_suffix

    def build_app_menu(self):
        """Build the application menu

        On Linux with GTK 3.24, this code is necessary but not sufficient for
        the menu to work. The headerbar code is also needed.

        On Windows with GTK 3.18, this cde is sufficient for the menu to work.
        """

        builder = Gtk.Builder()
        builder.add_from_file(bleachbit.app_menu_filename)
        menu = builder.get_object('app-menu')
        self.set_app_menu(menu)

        # set up mappings between <attribute name="action"> in app-menu.ui and methods in this class
        actions = {'shredFiles': self.cb_shred_file,
                   'shredFolders': self.cb_shred_folder,
                   'shredClipboard': self.cb_shred_clipboard,
                   'wipeFreeSpace': self.cb_wipe_free_space,
                   'makeChaff': self.cb_make_chaff,
                   'shredQuit': self.cb_shred_quit,
                   'preferences': self.cb_preferences_dialog,
                   'systemInformation': self.system_information_dialog,
                   'help': self.cb_help,
                   'about': self.about}

        for action_name, callback in actions.items():
            action = Gio.SimpleAction.new(action_name, None)
            action.connect('activate', callback)
            self.add_action(action)

    def cb_help(self, action, param):
        """Callback for help"""
        GuiBasic.open_url(bleachbit.help_contents_url, self._window)

    def cb_make_chaff(self, action, param):
        """Callback to make chaff"""
        from bleachbit.GuiChaff import ChaffDialog
        cd = ChaffDialog(self._window)
        cd.run()

    def cb_shred_file(self, action, param):
        """Callback for shredding a file"""

        # get list of files
        paths = GuiBasic.browse_files(self._window, _("Choose files to shred"))
        if not paths:
            return
        GUI.shred_paths(self._window, paths)

    def cb_shred_folder(self, action, param):
        """Callback for shredding a folder"""

        paths = GuiBasic.browse_folder(self._window,
                                       _("Choose folder to shred"),
                                       multiple=True,
                                       stock_button=_('_Delete'))
        if not paths:
            return
        GUI.shred_paths(self._window, paths)

    def cb_shred_clipboard(self, action, param):
        """Callback for menu option: shred paths from clipboard"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.request_targets(self.cb_clipboard_uri_received)

    def cb_clipboard_uri_received(self, clipboard, targets, data):
        """Callback for when URIs are received from clipboard"""
        shred_paths = None
        if Gdk.atom_intern_static_string('text/uri-list') in targets:
            # Linux
            shred_uris = clipboard.wait_for_contents(
                Gdk.atom_intern_static_string('text/uri-list')).get_uris()
            shred_paths = FileUtilities.uris_to_paths(shred_uris)
        elif Gdk.atom_intern_static_string('FileNameW') in targets:
            # Windows
            # Use non-GTK+ functions because because GTK+ 2 does not work.
            shred_paths = Windows.get_clipboard_paths()
        if shred_paths:
            GUI.shred_paths(self._window, shred_paths)
        else:
            logger.warning(_('No paths found in clipboard.'))

    def cb_shred_quit(self, action, param):
        """Shred settings (for privacy reasons) and quit"""
        # build a list of paths to delete
        paths = []
        if os.name == 'nt' and portable_mode:
            # in portable mode on Windows, the options directory includes
            # executables
            paths.append(bleachbit.options_file)
            if os.path.isdir(bleachbit.personal_cleaners_dir):
                paths.append(bleachbit.personal_cleaners_dir)
            for f in glob.glob(os.path.join(bleachbit.options_dir, "*.bz2")):
                paths.append(f)
        else:
            paths.append(bleachbit.options_dir)

        # prompt the user to confirm
        if not GUI.shred_paths(self._window, paths, shred_settings=True):
            logger.debug('user aborted shred')
            # aborted
            return

        # Quit the application through the idle loop to allow the worker
        # to delete the files.  Use the lowest priority because the worker
        # uses the standard priority. Otherwise, this will quit before
        # the files are deleted.
        #
        # Rebuild a minimal bleachbit.ini when quitting
        GLib.idle_add(self.quit, None, None, True,
                      priority=GObject.PRIORITY_LOW)

    def cb_wipe_free_space(self, action, param):
        """callback to wipe free space in arbitrary folder"""
        path = GuiBasic.browse_folder(self._window,
                                      _("Choose a folder"),
                                      multiple=False, stock_button=_('_OK'))
        if not path:
            # user cancelled
            return

        backends['_gui'] = Cleaner.create_wipe_cleaner(path)

        # execute
        operations = {'_gui': ['free_disk_space']}
        self._window.preview_or_run_operations(True, operations)

    def get_preferences_dialog(self):
        return self._window.get_preferences_dialog()

    def cb_preferences_dialog(self, action, param):
        """Callback for preferences dialog"""
        pref = self.get_preferences_dialog()
        pref.run()

        # In case the user changed the log level...
        GUI.update_log_level(self._window)

    def get_about_dialog(self):
        dialog = Gtk.AboutDialog(comments='Program to clean unnecessary files',
                                 copyright='Copyright (C) 2008-2021 Andrew Ziem',
                                 program_name=APP_NAME,
                                 version=bleachbit.APP_VERSION,
                                 website=bleachbit.APP_URL,
                                 transient_for=self._window)
        try:
            with open(bleachbit.license_filename) as f_license:
                dialog.set_license(f_license.read())
        except (IOError, TypeError):
            dialog.set_license(
                _("GNU General Public License version 3 or later.\nSee https://www.gnu.org/licenses/gpl-3.0.txt"))
        # dialog.set_name(APP_NAME)
        # TRANSLATORS: Maintain the names of translators here.
        # Launchpad does this automatically for translations
        # typed in Launchpad. This is a special string shown
        # in the 'About' box.
        dialog.set_translator_credits(_("translator-credits"))
        if appicon_path and os.path.exists(appicon_path):
            icon = Gtk.Image.new_from_file(appicon_path)
            dialog.set_logo(icon.get_pixbuf())

        return dialog

    def about(self, _action, _param):
        """Create and show the about dialog"""
        dialog = self.get_about_dialog()
        dialog.run()
        dialog.destroy()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.build_app_menu()

    def quit(self, _action=None, _param=None, init_configuration=False):
        if init_configuration:
            bleachbit.Options.init_configuration()
        self._window.destroy()

    def get_system_information_dialog(self):
        """Show system information dialog"""
        dialog = Gtk.Dialog(_("System information"), self._window)
        dialog.set_default_size(600, 400)
        txtbuffer = Gtk.TextBuffer()
        from bleachbit import SystemInformation
        txt = SystemInformation.get_system_information()
        txtbuffer.set_text(txt)
        textview = Gtk.TextView.new_with_buffer(txtbuffer)
        textview.set_editable(False)
        swindow = Gtk.ScrolledWindow()
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.add(textview)
        dialog.vbox.pack_start(swindow, True, True, 0)
        dialog.add_buttons(Gtk.STOCK_COPY, 100,
                           Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        return (dialog, txt)

    def system_information_dialog(self, _action, _param):
        dialog, txt = self.get_system_information_dialog()
        dialog.show_all()
        while True:
            rc = dialog.run()
            if rc != 100:
                break
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(txt, -1)
        dialog.destroy()

    def do_activate(self):
        if not self._window:
            self._window = GUI(
                application=self, title=APP_NAME, auto_exit=self._auto_exit)
        self._window.present()
        if self._shred_paths:
            GLib.idle_add(GUI.shred_paths, self._window, self._shred_paths, priority=GObject.PRIORITY_LOW)
            # When we shred paths and auto exit with the Windows Explorer context menu command we close the
            # application in GUI.shred_paths, because if it is closed from here there are problems.
            # Most probably this is something related with how GTK handles idle quit calls.
        elif self._auto_exit:
            GLib.idle_add(self.quit,
                          priority=GObject.PRIORITY_LOW)
            print('Success')


class TreeInfoModel:
    """Model holds information to be displayed in the tree view"""

    def __init__(self):
        self.tree_store = Gtk.TreeStore(
            GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_PYOBJECT, GObject.TYPE_STRING)
        if not self.tree_store:
            raise Exception("cannot create tree store")
        self.row_changed_handler_id = None
        self.refresh_rows()
        self.tree_store.set_sort_func(3, self.sort_func)
        self.tree_store.set_sort_column_id(3, Gtk.SortType.ASCENDING)

    def get_model(self):
        """Return the tree store"""
        return self.tree_store

    def on_row_changed(self, __treemodel, path, __iter):
        """Event handler for when a row changes"""
        parent = self.tree_store[path[0]][2]
        child = None
        if len(path) == 2:
            child = self.tree_store[path][2]
        value = self.tree_store[path][1]
        options.set_tree(parent, child, value)

    def refresh_rows(self):
        """Clear rows (cleaners) and add them fresh"""
        if self.row_changed_handler_id:
            self.tree_store.disconnect(self.row_changed_handler_id)
        self.tree_store.clear()
        for key in sorted(backends):
            if not any(backends[key].get_options()):
                # localizations has no options, so it should be hidden
                # https://github.com/az0/bleachbit/issues/110
                continue
            c_name = backends[key].get_name()
            c_id = backends[key].get_id()
            c_value = options.get_tree(c_id, None)
            if not c_value and options.get('auto_hide') and backends[key].auto_hide():
                logger.debug("automatically hiding cleaner '%s'", c_id)
                continue
            parent = self.tree_store.append(None, (c_name, c_value, c_id, ""))
            for (o_id, o_name) in backends[key].get_options():
                o_value = options.get_tree(c_id, o_id)
                self.tree_store.append(parent, (o_name, o_value, o_id, ""))
        self.row_changed_handler_id = self.tree_store.connect("row-changed",
                                                              self.on_row_changed)

    def sort_func(self, model, iter1, iter2, _user_data):
        """Sort the tree by the display name"""
        value1 = model[iter1][0].lower()
        value2 = model[iter2][0].lower()
        if value1 == value2:
            return 0
        if value1 > value2:
            return 1
        return -1


class TreeDisplayModel:
    """Displays the info model in a view"""

    def make_view(self, model, parent, context_menu_event):
        """Create and return a TreeView object"""
        self.view = Gtk.TreeView.new_with_model(model)

        # hide headers
        self.view.set_headers_visible(False)

        # listen for right click (context menu)
        self.view.connect("button_press_event", context_menu_event)

        # first column
        self.renderer0 = Gtk.CellRendererText()
        self.column0 = Gtk.TreeViewColumn(_("Name"), self.renderer0, text=0)
        self.view.append_column(self.column0)
        self.view.set_search_column(0)

        # second column
        self.renderer1 = Gtk.CellRendererToggle()
        self.renderer1.set_property('activatable', True)
        self.renderer1.connect('toggled', self.col1_toggled_cb, model, parent)
        self.column1 = Gtk.TreeViewColumn(_("Active"), self.renderer1)
        self.column1.add_attribute(self.renderer1, "active", 1)
        self.view.append_column(self.column1)

        # third column
        self.renderer2 = Gtk.CellRendererText()
        self.renderer2.set_alignment(1.0, 0.0)
        # TRANSLATORS: Size is the label for the column that shows how
        # much space an option would clean or did clean
        self.column2 = Gtk.TreeViewColumn(_("Size"), self.renderer2, text=3)
        self.column2.set_alignment(1.0)
        self.view.append_column(self.column2)

        # finish
        self.view.expand_all()
        return self.view

    def set_cleaner(self, path, model, parent_window, value):
        """Activate or deactivate option of cleaner."""
        assert isinstance(value, bool)
        assert isinstance(model, Gtk.TreeStore)
        cleaner_id = None
        i = path
        if isinstance(i, str):
            # type is either str or gtk.TreeIter
            i = model.get_iter(path)
        parent = model.iter_parent(i)
        if parent:
            # this is an option (child), not a cleaner (parent)
            cleaner_id = model[parent][2]
            option_id = model[path][2]
        if cleaner_id and value:
            # When enabling an option, present any warnings.
            # (When disabling an option, there is no need to present warnings.)
            warning = backends[cleaner_id].get_warning(option_id)
            # TRANSLATORS: %(cleaner) may be Firefox, System, etc.
            # %(option) may be cache, logs, cookies, etc.
            # %(warning) may be 'This option is really slow'
            msg = _("Warning regarding %(cleaner)s - %(option)s:\n\n%(warning)s") % \
                {'cleaner': model[parent][0],
                 'option': model[path][0],
                 'warning': warning}
            if warning:
                resp = GuiBasic.message_dialog(parent_window,
                                               msg,
                                               Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL)
                if Gtk.ResponseType.OK != resp:
                    # user cancelled, so don't toggle option
                    return
        model[path][1] = value

    def col1_toggled_cb(self, cell, path, model, parent_window):
        """Callback for toggling cleaners"""
        is_toggled_on = not model[path][1]  # Is the new state enabled?
        self.set_cleaner(path, model, parent_window, is_toggled_on)
        i = model.get_iter(path)
        parent = model.iter_parent(i)
        if parent and is_toggled_on:
            # If child is enabled, then also enable the parent.
            model[parent][1] = True
        # If all siblings were toggled off, then also disable the parent.
        if parent and not is_toggled_on:
            sibling = model.iter_nth_child(parent, 0)
            any_sibling_enabled = False
            while sibling:
                if model[sibling][1]:
                    any_sibling_enabled = True
                sibling = model.iter_next(sibling)
            if not any_sibling_enabled:
                model[parent][1] = False
        # If toggled and has children, then do the same for each child.
        child = model.iter_children(i)
        while child:
            self.set_cleaner(child, model, parent_window, is_toggled_on)
            child = model.iter_next(child)
        return


class GUI(Gtk.ApplicationWindow):
    """The main application GUI"""
    _style_provider = None
    _style_provider_regular = None
    _style_provider_dark = None

    def __init__(self, auto_exit, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        self._show_splash_screen()

        self._auto_exit = auto_exit

        self.set_wmclass(APP_NAME, APP_NAME)
        self.populate_window()

        # Redirect logging to the GUI.
        bb_logger = logging.getLogger('bleachbit')
        from bleachbit.Log import GtkLoggerHandler
        self.gtklog = GtkLoggerHandler(self.append_text)
        bb_logger.addHandler(self.gtklog)

        # process any delayed logs
        from bleachbit.Log import DelayLog
        if isinstance(sys.stderr, DelayLog):
            for msg in sys.stderr.read():
                self.append_text(msg)
            # if stderr was redirected - keep redirecting it
            sys.stderr = self.gtklog

        self.set_windows10_theme()
        Gtk.Settings.get_default().set_property(
            'gtk-application-prefer-dark-theme', options.get('dark_mode'))

        if options.is_corrupt():
            logger.error(
                _('Resetting the configuration file because it is corrupt: %s') % bleachbit.options_file)
            bleachbit.Options.init_configuration()

        GLib.idle_add(self.cb_refresh_operations)

    def _show_splash_screen(self):
        if os.name != 'nt':
            return

        font_conf_file = Windows.get_font_conf_file()
        if not os.path.exists(font_conf_file):
            logger.error('No fonts.conf file {}'.format(font_conf_file))
            return

        has_cache = Windows.has_fontconfig_cache(font_conf_file)
        if not has_cache:
            Windows.splash_thread.start()

    def _confirm_delete(self, mention_preview, shred_settings=False):
        if options.get("delete_confirmation"):
            return GuiBasic.delete_confirmation_dialog(self, mention_preview, shred_settings=shred_settings)
        return True

    def destroy(self):
        """Prevent textbuffer usage during UI destruction"""
        self.textbuffer = None
        super(GUI, self).destroy()

    def get_preferences_dialog(self):
        return PreferencesDialog(
            self,
            self.cb_refresh_operations,
            self.set_windows10_theme)

    def shred_paths(self, paths, shred_settings=False):
        """Shred file or folders

        When shredding_settings=True:
        If user confirms to delete, then returns True.  If user aborts, returns
        False.
        """
        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        # preview and confirm
        operations = {'_gui': ['files']}
        self.preview_or_run_operations(False, operations)

        if self._confirm_delete(False, shred_settings):
            # delete
            self.preview_or_run_operations(True, operations)
            if shred_settings:
                return True

        if self._auto_exit:
            GLib.idle_add(self.close,
                              priority=GObject.PRIORITY_LOW)

        # user aborted
        return False

    def append_text(self, text, tag=None, __iter=None, scroll=True):
        """Add some text to the main log"""
        if self.textbuffer is None:
            # textbuffer was destroyed.
            return
        if not __iter:
            __iter = self.textbuffer.get_end_iter()
        if tag:
            self.textbuffer.insert_with_tags_by_name(__iter, text, tag)
        else:
            self.textbuffer.insert(__iter, text)
        # Scroll to end.  If the command is run directly instead of
        # through the idle loop, it may only scroll most of the way
        # as seen on Ubuntu 9.04 with Italian and Spanish.
        if scroll:
            GLib.idle_add(lambda: self.textbuffer is not None and
                          self.textview.scroll_mark_onscreen(
                              self.textbuffer.get_insert()))

    def update_log_level(self):
        """This gets called when the log level might have changed via the preferences."""
        self.gtklog.update_log_level()

    def on_selection_changed(self, selection):
        """When the tree view selection changed"""
        model = self.view.get_model()
        selected_rows = selection.get_selected_rows()
        if not selected_rows[1]:  # empty
            # happens when searching in the tree view
            return
        paths = selected_rows[1][0]
        row = paths[0]
        name = model[row][0]
        cleaner_id = model[row][2]
        self.progressbar.hide()
        description = backends[cleaner_id].get_description()
        self.textbuffer.set_text("")
        self.append_text(name + "\n", 'operation', scroll=False)
        if not description:
            description = ""
        self.append_text(description + "\n\n\n", 'description', scroll=False)
        for (label, description) in backends[cleaner_id].get_option_descriptions():
            self.append_text(label, 'option_label', scroll=False)
            if description:
                self.append_text(': ', 'option_label', scroll=False)
                self.append_text(description, scroll=False)
            self.append_text("\n\n", scroll=False)

    def get_selected_operations(self):
        """Return a list of the IDs of the selected operations in the tree view"""
        ret = []
        model = self.tree_store.get_model()
        path = Gtk.TreePath(0)
        __iter = model.get_iter(path)
        while __iter:
            if model[__iter][1]:
                ret.append(model[__iter][2])
            __iter = model.iter_next(__iter)
        return ret

    def get_operation_options(self, operation):
        """For the given operation ID, return a list of the selected option IDs."""
        ret = []
        model = self.tree_store.get_model()
        path = Gtk.TreePath(0)
        __iter = model.get_iter(path)
        while __iter:
            if operation == model[__iter][2]:
                iterc = model.iter_children(__iter)
                if not iterc:
                    return None
                while iterc:
                    if model[iterc][1]:
                        # option is enabled
                        ret.append(model[iterc][2])
                    iterc = model.iter_next(iterc)
                return ret
            __iter = model.iter_next(__iter)
        return None

    def set_sensitive(self, is_sensitive):
        """Disable commands while an operation is running"""
        self.view.set_sensitive(is_sensitive)
        self.preview_button.set_sensitive(is_sensitive)
        self.run_button.set_sensitive(is_sensitive)
        self.stop_button.set_sensitive(not is_sensitive)

    def run_operations(self, __widget):
        """Event when the 'delete' toolbar button is clicked."""
        # fixme: should present this dialog after finding operations

        # Disable delete confirmation message.
        # if the option is selected under preference.

        if self._confirm_delete(True):
            self.preview_or_run_operations(True)

    def preview_or_run_operations(self, really_delete, operations=None):
        """Preview operations or run operations (delete files)"""

        assert isinstance(really_delete, bool)
        from bleachbit import Worker
        self.start_time = None
        if not operations:
            operations = {
                operation: self.get_operation_options(operation)
                for operation in self.get_selected_operations()
            }
        assert isinstance(operations, dict)
        if not operations:  # empty
            GuiBasic.message_dialog(self,
                                    _("You must select an operation"),
                                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK)
            return
        try:
            self.set_sensitive(False)
            self.textbuffer.set_text("")
            self.progressbar.show()
            self.worker = Worker.Worker(self, really_delete, operations)
        except Exception:
            logger.exception('Error in Worker()')
        else:
            self.start_time = time.time()
            worker = self.worker.run()
            GLib.idle_add(worker.__next__)

    def worker_done(self, worker, really_delete):
        """Callback for when Worker is done"""
        self.progressbar.set_text("")
        self.progressbar.set_fraction(1)
        self.progressbar.set_text(_("Done."))
        self.textview.scroll_mark_onscreen(self.textbuffer.get_insert())
        self.set_sensitive(True)

        # Close the program after cleaning is completed.
        # if the option is selected under preference.

        if really_delete:
            if options.get("exit_done"):
                sys.exit()

        # notification for long-running process
        elapsed = (time.time() - self.start_time)
        logger.debug('elapsed time: %d seconds', elapsed)
        if elapsed < 10 or self.is_active():
            return
        notify(_("Done."))

    def create_operations_box(self):
        """Create and return the operations box (which holds a tree view)"""
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_overlay_scrolling(False)
        self.tree_store = TreeInfoModel()
        display = TreeDisplayModel()
        mdl = self.tree_store.get_model()
        self.view = display.make_view(
            mdl, self, self.context_menu_event)
        self.view.get_selection().connect("changed", self.on_selection_changed)
        scrollbar_width = scrolled_window.get_vscrollbar().get_preferred_width()[1]
        self.view.set_margin_right(scrollbar_width) # avoid conflict with scrollbar
        scrolled_window.add(self.view)
        return scrolled_window

    def cb_refresh_operations(self):
        """Callback to refresh the list of cleaners"""
        # Is this the first time in this session?
        if not hasattr(self, 'recognized_cleanerml') and not self._auto_exit:
            from bleachbit import RecognizeCleanerML
            RecognizeCleanerML.RecognizeCleanerML()
            self.recognized_cleanerml = True
        # reload cleaners from disk
        self.view.expand_all()
        self.progressbar.show()
        rc = register_cleaners(self.update_progress_bar,
                               self.cb_register_cleaners_done)
        GLib.idle_add(rc.__next__)
        return False

    def cb_register_cleaners_done(self):
        """Called from register_cleaners()"""
        self.progressbar.hide()
        # update tree view
        self.tree_store.refresh_rows()
        # expand tree view
        self.view.expand_all()

        # Check for online updates.
        if not self._auto_exit and \
            bleachbit.online_update_notification_enabled and \
            options.get("check_online_updates") and \
                not hasattr(self, 'checked_for_updates'):
            self.checked_for_updates = True
            self.check_online_updates()

        # Show information for first start.
        # (The first start flag is set also for each new version.)
        if options.get("first_start") and not self._auto_exit:
            if os.name == 'posix':
                self.append_text(
                    _('Access the application menu by clicking the hamburger icon on the title bar.'))
                pref = self.get_preferences_dialog()
                pref.run()
            elif os.name == 'nt':
                self.append_text(
                    _('Access the application menu by clicking the logo on the title bar.'))
            options.set('first_start', False)

        if os.name == 'nt':
            # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
            # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
            # http://bleachbit.sourceforge.net/forum/074-fails-errors
            try:
                import sqlite3
            except ImportError as e:
                self.append_text(
                    _("Error loading the SQLite module: the antivirus software may be blocking it."), 'error')

        # Show notice about admin privileges.
        if os.name == 'posix' and os.path.expanduser('~') == '/root':
            self.append_text(
                _('You are running BleachBit with administrative privileges for cleaning shared parts of the system, and references to the user profile folder will clean only the root account.')+'\n')
        if os.name == 'nt' and options.get('shred'):
            from win32com.shell.shell import IsUserAnAdmin
            if not IsUserAnAdmin():
                self.append_text(
                    _('Run BleachBit with administrator privileges to improve the accuracy of overwriting the contents of files.'))
                self.append_text('\n')

        # remove from idle loop (see GObject.idle_add)
        return False

    def cb_run_option(self, widget, really_delete, cleaner_id, option_id):
        """Callback from context menu to delete/preview a single option"""
        operations = {cleaner_id: [option_id]}

        # preview
        if not really_delete:
            self.preview_or_run_operations(False, operations)
            return

        # delete
        if self._confirm_delete(False):
            self.preview_or_run_operations(True, operations)
            return

    def cb_stop_operations(self, __widget):
        """Callback to stop the preview/cleaning process"""
        self.worker.abort()

    def context_menu_event(self, treeview, event):
        """When user right clicks on the tree view"""
        if event.button != 3:
            return False
        pathinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if not pathinfo:
            return False
        path, col, _cellx, _celly = pathinfo
        treeview.grab_focus()
        treeview.set_cursor(path, col, 0)
        # context menu applies only to children, not parents
        if len(path) != 2:
            return False
        # find the selected option
        model = treeview.get_model()
        option_id = model[path][2]
        cleaner_id = model[path[0]][2]
        # make a menu
        menu = Gtk.Menu()
        menu.connect('hide', lambda widget: widget.detach())
        # TRANSLATORS: this is the context menu
        preview_item = Gtk.MenuItem(label=_("Preview"))
        preview_item.connect('activate', self.cb_run_option,
                             False, cleaner_id, option_id)
        menu.append(preview_item)
        # TRANSLATORS: this is the context menu
        clean_item = Gtk.MenuItem(label=_("Clean"))
        clean_item.connect('activate', self.cb_run_option,
                           True, cleaner_id, option_id)
        menu.append(clean_item)

        # show the context menu
        menu.attach_to_widget(treeview)
        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)
        return True

    def setup_drag_n_drop(self):
        def cb_drag_data_received(widget, _context, _x, _y, data, info, _time):
            if info == 80:
                uris = data.get_uris()
                paths = FileUtilities.uris_to_paths(uris)
                self.shred_paths(paths)

        def setup_widget(widget):
            widget.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,
                                 [Gtk.TargetEntry.new("text/uri-list", 0, 80)], Gdk.DragAction.COPY)
            widget.connect('drag_data_received', cb_drag_data_received)

        setup_widget(self)
        setup_widget(self.textview)
        self.textview.connect('drag_motion', lambda widget,
                              context, x, y, time: True)

    def update_progress_bar(self, status):
        """Callback to update the progress bar with number or text"""
        if isinstance(status, float):
            self.progressbar.set_fraction(status)
        elif isinstance(status, str):
            self.progressbar.set_show_text(True)
            self.progressbar.set_text(status)
        else:
            raise RuntimeError('unexpected type: ' + str(type(status)))

    def update_item_size(self, option, option_id, bytes_removed):
        """Update size in tree control"""
        model = self.view.get_model()

        text = FileUtilities.bytes_to_human(bytes_removed)
        if bytes_removed == 0:
            text = ""

        treepath = Gtk.TreePath(0)
        try:
            __iter = model.get_iter(treepath)
        except ValueError as e:
            logger.warning(
                'ValueError in get_iter() when updating file size for tree path=%s' % treepath)
            return
        while __iter:
            if model[__iter][2] == option:
                if option_id == -1:
                    model[__iter][3] = text
                else:
                    child = model.iter_children(__iter)
                    while child:
                        if model[child][2] == option_id:
                            model[child][3] = text
                        child = model.iter_next(child)
            __iter = model.iter_next(__iter)

    def update_total_size(self, bytes_removed):
        """Callback to update the total size cleaned"""
        context_id = self.status_bar.get_context_id('size')
        text = FileUtilities.bytes_to_human(bytes_removed)
        if bytes_removed == 0:
            text = ""
        self.status_bar.push(context_id, text)

    def create_headerbar(self):
        """Create the headerbar"""
        hbar = Gtk.HeaderBar()
        hbar.props.show_close_button = True
        hbar.props.title = APP_NAME

        box = Gtk.Box()
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        if os.name == 'nt':
            icon_size = Gtk.IconSize.BUTTON
        else:
            icon_size = Gtk.IconSize.LARGE_TOOLBAR

        # create the preview button
        self.preview_button = Gtk.Button.new_from_icon_name(
            'edit-find', icon_size)
        self.preview_button.set_always_show_image(True)
        self.preview_button.connect(
            'clicked', lambda *dummy: self.preview_or_run_operations(False))
        self.preview_button.set_tooltip_text(
            _("Preview files in the selected operations (without deleting any files)"))
        # TRANSLATORS: This is the preview button on the main window.  It
        # previews changes.
        self.preview_button.set_label(_('Preview'))
        box.add(self.preview_button)

        # create the delete button
        self.run_button = Gtk.Button.new_from_icon_name(
            'edit-clear-all', icon_size)
        self.run_button.set_always_show_image(True)
        # TRANSLATORS: This is the clean button on the main window.
        # It makes permanent changes: usually deleting files, sometimes
        # altering them.
        self.run_button.set_label(_('Clean'))
        self.run_button.set_tooltip_text(
            _("Clean files in the selected operations"))
        self.run_button.connect("clicked", self.run_operations)
        box.add(self.run_button)

        # stop cleaning
        self.stop_button = Gtk.Button.new_from_icon_name(
            'process-stop', icon_size)
        self.stop_button.set_always_show_image(True)
        self.stop_button.set_label(_('Abort'))
        self.stop_button.set_tooltip_text(
            _('Abort the preview or cleaning process'))
        self.stop_button.set_sensitive(False)
        self.stop_button.connect('clicked', self.cb_stop_operations)
        box.add(self.stop_button)

        hbar.pack_start(box)

        # Add hamburger menu on the right.
        # This is not needed for Microsoft Windows because other code places its
        # menu on the left side.
        if os.name == 'nt':
            return hbar
        menu_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        builder = Gtk.Builder()
        builder.add_from_file(bleachbit.app_menu_filename)
        menu_button.set_menu_model(builder.get_object('app-menu'))
        menu_button.add(image)
        hbar.pack_end(menu_button)

        return hbar

    def on_configure_event(self, widget, event):
        (x, y) = self.get_position()
        (width, height) = self.get_size()

        # fixup maximized window position:
        # on Windows if a window is maximized on a secondary monitor it is moved off the screen
        if 'nt' == os.name:
            window = self.get_window()
            if window.get_state() & Gdk.WindowState.MAXIMIZED != 0:
                screen = self.get_screen()
                monitor_num = screen.get_monitor_at_window(window)
                g = screen.get_monitor_geometry(monitor_num)
                if x < g.x or x >= g.x + g.width or y < g.y or y >= g.y + g.height:
                    logger.debug("Maximized window {}+{}: monitor ({}) geometry = {}+{}".format(
                        (x, y), (width, height), monitor_num, (g.x, g.y), (g.width, g.height)))
                    self.move(g.x, g.y)
                    return True

        # save window position and size
        options.set("window_x", x, commit=False)
        options.set("window_y", y, commit=False)
        options.set("window_width", width, commit=False)
        options.set("window_height", height, commit=False)
        return False

    def on_window_state_event(self, widget, event):
        # save window state
        fullscreen = event.new_window_state & Gdk.WindowState.FULLSCREEN != 0
        options.set("window_fullscreen", fullscreen, commit=False)
        maximized = event.new_window_state & Gdk.WindowState.MAXIMIZED != 0
        options.set("window_maximized", maximized, commit=False)
        return False

    def on_delete_event(self, widget, event):
        # commit options to disk
        options.commit()
        return False

    def on_show(self, widget):

        if 'nt' == os.name and Windows.splash_thread.is_alive():
            Windows.splash_thread.join(0)

        # restore window position, size and state
        if not options.get('remember_geometry'):
            return
        if options.has_option("window_x") and options.has_option("window_y") and \
           options.has_option("window_width") and options.has_option("window_height"):
            r = Gdk.Rectangle()
            (r.x, r.y) = (options.get("window_x"), options.get("window_y"))
            (r.width, r.height) = (options.get(
                "window_width"), options.get("window_height"))

            screen = self.get_screen()
            monitor_num = screen.get_monitor_at_point(r.x, r.y)
            g = screen.get_monitor_geometry(monitor_num)

            # only restore position and size if window left corner
            # is within the closest monitor
            if r.x >= g.x and r.x < g.x + g.width and \
               r.y >= g.y and r.y < g.y + g.height:
                logger.debug("closest monitor ({}) geometry = {}+{}, window geometry = {}+{}".format(
                    monitor_num, (g.x, g.y), (g.width, g.height), (r.x, r.y), (r.width, r.height)))
                self.move(r.x, r.y)
                self.resize(r.width, r.height)
        if options.get("window_fullscreen"):
            self.fullscreen()
        elif options.get("window_maximized"):
            self.maximize()

    def set_windows10_theme(self):
        """Toggle the Windows 10 theme"""
        if not 'nt' == os.name:
            return

        if not self._style_provider_regular:
            self._style_provider_regular = Gtk.CssProvider()
            self._style_provider_regular.load_from_path(
                os.path.join(windows10_theme_path, 'gtk.css'))
        if not self._style_provider_dark:
            self._style_provider_dark = Gtk.CssProvider()
            self._style_provider_dark.load_from_path(
                os.path.join(windows10_theme_path, 'gtk-dark.css'))

        screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
        if self._style_provider is not None:
            Gtk.StyleContext.remove_provider_for_screen(
                screen, self._style_provider)
        if options.get("win10_theme"):
            if options.get("dark_mode"):
                self._style_provider = self._style_provider_dark
            else:
                self._style_provider = self._style_provider_regular
            Gtk.StyleContext.add_provider_for_screen(
                screen, self._style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        else:
            self._style_provider = None

    def populate_window(self):
        """Create the main application window"""
        screen = self.get_screen()
        self.set_default_size(min(screen.width(), 800),
                              min(screen.height(), 600))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("configure-event", self.on_configure_event)
        self.connect("window-state-event", self.on_window_state_event)
        self.connect("delete-event", self.on_delete_event)
        self.connect("show", self.on_show)

        if appicon_path and os.path.exists(appicon_path):
            self.set_icon_from_file(appicon_path)

        # add headerbar
        self.headerbar = self.create_headerbar()
        self.set_titlebar(self.headerbar)

        # split main window twice
        hbox = Gtk.Box(homogeneous=False)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False)
        self.add(vbox)
        vbox.add(hbox)

        # add operations to left
        operations = self.create_operations_box()
        hbox.pack_start(operations, False, True, 0)

        # create the right side of the window
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.progressbar = Gtk.ProgressBar()
        right_box.pack_start(self.progressbar, False, True, 0)

        # add output display on right
        self.textbuffer = Gtk.TextBuffer()
        swindow = Gtk.ScrolledWindow()
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_property('expand', True)
        self.textview = Gtk.TextView.new_with_buffer(self.textbuffer)
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        swindow.add(self.textview)
        right_box.add(swindow)
        hbox.add(right_box)

        # add markup tags
        tt = self.textbuffer.get_tag_table()

        style_operation = Gtk.TextTag.new('operation')
        style_operation.set_property('size-points', 14)
        style_operation.set_property('weight', 700)
        style_operation.set_property('pixels-above-lines', 10)
        style_operation.set_property('justification', Gtk.Justification.CENTER)
        tt.add(style_operation)

        style_description = Gtk.TextTag.new('description')
        style_description.set_property(
            'justification', Gtk.Justification.CENTER)
        tt.add(style_description)

        style_option_label = Gtk.TextTag.new('option_label')
        style_option_label.set_property('weight', 700)
        style_option_label.set_property('left-margin', 20)
        tt.add(style_option_label)

        style_operation = Gtk.TextTag.new('error')
        style_operation.set_property('foreground', '#b00000')
        tt.add(style_operation)

        self.status_bar = Gtk.Statusbar()
        vbox.add(self.status_bar)
        # setup drag&drop
        self.setup_drag_n_drop()
        # done
        self.show_all()
        self.progressbar.hide()

    @threaded
    def check_online_updates(self):
        """Check for software updates in background"""
        from bleachbit import Update
        try:
            updates = Update.check_updates(options.get('check_beta'),
                                           options.get('update_winapp2'),
                                           self.append_text,
                                           lambda: GLib.idle_add(self.cb_refresh_operations))
            if updates:
                GLib.idle_add(
                    lambda: Update.update_dialog(self, updates))
        except Exception:
            logger.exception(_("Error when checking for updates: "))
