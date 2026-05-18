# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for __init__
"""

from tests import common

import os


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
        test_inputs = ('~', r'~\ntuser.dat')
        for test_input in test_inputs:
            test_output = os.path.expanduser(test_input)
            self.assertNotEqual(test_input, test_output)
            self.assertExists(test_output)


def suite():
    return unittest.makeSuite(InitTestCase)
