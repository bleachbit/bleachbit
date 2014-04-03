# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2014 Andrew Ziem
# http://bleachbit.sourceforge.net
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
Cross-platform, special cleaning operations
"""

import os.path

from Options import options
import FileUtilities


def __get_chrome_history(path, fn='History'):
    """Get Google Chrome or Chromium history version.  'path' is name of any file in same directory"""
    path_history = os.path.join(os.path.dirname(path), fn)
    ver = get_sqlite_int(
        path_history, 'select value from meta where key="version"')[0]
    assert(ver > 1)
    return ver


def __shred_sqlite_char_columns(table, cols=None, where=""):
    """Create an SQL command to shred character columns"""
    cmd = ""
    if cols and options.get('shred'):
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = randomblob(length(%s))" % (col, col)
             for col in cols]), where)
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = zeroblob(length(%s))" % (col, col)
             for col in cols]), where)
    cmd += "delete from %s %s;" % (table, where)
    return cmd


def get_sqlite_int(path, sql, parameters=None):
    """Run SQL on database in 'path' and return the integers"""
    ids = []
    import sqlite3
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    if parameters:
        cursor.execute(sql, parameters)
    else:
        cursor.execute(sql)
    for row in cursor:
        ids.append(int(row[0]))
    cursor.close()
    conn.close()
    return ids


def delete_chrome_autofill(path):
    """Delete autofill table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('name', 'value', 'value_lower')
    cmds = __shred_sqlite_char_columns('autofill', cols)
    cmds += __shred_sqlite_char_columns('autofill_dates', ())
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
    ver = __get_chrome_history(path)
    cmds = ""

    if ver in [4, 20, 22, 23, 25, 26, 28]:
        # Version 4 includes Chromium 12
        # Version 20 includes Chromium 14, Google Chrome 15, Google Chrome 19
        # Version 22 includes Google Chrome 20
        # Version 25 is Google Chrome 26
        # Version 26 is Google Chrome 29
        # Version 28 is Google Chrome 30

        # icon_mapping
        cols = ('page_url',)
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where page_url not in (select distinct url from History.urls)"
        cmds += __shred_sqlite_char_columns('icon_mapping', cols, where)

        # favicon images
        cols = ('image_data', )
        where = "where id not in (select distinct id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicon_bitmaps', cols, where)

        # favicons
        # Google Chrome 30 (database version 28): image_data moved to table
        # favicon_bitmaps
        if ver < 28:
            cols = ('url', 'image_data')
        else:
            cols = ('url', )
        where = "where id not in (select distinct icon_id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    elif 3 == ver:
        # Version 3 includes Google Chrome 11

        cols = ('url', 'image_data')
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where id not in(select distinct favicon_id from History.urls)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    else:
        raise RuntimeError('%s is version %d' % (path, ver))

    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_history(path):
    """Clean history from History and Favicon files without affecting bookmarks"""
    cols = ('url', 'title')
    where = ""
    ids_int = get_chrome_bookmark_ids(path)
    if ids_int:
        ids_str = ",".join([str(id0) for id0 in ids_int])
        where = "where id not in (%s) " % ids_str
    cmds = __shred_sqlite_char_columns('urls', cols, where)
    cmds += __shred_sqlite_char_columns('visits')
    cols = ('lower_term', 'term')
    cmds += __shred_sqlite_char_columns('keyword_search_terms', cols)
    ver = __get_chrome_history(path)
    if ver >= 20:
        # downloads, segments, segment_usage first seen in Chrome 14, Google Chrome 15 (database version = 20)
        # Google Chrome 30 (database version 28) doesn't have full_path, but it
        # does have current_path and target_path
        if ver >= 28:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('current_path', 'target_path'))
            cmds += __shred_sqlite_char_columns(
                'downloads_url_chains', ('url', ))
        else:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('full_path', 'url'))
        cmds += __shred_sqlite_char_columns('segments', ('name',))
        cmds += __shred_sqlite_char_columns('segment_usage')
    FileUtilities.execute_sqlite3(path, cmds)


def delete_chrome_keywords(path):
    """Delete keywords table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('short_name', 'keyword', 'favicon_url',
            'originating_url', 'suggest_url')
    where = "where not date_created = 0"
    cmds = __shred_sqlite_char_columns('keywords', cols, where)
    cmds += "update keywords set usage_count = 0;"
    ver = __get_chrome_history(path, 'Web Data')
    if ver >= 43 and ver < 49:
        # keywords_backup table first seen in Google Chrome 17 / Chromium 17 which is Web Data version 43
        # In Google Chrome 25, the table is gone.
        cmds += __shred_sqlite_char_columns('keywords_backup', cols, where)
        cmds += "update keywords_backup set usage_count = 0;"

    FileUtilities.execute_sqlite3(path, cmds)


def delete_office_registrymodifications(path):
    """Erase LibreOffice 3.4 and Apache OpenOffice.org 3.4 MRU in registrymodifications.xcu"""
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    modified = False
    for node in dom1.getElementsByTagName("item"):
        if not node.hasAttribute("oor:path"):
            continue
        if not node.getAttribute("oor:path").startswith('/org.openoffice.Office.Histories/Histories/'):
            continue
        node.parentNode.removeChild(node)
        node.unlink()
        modified = True
    if modified:
        dom1.writexml(open(path, "w"))


def delete_mozilla_url_history(path):
    """Delete URL history in Mozilla places.sqlite (Firefox 3 and family)"""

    cmds = ""

    # delete the URLs in moz_places
    places_suffix = "where id in (select " \
        "moz_places.id from moz_places " \
        "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
        "where moz_bookmarks.id is null); "

    cols = ('url', 'rev_host', 'title')
    cmds += __shred_sqlite_char_columns('moz_places', cols, places_suffix)

    # delete any orphaned annotations in moz_annos
    annos_suffix =  "where id in (select moz_annos.id " \
        "from moz_annos " \
        "left join moz_places " \
        "on moz_annos.place_id = moz_places.id " \
        "where moz_places.id is null); "

    cmds += __shred_sqlite_char_columns(
        'moz_annos', ('content', ), annos_suffix)

    # delete any orphaned favicons
    fav_suffix = "where id not in (select favicon_id " \
        "from moz_places where favicon_id is not null ); "

    cols = ('url', 'data')
    cmds += __shred_sqlite_char_columns('moz_favicons', cols, fav_suffix)

    # delete any orphaned history visits
    cmds += "delete from moz_historyvisits where place_id not " \
        "in (select id from moz_places where id is not null); "

    # delete any orphaned input history
    input_suffix = "where place_id not in (select distinct id from moz_places)"
    cols = ('input', )
    cmds += __shred_sqlite_char_columns('moz_inputhistory', cols, input_suffix)

    # execute the commands
    FileUtilities.execute_sqlite3(path, cmds)


def delete_ooo_history(path):
    """Erase the OpenOffice.org MRU in Common.xcu.  No longer valid in Apache OpenOffice.org 3.4."""
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    changed = False
    for node in dom1.getElementsByTagName("node"):
        if node.hasAttribute("oor:name"):
            if "History" == node.getAttribute("oor:name"):
                node.parentNode.removeChild(node)
                node.unlink()
                changed = True
                break
    if changed:
        dom1.writexml(open(path, "w"))


def get_chrome_bookmark_ids(history_path):
    """Given the path of a history file, return the ids in the
    urls table that are bookmarks"""
    bookmark_path = os.path.join(os.path.dirname(history_path), 'Bookmarks')
    if not os.path.exists(bookmark_path):
        return []
    urls = get_chrome_bookmark_urls(bookmark_path)
    ids = []
    for url in urls:
        ids += get_sqlite_int(
            history_path, 'select id from urls where url=?', (url,))
    return ids


def get_chrome_bookmark_urls(path):
    """Return a list of bookmarked URLs in Google Chrome/Chromium"""
    try:
        import json
    except:
        import simplejson as json

    # read file to parser
    js = json.load(open(path, 'r'))

    # empty list
    urls = []

    # local recursive function
    def get_chrome_bookmark_urls_helper(node):
        if not isinstance(node, dict):
            return
        if not node.has_key('type'):
            return
        if node['type'] == "folder":
            # folders have children
            for child in node['children']:
                get_chrome_bookmark_urls_helper(child)
        if node['type'] == "url" and node.has_key('url'):
            urls.append(node['url'])

    # find bookmarks
    for node in js['roots']:
        get_chrome_bookmark_urls_helper(js['roots'][node])

    return list(set(urls))  # unique
