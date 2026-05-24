# BleachBit

BleachBit cleans files to free disk space and to maintain privacy.

This is a backport of BleachBit 6 to BleachBit 4 for Windows XP through Windows 8.1.
Support for non-Windows has been removed, and users of Windows 10 and newer
are encouraged to use the newer version of BleachBit.

## Running from source

To run BleachBit without installation, setup the Python environment:

- Run [windows/install_msys2.ps1](windows/install_msys2.ps1) to setup MSYS2 for make (optional)
- Install Python 3.4.4 32-bit.
- Install Python dependencies as shown in [appveyor.yml](appveyor.yml).

Then, run

```
# Build translations (optional).
make -C po local

# Start application.
# Adjust paths according to your system.
\python34\python.exe bleachbit.py
```

Then, review the preferences.

Then, select some options, and click Preview.  Review the files, toggle options accordingly, and click Delete.

For information regarding the command line interface, run:

```
\python34\python.exe bleachbit.py --help
```

Read more about [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html).

## Links

- [BleachBit home page](https://www.bleachbit.org)
- [Support](https://www.bleachbit.org/help)
- [Documentation](https://docs.bleachbit.org)

## Localization

Read [translation documentation](https://www.bleachbit.org/contribute/translate) or translate now in [Weblate](https://hosted.weblate.org/projects/bleachbit/), a web-based translation platform.

## Licenses

BleachBit itself, including source code and cleaner definitions, is licensed under the [GNU General Public License version 3](COPYING), or at your option, any later version.

markovify is licensed under the [MIT License](https://github.com/jsvine/markovify/blob/master/LICENSE.txt).

## Development

- [BleachBit on AppVeyor](https://ci.appveyor.com/project/az0/bleachbit)  Build status
- [CleanerML Repository](https://github.com/bleachbit/cleanerml)
- [BleachBit Miscellaneous Repository](https://github.com/bleachbit/bleachbit-misc)
- [Winapp2.ini Repository](https://github.com/bleachbit/winapp2.ini)

