
# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
Show system information
"""

# standard library
import configparser
import ctypes
import locale
import logging
import os
import platform
import sqlite3
import sys
from collections import OrderedDict

# local
import bleachbit
from bleachbit.General import get_executable

logger = logging.getLogger(__name__)


def get_gtk_info():
    """Get dictionary of information about GTK"""
    info = {}
    try:
        # pylint: disable=import-outside-toplevel
        import gi
    except ImportError:
        logger.debug('import gi failed')
        return info

    info['gi.version'] = gi.__version__
    try:
        gi.require_version('Gtk', '3.0')
    except ValueError:
        logger.debug(
            'gi.require_version failed: GTK 3.0 not found or not available')
        return info

    # pylint: disable=import-outside-toplevel
    try:
        from gi.repository import Gtk
    except (ImportError, ValueError):
        logger.debug('import Gtk failed: GTK 3.0 not found or not available')
        return info

    settings = Gtk.Settings.get_default()
    if not settings:
        logger.debug('GTK settings not found')
        return info

    info['GTK version'] = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
    info['GTK theme'] = settings.get_property('gtk-theme-name')
    info['GTK icon theme'] = settings.get_property('gtk-icon-theme-name')
    info['GTK prefer dark theme'] = settings.get_property(
        'gtk-application-prefer-dark-theme')
    info['GTK font name'] = settings.get_property('gtk-font-name')

    return info


def get_windows_display_info():
    """Get Windows display information including ClearType, display count, resolution, and DPI."""
    from ctypes import windll, byref, Structure, c_uint, c_ulong, c_wchar_p, create_unicode_buffer, sizeof, POINTER, WINFUNCTYPE, WinError
    from ctypes import WinDLL
    from winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, KEY_READ, EnumKey, CloseKey

    # Define Windows types and constants
    class RECT(Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

    class DEVMODEW(Structure):
        _fields_ = [
            ('dmDeviceName', c_wchar_p * 32),
            ('dmSpecVersion', ctypes.c_ushort),
            ('dmDriverVersion', ctypes.c_ushort),
            ('dmSize', ctypes.c_ushort),
            ('dmDriverExtra', ctypes.c_ushort),
            ('dmFields', ctypes.c_ulong),
            ('dmPositionX', ctypes.c_long),
            ('dmPositionY', ctypes.c_long),
            ('dmDisplayOrientation', ctypes.c_ulong),
            ('dmDisplayFixedOutput', ctypes.c_ulong),
            ('dmColor', ctypes.c_short),
            ('dmDuplex', ctypes.c_short),
            ('dmYResolution', ctypes.c_short),
            ('dmTTOption', ctypes.c_short),
            ('dmCollate', ctypes.c_short),
            ('dmFormName', c_wchar_p * 32),
            ('dmLogPixels', ctypes.c_ushort),
            ('dmBitsPerPel', ctypes.c_ulong),
            ('dmPelsWidth', ctypes.c_ulong),
            ('dmPelsHeight', ctypes.c_ulong),
            ('dmDisplayFlags', ctypes.c_ulong),
            ('dmDisplayFrequency', ctypes.c_ulong),
            ('dmICMMethod', ctypes.c_ulong),
            ('dmICMIntent', ctypes.c_ulong),
            ('dmMediaType', ctypes.c_ulong),
            ('dmDitherType', ctypes.c_ulong),
            ('dmReserved1', ctypes.c_ulong),
            ('dmReserved2', ctypes.c_ulong),
            ('dmPanningWidth', ctypes.c_ulong),
            ('dmPanningHeight', ctypes.c_ulong)
        ]

    info = {}

    # ClearType is enabled?
    try:
        try:
            key = OpenKey(HKEY_CURRENT_USER, r"Software\Microsoft\Avalon.Graphics", 0, KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = EnumKey(key, i)
                    with OpenKey(key, subkey_name) as subkey:
                        try:
                            cleartype_level, _ = QueryValueEx(subkey, 'ClearTypeLevel')
                            info[f'Display {subkey_name} ClearTypeLevel'] = cleartype_level
                        except WindowsError:
                            pass
                    i += 1
                except WindowsError:
                    break
        except FileNotFoundError:
            info['ClearType registry'] = 'Key not found (ClearType settings not available)'
        except Exception as e:
            info['ClearType registry error'] = str(e)
    except ImportError as e:
        info['ClearType check error'] = 'winreg module not available'

    # Font smoothing and ClearType information
    SPI_GETFONTSMOOTHING = 0x004A
    SPI_GETFONTSMOOTHINGTYPE = 0x200A
    FE_FONTSMOOTHINGCLEARTYPE = 0x0002
    font_smoothing = ctypes.c_uint(0)
    smoothing_type = ctypes.c_uint(0)
    try:

        if windll.user32.SystemParametersInfoW(SPI_GETFONTSMOOTHING, 0, byref(font_smoothing), 0):
            info['Font Smoothing Enabled'] = bool(font_smoothing.value)

            if windll.user32.SystemParametersInfoW(SPI_GETFONTSMOOTHINGTYPE, 0, byref(smoothing_type), 0):
                info['Font Smoothing Type'] = 'ClearType' if smoothing_type.value == FE_FONTSMOOTHINGCLEARTYPE else 'Standard'
    except Exception as e:
        info['Font smoothing API error'] = str(e)

    # Get display count and information
    class MONITORINFOEX(Structure):
                _fields_ = [
                    ('cbSize', c_ulong),
                    ('rcMonitor', RECT),
                    ('rcWork', RECT),
                    ('dwFlags', c_ulong),
                    ('szDevice', c_wchar_p * 32)
                ]

    # Check for font registry values
    try:
        font_reg_path = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
        font_key = OpenKey(HKEY_LOCAL_MACHINE, font_reg_path)

        # Add Segoe UI font values
        segoe_ui_fonts = [
            "Segoe UI (TrueType)",
            "Segoe UI Bold (TrueType)",
            "Segoe UI Bold Italic (TrueType)",
            "Segoe UI Italic (TrueType)",
            "Segoe UI Light (TrueType)",
            "Segoe UI Semibold (TrueType)",
            "Segoe UI Symbol (TrueType)",
            "Tahoma (TrueType)",
            "Tahoma Bold (TrueType)",
        ]

        for font_name in segoe_ui_fonts:
            try:
                value, _ = QueryValueEx(font_key, font_name)
                info[f'Font: {font_name}'] = value
            except WindowsError:
                info[f'Font: {font_name}'] = 'not found'
        CloseKey(font_key)

        # Check font substitution
        subst_reg_path = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes'
        subst_key = OpenKey(HKEY_LOCAL_MACHINE, subst_reg_path)

        for font_name in ('Segoe UI', 'Tahoma'):
            try:
                value, _ = QueryValueEx(subst_key, font_name)
                info[f'Font Substitute: {font_name}'] = value
            except WindowsError:
                info[f'Font Substitute: {font_name}'] = 'not found'
        CloseKey(subst_key)
    except Exception as e:
        info['Font registry error'] = str(e)

    try:
        try:
            MonitorEnumProc = WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                        POINTER(RECT), ctypes.c_double)

            display_count = [0]

            def enum_proc(hmonitor, hdc, lprect, lparam):
                display_count[0] += 1
                return 1

            # Enumerate all monitors
            ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(enum_proc), 0)
            info['Display Count'] = display_count[0]

            # Get display information for each display
            # Use DISPLAY_DEVICE structure to enumerate devices
            class DISPLAY_DEVICEW(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("DeviceName", ctypes.c_wchar * 32),
                    ("DeviceString", ctypes.c_wchar * 128),
                    ("StateFlags", ctypes.c_ulong),
                    ("DeviceID", ctypes.c_wchar * 128),
                    ("DeviceKey", ctypes.c_wchar * 128)
                ]

            i = 0
            while True:
                display_device = DISPLAY_DEVICEW()
                display_device.cb = ctypes.sizeof(DISPLAY_DEVICEW)
                if not ctypes.windll.user32.EnumDisplayDevicesW(None, i, ctypes.byref(display_device), 0):
                    break
                device_name = display_device.DeviceName
                device_string = display_device.DeviceString

                # Get display settings
                devmode = DEVMODEW()
                devmode.dmSize = ctypes.sizeof(DEVMODEW)
                if ctypes.windll.user32.EnumDisplaySettingsW(device_name, -1, ctypes.byref(devmode)):
                    info[f'Display {i} Name'] = device_name
                    info[f'Display {i} String'] = device_string
                    info[f'Display {i} Resolution'] = f"{devmode.dmPelsWidth}x{devmode.dmPelsHeight}"
                else:
                    info[f'Display {i} Name'] = device_name
                    info[f'Display {i} String'] = device_string
                    info[f'Display {i} Resolution'] = 'Unknown'

                # DPI and scale as before
                try:
                    shcore = WinDLL('shcore')
                    PROCESS_PER_MONITOR_DPI_AWARE = 2
                    shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
                    MONITOR_DEFAULTTONEAREST = 2
                    # Use MonitorFromPoint with a point inside the display
                    point = ctypes.wintypes.POINT(getattr(devmode, 'dmPositionX', 0) + 1, getattr(devmode, 'dmPositionY', 0) + 1)
                    hmonitor = ctypes.windll.user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)
                    dpiX = ctypes.c_uint()
                    dpiY = ctypes.c_uint()
                    shcore.GetDpiForMonitor(hmonitor, 0, ctypes.byref(dpiX), ctypes.byref(dpiY))
                    info[f'Display {i} DPI'] = f"{dpiX.value}x{dpiY.value}"
                    scale_x = round((dpiX.value / 96.0) * 100)
                    scale_y = round((dpiY.value / 96.0) * 100)
                    info[f'Display {i} Scale'] = f"{scale_x}% x {scale_y}%"
                except Exception:
                    hdc = ctypes.windll.user32.GetDC(0)
                    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                    dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)
                    ctypes.windll.user32.ReleaseDC(0, hdc)
                    scale_x = round((dpi_x / 96.0) * 100)
                    scale_y = round((dpi_y / 96.0) * 100)
                    info[f'Display {i} Scale (legacy)'] = f"{scale_x}% x {scale_y}%"
                i += 1

                # Get DPI information (Windows 8.1+)
                try:
                    shcore = WinDLL('shcore')
                    PROCESS_PER_MONITOR_DPI_AWARE = 2
                    shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

                    MONITOR_DEFAULTTONEAREST = 2
                    hmonitor = ctypes.windll.user32.MonitorFromPoint(
                        ctypes.wintypes.POINT(devmode.dmPosition.x + 1, devmode.dmPosition.y + 1),
                        MONITOR_DEFAULTTONEAREST)

                    dpiX = ctypes.c_uint()
                    dpiY = ctypes.c_uint()
                    shcore.GetDpiForMonitor(hmonitor, 0, byref(dpiX), byref(dpiY))
                    info[f'Display {i} DPI'] = f"{dpiX.value}x{dpiY.value}"

                    # Calculate scale percentage (assuming 96 DPI = 100%)
                    scale_x = round((dpiX.value / 96.0) * 100)
                    scale_y = round((dpiY.value / 96.0) * 100)
                    info[f'Display {i} Scale'] = f"{scale_x}% x {scale_y}%"

                except (OSError, AttributeError):
                    # Fallback for Windows versions before 8.1
                    hdc = ctypes.windll.user32.GetDC(0)
                    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                    dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
                    ctypes.windll.user32.ReleaseDC(0, hdc)

                    scale_x = round((dpi_x / 96.0) * 100)
                    scale_y = round((dpi_y / 96.0) * 100)
                    info[f'Display {i} Scale (legacy)'] = f"{scale_x}% x {scale_y}%"

                except Exception as e:
                    info[f'Display {i} error'] = str(e)
                    continue

        except Exception as e:
            info['Display enumeration error'] = str(e)

    except Exception as e:
        info['Windows display info error'] = str(e)

    return info


def get_windows_language_info():
    info = {}
    # Check Windows registry for code page settings
    try:
        import winreg
        reg_path = r'SYSTEM\CurrentControlSet\Control\Nls\CodePage'
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)

        for value_name in ('ACP', 'OEMCP', 'MACCP'):
            try:
                value, _ = winreg.QueryValueEx(registry_key, value_name)
                info[f'Windows Registry CodePage {value_name}'] = value
            except WindowsError:
                info[f'Windows Registry CodePage {value_name}'] = 'not found'

        winreg.CloseKey(registry_key)
    except Exception as e:
        info['Windows Registry error'] = str(e)

    # Get the Windows ANSI Code Page and OEM Code Page using the Windows API
    from ctypes import windll, byref, Structure, c_uint, c_wchar_p, create_unicode_buffer, sizeof, c_ulong

    class CPINFO(Structure):
        _fields_ = [("MaxCharSize", c_uint),
                    ("DefaultChar", c_uint * 2),
                    ("LeadByte", c_uint * 12)]
    cp_info = CPINFO()
    try:
        info['Windows API GetACP'] = str(windll.kernel32.GetACP())
        info['Windows API GetOEMCP'] = str(windll.kernel32.GetOEMCP())
        if windll.kernel32.GetCPInfo(windll.kernel32.GetACP(), byref(cp_info)):
            info['Windows API MaxCharSize'] = str(cp_info.MaxCharSize)

        # Get language information
        kernel32 = windll.kernel32
        lcid = kernel32.GetUserDefaultLCID()
        info['Windows LCID'] = str(lcid)

        # Get UI language preferences
        info['Windows GetUserDefaultUILanguage'] = str(
            kernel32.GetUserDefaultUILanguage())
    except Exception as e:
        info['Windows API part 1 language error'] = str(e)

    # Get preferred UI languages
    MUI_LANGUAGE_NAME = 0x8
    num_languages = c_ulong(0)
    buffer_size = c_ulong(0)

    try:
        # Get buffer size needed
        if kernel32.GetUserPreferredUILanguages(MUI_LANGUAGE_NAME, byref(num_languages), None, byref(buffer_size)):
            buffer = create_unicode_buffer(buffer_size.value)
            if kernel32.GetUserPreferredUILanguages(MUI_LANGUAGE_NAME, byref(num_languages), buffer, byref(buffer_size)):
                languages = []
                offset = 0
                for i in range(num_languages.value):
                    languages.append(buffer[offset:].split('\0')[0])
                    offset += len(languages[-1]) + 1
                info['Windows GetUserPreferredUILanguages'] = ", ".join(
                    languages)

        # Get thread preferred UI languages
        num_languages = c_ulong(0)
        buffer_size = c_ulong(0)
        if kernel32.GetThreadPreferredUILanguages(MUI_LANGUAGE_NAME, byref(num_languages), None, byref(buffer_size)):
            buffer = create_unicode_buffer(buffer_size.value)
            if kernel32.GetThreadPreferredUILanguages(MUI_LANGUAGE_NAME, byref(num_languages), buffer, byref(buffer_size)):
                languages = []
                offset = 0
                for i in range(num_languages.value):
                    languages.append(buffer[offset:].split('\0')[0])
                    offset += len(languages[-1]) + 1
                info['Windows GetThreadPreferredUILanguages'] = ", ".join(
                    languages)

    except Exception as e:
        info['Windows API part 2 language error'] = str(e)
    # Convert Windows LCID to RFC1766 (e.g., en-US).
    user_locale = locale.windows_locale.get(lcid, '')
    info['Windows locale'] = user_locale
    return info


def get_version(four_parts=False):
    """Return version information as a string.

    CI builds will have an integer build number.

    If four_parts is True, always return a four-part version string.
    If False, return three or four parts, depending on available information.
    """
    build_number_env = os.getenv('APPVEYOR_BUILD_NUMBER')
    build_number_src = None
    try:
        # pylint: disable=import-outside-toplevel
        from bleachbit.Revision import build_number as build_number_import
        build_number_src = build_number_import
    except ImportError:
        pass

    build_number = build_number_src or build_number_env
    if not build_number:
        if not four_parts:
            return bleachbit.APP_VERSION
        return f'{bleachbit.APP_VERSION}.0'
    assert build_number.isdigit()
    return f'{bleachbit.APP_VERSION}.{build_number}'


def get_system_information():
    """Return system information as a string."""

    info = OrderedDict()

    # Application and library versions
    info['BleachBit version'] = get_version()

    try:
        # CI builds and Linux tarball will have a revision.
        # pylint: disable=import-outside-toplevel
        from bleachbit.Revision import revision
        info['Git revision'] = revision
    except ImportError:
        pass

    info.update(get_gtk_info())

    info['SQLite version'] = sqlite3.sqlite_version

    # System environment information
    info['locale.getlocale'] = str(locale.getlocale())

    # check whether GTK_CONFIG_HOME exists
    # Linux: USER_CONFIG_HOME/gtk-3.0
    # Windows: %LOCALAPPDATA%\gtk-3.0
    # settings.ini may not work on Windows
    if os.name == 'nt':
        gtk_config_home = os.getenv('LOCALAPPDATA')
    else:
        gtk_config_home = os.getenv('XDG_CONFIG_HOME')
    if gtk_config_home:
        gtk_config_home = os.path.join(gtk_config_home, 'gtk-3.0')
        if os.path.exists(gtk_config_home):
            info['GTK_CONFIG_HOME'] = 'found'
            gtk_css = os.path.join(gtk_config_home, 'gtk.css')
            if os.path.exists(gtk_css):
                info['GTK_CSS'] = f"{os.path.getsize(gtk_css):,} bytes"
            else:
                info['GTK_CSS'] = 'not found'
            gtk_settings_ini = os.path.join(gtk_config_home, 'settings.ini')
            if os.path.exists(gtk_settings_ini):
                info['GTK_SETTINGS_INI'] = f"{os.path.getsize(gtk_settings_ini):,} bytes"
                config = configparser.ConfigParser()
                try:
                    config.read(gtk_settings_ini)
                    if 'Settings' in config and 'gtk-font-name' in config['Settings']:
                        info['GTK font name'] = config['Settings']['gtk-font-name']
                    else:
                        info['GTK font name'] = 'not found in settings.ini'
                except Exception as e:
                    info['GTK_SETTINGS_INI error'] = str(e)
            else:
                info['GTK_SETTINGS_INI'] = 'not found'
        else:
            info['GTK_CONFIG_HOME'] = 'not found'

    if os.name == 'nt':
        language_info = get_windows_language_info()
        if language_info:
            info.update(language_info)
        display_info = get_windows_display_info()
        if display_info:
            info.update(display_info)

    # Variables defined in __init__.py
    info['local_cleaners_dir'] = bleachbit.local_cleaners_dir
    info['locale_dir'] = bleachbit.locale_dir
    info['options_dir'] = bleachbit.options_dir
    info['personal_cleaners_dir'] = bleachbit.personal_cleaners_dir
    info['system_cleaners_dir'] = bleachbit.system_cleaners_dir

    # Environment variables
    if 'posix' == os.name:
        envs = ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID')
    elif 'nt' == os.name:
        envs = ('APPDATA', 'cd', 'LocalAppData', 'LocalAppDataLow', 'Music',
                'USERPROFILE', 'ProgramFiles', 'ProgramW6432', 'TMP')
    else:
        envs = ()

    for env in envs:
        info[f'os.getenv({env})'] = os.getenv(env)

    info['os.path.expanduser(~")'] = os.path.expanduser('~')

    # Mac Version Name - Dictionary
    macosx_dict = {'5': 'Leopard', '6': 'Snow Leopard', '7': 'Lion', '8': 'Mountain Lion',
                   '9': 'Mavericks', '10': 'Yosemite', '11': 'El Capitan', '12': 'Sierra'}

    if sys.platform == 'linux':
        from bleachbit.Unix import get_distribution_name_version
        info['get_distribution_name_version()'] = get_distribution_name_version()
    elif sys.platform.startswith('darwin'):
        if hasattr(platform, 'mac_ver'):
            mac_version = platform.mac_ver()[0]
            version_minor = mac_version.split('.')[1]
            if version_minor in macosx_dict:
                info['platform.mac_ver()'] = f'{mac_version} ({macosx_dict[version_minor]})'
    else:
        info['platform.uname().version'] = platform.uname().version

    # System information
    info['sys.argv'] = sys.argv
    info['sys.executable'] = get_executable()
    info['sys.version'] = sys.version
    if 'nt' == os.name:
        from win32com.shell import shell
        info['IsUserAnAdmin()'] = shell.IsUserAnAdmin()
    info['__file__'] = __file__

    # Render the information as a string
    return '\n'.join(f'{key} = {value}' for key, value in info.items())
