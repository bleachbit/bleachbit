# vim: ts=4:sw=4:expandtab

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
General code
"""


import os
import sys
import traceback


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
    print 'debug: chown(%s, uid=%s)' % (path, uid)
    if 0 == path.find('/root'):
        print 'note: chown for path /root aborted'
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

    login = None

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
    print "debug: makedirs(%s)" % path
    if os.path.lexists(path):
        return
    parentdir = os.path.split(path)[0]
    if not os.path.lexists(parentdir):
        makedirs(parentdir)
    os.mkdir(path, 0700)
    if sudo_mode():
        chownself(path)


def run_external(args, stdout=False, env=None):
    """Run external command and return (return code, stdout, stderr)"""
    print 'debug: running cmd ', args
    import subprocess
    if False == stdout:
        stdout = subprocess.PIPE
    kwargs = {}
    if subprocess.mswindows:
        # hide the 'DOS box' window
        stui = subprocess.STARTUPINFO()
        import win32process
        stui.dwFlags = win32process.STARTF_USESHOWWINDOW
        import win32con
        stui.wShowWindow = win32con.SW_HIDE
        kwargs['startupinfo'] = stui
    p = subprocess.Popen(args, stdout=stdout,
                         stderr=subprocess.PIPE, env=env, **kwargs)
    try:
        out = p.communicate()
    except KeyboardInterrupt:
        out = p.communicate()
        print out[0]
        print out[1]
        raise
    return (p.returncode, out[0], out[1])


def sudo_mode():
    """Return whether running in sudo mode"""
    if not sys.platform.startswith('linux'):
        return False

    # if 'root' == os.getenv('USER'):
        # gksu in Ubuntu 9.10 changes the username.  If the username is root,
        # we're practically not in sudo mode.
        # Fedora 13: os.getenv('USER') = 'root' under sudo
        # return False

    return os.getenv('SUDO_UID') != None
