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
Cross-platform, special cleaning operations
"""

import os.path

from Options import options
import FileUtilities


def __shred_sqlite_char_columns(table, cols, where = ""):
    """Create an SQL command to shred character columns"""
    cmd = ""
    if cols and options.get('shred'):
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = randomblob(length(%s))" % (col, col)  for col in cols]), where)
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = zeroblob(length(%s))" % (col, col)  for col in cols]), where)
    cmd += "delete from %s %s;" % (table, where)
    return cmd


def delete_chrome_autofill(path):
    """Delete autofill table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('name', 'value', 'value_lower')
    cmds = __shred_sqlite_char_columns('autofill', cols)
    cmds += __shred_sqlite_char_columns('autofill_dates', () )
    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_databases_db(path):
    """Delete remote HTML5 cookies (avoiding extension data) from the Databases.db file"""
    cols = ('origin', 'name', 'description')
    where = "where origin not like 'chrome-%'"
    cmds = __shred_sqlite_char_columns('Databases', cols, where)
    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_favicons(path):
    """Delete Google Chrome and Chromium favicons not use in in history for bookmarks"""

    path_history = os.path.join(os.path.dirname(path), 'History')

    # icon_mapping
    cols = ('page_url',)
    where = None
    cmds = ""
    if os.path.exists(path_history):
        cmds += "attach database \"%s\" as History;" % path_history
        where = "where page_url not in (select distinct url from History.urls)"
    cmds += __shred_sqlite_char_columns('icon_mapping', cols, where)

    # favicons
    cols = ('url', 'image_data')
    where = "where id not in (select distinct icon_id from icon_mapping)"
    cmds += __shred_sqlite_char_columns('favicons', cols, where)

    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_history(path):
    """Clean history from History and Favicon files without affecting bookmarks"""
    cols = ('url', 'title')
    where = None
    ids_int = get_chrome_bookmark_ids(path)
    if ids_int:
        ids_str = ",".join([str(id0) for id0 in ids_int])
        where = "where id not in (%s) " % ids_str
    cmds = __shred_sqlite_char_columns('urls', cols, where)
    cmds += __shred_sqlite_char_columns('visits', None)
    cols = ('lower_term', 'term')
    cmds += __shred_sqlite_char_columns('keyword_search_terms', None)
    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_keywords(path):
    """Delete keywords table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('short_name', 'keyword', 'favicon_url', 'originating_url', 'suggest_url')
    where = "where not date_created = 0"
    cmds = __shred_sqlite_char_columns('keywords', cols, where)
    cmds += "update keywords set usage_count = 0;"
    FileUtilities.execute_sqlite3(path, cmds)


def delete_mozilla_url_history(path):
    """Delete URL history in Mozilla places.sqlite (Firefox 3 and family)"""

    cmds = ""

    # delete the URLs in moz_places
    places_suffix = "where id in (select " \
        "moz_places.id from moz_places " \
        "left join moz_inputhistory on moz_inputhistory.place_id = moz_places.id " \
        "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
        "where moz_inputhistory.input is null " \
        "and moz_bookmarks.id is null); "

    cols = ('url', 'rev_host', 'title')
    cmds += __shred_sqlite_char_columns('moz_places', cols, places_suffix)

    # delete any orphaned annotations in moz_annos
    annos_suffix =  "where id in (select moz_annos.id " \
        "from moz_annos " \
        "left join moz_places " \
        "on moz_annos.place_id = moz_places.id " \
        "where moz_places.id is null); "

    cmds += __shred_sqlite_char_columns('moz_annos', ('content', ), annos_suffix)

    # delete any orphaned favicons
    fav_suffix = "where id not in (select favicon_id " \
        "from moz_places where favicon_id is not null ); "

    cols = ('url', 'data')
    cmds += __shred_sqlite_char_columns('moz_favicons', cols, fav_suffix)

    # delete any orphaned history visits
    cmds += "delete from moz_historyvisits where place_id not " \
        "in (select id from moz_places where id is not null); "

    # execute the commands
    FileUtilities.execute_sqlite3(path, cmds)



def delete_ooo_history(path):
    """Erase the OpenOffice.org MRU in Common.xcu"""
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    for node in dom1.getElementsByTagName("node"):
        if node.hasAttribute("oor:name"):
            if "History" == node.getAttribute("oor:name"):
                node.parentNode.removeChild(node)
                node.unlink()
                break
    dom1.writexml(open(path, "w"))


def get_chrome_bookmark_ids(history_path):
    """Given the path of a history file, return the ids in the
    urls table that are bookmarks"""
    bookmark_path = os.path.join(os.path.dirname(history_path), 'Bookmarks')
    urls = get_chrome_bookmark_urls(bookmark_path)
    ids = []
    import sqlite3
    conn = sqlite3.connect(history_path)
    cursor = conn.cursor()
    for url in urls:
        cursor.execute('select id from urls where url=?', (url,))
        for row in cursor:
            ids.append(row[0])
    return ids


def get_chrome_bookmark_urls(path):
    """Return a list of bookmarked URLs in Google Chrome/Chromium"""
    try:
        import json
    except:
        import simplejson as json

    # read file to parser
    js = json.load(open(path, 'r'))

    # find bookmarks
    return [bookmark['url'] for bookmark in js['roots']['bookmark_bar']['children']]

