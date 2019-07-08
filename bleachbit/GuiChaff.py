# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-


# BleachBit
# Copyright (C) 2008-2019 Andrew Ziem
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
GUI for making chaff
"""

from __future__ import absolute_import

from bleachbit import _

from gi.repository import Gtk
import logging
import os
URL_SUBJECT = 'https://sourceforge.net/projects/bleachbit/files/chaff/subject_model.json.bz2/download'
URL_CONTENT = 'https://sourceforge.net/projects/bleachbit/files/chaff/content_model.json.bz2/download'


logger = logging.getLogger(__name__)


class ChaffDialog(Gtk.Dialog):

    """Present the dialog to make chaff"""

    def __init__(self, parent):
        from bleachbit import options_dir
        self.content_model_path = os.path.join(
            options_dir, 'clinton_content_model.json.bz2')
        self.subject_model_path = os.path.join(
            options_dir, 'clinton_subject_model.json.bz2')

        self._make_dialog(parent)

    def _make_dialog(self, parent):
        """Make the main dialog"""
        Gtk.Dialog.__init__(self, _("Make chaff"), parent)
        self.set_border_width(5)
        box = self.get_content_area()

        label = Gtk.Label(
            _("Make randomly-generated messages derived from Hillary Clinton's emails."))
        box.add(label)

        spin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        spin_box.add(Gtk.Label(_("Number of files")))
        adjustment = Gtk.Adjustment(100, 1, 99999, 1, 1000, 0)
        self.file_count = Gtk.SpinButton(adjustment=adjustment)
        spin_box.add(self.file_count)
        box.add(spin_box)

        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        folder_box.add(Gtk.Label(_("Select destination folder")))
        self.choose_folder_button = Gtk.FileChooserButton()
        self.choose_folder_button.set_action(
            Gtk.FileChooserAction.SELECT_FOLDER)
        folder_box.add(self.choose_folder_button)
        box.add(folder_box)

        make_button = Gtk.Button(_("Make files"))
        make_button.connect('clicked', self.on_make_files)
        box.add(make_button)

    def download_models(self):
        from urllib2 import urlopen, URLError, HTTPError
        from httplib import HTTPException
        import socket
        for (url, fn) in ((URL_SUBJECT, self.subject_model_path), (URL_CONTENT, self.content_model_path)):
            if os.path.exists(fn):
                logger.debug('File %s already exists', fn)
                continue
            logger.info('Downloading %s to %s', url, fn)
            try:
                resp = urlopen(url)
                with open(fn, 'wb') as f:
                    f.write(resp.read())
            except (URLError, HTTPError, HTTPException, socket.error) as exc:
                msg = _('Downloading url failed: %s') % url
                msg2 = '{}: {}'.format(type(exc).__name__, exc)
                logger.exception(msg)
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.CANCEL, msg)
                dialog.format_secondary_text(msg2)
                dialog.run()
                dialog.destroy()
                from bleachbit.FileUtilities import delete
                delete(fn, ignore_missing=True)  # delete any partial download
                return False

        return True

    def download_models_dialog(self):
        """Download models"""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.OK_CANCEL, _("Download data needed for email generator?"))
        response = dialog.run()
        ret = None
        if response == Gtk.ResponseType.OK:
            # User wants to download
            ret = self.download_models()  # True if successful
        elif response == Gtk.ResponseType.CANCEL:
            ret = False
        dialog.destroy()
        return ret

    def on_make_files(self, widget):
        """Callback for make files button"""
        email_count = self.file_count.get_value_as_int()
        email_output_folder = self.choose_folder_button.get_filename()
        if not email_output_folder:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CANCEL, _("Select destination folder"))
            dialog.run()
            dialog.destroy()
            return
        from bleachbit import options_dir
        if not os.path.exists(self.content_model_path) or not os.path.exists(self.subject_model_path):
            if not self.download_models_dialog():
                return

        from bleachbit.Chaff import generate_emails
        logger.info('Generating emails')
        generate_emails(email_count, self.content_model_path,
                        self.subject_model_path, email_output_folder)

    def run(self):
        """Run the dialog"""
        self.show_all()
