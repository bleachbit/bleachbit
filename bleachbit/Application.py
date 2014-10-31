import os

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from GUI import GUI
import GuiBasic
from GuiPreferences import PreferencesDialog
import Cleaner
from Cleaner import backends
from Common import _, APP_NAME, APP_VERSION, APP_URL, appicon_path, \
    help_contents_url, portable_mode, options_dir

class Bleachbit(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id='org.gnome.Bleachbit', flags=Gio.ApplicationFlags.FLAGS_NONE)

        self._window = None
    
    def build_app_menu(self):
        builder = Gtk.Builder()

        builder.add_from_file('data/app-menu.ui')

        menu = builder.get_object('app-menu')
        self.set_app_menu(menu)

        shredFilesAction = Gio.SimpleAction.new('shredFiles', None)
        shredFilesAction.connect('activate', self.cb_shred_file)
        self.add_action(shredFilesAction)

        shredFoldersAction = Gio.SimpleAction.new('shredFolders', None)
        shredFoldersAction.connect('activate', self.cb_shred_folder)
        self.add_action(shredFoldersAction)

        wipeFreeSpaceAction = Gio.SimpleAction.new('wipeFreeSpace', None)
        wipeFreeSpaceAction.connect('activate', self.cb_wipe_free_space)
        self.add_action(wipeFreeSpaceAction)

        shredQuitAction = Gio.SimpleAction.new('shredQuit', None)
        shredQuitAction.connect('activate', self.cb_shred_quit)
        self.add_action(shredQuitAction)

        preferencesAction = Gio.SimpleAction.new('preferences', None)
        preferencesAction.connect('activate', self.cb_preferences_dialog)
        self.add_action(preferencesAction)

        aboutAction = Gio.SimpleAction.new('about', None)
        aboutAction.connect('activate', self.about)
        self.add_action(aboutAction)

        helpAction = Gio.SimpleAction.new('help', None)
        helpAction.connect('activate', GuiBasic.open_url, help_contents_url, self._window)
        self.add_action(helpAction)

        quitAction = Gio.SimpleAction.new('quit', None)
        quitAction.connect('activate', self.quit)
        self.add_action(quitAction)

    def cb_shred_file(self, action, param):
        """Callback for shredding a file"""

        # get list of files
        paths = GuiBasic.browse_files(self._window,
                                          _("Choose files to shred"))

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

    def cb_shred_quit(self, action, param):
        """Shred settings (for privacy reasons) and quit"""
        paths = []
        if portable_mode:
            # in portable mode on Windows, the options directory includes
            # executables
            paths.append(options_file)
        else:
            paths.append(options_dir)

        if not GUI.shred_paths(self._window, paths):
            # aborted
            return

        if portable_mode:
            open(options_file, 'w').write('[Portable]\n')

        self.quit()

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
        pref = PreferencesDialog(self._window)
        pref.run()

    def about(self, action, param):
        """Create and show the about dialog"""
        builder = Gtk.Builder()
        builder.add_from_file('data/AboutDialog.ui')
        dialog = builder.get_object('about_dialog')
        dialog.set_name(APP_NAME)
        dialog.set_version(APP_VERSION)
        dialog.set_website(APP_URL)
        dialog.set_transient_for(self._window)
        if appicon_path and os.path.exists(appicon_path):
            icon = GdkPixbuf.Pixbuf.new_from_file(appicon_path)
            dialog.set_logo(icon)
        dialog.show()

    def about_response(self, dialog, response):
        dialog.destroy()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.build_app_menu()

    def quit(self, action=None, param=None):
        self._window.destroy()

    def do_activate(self):
        if not self._window:
            self._window = GUI(self)

        self._window.present()