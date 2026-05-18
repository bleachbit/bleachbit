# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module General
"""

from bleachbit.General import *
from bleachbit import logger
from tests import common

import shutil

class GeneralTestCase(common.BleachbitTestCase):
    """Test case for module General"""

    def test_boolstr_to_bool(self):
        """Test case for method boolstr_to_bool"""
        tests = (('True', True),
                 ('true', True),
                 ('False', False),
                 ('false', False))

        for test in tests:
            self.assertEqual(boolstr_to_bool(test[0]), test[1])

    def test_makedirs(self):
        """Unit test for makedirs"""
        dir = os.path.join(self.tempdir, 'just', 'a', 'directory', 'adventure')
        # directory does not exist
        makedirs(dir)
        self.assertLExists(dir)
        # directory already exists
        makedirs(dir)
        self.assertLExists(dir)
        # clean up
        shutil.rmtree(os.path.join(self.tempdir, 'just'))

    def test_run_external(self):
        """Unit test for run_external"""
        (rc, stdout, stderr) = run_external(['cmd.exe', '/c', 'dir', r'%windir%\system32', '/s', '/b'])
        self.assertEqual(0, rc)
        self.assertEqual(0, len(stderr))

        self.assertRaises(OSError, run_external, ['cmddoesnotexist'])

        (rc, stdout, stderr) = run_external(['cmd.exe', '/c', 'dir', r'c:\doesnotexist'])
        self.assertNotEqual(0, rc)

    def test_set_root_log_level(self):
        """Unit test for set_root_log_level"""
        import logging
        from bleachbit.Log import set_root_log_level
        root_logger = logging.getLogger('bleachbit')
        # Save original level to restore later
        original_level = root_logger.level
        try:
            # Test that set_root_log_level respects existing DEBUG level
            root_logger.setLevel(logging.DEBUG)
            set_root_log_level(False)  # Should NOT change from DEBUG
            self.assertEqual(root_logger.level, logging.DEBUG)
            # Test that set_root_log_level can set INFO when not DEBUG
            root_logger.setLevel(logging.INFO)
            set_root_log_level(False)
            self.assertEqual(root_logger.level, logging.INFO)
            # Test that set_root_log_level can enable DEBUG
            root_logger.setLevel(logging.INFO)
            set_root_log_level(True)
            self.assertEqual(root_logger.level, logging.DEBUG)
        finally:
            # Restore original level
            root_logger.setLevel(original_level)
