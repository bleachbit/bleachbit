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


import subprocess



###
### XML
###


def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError('Invalid boolean: %s' % value)


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

def run_external(args, stdout = subprocess.PIPE):
    """Run external command and return (return code, stdout, stderr)"""
    print 'debug: running cmd ', args
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


