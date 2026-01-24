# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

import os
import threading

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
        notify = Notify.Notification.new('BleachBit', msg, 'bleachbit')
        notify.set_hint("desktop-entry", GLib.Variant('s', 'bleachbit'))
        try:
            notify.show()
        except gi.repository.GLib.GError as e:
            logger.debug('Notify.Notification.show() failed: %s', e)
            return
        notify.set_timeout(10000)


def notify_plyer(msg):
    """Show a pop-up notification.

    Linux distributions do not include plyer, so this is just for Windows.
    """
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
