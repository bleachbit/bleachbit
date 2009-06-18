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


from bleachbit.globals import APP_VERSION
from distutils.core import setup
import sys
if sys.platform == 'win32':
    try:
        import py2exe
    except:
        print 'warning: py2exe not available'


data_files = []
if sys.platform == 'linux2':
    data_files.append(('/usr/share/applications', ['./bleachbit.desktop']))
    data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))

args = {}
if 'py2exe' in sys.argv:
    args['windows'] = [{
        'script' : 'bleachbit.py',
        'icon_resources' : [(1, 'bleachbit.ico')]
        }]
    args['options'] = {
        'py2exe' : {
            'packages' : 'encodings',
            'optimize' : 2, # extra optimization (like python -OO)
            'includes' : ['cairo', 'pango', 'pangocairo', 'atk', 'gobject'],
            'excludes' : ['_ssl', 'pyreadline', 'difflib', 'doctest',
                'optparse', 'pickle', 'calendar', 
                'ftplib', 'ssl', 'bleachbit.Unix'],
            'compressed' : True # create a compressed zipfile
            }
        }

print args

setup( name = 'bleachbit',
       version = APP_VERSION,
       description = "Free space and maintain privacy",
       long_description = "BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had. Supported applications include Firefox, Flash, Internet Explorer, Java, Opera, Safari, GNOME, and many others.",
       author = "Andrew Ziem",
       author_email = "ahz001@gmail.com",
       download_url = "http://bleachbit-project.appspot.com/download/",
       license = "GPLv3",
       url = "http://bleachbit-project.appspot.com",
       platforms = 'Linux and Windows with Python v2.4+ and PyGTK v2',
       packages = ['bleachbit'],
       **args)

