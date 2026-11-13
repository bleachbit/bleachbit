# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Make a macOS application bundle self-contained

Homebrew libraries are linked with absolute paths such as
/opt/homebrew/opt/glib/lib/libglib-2.0.0.dylib. This module copies those
libraries into the bundle, rewrites every reference to a path relative to
the file that uses it (@loader_path), removes run paths that point to the
build machine, and signs every Mach-O file ad hoc because changing the load
commands invalidates the existing signatures.

The functions that parse the output of otool do not run anything, so they
can be tested on any operating system.
"""

# standard library
import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)

# 64-bit Mach-O (little endian) and fat (universal) binaries
MACHO_MAGIC = (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe')

# Dependencies that are valid on any Mac, or are relative to the bundle.
ALLOWED_PREFIXES = ('/usr/lib/', '/System/', '@loader_path/',
                    '@executable_path/')


def run(*args):
    """Run a command and return its standard output"""
    return subprocess.run(args, check=True, capture_output=True,
                          text=True).stdout


def parse_otool_dependencies(output, own_ids=()):
    """Return the libraries named in the output of `otool -L`

    otool prints the file name first. For a universal binary it prints one
    header line per architecture, such as `file (architecture arm64):`.
    Every such header ends with a colon and is not a dependency.

    own_ids are the install names of the file itself (see
    parse_otool_ids), which otool also lists among the dependencies.
    """
    deps = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.endswith(':'):
            continue
        dep = line.split(' (')[0]
        if dep not in own_ids:
            deps.append(dep)
    return deps


def parse_otool_ids(output):
    """Return the install names in the output of `otool -D`"""
    ids = set()
    for line in output.splitlines():
        line = line.strip()
        if line and not line.endswith(':'):
            ids.add(line)
    return ids


def parse_otool_rpaths(output):
    """Return the run paths in the output of `otool -l`"""
    lines = output.splitlines()
    found = []
    for i, line in enumerate(lines):
        if line.strip() != 'cmd LC_RPATH':
            continue
        for following in lines[i + 1:i + 4]:
            following = following.strip()
            if following.startswith('path '):
                found.append(following[5:].split(' (offset')[0])
                break
    return found


def install_ids(path):
    """Return the install names of a Mach-O file (empty for a bundle)"""
    return parse_otool_ids(run('otool', '-D', path))


def external_ids(ids, prefixes):
    """Return the install names that point to the build machine"""
    return sorted(i for i in ids if i.startswith(tuple(prefixes)))


def bundle_install_name(path, libdir, frameworks):
    """Return the install name for a library that is in the bundle

    A library in libdir is found as @rpath/name. Others, such as the
    Python framework, are named relative to the Frameworks directory.
    """
    if os.path.dirname(path) == libdir:
        return '@rpath/' + os.path.basename(path)
    return '@rpath/' + os.path.relpath(path, frameworks)


def is_macho(path):
    """Return True for a regular file that is a Mach-O or fat binary"""
    if os.path.islink(path) or not os.path.isfile(path):
        return False
    with open(path, 'rb') as f:
        return f.read(4) in MACHO_MAGIC


def macho_files(bundle):
    """Return all Mach-O files in the bundle"""
    found = []
    for root, _dirs, files in os.walk(bundle):
        for name in files:
            path = os.path.join(root, name)
            if is_macho(path):
                found.append(path)
    return found


def dependencies(path):
    """Return the libraries a Mach-O file loads, except itself"""
    own_ids = parse_otool_ids(run('otool', '-D', path))
    return parse_otool_dependencies(run('otool', '-L', path), own_ids)


def rpaths(path):
    """Return the run paths of a Mach-O file"""
    return parse_otool_rpaths(run('otool', '-l', path))


class Relocator:
    """Copy the dependencies of a bundle into it and rewrite the paths

    bundle: path to the .app
    prefix: Homebrew prefix, from `brew --prefix`
    python_formula: Homebrew formula of the Python that is in the bundle
    """

    def __init__(self, bundle, prefix, python_formula='python@3.12'):
        self.bundle = os.path.realpath(bundle)
        self.prefix = os.path.realpath(prefix)
        # paths of the build machine, which must not be left in the bundle
        self.build_paths = (self.prefix, '/Users/')
        contents = os.path.join(self.bundle, 'Contents')
        self.libdir = os.path.join(contents, 'Frameworks', 'lib')
        self.framework_dst = os.path.join(
            contents, 'Frameworks', 'Python.framework') + '/'
        framework_src = '{}/opt/{}/Frameworks/Python.framework/'.format(
            self.prefix, python_formula)
        # the opt/ path is a symlink to the versioned Cellar directory
        self.framework_srcs = (framework_src,
                               os.path.realpath(framework_src) + '/')
        os.makedirs(self.libdir, exist_ok=True)

    def _copy_lib(self, src, name):
        target = os.path.join(self.libdir, name)
        shutil.copy2(os.path.realpath(src), target)
        # The copy of a read-only library must be writable to change it.
        os.chmod(target, os.stat(target).st_mode | 0o200)
        run('install_name_tool', '-id', '@rpath/' + name, target)
        return target

    def find_target(self, dep):
        """Return the path in the bundle for a dependency, or None

        The library is copied into the bundle if it is not there yet.
        """
        if dep.startswith('@rpath/'):
            name = os.path.basename(dep)
            target = os.path.join(self.libdir, name)
            if os.path.exists(target):
                return target
            candidate = os.path.join(self.prefix, 'lib', name)
            if os.path.exists(candidate):
                return self._copy_lib(candidate, name)
            return None
        if not dep.startswith(self.prefix + '/'):
            return None
        src = next((s for s in self.framework_srcs if dep.startswith(s)),
                   None)
        if src:
            target = self.framework_dst + dep[len(src):]
            if not os.path.exists(target):
                raise FileNotFoundError(
                    'missing in the bundled Python framework: ' + target)
            return target
        name = os.path.basename(dep)
        target = os.path.join(self.libdir, name)
        if os.path.exists(target):
            return target
        return self._copy_lib(dep, name)

    def rewrite_dependencies(self):
        """Copy libraries and point every reference to the bundle

        Copying a library can add new dependencies, so repeat until
        nothing changes. Return the number of rounds.
        """
        rounds = 0
        changed = True
        while changed:
            changed = False
            rounds += 1
            for path in macho_files(self.bundle):
                os.chmod(path, os.stat(path).st_mode | 0o200)
                for dep in dependencies(path):
                    target = self.find_target(dep)
                    if target is None:
                        continue
                    new = '@loader_path/' + os.path.relpath(
                        target, os.path.dirname(path))
                    run('install_name_tool', '-change', dep, new, path)
                    changed = True
        return rounds

    def remove_build_rpaths(self):
        """Delete run paths into Homebrew or a home directory

        Return the number of run paths removed.
        """
        removed = 0
        for path in macho_files(self.bundle):
            for rpath in rpaths(path):
                if rpath.startswith(self.build_paths):
                    run('install_name_tool', '-delete_rpath', rpath, path)
                    removed += 1
        return removed

    def fix_install_names(self):
        """Replace the install names that point to the build machine

        Libraries copied only because a typelib names them, such as
        libgtk-3.0.dylib, keep the install name of Homebrew until then.
        Return the number of files changed.
        """
        frameworks = os.path.dirname(self.libdir)
        fixed = 0
        for path in macho_files(self.bundle):
            if external_ids(install_ids(path), self.build_paths):
                run('install_name_tool', '-id',
                    bundle_install_name(path, self.libdir, frameworks), path)
                fixed += 1
        return fixed

    def problems(self):
        """Return a list of strings that describe what is not self-contained

        Checks that no dependency is outside the bundle or macOS, that
        every @loader_path and @executable_path reference exists, and that
        no run path points outside the bundle.
        """
        found = []
        for path in macho_files(self.bundle):
            rel = os.path.relpath(path, self.bundle)
            for dep in dependencies(path):
                if not dep.startswith(ALLOWED_PREFIXES):
                    found.append('{}: external dependency {}'.format(
                        rel, dep))
                elif dep.startswith('@loader_path/'):
                    target = os.path.normpath(os.path.join(
                        os.path.dirname(path), dep[len('@loader_path/'):]))
                    if not os.path.exists(target):
                        found.append('{}: {} does not exist'.format(
                            rel, dep))
            for own_id in external_ids(install_ids(path), self.build_paths):
                found.append('{}: install name {}'.format(rel, own_id))
            for rpath in rpaths(path):
                if rpath.startswith(self.build_paths):
                    found.append('{}: run path {}'.format(rel, rpath))
        return found

    def sign(self):
        """Sign every Mach-O file ad hoc. Return how many were signed."""
        files = macho_files(self.bundle)
        for path in files:
            run('codesign', '--force', '-s', '-', path)
        return len(files)

    def relocate(self):
        """Do all the steps. Return the list of problems that remain."""
        rounds = self.rewrite_dependencies()
        removed = self.remove_build_rpaths()
        renamed = self.fix_install_names()
        signed = self.sign()
        found = self.problems()
        logger.info('relocate: %d rounds, %d run paths removed, '
                    '%d install names fixed, %d files signed, '
                    '%d problems', rounds, removed, renamed, signed,
                    len(found))
        return found
