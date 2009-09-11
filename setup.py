#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



import bleachbit.Common
import bleachbit.General
import bleachbit.FileUtilities
import glob
import os
import sys
import tempfile
from distutils.core import setup
if sys.platform == 'win32':
    try:
        import py2exe
    except ImportError:
        print 'warning: py2exe not available'


##
## begin win32com.shell workaround for py2exe
## copied from http://spambayes.svn.sourceforge.net/viewvc/spambayes/trunk/spambayes/windows/py2exe/setup_all.py?revision=3245&content-type=text%2Fplain
## under Python license compatible with GPL
##

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

###
### end win32com.shell workaround for py2exe
###



data_files = []
if sys.platform == 'linux2':
    data_files.append(('/usr/share/applications', ['./bleachbit.desktop']))
    data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))
if sys.platform >= 'netbsd5':
    data_files.append(('/usr/pkg/share/applications',['./bleachbit.desktop']))
    data_files.append(('/usr/pkg/share/pixmaps/',['./bleachbit.png']))


args = {}
if 'py2exe' in sys.argv:
    args['windows'] = [{
        'script' : 'bleachbit.py',
        'icon_resources' : [(1, 'windows/bleachbit.ico')]
        }]
    args['console'] = [{
        'script' : 'bleachbit_console.py',
        'icon_resources' : [(1, 'windows/bleachbit.ico')]
        }]
    args['options'] = {
        'py2exe' : {
            'packages' : 'encodings',
            'optimize' : 2, # extra optimization (like python -OO)
            'includes' : ['cairo', 'pango', 'pangocairo', 'atk', 'gobject'],
            'excludes' : ['_ssl', 'pyreadline', 'difflib', 'doctest',
                'pickle', 'calendar', 'ftplib', 'ssl', 'bleachbit.Unix'],
            'compressed' : True # create a compressed zipfile
            }
        }


def recompile_mo(langdir, app, langid, dst):
    """Recompile gettext .mo file"""

    if not bleachbit.FileUtilities.exe_exists('msgunfmt'):
        print 'warning: msgunfmt missing: skipping recompile'
        return

    mo_pathname = os.path.normpath('%s/LC_MESSAGES/%s.mo' % (langdir, app))
    if not os.path.exists(mo_pathname):
        print 'info: does not exist: %s' % mo_pathname
        return

    # decompile .mo to .po
    po = os.path.join(dst, langid + '.po')
    args = ['msgunfmt', '-o', po,
        mo_pathname ]
    ret = bleachbit.General.run_external(args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # shrink .po
    po2 = os.path.join(dst, langid + '.po2')
    args = ['msgmerge', '--no-fuzzy-matching', po,
        os.path.normpath('windows/%s.pot' % app),
        '-o', po2 ]
    ret = bleachbit.General.run_external(args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # compile smaller .po to smaller .mo
    args = ['msgfmt', po2, '-o', mo_pathname ]
    ret = bleachbit.General.run_external(args)
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
        print "debug: GTK language = '%s'" % langid
        langdir = os.path.join(basedir, langid)
        if langid in langs:
            # reduce the size of the .mo file
            recompile_mo(langdir, 'gtk20', langid, tmpd)
        else:
            # remove language supported by GTK+ but not by BleachBit
            cmd = 'rd /s /q ' + langdir
            print cmd
            os.system(cmd)
    os.rmdir(tmpd)


if 2 == len(sys.argv) and sys.argv[1] == 'clean-dist':
    clean_dist_locale()
    sys.exit(0)

setup( name = 'bleachbit',
       version = bleachbit.Common.APP_VERSION,
       description = "Free space and maintain privacy",
       long_description = "BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had. Supported applications include Firefox, Flash, Internet Explorer, Java, Opera, Safari, GNOME, and many others.",
       author = "Andrew Ziem",
       author_email = "ahz001@gmail.com",
       download_url = "http://bleachbit.sourceforge.net/download",
       license = "GPLv3",
       url = bleachbit.Common.APP_URL,
       platforms = 'Linux and Windows with Python v2.4+ and PyGTK v2',
       packages = ['bleachbit'],
       **args)

