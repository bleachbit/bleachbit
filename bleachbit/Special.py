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
Special cleaning operations
"""


from Options import options
import FileUtilities



def delete_mozilla_url_history(path):
    """Delete URL history in Mozilla places.sqlite (Firefox 3 and family)"""

    # delete the URLs in moz_places
    places_suffix = "where id in (select " \
        "moz_places.id from moz_places " \
        "left join moz_inputhistory on moz_inputhistory.place_id = moz_places.id " \
        "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
        "where moz_inputhistory.input is null " \
        "and moz_bookmarks.id is null); "

    cmds = ""

    if options.get('shred'):
        shred_places_cmd = "update moz_places " \
            "set url = randomblob(length(url)), " \
            "rev_host = randomblob(length(rev_host)), " \
            "title = randomblob(length(title))" + places_suffix
        cmds += shred_places_cmd
        shred_places_cmd = "update moz_places " \
            "set url = zeroblob(length(url)), " \
            "rev_host = zeroblob(length(rev_host)), " \
            "title = zeroblob(length(title))" + places_suffix
        cmds += shred_places_cmd


    delete_places_cmd = "delete from moz_places " + places_suffix
    cmds += delete_places_cmd

    # delete any orphaned annotations in moz_annos
    annos_suffix =  "where id in (select moz_annos.id " \
        "from moz_annos " \
        "left join moz_places " \
        "on moz_annos.place_id = moz_places.id " \
        "where moz_places.id is null); "

    if options.get('shred'):
        shred_annos_cmd = "update moz_annos " \
            "set content = randomblob(length(content)) " \
            + annos_suffix
        cmds += shred_annos_cmd
        shred_annos_cmd = "update moz_annos " \
            "set content = zeroblob(length(content)) " \
            + annos_suffix
        cmds += shred_annos_cmd

    delete_annos_cmd = "delete from moz_annos " + annos_suffix
    cmds += delete_annos_cmd

    # delete any orphaned favicons
    fav_suffix = "where id not in (select favicon_id " \
        "from moz_places ); "

    if options.get('shred'):
        shred_fav_cmd = "update moz_favicons " \
            "set url = randomblob(length(url)), " \
            "data = randomblob(length(data)) " \
            +  fav_suffix
        cmds += shred_fav_cmd
        shred_fav_cmd = "update moz_favicons " \
            "set url = zeroblob(length(url)), " \
            "data = zeroblob(length(data)) " \
            +  fav_suffix
        cmds += shred_fav_cmd


    delete_fav_cmd = "delete from moz_favicons " + fav_suffix
    cmds += delete_fav_cmd

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

