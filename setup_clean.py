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


import os
import glob


"""
Clean the GTK+ locales shipped
"""


def supported_languages():
    langs = []
    for pathname in glob.glob('po/*.po'):
        basename = os.path.basename(pathname)
        langs.append(os.path.splitext(basename)[0])
    return langs


def clean_dist_locale():
    langs = supported_languages()
    basedir = 'dist\\share\\locale'
    for pathname in os.listdir(basedir):
        print "debug: GTK language = '%s'" % pathname
        if not pathname in langs:
            cmd = 'rd /s /q ' + os.path.join(basedir, pathname)
            print cmd
            os.system(cmd)

if __name__ == '__main__':
    clean_dist_locale()
