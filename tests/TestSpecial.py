# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
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
Test case for module Special
"""

from __future__ import absolute_import, print_function

from bleachbit.Options import options
from bleachbit import FileUtilities, Special
from tests import common

import os
import os.path
import shutil
import sqlite3


chrome_bookmarks = """
{
   "checksum": "0313bd70dd6343134782af4b233016bf",
   "roots": {
      "bookmark_bar": {
         "children": [  ],
         "date_added": "12985843036082659",
         "date_modified": "0",
         "id": "1",
         "name": "Bookmarks Bar",
         "type": "folder"
      },
      "other": {
         "children": [ {
            "children": [ {
               "date_added": "12985843072462200",
               "id": "6",
               "name": "BleachBit",
               "type": "url",
               "url": "https://www.bleachbit.org/"
            } ],
            "date_added": "12985843051141788",
            "date_modified": "12985843072462200",
            "id": "4",
            "name": "software",
            "type": "folder"
         }, {
            "children": [ {
               "date_added": "12985843081812026",
               "id": "7",
               "name": "Slashdot",
               "type": "url",
               "url": "http://www.slashdot.org/"
            } ],
            "date_added": "12985843060482329",
            "date_modified": "12985843081812026",
            "id": "5",
            "name": "news",
            "type": "folder"
         } ],
         "date_added": "12985843036082740",
         "date_modified": "0",
         "id": "2",
         "name": "Other Bookmarks",
         "type": "folder"
      },
      "synced": {
         "children": [  ],
         "date_added": "12985843036082744",
         "date_modified": "0",
         "id": "3",
         "name": "Mobile Bookmarks",
         "type": "folder"
      }
   },
   "version": 1
}"""

# <Default/History> from Google Chrome 23
chrome_history_sql = """
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
INSERT INTO "meta" VALUES('version','23');
CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL);
INSERT INTO "urls" VALUES(1,'http://sqlite.org/','SQLite Home Page',1,0,13001833567334094,0,0);
INSERT INTO "urls" VALUES(2,'https://www.bleachbit.org/','BleachBit - Clean Disk Space, Maintain Privacy',1,0,13001833567892577,0,0);
CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed BOOLEAN,visit_duration INTEGER DEFAULT 0 NOT NULL);
INSERT INTO "visits" VALUES(1,1,13001833567334094,0,805306374,0,1,8629624);
INSERT INTO "visits" VALUES(2,2,13001833567892577,0,805306374,0,1,9249493);
CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term LONGVARCHAR NOT NULL);
INSERT INTO "keyword_search_terms" VALUES(2,3,'bleachbit','bleachbit');
CREATE TABLE downloads (id INTEGER PRIMARY KEY,full_path LONGVARCHAR NOT NULL,url LONGVARCHAR NOT NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT NULL,end_time INTEGER NOT NULL,opened INTEGER NOT NULL);
CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id INTEGER NON NULL,pres_index INTEGER DEFAULT -1 NOT NULL);
CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER DEFAULT 0 NOT NULL);
"""


# <Default/Web Data> from Google Chrome 23
chrome_webdata = """
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
INSERT INTO "meta" VALUES('version','46');
CREATE TABLE keywords (id INTEGER PRIMARY KEY,short_name VARCHAR NOT NULL,keyword VARCHAR NOT NULL,favicon_url VARCHAR NOT NULL,url VARCHAR NOT NULL,safe_for_autoreplace INTEGER,originating_url VARCHAR,date_created INTEGER DEFAULT 0,usage_count INTEGER DEFAULT 0,input_encodings VARCHAR,show_in_default_list INTEGER,suggest_url VARCHAR,prepopulate_id INTEGER DEFAULT 0,created_by_policy INTEGER DEFAULT 0,instant_url VARCHAR,last_modified INTEGER DEFAULT 0,sync_guid VARCHAR);
INSERT INTO "keywords" VALUES(2,'Google','google.com','http://www.google.com/favicon.ico','{google:baseURL}search?q={searchTerms}&{google:RLZ}{google:acceptedSuggestion}{google:originalQueryForSuggestion}{google:assistedQueryStats}{google:searchFieldtrialParameter}sourceid=chrome&ie={inputEncoding}',1,'',0,0,'UTF-8',1,'{google:baseSuggestURL}search?{google:searchFieldtrialParameter}client=chrome&hl={language}&q={searchTerms}&sugkey={google:suggestAPIKeyParameter}',1,0,'{google:baseURL}webhp?sourceid=chrome-instant&{google:RLZ}{google:instantEnabledParameter}ie={inputEncoding}',0,'2D65ABE4-008A-21F1-8C9E-C95DE46CC245');
INSERT INTO "keywords" VALUES(3,'Yahoo! Canada','ca.yahoo.com','http://ca.search.yahoo.com/favicon.ico','http://ca.search.yahoo.com/search?ei={inputEncoding}&fr=crmas&p={searchTerms}',1,'',0,0,'UTF-8',1,'http://gossip.ca.yahoo.com/gossip-ca-sayt?output=fxjsonp&command={searchTerms}',2,0,'',0,'F4BAF053-6C8E-6183-C8BB-3104F82260AD');
INSERT INTO "keywords" VALUES(4,'Yahoo! QuÃ©bec','qc.yahoo.com','http://qc.search.yahoo.com/favicon.ico','http://qc.search.yahoo.com/search?ei={inputEncoding}&fr=crmas&p={searchTerms}',1,'',0,0,'UTF-8',1,'',5,0,'',0,'B42D7616-CF8F-6677-A206-19345BB5FE0F');
INSERT INTO "keywords" VALUES(5,'Bing','bing.com','http://www.bing.com/s/wlflag.ico','http://www.bing.com/search?setmkt=en-CA&q={searchTerms}',1,'',0,0,'UTF-8',1,'http://api.bing.com/osjson.aspx?query={searchTerms}&language={language}',3,0,'',0,'73FA48F9-1ABD-BA46-F563-1AF75572B5DF');
INSERT INTO "keywords" VALUES(6,'Bing','bing.com_','http://www.bing.com/s/wlflag.ico','http://www.bing.com/search?setmkt=fr-CA&q={searchTerms}',1,'',0,0,'UTF-8',1,'http://api.bing.com/osjson.aspx?query={searchTerms}&language={language}',7,0,'',0,'2D932B46-8F26-5C02-7E2F-BE62F263BE9D');
INSERT INTO "keywords" VALUES(7,'cnn.com','cnn.com','http://www.cnn.com/favicon.ico','http://www.cnn.com/search/?query={searchTerms}&x=0&y=0&primaryType=mixed&sortBy=relevance&intl=false',1,'',1357360881,0,'UTF-8',0,'',0,0,'',1357360881,'0B71F4CA-380D-0228-064F-24CDF1F8FBD1');
CREATE TABLE keywords_backup(
  id INT,
  short_name TEXT,
  keyword TEXT,
  favicon_url TEXT,
  url TEXT,
  safe_for_autoreplace INT,
  originating_url TEXT,
  date_created INT,
  usage_count INT,
  input_encodings TEXT,
  show_in_default_list INT,
  suggest_url TEXT,
  prepopulate_id INT,
  created_by_policy INT,
  instant_url TEXT,
  last_modified INT,
  sync_guid TEXT
);
INSERT INTO "keywords_backup" VALUES(2,'Google','google.com','http://www.google.com/favicon.ico','{google:baseURL}search?q={searchTerms}&{google:RLZ}{google:acceptedSuggestion}{google:originalQueryForSuggestion}{google:assistedQueryStats}{google:searchFieldtrialParameter}sourceid=chrome&ie={inputEncoding}',1,'',0,0,'UTF-8',1,'{google:baseSuggestURL}search?{google:searchFieldtrialParameter}client=chrome&hl={language}&q={searchTerms}&sugkey={google:suggestAPIKeyParameter}',1,0,'{google:baseURL}webhp?sourceid=chrome-instant&{google:RLZ}{google:instantEnabledParameter}ie={inputEncoding}',0,'CB88DDB4-E4A2-80BC-3BEE-C8F02FDBA58A');
INSERT INTO "keywords_backup" VALUES(3,'Yahoo! Canada','ca.yahoo.com','http://ca.search.yahoo.com/favicon.ico','http://ca.search.yahoo.com/search?ei={inputEncoding}&fr=crmas&p={searchTerms}',1,'',0,0,'UTF-8',1,'http://gossip.ca.yahoo.com/gossip-ca-sayt?output=fxjsonp&command={searchTerms}',2,0,'',0,'21CD15EC-B9CA-4DCB-8526-0A4048CBA5F3');
INSERT INTO "keywords_backup" VALUES(4,'Yahoo! QuÃ©bec','qc.yahoo.com','http://qc.search.yahoo.com/favicon.ico','http://qc.search.yahoo.com/search?ei={inputEncoding}&fr=crmas&p={searchTerms}',1,'',0,0,'UTF-8',1,'',5,0,'',0,'AB0C2A23-C483-F255-8BEB-7A2B4E0C465F');
INSERT INTO "keywords_backup" VALUES(5,'Bing','bing.com','http://www.bing.com/s/wlflag.ico','http://www.bing.com/search?setmkt=en-CA&q={searchTerms}',1,'',0,0,'UTF-8',1,'http://api.bing.com/osjson.aspx?query={searchTerms}&language={language}',3,0,'',0,'D77A8BC1-3CD6-4AB5-93B2-72B0C2E94E73');
INSERT INTO "keywords_backup" VALUES(6,'Bing','bing.com_','http://www.bing.com/s/wlflag.ico','http://www.bing.com/search?setmkt=fr-CA&q={searchTerms}',1,'',0,0,'UTF-8',1,'http://api.bing.com/osjson.aspx?query={searchTerms}&language={language}',7,0,'',0,'E1035236-31F4-216A-632A-A7323A1B7A70');
CREATE TABLE autofill (name VARCHAR, value VARCHAR, value_lower VARCHAR, pair_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 1);
CREATE TABLE autofill_dates ( pair_id INTEGER DEFAULT 0, date_created INTEGER DEFAULT 0);
INSERT INTO "autofill" VALUES('ltmpl','sso','sso',1,3);
INSERT INTO "autofill_dates" VALUES(1,1268958682);
CREATE TABLE autofill_profile_names ( guid VARCHAR, first_name VARCHAR, middle_name VARCHAR, last_name VARCHAR, full_name VARCHAR);
INSERT INTO "autofill_profile_names" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','andrew','','ziem','');
CREATE TABLE autofill_profile_emails ( guid VARCHAR, email VARCHAR);
INSERT INTO "autofill_profile_emails" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','a@a.a');
CREATE TABLE "autofill_profile_phones" ( guid VARCHAR, number VARCHAR);
INSERT INTO "autofill_profile_phones" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','123457890');
CREATE TABLE "autofill_profiles" ( guid VARCHAR PRIMARY KEY, company_name VARCHAR, street_address VARCHAR, dependent_locality VARCHAR, city VARCHAR, state VARCHAR, zipcode VARCHAR, sorting_code VARCHAR, country_code VARCHAR, date_modified INTEGER NOT NULL DEFAULT 0, origin VARCHAR DEFAULT '', language_code VARCHAR, use_count INTEGER NOT NULL DEFAULT 0, use_date INTEGER NOT NULL DEFAULT 0);
INSERT INTO "autofill_profiles" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','','1234 anywhere st','','City','ST','000000','','US',1386736740,'','',5,1437861201);
CREATE TABLE server_addresses (id VARCHAR,company_name VARCHAR,street_address VARCHAR,address_1 VARCHAR,address_2 VARCHAR,address_3 VARCHAR,address_4 VARCHAR,postal_code VARCHAR,sorting_code VARCHAR,country_code VARCHAR,language_code VARCHAR, recipient_name VARCHAR, phone_number VARCHAR);
INSERT INTO "server_addresses" VALUES('a','','123 anywhere','ST','City','',NULL,'0000','','US','','andrew ziem','+1 000-000-0000');
"""

# databases/Databases.db from Chromium 12
chrome_databases_db = """
CREATE TABLE Databases (id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, estimated_size INTEGER NOT NULL);
INSERT INTO "Databases" VALUES(1,'chrome-extension_fjnbnpbmkenffdnngjfgmeleoegfcffe_0','stylish','Stylish Styles',5242880);
INSERT INTO "Databases" VALUES(2,'http_samy.pl_0','sqlite_evercookie','evercookie',1048576);
"""


class SpecialAssertions:

    def assertTablesAreEmpty(self, path, tables):
        """Asserts SQLite tables exists and are empty"""
        if not os.path.lexists(path):
            raise AssertionError('Path does not exist: %s' % path)
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        for table in tables:
            cursor.execute('select 1 from %s limit 1' % table)
            row = cursor.fetchone()
            if row:
                raise AssertionError('Table is not empty: %s ' % table)


class SpecialTestCase(common.BleachbitTestCase, SpecialAssertions):

    """Test case for module Special"""

    def setUp(self):
        """Create test browser files."""

        super(SpecialTestCase, self).setUp()

        self.dir_base = self.mkdtemp(prefix='bleachbit-test-special')
        self.dir_google_chrome_default = os.path.join(self.dir_base, 'google-chrome/Default/')
        os.makedirs(self.dir_google_chrome_default)

        # google-chrome/Default/Bookmarks
        bookmark_path = os.path.join(
            self.dir_google_chrome_default, 'Bookmarks')
        f = open(bookmark_path, 'w')
        f.write(chrome_bookmarks)
        f.close()

        # google-chrome/Default/Web Data
        FileUtilities.execute_sqlite3(os.path.join(self.dir_google_chrome_default, 'Web Data'), chrome_webdata)

        # google-chrome/Default/History
        FileUtilities.execute_sqlite3(os.path.join(self.dir_google_chrome_default, 'History'), chrome_history_sql)

        # google-chrome/Default/databases/Databases.db
        os.makedirs(os.path.join(self.dir_google_chrome_default, 'databases'))
        FileUtilities.execute_sqlite3(
            os.path.join(self.dir_google_chrome_default, 'databases/Databases.db'), chrome_databases_db)

    def tearDown(self):
        """Remove test browser files."""
        shutil.rmtree(self.dir_base)

    def sqlite_clean_helper(self, sql, fn, clean_func, check_func=None, setup_func=None):
        """Helper for cleaning special SQLite cleaning"""

        self.assertFalse(sql and fn, "sql and fn are mutually exclusive ways to create the data")

        if fn:
            filename = os.path.normpath(os.path.join(self.dir_base, fn))
            self.assertExists(filename)

        # create sqlite file
        elif sql:
            # create test file
            filename = self.mkstemp(prefix='bleachbit-test-sqlite')

            # additional setup
            if setup_func:
                setup_func(filename)

            # before SQL creation executed, cleaning should fail
            self.assertRaises(sqlite3.DatabaseError, clean_func, filename)
            # create
            FileUtilities.execute_sqlite3(filename, sql)
            self.assertExists(filename)
        else:
            raise RuntimeError('neither fn nor sql supplied')

        # clean the file
        old_shred = options.get('shred')
        options.set('shred', False, commit=False)
        self.assertFalse(options.get('shred'))
        clean_func(filename)
        options.set('shred', True, commit=False)
        self.assertTrue(options.get('shred'))
        options.set('shred', old_shred, commit=False)
        clean_func(filename)
        self.assertExists(filename)

        # check
        if check_func:
            check_func(self, filename)

        # tear down
        FileUtilities.delete(filename)
        self.assertNotExists(filename)

    def test_delete_chrome_autofill(self):
        """Unit test for delete_chrome_autofill"""
        fn = "google-chrome/Default/Web Data"

        def check_autofill(testcase, filename):
            testcase.assertTablesAreEmpty(filename, ['autofill','autofill_profile_emails', 'autofill_profile_names',
                                                     'autofill_profile_phones', 'autofill_profiles','server_addresses'])

        self.sqlite_clean_helper(None, fn, Special.delete_chrome_autofill, check_func=check_autofill)

    def test_delete_chrome_databases_db(self):
        """Unit test for delete_chrome_databases_db"""
        self.sqlite_clean_helper(
            None, "google-chrome/Default/databases/Databases.db", Special.delete_chrome_databases_db)

    def test_delete_chrome_history(self):
        """Unit test for delete_chrome_history"""

        def check_chrome_history(self, filename):
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            c.execute('select id from urls')
            ids = []
            for row in c:
                ids.append(row[0])
            # id 1 is sqlite.org which is not a bookmark and should be cleaned
            # id 2 is www.bleachbit.org which is a bookmark and should
            # be cleaned
            self.assertEqual(ids, [2])

            # these tables should always be empty after cleaning
            self.assertTablesAreEmpty(filename, ['downloads', 'keyword_search_terms',
                                                 'segment_usage', 'segments', 'visits'])

        self.sqlite_clean_helper(None, "google-chrome/Default/History",
                                 Special.delete_chrome_history, check_chrome_history)

    def test_delete_chrome_keywords(self):
        """Unit test for delete_chrome_keywords"""

        def check_chrome_keywords(self, filename):
            conn = sqlite3.connect(filename)
            c = conn.cursor()
            c.execute('select id from keywords')
            ids = []
            for row in c:
                ids.append(row[0])
            self.assertEqual(ids, [2, 3, 4, 5, 6])

        self.sqlite_clean_helper(None, "google-chrome/Default/Web Data", Special.delete_chrome_keywords,
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
        self.sqlite_clean_helper(sql, None, Special.delete_mozilla_url_history)

    def test_get_chrome_bookmark_ids(self):
        """Unit test for get_chrome_bookmark_ids()"""
        # does not exist
        # Google Chrome 23 on Windows 8 does not create a bookmarks file on first startup
        # (maybe because the network was disconnected or because user created no bookmarks).
        self.assertEqual(
            [], Special.get_chrome_bookmark_ids('does_not_exist'))

    def test_get_chrome_bookmark_urls(self):
        """Unit test for get_chrome_bookmark_urls()"""
        path= self.write_file('bleachbit-test-sqlite', chrome_bookmarks)

        self.assertExists(path)
        urls = Special.get_chrome_bookmark_urls(path)
        self.assertEqual(set(urls), {u'https://www.bleachbit.org/', u'http://www.slashdot.org/'})

        os.unlink(path)

    def test_get_sqlite_int(self):
        """Unit test for get_sqlite_int()"""
        sql = """CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY,value LONGVARCHAR);
INSERT INTO "meta" VALUES('version','20');"""
        # create test file
        filename = self.mkstemp(prefix='bleachbit-test-sqlite')
        FileUtilities.execute_sqlite3(filename, sql)
        self.assertExists(filename)
        # run the test
        ver = Special.get_sqlite_int(filename, 'select value from meta where key="version"')
        self.assertEqual(ver, [20])
