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

# standard library
import sys

# third-party
from setuptools import setup

# local import
import bleachbit
import bleachbit.General
import bleachbit.FileUtilities


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


def run_setup(args={}):
    setup(name='bleachbit',
          version=bleachbit.APP_VERSION,
          description=bleachbit.APP_NAME,
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
    run_setup()
