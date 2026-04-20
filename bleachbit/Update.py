# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Check for updates via the Internet
"""

# standard library
import hashlib
import logging
import os
import sys
import xml.dom.minidom

# local
import bleachbit
from bleachbit import _
from bleachbit.Network import (download_url_to_fn, fetch_url,
                               get_ip_for_url, get_update_request_headers)


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
        raise RuntimeError("%s: %s" % (msg, msg2))

    if download_url_to_fn(url, fn, hash_expected, on_error):
        append_text(_('New winapp2.ini was downloaded.'))
        cb_success()


def user_agent():
    """Return the user agent string

    Deprecated: use bleachbit.Network.get_user_agent() instead.
    Kept for backward compatibility.
    """
    from bleachbit.Network import get_user_agent
    return get_user_agent()


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
    url = bleachbit.update_check_url
    if 'windowsapp' in sys.executable.lower():
        url += '?windowsapp=1'
    # https://github.com/bleachbit/bleachbit/issues/2095
    # requests fails to import on Windows XP/7
    try:
        import queue
    except ImportError:
        logger.exception('check_updates: queue library is not available')
        return ()
    try:
        import urllib3
    except ImportError:
        logger.exception('check_updates: urllib3 library is not available')
        return ()
    try:
        import requests
    except ImportError:
        logger.exception('check_updates: requests library is not available')
        return ()
    try:
        response = fetch_url(url,
                             headers=get_update_request_headers())
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
