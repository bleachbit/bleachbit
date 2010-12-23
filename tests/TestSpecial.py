# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2010 Andrew Ziem
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
Test case for module Special
"""


import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.append('.')
from bleachbit.Options import options
import bleachbit.FileUtilities
import bleachbit.Special


class SpecialTestCase(unittest.TestCase):
    """Test case for module Special"""


    def test_delete_chrome_keywords(self):
        """Unit test for delete_chrome_keywords"""

        # create test file
        sql = """
CREATE TABLE "keywords" (id INTEGER PRIMARY KEY,short_name VARCHAR NOT NULL,keyword VARCHAR NOT NULL,favicon_url VARCHAR NOT NULL,url VARCHAR NOT NULL,show_in_default_list INTEGER,safe_for_autoreplace INTEGER,originating_url VARCHAR,date_created INTEGER DEFAULT 0,usage_count INTEGER DEFAULT 0,input_encodings VARCHAR,suggest_url VARCHAR,prepopulate_id INTEGER DEFAULT 0,autogenerate_keyword INTEGER DEFAULT 0,logo_id INTEGER DEFAULT 0,created_by_policy INTEGER DEFAULT 0,instant_url VARCHAR);
INSERT INTO "keywords" VALUES(2,'Google','google.com','http://www.google.com/favicon.ico','{google:baseURL}search?{google:RLZ}{google:acceptedSuggestion}{google:originalQueryForSuggestion}sourceid=chrome&ie={inputEncoding}&q={searchTerms}',1,1,'',0,0,'UTF-8','{google:baseSuggestURL}search?client=chrome&hl={language}&q={searchTerms}',1,1,6245,0,'{google:baseURL}search?{google:RLZ}sourceid=chrome-instant&ie={inputEncoding}&q={searchTerms}');"""
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        self.assertRaises(sqlite3.DatabaseError, \
            bleachbit.Special.delete_chrome_keywords, filename)
        bleachbit.FileUtilities.execute_sqlite3(filename, sql)
        self.assert_(os.path.exists(filename))

        # clean the file
        old_shred = options.get('shred')
        options.set('shred', False, commit = False)
        self.assertEqual(False, options.get('shred'))
        bleachbit.Special.delete_chrome_keywords(filename)
        options.set('shred', True, commit = False)
        self.assertEqual(True, options.get('shred'))
        options.set('shred', old_shred, commit = False)
        bleachbit.Special.delete_chrome_keywords(filename)
        self.assert_(os.path.exists(filename))

        # tear down
        bleachbit.FileUtilities.delete(filename)
        self.assert_(not os.path.exists(filename))



def suite():
    return unittest.makeSuite(SpecialTestCase)


if __name__ == '__main__':
    unittest.main()

