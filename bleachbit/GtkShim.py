# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


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

import ctypes
import logging
import os
import tempfile
import warnings
import webbrowser
from pathlib import Path
from html import escape as esc
from traceback import format_exc

from bleachbit import bleachbit_exe_path

HELP_URL = 'https://link.bleachbit.org/get-help'
PYGOBJECT_URL = 'https://link.bleachbit.org/pygobject-lib-bin-error'

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


def path_has_lib_or_bin(path):
    """Check if any directory component is exactly 'lib' or 'bin'.

    This detects a PyGObject bug where certain directory names cause
    Gtk to fail to import.

    https://github.com/bleachbit/bleachbit/issues/1822
    https://github.com/bleachbit/bleachbit/issues/1978

    Returns the matched component name, or None.
    """
    p = Path(path)
    for part in p.parts:
        if part.lower() in ('lib', 'bin'):
            return part.lower()
    return None


def _build_error_html(error, is_lib_bin_bug, exe_path=None, traceback_text=None):
    """Build an HTML error report string.

    For the known lib/bin path bug, omit traceback and system information.
    For unknown errors, include traceback, system information, and a
    copyable bug-report block.

    It does not write to a file.
    """

    if is_lib_bin_bug:
        matched_name = path_has_lib_or_bin(exe_path) if exe_path else None
        if not matched_name:
            matched_name = 'lib/bin'
        body = f"""
<p>The installation folder contains a subfolder named
<b>{esc(matched_name)}</b>, which triggers a bug in a library BleachBit uses.</p>
<h3>Workaround</h3>
<p>Move BleachBit to a folder whose path does not contain
<code>lib</code> or <code>bin</code> as a folder name.</p>
<p>Current path: <code>{esc(exe_path or '')}</code></p>
<p><a href="{esc(PYGOBJECT_URL)}">More information</a></p>
"""
    else:
        try:
            # Import here to avoid a circular import.
            from bleachbit.SystemInformation import get_system_information
            sysinfo_text = get_system_information()
        except Exception:
            sysinfo_text = '(unavailable)'

        bug_info = (
            f"Error: {error}\n\n"
            f"Traceback:\n{traceback_text or '(none)'}\n\n"
            f"System information:\n{sysinfo_text}"
        )
        body = f"""
<p>Error: {esc(str(error))}</p>
<p><a id="get-help" href="{esc(HELP_URL)}">Get help</a></p>
<h3>Copy this for a bug report</h3>
<p><button type="button" onclick="copyBugReport()">Copy to clipboard</button>
<span id="copy-confirm" style="display:none; color:green; margin-left:1em;">Copied!</span></p>
<textarea id="bug-report" rows="10" cols="80" readonly onclick="this.select()">{esc(bug_info)}</textarea>
"""

    copy_script = """
<script>
function copyBugReport() {
  var textarea = document.getElementById('bug-report');
  var confirm = document.getElementById('copy-confirm');
  if (!textarea) {
    return;
  }
  textarea.focus();
  textarea.select();
  try {
    document.execCommand('copy');
    if (confirm) {
      confirm.style.display = 'inline';
      setTimeout(function() { confirm.style.display = 'none'; }, 2000);
    }
  } catch (error) {
  }
}
</script>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BleachBit Error</title>
<style>
body {{ font-family: sans-serif; margin: 2em; }}
pre {{ background: #f4f4f4; padding: 1em; overflow-x: auto; }}
textarea {{ width: 100%; font-family: monospace; }}
</style>
{copy_script}
</head>
<body>
<h2>BleachBit cannot start</h2>
<p id="pygobject-unknown-error">BleachBit failed to load its graphical interface.</p>
{body}
</body>
</html>
"""


def _show_windows_error_dialog(title, short_message, html_content):
    """Show a concise error dialog on Windows and optionally save an HTML log.

    Prompts the user with Yes/No: if Yes, writes an HTML file to %TEMP% and
    opens it in the default browser.  If No, closes silently.
    """
    try:
        MB_YESNO = 0x00000004
        MB_ICONERROR = 0x00000010
        IDYES = 6
        prompt = short_message + '\n\nSave error details to file and open in browser?'
        result = ctypes.windll.user32.MessageBoxW(
            0, prompt, title, MB_YESNO | MB_ICONERROR)
        if result == IDYES:
            tmp_dir = os.environ.get('TEMP', tempfile.gettempdir())
            html_path = os.path.join(tmp_dir, 'bleachbit_error.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            webbrowser.open(f'file:///{html_path}')
    except Exception:
        pass


def _handle_gtk_import_error(error):
    """On Windows, show a helpful error dialog when GTK import fails."""
    if os.name != 'nt':
        return

    matched = path_has_lib_or_bin(bleachbit_exe_path)
    if matched:
        short_message = (
            f"BleachBit cannot start.\n\n"
            f"The folder '{matched}' in the installation path triggers a known bug.\n"
            f"Move BleachBit to a path without 'lib' or 'bin' as a folder name."
        )
        logger.error(
            'GTK not available due to PyGObject lib/bin path bug: %s'
            '\nPath: %s', error, bleachbit_exe_path)
        html_content = _build_error_html(
            error, is_lib_bin_bug=True, exe_path=bleachbit_exe_path)
    else:
        short_message = (
            "BleachBit failed to load the graphical interface.\n\n"
            "This may be a bug or a broken installation."
        )
        logger.error('GTK not available: %s\n%s', error, format_exc())
        html_content = _build_error_html(
            error, is_lib_bin_bug=False, traceback_text=format_exc())

    _show_windows_error_dialog('BleachBit', short_message, html_content)


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
    global gi, Gtk, Gdk, GObject, GLib, Gio

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
            _handle_gtk_import_error(e)
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
            _handle_gtk_import_error(e)
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
