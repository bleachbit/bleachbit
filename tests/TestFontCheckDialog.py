# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for FontCheckDialog module.
"""

import unittest

from tests import common

from bleachbit.GtkShim import is_gtk_available

HAVE_GTK = is_gtk_available()
if HAVE_GTK:
    from bleachbit.GtkShim import Gtk
    from bleachbit.FontCheckDialog import (ALT_FONT_CLASS, DIGIT_SAMPLE,
                                           create_font_check_dialog)


@unittest.skipUnless(HAVE_GTK, 'requires GTK+ module and a display environment')
class FontCheckDialogTestCase(common.BleachbitTestCase):
    """Test case for module FontCheckDialog"""

    def _labels(self):
        """Return every label in a new dialog"""
        # pylint: disable-next=possibly-used-before-assignment
        dialog = create_font_check_dialog()
        self.addCleanup(dialog.destroy)
        return [child for child in dialog.get_content_area().get_children()
                if isinstance(child, Gtk.Label)]

    def test_one_label_uses_the_alternate_font(self):
        """The question is shown in the default and the alternate font"""
        labels = self._labels()
        self.assertEqual(len(labels), 2)
        # pylint: disable-next=possibly-used-before-assignment
        styled = [label for label in labels
                  if label.get_style_context().has_class(ALT_FONT_CLASS)]
        self.assertEqual(len(styled), 1)

    def test_digits_shown_in_both_fonts(self):
        """A font that breaks only the digits does not pass the check"""
        labels = self._labels()
        self.assertEqual(len(labels), 2)
        for label in labels:
            # pylint: disable-next=possibly-used-before-assignment
            self.assertIn(DIGIT_SAMPLE, label.get_text())
