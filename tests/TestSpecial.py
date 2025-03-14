# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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

from bleachbit.Options import options
from bleachbit import FileUtilities, Special
from tests import common

import os
import os.path
import shutil
import sqlite3
import contextlib

chrome_bookmarks = b"""
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
INSERT INTO "autofill" VALUES('ltmpl','sso','sso',1,3);
CREATE TABLE autofill_dates ( pair_id INTEGER DEFAULT 0, date_created INTEGER DEFAULT 0);
INSERT INTO "autofill_dates" VALUES(1,1268958682);
CREATE TABLE autofill_profile_names ( guid VARCHAR, first_name VARCHAR, middle_name VARCHAR, last_name VARCHAR, full_name VARCHAR);
INSERT INTO "autofill_profile_names" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','andrew','','ziem','');
CREATE TABLE autofill_profile_emails ( guid VARCHAR, email VARCHAR);
INSERT INTO "autofill_profile_emails" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','a@a.a');
CREATE TABLE "autofill_profile_phones" ( guid VARCHAR, number VARCHAR);
INSERT INTO "autofill_profile_phones" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','123457890');
CREATE TABLE "autofill_profiles" ( guid VARCHAR PRIMARY KEY, company_name VARCHAR, street_address VARCHAR, dependent_locality VARCHAR, city VARCHAR, state VARCHAR, zipcode VARCHAR, sorting_code VARCHAR, country_code VARCHAR, date_modified INTEGER NOT NULL DEFAULT 0, origin VARCHAR DEFAULT '', language_code VARCHAR, use_count INTEGER NOT NULL DEFAULT 0, use_date INTEGER NOT NULL DEFAULT 0);
INSERT INTO "autofill_profiles" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA','','1234 anywhere st','','City','ST','000000','','US',1386736740,'','',5,1437861201);
CREATE TABLE local_addresses(guid VARCHAR, use_count INTEGER, use_date INTEGER, date_modified INTEGER,  language_code VARCHAR, label VARCHAR, initial_creator_id INTEGER, last_modifier_id INTEGER);
INSERT INTO "local_addresses" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 1, 1667776445, 1667776456, '', '', 70073, 70073);
CREATE TABLE local_addresses_type_tokens(guid VARCHAR, type INTEGER, value VARCHAR, verification_status INTEGER);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 60, '', 0);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 3, 'andrew', 1);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 5, 'ziem', 1);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 77, '1234 anywhere st', 3);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 33, 'City', 0);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 36, 'US', 3);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 35, '0000000', 3);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 9, 'a@a.a', 0);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 14, '123457890', 0);
INSERT INTO "local_addresses_type_tokens" VALUES('AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', 60, 'bleachbit company', 0);
CREATE TABLE server_addresses (id VARCHAR,company_name VARCHAR,street_address VARCHAR,address_1 VARCHAR,address_2 VARCHAR,address_3 VARCHAR,address_4 VARCHAR,postal_code VARCHAR,sorting_code VARCHAR,country_code VARCHAR,language_code VARCHAR, recipient_name VARCHAR, phone_number VARCHAR);
INSERT INTO "server_addresses" VALUES('a','','123 anywhere','ST','City','',NULL,'0000','','US','','andrew ziem','+1 000-000-0000');
"""

# databases/Databases.db from Chromium 12
chrome_databases_db = """
CREATE TABLE Databases (id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, estimated_size INTEGER NOT NULL);
INSERT INTO "Databases" VALUES(1,'chrome-extension_fjnbnpbmkenffdnngjfgmeleoegfcffe_0','stylish','Stylish Styles',5242880);
INSERT INTO "Databases" VALUES(2,'http_samy.pl_0','sqlite_evercookie','evercookie',1048576);
"""


firefox78_places_sql = """
CREATE TABLE moz_annos (  id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, anno_attribute_id INTEGER, content LONGVARCHAR, flags INTEGER DEFAULT 0, expiration INTEGER DEFAULT 0, type INTEGER DEFAULT 0, dateAdded INTEGER DEFAULT 0, lastModified INTEGER DEFAULT 0);
CREATE TABLE moz_historyvisits (  id INTEGER PRIMARY KEY, from_visit INTEGER, place_id INTEGER, visit_date INTEGER, visit_type INTEGER, session INTEGER);
INSERT INTO moz_historyvisits VALUES(1,0,13,1597441943359769,2,0);
CREATE TABLE moz_inputhistory (  place_id INTEGER NOT NULL, input LONGVARCHAR NOT NULL, use_count INTEGER, PRIMARY KEY (place_id, input));
INSERT INTO moz_inputhistory VALUES(12,'bleachbit.org',1);
CREATE TABLE moz_meta (key TEXT PRIMARY KEY, value NOT NULL) WITHOUT ROWID ;
INSERT INTO moz_meta VALUES('origin_frecency_count',3);
INSERT INTO moz_meta VALUES('origin_frecency_sum',52148);
INSERT INTO moz_meta VALUES('origin_frecency_sum_of_squares',2312614202);
CREATE TABLE moz_origins ( id INTEGER PRIMARY KEY, prefix TEXT NOT NULL, host TEXT NOT NULL, frecency INTEGER NOT NULL, UNIQUE (prefix, host) );
INSERT INTO moz_origins VALUES(1,'https://','support.mozilla.org',-1);
CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER DEFAULT NULL, parent INTEGER, position INTEGER, title LONGVARCHAR, keyword_id INTEGER, folder_type TEXT, dateAdded INTEGER, lastModified INTEGER, guid TEXT, syncStatus INTEGER NOT NULL DEFAULT 0, syncChangeCounter INTEGER NOT NULL DEFAULT 1);
INSERT INTO moz_bookmarks VALUES(1,2,NULL,2,0,'Mozilla Firefox',NULL,NULL,1604681523951000,1604681523951000,'I3rvZbIM7HUh',0,1);
INSERT INTO moz_bookmarks VALUES(5,1,4,7,3,'About Us',NULL,NULL,1604681523951000,1604681523951000,'kz-2zgrxtHgA',0,1);
INSERT INTO moz_bookmarks VALUES(6,1,5,3,0,'Getting Started',NULL,NULL,1604681524006000,1604681524006000,'cLugSkZM_O0C',0,1);
INSERT INTO moz_bookmarks VALUES(7,1,10,5,0,'tubecast',NULL,NULL,1606684638623000,1606684669335000,'pTngoES7vS4t',1,4);
INSERT INTO moz_bookmarks VALUES(8,1,1048,5,1,'reddit: the front page of the internet',NULL,NULL,1625670902669000,1625670902669000,'HboIUJAnNSQq',1,1);
INSERT INTO moz_bookmarks VALUES(9,1,1049,5,2,'Wikipedia',NULL,NULL,1625678442192000,1625678442192000,'kLNboN4LnQyQ',1,1);
INSERT INTO moz_bookmarks VALUES(10,1,1047,5,3,'Base64 Image Encoder',NULL,NULL,1625678511003000,1625678511003000,'mJswt5mUpX6V',1,1);
INSERT INTO moz_bookmarks VALUES(11,1,1052,5,4,'Lebab Modernizing Javascript Code',NULL,NULL,1625678570164000,1625678570164000,'KnR8OLEDutKj',1,1);
INSERT INTO moz_bookmarks VALUES(12,1,1055,5,5,'Epoch Times | Truth and Tradition',NULL,NULL,1634407905800000,1634407905800000,'xiNkiy3pRnRM',1,1);
INSERT INTO moz_bookmarks VALUES(13,1,1074,5,3,'javascript_bookmark',NULL,NULL,1634541546301000,1634541578237000,'5zn7HFpTz9Zk',1,3);
CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url LONGVARCHAR, title LONGVARCHAR, rev_host LONGVARCHAR, visit_count INTEGER DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL, typed INTEGER DEFAULT 0 NOT NULL, frecency INTEGER DEFAULT -1 NOT NULL, last_visit_date INTEGER , guid TEXT, foreign_count INTEGER DEFAULT 0 NOT NULL, url_hash INTEGER DEFAULT 0 NOT NULL , description TEXT, preview_image_url TEXT, origin_id INTEGER REFERENCES moz_origins(id));
INSERT INTO moz_places VALUES(4,'https://www.mozilla.org/en-US/about/',NULL,'gro.allizom.www.',0,0,0,-1,NULL,'qku4XnVuwKXz',1,47358774953055,NULL,NULL,2);
INSERT INTO moz_places VALUES(5,'https://www.mozilla.org/en-US/firefox/central/',NULL,'gro.allizom.www.',0,0,1,-1,NULL,'zEH44cXgEbiW',1,47356370932282,NULL,NULL,2);
INSERT INTO moz_places VALUES(10,'javascript:location.href="tubecast:link="+location.href%3B',NULL,'.',0,0,0,-1,NULL,'CVfq8S1yN9ob',1,61195540700963,NULL,NULL,4);
INSERT INTO moz_places VALUES(1047,'https://www.base64-image.de/',NULL,'ed.egami-46esab.www.',0,0,1,-1,NULL,'CdMLr4ivquym',1,47357677431233,NULL,NULL,52);
INSERT INTO moz_places VALUES(1048,'https://www.reddit.com/',NULL,'moc.tidder.www.',2,0,1,2250,1634421287533000,'Wm14AXzccAt2',1,47359719085711,NULL,NULL,53);
INSERT INTO moz_places VALUES(1049,'https://www.wikipedia.org/',NULL,'gro.aidepikiw.www.',0,0,1,-1,NULL,'S1IyTeEofltl',1,47356939545358,NULL,NULL,54);
INSERT INTO moz_places VALUES(1052,'https://lebab.unibtc.me/editor/',NULL,'em.ctbinu.babel.',0,0,1,-1,NULL,'y4p_ByrC9qLQ',1,47358502989035,NULL,NULL,56);
INSERT INTO moz_places VALUES(1055,'https://theepochtimes.com/',NULL,'gro.afadnulaf.',0,0,1,-1,NULL,'oLhJTCaTzP2H',1,47357288143104,NULL,NULL,59);
INSERT INTO moz_places VALUES(1056,'https://www.youtube.com/',NULL,'moc.ebutuoy.www.',1,0,1,2000,1634421071354000,'nqpzAbgRUY_X',0,47360296250519,NULL,NULL,60);
INSERT INTO moz_places VALUES(1057,'https://duckduckgo.com/?t=ffab&q=duck',NULL,'moc.ogkcudkcud.',1,0,1,2000,1634421160833000,'R1rB2oXM7G1w',0,47357908794703,NULL,NULL,61);
INSERT INTO moz_places VALUES(1058,'https://duckduckgo.com/?t=ffab&q=duck&ia=web',NULL,'moc.ogkcudkcud.',1,0,0,100,1634421161955000,'LfiihU6H8JTJ',0,47357725238190,NULL,NULL,61);
INSERT INTO moz_places VALUES(1059,'https://duckduckgo.com/',NULL,'moc.ogkcudkcud.',1,0,0,100,1634421168747000,'3_aU-W5GQtVY',0,47357557756924,NULL,NULL,61);
INSERT INTO moz_places VALUES(1060,'https://www.reddit.com/r/bulgaria/?f=flair_name%3A%22IMAGE%22',NULL,'moc.tidder.www.',1,0,0,100,1634421202542000,'91A-gGXCdGJo',0,47358238683930,NULL,NULL,53);
INSERT INTO moz_places VALUES(1074,'javascript:(function(d){d.PwnBkmkVer=3%3Bd.body.appendChild(d.createElement(''script'')).src=''https://deturl.com/ld.php?''+1*new Date%3B})(document)%3B',NULL,'.',0,0,0,140,NULL,'MHLDGrz54C06',1,61196492657957,NULL,NULL,69);
"""


firefox78_favicons_sql = """
CREATE TABLE moz_icons (id INTEGER PRIMARY KEY, icon_url TEXT NOT NULL, fixed_icon_url_hash INTEGER NOT NULL, width INTEGER NOT NULL DEFAULT 0, root INTEGER NOT NULL DEFAULT 0, color INTEGER, expire_ms INTEGER NOT NULL DEFAULT 0, data BLOB);
INSERT INTO moz_icons VALUES(1,'fake-favicon-uri:https://support.mozilla.org/en-US/products/firefox',136572340459075,32,0,NULL,1605286324005,NULL);
INSERT INTO moz_icons VALUES(2,'fake-favicon-uri:https://support.mozilla.org/en-US/kb/customize-firefox-controls-buttons-and-toolbars?utm_source=firefox-browser&utm_medium=default-bookmarks&utm_campaign=customize',136571753046205,32,0,NULL,1605286324005,NULL);
INSERT INTO moz_icons VALUES(3,'fake-favicon-uri:https://www.mozilla.org/en-US/contribute/',136575540959674,65535,0,NULL,1605286324005,NULL);
INSERT INTO moz_icons VALUES(4,'fake-favicon-uri:https://www.mozilla.org/en-US/about/',136574776814270,65535,0,NULL,1605286324005,NULL);
INSERT INTO moz_icons VALUES(5,'fake-favicon-uri:https://www.mozilla.org/en-US/firefox/central/',136572730577725,32,0,NULL,1605286324059,NULL);
INSERT INTO moz_icons VALUES(6,'https://www.redditstatic.com/desktop2x/img/favicon/android-icon-192x192.png',292525218,192,0,NULL,1635025978652,NULL);
INSERT INTO moz_icons VALUES(7,'https://www.redditstatic.com/desktop2x/img/favicon/favicon-16x16.png',2364888881,16,0,NULL,1635025978655,NULL);
INSERT INTO moz_icons VALUES(13,'https://lebab.unibtc.me/favicon.ico',2265932027,32,1,NULL,1635027449609,NULL);
INSERT INTO moz_icons VALUES(14,'https://theepochtimes.com/favicon.ico',4178624107,16,1,NULL,1634917808089,NULL);
INSERT INTO moz_icons VALUES(23,'https://duckduckgo.com/assets/icons/meta/DDG-iOS-icon_152x152.png?v=2',2781351171,144,0,NULL,1635025961392,NULL);
INSERT INTO moz_icons VALUES(24,'https://duckduckgo.com/favicon.ico',4139558766,16,1,NULL,1635025969003,NULL);
INSERT INTO moz_icons VALUES(25,'https://duckduckgo.com/favicon.ico',4139558766,32,1,NULL,1635025969003,NULL);
INSERT INTO moz_icons VALUES(29,'https://www.mozilla.org/media/img/favicons/firefox/browser/favicon-196x196.59e3822720be.png',3142301241,192,0,NULL,1634993957394,NULL);
INSERT INTO moz_icons VALUES(33,'https://www.youtube.com/s/desktop/89d6cbd0/img/favicon_144x144.png',2213531744,144,0,NULL,1635025873106,NULL);
INSERT INTO moz_icons VALUES(34,'https://www.youtube.com/s/desktop/89d6cbd0/img/favicon.ico',2155043602,16,0,NULL,1635025873107,NULL);
INSERT INTO moz_icons VALUES(42,'https://www.base64-image.de/favicon.ico',834103348,16,1,NULL,1635088213227,NULL);
CREATE TABLE moz_icons_to_pages ( page_id INTEGER NOT NULL, icon_id INTEGER NOT NULL, expire_ms INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (page_id, icon_id), FOREIGN KEY (page_id) REFERENCES moz_pages_w_icons ON DELETE CASCADE, FOREIGN KEY (icon_id) REFERENCES moz_icons ON DELETE CASCADE ) WITHOUT ROWID;
INSERT INTO moz_icons_to_pages VALUES(1,1,1605286324005);
INSERT INTO moz_icons_to_pages VALUES(2,2,1605286324005);
INSERT INTO moz_icons_to_pages VALUES(3,3,1605286324005);
INSERT INTO moz_icons_to_pages VALUES(4,4,1605286324005);
INSERT INTO moz_icons_to_pages VALUES(5,5,1605286324059);
INSERT INTO moz_icons_to_pages VALUES(6,6,1635025978652);
INSERT INTO moz_icons_to_pages VALUES(6,7,1635025978655);
INSERT INTO moz_icons_to_pages VALUES(14,23,1634993919592);
INSERT INTO moz_icons_to_pages VALUES(16,29,1634993957394);
INSERT INTO moz_icons_to_pages VALUES(17,33,1635025873106);
INSERT INTO moz_icons_to_pages VALUES(17,34,1635025873107);
INSERT INTO moz_icons_to_pages VALUES(21,6,1635025978652);
INSERT INTO moz_icons_to_pages VALUES(21,7,1635025978655);
CREATE TABLE moz_pages_w_icons ( id INTEGER PRIMARY KEY, page_url TEXT NOT NULL, page_url_hash INTEGER NOT NULL );
INSERT INTO moz_pages_w_icons VALUES(1,'https://support.mozilla.org/en-US/products/firefox',47357795150914);
INSERT INTO moz_pages_w_icons VALUES(2,'https://support.mozilla.org/en-US/kb/customize-firefox-controls-buttons-and-toolbars?utm_source=firefox-browser&utm_medium=default-bookmarks&utm_campaign=customize',47359532431620);
INSERT INTO moz_pages_w_icons VALUES(3,'https://www.mozilla.org/en-US/contribute/',47358034485371);
INSERT INTO moz_pages_w_icons VALUES(4,'https://www.mozilla.org/en-US/about/',47358774953055);
INSERT INTO moz_pages_w_icons VALUES(5,'https://www.mozilla.org/en-US/firefox/central/',47356370932282);
INSERT INTO moz_pages_w_icons VALUES(6,'https://www.reddit.com/',47359719085711);
INSERT INTO moz_pages_w_icons VALUES(14,'https://duckduckgo.com/?t=ffab&q=firefox+version+history&ia=web',47359570459686);
INSERT INTO moz_pages_w_icons VALUES(16,'https://www.mozilla.org/en-US/firefox/78.0/releasenotes/',47357311834713);
INSERT INTO moz_pages_w_icons VALUES(17,'https://www.youtube.com/',47360296250519);
INSERT INTO moz_pages_w_icons VALUES(21,'https://www.reddit.com/r/bulgaria/?f=flair_name%3A%22IMAGE%22',47358238683930);
"""


class SpecialAssertions:

    def assertTablesAreEmpty(self, path, tables):
        """Asserts SQLite tables exists and are empty"""
        if not os.path.lexists(path):
            raise AssertionError('Path does not exist: %s' % path)
        with sqlite3.connect(path) as conn:
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

        dir_google_chrome_default = os.path.join(
            self.dir_base, 'google-chrome/Default/')
        os.makedirs(dir_google_chrome_default)

        # google-chrome/Default/Bookmarks
        bookmark_path = os.path.join(
            dir_google_chrome_default, 'Bookmarks')
        with open(bookmark_path, 'wb') as f:
            f.write(chrome_bookmarks)

        # google-chrome/Default/Web Data
        FileUtilities.execute_sqlite3(os.path.join(
            dir_google_chrome_default, 'Web Data'), chrome_webdata)

        # google-chrome/Default/History
        FileUtilities.execute_sqlite3(os.path.join(
            dir_google_chrome_default, 'History'), chrome_history_sql)

        # google-chrome/Default/databases/Databases.db
        os.makedirs(os.path.join(dir_google_chrome_default, 'databases'))
        FileUtilities.execute_sqlite3(
            os.path.join(dir_google_chrome_default, 'databases/Databases.db'), chrome_databases_db)

        dir_firefox_default = os.path.join(
            self.dir_base, 'firefox/default-release/')
        os.makedirs(dir_firefox_default)

        # firefox/xxxxx.default-release/places.sqlite
        FileUtilities.execute_sqlite3(
            os.path.join(dir_firefox_default, 'places.sqlite'), firefox78_places_sql)

        # firefox/xxxxx.default-release/favicons.sqlite
        FileUtilities.execute_sqlite3(
            os.path.join(dir_firefox_default, 'favicons.sqlite'), firefox78_favicons_sql)

    def tearDown(self):
        """Remove test browser files."""
        from bleachbit.General import gc_collect
        gc_collect()
        shutil.rmtree(self.dir_base)

    def sqlite_clean_helper(self, sql, fn, clean_func, check_func=None, setup_func=None):
        """Helper for cleaning special SQLite cleaning

        sql: string with SQL code to initialize an SQLite database
        fn: filename of an existing SQLite database
        clean_func: a function to clean the SQLite database
        check_func (optional): a function to perform extra checks on the database
        setup_func (optional): a function to initialize the database before executing the SQL
        """

        self.assertFalse(
            sql and fn, "sql and fn are mutually exclusive ways to create the data")

        if fn and sql:
            raise RuntimError(
                'sqlite_clean_helper: supply either fn or sql but not both')
        elif fn:
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
        clean_func(filename)
        options.set('shred', old_shred, commit=False)
        self.assertExists(filename)

        # check
        if check_func:
            check_func(self, filename)

        # tear down
        # FileUtilities.delete(filename)
        # self.assertNotExists(filename)

    def test_delete_chrome_autofill(self):
        """Unit test for delete_chrome_autofill"""
        fn = "google-chrome/Default/Web Data"

        def check_autofill(testcase, filename):
            testcase.assertTablesAreEmpty(
                filename,
                ['autofill', 'local_addresses',
                    'local_addresses_type_tokens', 'server_addresses']
            )

        self.sqlite_clean_helper(
            None, fn, Special.delete_chrome_autofill, check_func=check_autofill)

    def test_delete_chrome_databases_db(self):
        """Unit test for delete_chrome_databases_db"""
        self.sqlite_clean_helper(
            None, "google-chrome/Default/databases/Databases.db", Special.delete_chrome_databases_db)

    def test_delete_chrome_history(self):
        """Unit test for delete_chrome_history"""

        def check_chrome_history(self, filename):
            conn = sqlite3.connect(filename)
            try:
                c = conn.cursor()
                c.execute('select id from urls')
                ids = [row[0] for row in c]
                # id 1 is sqlite.org which is not a bookmark and should be cleaned
                # id 2 is www.bleachbit.org which is a bookmark and should
                # be cleaned
                self.assertEqual(ids, [2])

                # these tables should always be empty after cleaning
                self.assertTablesAreEmpty(filename, ['downloads', 'keyword_search_terms',
                                                     'segment_usage', 'segments', 'visits'])
            finally:
                conn.close()

        self.sqlite_clean_helper(None, "google-chrome/Default/History",
                                 Special.delete_chrome_history, check_chrome_history)

    def test_delete_chrome_keywords(self):
        """Unit test for delete_chrome_keywords"""

        def check_chrome_keywords(self, filename):
            conn = sqlite3.connect(filename)
            try:
                c = conn.cursor()
                c.execute('select id from keywords')
                ids = [row[0] for row in c]
                self.assertEqual(ids, [2, 3, 4, 5, 6])
            finally:
                conn.close()

        self.sqlite_clean_helper(None, "google-chrome/Default/Web Data", Special.delete_chrome_keywords,
                                 check_chrome_keywords)

    def test_delete_mozilla_url_history(self):
        """Test for delete_mozilla_url_history"""
        self.sqlite_clean_helper(
            None, "firefox/default-release/places.sqlite", Special.delete_mozilla_url_history)

        # Pale Moon 28 comes from an older Firefox, and it does not have moz_origins or moz_meta in places.sqlite.
        import re
        re_palemoon = '(CREATE TABLE|INSERT INTO) moz_(meta|origins)'
        sql_palemoon = '\n'.join([line for line in firefox78_places_sql.split(
            '\n') if not re.search(re_palemoon, line)])
        self.sqlite_clean_helper(
            sql_palemoon, None, Special.delete_mozilla_url_history)

    def test_delete_mozilla_no_places(self):
        """Test for delete_mozilla_url_history without places.sqlite

        See https://github.com/bleachbit/bleachbit/issues/1423
        """
        sql_no_places = firefox78_places_sql + ";\ndrop table moz_places;"
        self.sqlite_clean_helper(
            sql_no_places, None, Special.delete_mozilla_url_history)

    def test_delete_mozilla_favicons(self):
        """Test for delete_mozilla_favicons"""

        # Firefox favicons for domains are kept differently than those for specific pages:
        # https://bugzilla.mozilla.org/show_bug.cgi?id=1468968
        # so we need a more detailed unit test.

        fn = "firefox/default-release/favicons.sqlite"
        self.sqlite_clean_helper(
            None, fn, Special.delete_mozilla_favicons)

        filename = os.path.normpath(os.path.join(self.dir_base, fn))
        with contextlib.closing(sqlite3.connect(filename)) as conn:
            cursor = conn.cursor()
            icon_entries = cursor.execute('SELECT * FROM moz_icons').fetchall()
            icon_ids = map(lambda x: x[0], icon_entries)
            cursor.close()

        # not removed ids from moz_icons table
        expected_icon_ids = [4, 5, 6, 7, 13, 14, 42]
        assert sorted(expected_icon_ids) == sorted(icon_ids)

    def test_get_chrome_bookmark_ids(self):
        """Unit test for get_chrome_bookmark_ids()"""
        # does not exist
        # Google Chrome 23 on Windows 8 does not create a bookmarks file on first startup
        # (maybe because the network was disconnected or because user created no bookmarks).
        self.assertEqual(
            [], Special.get_chrome_bookmark_ids('does_not_exist'))

    def test_get_chrome_bookmark_urls(self):
        """Unit test for get_chrome_bookmark_urls()"""
        path = self.write_file('bleachbit-test-sqlite', chrome_bookmarks)

        self.assertExists(path)
        urls = Special.get_chrome_bookmark_urls(path)
        self.assertEqual(
            set(urls), {'https://www.bleachbit.org/', 'http://www.slashdot.org/'})

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
        ver = Special.get_sqlite_int(
            filename, 'select value from meta where key="version"')
        self.assertEqual(ver, [20])
