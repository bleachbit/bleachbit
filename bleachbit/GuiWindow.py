# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import logging
import os
import sys
import time

import bleachbit
from bleachbit import APP_NAME, Cleaner, FileUtilities, GuiBasic, appicon_path, windows10_theme_path
from bleachbit.Cleaner import backends, register_cleaners
from bleachbit.GUI import logger
from bleachbit.GtkShim import GLib, Gdk, Gio, Gtk, require_gtk
from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.GuiTreeModels import TreeDisplayModel, TreeInfoModel
from bleachbit.GuiUtil import get_font_size_from_name, get_window_info, notify, threaded
from bleachbit.Language import get_text as _
from bleachbit.Options import options
from bleachbit.Wipe import detect_orphaned_wipe_files

if os.name == 'nt':
    from bleachbit import Windows

# Ensure GTK is available for this GUI module
require_gtk()


class GUI(Gtk.ApplicationWindow):
    """The main application GUI"""
    _style_provider = None
    _style_provider_regular = None
    _style_provider_dark = None

    def __init__(self, auto_exit, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        self._show_splash_screen()

        self._auto_exit = auto_exit
        self._infobar_timeout_id = None

        self.set_property('name', APP_NAME)
        self.set_property('role', APP_NAME)
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

        dark_mode = options.get('dark_mode')
        settings = self.get_settings() or Gtk.Settings.get_default()
        if settings:
            settings.set_property(
                'gtk-application-prefer-dark-theme', dark_mode)
        else:
            logger.warning("Could not get GTK settings to apply dark mode")

        if options.is_corrupt():
            logger.error(
                _('Resetting the configuration file because it is corrupt: %s') % bleachbit.options_file)
            bleachbit.Options.init_configuration()

        GLib.idle_add(self.cb_refresh_operations)

        # Close the application when user presses CTRL+Q or CTRL+W.
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        key, mod = Gtk.accelerator_parse("<Control>Q")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, self.on_quit)
        key, mod = Gtk.accelerator_parse("<Control>W")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, self.on_quit)

        # Enable the user to change font size with keyboard or mouse.
        try:
            gtk_font_name = Gtk.Settings.get_default().get_property('gtk-font-name')
        except TypeError as e:
            logger.debug("Error getting font name from GTK settings: %s", e)
        self.font_size = get_font_size_from_name(gtk_font_name) or 12
        self.default_font_size = self.font_size
        self.textview.connect("scroll-event", self.on_scroll_event)
        self.connect("key-press-event", self.on_key_press_event)
        self._font_css_provider = None

    def populate_window(self):
        """Create the main application window"""
        screen = self.get_screen()
        display = screen.get_display()
        monitor = display.get_primary_monitor()
        if monitor is None:
            # See https://github.com/bleachbit/bleachbit/issues/1793
            if display.get_n_monitors() > 0:
                monitor = display.get_monitor(0)
        if monitor is None:
            self.set_default_size(800, 600)
        else:
            geometry = monitor.get_geometry()
            self.set_default_size(min(geometry.width, 800),
                                  min(geometry.height, 600))
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

        # add InfoBar for non-blocking messages
        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect('response', self._on_infobar_response)
        self.infobar_label = Gtk.Label()
        self.infobar_label.set_line_wrap(True)
        self.infobar.get_content_area().add(self.infobar_label)
        vbox.pack_start(self.infobar, False, False, 0)

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
        self.infobar.hide()

    def _get_windows10_theme_css(self):
        """Load the Windows 10 theme CSS files (if not already loaded)"""
        if not 'nt' == os.name:
            return

        if not options.get("win10_theme"):
            return

        # Load regular theme CSS
        dark_mode = options.get('dark_mode')
        if not dark_mode:
            if not self._style_provider_regular:
                self._style_provider_regular = Gtk.CssProvider()
                regular_path = os.path.join(windows10_theme_path, 'gtk.css')
                logger.debug(
                    'Loading Windows 10 regular theme from: %s', regular_path)
                try:
                    self._style_provider_regular.load_from_path(regular_path)
                    logger.debug('Successfully loaded regular theme')
                except Exception as e:
                    logger.error(
                        'Failed to load Windows 10 regular theme: %s', e)
                    self._style_provider_regular = None
            return self._style_provider_regular

        # Load dark theme CSS
        if not self._style_provider_dark:
            self._style_provider_dark = Gtk.CssProvider()
            dark_path = os.path.join(windows10_theme_path, 'gtk-dark.css')
            logger.debug('Loading Windows 10 dark theme from: %s', dark_path)
            try:
                self._style_provider_dark.load_from_path(dark_path)
                logger.debug('Successfully loaded dark theme')
            except Exception as e:
                logger.error('Failed to load Windows 10 dark theme: %s', e)
                self._style_provider_dark = None
        return self._style_provider_dark

    def set_windows10_theme(self):
        """Apply or remove the Windows 10 theme based on current settings"""
        if not 'nt' == os.name:
            return

        # Get the screen - if not available yet (e.g., during __init__), return early
        screen = self.get_screen()
        if screen is None:
            logger.info(
                'Screen not available yet, deferring theme application')
            return

        # Remove the current style provider if it's active
        if self._style_provider is not None:
            Gtk.StyleContext.remove_provider_for_screen(
                screen, self._style_provider)
            self._style_provider = None

        # Apply the theme if the option is enabled
        if options.get("win10_theme"):
            self._style_provider = self._get_windows10_theme_css()

            if self._style_provider is not None:
                Gtk.StyleContext.add_provider_for_screen(
                    screen, self._style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            else:
                logger.warning(
                    'Windows 10 theme style provider is None, cannot apply theme')
        else:
            logger.debug('Windows 10 theme disabled, using default theme')

    def _show_splash_screen(self):
        """Show the splash screen on Windows because startup may be slow"""
        if os.name != 'nt':
            return

        font_conf_file = Windows.get_font_conf_file()
        if not os.path.exists(font_conf_file):
            logger.error('No fonts.conf file {}'.format(font_conf_file))
            return

        has_cache = Windows.has_fontconfig_cache(font_conf_file)
        if not has_cache:
            Windows.splash_thread.start()

    def set_font_size(self, absolute_size=None, relative_size=None):
        """Set the font size of the entire application"""
        assert absolute_size is not None or relative_size is not None
        if absolute_size is None:
            absolute_size = self.font_size + relative_size
        absolute_size = max(5, min(25, absolute_size))
        self.font_size = absolute_size
        css = f"* {{ font-size: {absolute_size}pt; }}"
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())

        # Remove any previous provider to avoid stacking rules.
        screen = self.get_screen()
        if self._font_css_provider is not None:
            Gtk.StyleContext.remove_provider_for_screen(
                screen, self._font_css_provider)

        # Add the new provider globally so it affects all widgets.
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._font_css_provider = provider

    def on_key_press_event(self, _widget, event):
        """Handle key press events"""
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK

        if event.keyval == Gdk.KEY_F11 and not ctrl:
            is_fullscreen = self.get_window().get_state() & Gdk.WindowState.FULLSCREEN
            if is_fullscreen:
                self.unfullscreen()
            else:
                self.fullscreen()
            options.set("window_fullscreen", is_fullscreen, commit=False)
            return True
        if not ctrl:
            return False
        if event.keyval in (Gdk.KEY_plus, Gdk.KEY_KP_Add):
            self.set_font_size(relative_size=1)
            return True
        if event.keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self.set_font_size(relative_size=-1)
            return True
        if event.keyval == Gdk.KEY_0:
            self.set_font_size(absolute_size=self.default_font_size)
            return True

        return False

    def on_scroll_event(self, _widget, event):
        """Handle mouse scroll events

        The first smooth scroll event, whether up or down, has dy=0.
        """
        if not event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            return False

        relative_size = 0
        if event.direction == Gdk.ScrollDirection.UP:
            logger.debug('scroll event ctrl + Gdk.ScrollDirection.UP')
            relative_size = 1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            logger.debug('scroll event ctrl + Gdk.ScrollDirection.DOWN')
            relative_size = -1
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            try:
                finished, dx, dy = event.get_scroll_deltas()
            except TypeError as e:
                logger.warning("Could not unpack scroll deltas: %s", e)
                return False  # event not handled

            if dy < 0:
                relative_size = 1
            elif dy > 0:
                relative_size = -1
            else:
                logger.debug(
                    "Smooth scroll: finished=%s, dx=%s, dy=%s", finished, dx, dy)
        else:
            logger.debug(
                'scroll event ctrl + unknown direction %s', event.direction)

        if relative_size != 0:
            self.set_font_size(relative_size=relative_size)
            return True  # Event handled

        return False

    def on_quit(self, *args):
        """Quit the application, used with CTRL+Q or CTRL+W"""
        if Gtk.main_level() > 0:
            Gtk.main_quit()
        else:
            self.destroy()

    def _on_infobar_response(self, infobar, response_id):
        """Handle InfoBar close button click"""
        timeout_id = getattr(self, '_infobar_timeout_id', None)
        if timeout_id is not None:
            GLib.source_remove(timeout_id)
            self._infobar_timeout_id = None
        self.infobar.hide()

    def _hide_infobar(self):
        """Hide the InfoBar (used for auto-dismiss timeout)"""
        self.infobar.hide()
        self._infobar_timeout_id = None
        return False  # Remove from GLib timeout

    def show_infobar(self, message, message_type=Gtk.MessageType.ERROR):
        """Show a non-blocking InfoBar message that auto-dismisses

        Args:
            message: The message to display
            message_type: Gtk.MessageType (ERROR, WARNING, INFO, etc.)
        """
        # Cancel any existing timeout before creating a new one
        timeout_id = getattr(self, '_infobar_timeout_id', None)
        if timeout_id is not None:
            GLib.source_remove(timeout_id)
        self.infobar_label.set_text(message)
        self.infobar.set_message_type(message_type)
        self.infobar.show_all()
        self._infobar_timeout_id = GLib.timeout_add_seconds(
            15, self._hide_infobar)

    def _confirm_delete(self, mention_preview, shred_settings=False):
        if options.get("delete_confirmation") or not options.get('expert_mode'):
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

        This function has several uses:
        1. Shred files or folders from the application menu.
        2. Shred objects in the clipboard, trigger by application menu.
        3. Shred objects in the clipboard, trigger by pasting.
        4. Shred objects by drag and drop.
        5. Shred application settings and quit.
        6. Integration with the Windows Explorer context menu.

        When shred_settings=True, the caller checks if the user confirmed to delete,
        so return True or False, depending on the user's confirmation.

        Otherwise, return False to remove from idle queue.
        """
        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        operations = {'_gui': ['files']}

        # If no confirmation is requested, skip the preview.
        if options.get("delete_confirmation"):
            self.preview_or_run_operations(False, operations)
            if not self._confirm_delete(False, shred_settings):
                # User dis-confirmed the deletion.
                return False

        # Either confirmation was not required or user approved, so
        # continue with deletion.
        self.preview_or_run_operations(True, operations)
        if shred_settings:
            return True

        if self._auto_exit:
            GLib.idle_add(self.close,
                          priority=GLib.PRIORITY_LOW)

        # Return False to remove from idle queue.
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

    def _filter_operations_for_expert_mode(self, operations, really_delete):
        """Filter out options with warnings when expert mode is disabled.

        When cleaning (really_delete=True) without expert mode, options
        with warnings are removed and a log message is shown for each.
        Preview is always allowed.
        """
        if not really_delete or options.get('expert_mode'):
            return operations
        filtered = {}
        for cleaner_id, option_ids in operations.items():
            if option_ids is None:
                filtered[cleaner_id] = option_ids
                continue
            safe_options = []
            for option_id in option_ids:
                if backends[cleaner_id].get_warning(option_id):
                    cleaner_name = backends[cleaner_id].get_name()
                    option_name = option_id
                    # Find the friendly option_name for option_id
                    for (oid, oname) in backends[cleaner_id].get_options():
                        if oid == option_id:
                            option_name = oname
                            break
                    self.append_text(
                        _("%(cleaner)s - %(option)s cannot be cleaned because expert mode is disabled.") % {
                            'cleaner': cleaner_name, 'option': option_name} + "\n",
                        'error')
                else:
                    safe_options.append(option_id)
            if safe_options:
                filtered[cleaner_id] = safe_options
        return filtered

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
            self.show_infobar(_("You must select an operation"),
                              Gtk.MessageType.ERROR)
            return
        try:
            self.set_sensitive(False)
            self.textbuffer.set_text("")
            self.progressbar.show()
            operations = self._filter_operations_for_expert_mode(
                operations, really_delete)
            if not operations:
                self.set_sensitive(True)
                self.progressbar.hide()
                return
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
        scrollbar_width = scrolled_window.get_vscrollbar().get_preferred_width()[
            1]
        # avoid conflict with scrollbar
        self.view.set_margin_end(scrollbar_width)
        scrolled_window.add(self.view)
        return scrolled_window

    def cb_refresh_operations(self):
        """Callback to refresh the list of cleaners and header bar labels"""
        # In case language changed, update the header bar labels.
        self.update_headerbar_labels()
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

        # Show notice about admin privileges.
        if os.name == 'posix' and os.path.expanduser('~') == '/root':
            self.append_text(
                _('You are running BleachBit with administrative privileges for cleaning shared parts of the system, and references to the user profile folder will clean only the root account.') + '\n')
        if os.name == 'nt' and options.get('shred'):
            from win32com.shell.shell import IsUserAnAdmin
            if not IsUserAnAdmin():
                self.append_text(
                    _('Run BleachBit with administrator privileges to improve the accuracy of overwriting the contents of files.'))
                self.append_text('\n')
        if os.name == 'nt' and Windows.is_ots_elevation():
            self.append_text(
                _('You elevated privileges using a different account to clean shared parts of the system. User-specific paths will refer to the administrator account, so to clean your profile, run BleachBit again as a standard user.') + '\n')

        if 'windowsapps' in sys.executable.lower():
            self.append_text(
                _('There is no official version of BleachBit on the Microsoft Store. Get the genuine version at https://www.bleachbit.org where it is always free of charge.') + '\n', 'error')

        # remove from idle loop (see GObject.idle_add)
        return False

    def cb_run_option(self, widget, really_delete, cleaner_id, option_id):
        """Callback from context menu to delete/preview a single option"""
        operations = {cleaner_id: [option_id]}

        # preview
        if not really_delete:
            self.preview_or_run_operations(False, operations)
            return

        # block cleaning of warning options without expert mode
        if not options.get('expert_mode') and backends[cleaner_id].get_warning(option_id):
            self.show_infobar(
                _("This option requires expert mode. Enable it in Preferences."))
            return

        # delete
        if self._confirm_delete(False):
            self.preview_or_run_operations(True, operations)
            return

    def cb_stop_operations(self, __widget):
        """Callback to stop the preview/cleaning process"""
        self.worker.abort()

    def cb_manage_cookies(self, widget):
        """Callback to launch the cookie manager dialog"""
        from bleachbit.GuiCookie import CookieManagerDialog
        dialog = CookieManagerDialog()
        dialog.show_all()

    def cb_manage_custom_paths(self, widget):
        """Callback to launch the preferences dialog with Custom tab"""
        pref = self.get_preferences_dialog()
        pref.dialog.show_all()
        pref.infobar.hide()
        # Switch to Custom tab (index 1: General=0, Custom=1)
        notebook = pref.dialog.get_content_area().get_children()[1]
        notebook.set_current_page(1)
        pref.dialog.run()
        pref.dialog.destroy()
        if pref.refresh_operations:
            self.cb_refresh_operations()

    def _option_has_cookie_command(self, cleaner_id, option_id):
        """Return True if the given option runs a cookie command."""
        cleaner = backends.get(cleaner_id)
        if not cleaner:
            return False
        actions = getattr(cleaner, 'actions', ())
        for opt_id, action in actions:
            if opt_id == option_id and getattr(action, 'action_key', None) == 'cookie':
                return True
        return False

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

        # Check if this option has a cookie command
        if self._option_has_cookie_command(cleaner_id, option_id):
            menu.append(Gtk.SeparatorMenuItem())
            # TRANSLATORS: this is the context menu
            cookie_item = Gtk.MenuItem(label=_("Manage Cookies"))
            cookie_item.connect('activate', self.cb_manage_cookies)
            menu.append(cookie_item)

        # Check if this is the system.custom option
        if cleaner_id == 'system' and option_id == 'custom':
            menu.append(Gtk.SeparatorMenuItem())
            # TRANSLATORS: this is the context menu
            custom_paths_item = Gtk.MenuItem(label=_("Manage custom paths"))
            custom_paths_item.connect('activate', self.cb_manage_custom_paths)
            menu.append(custom_paths_item)

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
        except ValueError:
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

    def update_headerbar_labels(self):
        """Update the labels and tooltips in the headerbar buttons"""
        # Preview button
        self.preview_button.set_tooltip_text(
            _("Preview files in the selected operations (without deleting any files)"))
        # TRANSLATORS: This is the preview button on the main window.  It
        # previews changes.
        self.preview_button.set_label(_('Preview'))

        # Clean button
        # TRANSLATORS: This is the clean button on the main window.
        # It makes permanent changes: usually deleting files, sometimes
        # altering them.
        self.run_button.set_label(_('Clean'))
        self.run_button.set_tooltip_text(
            _("Clean files in the selected operations"))

        # Stop button
        self.stop_button.set_label(_('Abort'))
        self.stop_button.set_tooltip_text(
            _('Abort the preview or cleaning process'))

    def on_update_button_clicked(self, widget):
        """Callback when the update button on the headerbar is clicked"""
        if not (hasattr(self, '_available_updates') and self._available_updates):
            return

        self.update_button.get_style_context().remove_class('update-available')
        updates = self._available_updates
        if len(updates) == 1:
            ver, url = updates[0]
            GuiBasic.open_url(url, self, False)
            return
        # If multiple updates are available, find out which one the user wants.
        from bleachbit import Update
        Update.update_dialog(self, updates)

    def create_headerbar(self):
        """Create the headerbar"""
        hbar = Gtk.HeaderBar()

        # The update button is on the right side of the headerbar.
        # It is hidden until an update is available.
        self.update_button = Gtk.Button()
        self.update_button.set_visible(False)
        self.update_button.connect('clicked', self.on_update_button_clicked)
        # TRANSLATORS: Button in headerbar to update the application
        self.update_button.set_label(_('Update'))
        self.update_button.set_tooltip_text(
            _('Update BleachBit to the latest version'))

        # Add CSS to animate the update button.
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            @keyframes update-pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            .update-available {
                background: @theme_selected_bg_color;
                color: @theme_selected_fg_color;
                animation: update-pulse 2s ease-in-out;
                animation-delay: 2s;
                animation-iteration-count: 1;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.update_button.get_style_context().add_class('update-available')
        hbar.pack_end(self.update_button)
        self.update_button.set_no_show_all(True)
        self.update_button.hide()
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
        box.add(self.preview_button)

        # create the delete button
        self.run_button = Gtk.Button.new_from_icon_name(
            'edit-clear-all', icon_size)
        self.run_button.set_always_show_image(True)
        self.run_button.connect("clicked", self.run_operations)
        box.add(self.run_button)

        # stop cleaning
        self.stop_button = Gtk.Button.new_from_icon_name(
            'process-stop', icon_size)
        self.stop_button.set_always_show_image(True)
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
        app_menu_path = bleachbit.get_share_path('app-menu.ui')
        if app_menu_path:
            builder.add_from_file(app_menu_path)
            menu_button.set_menu_model(builder.get_object('app-menu'))
            menu_button.add(image)
            hbar.pack_end(menu_button)
        else:
            hbar.pack_end(Gtk.Label('error: app-menu.ui not found'))

        # Update all labels and tooltips
        self.update_headerbar_labels()
        return hbar

    def on_configure_event(self, widget, event):
        (x, y) = self.get_position()
        (width, height) = self.get_size()

        # fixup maximized window position:
        # on Windows if a window is maximized on a secondary monitor it is moved off the screen
        if 'nt' == os.name:
            window = self.get_window()
            if window.get_state() & Gdk.WindowState.MAXIMIZED != 0:
                g = get_window_info(self)
                if x < g.x or x >= g.x + g.width or y < g.y or y >= g.y + g.height:
                    logger.debug("Maximized window {}+{}: {}".format(
                        (x, y), (width, height), str(g)))
                    self.move(g.x, g.y)
                    return True

        # save window position and size
        options.set("window_x", x, commit=False)
        options.set("window_y", y, commit=False)
        options.set("window_width", width, commit=False)
        options.set("window_height", height, commit=False)
        return False

    def on_window_state_event(self, widget, event):
        """Save window state

        GTK version 3.24.34 on Windows 11 behaves strangely:
        * It reports maximized only when application starts.
        * Later, it reports window is fullscreen when neither
          full screen nor maximized.

        Because of this issue, we check the tiling state.
        """
        tiling_states = (Gdk.WindowState.TILED |
                         Gdk.WindowState.TOP_TILED |
                         Gdk.WindowState.RIGHT_TILED |
                         Gdk.WindowState.BOTTOM_TILED |
                         Gdk.WindowState.LEFT_TILED)

        is_tiled = event.new_window_state & tiling_states != 0
        fullscreen = (event.new_window_state &
                      Gdk.WindowState.FULLSCREEN != 0) and not is_tiled
        options.set("window_fullscreen", fullscreen, commit=False)
        maximized = event.new_window_state & Gdk.WindowState.MAXIMIZED != 0
        options.set("window_maximized", maximized, commit=False)
        if 'nt' == os.name:
            logger.debug(
                f'window state = {event.new_window_state}, full screen = {fullscreen}, maximized = {maximized}')
        return False

    def on_delete_event(self, widget, event):
        # commit options to disk
        options.commit()
        return False

    def on_show(self, _widget):
        """Handle the show event.

        The event is triggered when the window is first shown.
        It is not emitted when the window is moved or unminimized.
        """
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

            g = get_window_info(self)

            # only restore position and size if window left corner
            # is within the closest monitor
            if r.x >= g.x and r.x < g.x + g.width and \
               r.y >= g.y and r.y < g.y + g.height:
                logger.debug("closest monitor {}, prior window geometry = {}+{}".format(
                    str(g), (r.x, r.y), (r.width, r.height)))
                self.move(r.x, r.y)
                self.resize(r.width, r.height)
        if options.get("window_fullscreen"):
            self.fullscreen()
            self.append_text(
                _("Press F11 to exit fullscreen mode.") + '\n')
        elif options.get("window_maximized"):
            self.maximize()

        # Apply Windows 10 theme if on Windows and enabled
        if os.name == 'nt':
            self.set_windows10_theme()

    def check_orphaned_wipe_files(self):
        """Check for orphaned wipe files and offer to delete them.

        These files are created by wipe_path() to fill empty disk space."""
        orphaned_files = detect_orphaned_wipe_files()
        if not orphaned_files:
            return

        # TRANSLATORS: This message is shown when orphaned temporary files
        # from an interrupted disk wipe operation are detected.
        msg = _("BleachBit detected leftover files from an interrupted "
                "disk wipe operation. Would you like to preview them with an option to delete them?")

        resp = GuiBasic.message_dialog(self,
                                       msg,
                                       Gtk.MessageType.WARNING,
                                       Gtk.ButtonsType.YES_NO,
                                       _('Confirm'))

        if resp == Gtk.ResponseType.YES:
            self.shred_paths(orphaned_files)

    @threaded
    def check_online_updates(self):
        """Check for software updates in background"""
        try:
            from bleachbit import Update
        except ImportError as e:
            logger.error("Cannot check online for updates: %s", e)
            return
        try:
            updates = Update.check_updates(options.get('check_beta'),
                                           options.get('update_winapp2'),
                                           self.append_text,
                                           lambda: GLib.idle_add(self.cb_refresh_operations))

        except Exception:
            logger.exception(_("Error when checking for updates: "))
        else:
            self._available_updates = updates

            def update_button_state():
                if updates:
                    self.update_button.show()
                    self.set_sensitive(True)
            GLib.idle_add(update_button_state)
