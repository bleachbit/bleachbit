# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
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
Check for updates via the Internet
"""

import bleachbit
from bleachbit import _

import hashlib
import logging
import os
import os.path
import platform
import socket
import sys
import xml.dom.minidom
from urllib.request import build_opener
from urllib.error import URLError


logger = logging.getLogger(__name__)


def update_winapp2(url, hash_expected, append_text, cb_success):
    """Download latest winapp2.ini file.  Hash is sha512 or None to disable checks"""
    # first, determine whether an update is necessary
    from bleachbit import personal_cleaners_dir
    fn = os.path.join(personal_cleaners_dir, 'winapp2.ini')
    delete_current = False
    if os.path.exists(fn):
        with open(fn, 'rb') as f:
            hash_current = hashlib.sha512(f.read()).hexdigest()
            if not hash_expected or hash_current == hash_expected:
                # update is same as current
                return
        delete_current = True
    # download update
    opener = build_opener()
    opener.addheaders = [('User-Agent', user_agent())]
    doc = opener.open(fullurl=url, timeout=20).read()
    # verify hash
    hash_actual = hashlib.sha512(doc).hexdigest()
    if hash_expected and not hash_actual == hash_expected:
        raise RuntimeError("hash for %s actually %s instead of %s" %
                           (url, hash_actual, hash_expected))
    # delete current
    if delete_current:
        from bleachbit.FileUtilities import delete
        delete(fn, True)
    # write file
    if not os.path.exists(personal_cleaners_dir):
        os.mkdir(personal_cleaners_dir)
    with open(fn, 'wb') as f:
        f.write(doc)
    append_text(_('New winapp2.ini was downloaded.'))
    cb_success()


def user_agent():
    """Return the user agent string"""
    __platform = platform.system()  # Linux or Windows
    __os = platform.uname()[2]  # e.g., 2.6.28-12-generic or XP
    if sys.platform == "win32":
        # misleading: Python 2.5.4 shows uname()[2] as Vista on Windows 7
        __os = platform.uname()[3][
            0:3]  # 5.1 = Windows XP, 6.0 = Vista, 6.1 = 7
    elif sys.platform.startswith('linux'):
        dist = platform.linux_distribution()
        # example: ('fedora', '11', 'Leonidas')
        # example: ('', '', '') for Arch Linux
        if 0 < len(dist[0]):
            __os = dist[0] + '/' + dist[1] + '-' + dist[2]
    elif sys.platform[:6] == 'netbsd':
        __sys = platform.system()
        mach = platform.machine()
        rel = platform.release()
        __os = __sys + '/' + mach + ' ' + rel
    __locale = ""
    try:
        import locale
        __locale = locale.getdefaultlocale()[0]  # e.g., en_US
    except:
        logger.exception('Exception when getting default locale')

    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        gtkver = '; GTK %s' % '.'.join([str(x) for x in Gtk.gtk_version])
    except:
        gtkver = ""

    agent = "BleachBit/%s (%s; %s; %s%s)" % (bleachbit.APP_VERSION,
                                             __platform, __os, __locale, gtkver)
    return agent


def update_dialog(parent, updates):
    """Updates contains the version numbers and URLs"""
    from gi.repository import Gtk
    from bleachbit.GuiBasic import open_url
    dlg = Gtk.Dialog(title=_("Update BleachBit"),
                     transient_for=parent,
                     modal=True,
                     destroy_with_parent=True)
    dlg.set_default_size(250, 125)

    label = Gtk.Label(label=_("A new version is available."))
    dlg.vbox.pack_start(label, True, True, 0)

    for update in updates:
        ver = update[0]
        url = update[1]
        box_update = Gtk.Box()
        # TRANSLATORS: %s expands to version such as '0.8.4' or '0.8.5beta' or
        # similar
        button_stable = Gtk.Button(_("Update to version %s") % ver)
        button_stable.connect(
            'clicked', lambda dummy: open_url(url, parent, False))
        button_stable.connect('clicked', lambda dummy: dlg.response(0))
        box_update.pack_start(button_stable, False, True, 10)
        dlg.vbox.pack_start(box_update, False, True, 0)

    dlg.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

    dlg.show_all()
    dlg.run()
    dlg.destroy()

    return False


def check_updates(check_beta, check_winapp2, append_text, cb_success):
    """Check for updates via the Internet"""
    opener = build_opener()
    socket.setdefaulttimeout(bleachbit.socket_timeout)
    opener.addheaders = [('User-Agent', user_agent())]
    import encodings.idna  # https://github.com/bleachbit/bleachbit/issues/760
    url = bleachbit.update_check_url
    if 'windowsapp' in sys.executable.lower():
        url += '?windowsapp=1'
    try:
        handle = opener.open(url)
    except URLError as e:
        logger.error(
            _('Error when opening a network connection to check for updates. Please verify the network is working and that a firewall is not blocking this application. Error message: {}').format(e))
        return ()
    doc = handle.read()
    try:
        dom = xml.dom.minidom.parseString(doc)
    except:
        logger.exception('The update information does not parse: %s', doc)
        return ()

    def parse_updates(element):
        if element:
            ver = element[0].getAttribute('ver')
            url = element[0].firstChild.data
            return ver, url
        return ()

    stable = parse_updates(dom.getElementsByTagName("stable"))
    beta = parse_updates(dom.getElementsByTagName("beta"))

    wa_element = dom.getElementsByTagName('winapp2')
    if check_winapp2 and wa_element:
        wa_sha512 = wa_element[0].getAttribute('sha512')
        wa_url = wa_element[0].getAttribute('url')
        update_winapp2(wa_url, wa_sha512, append_text, cb_success)

    dom.unlink()

    if stable and beta and check_beta:
        return stable, beta
    if stable:
        return stable,
    if beta and check_beta:
        return beta,
    return ()
