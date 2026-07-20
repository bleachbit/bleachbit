# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module DesktopMenuOptions
"""

import os
import stat
from unittest import mock

from tests import common
from bleachbit.DesktopMenuOptions import install_kde_service_menu_file
from bleachbit.Options import options


class DesktopMenuOptionsTestCase(common.BleachbitTestCase):
    """Test case for install_kde_service_menu_file()"""

    def _service_file_path(self, home):
        return os.path.join(
            home, '.local', 'share', 'kio', 'servicemenus',
            'shred_with_bleachbit.desktop')

    @common.skipIfWindows
    def test_install_kde_service_menu_file_refuses_symlink(self):
        """A planted symlink at the service file path must be refused, not followed"""
        home = self.mkdtemp(prefix='bb-kde-home')
        service_file = self._service_file_path(home)
        os.makedirs(os.path.dirname(service_file))
        with mock.patch.dict(os.environ, {'HOME': home}, clear=False), \
                mock.patch.object(options, 'get', return_value=True), \
                mock.patch('bleachbit.FileUtilities.os.path.islink',
                          side_effect=lambda p: p == service_file):
            os.environ.pop('XDG_DATA_HOME', None)
            install_kde_service_menu_file()
        self.assertNotExists(service_file)

    @common.skipIfWindows
    def test_install_kde_service_menu_file_creates_file(self):
        """The service file is created with mode 0o755 when the option is enabled"""
        home = self.mkdtemp(prefix='bb-kde-home')
        service_file = self._service_file_path(home)
        with mock.patch.dict(os.environ, {'HOME': home}, clear=False), \
                mock.patch.object(options, 'get', return_value=True):
            os.environ.pop('XDG_DATA_HOME', None)
            install_kde_service_menu_file()
        self.assertExists(service_file)
        with open(service_file, encoding='utf-8') as f:
            self.assertIn('Shred With Bleachbit', f.read())
        mode = stat.S_IMODE(os.stat(service_file).st_mode)
        self.assertEqual(mode, 0o755)

    @common.skipIfWindows
    def test_install_kde_service_menu_file_removes_when_disabled(self):
        """The service file is removed when the option is disabled"""
        home = self.mkdtemp(prefix='bb-kde-home')
        service_file = self._service_file_path(home)
        os.makedirs(os.path.dirname(service_file))
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write('placeholder')
        with mock.patch.dict(os.environ, {'HOME': home}, clear=False), \
                mock.patch.object(options, 'get', return_value=False):
            os.environ.pop('XDG_DATA_HOME', None)
            install_kde_service_menu_file()
        self.assertNotExists(service_file)
