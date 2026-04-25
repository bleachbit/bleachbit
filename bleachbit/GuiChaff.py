# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
GUI for making chaff
"""

import functools
import logging
import os
import shutil
import tempfile
import threading


from bleachbit.Chaff import generate_emails, generate_2600
from bleachbit.Constant import ABORT_BUTTON_LABEL
from bleachbit.GtkShim import Gtk, GLib
from bleachbit.Language import get_text as _


logger = logging.getLogger(__name__)


STOP_MODE_FILE_COUNT = 0
STOP_MODE_TOTAL_SIZE = 1
STOP_MODE_FREE_SPACE = 2

MAX_FILE_COUNT = 999999
MAX_MB_COUNT = 999999
MAX_FREE_SPACE_PCT = 99

STOP_MODE_LABELS = {
    # TRANSLATORS: Option in combo box to choose to stop after a number
    # of files have been generated.
    STOP_MODE_FILE_COUNT: _("Number of files"),
    # TRANSLATORS: Option in a combo box for choosing the stop condition
    # when generating chaff (dummy) files. This option means "stop after
    # the total size of generated files reaches a threshold in megabytes."
    # "MB" is the megabyte unit abbreviation. Localize it if your language
    # has an official abbreviation (e.g., "Mo" in French); otherwise keep
    # "MB".
    STOP_MODE_TOTAL_SIZE: _("Size (MB)"),
    # TRANSLATORS: Option in combo box to choose to stop when free space
    # reaches a certain percentage.
    # The percentage symbol (%) is a literal character, not a format
    # placeholder.
    STOP_MODE_FREE_SPACE: _("Free space (%)"),
}


# TRANSLATORS: Used for (1) label for folder chooser button and
# (2) error message shown in the infobar when the folder has not
# been set. 'Select' is a verb.
SELECT_DEST_FOLDER_MSG = _("Select destination folder")


def _make_should_stop(stop_mode, stop_value, output_folder, abort_event):
    """Create a should_stop callback based on the stop mode.

    The returned callable accepts generated_file_names (list of paths)
    and cumulative_size (total bytes written so far).

    Returns (should_stop, file_count).
    """
    if stop_mode == STOP_MODE_FILE_COUNT:
        def should_stop(generated_file_names, cumulative_size=0):  # pylint: disable=unused-argument
            return abort_event.is_set()

        return should_stop, stop_value

    if stop_mode == STOP_MODE_TOTAL_SIZE:
        target_bytes = stop_value * 1024 * 1024  # MB to bytes

        def should_stop(generated_file_names, cumulative_size=0):  # pylint: disable=unused-argument
            if abort_event.is_set():
                return True
            return cumulative_size >= target_bytes

        return should_stop, MAX_FILE_COUNT

    if stop_mode == STOP_MODE_FREE_SPACE:
        target_free_pct = stop_value

        def should_stop(generated_file_names, cumulative_size=0):  # pylint: disable=unused-argument
            if abort_event.is_set():
                return True
            try:
                usage = shutil.disk_usage(output_folder)
            except FileNotFoundError:
                return False
            free_pct = 100.0 * usage.free / usage.total
            return free_pct <= target_free_pct

        return should_stop, MAX_FILE_COUNT

    raise ValueError(f'Invalid stop_mode {stop_mode}')


def _make_progress_cb(stop_mode, stop_value, output_folder, on_progress):
    """Create a progress callback appropriate for the stop mode.

    For file count mode, the fraction from Chaff is already correct.
    For size/free-space modes, we use cumulative_size passed from Chaff
    or compute from disk usage.
    """
    if stop_mode == STOP_MODE_FILE_COUNT:
        def progress_cb(fraction, generated_file_names=None, cumulative_size=0):  # pylint: disable=unused-argument
            on_progress(fraction)

        return progress_cb

    if stop_mode == STOP_MODE_TOTAL_SIZE:
        target_bytes = stop_value * 1024 * 1024

        def progress_cb(fraction, generated_file_names=None, cumulative_size=0):  # pylint: disable=unused-argument
            if cumulative_size > 0:
                on_progress(min(1.0, cumulative_size / target_bytes))
            else:
                on_progress(fraction)

        return progress_cb

    if stop_mode == STOP_MODE_FREE_SPACE:
        target_free_pct = stop_value
        initial_free_pct = [None]  # Use list to allow mutation in nested function

        def progress_cb(_fraction, generated_file_names=None, cumulative_size=0):  # pylint: disable=unused-argument
            try:
                usage = shutil.disk_usage(output_folder)
            except FileNotFoundError:
                on_progress(0.0)
                return
            current_free_pct = 100.0 * usage.free / usage.total
            if initial_free_pct[0] is None:
                initial_free_pct[0] = current_free_pct
            if initial_free_pct[0] > target_free_pct:
                frac = (initial_free_pct[0] - current_free_pct) / \
                    (initial_free_pct[0] - target_free_pct)
                frac = min(1.0, max(0.0, frac))
            else:
                frac = 1.0
            on_progress(frac)

        return progress_cb

    raise ValueError(f'Invalid stop_mode {stop_mode}')


def make_files_thread(stop_mode, stop_value, inspiration, output_folder,
                      delete_when_finished, on_progress, abort_event):
    """Make files in a separate thread"""
    should_stop, file_count = _make_should_stop(
        stop_mode, stop_value, output_folder, abort_event)
    progress_cb = _make_progress_cb(
        stop_mode, stop_value, output_folder, on_progress)

    try:
        if inspiration == 0:
            generated_file_names = generate_2600(
                file_count, output_folder, on_progress=progress_cb,
                should_stop=should_stop)
        elif inspiration == 1:
            generated_file_names = generate_emails(
                file_count, output_folder, on_progress=progress_cb,
                should_stop=should_stop)
        else:
            raise ValueError(f'Invalid inspiration {inspiration}')
    except Exception as exc:
        logger.exception('Error generating chaff')
        # TRANSLATORS: Error message shown when chaff file generation fails.
        # The placeholder is for the technical error details.
        error_msg = _("Error generating chaff: {error}").format(error=str(exc))
        on_progress(1.0, is_done=True, error=error_msg)
        return
    try:
        if delete_when_finished and not abort_event.is_set():
            # TRANSLATORS: Progress message shown while deleting chaff files.
            # 'Deleting files' is a present participle.
            # To indicate an ongoing operation, include the ellipsis as literal
            # Unicode (…) or as Unicode escape (\u2026).
            on_progress(0, msg=_('Deleting files\u2026'))
            count = len(generated_file_names)
            for i, fn in enumerate(generated_file_names):
                if abort_event.is_set():
                    break
                os.unlink(fn)
                on_progress(1.0 * (i + 1) / count)
    except Exception as exc:
        logger.exception('Error deleting chaff files')
        # TRANSLATORS: Error message shown when deleting chaff files fails.
        # The placeholder is for the technical error details.
        error_msg = _("Error deleting chaff files: {error}").format(error=str(exc))
        on_progress(1.0, is_done=True, error=error_msg)
        return
    on_progress(1.0, is_done=True)


class ChaffDialog(Gtk.Dialog):

    """Present the dialog to make chaff"""

    _infobar_timeout_id = None
    _download_success = None
    _abort_event = None
    thread = None

    def __init__(self, parent):
        self._make_dialog(parent)

    def _make_dialog(self, parent):
        """Make the main dialog"""
        # TRANSLATORS: Title for dialog window.
        # Digital chaff is like physical chaff that airplanes use to protect themselves
        # from radar-guided missiles. For more explanation, see the online documentation.
        Gtk.Dialog.__init__(self, title=_("Make chaff"), transient_for=parent)
        Gtk.Dialog.set_modal(self, True)
        self.set_border_width(10)
        self.set_default_size(400, -1)
        self.connect('delete-event', self._on_delete_event)
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

        # TRANSLATORS: Label for the combo box that selects when to stop
        # generating chaff files.
        stop_after_label = Gtk.Label(label=_("Stop after"))
        stop_after_label.set_xalign(0)
        grid.attach(stop_after_label, 0, 1, 1, 1)
        self.stop_mode_combo = Gtk.ComboBoxText()
        self.stop_mode_combo.set_hexpand(True)
        for mode in (STOP_MODE_FILE_COUNT, STOP_MODE_TOTAL_SIZE, STOP_MODE_FREE_SPACE):
            self.stop_mode_combo.append_text(STOP_MODE_LABELS[mode])
        self.stop_mode_combo.set_active(STOP_MODE_FILE_COUNT)
        self.stop_mode_combo.connect('changed', self._on_stop_mode_changed)
        grid.attach(self.stop_mode_combo, 1, 1, 1, 1)

        # TRANSLATORS: Label for the spin button that selects the stop value.
        self.stop_value_label = Gtk.Label(
            label=STOP_MODE_LABELS[self.stop_mode_combo.get_active()])
        self.stop_value_label.set_xalign(0)
        grid.attach(self.stop_value_label, 0, 2, 1, 1)
        self._stop_value_adjustments = {
            STOP_MODE_FILE_COUNT: Gtk.Adjustment(
                value=100, lower=1, upper=MAX_FILE_COUNT,
                step_increment=1, page_increment=1000, page_size=0),
            STOP_MODE_TOTAL_SIZE: Gtk.Adjustment(
                value=100, lower=1, upper=MAX_MB_COUNT,
                step_increment=100, page_increment=1000, page_size=0),
            STOP_MODE_FREE_SPACE: Gtk.Adjustment(
                value=1, lower=1, upper=MAX_FREE_SPACE_PCT,
                step_increment=1, page_increment=10, page_size=0),
        }
        self.stop_value_spin = Gtk.SpinButton(
            adjustment=self._stop_value_adjustments[STOP_MODE_FILE_COUNT])
        self.stop_value_spin.set_hexpand(True)
        grid.attach(self.stop_value_spin, 1, 2, 1, 1)

        folder_label = Gtk.Label(label=SELECT_DEST_FOLDER_MSG)
        folder_label.set_xalign(0)
        grid.attach(folder_label, 0, 3, 1, 1)
        # The file chooser button displays a stock GTK icon. When some parts of GTK are not
        # set up correctly on Windows, then the application may crash here with the error
        # message "No GSettings schemas".
        # https://github.com/bleachbit/bleachbit/issues/1780
        self.choose_folder_button = Gtk.FileChooserButton()
        self.choose_folder_button.set_action(
            Gtk.FileChooserAction.SELECT_FOLDER)
        self.choose_folder_button.set_filename(tempfile.gettempdir())
        self.choose_folder_button.set_hexpand(True)
        grid.attach(self.choose_folder_button, 1, 3, 1, 1)

        # TRANSLATORS: Label for the combo box that selects what to do
        # when chaff generation is finished.
        finished_label = Gtk.Label(label=_("When finished"))
        finished_label.set_xalign(0)
        grid.attach(finished_label, 0, 4, 1, 1)
        self.when_finished_combo = Gtk.ComboBoxText()
        self.when_finished_combo.set_hexpand(True)
        self.combo_options = (
            # TRANSLATORS: Option in combo box to delete generated chaff
            # files without shredding them.
            _('Delete without shredding'),
            # TRANSLATORS: Option in combo box to keep generated chaff files.
            _('Do not delete'))
        for combo_option in self.combo_options:
            self.when_finished_combo.append_text(combo_option)
        self.when_finished_combo.set_active(0)  # Set default
        grid.attach(self.when_finished_combo, 1, 4, 1, 1)

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
        # 'Downloading' is a present participle.
        # 'Inspiration content' refers to source documents from which
        # random text will be generated.
        # To indicate an ongoing operation, include the ellipsis as literal
        # Unicode (…) or as Unicode escape (\u2026).
        download_label_str = _("Downloading inspiration content\u2026")
        self._download_label = Gtk.Label(label=download_label_str)
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

        self.abort_button = Gtk.Button(label=ABORT_BUTTON_LABEL)
        self.abort_button.get_style_context().add_class('destructive-action')
        self.abort_button.connect('clicked', self._on_abort)
        box.pack_start(self.abort_button, False, False, 0)
        self.abort_button.set_sensitive(False)

        self._abort_event = None

    def _on_infobar_response(self, _infobar, _response_id):
        """Handle InfoBar close button click"""
        if self._infobar_timeout_id:
            GLib.source_remove(self._infobar_timeout_id)
            self._infobar_timeout_id = None
        self.infobar.hide()

    def _on_stop_mode_changed(self, combo):
        """Update the value spin button when the stop mode changes"""
        mode = combo.get_active()
        self.stop_value_label.set_text(STOP_MODE_LABELS[mode])
        self.stop_value_spin.set_adjustment(
            self._stop_value_adjustments[mode])

    def _on_abort(self, _widget):
        """Callback for abort button"""
        if self._abort_event:
            self._abort_event.set()

    def _on_delete_event(self, _widget, _event):
        """Handle dialog close (e.g., X button) by aborting the thread."""
        if self._abort_event:
            self._abort_event.set()
        return False  # Allow the dialog to close

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
            message = f'{msg}: {msg2}'
            GLib.idle_add(
                functools.partial(self.show_infobar, message, Gtk.MessageType.ERROR))

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

    def on_make_files(self, _widget):
        """Callback for make files button"""
        self.infobar.hide()
        stop_mode = self.stop_mode_combo.get_active()
        stop_value = self.stop_value_spin.get_value_as_int()
        output_dir = self.choose_folder_button.get_filename()
        delete_when_finished = self.when_finished_combo.get_active() == 0
        inspiration = self.inspiration_combo.get_active()
        if not output_dir:
            self.show_infobar(SELECT_DEST_FOLDER_MSG,
                              Gtk.MessageType.ERROR)
            return

        from bleachbit.Chaff import have_models
        if not have_models():
            # Download models first, then proceed to file generation
            def on_download_complete(success):
                if success:
                    self._start_file_generation(
                        stop_mode, stop_value, inspiration, output_dir, delete_when_finished)
                else:
                    # TRANSLATORS: Error message shown when downloading
                    # chaff models failed.
                    self.show_infobar(_("Download failed"),
                                      Gtk.MessageType.ERROR)
            self.download_models_gui(on_download_complete)
        else:
            self._start_file_generation(
                stop_mode, stop_value, inspiration, output_dir, delete_when_finished)

    def _start_file_generation(self, stop_mode, stop_value, inspiration,
                               output_dir, delete_when_finished):
        """Start generating files after download is complete."""
        self._abort_event = threading.Event()

        def _on_progress(fraction, msg, is_done, error=None):
            """Update progress bar from GLib main loop"""
            if msg:
                self.progressbar.set_text(msg)
            self.progressbar.set_fraction(fraction)
            if is_done:
                self.progressbar.hide()
                self.abort_button.set_sensitive(False)
                self.make_button.set_sensitive(True)
                if error:
                    self.show_infobar(error, Gtk.MessageType.ERROR)
                elif self._abort_event and self._abort_event.is_set():
                    # TRANSLATORS: Notification shown in an infobar when
                    # chaff file generation is aborted by the user.
                    self.show_infobar(_("Chaff generation aborted"),
                                      Gtk.MessageType.WARNING)
                else:
                    # TRANSLATORS: Notification shown in an infobar when chaff file generation
                    # is complete.
                    self.show_infobar(_("Chaff generation complete"),
                                      Gtk.MessageType.INFO)

        def on_progress(fraction, msg=None, is_done=False, error=None):
            """Callback for progress bar"""
            # Use idle_add() because threads cannot make GDK calls.
            GLib.idle_add(_on_progress, fraction, msg, is_done, error)

        # TRANSLATORS: Progress message shown while generating chaff files.
        # 'Generating' is a present participle.
        # To indicate an ongoing operation, include the ellipsis as literal
        # Unicode (…) or as Unicode escape (\u2026).
        msg = _('Generating files\u2026')
        logger.info(msg)
        self.progressbar.show()
        self.progressbar.set_text(msg)
        self.progressbar.set_show_text(True)
        self.progressbar.set_fraction(0.0)
        self.make_button.set_sensitive(False)
        self.abort_button.set_sensitive(True)
        args = (stop_mode, stop_value, inspiration, output_dir,
                delete_when_finished, on_progress, self._abort_event)
        self.thread = threading.Thread(target=make_files_thread, args=args)
        self.thread.start()

    def run(self):
        """Run the dialog"""
        self.show_all()
        self.infobar.hide()
