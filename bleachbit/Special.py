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
Cross-platform, special cleaning operations
"""


from Options import options
import FileUtilities


def __shred_sqlite_char_columns(table, cols, where = ""):
    """Create an SQL command to shred character columns"""
    cmd = ""
    if options.get('shred'):
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = randomblob(length(%s))" % (col, col)  for col in cols]), where)
        cmd += "update %s set %s %s;" % \
            (table, ",".join(["%s = zeroblob(length(%s))" % (col, col)  for col in cols]), where)
    cmd += "delete from %s %s;" % (table, where)
    return cmd


def delete_chrome_keywords(path):
    """Delete keywords table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('short_name', 'keyword', 'favicon_url', 'originating_url', 'suggest_url')
    cmds = __shred_sqlite_char_columns('keywords', cols)
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
        "from moz_places ); "

    cols = ('url', 'data')
    cmds += __shred_sqlite_char_columns('moz_favicons', cols, fav_suffix)

    # delete any orphaned history visits
    cmds += "delete from moz_historyvisits where place_id not " \
        "in (select id from moz_places); "

    # execute the commands
    FileUtilities.execute_sqlite3(path, cmds)



def delete_ooo_history(path):
    """Erase the Openoffice.org MRU in Common.xcu"""
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    for node in dom1.getElementsByTagName("node"):
        if node.hasAttribute("oor:name"):
            if "History" == node.getAttribute("oor:name"):
                node.parentNode.removeChild(node)
                node.unlink()
                break
    dom1.writexml(open(path, "w"))

