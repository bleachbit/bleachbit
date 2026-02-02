# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import glob
import os
import sys

import bleachbit
from bleachbit import APP_NAME, Cleaner, FileUtilities, GuiBasic, appicon_path, portable_mode
from bleachbit.Cleaner import backends
from bleachbit.GUI import logger
from bleachbit.GtkShim import GLib, Gdk, Gio, Gtk, require_gtk
from bleachbit.GuiWindow import GUI
from bleachbit.Language import get_text as _

# Ensure GTK is available for this GUI module
require_gtk()

if os.name == 'nt':
    from bleachbit import Windows


class Bleachbit(Gtk.Application):
    _window = None
    _shred_paths = None
    _auto_exit = False

    def __init__(self, uac=True, shred_paths=None, auto_exit=False):

        application_id_suffix = self._init_windows_misc(
            auto_exit, shred_paths, uac)
        # Support pytest-xdist parallel workers by making application ID unique
        xdist_worker = os.environ.get('PYTEST_XDIST_WORKER', '')
        if xdist_worker:
            application_id_suffix += xdist_worker
        application_id = '{}{}'.format(
            'org.gnome.Bleachbit', application_id_suffix)
        Gtk.Application.__init__(
            self, application_id=application_id, flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_prgname('org.bleachbit.BleachBit')

        if auto_exit:
            # This is used for automated testing of whether the GUI can start.
            # It is called from assert_execute_console() in windows/setup.py
            self._auto_exit = True

        if shred_paths:
            self._shred_paths = shred_paths

        if os.name == 'nt':
            # clean up nonce files https://github.com/bleachbit/bleachbit/issues/858
            import atexit
            atexit.register(Windows.cleanup_nonce)

    def _init_windows_misc(self, auto_exit, shred_paths, uac):
        application_id_suffix = ''
        is_context_menu_executed = auto_exit and shred_paths
        if not os.name == 'nt':
            return ''
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

        On Windows with GTK 3.18, this code is sufficient for the menu to work.
        """
        from bleachbit.Language import setup_translation
        setup_translation()
        builder = Gtk.Builder()
        # set_translation_domain() seems to have no effect.
        # builder.set_translation_domain('bleachbit')
        builder.add_from_file(bleachbit.app_menu_filename)
        menu = builder.get_object('app-menu')
        self.set_app_menu(menu)

        # set up mappings between <attribute name="action"> in app-menu.ui and methods in this class
        actions = {'shredFiles': self.cb_shred_file,
                   'shredFolders': self.cb_shred_folder,
                   'shredClipboard': self.cb_shred_clipboard,
                   'wipeEmptySpace': self.cb_wipe_empty_space,
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
        """Callback for when URIs are received from clipboard

        With GTK 3.18.9 on Windows, there was no text/uri-list in targets,
        but there is with GTK 3.24.34. However, Windows does not have
        get_uris().
        """
        shred_paths = None
        if 'nt' == os.name and Gdk.atom_intern_static_string('FileNameW') in targets:
            # Windows
            # Use non-GTK+ functions because because GTK+ 2 does not work.
            shred_paths = Windows.get_clipboard_paths()
        elif Gdk.atom_intern_static_string('text/uri-list') in targets:
            # Linux
            shred_uris = clipboard.wait_for_contents(
                Gdk.atom_intern_static_string('text/uri-list')).get_uris()
            shred_paths = FileUtilities.uris_to_paths(shred_uris)
        else:
            logger.warning(_('No paths found in clipboard.'))
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
                      priority=GLib.PRIORITY_LOW)

    def cb_wipe_empty_space(self, action, param):
        """callback to wipe empty space in arbitrary folder"""
        path = GuiBasic.browse_folder(self._window,
                                      _("Choose a folder"),
                                      multiple=False, stock_button=_('_OK'))
        if not path:
            # user cancelled
            return

        backends['_gui'] = Cleaner.create_wipe_empty_space_cleaner(path)

        # execute
        operations = {'_gui': ['empty_space']}
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
        dialog = Gtk.AboutDialog(comments=_("Program to clean unnecessary files"),
                                 copyright=bleachbit.APP_COPYRIGHT,
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
        dialog = Gtk.Dialog(title=_("System information"), transient_for=self._window)
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
            GLib.idle_add(GUI.shred_paths, self._window,
                          self._shred_paths, priority=GLib.PRIORITY_LOW)
            # When we shred paths and auto exit with the Windows Explorer context menu command we close the
            # application in GUI.shred_paths, because if it is closed from here there are problems.
            # Most probably this is something related with how GTK handles idle quit calls.
        elif self._auto_exit:
            GLib.idle_add(self.quit,
                          priority=GLib.PRIORITY_LOW)
            print('Success')
        else:
            # Check for orphaned wipe files from interrupted operations
            GLib.idle_add(self._window.check_orphaned_wipe_files,
                          priority=GLib.PRIORITY_LOW)
