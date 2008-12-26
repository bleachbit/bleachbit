#!/usr/bin/env python

from distutils.core import setup

data_files = []
data_files.append(('/usr/share/applications', ['./bleachbit.desktop']))
data_files.append(('/usr/bin', ['bin/bleachbit']))

setup(name='bleachbit',
      version='0.2.0',
      description='Free space and maintain privacy',
      long_description="BleachBit frees space and maintains privacy by quickly wiping files you don't need and didn't know you had. Supported applications include Firefox, Opera, Epihany, Adobe Flash, Java, Gnome, and more.",
      author='Andrew Ziem',
      author_email='ahz001@gmail.com',
      license='GPLv3',
      url='http://bleachbit.sourceforge.net',
      platforms='Linux with Python v2 and PyGTK v2',
      data_files = data_files,
      packages = ['bleachbit'],
     )

