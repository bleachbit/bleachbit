# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
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
Test case for module General
"""


import sys
import unittest

sys.path.append('.')
from bleachbit.General import *
from bleachbit.Common import logger


class GeneralTestCase(unittest.TestCase):

    """Test case for module General"""

    def test_boolstr_to_bool(self):
        """Test case for method boolstr_to_bool"""
        tests = (('True', True),
                 ('true', True),
                 ('False', False),
                 ('false', False))

        for test in tests:
            self.assertEqual(boolstr_to_bool(test[0]), test[1])

    def test_getrealuid(self):
        """Test for getrealuid()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, getrealuid)
            return
        uid = getrealuid()
        self.assert_(isinstance(uid, int))
        self.assert_(0 <= uid <= 65535)
        if sudo_mode():
            self.assert_(uid > 0)
        logger.debug("os.getenv('LOGNAME') = %s", os.getenv('LOGNAME'))
        logger.debug("os.getenv('SUDO_UID') = %s", os.getenv('SUDO_UID'))
        logger.debug('os.geteuid() = %d', os.geteuid())
        logger.debug('os.getuid() = %d', str(os.getuid()))
        try:
            logger.debug('os.login() = %s', os.getlogin())
        except:
            traceback.print_exc()
            logger.debug('os.login() raised exception')

    def test_makedirs(self):
        """Unit test for makedirs"""
        def cleanup(dir):
            if not os.path.lexists(dir):
                return
            os.rmdir(dir)
            os.rmdir(os.path.dirname(dir))
            self.assert_(not os.path.lexists(dir))

        if 'nt' == os.name:
            dir = 'c:\\temp\\bleachbit-test-makedirs\\a'
        if 'posix' == os.name:
            dir = '/tmp/bleachbit-test-makedirs/a'
        cleanup(dir)
        # directory does not exist
        makedirs(dir)
        self.assert_(os.path.lexists(dir))
        # directory already exists
        makedirs(dir)
        self.assert_(os.path.lexists(dir))
        # clean up
        cleanup(dir)

    def test_run_external(self):
        """Unit test for run_external"""
        if 'nt' == os.name:
            args = ['cmd.exe', '/c', 'dir', '%windir%\system32', '/s', '/b']
        elif 'posix' == os.name:
            args = ['find', '/usr/bin']
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(0, rc)
        self.assertEqual(0, len(stderr))

        args = ['cmddoesnotexist']
        self.assertRaises(OSError, run_external, args)

        if 'nt' == os.name:
            args = ['cmd.exe', '/c', 'dir', 'c:\doesnotexist']
        elif 'posix' == os.name:
            args = ['ls', '/doesnotexist']
        (rc, stdout, stderr) = run_external(args)
        self.assertNotEqual(0, rc)

    @unittest.skipUnless('posix' == os.name, 'skipping on platforms without sudo')
    def test_sudo_mode(self):
        """Unit test for sudo_mode"""
        self.assert_(isinstance(sudo_mode(), bool))


def suite():
    return unittest.makeSuite(GeneralTestCase)


if __name__ == '__main__':
    unittest.main()
