# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
License notices for the software that is in the macOS application bundle

The bundle contains libraries from Homebrew packages, most of them under
the LGPL, and Python packages. This module finds the Homebrew formula of
each file that was copied into the bundle, writes
THIRD-PARTY-NOTICES.txt, and copies the license files that the formulas
install. The licenses and the addresses of the source code are the ones
that Homebrew declares, so nothing is written from memory.
"""

# standard library
import email.parser
import glob
import json
import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)

LICENSE_PATTERNS = ('COPYING*', 'LICENSE*', 'LICENCE*', 'COPYRIGHT*')

# A file inside each icon theme, to find the formula that installed it.
ICON_THEMES = ('Adwaita', 'hicolor')


def formula_of(path, cellar):
    """Return the name of the Homebrew formula that installed a file

    Homebrew links its files into the prefix, so the real path of the
    file is inside the Cellar, in a directory named after the formula.
    Return None if the file is not from the Cellar.
    """
    real = os.path.realpath(path)
    cellar = os.path.realpath(cellar) + os.sep
    if real.startswith(cellar):
        return real[len(cellar):].split(os.sep)[0]
    return None


def dylib_sources(prefix, libdir):
    """Return where Homebrew has the libraries that are in libdir

    Some packages (openssl, sqlite) are keg-only: they are not linked
    into prefix/lib, only into prefix/opt/<formula>/lib.
    """
    sources = []
    for name in sorted(os.listdir(libdir)):
        if not name.endswith('.dylib'):
            continue
        candidates = [os.path.join(prefix, 'lib', name)]
        candidates.extend(sorted(glob.glob(
            os.path.join(prefix, 'opt', '*', 'lib', name))))
        sources.append(next((c for c in candidates if os.path.exists(c)),
                            candidates[0]))
    return sources


def mirrored_sources(bundle_dir, homebrew_dir, suffix=''):
    """Return the files in homebrew_dir that have the names in bundle_dir"""
    return [os.path.join(homebrew_dir, name)
            for name in sorted(os.listdir(bundle_dir))
            if name.endswith(suffix)]


def theme_sources(prefix):
    """Return a file of each icon theme in Homebrew"""
    return [os.path.join(prefix, 'share', 'icons', theme, 'index.theme')
            for theme in ICON_THEMES]


def formulas_of(paths, cellar):
    """Return the sorted names of the formulas that installed the files

    A file that has no formula is logged, because its license would be
    missing from the notices.
    """
    found = set()
    for path in paths:
        formula = formula_of(path, cellar) if os.path.exists(path) else None
        if formula:
            found.add(formula)
        else:
            logger.warning('no Homebrew formula found for %s', path)
    return sorted(found)


def license_files(directory):
    """Return the license files in the top directory of a package"""
    found = set()
    for pattern in LICENSE_PATTERNS:
        found.update(path for path in glob.glob(os.path.join(directory,
                                                             pattern))
                     if os.path.isfile(path))
    return sorted(found)


def formula_entries(formulas, prefix):
    """Return the license data of the formulas, from `brew info`"""
    output = subprocess.run(
        ['brew', 'info', '--json=v2'] + list(formulas), check=True,
        capture_output=True, text=True).stdout
    info = {item['name']: item for item in json.loads(output)['formulae']}
    entries = []
    for name in formulas:
        item = info.get(name, {})
        installed = item.get('installed') or [{}]
        stable = (item.get('urls') or {}).get('stable') or {}
        entries.append({
            'name': name,
            'version': installed[0].get('version'),
            'license': item.get('license'),
            'homepage': item.get('homepage'),
            'source': stable.get('url'),
            'files': license_files(os.path.join(prefix, 'opt', name)),
        })
    return entries


def python_packages(site_packages):
    """Return the name, version and license of the pip packages"""
    packages = []
    pattern = os.path.join(site_packages, '*.dist-info', 'METADATA')
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding='utf-8') as f:
            message = email.parser.Parser().parsestr(f.read(),
                                                     headersonly=True)
        text = message['License-Expression'] or message['License'] or ''
        first_line = text.strip().splitlines()[0][:80] if text.strip() else ''
        packages.append({'name': message['Name'],
                         'version': message['Version'],
                         'license': first_line or None})
    return packages


def render_notice(app_version, entries, packages):
    """Return the text of THIRD-PARTY-NOTICES.txt"""
    lines = [
        'BleachBit {} for macOS: third-party software'.format(app_version),
        '',
        'BleachBit is free software under the GNU General Public License,',
        'version 3 or later. See COPYING in this directory.',
        '',
        'This application also contains the software of the Homebrew',
        'packages and the Python packages listed below. The license and the',
        'address of the source code of each Homebrew package are those that',
        'Homebrew declares for it. The license files that the packages',
        'install are copied to licenses/<package>/ next to this file.',
        '',
        'Libraries under the LGPL are separate files in',
        'Contents/Frameworks/lib (typelibs, loaders and Python extensions',
        'are also separate files), so you can replace them with a modified',
        'version. The application has to be signed again after that, for',
        'example with: codesign --force -s - <file>',
        'The source code is at the address given as "Source".',
        '',
        '=== Homebrew packages ===',
    ]
    for entry in entries:
        lines.extend(['',
                      '{} {}'.format(entry['name'], entry['version'] or ''),
                      '  License:  {}'.format(entry['license'] or 'unknown'),
                      '  Homepage: {}'.format(entry['homepage'] or 'unknown'),
                      '  Source:   {}'.format(entry['source'] or 'unknown')])
        if entry['files']:
            names = ', '.join(os.path.basename(f) for f in entry['files'])
            lines.append('  License files: {}'.format(names))
        else:
            lines.append('  License files: Homebrew does not install them; '
                         'see the source')
    lines.extend(['', '=== Python packages (installed with pip) ===',
                  '', 'The license files are in the .dist-info directory of',
                  'each package, in the site-packages directory of the',
                  'bundled Python.'])
    for package in packages:
        lines.extend(['', '{} {}'.format(package['name'],
                                         package['version']),
                      '  License:  {}'.format(package['license']
                                              or 'see the license file')])
    return '\n'.join(lines) + '\n'


def write_notices(resources, app_version, entries, packages):
    """Write THIRD-PARTY-NOTICES.txt and copy the license files

    Return the path of the notices.
    """
    for entry in entries:
        if not entry['files']:
            continue
        destination = os.path.join(resources, 'licenses', entry['name'])
        os.makedirs(destination, exist_ok=True)
        for path in entry['files']:
            shutil.copy2(path, destination)
    notices = os.path.join(resources, 'THIRD-PARTY-NOTICES.txt')
    with open(notices, 'w', encoding='utf-8') as f:
        f.write(render_notice(app_version, entries, packages))
    return notices
