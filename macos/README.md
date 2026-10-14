# Building BleachBit for macOS (experimental)

This directory builds an application bundle, `BleachBit.app`, and
optionally a `.dmg` that contains it, from the Homebrew packages that
are installed on the build machine.

This is experimental. The result is **not signed with a Developer ID and
is not notarized**, so Gatekeeper treats it as an application from an
unidentified developer. Only Apple Silicon is supported.

## Requirements

Install the Homebrew packages:

```
brew install python@3.12 gtk+3 librsvg gdk-pixbuf adwaita-icon-theme \
    gobject-introspection pkgconf cairo gettext
```

The script also needs a Python that can import `bleachbit` and `setup`
(which needs `setuptools`). It does not need the GTK packages: the
bundled Python gets its own copy of `pycairo` and `PyGObject`, built
against the Homebrew libraries (see `requirements.txt`).

## Build

Run it from the top directory of the source tree, not from this
directory:

```
python3 -m macos.build_dmg
```

Options:

* `--output DIR`: where to write the result (default: `macos/build`,
  which is ignored by git)
* `--no-dmg`: build only `BleachBit.app`
* `--strict`: fail if any file still contains the Homebrew prefix or
  `/Users/` (by default these are warnings)

For example, to build only the application in a temporary directory:

```
python3 -m macos.build_dmg --output /tmp/bleachbit-macos --no-dmg
```

At the end the script checks the bundle and reports problems: libraries
that still depend on a Homebrew path, missing libraries, build paths in
the run paths, bytecode caches, and a missing license notice. A problem
makes the build fail.

## What the build does

* `relocate.py` copies the Homebrew libraries into
  `Contents/Frameworks`, points them to each other with relative paths,
  removes the run paths that point to the build machine, and signs every
  file with an ad hoc signature.
* `build_dmg.py` copies the Python framework, installs the Python
  packages, the typelibs, the GLib schemas, the icon themes and the
  translations, and writes the launcher and `Info.plist`.
* `licenses.py` writes `Contents/Resources/THIRD-PARTY-NOTICES.txt` and
  copies the license files of the Homebrew packages to
  `Contents/Resources/licenses`. The licenses and the addresses of the
  source code are the ones that Homebrew declares.

The libraries under the LGPL are separate files, so they can be replaced
by a modified version. The application has to be signed again after that,
for example with `codesign --force -s - <file>`.

## Limitations

* The libraries are built for the macOS version of the build machine, so
  the result runs on that version of macOS or newer.
* The application is not notarized. Because of that, the first launch
  needs the usual steps for an application from an unidentified
  developer.
* The bundle has to be built again after `brew upgrade`, because it
  contains the versions that were installed at the time.

## Tests

`tests/TestMacosRelocate.py`, `tests/TestMacosBuild.py` and
`tests/TestMacosLicenses.py` cover the parts that do not need Homebrew.
