# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
General code
"""

import logging
import os
import sys

import bleachbit

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
    rc = "".join(
        node.data for node in nodelist if node.nodeType == node.TEXT_NODE
    )
    return rc


#
# General
#
class WindowsError(Exception):

    """Dummy class for non-Windows systems"""

    def __str__(self):
        return 'this is a dummy class for non-Windows systems'


def makedirs(path):
    """Make directory recursively.
    'Path' should not end in a delimiter."""
    logger.debug('makedirs(%s)', path)
    if os.path.lexists(path):
        return
    parentdir = os.path.split(path)[0]
    if not os.path.lexists(parentdir):
        makedirs(parentdir)
    os.mkdir(path, 0o700)


def run_external(args, stdout=None, env=None, clean_env=None):
    """Run external command and return (return code, stdout, stderr)

    clean_env parameter is unused (kept for backward compatibility)
    """
    logger.debug('running cmd ' + ' '.join(args))
    import subprocess
    if stdout is None:
        stdout = subprocess.PIPE
    kwargs = {}
    encoding = bleachbit.stdout_encoding
    # hide the 'DOS box' window
    import win32process
    import win32con
    stui = subprocess.STARTUPINFO()
    stui.dwFlags = win32process.STARTF_USESHOWWINDOW
    stui.wShowWindow = win32con.SW_HIDE
    kwargs['startupinfo'] = stui
    encoding='mbcs'
    p = subprocess.Popen(args, stdout=stdout,
                         stderr=subprocess.PIPE, env=env, **kwargs)
    try:
        out = p.communicate()
    except KeyboardInterrupt:
        out = p.communicate()
        print(out[0])
        print(out[1])
        raise
    return (p.returncode,
            str(out[0], encoding=encoding) if out[0] else '',
            str(out[1], encoding=encoding) if out[1] else '')


def startup_check():
    """At application startup, check some things are okay."""

    if 'nt' == os.name:
        from bleachbit.Windows import check_dll_hijacking
        check_dll_hijacking()

    # BitDefender false positive.  BitDefender didn't mark BleachBit as infected or show
    # anything in its log, but sqlite would fail to import unless BitDefender was in "game mode."
    # https://www.bleachbit.org/forum/074-fails-errors
    from bleachbit import ModuleNotFoundError
    try:
        from sqlite3 import SQLITE_OK
    except (ModuleNotFoundError, ImportError):
        logger.exception(
            'The sqlite3 module could not be loaded. On Windows, the antivirus may be blocking it. On FreeBSD, install the package databases/py-sqlite3.')


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
