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



from distutils.core import setup

data_files = []
data_files.append(('/usr/share/applications', ['./bleachbit.desktop']))
data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))

setup(name='bleachbit',
      version='0.4.1',
      description='Free space and maintain privacy',
      long_description="BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had. Supported applications include Firefox, Opera, Epihany, Adobe Flash, Java, GNOME, and more.",
      author='Andrew Ziem',
      author_email='ahz001@gmail.com',
      license='GPLv3',
      url='http://bleachbit.sourceforge.net',
      platforms='Linux with Python v2.4+ and PyGTK v2',
      data_files = data_files,
      packages = ['bleachbit'],
     )

