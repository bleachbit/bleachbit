#!/usr/bin/env python
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

from __future__ import absolute_import, print_function

import bleachbit

from bleachbit.Cleaner import backends, register_cleaners
from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.Options import options
from bleachbit import _, APP_NAME, appicon_path, portable_mode
from bleachbit import Cleaner, FileUtilities
from bleachbit import GuiBasic

import logging
import os
import sys
import threading
import time
import types

from gi.repository import Gtk, Gdk, GObject, GLib, Gio

if 'nt' == os.name:
    from bleachbit import Windows

logger = logging.getLogger(__name__)


def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    return wrapper


class Bleachbit(Gtk.Application):
    _window = None

    def __init__(self, uac=True, shred_paths=None, exit=False):
        if uac and 'nt' == os.name and Windows.elevate_privileges():
            # privileges escalated in other process
            sys.exit(0)
        Gtk.Application.__init__(self, application_id='org.gnome.Bleachbit', flags=Gio.ApplicationFlags.FLAGS_NONE)
        if not exit:
            from bleachbit import RecognizeCleanerML
            RecognizeCleanerML.RecognizeCleanerML()
            register_cleaners()
        GObject.threads_init()

        if shred_paths:
            self.shred_paths(shred_paths)
            return
        if 'nt' == os.name:
            # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
            # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
            # https://www.bleachbit.org/forum/074-fails-errors
            try:
                import sqlite3
            except ImportError:
                logger.exception(_("Error loading the SQLite module: the antivirus software may be blocking it."))
        if 'posix' == os.name and bleachbit.expanduser('~') == '/root':
            self.append_text(
                _('You are running BleachBit with administrative privileges for cleaning shared parts of the system, and references to the user profile folder will clean only the root account.'))
        if 'nt' == os.name and options.get('shred'):
            from win32com.shell.shell import IsUserAnAdmin
            if not IsUserAnAdmin():
                self.append_text(
                    _('Run BleachBit with administrator privileges to improve the accuracy of overwriting the contents of files.'))
                self.append_text('\n')
        if exit:
            # This is used for automated testing of whether the GUI can start.
            print('Success')
            GObject.idle_add(lambda: self.quit(), priority=GObject.PRIORITY_LOW)

    def build_app_menu(self):
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(bleachbit.bleachbit_exe_path, 'data', 'app-menu.ui'))
        menu = builder.get_object('app-menu')
        self.set_app_menu(menu)

        # set up mappings between <attribute name="action"> in app-menu.ui and methods in this class
        actions = {'shredFiles': self.cb_shred_file,
                   'shredFolders': self.cb_shred_folder,
                   'wipeFreeSpace': self.cb_wipe_free_space,
                   'shredQuit': self.cb_shred_quit,
                   'preferences': self.cb_preferences_dialog,
                   'diagnostics': self.diagnostic_dialog,
                   'about': self.about,
                   'quit': self.quit}

        for actionName, callback in actions.items():
            action = Gio.SimpleAction.new(actionName, None)
            action.connect('activate', callback)
            self.add_action(action)

        # help needs more parameters and needs to be declared separately
        helpAction = Gio.SimpleAction.new('help', None)
        helpAction.connect('activate', GuiBasic.open_url, bleachbit.help_contents_url, self._window)
        self.add_action(helpAction)

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

    def cb_shred_quit(self, action):
        """Shred settings (for privacy reasons) and quit"""
        # build a list of paths to delete
        paths = []
        if 'nt' == os.name and portable_mode:
            # in portable mode on Windows, the options directory includes
            # executables
            paths.append(bleachbit.options_file)
        else:
            paths.append(bleachbit.options_dir)

        # prompt the user to confirm
        if not self.shred_paths(paths):
            logger.debug('user aborted shred')
            # aborted
            return

        # in portable mode, rebuild a minimal bleachbit.ini
        if 'nt' == os.name and portable_mode:
            with open(bleachbit.options_file, 'w') as f:
                f.write('[Portable]\n')

        # Quit the application through the idle loop to allow the worker
        # to delete the files.  Use the lowest priority because the worker
        # uses the standard priority.  Otherwise, this will quit before
        # the files are deleted.
        GLib.idle_add(
            lambda: Gtk.main_quit(), priority=GObject.PRIORITY_LOW)

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
        self.preview_or_run_operations(True, operations)

    def cb_preferences_dialog(self, action, param):
        """Callback for preferences dialog"""
        pref = PreferencesDialog(self._window, self._window.cb_refresh_operations)
        pref.run()

    def about(self, action, param):
        """Create and show the about dialog"""

        dialog = Gtk.AboutDialog(comments='Program to clean unnecessary files',
                                 copyright='Copyright (C) 2008-2016 Andrew Ziem',
                                 name=APP_NAME,
                                 version=bleachbit.APP_VERSION,
                                 website=bleachbit.APP_URL,
                                 transient_for=self._window)
        try:
            with open(bleachbit.license_filename) as f:
                dialog.set_license(f.read())
        except IOError:
            dialog.set_license(
                _("GNU General Public License version 3 or later.\nSee http://www.gnu.org/licenses/gpl-3.0.txt"))
        #dialog.set_name(APP_NAME)
        # TRANSLATORS: Maintain the names of translators here.
        # Launchpad does this automatically for translations
        # typed in Launchpad. This is a special string shown
        # in the 'About' box.
        dialog.set_translator_credits(_("translator-credits"))
        if appicon_path and os.path.exists(appicon_path):
            icon = Gtk.Image.new_from_file(appicon_path)
            dialog.set_logo(icon.get_pixbuf())
        dialog.run()
        dialog.hide()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.build_app_menu()

    def quit(self, action=None, param=None):
        self._window.destroy()

    def diagnostic_dialog(self, action, param):
        """Show diagnostic information"""
        dialog = Gtk.Dialog(_("System information"))
        dialog.set_default_size(600, 400)
        txtbuffer = Gtk.TextBuffer()
        from bleachbit import Diagnostic
        txt = Diagnostic.diagnostic_info()
        txtbuffer.set_text(txt)
        textview = Gtk.TextView.new_with_buffer(txtbuffer)
        textview.set_editable(False)
        swindow = Gtk.ScrolledWindow()
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.add_with_viewport(textview)
        dialog.vbox.pack_start(swindow, True, True, 0)
        dialog.add_buttons(Gtk.STOCK_COPY, 100, Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        dialog.show_all()
        while True:
            rc = dialog.run()
            if 100 == rc:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(txt, -1)
            else:
                break
        dialog.hide()

    def do_activate(self):
        if not self._window:
            self._window = GUI(application=self,title=APP_NAME)
        self._window.present()


class TreeInfoModel:
    """Model holds information to be displayed in the tree view"""

    def __init__(self):
        self.tree_store = Gtk.TreeStore(
            GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_PYOBJECT, GObject.TYPE_STRING)
        if None == self.tree_store:
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
        if 2 == len(path):
            child = self.tree_store[path][2]
        value = self.tree_store[path][1]
        options.set_tree(parent, child, value)

    def refresh_rows(self):
        """Clear rows (cleaners) and add them fresh"""
        if None != self.row_changed_handler_id:
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

    def sort_func(self, model, iter1, iter2, user_data):
        """Sort the tree by the display name"""
        s1 = model[iter1][0].lower()
        s2 = model[iter2][0].lower()
        if s1 == s2:
            return 0
        if s1 > s2:
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
        if hasattr(self.renderer2, 'set_alignment'):
            # requires PyGTK 2.22
            # http://www.pygtk.org/pygtk2reference/class-gtkcellrenderer.html#method-gtkcellrenderer--set-alignment
            self.renderer2.set_alignment(1.0, 0.0)
        # TRANSLATORS: Size is the label for the column that shows how
        # much space an option would clean or did clean
        self.column2 = Gtk.TreeViewColumn(_("Size"), self.renderer2, text=3)
        self.column2.set_alignment(1.0)
        self.view.append_column(self.column2)

        # finish
        self.view.expand_all()
        return self.view

    def set_cleaner(self, path, model, parent_window, value=None):
        """Activate or deactive option of cleaner."""
        if None == value:
            # if not value given, toggle current value
            value = not model[path][1]
        assert(type(value) is types.BooleanType)
        assert(type(model) is Gtk.TreeStore)
        cleaner_id = None
        i = path
        if type(i) is str:
            # type is either str or gtk.TreeIter
            i = model.get_iter(path)
        parent = model.iter_parent(i)
        if None != parent:
            # this is an option (child), not a cleaner (parent)
            cleaner_id = model[parent][2]
            option_id = model[path][2]
        if cleaner_id and value:
            # when toggling an option, present any warnings
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
        self.set_cleaner(path, model, parent_window)
        i = model.get_iter(path)
        # if toggled on, enable the parent
        parent = model.iter_parent(i)
        if None != parent and model[path][1]:
            model[parent][1] = True
        # if all siblings toggled off, disable the parent
        if parent and not model[path][1]:
            sibling = model.iter_nth_child(parent, 0)
            any_true = False
            while sibling:
                if model[sibling][1]:
                    any_true = True
                sibling = model.iter_next(sibling)
            if not any_true:
                model[parent][1] = False
        # if toggled and has children, do the same for each child
        child = model.iter_children(i)
        while child:
            self.set_cleaner(child, model, parent_window, model[path][1])
            child = model.iter_next(child)
        return


class GtkLoggerHandler(logging.Handler):
    def __init__(self, append_text):
        logging.Handler.__init__(self)
        self.append_text = append_text
        self.min_level = logging.WARNING
        if '--debug-log' in sys.argv:
            self.min_level = logging.DEBUG

    def emit(self, record):
        if record.levelno < self.min_level:
            return
        tag = 'error' if record.levelno >= logging.WARNING else None
        msg = record.getMessage()
        if record.exc_text:
            msg = msg + '\n' + record.exc_text
        self.append_text(msg + '\n', tag)


class GUI(Gtk.ApplicationWindow):
    """The main application GUI"""

    def __init__(self, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        from bleachbit import RecognizeCleanerML
        RecognizeCleanerML.RecognizeCleanerML()
        register_cleaners()

        self.populate_window()

        # Redirect logging to the GUI.
        bb_logger = logging.getLogger('bleachbit')
        gtklog = GtkLoggerHandler(self.append_text)
        bb_logger.addHandler(gtklog)
        if 'nt' == os.name and 'windows_exe' == getattr(sys, 'frozen', None):
            # On Microsoft Windows this avoids py2exe redirecting stderr to
            # bleachbit.exe.log.
            # sys.frozen = console_exe means the console is shown
            from bleachbit import logger_sh
            bb_logger.removeHandler(logger_sh)

        if options.get("first_start") and 'posix' == os.name:
            pref = PreferencesDialog(self, self.cb_refresh_operations)
            pref.run()
            options.set('first_start', False)
        if bleachbit.online_update_notification_enabled and options.get("check_online_updates"):
            self.check_online_updates()
        if 'nt' == os.name:
            # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
            # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
            # http://bleachbit.sourceforge.net/forum/074-fails-errors
            try:
                import sqlite3
            except ImportError as e:
                print(e)
                print(dir(e))
                self.append_text(
                    _("Error loading the SQLite module: the antivirus software may be blocking it."), 'error')

    def shred_paths(self, paths):
        """Shred file or folders

        If user confirms and files are deleted, returns True.  If
        user aborts, returns False.
        """
        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        # preview and confirm
        operations = {'_gui': ['files']}
        self.preview_or_run_operations(False, operations)

        if GuiBasic.delete_confirmation_dialog(self, mention_preview=False):
            # delete
            self.preview_or_run_operations(True, operations)
            return True

        # user aborted
        return False

    def append_text(self, text, tag=None, __iter=None):
        """Add some text to the main log"""
        if not __iter:
            __iter = self.textbuffer.get_end_iter()
        if tag:
            self.textbuffer.insert_with_tags_by_name(__iter, text, tag)
        else:
            self.textbuffer.insert(__iter, text)
        # Scroll to end.  If the command is run directly instead of
        # through the idle loop, it may only scroll most of the way
        # as seen on Ubuntu 9.04 with Italian and Spanish.
        GLib.idle_add(lambda:
                      self.textview.scroll_mark_onscreen(
                          self.textbuffer.get_insert()))

    def on_selection_changed(self, selection):
        """When the tree view selection changed"""
        model = self.view.get_model()
        selected_rows = selection.get_selected_rows()
        if 0 == len(selected_rows[1]):
            # happens when searching in the tree view
            return
        paths = selected_rows[1][0]
        row = paths[0]
        name = model[row][0]
        cleaner_id = model[row][2]
        self.progressbar.hide()
        description = backends[cleaner_id].get_description()
        self.textbuffer.set_text("")
        self.append_text(name + "\n", 'operation')
        if not description:
            description = ""
        self.append_text(description + "\n\n\n", 'description')
        for (label, description) in backends[cleaner_id].get_option_descriptions():
            self.append_text(label, 'option_label')
            if description:
                self.append_text(': ', 'option_label')
                self.append_text(description)
            self.append_text("\n\n")

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
                if None == iterc:
                    return None
                while iterc:
                    if model[iterc][1]:
                        # option is enabled
                        ret.append(model[iterc][2])
                    iterc = model.iter_next(iterc)
                return ret
            __iter = model.iter_next(__iter)
        return None

    def set_sensitive(self, true):
        """Disable commands while an operation is running"""
        self.headerbar.set_sensitive(true)
        self.view.set_sensitive(true)

    def run_operations(self, __widget):
        """Event when the 'delete' toolbar button is clicked."""
        # fixme: should present this dialog after finding operations

        # Disable delete confirmation message.
        # if the option is selected under preference.

        if options.get("delete_confirmation"):
            if not GuiBasic.delete_confirmation_dialog(self, True):
                return
        self.preview_or_run_operations(True)

    def preview_or_run_operations(self, really_delete, operations=None):
        """Preview operations or run operations (delete files)"""

        assert(isinstance(really_delete, bool))
        from bleachbit import Worker
        self.start_time = None
        if None == operations:
            operations = {}
            for operation in self.get_selected_operations():
                operations[operation] = self.get_operation_options(operation)
        assert(isinstance(operations, dict))
        if 0 == len(operations):
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
            GLib.idle_add(worker.next)

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
        try:
            import gi
            gi.require_version('Notify', '0.7')
            from gi.repository import Notify
        except:
            logger.debug('Notify not available')
        else:
            if Notify.init(APP_NAME):
                notify = Notify.Notification.new('BleachBit', _("Done."), 'bleachbit')
                notify.show()
                notify.set_timeout(10000)

    def create_operations_box(self):
        """Create and return the operations box (which holds a tree view)"""
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.tree_store = TreeInfoModel()
        display = TreeDisplayModel()
        mdl = self.tree_store.get_model()
        self.view = display.make_view(
            mdl, self, self.context_menu_event)
        self.view.get_selection().connect("changed", self.on_selection_changed)
        scrolled_window.add(self.view)
        return scrolled_window

    def cb_refresh_operations(self):
        """Callback to refresh the list of cleaners"""
        # reload cleaners from disk
        register_cleaners()
        # update tree view
        self.tree_store.refresh_rows()
        # expand tree view
        self.view.expand_all()
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
        if GuiBasic.delete_confirmation_dialog(self, mention_preview=False):
            self.preview_or_run_operations(True, operations)
            return

    def cb_wipe_free_space(self, action):
        """callback to wipe free space in arbitrary folder"""
        path = GuiBasic.browse_folder(self,
                                      _("Choose a folder"),
                                      multiple=False, stock_button=Gtk.STOCK_OK)
        if not path:
            # user cancelled
            return

        backends['_gui'] = Cleaner.create_wipe_cleaner(path)

        # execute
        operations = {'_gui': ['free_disk_space']}
        self.preview_or_run_operations(True, operations)

    def context_menu_event(self, treeview, event):
        """When user right clicks on the tree view"""
        if event.button != 3:
            return False
        pathinfo = treeview.get_path_at_pos(int(event.x), int(event.y))
        if None == pathinfo:
            return False
        path, col, cellx, celly = pathinfo
        treeview.grab_focus()
        treeview.set_cursor(path, col, 0)
        # context menu applies only to children, not parents
        if 2 != len(path):
            return False
        # find the seleted option
        model = treeview.get_model()
        option_id = model[path][2]
        cleaner_id = model[path[0]][2]
        cleaner_name = model[path[0]][0]
        # make a menu
        menu = Gtk.Menu()
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
        menu.attach_to_widget(treeview, menu.destroy)
        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)
        return True

    def setup_drag_n_drop(self):
        def cb_drag_data_received(widget, context, x, y, data, info, time):
            print('drop')
            if info == 80:
                import urlparse
                import urllib
                uri = data.get_data().strip('\r\n\x00')
                assert (type(uri) is str)
                file_urls = uri.split("\n")
                file_paths = []
                for file_url in file_urls:
                    # strip needed to remove "\r"
                    file_url = file_url.strip()
                    parsed_url = urlparse.urlparse(file_url)
                    if parsed_url.scheme == "file":
                        file_path = urllib.url2pathname(parsed_url.path)
                        file_path_unicode = file_path.decode("utf-8")
                        file_paths.append(file_path_unicode)
                self.shred_paths(file_paths)

        self.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,
                           [Gtk.TargetEntry.new("text/uri-list", 0, 80)], Gdk.DragAction.COPY)
        self.connect('drag_data_received', cb_drag_data_received)

    def update_progress_bar(self, status):
        """Callback to update the progress bar with number or text"""
        if type(status) is float:
            self.progressbar.set_fraction(status)
        elif (type(status) is str) or (type(status) is unicode):
            self.progressbar.set_text(status)
        else:
            raise RuntimeError('unexpected type: ' + str(type(status)))

    def update_item_size(self, option, option_id, bytes_removed):
        """Update size in tree control"""
        model = self.view.get_model()

        text = FileUtilities.bytes_to_human(bytes_removed)
        if 0 == bytes_removed:
            text = ""

        __iter = model.get_iter(Gtk.TreePath(0))
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
        if 0 == bytes_removed:
            text = ""
        self.status_bar.push(context_id, text)

    def create_headerbar(self):
        """Create the headerbar"""
        hb = Gtk.HeaderBar()
        hb.props.show_close_button = True
        hb.props.title = APP_NAME

        box = Gtk.Box()
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        # create the preview button
        preview_icon = Gio.ThemedIcon(name='edit-find')


        # TRANSLATORS: This is the preview button on the main window.  It
        # previews changes.
        preview_button = Gtk.Button()
        preview_button.add(Gtk.Image.new_from_gicon(preview_icon, Gtk.IconSize.BUTTON))
        preview_button.connect('clicked', lambda *dummy: self.preview_or_run_operations(False))
        preview_button.set_tooltip_text(
            _("Preview files in the selected operations (without deleting any files)"))
        box.add(preview_button)

        # create the delete button
        run_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-clear-all-symbolic")
        # TRANSLATORS: This is the clean button on the main window.
        # It makes permanent changes: usually deleting files, sometimes
        # altering them.
        run_button.add(Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON))
        run_button.set_tooltip_text(_("Clean files in the selected operations"))
        run_button.connect("clicked", self.run_operations)
        box.add(run_button)

        hb.pack_start(box)
        return hb

    def populate_window(self):
        """Create the main application window"""
        self.resize(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
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
        style_description.set_property('justification', Gtk.Justification.CENTER)
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
        return

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
