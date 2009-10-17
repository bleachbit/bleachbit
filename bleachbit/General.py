# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
General code
"""



import os
import sys
import traceback



###
### XML
###

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



###
### General
###

class WindowsError(Exception):
    """Dummy class for non-Windows systems"""
    def __str__(self):
        return 'this is a dummy class for non-Windows systems'


def chownself(path):
    """Set path owner to real self when running in sudo.
    If sudo creates a path and the owner isn't changed, the 
    owner may not be able to access the path."""
    if 'linux2' != sys.platform:
        return
    import pwd
    try:
        login = os.getlogin()
    except:
        login = os.getenv('LOGNAME')
    try:
        uid = pwd.getpwnam(login)[3]
        print 'debug: chown(%s, uid=%s)' % (path, uid)
        os.chown(path, uid, -1)
    except:
        traceback.print_exc()


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
    chownself(path)


def run_external(args, stdout = False):
    """Run external command and return (return code, stdout, stderr)"""
    print 'debug: running cmd ', args
    import subprocess
    if False == stdout:
        stdout = subprocess.PIPE
    p = subprocess.Popen(args, stdout = stdout, \
        stderr = subprocess.PIPE)
    try:
        p.wait()
    except KeyboardInterrupt:
        out = p.communicate()
        print out[0]
        print out[1]
        raise
    outputs = p.communicate()
    return (p.returncode, outputs[0], outputs[1])


def sudo_mode():
    """Return whether running in sudo mode"""
    if 'linux2' != sys.platform:
        return False

    try:
        login1 = os.getlogin()
    except:
        login1 = os.getenv('LOGNAME')

    try:
        import pwd
        login2 = pwd.getpwuid(os.getuid())[0]
        return login1 != login2
    except:
        traceback.print_exc()
        return False



###
### Tests
###

import unittest

class TestGeneral(unittest.TestCase):
    """Test case for module General"""


    def test_boolstr_to_bool(self):
        """Test case for method boolstr_to_bool"""
        tests = ( ('True', True),
            ('true', True ),
            ('False', False ),
            ('false', False ) )

        for test in tests:
            self.assertEqual(boolstr_to_bool(test[0]), test[1])


    def test_makedirs(self):
        """Unit test for makedirs"""
        def cleanup(dir):
            if not os.path.lexists(dir):
                return
            os.rmdir(dir)
            os.rmdir(os.path.dirname(dir))
            self.assert_(not os.path.lexists(dir))

        if 'nt' == os.name:
            dir = 'c:\\temp\\bleachbit-test-makedirs\\a'
        if 'posix' == os.name:
            dir = '/tmp/bleachbit-test-makedirs/a'
        cleanup(dir)
        # directory does not exist
        makedirs(dir)
        self.assert_(os.path.lexists(dir))
        # directory already exists
        makedirs(dir)
        self.assert_(os.path.lexists(dir))
        # clean up
        cleanup(dir)


    def test_sudo_mode(self):
        """Unit test for sudo_mode()"""
        if not sys.platform == 'linux2':
            return
        self.assert_(type(sudo_mode()) is bool)


if __name__ == '__main__':
    unittest.main()

