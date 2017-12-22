# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
General code
"""

from __future__ import absolute_import, print_function

import bleachbit

import logging
import os
import sys
import traceback

logger = logging.getLogger(__name__)


#
# XML
#
def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError("Invalid boolean: '%s'" % value)


def getText(nodelist):
    """Return the text data in an XML node
    http://docs.python.org/library/xml.dom.minidom.html"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


#
# General
#
class WindowsError(Exception):

    """Dummy class for non-Windows systems"""

    def __str__(self):
        return 'this is a dummy class for non-Windows systems'


def chownself(path):
    """Set path owner to real self when running in sudo.
    If sudo creates a path and the owner isn't changed, the
    owner may not be able to access the path."""
    if 'posix' != os.name:
        return
    uid = getrealuid()
    logger.debug('chown(%s, uid=%s)', path, uid)
    if 0 == path.find('/root'):
        logger.info('chown for path /root aborted')
        return
    try:
        os.chown(path, uid, -1)
    except:
        traceback.print_exc()


def getrealuid():
    """Get the real user ID when running in sudo mode"""

    if 'posix' != os.name:
        raise RuntimeError('getrealuid() requires POSIX')

    if os.getenv('SUDO_UID'):
        return int(os.getenv('SUDO_UID'))

    try:
        login = os.getlogin()
        # On Ubuntu 9.04, getlogin() under sudo returns non-root user.
        # On Fedora 11, getlogin() under sudo returns 'root'.
        # On Fedora 11, getlogin() under su returns non-root user.
    except:
        login = os.getenv('LOGNAME')

    if login and 'root' != login:
        import pwd
        return pwd.getpwnam(login)[3]

    return os.getuid()


def makedirs(path):
    """Make directory recursively considering sudo permissions.
    'Path' should not end in a delimiter."""
    logger.debug('makedirs(%s)', path.encode(bleachbit.FSE))
    if os.path.lexists(path):
        return
    parentdir = os.path.split(path)[0]
    if not os.path.lexists(parentdir):
        makedirs(parentdir)
    os.mkdir(path, 0o700)
    if sudo_mode():
        chownself(path)


def run_external(args, stdout=False, env=None, clean_env=True):
    """Run external command and return (return code, stdout, stderr)"""
    logger.debug('running cmd ' + ' '.join(args))
    import subprocess
    if not stdout:
        stdout = subprocess.PIPE
    kwargs = {}
    if subprocess.mswindows:
        # hide the 'DOS box' window
        import win32process, win32con
        stui = subprocess.STARTUPINFO()
        stui.dwFlags = win32process.STARTF_USESHOWWINDOW
        stui.wShowWindow = win32con.SW_HIDE
        kwargs['startupinfo'] = stui
    if not env and clean_env and 'posix' == os.name:
        # Clean environment variables so that that subprocesses use English
        # instead of translated text. This helps when checking for certain
        # strings in the output.
        # https://github.com/bleachbit/bleachbit/issues/167
        # https://github.com/bleachbit/bleachbit/issues/168
        keep_env = ('PATH', 'HOME', 'LD_LIBRARY_PATH', 'TMPDIR')
        env = dict((key, value)
                   for key, value in os.environ.iteritems() if key in keep_env)
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
    p = subprocess.Popen(args, stdout=stdout,
                         stderr=subprocess.PIPE, env=env, **kwargs)
    try:
        out = p.communicate()
    except KeyboardInterrupt:
        out = p.communicate()
        print(out[0])
        print(out[1])
        raise
    return p.returncode, out[0], out[1]


def sudo_mode():
    """Return whether running in sudo mode"""
    if not sys.platform.startswith('linux'):
        return False

    # if 'root' == os.getenv('USER'):
        # gksu in Ubuntu 9.10 changes the username.  If the username is root,
        # we're practically not in sudo mode.
        # Fedora 13: os.getenv('USER') = 'root' under sudo
        # return False

    return os.getenv('SUDO_UID') is not None
