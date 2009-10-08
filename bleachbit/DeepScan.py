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
Scan directory tree for files to delete
"""


import Common
import os
import re
import sqlite3
import unittest


class ScanCache:

    def __init__(self):
        dbpath = os.path.join(Common.options_dir, "deepscan.sqlite3")
        self.conn = sqlite3.connect(dbpath)
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute("CREATE TABLE deepscan (path PRIMARY KEY, modified, size)")
        except sqlite3.OperationalError, e:
            if not str(e).strip() == "table deepscan already exists":
                raise



    def cache(self, path):
        size = os.path.getsize(path)
        modified = os.path.getmtime(path)
        sql = "insert into deepscan values (?, ?, ?)"
        self.cursor.execute(sql, [ path, modified, size ] )


    def is_cached(self, path):
        try:
            size = os.path.getsize(path)
            modified = os.path.getmtime(path)
        except:
            return False
        sql = "select size from deepscan where path=? and modified=? and size=?"
        for row in self.cursor.execute(sql, [ path, modified, size ]):
            return True
        return False


    def purge(self):
        for path in self.cursor.execute('select path from deepscan'):
            print 'cached=', path, path[0]
            if not os.path.lexists(path[0]):
                self.cursor.execute('delete from deepscan where path=?', path)
        self.cursor.execute('vacuum')


    def __del__(self):
        self.purge()
        self.conn.commit()



class DeepScan:

   def __init__(self):
        self.roots = []
        self.searches = {}


   def add_search(self, dirname, regex):
        """Starting in dirname, look for files matching regex"""
        if not self.searches.has_key(dirname):
            self.searches[dirname] = [ regex ]
        else:
            self.searches[dirname].append( regex )


   def scan(self):
        """Perform requested searches and yield each match"""
        print 'debug: searches=', self.searches
        import time
        yield_time = time.time()

        for (top, regexes) in self.searches.iteritems():
            for (dirpath, dirnames, filenames) in os.walk(top):
                for regex in regexes:
                    # fixme, don't match filename twice
                    r = re.compile(regex)
                    for filename in filenames:
                        if r.search(filename):
                            yield os.path.join(dirpath, filename)
                if time.time() - yield_time > 0.25:
                    # allow GTK+ to process the idle loop
                    yield True
                    yield_time = time.time()



class TestDeepScan(unittest.TestCase):
    """Unit test for module DeepScan"""


    def test_DeepScan(self):
        """Unit test for class DeepScan"""
        ds = DeepScan()
        path = os.path.expanduser('~')
        ds.add_search(path, '^Makefile$')
        ds.add_search(path, '~$')
        ds.add_search(path, 'bak$')
        ds.add_search(path, '^Thumbs.db$')
        ds.add_search(path, '^Thumbs.db:encryptable$')
        for ret in ds.scan():
            if True == ret:
                # it's yielding control to the GTK idle loop
                continue
            self.assert_(isinstance(ret, (str, unicode)), \
                "Expecting string but got '%s' (%s)" % \
                 (ret, str(type(ret))))
            self.assert_(os.path.lexists(ret))


    def test_ScanCache(self):
        """Unit test for class ScanCache"""
        sc = ScanCache()
        import tempfile
        (fd, filename) = tempfile.mkstemp('bleachbit-deepscan-test')
        os.close(fd)
        self.assertEqual(sc.is_cached(filename), False)
        sc.cache(filename)
        self.assertEqual(sc.is_cached(filename), True)
        os.remove(filename)
        sc.purge()
        self.assertEqual(sc.is_cached(filename), False)


if __name__ == '__main__':
    unittest.main()

