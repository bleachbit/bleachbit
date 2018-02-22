# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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

from __future__ import absolute_import, print_function

from bleachbit.General import *
from bleachbit import logger
from tests import common

import shutil
import unittest


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

    def test_getrealuid(self):
        """Test for getrealuid()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, getrealuid)
            return
        uid = getrealuid()
        self.assertIsInstance(uid, int)
        self.assertTrue(0 <= uid <= 65535)
        if sudo_mode():
            self.assertGreater(uid, 0)
        logger.debug("os.getenv('LOGNAME') = %s", os.getenv('LOGNAME'))
        logger.debug("os.getenv('SUDO_UID') = %s", os.getenv('SUDO_UID'))
        logger.debug('os.geteuid() = %d', os.geteuid())
        logger.debug('os.getuid() = %d', os.getuid())
        try:
            logger.debug('os.login() = %s', os.getlogin())
        except:
            logger.exception('os.login() raised exception')

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
        args = {'nt': ['cmd.exe', '/c', 'dir', '%windir%\system32', '/s', '/b'],
                'posix': ['find', '/usr/bin']}
        (rc, stdout, stderr) = run_external(args[os.name])
        self.assertEqual(0, rc)
        self.assertEqual(0, len(stderr))

        self.assertRaises(OSError, run_external, ['cmddoesnotexist'])

        args = {'nt': ['cmd.exe', '/c', 'dir', 'c:\doesnotexist'],
                'posix': ['ls', '/doesnotexist']}
        (rc, stdout, stderr) = run_external(args[os.name])
        self.assertNotEqual(0, rc)

    @unittest.skipUnless('posix' == os.name, 'skipping on platforms without sudo')
    def test_run_external_clean_env(self):
        """Unit test for clean_env parameter to run_external()"""

        def run(args, clean_env):
            (rc, stdout, stderr) = run_external(args, clean_env=clean_env)
            self.assertEqual(rc, 0)
            return stdout.rstrip('\n')

        # clean_env should set language to C
        run(['sh', '-c', '[ "x$LANG" = "xC" ]'], clean_env=True)
        run(['sh', '-c', '[ "x$LC_ALL" = "xC" ]'], clean_env=True)

        # clean_env parameter should not alter the PATH, and the PATH
        # should not be empty
        path_clean = run(['bash', '-c', 'echo $PATH'], clean_env=True)
        self.assertEqual(os.getenv('PATH'), path_clean)
        self.assertGreater(len(path_clean), 10)

        path_unclean = run(['bash', '-c', 'echo $PATH'], clean_env=False)
        self.assertEqual(path_clean, path_unclean)

        # With parent environment set to English and parameter clean_env=False,
        # expect English.
        os.putenv('LC_ALL', 'C')
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        self.assertTrue('No such file' in stderr)

        # Set parent environment to Spanish.
        os.putenv('LC_ALL', 'es_MX.UTF-8')
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        if os.path.exists('/usr/share/locale-langpack/es/LC_MESSAGES/coreutils.mo'):
            # Spanish language pack is installed.
            self.assertTrue('No existe el archivo' in stderr)

        # Here the parent environment has Spanish, but the child process
        # should use English.
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=True)
        self.assertEqual(rc, 2)
        self.assertTrue('No such file' in stderr)

        # Reset environment
        os.unsetenv('LC_ALL')

    @unittest.skipUnless('posix' == os.name, 'skipping on platforms without sudo')
    def test_sudo_mode(self):
        """Unit test for sudo_mode"""
        self.assertIsInstance(sudo_mode(), bool)
