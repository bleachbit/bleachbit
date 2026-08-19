# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module Log
"""

import logging
import os
import stat
import sys
from unittest import mock

from bleachbit.Log import init_log
from tests import common


class LogTestCase(common.BleachbitTestCase):
    """Test case for module Log"""

    def setUp(self):
        super().setUp()
        self.bleachbit_logger = logging.getLogger('bleachbit')
        self.saved_handlers = list(self.bleachbit_logger.handlers)
        self.saved_level = self.bleachbit_logger.level

    def tearDown(self):
        for handler in self.bleachbit_logger.handlers:
            if handler not in self.saved_handlers:
                handler.close()
        self.bleachbit_logger.handlers = self.saved_handlers
        self.bleachbit_logger.setLevel(self.saved_level)
        super().tearDown()

    @common.skipIfWindows
    def test_init_log_debug_log_file_not_world_readable(self):
        """The --debug-log file must not be created world-readable

        It can contain sensitive system info such as paths and username.
        """
        debug_log_path = os.path.join(self.tempdir, 'debug.log')
        self.assertNotExists(debug_log_path)
        with mock.patch.object(sys, 'argv', ['bleachbit', '--debug-log', debug_log_path]):
            init_log()
        self.assertExists(debug_log_path)
        mode = stat.S_IMODE(os.stat(debug_log_path).st_mode)
        self.assertEqual(mode, 0o600)

    @common.skipIfWindows
    def test_init_log_debug_log_file_existing_untouched(self):
        """init_log() must not clobber an existing debug log file's permissions"""
        debug_log_path = self.write_file('existing_debug.log', text='previous content\n')
        # Any mode that init_log() would not pick on its own works here.
        # The execute bit is the harmless way to differ from its 0o600.
        os.chmod(debug_log_path, 0o700)
        with mock.patch.object(sys, 'argv', ['bleachbit', '--debug-log', debug_log_path]):
            init_log()
        mode = stat.S_IMODE(os.stat(debug_log_path).st_mode)
        self.assertEqual(mode, 0o700)
        with open(debug_log_path, encoding='utf-8') as f:
            self.assertIn('previous content', f.read())
