# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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

# standard library
import copy
import os
import shutil

# local
from bleachbit import logger
from bleachbit.FileUtilities import exists_in_path
from bleachbit.General import (
    boolstr_to_bool,
    get_real_uid,
    get_real_username,
    makedirs,
    run_external,
    sudo_mode)
from tests import common


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

    def test_get_real_uid(self):
        """Test for get_real_uid()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, get_real_uid)
            return
        uid = get_real_uid()
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

    def test_get_real_username(self):
        """Test for get_real_username()"""
        if 'posix' != os.name:
            self.assertRaises(RuntimeError, get_real_username)
            return
        username = get_real_username()
        self.assertIsInstance(username, str)
        self.assertGreater(len(username), 0)
        if sudo_mode():
            self.assertNotEqual(username, 'root')

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
        args = {'nt': ['cmd.exe', '/c', 'dir', r'%windir%\system32', '/s', '/b'],
                'posix': ['find', '/usr/bin']}
        (rc, stdout, stderr) = run_external(args[os.name])
        self.assertEqual(0, rc)
        self.assertEqual(0, len(stderr))

        self.assertRaises(OSError, run_external, ['cmddoesnotexist'])

        args = {'nt': ['cmd.exe', '/c', 'dir', r'c:\doesnotexist'],
                'posix': ['ls', '/doesnotexist']}
        (rc, stdout, stderr) = run_external(args[os.name])
        self.assertNotEqual(0, rc)

    @common.skipIfWindows
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
        self.assertEqual(common.get_env('PATH'), path_clean)
        self.assertGreater(len(path_clean), 10)

        path_unclean = run(['bash', '-c', 'echo $PATH'], clean_env=False)
        self.assertEqual(path_clean, path_unclean)

        # With parent environment set to English and parameter clean_env=False,
        # expect English

        old_environ = copy.deepcopy(os.environ)

        lc_all_old = common.get_env('LC_ALL')
        lang_old = common.get_env('LANG')
        common.put_env('LC_ALL', 'C')
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        self.assertIn('No such file', stderr)

        # Set parent environment to Spanish.
        common.put_env('LC_ALL', 'es_MX.UTF-8')
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=False)
        self.assertEqual(rc, 2)
        if os.path.exists('/usr/share/locale-langpack/es/LC_MESSAGES/coreutils.mo'):
            # Spanish language pack is installed.
            self.assertIn('No existe el archivo', stderr)

        # Here the parent environment has Spanish, but the child process
        # should use English.
        (rc, stdout, stderr) = run_external(
            ['ls', '/doesnotexist'], clean_env=True)
        self.assertEqual(rc, 2)
        self.assertIn('No such file', stderr)

        # Reset environment
        self.assertNotEqual(old_environ, copy.deepcopy(os.environ))
        common.put_env('LC_ALL', lc_all_old)
        common.put_env('LANG', lang_old)
        self.assertEqual(old_environ, copy.deepcopy(os.environ))

    @common.skipIfWindows
    def test_dconf(self):
        """Unit test for dconf"""
        if not exists_in_path('dconf'):
            self.skipTest('dconf not found')
        if sudo_mode():
            self.skipTest('dconf not supported in sudo mode')
        args = ['dconf', 'write',
                '/apps/bleachbit/test', 'true']
        (rc, stdout, stderr) = run_external(args)
        self.assertEqual(0, rc, stderr)
        self.assertEqual('', stderr)
        self.assertEqual('', stdout)

    @common.skipIfWindows
    def test_sudo_mode(self):
        """Unit test for sudo_mode"""
        self.assertIsInstance(sudo_mode(), bool)
