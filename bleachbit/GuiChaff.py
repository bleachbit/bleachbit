# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
GUI for making chaff
"""

import logging
import os
import threading

from bleachbit.Language import get_text as _
from bleachbit.GtkShim import Gtk, GLib


logger = logging.getLogger(__name__)


def make_files_thread(file_count, inspiration, output_folder, delete_when_finished, on_progress):
    if inspiration == 0:
        from bleachbit.Chaff import generate_2600
        generated_file_names = generate_2600(
            file_count, output_folder, on_progress=on_progress)
    elif inspiration == 1:
        from bleachbit.Chaff import generate_emails
        generated_file_names = generate_emails(
            file_count, output_folder, on_progress=on_progress)
    else:
        raise ValueError(f'Invalid inspiration {inspiration}')
    if delete_when_finished:
        on_progress(0, msg=_('Deleting files'))
        for i in range(0, file_count):
            os.unlink(generated_file_names[i])
            on_progress(1.0 * (i + 1) / file_count)
    on_progress(1.0, is_done=True)


class ChaffDialog(Gtk.Dialog):

    """Present the dialog to make chaff"""

    def __init__(self, parent):
        self._make_dialog(parent)

    def _make_dialog(self, parent):
        """Make the main dialog"""
# TRANSLATORS: BleachBit creates digital chaff like that is like the
# physical chaff airplanes use to protect themselves from radar-guided
# missiles. For more explanation, see the online documentation.
        Gtk.Dialog.__init__(self, title=_("Make chaff"), transient_for=parent)
        Gtk.Dialog.set_modal(self, True)
        self.set_border_width(10)
        self.set_default_size(400, -1)
        box = self.get_content_area()
        box.set_spacing(10)

        # Add InfoBar for non-blocking messages
        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect('response', self._on_infobar_response)
        self.infobar_label = Gtk.Label()
        self.infobar_label.set_line_wrap(True)
        self.infobar.get_content_area().add(self.infobar_label)
        box.pack_start(self.infobar, False, False, 0)
        self._infobar_timeout_id = None

        # TRANSLATORS: Label at the top of the chaff dialog
        dialog_label = _("Make randomly-generated messages "
                         "inspired by documents.")
        label = Gtk.Label(label=dialog_label)
        label.set_line_wrap(True)
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)
        box.pack_start(grid, False, False, 0)

        # TRANSLATORS: Label for the inspiration combo box.
        # 'Inspiration' is a choice of documents from which random text will be generated.
        inspiration_label = Gtk.Label(label=_("Inspiration"))
        inspiration_label.set_xalign(0)
        grid.attach(inspiration_label, 0, 0, 1, 1)
        self.inspiration_combo = Gtk.ComboBoxText()
        self.inspiration_combo.set_hexpand(True)
        self.inspiration_combo_options = (
            _('2600 Magazine'), _("Hillary Clinton's emails"))
        for combo_option in self.inspiration_combo_options:
            self.inspiration_combo.append_text(combo_option)
        self.inspiration_combo.set_active(0)  # Set default
        grid.attach(self.inspiration_combo, 1, 0, 1, 1)

        file_count_label = Gtk.Label(label=_("Number of files"))
        file_count_label.set_xalign(0)
        grid.attach(file_count_label, 0, 1, 1, 1)
        adjustment = Gtk.Adjustment(
            value=100, lower=1, upper=99999, step_increment=1, page_increment=1000, page_size=0)
        self.file_count = Gtk.SpinButton(adjustment=adjustment)
        self.file_count.set_hexpand(True)
        grid.attach(self.file_count, 1, 1, 1, 1)

        folder_label = Gtk.Label(label=_("Select destination folder"))
        folder_label.set_xalign(0)
        grid.attach(folder_label, 0, 2, 1, 1)
        # The file chooser button displays a stock GTK icon. When some parts of GTK are not
        # set up correctly on Windows, then the application may crash here with the error
        # message "No GSettings schemas".
        # https://github.com/bleachbit/bleachbit/issues/1780
        self.choose_folder_button = Gtk.FileChooserButton()
        self.choose_folder_button.set_action(
            Gtk.FileChooserAction.SELECT_FOLDER)
        import tempfile
        self.choose_folder_button.set_filename(tempfile.gettempdir())
        self.choose_folder_button.set_hexpand(True)
        grid.attach(self.choose_folder_button, 1, 2, 1, 1)

        finished_label = Gtk.Label(label=_("When finished"))
        finished_label.set_xalign(0)
        grid.attach(finished_label, 0, 3, 1, 1)
        self.when_finished_combo = Gtk.ComboBoxText()
        self.when_finished_combo.set_hexpand(True)
        self.combo_options = (
            _('Delete without shredding'), _('Do not delete'))
        for combo_option in self.combo_options:
            self.when_finished_combo.append_text(combo_option)
        self.when_finished_combo.set_active(0)  # Set default
        grid.attach(self.when_finished_combo, 1, 3, 1, 1)

        # Loading indicator for download (hidden by default)
        self._download_spinner_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._download_spinner_box.set_halign(Gtk.Align.CENTER)
        self._download_spinner = Gtk.Spinner()
        self._download_spinner.set_size_request(24, 24)
        self._download_spinner_box.pack_start(
            self._download_spinner, False, False, 0)
        # TRANSLATORS: This is a label in a dialog shown when the user
        # clicks the button to download models for chaff generation.
        self._download_label = Gtk.Label(
            label=_("Downloading inspiration content\u2026"))
        self._download_spinner_box.pack_start(
            self._download_label, False, False, 0)
        box.pack_start(self._download_spinner_box, False, False, 0)
        self._download_spinner_box.set_no_show_all(True)
        self._download_spinner_box.hide()

        self.progressbar = Gtk.ProgressBar()
        box.pack_start(self.progressbar, False, False, 0)
        self.progressbar.hide()

        # TRANSLATORS: Button label in a dialog window to start making
        # chaff files.
        self.make_button = Gtk.Button(label=_("Make files"))
        self.make_button.get_style_context().add_class('suggested-action')
        self.make_button.connect('clicked', self.on_make_files)
        box.pack_start(self.make_button, False, False, 0)

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
        """Show a non-blocking InfoBar message that auto-dismisses"""
        if self._infobar_timeout_id:
            GLib.source_remove(self._infobar_timeout_id)
            self._infobar_timeout_id = None
        self.infobar_label.set_text(message)
        self.infobar.set_message_type(message_type)
        self.infobar.show_all()
        self._infobar_timeout_id = GLib.timeout_add_seconds(
            15, self._hide_infobar)

    def download_models_gui(self, on_complete):
        """Download models in a background thread.

        Shows a spinner in the main dialog during download.
        Calls on_complete(success) when done, where success is boolean.
        """

        self._download_success = None

        def on_download_error(msg, msg2):
            # Use idle_add to show error from main thread
            GLib.idle_add(lambda: self.show_infobar(
                f"{msg}: {msg2}", Gtk.MessageType.ERROR))

        def download_models_thread(on_error):
            """Download models in a background thread."""
            import bleachbit.Chaff
            return bleachbit.Chaff.download_models(on_error=on_error)

        def _finish_download(success):
            """Called on main thread when download completes."""
            self._download_spinner.stop()
            self._download_spinner_box.hide()
            self._download_spinner_box.set_no_show_all(True)
            self.make_button.set_sensitive(True)
            on_complete(success)
            return False

        def on_thread_complete(success):
            """Callback when download thread completes."""
            GLib.idle_add(_finish_download, success)

        # Show loading state
        self._download_spinner.start()
        self._download_spinner_box.set_no_show_all(False)
        self._download_spinner_box.show_all()
        self.make_button.set_sensitive(False)

        # Start download in background thread
        def _worker():
            success = download_models_thread(on_download_error)
            on_thread_complete(success)

        thread = threading.Thread(target=_worker)
        thread.start()

    def on_make_files(self, widget):
        """Callback for make files button"""
        file_count = self.file_count.get_value_as_int()
        output_dir = self.choose_folder_button.get_filename()
        delete_when_finished = self.when_finished_combo.get_active() == 0
        inspiration = self.inspiration_combo.get_active()
        if not output_dir:
            self.show_infobar(_("Select destination folder"),
                              Gtk.MessageType.ERROR)
            return

        from bleachbit.Chaff import have_models
        if not have_models():
            # Download models first, then proceed to file generation
            def on_download_complete(success):
                if success:
                    self._start_file_generation(
                        file_count, inspiration, output_dir, delete_when_finished)
                else:
                    self.show_infobar(_("Download failed"),
                                      Gtk.MessageType.ERROR)
            self.download_models_gui(on_download_complete)
        else:
            self._start_file_generation(
                file_count, inspiration, output_dir, delete_when_finished)

    def _start_file_generation(self, file_count, inspiration, output_dir, delete_when_finished):
        """Start generating files after download is complete."""
        def _on_progress(fraction, msg, is_done):
            """Update progress bar from GLib main loop"""
            if msg:
                self.progressbar.set_text(msg)
            self.progressbar.set_fraction(fraction)
            if is_done:
                self.progressbar.hide()
                self.make_button.set_sensitive(True)
                # TRANSLATORS: Notification shown in an infobar when chaff file generation
                # is complete.
                self.show_infobar(_("Chaff generation complete"),
                                  Gtk.MessageType.INFO)

        def on_progress(fraction, msg=None, is_done=False):
            """Callback for progress bar"""
            # Use idle_add() because threads cannot make GDK calls.
            GLib.idle_add(_on_progress, fraction, msg, is_done)

        msg = _('Generating files')
        logger.info(msg)
        self.progressbar.show()
        self.progressbar.set_text(msg)
        self.progressbar.set_show_text(True)
        self.progressbar.set_fraction(0.0)
        self.make_button.set_sensitive(False)
        import threading
        args = (file_count, inspiration, output_dir,
                delete_when_finished, on_progress)
        self.thread = threading.Thread(target=make_files_thread, args=args)
        self.thread.start()

    def run(self):
        """Run the dialog"""
        self.show_all()
        self.infobar.hide()
