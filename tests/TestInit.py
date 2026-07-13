# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test cases for __init__
"""

import os

from bleachbit import IS_MAC, IS_POSIX, IS_WINDOWS, get_share_dirs, get_share_path
from tests import common


class InitTestCase(common.BleachbitTestCase):

    """Test cases for __init__"""

    def test_expanduser(self):
        """Unit test for function expanduser()"""
        # already absolute
        test_input = '/home/user/foo'
        test_output = os.path.expanduser(test_input)
        self.assertEqual(test_input, test_output)

        # tilde not at beginning
        test_input = '/home/user/~'
        test_output = os.path.expanduser(test_input)
        self.assertEqual(test_input, test_output)

        # should be expanded
        test_inputs = ()
        if IS_WINDOWS:
            test_inputs = ('~', r'~\ntuser.dat')
        elif IS_MAC:
            # macOS defaults to zsh
            test_inputs = ('~', '~/.zshrc')
        elif IS_POSIX:
            test_inputs = ('~', '~/.profile')
        for test_input in test_inputs:
            test_output = os.path.expanduser(test_input)
            self.assertNotEqual(test_input, test_output)
            msg = None
            if not os.path.exists(test_output) and not test_input == '~':
                msg = f"contents of home directory: {os.listdir(os.path.expanduser('~'))}"
            self.assertExists(test_output, msg)
            if IS_POSIX:
                self.assertTrue(os.path.samefile(
                    test_output, os.path.expanduser(test_input)))

    def test_get_share_dirs(self):
        """Unit test for get_share_dirs()"""
        got_shared_dirs = get_share_dirs()
        # There must be at least one shared directory.
        self.assertGreater(len(got_shared_dirs), 0)
        existing = [d for d in got_shared_dirs if os.path.isdir(d)]
        # At least one of the shared directories must exist.
        self.assertGreater(len(existing), 0,
                           f'No share dir exists among: {got_shared_dirs}')

    def test_get_share_path(self):
        """Unit test for get_share_path()"""
        for fn in ('app-menu.ui', 'protected_path.xml'):
            self.assertExists(get_share_path(fn))
        self.assertIsNone(get_share_path('nonexistent'))


def suite():
    """Return a test suite"""
    return unittest.TestLoader().loadTestsFromTestCase(InitTestCase)
