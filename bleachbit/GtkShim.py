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
- Avoids opening display sockets when they are not needed
- Provides a single source of truth for GTK availability

Scenarios in which GTK is not needed or not available:

- CLI mode explicitly requested
- Text User Interface (TUI) mode
- Non-GTK GUI environment (e.g., wxWidgets)
- GTK/PyGObject not installed
- chroot
- crontab
- SSH
- Limited environment variables (e.g., missing DISPLAY/XAUTHORITY)

Usage
=====

Consider two axes:

- Cost: cheap preconditions versus an expensive import
- Failure mode: return a Boolean versus raise an exception

Cheap exposure check
--------------------

- Does not open a display socket
- Checks only gi, typelib, and DISPLAY environment variables

::

    from bleachbit.GtkShim import gtk_may_be_available

    if gtk_may_be_available():
        self.add_option('clipboard', ...)  # exposure only

Expensive use, raise on failure
-------------------------------

- Opens a Wayland/X11 socket through a gi.repository import
- Raises on failure; use when about to call GTK::

    from bleachbit.GtkShim import require_gtk

    require_gtk()  # raises RuntimeError if GTK is unavailable
    from bleachbit.GtkShim import Gtk
    Gtk.RecentManager().get_default().purge_items()

Expensive use, return a Boolean
------------------------------

Use when about to import or run other GUI code and want to skip
cleanly instead of raising::

    from bleachbit.GtkShim import is_gtk_available

    if is_gtk_available():
        from bleachbit.GuiApplication import Bleachbit

Lazy attribute access
---------------------

``import bleachbit.GtkShim`` runs only the cheap preconditions. However,
``from bleachbit.GtkShim import Gtk`` (or Gdk/GObject/GLib/Gio) triggers
module-level ``__getattr__``, which calls ``_ensure_gtk_libraries()`` and
opens the display socket on first access.  Until that import succeeds,
``is_gtk_available()`` returns ``False`` and ``require_gtk()`` raises.

"""

import ctypes
import logging
import os
import sys
import tempfile
import warnings
import webbrowser
from contextlib import contextmanager
from pathlib import PureWindowsPath
from html import escape as esc
from traceback import format_exc

from bleachbit import bleachbit_exe_path, IS_POSIX, IS_WINDOWS

HELP_URL = 'https://link.bleachbit.org/get-help'
PYGOBJECT_URL = 'https://link.bleachbit.org/pygobject-lib-bin-error'

logger = logging.getLogger(__name__)

# Module-level GTK state.  See the module docstring for the distinction
# between the cheap preconditions (_gtk_preconditions_met) and the
# expensive gi.repository import (_gtk_libraries_imported).
gi = None
# Gtk, Gdk, GObject, GLib, Gio are intentionally NOT defined here as
# module-level names.  They are populated by _import_gtk_libraries()
# and accessed lazily via __getattr__ before that.

# Whether the cheap, non-GUI GTK preconditions have passed.
_gtk_preconditions_met = False

# Reason that GTK is unavailable
_gtk_unavailable_reason = None


def _fix_arg(arg):
    """Replace unpaired surrogates in an argument with the replacement char.

    Gdk.init_check() inside gi.overrides.Gdk reads sys.argv during import
    and fails with UnicodeEncodeError if arguments contain unpaired
    surrogates (e.g., Windows filenames). This sanitizes each argument.
    """
    return arg.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')


@contextmanager
def _patched_argv(transform):
    """Temporarily replace sys.argv with a transformed copy.

    Guarantees restoration even on exceptions.
    """
    original = sys.argv
    sys.argv = [transform(arg) for arg in sys.argv]
    try:
        yield
    finally:
        sys.argv = original


def path_has_lib_or_bin(path):
    """Check if any directory component is exactly 'lib' or 'bin'.

    This detects a PyGObject bug where certain directory names cause
    Gtk to fail to import.

    https://github.com/bleachbit/bleachbit/issues/1822
    https://github.com/bleachbit/bleachbit/issues/1978

    Returns the matched component name, or None.
    """
    if not path:
        return None

    try:
        parts = PureWindowsPath(path).parts
    except TypeError:
        return None

    for part in parts:
        if part and part.lower() in ('lib', 'bin'):
            return part.lower()
    return None


def _build_error_html(error, traceback_text=None):
    """Build an HTML error report string.

    Include traceback, system information, and a copyable bug-report block.

    It does not write to a file.
    """

    try:
        # Import here to avoid a circular import.
        from bleachbit.SystemInformation import get_system_information
        sysinfo_text = get_system_information()
    except Exception:
        sysinfo_text = '(unavailable)'

    bug_info = (
        f"Error: {error}\n\n"
        f"{traceback_text or ''}\n\n"  # It already has "Traceback:" header
        f"System information:\n{sysinfo_text}"
    )

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
<script type="text/javascript">
function copyBugReport() {{
  var textarea = document.getElementById('bug-report');
  var confirm = document.getElementById('copy-confirm');
  if (!textarea) {{
    return;
  }}
  textarea.focus();
  textarea.select();
  try {{
    document.execCommand('copy');
    if (confirm) {{
      confirm.style.display = 'inline';
      setTimeout(function() {{ confirm.style.display = 'none'; }}, 2000);
    }}
  }} catch (error) {{
  }}
}}
</script>
</head>
<body>
<h2>BleachBit cannot start</h2>
<p id="pygobject-unknown-error">BleachBit failed to load its graphical interface.</p>
<p>Error: {esc(str(error))}</p>
<p><a id="get-help" href="{esc(HELP_URL)}">Get help</a></p>
<h3>Copy this for a bug report</h3>
<p><button type="button" onclick="copyBugReport()">Copy to clipboard</button>
<span id="copy-confirm" style="display:none; color:green; margin-left:1em;">Copied!</span></p>
<textarea id="bug-report" rows="10" cols="80" readonly onclick="this.select()">{esc(bug_info)}</textarea>
</body>
</html>
"""


def _show_windows_error_dialog(title, html_content):
    """Show a concise error dialog on Windows and optionally save an HTML log.

    Prompts the user with Yes/No: if Yes, writes an HTML file to %TEMP% and
    opens it in the default browser.  If No, closes silently.
    """
    assert IS_WINDOWS
    prompt = (
        "BleachBit failed to load the graphical interface.\n\n"
        "This may be a bug or a broken installation."
        "\n\nSave error details to file and open in browser?"
    )
    try:
        MB_YESNO = 0x00000004
        MB_ICONERROR = 0x00000010
        IDYES = 6
        result = ctypes.windll.user32.MessageBoxW(
            0, prompt, title, MB_YESNO | MB_ICONERROR)
        if result == IDYES:
            tmp_dir = os.environ.get('TEMP', tempfile.gettempdir())
            html_path = os.path.join(tmp_dir, 'bleachbit_error.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            webbrowser.open(f'file:///{html_path}')
    except Exception as e:
        logger.error('Failed to show Windows error dialog: %s', e)


def _handle_gtk_import_error(error):
    """On Windows, show a helpful error dialog when GTK import fails."""
    if not IS_WINDOWS:
        return

    logger.error('GTK not available: %s\n%s', error, format_exc())
    html_content = _build_error_html(
        error, traceback_text=format_exc())
    _show_windows_error_dialog('BleachBit', html_content)


def _check_display_available():
    """Check if a display server is available.

    Returns:
        tuple: (is_available: bool, reason: str or None)
    """
    if IS_WINDOWS:
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


def _check_gtk_available():
    """Check the cheap GTK preconditions without importing gi.repository.

    See the module docstring for why the gi.repository import is deferred.
    This checks that ``gi`` is importable, the typelib version can be
    required, and a display server appears to be reachable.

    Returns:
        tuple: (success: bool, reason: str or None)
    """
    global gi

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Always try to import gi first (for gi.version reporting).
        # The top-level ``gi`` package itself does not open a display
        # connection; only ``gi.repository.Gtk``/``Gdk`` do.
        try:
            import gi as _gi
            gi = _gi
        except ImportError:
            return False, 'PyGObject (gi) module not installed'

        # Check display availability before GTK imports (on POSIX)
        display_available, display_reason = _check_display_available()
        if not display_available:
            return False, display_reason

        if path_has_lib_or_bin(bleachbit_exe_path) and hasattr(sys, 'frozen'):
            # Setting search path prevents crash when importing GTK
            # when application is run from directory with foldername lib or bin.
            typelib_dir = os.path.join(
                bleachbit_exe_path, 'lib', 'girepository-1.0')
            if os.path.isdir(typelib_dir):
                logger.debug('Setting typelib search path to: %s', typelib_dir)
                gi._gi.Repository.get_default().prepend_search_path(typelib_dir)
            else:
                logger.warning('Typelib directory not found: %s', typelib_dir)

        try:
            gi.require_version('Gtk', '3.0')
        except Exception as e:
            _handle_gtk_import_error(e)
            return False, f'GTK 3.0 not available: {e}'

    return True, None


def _import_gtk_libraries():
    """Import ``gi.repository`` GTK libraries and verify the display.

    This is the expensive counterpart to :func:`_check_gtk_available`.
    It is called lazily by :func:`_ensure_gtk_libraries` and thus by
    :func:`require_gtk` and module-level ``__getattr__``.

    Returns:
        tuple: (success: bool, reason: str or None)
    """
    global Gtk, Gdk, GObject, GLib, Gio

    if not _gtk_preconditions_met or gi is None:
        return False, _gtk_unavailable_reason or 'GTK preconditions not met'

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Gdk.init_check() inside gi.overrides.Gdk reads sys.argv during
        # import and fails with UnicodeEncodeError if arguments contain
        # unpaired surrogates (e.g., Windows filenames). Sanitize argv
        # temporarily, so the import can proceed.
        try:
            with _patched_argv(_fix_arg):
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
        if IS_POSIX:
            try:
                if Gdk.get_default_root_window() is None:
                    return False, 'No default root window (display not accessible)'
            except Exception as e:
                return False, f'Display check failed: {e}'

    return True, None


# Track whether the expensive gi.repository import has been attempted and
# whether it succeeded.  _gtk_libraries_imported gates the one-time
# attempt; _gtk_libraries_available caches its result for repeat callers.
_gtk_libraries_imported = False
_gtk_libraries_available = False


def _ensure_gtk_libraries():
    """Lazily import gi.repository GTK libraries once.

    Called by :func:`require_gtk`, :func:`is_gtk_available`, and
    module-level ``__getattr__``.  Returns whether the GTK libraries and
    display are available.  Does nothing when the cheap preconditions
    have failed.
    """
    global _gtk_libraries_imported, _gtk_libraries_available, _gtk_unavailable_reason
    if _gtk_libraries_imported:
        return _gtk_libraries_available
    if not _gtk_preconditions_met:
        return False
    _gtk_libraries_imported = True
    success, reason = _import_gtk_libraries()
    _gtk_libraries_available = success
    if not success:
        _gtk_unavailable_reason = reason
    return success


def _init_gtk():
    """Check cheap GTK preconditions when the module loads.

    The expensive gi.repository import is deferred to
    :func:`_ensure_gtk_libraries`; ``is_gtk_available()`` returns
    ``False`` and ``require_gtk()`` raises until it succeeds.
    """
    global _gtk_preconditions_met, _gtk_unavailable_reason

    _gtk_preconditions_met, _gtk_unavailable_reason = _check_gtk_available()

    if not _gtk_preconditions_met and _gtk_unavailable_reason:
        logger.debug('GTK not available: %s', _gtk_unavailable_reason)


def get_gtk_unavailable_reason():
    """Return the reason GTK is unavailable, or None if available."""
    return _gtk_unavailable_reason


def gtk_may_be_available():
    """Return whether the cheap GTK preconditions passed.

    Use this only when exposing operations that call :func:`require_gtk`
    immediately before using GTK.  GUI code should call
    :func:`is_gtk_available` or :func:`require_gtk` instead.
    """
    return _gtk_preconditions_met


def is_gtk_available():
    """Return whether GTK libraries and a display are actually available."""
    return _ensure_gtk_libraries()


def require_gtk():
    """Raise ``RuntimeError`` if GTK is not available.

    Triggers the lazy ``gi.repository`` import on its first call.  Use
    this in modules that absolutely require GTK (e.g., GUI modules).
    """
    if not _ensure_gtk_libraries():
        reason = _gtk_unavailable_reason or 'unknown reason'
        raise RuntimeError(f'GTK is required but not available: {reason}')


@contextmanager
def suppress_pygobject_asyncio_warnings():
    """Suppress known PyGObject asyncio warnings under Python 3.14+."""
    if sys.version_info < (3, 14):
        yield
        return
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*asyncio.AbstractEventLoopPolicy.*",
            category=DeprecationWarning)
        warnings.filterwarnings(
            "ignore",
            message=".*asyncio.get_event_loop_policy.*",
            category=DeprecationWarning)
        yield


@contextmanager
def suppress_pygobject_import_warnings():
    """Suppress ImportWarning from old-style PyGObject import hooks.

    Older PyGObject versions use a legacy importer for ``gi.repository``
    that triggers ``ImportWarning: DynamicImporter.exec_module() not found;
    falling back to load_module()`` under Python's modern import system.
    This is harmless but breaks imports when warnings are errors (e.g.,
    ``PYTHONWARNINGS=error`` in the test suite).
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*DynamicImporter.exec_module\\(\\) not found.*",
            category=ImportWarning)
        yield


# Names whose access triggers the lazy gi.repository import.
_LAZY_GTK_NAMES = frozenset(('Gtk', 'Gdk', 'GObject', 'GLib', 'Gio'))


def __getattr__(name):
    """Lazily import gi.repository GTK libraries on first attribute access.

    ``from bleachbit.GtkShim import Gtk`` (or Gdk/GObject/GLib/Gio)
    triggers this hook because those names are not defined at module
    level until :func:`_import_gtk_libraries` populates them.  See the
    module docstring for why this deferral matters.
    """
    if name in _LAZY_GTK_NAMES:
        _ensure_gtk_libraries()
        # On success the module global is populated by _import_gtk_libraries.
        # On failure the name is absent; return None so callers see a
        # falsy placeholder rather than an AttributeError from this import.
        return globals().get(name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


# Perform initialization at module load
_init_gtk()
