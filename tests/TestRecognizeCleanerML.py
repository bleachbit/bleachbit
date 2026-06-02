# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2024 Andrew Ziem
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
Test case for RecognizeCleanerML
"""

import os
from unittest import mock

import bleachbit
from tests import common
from bleachbit.Options import options, path_to_option
from bleachbit.RecognizeCleanerML import hashdigest, RecognizeCleanerML


class RecognizeCleanerMLTestCase(common.BleachbitTestCase):
    """Test case for RecognizeCleanerML"""

    def test_hash(self):
        """Unit test for hash()"""
        digest = hashdigest('bleachbit')
        self.assertEqual(len(digest), 128)
        self.assertEqual(digest[1:10], '6382c203e')

    def test_init_without_salt(self):
        """Unit test for __init__ when hashsalt is not set in options"""
        if options.has_option('hashsalt'):
            options.config.remove_option('bleachbit', 'hashsalt')
        self.assertFalse(options.has_option('hashsalt'))
        # Create a CleanerML file so list_cleanerml_files() returns a file,
        # which exercises __recognized().
        cleaner_dir = bleachbit.PERSONAL_CLEANERS_DIR
        os.makedirs(cleaner_dir, exist_ok=True)
        cleaner_file = os.path.join(cleaner_dir, 'test_recognize.xml')
        with open(cleaner_file, 'w', encoding='utf-8') as f:
            f.write(
                '<?xml version="1.0"?><cleaner id="test"><label>Test</label></cleaner>')
        with mock.patch('bleachbit.RecognizeCleanerML.cleaner_change_dialog'):
            rcm = RecognizeCleanerML(parent_window=None)
        self.assertIsNotNone(rcm.salt)
        self.assertIsInstance(rcm.salt, str)
        self.assertEqual(len(rcm.salt), 128)
        # Verify __recognized() was exercised by checking the hash was stored.
        self.assertTrue(options.has_option(
            path_to_option(cleaner_file), 'hashpath'))
