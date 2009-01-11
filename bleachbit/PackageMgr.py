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

import subprocess


class RPM:
    def __init__(self):
        self.packages = []

    def scan(self):
        """Refresh list of packages in memory cache"""
        args = ["rpm", "-qa", "--queryformat", "%{NAME}\n"]
        output = subprocess.Popen(args, stdout=subprocess.PIPE).\
                communicate()[0]
        for line in output.split("\n"):
            line = line.replace("\n", "")
            self.packages.append(line)

    def is_installed(self, pkgname):
        if 0 == len(self.packages):
            self.scan()
        return pkgname in self.packages

    def getsize(self, pkgname):
        """Return the size in bytes of a package"""
        raise Exception("not implemented")

    def remove_pkg(self, pkgnames):
        ### --test
        args = ["rpm", "-e"]
        for pkgname in pkgnames:
            args.append(pkgname)
        rc = subprocess.call(args)
        if rc != 0:
            raise Exception("fail")

    def list_packages(self, filter_cb = None):
        """Iterate packages with optional callback filter"""
        if 0 == len(self.packages):
            self.scan()
        for pkg in self.packages:
            if None == filter_cb or filter_cb(pkg):
                yield pkg


import unittest

class TestRPM(unittest.TestCase):
    def setUp(self):
        self.rpm = RPM()

    def test_is_installed(self):
        self.rpm.scan()
        self.assertEqual(self.rpm.is_installed("bash"), True)
        self.assertEqual(self.rpm.is_installed("doesnotexist"), False)

    def test_list_pckages(self):
        # check return value and expect no exceptions
        count = 0
        for pkg in self.rpm.list_packages():
            count += 1
            self.assert_ (type(pkg) is str)
        self.assert_ ( count > 0 )

        # check filter
        count = 0
        filter_cb = lambda pkg: pkg.startswith("py")
        for pkg in self.rpm.list_packages(filter_cb):
            count += 1
            self.assert_ (type(pkg) is str)
        self.assert_ ( count > 0 )


    def test_remove_pkg(self):
        # dependency
        self.assertRaises(Exception, self.rpm.remove_pkg, ["tar"])
        # does not exist
        self.assertRaises(Exception, self.rpm.remove_pkg, ["doesnotexist"])
        # success
        print "fixme"
        # permissions
        print "fixme"
        # verify does not still exist in cached list
        print "fixme"


if __name__ == '__main__':
    unittest.main()

