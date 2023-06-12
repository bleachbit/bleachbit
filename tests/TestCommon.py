# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Test case for Common
"""

import os

import bleachbit
from tests import common


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
        envs = {'posix': ['XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'HOME'],
                'nt': ['AppData', 'CommonAppData', 'Documents', 'ProgramFiles', 'UserProfile', 'WinDir']}
        for env in envs[os.name]:
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
        abs_dirs = {'posix': '$HOME', 'nt': '%USERPROFILE%'}
        abs_dir = os.path.expandvars(abs_dirs[os.name])
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
            f.write(' ' * fsize)
        self.assertEqual(fsize, getsize(fn))

        # Do not truncate.
        common.touch_file(fn)
        self.assertExists(fn)
        self.assertEqual(fsize, getsize(fn))
