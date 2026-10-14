# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
macOS build and packaging (experimental, unsigned)

Build a self-contained BleachBit.app from the Homebrew packages that are
installed on the build machine, and optionally a .dmg that contains it.
Only Apple Silicon is supported.

Requirements on the build machine (Homebrew): python@3.12, gtk+3, librsvg,
gdk-pixbuf, adwaita-icon-theme, gobject-introspection, pkg-config, cairo,
gettext, and a Python that can import bleachbit and setup (setuptools).

Examples of invocation (from parent directory):

```
python3 -m macos.build_dmg
python3 -m macos.build_dmg --output /tmp/bleachbit-macos --no-dmg
python3 -m macos.build_dmg --strict
```

The result is not signed with a Developer ID and is not notarized. Because
the libraries are built for the macOS version of the build machine, the
result runs on that version of macOS or newer.
"""

# standard library
import argparse
import collections
import logging
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile

# local import
import bleachbit
from setup import supported_languages
from macos.relocate import Relocator, macho_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Prevent propagation to root logger to avoid duplicate messages
logger.propagate = False

# show the summary of the relocation, which has its own logger
relocate_logger = logging.getLogger('macos.relocate')
relocate_logger.setLevel(logging.INFO)
relocate_logger.addHandler(ch)
relocate_logger.propagate = False

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON_FORMULA = 'python@3.12'
PYTHON_VERSION = '3.12'

# Parts of the Python framework that BleachBit does not need.
PRUNE_FROM_STDLIB = ('test', 'idlelib', 'tkinter', 'ensurepip',
                     'turtledemo', 'lib2to3', 'config-3.12-darwin')

# Keys of the Python.app Info.plist that describe Python, not BleachBit.
PYTHON_APP_DELETE_KEYS = (
    'CFBundleLongVersionString', 'CFBundleGetInfoString',
    'CFBundleSignature', 'CFBundleDocumentTypes', 'CFBundleHelpBookName',
    'CFBundleHelpBookFolder', 'CFBundleHelpTOCFile')

Bundle = collections.namedtuple('Bundle', [
    'app', 'contents', 'macos', 'frameworks', 'lib', 'resources', 'share',
    'locale', 'python_framework', 'python_dir', 'site_packages',
    'python_app'])


def bundle_paths(app):
    """Return the locations inside the .app"""
    contents = os.path.join(app, 'Contents')
    frameworks = os.path.join(contents, 'Frameworks')
    framework = os.path.join(frameworks, 'Python.framework')
    python_dir = os.path.join(framework, 'Versions', PYTHON_VERSION)
    return Bundle(
        app=app,
        contents=contents,
        macos=os.path.join(contents, 'MacOS'),
        frameworks=frameworks,
        lib=os.path.join(frameworks, 'lib'),
        resources=os.path.join(contents, 'Resources'),
        share=os.path.join(contents, 'Resources', 'share'),
        locale=os.path.join(contents, 'locale'),
        python_framework=framework,
        python_dir=python_dir,
        site_packages=os.path.join(
            python_dir, 'lib', 'python' + PYTHON_VERSION, 'site-packages'),
        python_app=os.path.join(python_dir, 'Resources', 'Python.app'))


def run(*args, **kwargs):
    """Run a command, show its output, and raise an exception on failure"""
    logger.debug('running %s', ' '.join(args))
    subprocess.run(args, check=True, **kwargs)


def make_writable(path):
    """Add the owner write permission to everything below path"""
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            full = os.path.join(root, name)
            if not os.path.islink(full):
                os.chmod(full, os.stat(full).st_mode | 0o200)


def brew_prefix():
    """Return the Homebrew prefix"""
    return subprocess.check_output(['brew', '--prefix'], text=True).strip()


def render_template(text, **values):
    """Replace @NAME@ in a template with the values"""
    for key, value in values.items():
        text = text.replace('@{}@'.format(key.upper()), value)
    return text


def customize_info_plist(info, version):
    """Return the Info.plist of the bundled Python.app, now named BleachBit

    macOS shows the name and icon of the nested Python.app in the menu bar
    and the Dock, because that is the process that runs.
    """
    info = dict(info)
    info.update({
        'CFBundleName': 'BleachBit',
        'CFBundleDisplayName': 'BleachBit',
        'CFBundleIdentifier': 'org.bleachbit.BleachBit',
        'CFBundleIconFile': 'BleachBit.icns',
        'CFBundleVersion': version,
        'CFBundleShortVersionString': version,
        'NSHumanReadableCopyright': 'Copyright 2008-2026 Andrew Ziem',
    })
    for key in PYTHON_APP_DELETE_KEYS:
        info.pop(key, None)
    return info


def loaders_cache_template(output, libdir):
    """Make the gdk-pixbuf loaders cache independent of the location

    libdir is replaced with the placeholder @LIB@, which launcher.sh
    replaces with the real location each time the application starts.
    """
    return output.replace(libdir, '@LIB@')


def find_files_containing(root, needles):
    """Return {needle: [relative paths]} of files that contain the needle"""
    found = {needle: [] for needle in needles}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            with open(path, 'rb') as f:
                data = f.read()
            for needle in needles:
                if needle.encode() in data:
                    found[needle].append(os.path.relpath(path, root))
    return found


def find_bytecode(root):
    """Return the relative paths of the __pycache__ directories

    The bytecode contains the path where it was compiled, so it must not
    be in the bundle. Running the bundled Python without -B creates it.
    """
    found = []
    for dirpath, dirs, _files in os.walk(root):
        if '__pycache__' in dirs:
            found.append(os.path.relpath(
                os.path.join(dirpath, '__pycache__'), root))
            dirs.remove('__pycache__')
    return sorted(found)


def requirement_lines():
    """Return the Python packages to install in the bundle

    setuptools is only needed to build, not to run.
    """
    lines = []
    for path in ('requirements.txt', os.path.join(HERE, 'requirements.txt')):
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line and not line.lower().startswith('setuptools'):
                    lines.append(line)
    return lines


def copy_python_framework(prefix, b):
    """Copy and slim down the Python framework of Homebrew"""
    src = os.path.realpath(os.path.join(
        prefix, 'opt', PYTHON_FORMULA, 'Frameworks', 'Python.framework'))
    os.makedirs(b.frameworks)
    run('ditto', src, b.python_framework)
    make_writable(b.contents)
    stdlib = os.path.join(b.python_dir, 'lib', 'python' + PYTHON_VERSION)
    for name in PRUNE_FROM_STDLIB:
        shutil.rmtree(os.path.join(stdlib, name), ignore_errors=True)
    shutil.rmtree(os.path.join(b.python_dir, 'include'), ignore_errors=True)
    shutil.rmtree(os.path.join(b.python_dir, 'lib', 'pkgconfig'),
                  ignore_errors=True)
    dynload = os.path.join(stdlib, 'lib-dynload')
    for name in os.listdir(dynload):
        if name.startswith('_tkinter'):
            os.remove(os.path.join(dynload, name))
    bindir = os.path.join(b.python_dir, 'bin')
    for name in os.listdir(bindir):
        path = os.path.join(bindir, name)
        if name != 'python' + PYTHON_VERSION and not os.path.isdir(path):
            os.remove(path)
    for root, dirs, _files in os.walk(b.python_framework):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
            dirs.remove('__pycache__')
    sitecustomize = os.path.join(stdlib, 'sitecustomize.py')
    if os.path.exists(sitecustomize):
        os.remove(sitecustomize)
    # ctypes.util looks in the Homebrew directory, which may not exist.
    dyld = os.path.join(stdlib, 'ctypes', 'macholib', 'dyld.py')
    with open(dyld, encoding='utf-8') as f:
        text = f.read()
    with open(dyld, 'w', encoding='utf-8') as f:
        f.write(text.replace(prefix, '/usr/local'))
    # Homebrew points site-packages to a directory outside the framework.
    if os.path.islink(b.site_packages):
        os.unlink(b.site_packages)
    os.makedirs(b.site_packages, exist_ok=True)


def install_python_packages(prefix, b):
    """Install the Python dependencies into the bundled Python"""
    python = os.path.join(prefix, 'opt', PYTHON_FORMULA, 'bin',
                          'python' + PYTHON_VERSION)
    env = dict(os.environ, PATH=os.path.join(prefix, 'bin') + os.pathsep
               + os.environ.get('PATH', ''))
    with tempfile.TemporaryDirectory() as tmp:
        reqs = os.path.join(tmp, 'requirements.txt')
        with open(reqs, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirement_lines()) + '\n')
        # --target avoids the protection of the Homebrew Python
        run(python, '-m', 'pip', 'install', '--disable-pip-version-check',
            '--no-compile', '--target', b.site_packages, '-r', reqs,
            env=env)
    shutil.rmtree(os.path.join(b.site_packages, 'bin'), ignore_errors=True)


def copy_typelibs(prefix, b):
    """Copy the typelibs and the libraries they load by name

    Typelibs name libraries such as libgtk-3.0.dylib, which GObject
    Introspection opens at run time, so the relocation does not find them.
    """
    dst = os.path.join(b.frameworks, 'girepository-1.0')
    shutil.copytree(os.path.join(prefix, 'lib', 'girepository-1.0'), dst)
    make_writable(dst)
    names = set()
    for typelib in os.listdir(dst):
        with open(os.path.join(dst, typelib), 'rb') as f:
            names.update(re.findall(rb'lib[A-Za-z0-9_.+-]+\.dylib',
                                    f.read()))
    os.makedirs(b.lib, exist_ok=True)
    for name in sorted(n.decode() for n in names):
        src = os.path.join(prefix, 'lib', name)
        if os.path.exists(src):
            target = os.path.join(b.lib, name)
            shutil.copy2(os.path.realpath(src), target)
            os.chmod(target, 0o755)
        else:
            logger.warning('typelib names %s, which is not in %s/lib',
                           name, prefix)


def copy_runtime_data(prefix, b):
    """Copy gdk-pixbuf loaders, icon themes, and GLib schemas"""
    pixbuf = os.path.join(b.lib, 'gdk-pixbuf-2.0')
    shutil.copytree(os.path.join(prefix, 'lib', 'gdk-pixbuf-2.0'), pixbuf)
    cache = os.path.join(pixbuf, '2.10.0', 'loaders.cache')
    if os.path.exists(cache):
        os.remove(cache)
    for theme in ('Adwaita', 'hicolor'):
        shutil.copytree(os.path.join(prefix, 'share', 'icons', theme),
                        os.path.join(b.share, 'icons', theme))
    schemas = os.path.join(b.share, 'glib-2.0', 'schemas')
    shutil.copytree(os.path.join(prefix, 'share', 'glib-2.0', 'schemas'),
                    schemas)
    make_writable(b.contents)
    run(os.path.join(prefix, 'bin', 'glib-compile-schemas'), schemas)


def copy_bleachbit(b):
    """Copy BleachBit from the working directory (the repository root)"""
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    shutil.copytree('bleachbit', os.path.join(b.resources, 'bleachbit'),
                    ignore=ignore)
    shutil.copytree('cleaners', os.path.join(b.resources, 'cleaners'),
                    ignore=shutil.ignore_patterns('__pycache__', 'Makefile'))
    for name in ('bleachbit.py', 'COPYING'):
        shutil.copy2(name, b.resources)
    os.makedirs(b.share, exist_ok=True)
    for name in ('app-menu.ui', 'protected_path.xml'):
        shutil.copy2(os.path.join('share', name), b.share)


def compile_translations(prefix, b):
    """Compile the .po files. Return the list of languages."""
    msgfmt = shutil.which('msgfmt') or os.path.join(
        prefix, 'opt', 'gettext', 'bin', 'msgfmt')
    languages = []
    for lang in supported_languages():
        out_dir = os.path.join(b.locale, lang, 'LC_MESSAGES')
        os.makedirs(out_dir)
        try:
            run(msgfmt, '-o', os.path.join(out_dir, 'bleachbit.mo'),
                os.path.join('po', lang + '.po'), stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            logger.warning('msgfmt failed for %s', lang)
            shutil.rmtree(os.path.join(b.locale, lang))
        else:
            languages.append(lang)
    return languages


def make_icon(b):
    """Make BleachBit.icns for the app and for the nested Python.app"""
    icns = os.path.join(b.resources, 'BleachBit.icns')
    with tempfile.TemporaryDirectory() as tmp:
        iconset = os.path.join(tmp, 'BleachBit.iconset')
        os.makedirs(iconset)
        for size in (16, 32, 128, 256):
            for scale, suffix in ((1, ''), (2, '@2x')):
                run('sips', '-z', str(size * scale), str(size * scale),
                    'bleachbit.png', '--out',
                    os.path.join(iconset, 'icon_{0}x{0}{1}.png'.format(
                        size, suffix)), stdout=subprocess.DEVNULL)
        run('iconutil', '-c', 'icns', iconset, '-o', icns)
    return icns


def set_python_app_identity(b, version, icns):
    """Make the nested Python.app say BleachBit and use its icon"""
    resources = os.path.join(b.python_app, 'Contents', 'Resources')
    for name in os.listdir(resources):
        if name.endswith('.icns'):
            os.remove(os.path.join(resources, name))
    shutil.copy2(icns, resources)
    plist = os.path.join(b.python_app, 'Contents', 'Info.plist')
    with open(plist, 'rb') as f:
        info = plistlib.load(f)
    with open(plist, 'wb') as f:
        plistlib.dump(customize_info_plist(info, version), f)


def copy_gtk_translations(prefix, b, languages):
    """Copy the GTK catalogs (gettext domain gtk30) for the app menu

    On macOS, GTK looks them up in Resources/share/locale of the main
    bundle, which is the nested Python.app, not the outer BleachBit.app.
    Without them the menu (About, Preferences, Hide, Quit) is in English.
    """
    src_root = os.path.join(prefix, 'opt', 'gtk+3', 'share', 'locale')
    copied = 0
    for lang in languages:
        src = os.path.join(src_root, lang, 'LC_MESSAGES', 'gtk30.mo')
        if not os.path.exists(src):
            continue
        dst = os.path.join(b.python_app, 'Contents', 'Resources', 'share',
                           'locale', lang, 'LC_MESSAGES')
        os.makedirs(dst)
        shutil.copy2(src, dst)
        copied += 1
    logger.info('gtk30 catalogs copied: %d of %d languages', copied,
                len(languages))


def write_loaders_cache(prefix, b):
    """Write the template of the gdk-pixbuf loaders cache"""
    libdir = os.path.realpath(b.lib)
    moduledir = os.path.join(libdir, 'gdk-pixbuf-2.0', '2.10.0', 'loaders')
    output = subprocess.run(
        [os.path.join(prefix, 'bin', 'gdk-pixbuf-query-loaders')],
        check=True, capture_output=True, text=True,
        env=dict(os.environ, GDK_PIXBUF_MODULEDIR=moduledir)).stdout
    template = loaders_cache_template(output, libdir)
    with open(os.path.join(b.share, 'gdk-pixbuf-loaders.cache.in'), 'w',
              encoding='utf-8') as f:
        f.write(template)
    logger.info('loaders in cache: %d, svg: %d',
                template.count('\n"@LIB@'), template.count('svg'))


def write_launcher_and_plist(b, version):
    """Install the launcher and the Info.plist"""
    os.makedirs(b.macos, exist_ok=True)
    launcher = os.path.join(b.macos, 'BleachBit')
    shutil.copy2(os.path.join(HERE, 'launcher.sh'), launcher)
    os.chmod(launcher, 0o755)
    with open(os.path.join(HERE, 'Info.plist.in'), encoding='utf-8') as f:
        text = f.read()
    with open(os.path.join(b.contents, 'Info.plist'), 'w',
              encoding='utf-8') as f:
        f.write(render_template(text, version=version))


def smoke_tests(b):
    """Run the bundled Python and the launcher. Return a list of errors."""
    errors = []
    python = os.path.join(b.python_dir, 'bin', 'python' + PYTHON_VERSION)
    # A bare environment shows a dependency on DYLD_*, PATH or the like.
    result = subprocess.run(
        [python, '-I', '-B', '-c',
         'import ssl, _hashlib, sqlite3, ctypes'],
        env={}, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append('import ssl, _hashlib, ... with an empty environment '
                      'failed: ' + result.stderr.strip())
    env = {'HOME': os.path.expanduser('~'), 'PATH': '/usr/bin:/bin'}
    result = subprocess.run(
        [os.path.join(b.macos, 'BleachBit'), '--list-cleaners'],
        env=env, capture_output=True, text=True, check=False)
    count = len(result.stdout.splitlines())
    if result.returncode or count < 50:
        errors.append('the launcher did not list cleaners (rc={}, {} '
                      'lines): {}'.format(result.returncode, count,
                                          result.stderr.strip()[-300:]))
    else:
        logger.info('launcher lists %d cleaners', count)
    return errors


def verify(b, relocator, prefix, strict):
    """Check that the bundle is self-contained. Return the errors."""
    errors = relocator.problems()
    errors.extend(smoke_tests(b))
    for path in find_bytecode(b.app):
        errors.append('bytecode cache in the bundle: ' + path)
    found = find_files_containing(b.app, [prefix, '/Users/', b.app])
    # The path of the build is never wanted, and it is ours to avoid.
    for path in found.pop(b.app):
        errors.append('the build path {} is in {}'.format(b.app, path))
    for needle, paths in found.items():
        if strict:
            errors.extend('the text {} is in {}'.format(needle, path)
                          for path in paths)
        elif paths:
            logger.warning('%d files contain the text %s, for example %s '
                           '(--strict makes this an error)', len(paths),
                           needle, ', '.join(paths[:2]))
    return errors


def make_dmg(b, output, version):
    """Create the disk image. Return its path."""
    dmg = os.path.join(output, 'BleachBit-{}-macOS-arm64-unsigned.dmg'.format(
        version))
    stage = os.path.join(output, 'dmg-root')
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    run('ditto', b.app, os.path.join(stage, 'BleachBit.app'))
    os.symlink('/Applications', os.path.join(stage, 'Applications'))
    if os.path.exists(dmg):
        os.remove(dmg)
    run('hdiutil', 'create', '-volname', 'BleachBit', '-srcfolder', stage,
        '-format', 'UDZO', dmg)
    shutil.rmtree(stage)
    return dmg


def build(output, make_image, strict):
    """Build the application and optionally the disk image"""
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        sys.exit('This script needs macOS on Apple Silicon.')
    prefix = os.path.realpath(brew_prefix())
    version = bleachbit.APP_VERSION
    output = os.path.abspath(output)
    b = bundle_paths(os.path.join(output, 'BleachBit.app'))
    shutil.rmtree(b.app, ignore_errors=True)
    os.makedirs(b.app)
    logger.info('building BleachBit %s with Homebrew at %s', version, prefix)

    copy_python_framework(prefix, b)
    install_python_packages(prefix, b)
    copy_typelibs(prefix, b)
    copy_runtime_data(prefix, b)
    copy_bleachbit(b)
    languages = compile_translations(prefix, b)

    relocator = Relocator(b.app, prefix, PYTHON_FORMULA)
    relocator.relocate()

    # These come after relocation, which signs the files it changes.
    set_python_app_identity(b, version, make_icon(b))
    copy_gtk_translations(prefix, b, languages)
    run('codesign', '--force', '-s', '-', b.python_app)
    write_loaders_cache(prefix, b)
    write_launcher_and_plist(b, version)

    errors = verify(b, relocator, prefix, strict)
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit('the bundle is not self-contained ({} problems)'.format(
            len(errors)))
    logger.info('%d Mach-O files; application: %s',
                len(macho_files(b.app)), b.app)
    if make_image:
        logger.info('disk image: %s', make_dmg(b, output, version))


def main(argv=None):
    """Command line entry point"""
    parser = argparse.ArgumentParser(
        description=__doc__.split('\n\n', maxsplit=1)[0])
    parser.add_argument('--output', default=os.path.join('macos', 'build'),
                        help='directory for the result (default: %(default)s)')
    parser.add_argument('--no-dmg', action='store_true',
                        help='build only BleachBit.app')
    parser.add_argument('--strict', action='store_true',
                        help='fail if a file contains the Homebrew prefix '
                        'or /Users/')
    args = parser.parse_args(argv)
    build(args.output, not args.no_dmg, args.strict)


if __name__ == '__main__':
    main()
