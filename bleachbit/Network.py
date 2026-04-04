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
import socket
import struct
import sys
import platform
from collections.abc import Callable
try:
    from urllib3.util.retry import Retry
    HAVE_URLLIB3 = True
except ImportError:
    HAVE_URLLIB3 = False

# third party
import requests

# local imports
from bleachbit import bleachbit_exe_path, APP_VERSION
from bleachbit.FileUtilities import delete
from bleachbit.Language import get_active_language_code, get_text as _

logger = logging.getLogger(__name__)


def unset_sslkeylogfile(use_logger):
    """Unset environment variable SSLKEYLOGFILE

    Workaround for an OpenSSL crash before checking for updates.
    https://github.com/bleachbit/bleachbit/issues/1826

    Returns True if unset
    """
    if not os.name == 'nt':
        return False
    if not os.environ.get('SSLKEYLOGFILE'):
        return False
    del os.environ['SSLKEYLOGFILE']
    if use_logger:
        logger.debug('The environment variable SSLKEYLOGFILE is not supported')
    return True


def download_url_to_fn(url, fn, expected_sha512=None, on_error=None,
                       max_retries=3, backoff_factor=0.5, timeout=60):
    """Download a URL to the given filename

    fn: target filename

    expected_sha512: expected SHA-512 hash

    on_error: callback function in case of error

    max_retries: retry count

    backoff_factor: how long to wait before retries

    timeout: number of seconds to wait to establish connection

    return: True if succeeded, False if failed
    """
    logger.info('Downloading %s to %s', url, fn)
    assert isinstance(url, str)
    assert isinstance(fn, str), f'fn is not a string: {repr(fn)}'
    assert isinstance(expected_sha512, (type(None), str))
    assert isinstance(on_error, (type(None), Callable))
    assert isinstance(max_retries, int)
    assert isinstance(backoff_factor, float)
    assert isinstance(timeout, int)

    unset_sslkeylogfile(True)

    msg = _('Downloading URL failed: %s') % url

    def do_error(msg2):
        if on_error:
            on_error(msg, msg2)
        delete(fn, ignore_missing=True)  # delete any partial download

    try:
        response = fetch_url(url)
    except requests.exceptions.RequestException as exc:
        # For retryable errors (like 503), use a simplified error message
        if isinstance(exc, requests.exceptions.RetryError):
            msg2 = 'Server temporarily unavailable (retries exceeded)'
            logger.warning("%s: %s", msg, type(exc).__name__)
        else:
            msg2 = f'{type(exc).__name__}: {exc}'
            logger.exception(msg)
        do_error(msg2)
        return False
    if response.status_code != 200:
        logger.error(msg)
        msg2 = f'HTTP status code: {response.status_code}'
        do_error(msg2)
        return False
    if expected_sha512:
        hash_actual = hashlib.sha512(response.content).hexdigest()
        if hash_actual != expected_sha512:
            msg2 = f"SHA-512 mismatch: expected {expected_sha512}, got {hash_actual}"
            do_error(msg2)
            return False
    fn_dir = os.path.dirname(fn)
    if not os.path.exists(fn_dir):
        os.makedirs(fn_dir)
    with open(fn, 'wb') as f:
        f.write(response.content)
    return True


def fetch_url(url, max_retries=3, backoff_factor=0.5, timeout=60,
              headers=None):
    """Fetch a URL using requests library

    Args:
        url (str): URL to fetch content from
        max_retries (int, optional): Maximum number of retry attempts
        backoff_factor (float, optional): A backoff factor to apply between attempts
        timeout (int, optional): How many seconds to wait for the server before giving up
        headers (dict, optional): Extra HTTP headers appended to default headers

    Returns:
        requests.Response: Response object from requests library

    Raises:
        requests.RequestException: If there is an error fetching the URL
    """
    assert isinstance(url, str)
    assert url.startswith('http'), f"URL must start with http, got {url}"
    assert isinstance(max_retries, int)
    assert max_retries >= 0
    assert isinstance(backoff_factor, float)
    assert backoff_factor > 0
    assert isinstance(timeout, int)
    assert timeout > 0
    if hasattr(sys, 'frozen'):
        # when frozen by py2exe, certificates are in alternate location
        ca_bundle = os.path.join(bleachbit_exe_path, 'cacert.pem')
        if os.path.exists(ca_bundle):
            requests.utils.DEFAULT_CA_BUNDLE_PATH = ca_bundle
            requests.adapters.DEFAULT_CA_BUNDLE_PATH = ca_bundle
        else:
            logger.error(
                'Application is frozen but certificate file not found: %s', ca_bundle)
    assert headers is None or isinstance(headers, dict)
    request_headers = {'User-Agent': get_user_agent()}
    if headers:
        request_headers.update(headers)
    unset_sslkeylogfile(True)
    # 408: request timeout
    # 429: too many requests
    # 500: internal server error
    # 502: bad gateway
    # 503: service unavailable
    # 504: gateway_timeout
    status_forcelist = (408, 429, 500, 502, 503, 504)
    with requests.Session() as session:
        if HAVE_URLLIB3:
            retries = Retry(total=max_retries, backoff_factor=backoff_factor,
                            status_forcelist=status_forcelist, redirect=5)
            session.mount(
                'http://', requests.adapters.HTTPAdapter(max_retries=retries))
            session.mount(
                'https://', requests.adapters.HTTPAdapter(max_retries=retries))
        response = session.get(url, headers=request_headers,
                               timeout=timeout, verify=True)
    return response


def _get_os_name_version():
    """Return (os_name, os_version) tuple for network requests."""
    os_name = platform.system()  # 'Linux', 'Windows', etc.
    if sys.platform == 'linux':
        # pylint: disable=import-outside-toplevel
        from bleachbit.Unix import get_distribution_name_version
        os_version = get_distribution_name_version()
    elif sys.platform[:6] == 'netbsd':
        os_version = os_name + '/' + platform.machine() + ' ' + platform.release()
    else:
        os_version = platform.uname().version
    return os_name, os_version


def get_update_request_headers():
    """Return headers specific to update checks."""
    os_name, os_version = _get_os_name_version()

    headers = {
        'X-BleachBit-Version': APP_VERSION,
        'X-OS-Type': os_name,
        'X-OS-Version': os_version,
        'X-Locale': get_active_language_code(),
    }

    if (gtk_version := get_gtk_version()):
        headers['X-GTK-Version'] = gtk_version

    if os.name == 'nt':
        headers['X-Python-Version'] = platform.python_version()
        headers['X-Pointer-Bits'] = str(8 * struct.calcsize('P'))

    return headers


def get_gtk_version():
    """Return the version of GTK

    If GTK is not available, returns None.
    """
    # pylint: disable=import-outside-toplevel, import-error
    from bleachbit.GtkShim import Gtk, HAVE_GTK
    if not HAVE_GTK:
        return None
    gtk_version = (Gtk.get_major_version(),
                   Gtk.get_minor_version(), Gtk.get_micro_version())
    return '.'.join([str(x) for x in gtk_version])


def get_ip_for_url(url):
    """Given an https URL, return the IP address"""
    if not url:
        return '(no URL)'
    url_split = url.split('/')
    if len(url_split) < 3:
        return '(bad URL)'
    hostname = url.split('/')[2]
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        return '(socket.gaierror)'
    return ip_address


def get_user_agent():
    """Return the user agent string"""
    os_name, os_ver = _get_os_name_version()
    locale = get_active_language_code()
    parts = [os_name, os_ver, locale]
    if (gtk_ver := get_gtk_version()):
        parts.append(f'GTK {gtk_ver}')

    agent = f"BleachBit/{APP_VERSION} ({'; '.join(parts)})"
    return agent
