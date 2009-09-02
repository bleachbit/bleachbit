#!/usr/bin/env python
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
Command line interface
"""



import optparse
import sys

import Common



def process_cmd_line():
    """Parse the command line and execute given commands."""
    parser = optparse.OptionParser()
    parser.add_option("-v", "--version", action="store_true", 
        help="Output version information and exit")
    (options, args) = parser.parse_args()
    if options.version:
        print """
BleachBit version %s
Copyright (C) 2009 Andrew Ziem
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""" % Common.APP_VERSION
        sys.exit(0)



process_cmd_line()

