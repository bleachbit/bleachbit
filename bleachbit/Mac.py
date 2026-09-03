# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Integration specific to macOS
"""

import logging
import platform
import subprocess

import bleachbit
from bleachbit import APP_NAME, IS_MAC

logger = logging.getLogger(__name__)

# macOS 10.0-10.15 (Cheetah..Catalina) used '10.x' with the release
# identified by the SECOND component (the old scheme this dict was
# originally written for). Since macOS 11 (Big Sur), Apple dropped
# the '10.' prefix and the release is identified by the FIRST
# component instead (11, 12, ..., 26); using split('.')[1] against a
# modern version string reads the minor/patch number instead of the
# release identifier, so e.g. '26.6.2' incorrectly looked up '6' and
# showed 'Snow Leopard'. Two separate dicts, keyed by the field that
# actually identifies the release in each scheme.
MACOSX_DICT_LEGACY = {
    '5': 'Leopard',
    '6': 'Snow Leopard',
    '7': 'Lion',
    '8': 'Mountain Lion',
    '9': 'Mavericks',
    '10': 'Yosemite',
    '11': 'El Capitan',
    '12': 'Sierra',
    '13': 'High Sierra',
    '14': 'Mojave',
    '15': 'Catalina',
}
MACOSX_DICT_MODERN = {
    '11': 'Big Sur',
    '12': 'Monterey',
    '13': 'Ventura',
    '14': 'Sonoma',
    '15': 'Sequoia',
    '26': 'Tahoe',
}


def get_macos_locale():
    """Return the user's preferred locale on macOS, e.g. 'es_ES'.

    On macOS, locale.getlocale() reflects POSIX environment variables
    (LANG/LC_ALL), which are not set when the app is launched from
    Finder (as opposed to a terminal) and can be stale or inconsistent
    with the user's actual System Settings > General > Language & Region
    preference. AppleLocale, read via `defaults read -g AppleLocale`,
    reflects the real system preference regardless of how the app was
    launched.
    """
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleLocale'],
            capture_output=True, text=True, timeout=2, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        # SubprocessError covers TimeoutExpired, which is not an OSError.
        logger.debug('failed to read AppleLocale: %s', e)
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    if not value:
        return None
    # AppleLocale can include a variant suffix like 'es_ES@currency=EUR'.
    value = value.split('@')[0]
    return value or None


def notify_macos(msg):
    """Show a pop-up notification on macOS via osascript.

    The macOS GTK stack ships no libnotify typelib, so route the message
    through AppleScript's ``display notification``, which posts it to the
    system Notification Center.
    """
    if not IS_MAC:
        raise RuntimeError("notify_macos() is only for macOS")

    def _escape(text):
        # AppleScript string literals: escape backslash then double quote.
        return text.replace('\\', '\\\\').replace('"', '\\"')

    script = 'display notification "{}" with title "{}"'.format(
        _escape(msg), _escape(APP_NAME))
    try:
        subprocess.run(['osascript', '-e', script],
                       capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug('osascript notification failed: %s', e)


def macos_version_name(version=None):
    """Return the marketing/release name for a macOS version string, e.g. 'Tahoe'."""
    if version is None:
        if not hasattr(platform, 'mac_ver'):
            return None
        version = platform.mac_ver()[0]
    if not version:
        return None
    version_parts = version.split('.')
    version_major = version_parts[0]
    name = MACOSX_DICT_MODERN.get(version_major)
    if name is None and version_major == '10' and len(version_parts) > 1:
        name = MACOSX_DICT_LEGACY.get(version_parts[1])
    return name
