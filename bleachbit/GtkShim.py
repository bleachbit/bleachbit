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
Centralized GTK import handling.

This module handles importing GTK and related libraries (e.g., Gdk)
in a way that:
- Avoids crashes when GTK is unavailable
- Suppresses warning messages in non-GUI scenarios
- Provides a single source of truth for GTK availability

Scenarios when GTK is not needed or not available:
- CLI mode requested
- GTK/PyGObject not installed
- chroot
- crontab
- ssh
- limited environment variables (e.g., missing DISPLAY/XAUTHORITY)

Usage:
    from bleachbit.GtkShim import Gtk, Gdk, GObject, GLib, Gio, HAVE_GTK

    if HAVE_GTK:
        # do GTK stuff
"""

import logging
import os
import warnings

logger = logging.getLogger(__name__)

# Module-level GTK availability flag and placeholder objects
HAVE_GTK = False
gi = None
Gtk = None
Gdk = None
GObject = None
GLib = None
Gio = None

# Reason that GTK is unavailable
_gtk_unavailable_reason = None


def _check_display_available():
    """Check if a display server is available.

    Returns:
        tuple: (is_available: bool, reason: str or None)
    """
    if os.name == 'nt':
        # Windows always has a display
        return True, None

    # Check for X11 or Wayland display
    has_display = bool(
        os.environ.get('DISPLAY') or
        os.environ.get('WAYLAND_DISPLAY')
    )
    if not has_display:
        return False, 'No DISPLAY or WAYLAND_DISPLAY environment variable set'

    return True, None


def _try_import_gtk():
    """Attempt to import GTK and related libraries.

    Returns:
        tuple: (success: bool, reason: str or None)
    """
    global gi, Gtk, Gdk, GObject, GLib, Gio, HAVE_GTK

    # Suppress GTK warning messages during import
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Always try to import gi first (for gi.version reporting)
        try:
            import gi as _gi
            gi = _gi
        except ImportError:
            return False, 'PyGObject (gi) module not installed'

        # Check display availability before GTK imports (on POSIX)
        display_available, display_reason = _check_display_available()
        if not display_available:
            return False, display_reason

        try:
            gi.require_version('Gtk', '3.0')
        except ValueError as e:
            return False, f'GTK 3.0 not available: {e}'

        try:
            from gi.repository import Gtk as _Gtk
            from gi.repository import Gdk as _Gdk
            from gi.repository import GObject as _GObject
            from gi.repository import GLib as _GLib
            from gi.repository import Gio as _Gio

            Gtk = _Gtk
            Gdk = _Gdk
            GObject = _GObject
            GLib = _GLib
            Gio = _Gio

        except (ImportError, RuntimeError, ValueError) as e:
            return False, f'Failed to import GTK libraries: {e}'

        # On POSIX, verify we can actually get a display
        if os.name == 'posix':
            try:
                if Gdk.get_default_root_window() is None:
                    return False, 'No default root window (display not accessible)'
            except Exception as e:
                return False, f'Display check failed: {e}'

    return True, None


def _init_gtk():
    """Initialize GTK imports. Called once at module load."""
    global HAVE_GTK, _gtk_unavailable_reason

    success, reason = _try_import_gtk()
    HAVE_GTK = success
    _gtk_unavailable_reason = reason

    if not success and reason:
        logger.debug('GTK not available: %s', reason)


def get_gtk_unavailable_reason():
    """Return the reason GTK is unavailable, or None if available."""
    return _gtk_unavailable_reason


def require_gtk():
    """Raise an exception if GTK is not available.

    Use this in modules that absolutely require GTK (e.g., GUI modules).
    """
    if not HAVE_GTK:
        reason = _gtk_unavailable_reason or 'unknown reason'
        raise RuntimeError(f'GTK is required but not available: {reason}')


# Perform initialization at module load
_init_gtk()
