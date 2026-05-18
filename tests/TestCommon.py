# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for Common
"""

from tests import common

import os


class CommonTestCase(common.BleachbitTestCase):
    """Test case for Common."""

    def test_expandvars(self):
        """Unit test for expandvars."""
        var = os.path.expandvars('$HOME')
        self.assertIsString(var)

    def test_environment(self):
        """Test for important environment variables"""
        # useful for researching
        # grep -Poh "([\\$%]\w+)" cleaners/*xml | cut -b2- | sort | uniq -i
        envs = ['AppData', 'CommonAppData', 'Documents',
                'ProgramFiles', 'UserProfile', 'WinDir']
        for env in envs:
            e = os.getenv(env)
            self.assertIsNotNone(e)
            self.assertGreater(len(e), 4)

    def test_expanduser(self):
        """Unit test for expanduser."""
        # Return Unicode when given Unicode.
        self.assertIsString(os.path.expanduser('~'))

        # Blank input should give blank output.
        self.assertEqual(os.path.expanduser(''), '')

        # An absolute path should not be altered.
        abs_dir = os.path.expandvars('%USERPROFILE%')
        self.assertExists(abs_dir)
        self.assertEqual(os.path.expanduser(abs_dir), abs_dir)
        # A relative path (without a reference to the home directory)
        # should not be expanded.
        self.assertEqual(os.path.expanduser('common'), 'common')

    def test_touch_file(self):
        """Unit test for touch_file"""
        fn = os.path.join(self.tempdir, 'test_touch_file')
        self.assertNotExists(fn)

        # Create empty file.
        common.touch_file(fn)
        from bleachbit.FileUtilities import getsize
        self.assertExists(fn)
        self.assertEqual(0, getsize(fn))

        # Increase size of file.
        fsize = 2**13
        with open(fn, "w") as f:
            f.write(' '*fsize)
        self.assertEqual(fsize, getsize(fn))

        # Do not truncate.
        common.touch_file(fn)
        self.assertExists(fn)
        self.assertEqual(fsize, getsize(fn))
