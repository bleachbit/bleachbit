# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for GuiBasic module.
"""

import unittest
from unittest import mock

from tests import common

from bleachbit.GtkShim import is_gtk_available
from bleachbit.Options import options

HAVE_GTK = is_gtk_available()
if HAVE_GTK:
    from bleachbit import GuiBasic
    from bleachbit.GuiBasic import open_url


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class GuiBasicTestCase(common.BleachbitTestCase):
    """Test case for module GuiBasic"""

    def test_open_url_rejects_disallowed_scheme(self):
        """open_url() must refuse any scheme other than http(s)"""
        urls = ('file:///etc/passwd',
                'javascript:alert(1)',
                'myapp://action',
                'HTTP:evil')  # missing slashes: not a valid http(s) URL
        # The name is reported on a continuation line, which cannot be
        # preceded by a comment, so this covers the statement instead.
        # pylint: disable=possibly-used-before-assignment
        with mock.patch('webbrowser.open') as mock_open, \
                mock.patch.object(GuiBasic.Gtk, 'show_uri_on_window') as mock_show_uri, \
                mock.patch.object(GuiBasic.Gtk, 'show_uri') as mock_show_uri_old, \
                mock.patch.object(GuiBasic, 'logger') as mock_logger:
            for url in urls:
                with self.subTest(url=url):
                    mock_logger.reset_mock()
                    # pylint: disable-next=possibly-used-before-assignment
                    open_url(url, prompt=False)
                    mock_open.assert_not_called()
                    mock_show_uri.assert_not_called()
                    mock_show_uri_old.assert_not_called()
                    mock_logger.error.assert_called_once()

    def test_open_url_accepts_http_https(self):
        """open_url() proceeds past the scheme check for http(s) URLs"""
        with mock.patch('webbrowser.open'), \
                mock.patch.object(GuiBasic.Gtk, 'show_uri_on_window'), \
                mock.patch.object(GuiBasic.Gtk, 'show_uri'), \
                mock.patch.object(GuiBasic, 'logger') as mock_logger:
            open_url('https://example.com', prompt=False)
            mock_logger.error.assert_not_called()

    def test_delete_confirmation_cancel_keeps_setting(self):
        """Only Delete may save an unticked 'Confirm before delete'"""
        # pylint: disable=possibly-used-before-assignment
        gtk = GuiBasic.Gtk
        options.set('expert_mode', True)
        for response, expected in ((gtk.ResponseType.CANCEL, True),
                                   (gtk.ResponseType.DELETE_EVENT, True),
                                   (gtk.ResponseType.ACCEPT, False)):
            with self.subTest(response=response):
                options.set('delete_confirmation', True)
                with mock.patch.object(gtk.Dialog, 'run', return_value=response), \
                        mock.patch.object(gtk.CheckButton, 'get_active', return_value=False):
                    GuiBasic.delete_confirmation_dialog(None, False)
                self.assertEqual(options.get('delete_confirmation'), expected)
