# BleachBit

BleachBit cleans files to free disk space and to maintain privacy.

## Installation instructions

### Native packages

[![Packaging status](https://repology.org/badge/tiny-repos/bleachbit.svg)](https://repology.org/project/bleachbit/versions)

#### Ubuntu-based distros

`sudo apt install bleachbit`

#### Arch-based distros

`sudo pacman -S bleachbit`

## Running from source

### Prerequisites

- Python 2
- Gtk 3

To run BleachBit without installation, unpack the tarball and then run these
commands:

    make -C po local # build translations
    python bleachbit.py

Then, review the preferences.

Then, select some options, and click Preview.  Review the files, toggle options accordingly, and click Delete.

For information regarding the command line interface, run:

     python bleachbit.py --help

## Links

* [BleachBit home 
page](https://www.bleachbit.org)
* [Support](https://www.bleachbit.org/help)
* [Documentation](https://docs.bleachbit.org)


## Licenses

BleachBit itself, including source code and cleaner definitions, is licensed under the [GNU General Public License version 3](COPYING), or at your option, any later version.

markovify is licensed under the [MIT License](https://github.com/jsvine/markovify/blob/master/LICENSE.txt).

### Development
* [BleachBit on AppVeyor](https://ci.appveyor.com/project/az0/bleachbit)  [![Build status](https://ci.appveyor.com/api/projects/status/7p8amofd7rv7n268?svg=true)](https://ci.appveyor.com/project/az0/bleachbit)
* [BleachBit on Travis CI](https://travis-ci.org/bleachbit/bleachbit)  [![Build Status](https://travis-ci.org/bleachbit/bleachbit.svg?branch=master)](https://travis-ci.org/bleachbit/bleachbit)
* [CleanerML Repository](https://github.com/az0/cleanerml)
* [BleachBit Miscellaneous Repository](https://github.com/bleachbit/bleachbit-misc)
* [Winapp2.ini Repository](https://github.com/bleachbit/winapp2.ini)
