#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Build BleachBit tarballs
"""

# standard library
import glob
import os

# local import
import bleachbit


APP_DESCRIPTION = "BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had."

data_files = []
if bleachbit.IS_LINUX:
    data_files.append(('/usr/share/applications',
                      ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/share/pixmaps/', ['./bleachbit.png']))
elif bleachbit.IS_NETBSD:
    data_files.append(('/usr/pkg/share/applications',
                      ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/pkg/share/pixmaps/', ['./bleachbit.png']))
elif bleachbit.IS_BSD:
    data_files.append(
        ('/usr/local/share/applications', ['./org.bleachbit.BleachBit.desktop']))
    data_files.append(('/usr/local/share/pixmaps/', ['./bleachbit.png']))


def run_setup(args=None):
    """Run setup from setuptools"""
    if args is None:
        args = {}
    # pylint: disable=import-outside-toplevel
    from setuptools import setup
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
              'Operating System :: Microsoft :: Windows',
              'Operating System :: POSIX :: Linux',
          ],
          license='GPL-3.0-or-later',
          # py_requires='>=3.8',
          # Ubuntu 20.04 LTS is EOL on April 2025, and it has Python 3.8.
          platforms='Linux and Windows, Python v3.8+, GTK v3.24+',
          packages=['bleachbit', 'bleachbit.markovify'],
          **args)


def supported_languages():
    """Return list of supported languages by scanning ./po/

    This function is used by:
    * windows/setup.py
    * bleachbit-misc/extract_desktop.py
    """
    langs = []
    for pathname in glob.glob('po/*.po'):
        basename = os.path.basename(pathname)
        langs.append(os.path.splitext(basename)[0])
    return sorted(langs)


if __name__ == '__main__':
    run_setup()
