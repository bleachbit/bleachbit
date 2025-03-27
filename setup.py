#!/usr/bin/env python
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
Build BleachBit tarballs and exe
"""

import glob
import os
import sys
import tempfile
from setuptools import setup

if sys.platform == 'win32':
    try:
        import py2exe
    except ImportError:
        print('warning: py2exe not available')

import bleachbit
import bleachbit.General
import bleachbit.FileUtilities

APP_NAME = 'BleachBit'
APP_DESCRIPTION = "BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had."

data_files = []
if sys.platform == 'linux':
    data_files.append(('/usr/share/applications',
                      ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))
elif sys.platform[:6] == 'netbsd':
    data_files.append(('/usr/pkg/share/applications',
                      ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/pkg/share/pixmaps/', ['./bleachbit.png']))
elif sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
    data_files.append(
        ('/usr/local/share/applications', ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/local/share/pixmaps/', ['./bleachbit.png']))


args = {}
if 'py2exe' in sys.argv:
    # see multiple issues such as https://github.com/bleachbit/bleachbit/issues/1000
    APP_DESCRIPTION = 'BleachBit software cleaner'

    # Common metadata for both GUI and console executables
    common_metadata = {
        'product_name': APP_NAME,
        'description': APP_DESCRIPTION,
        'version': bleachbit.APP_VERSION,
        'icon_resources': [(1, 'windows/bleachbit.ico')],
        'company_name': APP_NAME,
        'copyright': 'Copyright (C) 2008-2025 Andrew Ziem'
    }

    # GUI executable
    gui_metadata = common_metadata.copy()
    gui_metadata['script'] = 'bleachbit.py'
    args['windows'] = [gui_metadata]

    # Console executable
    console_metadata = common_metadata.copy()
    console_metadata['script'] = 'bleachbit_console.py'
    args['console'] = [console_metadata]
    args['options'] = {
        'py2exe': {
            'packages': ['encodings', 'gi', 'gi.overrides', 'plyer'],
            'optimize': 2,  # extra optimization (like python -OO)
            'includes': ['gi'],
            'excludes': ['pyreadline', 'difflib', 'doctest',
                         'pickle', 'ftplib', 'bleachbit.Unix'],
            'dll_excludes': [
                'libgstreamer-1.0-0.dll',
                'CRYPT32.DLL',  # required by ssl
                'DNSAPI.DLL',
                'IPHLPAPI.DLL',  # psutil
                'MPR.dll',
                'MSIMG32.DLL',
                'MSWSOCK.dll',
                'NSI.dll',  # psutil
                'PDH.DLL',  # psutil
                'PSAPI.DLL',
                'POWRPROF.dll',
                'USP10.DLL',
                'WINNSI.DLL',  # psutil
                'WTSAPI32.DLL',  # psutil
                'api-ms-win-core-apiquery-l1-1-0.dll',
                'api-ms-win-core-crt-l1-1-0.dll',
                'api-ms-win-core-crt-l2-1-0.dll',
                'api-ms-win-core-debug-l1-1-1.dll',
                'api-ms-win-core-delayload-l1-1-1.dll',
                'api-ms-win-core-errorhandling-l1-1-0.dll',
                'api-ms-win-core-errorhandling-l1-1-1.dll',
                'api-ms-win-core-file-l1-1-0.dll',
                'api-ms-win-core-file-l1-2-1.dll',
                'api-ms-win-core-handle-l1-1-0.dll',
                'api-ms-win-core-heap-l1-1-0.dll',
                'api-ms-win-core-heap-l1-2-0.dll',
                'api-ms-win-core-heap-obsolete-l1-1-0.dll',
                'api-ms-win-core-io-l1-1-1.dll',
                'api-ms-win-core-kernel32-legacy-l1-1-0.dll',
                'api-ms-win-core-kernel32-legacy-l1-1-1.dll',
                'api-ms-win-core-libraryloader-l1-2-0.dll',
                'api-ms-win-core-libraryloader-l1-2-1.dll',
                'api-ms-win-core-localization-l1-2-1.dll',
                'api-ms-win-core-localization-obsolete-l1-2-0.dll',
                'api-ms-win-core-memory-l1-1-0.dll',
                'api-ms-win-core-memory-l1-1-2.dll',
                'api-ms-win-core-perfstm-l1-1-0.dll',
                'api-ms-win-core-processenvironment-l1-2-0.dll',
                'api-ms-win-core-processthreads-l1-1-0.dll',
                'api-ms-win-core-processthreads-l1-1-2.dll',
                'api-ms-win-core-profile-l1-1-0.dll',
                'api-ms-win-core-registry-l1-1-0.dll',
                'api-ms-win-core-registry-l2-1-0.dll',
                'api-ms-win-core-string-l1-1-0.dll',
                'api-ms-win-core-string-obsolete-l1-1-0.dll',
                'api-ms-win-core-synch-l1-1-0.dll',
                'api-ms-win-core-synch-l1-2-0.dll',
                'api-ms-win-core-sysinfo-l1-1-0.dll',
                'api-ms-win-core-sysinfo-l1-2-1.dll',
                'api-ms-win-core-threadpool-l1-2-0.dll',
                'api-ms-win-core-timezone-l1-1-0.dll',
                'api-ms-win-core-util-l1-1-0.dll',
                'api-ms-win-eventing-classicprovider-l1-1-0.dll',
                'api-ms-win-eventing-consumer-l1-1-0.dll',
                'api-ms-win-eventing-controller-l1-1-0.dll',
                'api-ms-win-eventlog-legacy-l1-1-0.dll',
                'api-ms-win-perf-legacy-l1-1-0.dll',
                'api-ms-win-security-base-l1-2-0.dll',
                'w9xpopen.exe',  # not needed after Windows 9x
            ],
            'compressed': True  # create a compressed zipfile
        }
    }

    # check for 32-bit
    import struct
    bits = 8 * struct.calcsize('P')
    assert 32 == bits


def recompile_mo(langdir, app, langid, dst):
    """Recompile gettext .mo file to shrink file size."""
    mo_pathname = os.path.normpath(f'{langdir}/LC_MESSAGES/{app}.mo')
    if not os.path.exists(mo_pathname):
        print('info: does not exist: %s', mo_pathname)
        return

    # decompile .mo to .po
    po = os.path.join(dst, langid + '.po')
    __args = ['msgunfmt', '-o', po,
              mo_pathname]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # shrink .po
    po2 = os.path.join(dst, langid + '.po2')
    __args = ['msgmerge', '--no-fuzzy-matching', po,
              os.path.normpath(f'windows/{app}.pot'),
              '-o', po2]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # compile smaller .po to smaller .mo
    __args = ['msgfmt', po2, '-o', mo_pathname]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # clean up
    os.remove(po)
    os.remove(po2)


def supported_languages():
    """Return list of supported languages by scanning ./po/"""
    langs = []
    for pathname in glob.glob('po/*.po'):
        basename = os.path.basename(pathname)
        langs.append(os.path.splitext(basename)[0])
    return sorted(langs)


def clean_dist_locale():
    """Clean dist/share/locale"""
    tmpd = tempfile.mkdtemp('gtk_locale')
    supported_langs = supported_languages()
    basedir = os.path.normpath('dist/share/locale')
    have_msgunfmt = bleachbit.FileUtilities.exe_exists(
        'msgunfmt') or bleachbit.FileUtilities.exe_exists('msgunfmt.exe')
    recompile_langs = []  # supported languages to recompile
    remove_langs = []  # unsupported languages to remove
    for langid in sorted(os.listdir(basedir)):
        if langid in supported_langs:
            recompile_langs.append(langid)
        else:
            remove_langs.append(langid)
    if recompile_langs:
        if have_msgunfmt:
            print(f"recompiling supported GTK languages: {recompile_langs}")
            for lang_id in recompile_langs:
                recompile_mo(basedir, 'gtk30', lang_id, tmpd)
        else:
            print('warning: msgunfmt missing: skipping recompile')
    if remove_langs:
        print(f"removing unsupported GTK languages: {remove_langs}")
        for langid in remove_langs:
            langdir = os.path.join(basedir, langid)
            if os.path.exists(langdir):
                print(f"Removing directory: {langdir}")
                shutil.rmtree(langdir)
    else:
        print("no unsupported GTK languages found")
    os.rmdir(tmpd)


def run_setup():
    setup(name='bleachbit',
          version=bleachbit.APP_VERSION,
          description=APP_NAME,
          long_description=APP_DESCRIPTION,
          author="Andrew Ziem",
          author_email="andrew@bleachbit.org",
          url=bleachbit.APP_URL,
          download_url="https://www.bleachbit.org/download",
          classifiers=[
              'Development Status :: 5 - Production/Stable',
              'Programming Language :: Python',
              'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
              'Operating System :: Microsoft :: Windows',
              'Operating System :: POSIX :: Linux',
          ],
          license='GPLv3+',
          # py_requires='>=3.8',
          # Ubuntu 20.04 LTS is EOL on April 2025, and it has Python 3.8.
          platforms='Linux and Windows, Python v3.8+, GTK v3.24+',
          packages=['bleachbit', 'bleachbit.markovify'],
          **args)


if __name__ == '__main__':
    if 2 == len(sys.argv) and sys.argv[1] == 'clean-dist':
        clean_dist_locale()
    else:
        run_setup()
