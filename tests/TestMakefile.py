# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for Makefile
"""

import os
import subprocess

from tests import common
from bleachbit import APP_VERSION, IS_LINUX, IS_MAC, IS_WINDOWS
from bleachbit.FileUtilities import exe_exists
from bleachbit.General import get_executable, run_external


def _find_gnu_make():
    """Return a GNU Make executable, or None.

    The Makefile is GNU-specific (ifdef, ifneq, abspath, $(shell)). On
    FreeBSD /usr/bin/make is BSD make, so honor $MAKE and prefer gmake.
    """
    candidates = []
    env_make = os.environ.get('MAKE')
    if env_make:
        candidates.append(env_make)
    # Prefer `make` when it is GNU (Linux/macOS). On FreeBSD, /usr/bin/make
    # is BSD make, so the GNU Make check fails and we fall through to gmake.
    candidates.extend(('make', 'gmake'))
    seen = set()
    for exe in candidates:
        if exe in seen:
            continue
        seen.add(exe)
        if not exe_exists(exe) and not os.path.isfile(exe):
            continue
        (_rc, stdout, stderr) = run_external([exe, '--version'])
        if 'GNU Make' in (stdout or '') + (stderr or ''):
            return exe
    return None


class MakefileTestCase(common.BleachbitTestCase):
    """Test case for Makefile"""

    def setUp(self):
        """Locate xgettext, make, and tar before running the test"""
        super().setUp()
        src_base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        self.src_base_dir = src_base_dir

        # the CI workflow adds the MSYS2 bin directory to PATH before tests,
        # so the tools are found via exe_exists() (which searches PATH).
        # On Windows, exists_in_path() does not append .exe, so do it here.
        exe_suffix = '.exe' if IS_WINDOWS else ''

        tools = {
            'xgettext_exe': ('xgettext', 'xgettext (run `apt install gettext` or equivalent)'),
            'tar_exe': ('tar', 'tar (not found in PATH)'),
        }
        # GNU make is only used on non-Windows; the Windows path returns
        # early before invoking it, so do not require it there.
        if not IS_WINDOWS:
            self.make_exe = _find_gnu_make()
            missing_make = not self.make_exe
        else:
            self.make_exe = None
            missing_make = False

        missing = []
        if missing_make:
            missing.append(
                'GNU Make (gmake or GNU make; set MAKE= if it is not in PATH)')
        for attr, (tool_name, error_msg) in tools.items():
            exe_name = tool_name + exe_suffix
            if exe_exists(exe_name):
                setattr(self, attr, exe_name)
            else:
                setattr(self, attr, None)
                missing.append(error_msg)

        if missing:
            # Linux always requires the build tools. On macOS and Windows,
            # they are optional locally but required in CI.
            if IS_LINUX or ('CI' in os.environ and (IS_MAC or IS_WINDOWS)):
                raise RuntimeError(
                    'Missing required build tools: ' + '; '.join(missing))
            self.skipTest(
                'Missing required build tools: ' + '; '.join(missing))

    def test_make_source(self):
        """Test Makefile for source distribution"""
        src_base_dir = self.src_base_dir
        os.chdir(src_base_dir)
        make_exe = self.make_exe
        tar_exe = self.tar_exe

        ver_name = 'bleachbit-' + APP_VERSION

        # clean up from any previous test
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        if os.path.exists(pkg_fn):
            os.remove(pkg_fn)
        self.assertNotExists(pkg_fn)

        # build source distribution
        # Override PYTHONWARNINGS because the CI environment sets it to 'error',
        # which can cause sdist to fail silently on Windows (rc=0 but no archive).
        sdist_env = dict(os.environ)
        if IS_WINDOWS:
            sdist_env['PYTHONWARNINGS'] = 'default'
        sdist_cmd = [get_executable(), 'setup.py', 'sdist', '--formats=gztar']
        (rc, stdout, stderr) = run_external(
            sdist_cmd, env=sdist_env, clean_env=False)
        self.assertEqual(rc, 0, stderr + stdout)
        pkg_fn = os.path.join('dist', ver_name + '.tar.gz')
        self.assertExists(pkg_fn)

        # extract source distribution
        extract_dir = os.path.join(self.tempdir, 'extract')
        os.mkdir(extract_dir)
        tar_cmd = [tar_exe, 'xzf', pkg_fn, '-C', extract_dir]
        (rc, _, stderr) = run_external(tar_cmd)
        self.assertEqual(rc, 0, stderr)
        extract_subdir = os.path.join(extract_dir, ver_name)
        self.assertExists(os.path.join(extract_subdir, 'Makefile'))

        # Verify a cleaner is present in the source distribution
        self.assertExists(os.path.join(
            extract_subdir, 'cleaners', 'chromium.xml'))

        if IS_WINDOWS:
            # The make targets `delete_windows_files` and `install` do not
            # work under MSYS2 because bash strips backslashes from the
            # Windows make path, and Windows does not use make for installation.
            return

        # delete Windows files using make
        canary_fn = os.path.join(
            extract_subdir, 'cleaners', 'windows_explorer.xml')
        self.assertExists(canary_fn)
        del_win_command = [make_exe, 'delete_windows_files']
        os.chdir(extract_subdir)
        (rc, _, stderr) = run_external(del_win_command)
        self.assertEqual(rc, 0, stderr)
        self.assertNotExists(canary_fn)

        # install using make
        install_tgt_dir = os.path.join(self.tempdir, 'install')
        install_command = [make_exe,
                           'install', 'DESTDIR=' + install_tgt_dir]
        os.chdir(extract_subdir)
        (rc, _, stderr) = run_external(install_command)
        self.assertEqual(
            rc, 0, f"make install failed with rc={rc}, stderr={stderr}")
        self.assertTrue(os.path.isdir(install_tgt_dir))
        self.assertExists(os.path.join(
            install_tgt_dir, 'usr/local/share/bleachbit/cleaners/chromium.xml'))

        # The launcher must not depend on PATH, where a pyenv shim or a
        # venv without PyGObject may come first.
        launcher_fn = os.path.join(install_tgt_dir, 'usr/local/bin/bleachbit')
        self.assertExists(launcher_fn)
        self.assertTrue(os.access(launcher_fn, os.X_OK))
        with open(launcher_fn, encoding='utf-8') as f:
            shebang = f.readline().rstrip('\n')
        self.assertTrue(shebang.startswith('#!/'), shebang)
        interpreter = shebang[2:]
        self.assertNotEqual(os.path.basename(interpreter), 'env', shebang)
        self.assertTrue(os.path.isfile(interpreter), shebang)
        with open(launcher_fn, encoding='utf-8') as f:
            lines = f.readlines()
        with open('bleachbit.py', encoding='utf-8') as f:
            self.assertEqual(lines[1:], f.readlines()[1:])

        # a relative PATH entry must still give an absolute shebang
        rel_bin = os.path.join(extract_subdir, 'rel', 'bin')
        os.makedirs(rel_bin)
        wrapper_fn = os.path.join(rel_bin, 'python3')
        marker_fn = os.path.join(self.tempdir, 'wrapper-ran')
        with open(wrapper_fn, 'w', encoding='utf-8') as f:
            f.write(f'#!/bin/sh\n: > "{marker_fn}"\n'
                    f'exec "{get_executable()}" "$@"\n')
        os.chmod(wrapper_fn, 0o700)
        # an outer `make tests-pytest PYTHON=...` reaches this make through
        # MAKEFLAGS and would skip the PATH lookup
        rel_env = {key: value for key, value in os.environ.items()
                   if key not in ('MAKEFLAGS', 'MFLAGS', 'MAKELEVEL')}
        rel_env['PATH'] = os.pathsep.join(
            [os.path.join('rel', 'bin'), rel_env['PATH']])
        rel_tgt_dir = os.path.join(self.tempdir, 'install-rel')
        # not run_external(), which drops a relative PATH entry as root
        proc = subprocess.run(
            [make_exe, 'install', 'DESTDIR=' + rel_tgt_dir, 'PYTHON=python3'],
            env=rel_env, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertExists(marker_fn)
        with open(os.path.join(rel_tgt_dir, 'usr/local/bin/bleachbit'),
                  encoding='utf-8') as f:
            shebang = f.readline().rstrip('\n')
        self.assertTrue(shebang.startswith('#!/'), shebang)
        self.assertTrue(os.path.isfile(shebang[2:]), shebang)

        # written as given, not through a sed replacement
        odd_tgt_dir = os.path.join(self.tempdir, 'install-odd')
        odd_python = '/opt/a&b|c/python3'
        (rc, _, stderr) = run_external(
            [make_exe, 'install', 'DESTDIR=' + odd_tgt_dir,
             'PYTHON_SHEBANG=' + odd_python])
        self.assertEqual(rc, 0, stderr)
        with open(os.path.join(odd_tgt_dir, 'usr/local/bin/bleachbit'),
                  encoding='utf-8') as f:
            self.assertEqual(f.readline(), f'#!{odd_python}\n')

        # the kernel would cut the interpreter at the space
        (rc, stdout, _) = run_external(
            [make_exe, 'install',
             'DESTDIR=' + os.path.join(self.tempdir, 'install-space'),
             'PYTHON_SHEBANG=/opt/my python/python3'])
        self.assertNotEqual(rc, 0)
        self.assertIn('shebang', stdout)
