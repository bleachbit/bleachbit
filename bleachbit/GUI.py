#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
## http://sourceforge.net
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
import sys
import threading
import time
import traceback
import types
import warnings

warnings.simplefilter('error')
import pygtk
pygtk.require('2.0')
import gtk
import gobject
warnings.simplefilter('default')

from Common import _, _p, APP_NAME, APP_VERSION, APP_URL, appicon_path, \
    help_contents_url, license_filename, options_file, options_dir, \
    online_update_notification_enabled, release_notes_url, portable_mode
from Cleaner import backends
from GuiPreferences import PreferencesDialog
from Options import options
import Cleaner
import FileUtilities
import GuiBasic

if 'nt' == os.name:
    import Windows



def open_url(url):
    """Open an HTTP URL"""
    print "debug: on_url('%s')" % (url,)
    try:
        import gnomevfs
        gnomevfs.url_show(url)
        return
    except:
        import webbrowser
        webbrowser.open(url)



def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target = func, args=args)
        thread.start()
    return wrapper



class TreeInfoModel:
    """Model holds information to be displayed in the tree view"""


    def __init__(self):
        self.tree_store = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT)
        if None == self.tree_store:
            raise Exception("cannot create tree store")
        self.row_changed_handler_id = None
        self.refresh_rows()
        self.tree_store.set_sort_func(3, self.sort_func)
        self.tree_store.set_sort_column_id(3, gtk.SORT_ASCENDING)


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
            if not c_value and options.get('auto_hide') \
                and backends[key].auto_hide():
                print "info: automatically hiding cleaner '%s'" % (c_id)
                continue
            parent = self.tree_store.append(None, (c_name, c_value, c_id))
            for (o_id, o_name) in backends[key].get_options():
                o_value = options.get_tree(c_id, o_id)
                self.tree_store.append(parent, (o_name, o_value, o_id))
        self.row_changed_handler_id = self.tree_store.connect("row-changed", \
            self.on_row_changed)


    def sort_func(self, model, iter1, iter2):
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


    def make_view(self, model, parent):
        """Create and return a TreeView object"""
        self.view = gtk.TreeView(model)

        # first column
        self.renderer0 = gtk.CellRendererText()
        self.column0 = gtk.TreeViewColumn(_("Name"), self.renderer0, text=0)
        self.view.append_column(self.column0)
        self.view.set_search_column(0)

        # second column
        self.renderer1 = gtk.CellRendererToggle()
        self.renderer1.set_property('activatable', True)
        self.renderer1.connect('toggled', self.col1_toggled_cb, model, parent)
        self.column1 = gtk.TreeViewColumn(_("Active"), self.renderer1)
        self.column1.add_attribute(self.renderer1, "active", 1)
        self.view.append_column(self.column1)

        # finish
        self.view.expand_all()
        return self.view


    def set_cleaner(self, path, model, parent_window, value = None):
        """Activate or deactive option of cleaner."""
        if None == value:
            # if not value given, toggle current value
            value = not model[path][1]
        assert(type(value) is types.BooleanType)
        assert(type(model) is gtk.TreeStore)
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
            if warning:
                resp = GuiBasic.message_dialog(parent_window, \
                    warning, \
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL)
                if gtk.RESPONSE_OK != resp:
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


class GUI:
    """The main application GUI"""

    ui = \
'''
<ui>
    <menubar name="MenuBar">
        <menu action="File">
            <menuitem action="ShredFiles"/>
            <menuitem action="ShredQuit"/>
            <menuitem action="Quit"/>
        </menu>
        <menu action="Edit">
            <menuitem action="Preferences"/>
        </menu>
        <menu action="Help">
            <menuitem action="HelpContents"/>
            <menuitem action="ReleaseNotes"/>
            <menuitem action="SystemInformation"/>
            <menuitem action="About"/>
        </menu>
    </menubar>
</ui>'''


    def append_text(self, text, tag = None, __iter = None):
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
        gobject.idle_add(lambda : \
        self.textview.scroll_mark_onscreen( \
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
        self.append_text(description + "\n\n\n")
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
        __iter = model.get_iter_root()
        while __iter:
            if model[__iter][1]:
                ret.append(model[__iter][2])
            __iter = model.iter_next(__iter)
        return ret


    def get_operation_options(self, operation):
        """For the given operation ID, return a list of the selected option IDs."""
        ret = []
        model = self.tree_store.get_model()
        __iter = model.get_iter_root()
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
        self.actiongroup.set_sensitive(true)
        self.toolbar.set_sensitive(true)
        self.view.set_sensitive(true)


    def run_operations(self, __widget):
        """Event when the 'delete' toolbar button is clicked."""
        # fixme: should present this dialog after finding operations
        if not GuiBasic.delete_confirmation_dialog(self.window, True):
            return
        self.preview_or_run_operations(True)


    def preview_or_run_operations(self, really_delete, operations = None):
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
            GuiBasic.message_dialog(self.window, \
                _("You must select an operation"),
                gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
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
            gobject.idle_add(worker.next)



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
        if elapsed < 10 or self.window.is_active():
            return
        try:
            import pynotify
        except:
            print "debug: pynotify not available"
        else:
            if pynotify.init(APP_NAME):
                notify = pynotify.Notification('BleachBit', _("Done."), \
                    icon = 'bleachbit')
                notify.show()
                notify.set_timeout(10000)



    def about(self, __event):
        """Create and show the about dialog"""
        gtk.about_dialog_set_url_hook(lambda dialog, link: open_url(link))
        dialog = gtk.AboutDialog()
        dialog.set_comments(_("Program to clean unnecessary files"))
        dialog.set_copyright("Copyright (C) 2010 Andrew Ziem")
        try:
            dialog.set_license(open(license_filename).read())
        except:
            dialog.set_license(_("GNU General Public License version 3 or later.\nSee http://www.gnu.org/licenses/gpl-3.0.txt"))
        dialog.set_name(APP_NAME)
        # TRANSLATORS: Maintain the names of translators here.
        # Launchpad does this automatically for translations
        # typed in Launchpad. This is a special string shown
        # in the 'About' box.
        dialog.set_translator_credits(_("translator-credits"))
        dialog.set_version(APP_VERSION)
        dialog.set_website(APP_URL)
        dialog.set_transient_for(self.window)
        if appicon_path and os.path.exists(appicon_path):
            icon = gtk.gdk.pixbuf_new_from_file(appicon_path)
            dialog.set_logo(icon)
        dialog.run()
        dialog.hide()


    def diagnostic_dialog(self, parent):
        """Show diagnostic information"""
        dialog = gtk.Dialog(_("System information"), parent)
        dialog.resize(600, 400)
        buffer = gtk.TextBuffer()
        import Diagnostic
        txt = Diagnostic.diagnostic_info()
        buffer.set_text(txt)
        textview = gtk.TextView(buffer)
        textview.set_editable(False)
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swindow.add_with_viewport(textview)
        dialog.vbox.pack_start(swindow)
        dialog.add_buttons(gtk.STOCK_COPY, 100, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        dialog.show_all()
        while True:
            rc = dialog.run()
            if 100 == rc:
                clipboard = gtk.clipboard_get()
                clipboard.set_text(txt)
            else:
                break
        dialog.hide()


    def create_operations_box(self):
        """Create and return the operations box (which holds a tree view)"""
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.tree_store = TreeInfoModel()
        display = TreeDisplayModel()
        mdl = self.tree_store.get_model()
        self.view = display.make_view(mdl, self.window)
        self.view.get_selection().connect("changed", self.on_selection_changed)
        scrolled_window.add(self.view)
        return scrolled_window


    def cb_preferences_dialog(self, action):
        """Callback for preferences dialog"""
        pref = PreferencesDialog(self.window, self.cb_refresh_operations)
        pref.run()


    def cb_refresh_operations(self):
        """Callback to refresh the list of cleaners"""
        self.tree_store.refresh_rows()
        self.view.expand_all()


    def cb_shred_file(self, action):
        """Callback for shredding a file"""

        # get list of files
        paths = GuiBasic.browse_files(self.window, \
            _("Choose files to shred"))

        if not paths:
            return

        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        # preview and confirm
        operations = { '_gui' : [ 'files' ] }
        self.preview_or_run_operations(False, operations)

        if GuiBasic.delete_confirmation_dialog(self.window, mention_preview = False):
            # delete
            options.set('shred', True, commit = False)
            self.preview_or_run_operations(True, operations)
            options.restore()
            return

        # clean up temporary cleaner
        del backends['_gui']


    def cb_shred_quit(self, action):
        """Shred settings (for privacy reasons) and quit"""
        try:
            FileUtilities.delete(options_file, shred = True)
            if portable_mode:
                open(options_file, 'w').write('[Portable]\n')
            fn = os.path.join(options_dir, "deepscan.sqlite3")
            if os.path.exists(fn):
                FileUtilities.delete(fn, shred = True)
        except:
            print traceback.print_exc()
            err = str(sys.exc_info()[1])
            self.append_text(err, 'error')
            return

        if not portable_mode:
            try:
                os.rmdir(options_dir)
            except:
                print traceback.print_exc()
                err = str(sys.exc_info()[1])
                self.append_text(err, 'error')
                while gtk.events_pending():
                    gtk.main_iteration()
                time.sleep(3)

        gtk.main_quit()


    def update_progress_bar(self, status):
        """Callback to update the progress bar with number or text"""
        if type(status) is float:
            self.progressbar.set_fraction(status)
        elif (type(status) is str) or (type(status) is unicode):
            self.progressbar.set_text(status)
        else:
            raise RuntimeError('unexpected type: ' + str(type(status)))


    def update_total_size(self, bytes):
        """Callback to update the total size cleaned"""
        context_id = self.status_bar.get_context_id('size')
        text = FileUtilities.bytes_to_human(bytes)
        if 0 == bytes:
            text = ""
        self.status_bar.push(context_id, text)


    def create_menubar(self):
        """Create the menu bar (file, help)"""
        # Create a UIManager instance
        uimanager = gtk.UIManager()

        # Add the accelerator group to the top level window
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup

        # Create actions
        entries = (
                    ('ShredFiles', gtk.STOCK_DELETE, _('_Shred Files'), None, None, self.cb_shred_file),
                    ('ShredQuit', None, _('S_hred Settings and Quit'), None, None, self.cb_shred_quit),
                    ('Quit', gtk.STOCK_QUIT, _('_Quit'), None, None, lambda *dummy: gtk.main_quit()),
                    ('File', None, _('_File')),
                    ('Preferences', gtk.STOCK_PREFERENCES, _("Preferences"), None, None, self.cb_preferences_dialog),
                    ('Edit', None, _("_Edit")),
                    ('HelpContents', gtk.STOCK_HELP, _('Help Contents'), 'F1', None, lambda link: open_url(help_contents_url)),
                    ('ReleaseNotes', gtk.STOCK_INFO, _('_Release Notes'), None, None, lambda link: open_url(release_notes_url)),
                    ('SystemInformation', None, _('_System Information'), None, None, lambda foo: self.diagnostic_dialog(self.window)),
                    ('About', gtk.STOCK_ABOUT, _('_About'), None, None, self.about),
                    ('Help', None, _("_Help")))
        actiongroup.add_actions(entries)
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(self.ui)

        # Create a MenuBar
        menubar = uimanager.get_widget('/MenuBar')
        return menubar


    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = gtk.Toolbar()


        # create the preview button
        preview_icon = gtk.Image()
        preview_icon.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_LARGE_TOOLBAR)
        # TRANSLATORS: This is the preview button on the main window.  It previews changes.
        preview_button = gtk.ToolButton(icon_widget = preview_icon, label = _p('button', "Preview"))
        preview_button.connect("clicked", lambda *dummy: self.preview_or_run_operations(False))
        toolbar.insert(preview_button, -1)
        preview_button.set_tooltip_text(_("Preview files in the selected operations (without deleting any files)"))
        preview_button.set_is_important(True)

        # create the delete button
        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_LARGE_TOOLBAR)
        # TRANSLATORS: This is the delete button on the main window.
        # It makes permanent changes: usually deleting files, sometimes altering them.
        run_button = gtk.ToolButton(icon_widget = icon, label = _p("button", "Delete"))
        run_button.connect("clicked", self.run_operations)
        toolbar.insert(run_button, -1)
        run_button.set_tooltip_text(_("Delete files in the selected operations"))
        run_button.set_is_important(True)

        return toolbar


    def create_window(self):
        """Create the main application window"""

        print 'info: GTK version %s' % '.'.join([str(x) for x in gtk.gtk_version])

        self.window = gtk.Window()
        self.window.connect('destroy', lambda w: gtk.main_quit())

        self.window.resize(800, 600)
        self.window.set_title(APP_NAME)
        if appicon_path and os.path.exists(appicon_path):
            self.window.set_icon_from_file(appicon_path)
        vbox = gtk.VBox()
        self.window.add(vbox)

        # add menubar
        vbox.pack_start(self.create_menubar(), False)

        # add toolbar
        self.toolbar = self.create_toolbar()
        vbox.pack_start(self.toolbar, False)

        # split main window
        hbox = gtk.HBox(homogeneous=False, spacing=10)
        vbox.pack_start(hbox, True)

        # add operations to left
        operations = self.create_operations_box()
        hbox.pack_start(operations, False)

        # create the right side of the window
        right_box = gtk.VBox()
        self.progressbar = gtk.ProgressBar()
        right_box.pack_start(self.progressbar, False)

        # add output display on right
        self.textbuffer = gtk.TextBuffer()
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview = gtk.TextView(self.textbuffer)
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        swindow.add(self.textview)
        right_box.add(swindow)
        hbox.add(right_box)

        # add markup tags
        tt = self.textbuffer.get_tag_table()

        style_operation = gtk.TextTag('operation')
        style_operation.set_property('size-points', 14)
        style_operation.set_property('weight', 700)
        tt.add(style_operation)

        style_option_label = gtk.TextTag('option_label')
        style_option_label.set_property('weight', 700)
        tt.add(style_option_label)

        style_operation = gtk.TextTag('error')
        style_operation.set_property('foreground', '#b00000')
        tt.add(style_operation)

        # add status bar
        self.status_bar = gtk.Statusbar()
        vbox.pack_start(self.status_bar, False)

        # done
        self.window.show_all()
        self.progressbar.hide()
        return

    def enable_online_update(self, url):
        """Create a button to launch browser to initiate software update"""
        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_NETWORK, gtk.ICON_SIZE_LARGE_TOOLBAR)
        update_button = gtk.ToolButton(icon_widget = icon, label = _p('button', 'Update BleachBit'))
        update_button.show_all()
        update_button.connect("clicked", lambda toolbutton, url: open_url(url), url)
        update_button.set_is_important(True)
        self.toolbar.insert(update_button, -1)
        msg = _("BleachBit update is available")
        try:
            import pynotify
        except:
            print "debug: pynotify not available"
            self.append_text(msg)
        else:
            if pynotify.init(APP_NAME):
                notify = pynotify.Notification(msg, _("Click 'Update BleachBit' for more information"))
                # this doesn't align the notification properly
                #n.attach_to_widget(update_button)
                notify.attach_to_widget(self.toolbar)
                notify.show()


    @threaded
    def check_online_updates(self):
        """Check for software updates in background"""
        import Update
        try:
            update = Update.Update()
            if update.is_update_available():
                gobject.idle_add(self.enable_online_update, update.get_update_info_url())
        except:
            self.append_text(_("Error when checking for updates: ") + str(sys.exc_info()[1]), 'error')


    def __init__(self):
        if 'nt' == os.name and Windows.elevate_privileges():
            # privileges escalated in other process
            sys.exit(0)
        import RecognizeCleanerML
        RecognizeCleanerML.RecognizeCleanerML()
        import CleanerML
        CleanerML.load_cleaners()
        self.create_window()
        gobject.threads_init()
        if options.get("first_start") and 'posix' == os.name:
            pref = PreferencesDialog(self.window, self.cb_refresh_operations)
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
                self.append_text(_("Error loading the SQLite module: the antivirus software may be blocking it."), 'error')



if __name__ == '__main__':
    gui = GUI()
    gtk.main()

