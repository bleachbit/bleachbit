# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for Bootstrap module.
"""

import os
from unittest import mock

from tests import common

from bleachbit import Bootstrap


class BootstrapTestCase(common.BleachbitTestCase):
    """Test cases for Bootstrap"""

    def test_gdk_scale_environ(self):
        """Scale rounds to the nearest integer, 150% rounds down"""
        tests = (
            (None, {}),
            (96, {}),
            (120, {}),
            (144, {}),
            (168, {'GDK_SCALE': '2'}),
            (192, {'GDK_SCALE': '2'}),
            (240, {'GDK_SCALE': '2'}),
            (264, {'GDK_SCALE': '3'}),
            (288, {'GDK_SCALE': '3'}),
        )
        for dpi, expected in tests:
            with self.subTest(dpi=dpi):
                self.assertEqual(Bootstrap.gdk_scale_environ(dpi), expected)

    @common.skipUnlessWindows
    def test_apply_hidpi_scale(self):
        """GDK variables are set from the DPI unless the user set one"""
        clean = {k: v for k, v in os.environ.items() if k not in
                 ('GDK_SCALE', 'GDK_WIN32_FONT_RESOLUTION', 'GDK_WIN32_DISABLE_HIDPI')}
        with mock.patch.dict(os.environ, clean, clear=True), \
                mock.patch('bleachbit.Bootstrap.gtk_default_scale', None), \
                mock.patch('bleachbit.Windows.get_system_dpi', return_value=168):
            Bootstrap._apply_hidpi_scale()  # pylint: disable=protected-access
            self.assertEqual(os.environ['GDK_SCALE'], '2')
            self.assertNotIn('GDK_WIN32_FONT_RESOLUTION', os.environ)
            self.assertEqual(Bootstrap.gtk_default_scale, 1)
        for var in ('GDK_SCALE', 'GDK_WIN32_FONT_RESOLUTION', 'GDK_WIN32_DISABLE_HIDPI'):
            with self.subTest(var=var), \
                    mock.patch.dict(os.environ, dict(clean, **{var: '1'}), clear=True), \
                    mock.patch('bleachbit.Windows.get_system_dpi') as get_dpi:
                Bootstrap._apply_hidpi_scale()  # pylint: disable=protected-access
                get_dpi.assert_not_called()
                self.assertEqual(os.environ[var], '1')
