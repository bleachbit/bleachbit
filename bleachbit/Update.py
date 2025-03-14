# vim: ts=4:sw=4:expandtab

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
Check for updates via the Internet
"""

# standard library
import hashlib
import logging
import os
import sys
import xml.dom.minidom

# third-party
import requests

# local
import bleachbit
from bleachbit.Language import get_text as _
from bleachbit.Network import download_url_to_fn, fetch_url, get_ip_for_url


logger = logging.getLogger(__name__)


def update_winapp2(url, hash_expected, append_text, cb_success):
    """Download latest winapp2.ini file.  Hash is sha512 or None to disable checks"""
    # first, determine whether an update is necessary

    fn = os.path.join(bleachbit.personal_cleaners_dir, 'winapp2.ini')
    if os.path.exists(fn):
        with open(fn, 'rb') as f:
            hash_current = hashlib.sha512(f.read()).hexdigest()
            if not hash_expected or hash_current == hash_expected:
                # update is same as current
                return
    # download update
    # Define error handler to propagate download errors

    def on_error(msg, msg2):
        raise RuntimeError(f"{msg}: {msg2}")

    if download_url_to_fn(url, fn, hash_expected, on_error):
        append_text(_('New winapp2.ini was downloaded.'))
        cb_success()


def update_dialog(parent, updates):
    """Updates contains the version numbers and URLs"""
    # import these here to allow headless mode.
    from gi.repository import Gtk  # pylint: disable=import-outside-toplevel
    from bleachbit.GuiBasic import open_url  # pylint: disable=import-outside-toplevel
    dlg = Gtk.Dialog(title=_("Update BleachBit"),
                     transient_for=parent,
                     modal=True,
                     destroy_with_parent=True)
    dlg.set_default_size(250, 125)

    label = Gtk.Label(label=_("A new version is available."))
    dlg.vbox.pack_start(label, True, True, 0)

    for (ver, url) in updates:
        box_update = Gtk.Box()
        # TRANSLATORS: %s expands to version such as '4.6.0'
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
    url = bleachbit.update_check_url
    if 'windowsapp' in sys.executable.lower():
        url += '?windowsapp=1'
    try:
        response = fetch_url(url)
    except requests.RequestException as e:
        logger.error(
            _('Error when opening a network connection to check for updates. Please verify the network is working and that a firewall is not blocking this application. Error message: {}').format(e))
        logger.debug('URL %s has IP address %s', url, get_ip_for_url(url))
        if hasattr(e, 'response') and e.response is not None:
            logger.debug(e.response.headers)
        return ()
    try:
        dom = xml.dom.minidom.parseString(response.text)
    except:
        logger.exception(
            'The update information does not parse: %s', response.text)
        return ()

    def parse_updates(element):
        if element:
            ver = element[0].getAttribute('ver')
            url = element[0].firstChild.data
            assert isinstance(ver, str)
            assert isinstance(url, str)
            assert url.startswith('http')
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
        return (stable, beta)
    if stable:
        return (stable,)
    if beta and check_beta:
        return (beta,)
    return ()
