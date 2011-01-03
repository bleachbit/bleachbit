# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2011 Andrew Ziem
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


    def sqlite_clean_helper(self, sql, clean_func, check_func = None):
        """Helper for cleaning special SQLite cleaning"""

        # create test file
        (fd, filename) = tempfile.mkstemp()
        os.close(fd)
        self.assertRaises(sqlite3.DatabaseError, \
            clean_func, filename)
        bleachbit.FileUtilities.execute_sqlite3(filename, sql)
        self.assert_(os.path.exists(filename))

        # clean the file
        old_shred = options.get('shred')
        options.set('shred', False, commit = False)
        self.assertEqual(False, options.get('shred'))
        clean_func(filename)
        options.set('shred', True, commit = False)
        self.assertEqual(True, options.get('shred'))
        options.set('shred', old_shred, commit = False)
        clean_func(filename)
        self.assert_(os.path.exists(filename))

        # check
        if check_func:
            check_func(self, filename)

        # tear down
        bleachbit.FileUtilities.delete(filename)
        self.assert_(not os.path.exists(filename))


    def test_delete_chrome_autofill(self):
        """Unit test for delete_chrome_autofill"""
        sql = """
CREATE TABLE autofill (name VARCHAR, value VARCHAR, value_lower VARCHAR, pair_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 1);
INSERT INTO "autofill" VALUES('ltmpl','sso','sso',1,3);
CREATE TABLE autofill_dates ( pair_id INTEGER DEFAULT 0, date_created INTEGER DEFAULT 0);
INSERT INTO "autofill_dates" VALUES(1,1268958682);
"""
        self.sqlite_clean_helper(sql, bleachbit.Special.delete_chrome_autofill)


    def test_delete_chrome_keywords(self):
        """Unit test for delete_chrome_keywords"""
        sql = """
CREATE TABLE keywords (id INTEGER PRIMARY KEY,short_name VARCHAR NOT NULL,keyword VARCHAR NOT NULL,favicon_url VARCHAR NOT NULL,url VARCHAR NOT NULL,show_in_default_list INTEGER,safe_for_autoreplace INTEGER,originating_url VARCHAR,date_created INTEGER DEFAULT 0,usage_count INTEGER DEFAULT 0,input_encodings VARCHAR,suggest_url VARCHAR,prepopulate_id INTEGER DEFAULT 0,autogenerate_keyword INTEGER DEFAULT 0,logo_id INTEGER DEFAULT 0,created_by_policy INTEGER DEFAULT 0,instant_url VARCHAR);
INSERT INTO "keywords" VALUES(2,'Google','google.com','http://www.google.com/favicon.ico','{google:baseURL}search?{google:RLZ}{google:acceptedSuggestion}{google:originalQueryForSuggestion}sourceid=chrome&ie={inputEncoding}&q={searchTerms}',1,1,'',0,0,'UTF-8','{google:baseSuggestURL}search?client=chrome&hl={language}&q={searchTerms}',1,1,6245,0,'{google:baseURL}search?{google:RLZ}sourceid=chrome-instant&ie={inputEncoding}&q={searchTerms}');
INSERT INTO "keywords" VALUES(3,'Yahoo!','yahoo.com','http://search.yahoo.com/favicon.ico','http://search.yahoo.com/search?ei={inputEncoding}&fr=crmas&p={searchTerms}',1,1,'',0,0,'UTF-8','http://ff.search.yahoo.com/gossip?output=fxjson&command={searchTerms}',2,0,6262,0,'');
INSERT INTO "keywords" VALUES(4,'Bing','bing.com','http://www.bing.com/s/wlflag.ico','http://www.bing.com/search?setmkt=en-US&q={searchTerms}',1,1,'',0,0,'UTF-8','http://api.bing.com/osjson.aspx?query={searchTerms}&language={language}',3,0,6239,0,'');
INSERT INTO "keywords" VALUES(5,'CNN.com','cnn.com','http://www.cnn.com/favicon.ico','http://www.cnn.com/search/?query={searchTerms}',0,1,'http://www.cnn.com/tools/search/cnncom.xml',1294062457,0,'UTF-8','',0,0,0,0,'');
"""

        def check_chrome_keywords(self, filename):
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            c.execute('select id from keywords')
            ids = []
            for row in c:
                ids.append(row[0])
            self.assertEqual(ids, [2,3,4])

        self.sqlite_clean_helper(sql, bleachbit.Special.delete_chrome_keywords, \
            check_chrome_keywords)


    def test_delete_mozilla_url_history(self):
        """Test for delete_mozilla_url_history"""
        sql = """
CREATE TABLE moz_annos (id INTEGER PRIMARY KEY,place_id INTEGER NOT NULL,anno_attribute_id INTEGER,mime_type VARCHAR(32) DEFAULT NULL,content LONGVARCHAR, flags INTEGER DEFAULT 0,expiration INTEGER DEFAULT 0,type INTEGER DEFAULT 0,dateAdded INTEGER DEFAULT 0,lastModified INTEGER DEFAULT 0);
CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY,type INTEGER, fk INTEGER DEFAULT NULL, parent INTEGER, position INTEGER, title LONGVARCHAR, keyword_id INTEGER, folder_type TEXT, dateAdded INTEGER, lastModified INTEGER);
CREATE TABLE moz_favicons (id INTEGER PRIMARY KEY, url LONGVARCHAR UNIQUE, data BLOB, mime_type VARCHAR(32), expiration LONG);
CREATE TABLE moz_historyvisits (id INTEGER PRIMARY KEY, from_visit INTEGER, place_id INTEGER, visit_date INTEGER, visit_type INTEGER, session INTEGER);
CREATE TABLE moz_inputhistory (place_id INTEGER NOT NULL, input LONGVARCHAR NOT NULL, use_count INTEGER, PRIMARY KEY (place_id, input));
CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url LONGVARCHAR, title LONGVARCHAR, rev_host LONGVARCHAR, visit_count INTEGER DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL, typed INTEGER DEFAULT 0 NOT NULL, favicon_id INTEGER, frecency INTEGER DEFAULT -1 NOT NULL, last_visit_date INTEGER);
INSERT INTO "moz_annos" VALUES(46,51918,7,NULL,'UTF-8',0,4,3,1222405592086437,0);
INSERT INTO "moz_bookmarks" VALUES(1,2,NULL,0,0,'',NULL,'',1210078682986320,1246454506982902);
INSERT INTO "moz_favicons" VALUES(28,'http://download.openoffice.org/branding/images/favicon.ico',X'0000010001001010000001001800680300001600000028000000100000002000000001001800000000000000000058020000580200000000000000000000FFFFFEFFFFFFFFFFFEFFFEFFFFFFFFFFFFFFFFFFFFFFFFFEFEFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFEFFFFFFFEFFFF808080FCF8F8F9F6F7F9F6F5FDF6F5FCF9F5FCF8F6FBF8F6FBF7F5FDF6F5FAF9F5FDF6F7FCF9F5F9F8F6FAFAF5FBF7F7808080000000808080F9F2EEF7F2EDF9F3EFF7F1EEF8F1EDF8F0F0F7F1EFF6F2F0F9F0EDF6F1F0F6F2EEF9F3EDF6F3EFF4E9E8000000000000808080F2EAE5F4EAE7F4ECE8F5ECE4F3EAE6F4EBE5F4EAE7F5E9E4F3EAE5F4EAE5F4E9E8F3EBE7EEE6DEF0E5DE808080000000000000808080808080808080EFE3DCEEE4DFEFE3DFEEE6DEF1E4DDEFE4DDEEE4DFEEE2DCEDDDD5EDDDD7EADDD7808080808080000000000000000000EBDED4EADBD6EBDED7EDDDD7EDDFD6EDDBD6EADDD7EBDCD7E7D7CCE8D6CDE9D6CEE7D8CDE9D7CEE6D6CC808080000000000000E9D5CFE7D7CEE8D6CDE7D7CCE6D4CDE8D7CFE7D6CEE5D0C5E3CFC4E3D0C5E4CFC4E3CFC6E2D0C4E4D1C6808080000000808080E3D1C5E2D0C4E5CEC6E4CFC5E5D1C3E4CFC4E0C8BFE2CBBDE0C9BDE1CABCDFC9BCDFCBBBE0CABEDFC7BD808080000000000000808080DFC9BCE0CABFDFC9BEE1CABEDCC3B7DDC3B4DBC2B4DBC2B4DEC2B4DDC1B4808080DEC0B3DDC1B4808080808080808080808080DCC2B5DBC2B6DDC1B6DABDADD8BDADDABEADD8BEADD7BCACD9BDAE808080808080D8BEADD8BCACD7BCACDABBAEDABCACDABEADD9BCACD7BCAED5B4A3D4B7A3D3B5A4D5B6A6D5B6A6D5B4A3D7B5A6000000000000808080808080808080D6B7A5D5B5A4D6B5A6D4B7A5CFAF9DD0AD9ED0B09CD1AE9DD2AD9ECFAF9BD0B09AD1AE9D808080000000000000000000808080D1AE9DD1AE9BD3AF9DCEA895CEA795CCA992CDA895CDA794CCA795CCA793CDA895CDA794CCA895CEA696808080000000808080CCA694CDA996CAA08ACAA28DC9A28DC9A08ACAA28AC9A28CC9A18BCBA18DC8A38CCAA28CC9A08CC8A18D808080000000000000808080C89984C89B85C69A82C79C82C69A83C59B82C69A83C49B85C59985C69A83C59B82C89984C69A82C49982C59C82C89B8300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000','image/x-icon',1266937768995663);
INSERT INTO "moz_historyvisits" VALUES(85696,0,211406,1277603269156003,1,552364937919476439);
INSERT INTO "moz_inputhistory" VALUES(164860,'blog',0.0125459501500806);
INSERT INTO "moz_places" VALUES(17251,'http://download.openoffice.org/2.3.1/index.html','download: OpenOffice.org 2.3.1 Downloads','gro.eciffonepo.daolnwod.',0,0,0,28,20,NULL);
"""
        self.sqlite_clean_helper(sql, bleachbit.Special.delete_mozilla_url_history)



def suite():
    return unittest.makeSuite(SpecialTestCase)


if __name__ == '__main__':
    unittest.main()

