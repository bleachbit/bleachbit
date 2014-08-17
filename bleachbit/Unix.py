# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Integration specific to Unix-like operating systems
"""


import glob
import os
import re
import shlex
import subprocess
import ConfigParser

from Common import _, autostart_path, launcher_path
import FileUtilities
import General

HAVE_GNOME_VFS = True
try:
    import gnomevfs
except:
    try:
        # this is the deprecated name
        import gnome.vfs
    except:
        HAVE_GNOME_VFS = False
    else:
        gnomevfs = gnome.vfs


def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', 'autoclean']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # Del cups-common 1.3.9-17ubuntu3 [1165kB]
        match = re.search("^Del .*\[([0-9.]+[a-zA-Z]{2})\]", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes)
        of freed space"""

    if not FileUtilities.exe_exists('apt-get'):
        raise RuntimeError(_('Executable not found: %s') % 'apt-get')

    args = ['apt-get', '--yes', 'autoremove']

    process = subprocess.Popen(args,
                               stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    total_bytes = 0

    while True:
        line = process.stdout.readline().replace("\n", "")
        if line.startswith('E: '):
            raise RuntimeError(line)
        # After this operation, 74.7MB disk space will be freed.
        match = re.search(
            ", ([0-9.]+[a-zA-Z]{2}) disk space will be freed", line)
        if match:
            pkg_bytes_str = match.groups(0)[0]
            pkg_bytes = FileUtilities.human_to_bytes(pkg_bytes_str.upper())
            total_bytes += pkg_bytes
        if "" == line and process.poll() != None:
            break

    return total_bytes


def __is_broken_xdg_desktop_application(config, desktop_pathname):
    """Returns boolean whether application deskop entry file is broken"""
    if not config.has_option('Desktop Entry', 'Exec'):
        print "info: is_broken_xdg_menu: missing required option 'Exec': '%s'" \
            % (desktop_pathname)
        return True
    exe = config.get('Desktop Entry', 'Exec').split(" ")[0]
    if not FileUtilities.exe_exists(exe):
        print "info: is_broken_xdg_menu: executable '%s' does not exist '%s'" \
            % (exe, desktop_pathname)
        return True
    if 'env' == exe:
        # Wine v1.0 creates .desktop files like this
        # Exec=env WINEPREFIX="/home/z/.wine" wine "C:\\Program
        # Files\\foo\\foo.exe"
        execs = shlex.split(config.get('Desktop Entry', 'Exec'))
        wineprefix = None
        del(execs[0])
        while True:
            if 0 <= execs[0].find("="):
                (name, value) = execs[0].split("=")
                if 'WINEPREFIX' == name:
                    wineprefix = value
                del(execs[0])
            else:
                break
        if not FileUtilities.exe_exists(execs[0]):
            print "info: is_broken_xdg_menu: executable '%s'" \
                "does not exist '%s'" % (execs[0], desktop_pathname)
            return True
        # check the Windows executable exists
        if wineprefix:
            windows_exe = wine_to_linux_path(wineprefix, execs[1])
            if not os.path.exists(windows_exe):
                print "info: is_broken_xdg_menu: Windows executable" \
                    "'%s' does not exist '%s'" % \
                    (windows_exe, desktop_pathname)
                return True
    return False


def is_broken_xdg_desktop(pathname):
    """Returns boolean whether the given XDG desktop entry file is broken.
    Reference: http://standards.freedesktop.org/desktop-entry-spec/latest/"""
    config = ConfigParser.RawConfigParser()
    config.read(pathname)
    if not config.has_section('Desktop Entry'):
        print "info: is_broken_xdg_menu: missing required section " \
            "'Desktop Entry': '%s'" % (pathname)
        return True
    if not config.has_option('Desktop Entry', 'Type'):
        print "info: is_broken_xdg_menu: missing required option 'Type': '%s'" % (pathname)
        return True
    file_type = config.get('Desktop Entry', 'Type').strip().lower()
    if 'link' == file_type:
        if not config.has_option('Desktop Entry', 'URL') and \
                not config.has_option('Desktop Entry', 'URL[$e]'):
            print "info: is_broken_xdg_menu: missing required option 'URL': '%s'" % (pathname)
            return True
        return False
    if 'mimetype' == file_type:
        if not config.has_option('Desktop Entry', 'MimeType'):
            print "info: is_broken_xdg_menu: missing required option 'MimeType': '%s'" % (pathname)
            return True
        mimetype = config.get('Desktop Entry', 'MimeType').strip().lower()
        if HAVE_GNOME_VFS and 0 == len(gnomevfs.mime_get_all_applications(mimetype)):
            print "info: is_broken_xdg_menu: MimeType '%s' not " \
                "registered '%s'" % (mimetype, pathname)
            return True
        return False
    if 'application' != file_type:
        print "Warning: unhandled type '%s': file '%s'" % (file_type, pathname)
        return False
    if __is_broken_xdg_desktop_application(config, pathname):
        return True
    return False


def is_running(exename):
    """Check whether exename is running"""
    for filename in glob.iglob("/proc/*/exe"):
        try:
            target = os.path.realpath(filename)
        except TypeError:
            # happens, for example, when link points to
            # '/etc/password\x00 (deleted)'
            continue
        except OSError:
            # 13 = permission denied
            continue
        if exename == os.path.basename(target):
            return True
    return False


def rotated_logs():
    """Yield a list of rotated (i.e., old) logs in /var/log/"""
    # Ubuntu 9.04
    # /var/log/dmesg.0
    # /var/log/dmesg.1.gz
    # Fedora 10
    # /var/log/messages-20090118
    globpaths = ('/var/log/*.[0-9]',
                 '/var/log/*/*.[0-9]',
                 '/var/log/*.gz',
                 '/var/log/*/*gz',
                 '/var/log/*/*.old',
                 '/var/log/*.old')
    for globpath in globpaths:
        for path in glob.iglob(globpath):
            yield path
    regex = '-[0-9]{8}$'
    globpaths = ('/var/log/*-*', '/var/log/*/*-*')
    for path in FileUtilities.globex(globpaths, regex):
        whitelist_re = '^/var/log/(removed_)?(packages|scripts)'
        if None == re.match(whitelist_re, path):  # for Slackware, Launchpad #367575
            yield path


def start_with_computer(enabled):
    """If enabled, create shortcut to start application with computer.
    If disabled, then delete the shortcut."""
    if not enabled:
        if os.path.lexists(autostart_path):
            FileUtilities.delete(autostart_path)
        return
    if os.path.lexists(autostart_path):
        return
    import shutil
    General.makedirs(os.path.dirname(autostart_path))
    shutil.copy(launcher_path, autostart_path)
    os.chmod(autostart_path, 0755)
    if General.sudo_mode():
        General.chownself(autostart_path)


def start_with_computer_check():
    """Return boolean whether BleachBit will start with the computer"""
    return os.path.lexists(autostart_path)


def wine_to_linux_path(wineprefix, windows_pathname):
    """Return a Linux pathname from an absolute Windows pathname and Wine prefix"""
    drive_letter = windows_pathname[0]
    windows_pathname = windows_pathname.replace(drive_letter + ":",
                                                "drive_" + drive_letter.lower())
    windows_pathname = windows_pathname.replace("\\", "/")
    return os.path.join(wineprefix, windows_pathname)


def yum_clean():
    """Run 'yum clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/yum.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Yum"
        raise RuntimeError(msg)
    if not FileUtilities.exe_exists('yum'):
        raise RuntimeError(_('Executable not found: %s') % 'yum')
    old_size = FileUtilities.getsizedir('/var/cache/yum')
    args = ['yum', "--enablerepo=*", 'clean', 'all']
    p = subprocess.Popen(args, stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    non_blank_line = ""
    while True:
        line = p.stdout.readline().replace("\n", "")
        if len(line) > 2:
            non_blank_line = line
        if -1 != line.find('You need to be root'):
            # Seen before Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Cannot remove rpmdb file'):
            # Since first in Fedora 13
            raise RuntimeError(line)
        if -1 != line.find('Another app is currently holding'):
            print "debug: yum: '%s'" % line
            old_size = FileUtilities.getsizedir('/var/cache/yum')
        if "" == line and p.poll() != None:
            break
    print 'debug: yum process return code = %d' % p.returncode
    if p.returncode > 0:
        raise RuntimeError(non_blank_line)
    new_size = FileUtilities.getsizedir('/var/cache/yum')
    return old_size - new_size
