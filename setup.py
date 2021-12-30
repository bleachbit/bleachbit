#!/usr/bin/env python
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
Build BleachBit tarballs and exe
"""

import glob
import os
import sys
import tempfile
from setuptools import setup

if sys.platform == 'win32':
    # workaround for
    # Error: Namespace packages not yet supported: Skipping package 'pywintypes'
    import importlib
    for m in ('pywintypes', 'pythoncom'):
        l = importlib.find_loader(m, None)
        __import__(m)
        sys.modules[m].__loader__ = l

    try:
        import py2exe
    except ImportError:
        print('warning: py2exe not available')

import bleachbit
import bleachbit.General
import bleachbit.FileUtilities

APP_NAME = "BleachBit - Free space and maintain privacy"
APP_DESCRIPTION = "BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had. Supported applications include Edge, Firefox, Google Chrome, VLC, and many others."

#
# begin win32com.shell workaround for py2exe
# copied from http://spambayes.svn.sourceforge.net/viewvc/spambayes/trunk/spambayes/windows/py2exe/setup_all.py?revision=3245&content-type=text%2Fplain
# under Python license compatible with GPL
#

# ModuleFinder can't handle runtime changes to __path__, but win32com uses them,
# particularly for people who build from sources.  Hook this in.
try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell", "win32com.mapi"]:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass

#
# end win32com.shell workaround for py2exe
#


data_files = []
if sys.platform.startswith('linux'):
    data_files.append(('/usr/share/applications', ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))
elif sys.platform[:6] == 'netbsd':
    data_files.append(('/usr/pkg/share/applications', ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/pkg/share/pixmaps/', ['./bleachbit.png']))
elif sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
    data_files.append(
        ('/usr/local/share/applications', ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/local/share/pixmaps/', ['./bleachbit.png']))


args = {}
if 'py2exe' in sys.argv:
    args['windows'] = [{
        'script': 'bleachbit.py',
        'product_name': APP_NAME,
        'description': APP_DESCRIPTION,
        'version': bleachbit.APP_VERSION,
        'icon_resources': [(1, 'windows/bleachbit.ico')]
    }]
    args['console'] = [{
        'script': 'bleachbit_console.py',
        'product_name': APP_NAME,
        'description': APP_DESCRIPTION,
        'version': bleachbit.APP_VERSION,
        'icon_resources': [(1, 'windows/bleachbit.ico')]
    }]
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
    """Recompile gettext .mo file"""

    if not bleachbit.FileUtilities.exe_exists('msgunfmt') and not bleachbit.FileUtilities.exe_exists('msgunfmt.exe'):
        print('warning: msgunfmt missing: skipping recompile')
        return

    mo_pathname = os.path.normpath('%s/LC_MESSAGES/%s.mo' % (langdir, app))
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
              os.path.normpath('windows/%s.pot' % app),
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
    langs = supported_languages()
    basedir = os.path.normpath('dist/share/locale')
    for langid in sorted(os.listdir(basedir)):
        langdir = os.path.join(basedir, langid)
        if langid in langs:
            print("recompiling supported GTK language = %s" % langid)
            # reduce the size of the .mo file
            recompile_mo(langdir, 'gtk30', langid, tmpd)
        else:
            print("removing unsupported GTK language = %s" % langid)
            # remove language supported by GTK+ but not by BleachBit
            cmd = 'rd /s /q ' + langdir
            print(cmd)
            os.system(cmd)
    os.rmdir(tmpd)


def run_setup():
    setup(name='bleachbit',
          version=bleachbit.APP_VERSION,
          description=APP_NAME,
          long_description=APP_DESCRIPTION,
          author="Andrew Ziem",
          author_email="andrew@bleachbit.org",
          download_url="https://www.bleachbit.org/download",
          license="GPLv3",
          url=bleachbit.APP_URL,
          platforms='Linux and Windows; Python v2.6 and 2.7; GTK v3.12+',
          packages=['bleachbit', 'bleachbit.markovify'],
          **args)


if __name__ == '__main__':
    if 2 == len(sys.argv) and sys.argv[1] == 'clean-dist':
        clean_dist_locale()
    else:
        run_setup()
