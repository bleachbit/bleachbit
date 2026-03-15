# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import os
import threading
from enum import Enum
from typing import Optional

from bleachbit import APP_NAME
from bleachbit.GUI import logger
from bleachbit.GtkShim import GLib, Gdk, Gtk, gi


class WindowInfo:
    def __init__(self, x, y, width, height, monitor_model):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.monitor_model = monitor_model

    def __str__(self):
        return f"WindowInfo(x={self.x}, y={self.y}, width={self.width}, height={self.height}, monitor_model={self.monitor_model})"


def get_font_size_from_name(font_name):
    """Get the font size from the font name"""
    if not isinstance(font_name, str):
        return None
    if not font_name:
        return None
    try:
        number_part = font_name.split()[-1]
    except IndexError:
        return None
    if '.' in number_part:
        return int(float(number_part))
    try:
        size_int = int(number_part)
    except ValueError:
        return None
    if size_int < 1:
        return None
    return size_int


def get_window_info(window):
    """Get the geometry and monitor of a window.

    window: Gtk.Window

    https://docs.gtk.org/gdk3/method.Screen.get_monitor_at_window.html
    Deprecated since: 3.22
    Use gdk_display_get_monitor_at_window() instead.

    https://docs.gtk.org/gdk3/method.Display.get_monitor_at_window.html
    Available since: 3.22

    https://docs.gtk.org/gdk3/method.Screen.get_monitor_geometry.html
    Deprecated since: 3.22
    Use gdk_monitor_get_geometry() instead.

    https://docs.gtk.org/gdk3/method.Monitor.get_geometry.html
    Available since: 3.22

    Returns a Rectangle-like object with with extra `monitor_model`
    property with the monitor model string.
    """
    assert window is not None
    assert isinstance(window, Gtk.Window)
    gdk_window = window.get_window()
    display = Gdk.Display.get_default()
    assert display is not None
    monitor = display.get_monitor_at_window(gdk_window)
    assert monitor is not None
    geo = monitor.get_geometry()
    assert geo is not None
    assert isinstance(geo, Gdk.Rectangle)
    if display.get_n_monitors() > 0 and monitor.get_model():
        monitor_model = monitor.get_model()
    else:
        monitor_model = "(unknown)"
    return WindowInfo(geo.x, geo.y, geo.width, geo.height, monitor_model)


class ThemeChangeStatus(Enum):
    """State machine for detecting whether a theme update occurred."""

    CHANGED = "changed"
    UNCHANGED = "unchanged"
    UNKNOWN = "unknown"


def detect_dark_background(widget: Optional[Gtk.Widget]) -> Optional[bool]:
    """Return True if the widget background is dark, False if light, None on failure."""
    threshold = 0.45
    if widget is None:
        return None

    try:
        style_context = widget.get_style_context()
        rgba = None
        if style_context is not None and hasattr(style_context, 'lookup_color'):
            lookup = style_context.lookup_color('theme_bg_color')
            if lookup:
                rgba = lookup[-1] if isinstance(lookup, tuple) else lookup

        if rgba is None:
            return None

        luminance = 0.2126 * rgba.red + 0.7152 * rgba.green + 0.0722 * rgba.blue
        is_dark = luminance < threshold
        # logger.debug("Detected widget luminance=%f -> dark=%s", luminance, is_dark)
        return is_dark
    except Exception:
        logger.debug("Failed to detect widget background", exc_info=True)
        return None


def classify_theme_change(before_dark: Optional[bool], after_dark: Optional[bool]) -> ThemeChangeStatus:
    """Compare observations before and after a toggle to classify change."""
    if before_dark is None or after_dark is None:
        return ThemeChangeStatus.UNKNOWN
    if before_dark == after_dark:
        return ThemeChangeStatus.UNCHANGED
    return ThemeChangeStatus.CHANGED


def should_show_dark_mode_warning(before_dark: Optional[bool], after_dark: Optional[bool]) -> bool:
    """Return True when we should warn the user about theme toggles."""
    status = classify_theme_change(before_dark, after_dark)
    # Warn when the theme did not change or when we cannot tell (UNKNOWN).
    return status != ThemeChangeStatus.CHANGED


def flush_gtk_events(max_iterations: int = 5):
    """Process pending GTK events to allow style updates to land."""
    iterations = 0
    while Gtk.events_pending() and (max_iterations is None or iterations < max_iterations):
        Gtk.main_iteration_do(False)
        iterations += 1


def notify(msg):
    """Show a popup-notification"""
    import importlib
    if importlib.util.find_spec('plyer'):
        # On Windows, use Plyer.
        notify_plyer(msg)
        return
    # On Linux, use GTK Notify.
    notify_gi(msg)


def notify_gi(msg):
    """Show a pop-up notification.

    The Windows pygy-aio installer does not include notify, so this is just for Linux.
    """
    try:
        gi.require_version('Notify', '0.7')
    except ValueError as e:
        logger.debug('gi.require_version("Notify", "0.7") failed: %s', e)
        return
    from gi.repository import Notify
    if Notify.init(APP_NAME):
        notification_obj = Notify.Notification.new(
            'BleachBit', msg, 'bleachbit')
        notification_obj.set_hint(
            "desktop-entry", GLib.Variant('s', 'bleachbit'))
        try:
            notification_obj.show()
        except gi.repository.GLib.GError as e:
            logger.debug('Notify.Notification.show() failed: %s', e)
            return
        notification_obj.set_timeout(10000)


def notify_plyer(msg):
    """Show a pop-up notification.

    Linux distributions do not include plyer, so this is just for Windows.
    """
    if not os.name == 'nt':
        raise RuntimeError("notify_plyer() is only for Windows")
    from bleachbit import bleachbit_exe_path

    # On Windows 10,  PNG does not work.
    __icon_fns = (
        os.path.normpath(os.path.join(bleachbit_exe_path,
                                      'share\\bleachbit.ico')),
        os.path.normpath(os.path.join(bleachbit_exe_path,
                                      'windows\\bleachbit.ico')))

    icon_fn = None
    for __icon_fn in __icon_fns:
        if os.path.exists(__icon_fn):
            icon_fn = __icon_fn
            break

    from plyer import notification
    notification.notify(
        title=APP_NAME,
        message=msg,
        app_name=APP_NAME,  # not shown on Windows 10
        app_icon=icon_fn,
    )


def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    return wrapper
