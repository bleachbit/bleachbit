#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://sourceforge.net
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


import os
import sys
import threading
import time
import traceback
import types
import warnings

warnings.simplefilter('error')
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import GdkPixbuf
warnings.simplefilter('default')

from Common import _, _p, APP_NAME, appicon_path, \
    options_file, online_update_notification_enabled
from Cleaner import backends, register_cleaners
from GuiPreferences import PreferencesDialog
from Options import options
import Cleaner
import FileUtilities
import GuiBasic

if 'nt' == os.name:
    import Windows


def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    return wrapper


class TreeInfoModel:

    """Model holds information to be displayed in the tree view"""

    def __init__(self):
        self.tree_store = Gtk.TreeStore(
            GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_PYOBJECT)
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
            c_name = backends[key].get_name()
            c_id = backends[key].get_id()
            c_value = options.get_tree(c_id, None)
            if not c_value and backends[key].auto_hide():
                # hide irrelevant cleaner (e.g., the application is not
                # detected)
                continue
            parent = self.tree_store.append(None, (c_name, c_value, c_id))
            for (o_id, o_name) in backends[key].get_options():
                o_value = options.get_tree(c_id, o_id)
                self.tree_store.append(parent, (o_name, o_value, o_id))
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
            # type is either str or Gtk.TreeIter
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


class GUI(Gtk.ApplicationWindow):

    """The main application GUI"""

    def __init__(self, app, uac=True, shred_paths=None):
        Gtk.Window.__init__(self, title=APP_NAME, application=app)
        if uac and 'nt' == os.name and Windows.elevate_privileges():
            # privileges escalated in other process
            sys.exit(0)

        import RecognizeCleanerML
        RecognizeCleanerML.RecognizeCleanerML()
        register_cleaners()

        self.populate_window()

        if shred_paths:
            self.shred_paths(shred_paths)
            return
        if options.get("first_start") and 'posix' == os.name:
            pref = PreferencesDialog(self)
            pref.run()
            options.set('first_start', False)
        if online_update_notification_enabled and options.get("check_online_updates"):
            self.check_online_updates()
        if 'nt' == os.name:
            # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
            # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
            # http://bleachbit.sourceforge.net/forum/074-fails-errors
            try:
                import sqlite3
            except ImportError, e:
                print e
                print dir(e)
                self.append_text(
                    _("Error loading the SQLite module: the antivirus software may be blocking it."), 'error')

    def shred_paths(self, paths):
        """Shred file or folders"""
        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        # preview and confirm
        operations = {'_gui': ['files']}
        self.preview_or_run_operations(False, operations)

        if GuiBasic.delete_confirmation_dialog(self, mention_preview=False):
            # delete
            self.preview_or_run_operations(True, operations)
            return True
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
        if not GuiBasic.delete_confirmation_dialog(self, True):
            return
        self.preview_or_run_operations(True)

    def preview_or_run_operations(self, really_delete, operations=None):
        """Preview operations or run operations (delete files)"""

        assert(isinstance(really_delete, bool))
        import Worker
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
        except:
            traceback.print_exc()
            err = str(sys.exc_info()[1])
            self.append_text(err + "\n", 'error')
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

        # notification for long-running process
        elapsed = (time.time() - self.start_time)
        print 'debug: elapsed time: %d seconds' % elapsed
        if elapsed < 10 or self.is_active():
            return
        try:
            from gi.repository import Notify
        except:
            print "debug: pynotify not available"
        else:
            if Notify.init(APP_NAME):
                notify = Notify.Notification('BleachBit', _("Done."),
                                               icon='bleachbit')
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

    def update_progress_bar(self, status):
        """Callback to update the progress bar with number or text"""
        if type(status) is float:
            self.progressbar.set_fraction(status)
        elif (type(status) is str) or (type(status) is unicode):
            self.progressbar.set_text(status)
        else:
            raise RuntimeError('unexpected type: ' + str(type(status)))

    def create_headerbar(self):
        """Create the headerbar"""
        hb = Gtk.HeaderBar()
        hb.props.show_close_button = True
        hb.props.title = APP_NAME

        box = Gtk.Box()
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        # create the preview button
        # TRANSLATORS: This is the preview button on the main window.  It
        # previews changes.
        preview_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-find-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        preview_button.add(image)
        preview_button.set_tooltip_text(
            _("Preview files in the selected operations (without deleting any files)"))
        preview_button.connect(
            "clicked", lambda *dummy: self.preview_or_run_operations(False))
        box.add(preview_button)

        # create the delete button
        # TRANSLATORS: This is the clean button on the main window.
        # It makes permanent changes: usually deleting files, sometimes
        # altering them.
        run_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-clear-all-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        run_button.add(image)
        run_button.set_tooltip_text(
            _("Clean files in the selected operations"))
        run_button.connect("clicked", self.run_operations)
        box.add(run_button)

        hb.pack_start(box)

        return hb

    def populate_window(self):
        """Create the main application window"""
        self.resize(800, 600)
        if appicon_path and os.path.exists(appicon_path):
            self.set_icon_from_file(appicon_path)

        # add headerbar
        self.headerbar = self.create_headerbar()
        self.set_titlebar(self.headerbar)

        # split main window
        hbox = Gtk.Box(homogeneous=False)
        self.add(hbox)

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

        # done
        self.show_all()
        self.progressbar.hide()
        return

    @threaded
    def check_online_updates(self):
        """Check for software updates in background"""
        import Update
        try:
            updates = Update.check_updates(options.get('check_beta'),
                                           options.get('update_winapp2'),
                                           self.append_text,
                                           lambda: GLib.idle_add(self.cb_refresh_operations))
            if updates:
                GLib.idle_add(
                    lambda: Update.update_dialog(self, updates))
        except:
            traceback.print_exc()
            self.append_text(
                _("Error when checking for updates: ") + str(sys.exc_info()[1]), 'error')
