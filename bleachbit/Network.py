# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Check for updates via the Internet
"""

# standard library
from bisect import bisect_right
import hashlib
import logging
import os
import re
import socket
import sys
import platform
import warnings
from collections.abc import Callable

# local imports
from bleachbit import bleachbit_exe_path, APP_VERSION, ARCH_BITS, General, IS_LINUX, IS_MAC, IS_NETBSD, IS_WINDOWS
from bleachbit.FileUtilities import delete, open_for_overwrite
from bleachbit.General import unset_sslkeylogfile
from bleachbit.Language import get_active_language_code, get_text as _

# urllib3 v2 warns when the ssl module is not OpenSSL (e.g. macOS
# LibreSSL).  The warning is informational and does not prevent
# urllib3 from functioning, so suppress it before importing urllib3.
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

try:
    from urllib3.util.retry import Retry
    HAVE_URLLIB3 = True
except ImportError:
    HAVE_URLLIB3 = False

# third party
try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False

if HAVE_REQUESTS:
    RequestException = requests.exceptions.RequestException
else:
    class RequestException(Exception):
        pass

logger = logging.getLogger(__name__)


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
        response = fetch_url(url, max_retries=max_retries,
                             backoff_factor=backoff_factor, timeout=timeout)
    except RequestException as exc:
        # For retryable errors (like 503), use a simplified error message
        if HAVE_REQUESTS and isinstance(exc, requests.exceptions.RetryError):
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
    General.makedirs(os.path.dirname(fn))
    with open_for_overwrite(fn, 'wb') as f:
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
    if not url.startswith('http'):
        raise ValueError(f'URL must start with http, got {url}')
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
    if not HAVE_REQUESTS:
        raise RequestException(
            'The requests package is not installed: network features are disabled.')
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


def _version_major_minor(version):
    """Reduce one version token to at most major.minor precision

    For more examples, see test_version_major_minor.
    """
    # ISO date: YYYY-MM-DD or YYYY-MM -> YYYY-MM (e.g., '2008-12-21' -> '2008-12')
    if re.match(r'^\d{4}-\d{2}(-\d{2})?$', version):
        return version[:7]
    # Compact date or Arch build: YYYYMMDD... -> YYYYMM (e.g., '20081221' -> '200812')
    if re.match(r'^\d{8}', version):
        return version[:6]
    # Strip suffix like '-generic', '+deb14', '_1', '-STABLE' (e.g., '6.18.50_1' -> '6.18')
    version = re.split(r'[-+_]', version)[0]
    # Keep major.minor (e.g., '7.0.12' -> '7.0')
    return '.'.join(version.split('.')[:2])


def _coarsen_os_version(os_version):
    """Reduce precision of an 'OS-name version' string

    Keeps the OS/distribution name and reduces the version to
    -  major.minor (e.g., Linux 7.2)
    -  year-month (e.g., 'arch 200812')

    For more examples, see test_coarsen_os_version.
    """
    if not os_version:
        return os_version
    name, sep, rest = os_version.partition(' ')
    if not sep:
        # Bare token: reduce if it is a version, else it is a name
        return _version_major_minor(name) if name[0].isdigit() else name
    version = rest.partition(' ')[0]
    if not version or not version[0].isdigit():
        return os_version
    return f'{name} {_version_major_minor(version)}'


def _coarsen_windows_build(os_version):
    """Reduce precision of a Windows version like '10.0.26461'

    For Windows 10/11 releases within the known range, round the
    build number down.

    For future, unknown build numbers, keep the first two digits.

    For more examples, see test_coarsen_windows_build.
    """
    # Known Windows "10.0.x" versions:
    # Windows 10 1507 (2015) through Windows 11 26H2 (2026).
    windows10_release_builds = (
        10240, 10586, 14393, 15063, 16299, 17134, 17763, 18362, 18363,
        19041, 19042, 19043, 19044, 19045, 22000, 22621, 22631,
        26100, 26200, 26300, 28000
    )

    parts = os_version.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return os_version
    build = parts[2]
    if int(build) > windows10_release_builds[-1]:
        # Future release beyond the known builds
        parts[2] = build[:2].ljust(len(build), '0')
        return '.'.join(parts)
    idx = bisect_right(windows10_release_builds, int(build)) - 1
    if idx < 0:
        return os_version
    parts[2] = str(windows10_release_builds[idx])
    return '.'.join(parts)


def _get_os_name_version():
    """Return (os_name, os_version) tuple for network requests."""
    os_name = platform.system()  # 'Linux', 'Windows', etc.
    if IS_LINUX:
        from bleachbit.Unix import get_distribution_name_version
        os_version = get_distribution_name_version()
    elif IS_MAC:
        # platform.uname().version returns too much info on macOS.
        # Also, drop the patch version (e.g. 26.6.2 -> 26.6).
        os_version = '.'.join(platform.mac_ver()[0].split('.')[:2])
    elif IS_NETBSD:
        os_version = os_name + '/' + platform.machine() + ' ' + platform.release()
    else:
        os_version = platform.uname().version
    if IS_WINDOWS:
        os_version = _coarsen_windows_build(os_version)
    else:
        os_version = _coarsen_os_version(os_version)
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

    if IS_WINDOWS:
        headers['X-Python-Version'] = platform.python_version()
        headers['X-Pointer-Bits'] = str(ARCH_BITS)

    return headers


def get_gtk_version():
    """Return the version of GTK

    If GTK is not available, returns None.
    """
    # pylint: disable=import-error
    from bleachbit.GtkShim import Gtk, is_gtk_available
    if not is_gtk_available():
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

    return f"BleachBit/{APP_VERSION} ({'; '.join(parts)})"
