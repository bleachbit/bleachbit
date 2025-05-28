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
Logging
"""

import logging
import sys


def is_debugging_enabled_via_cli():
    """Return boolean whether user required debugging on the command line"""
    return any(arg.startswith('--debug') for arg in sys.argv)


class DelayLog(object):
    def __init__(self):
        self.queue = []
        self.msg = ''

    def read(self):
        yield from self.queue
        self.queue = []

    def write(self, msg):
        self.msg += msg
        if self.msg[-1] == '\n':
            self.queue.append(self.msg)
            self.msg = ''


def init_log():
    """Set up the root logger

    This is one of the first steps in __init___
    """
    logger = logging.getLogger('bleachbit')
    # On Microsoft Windows when running frozen without the console,
    # avoid py2exe redirecting stderr to bleachbit.exe.log by not
    # writing to stderr because py2exe redirects stderr to a file.
    #
    # sys.frozen = 'console_exe' means the console is shown, which
    # does not require special handling.
    if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':  # pylint: disable=no-member
        sys.stderr = DelayLog()

    # debug if command line asks for it or if this a non-final release
    if is_debugging_enabled_via_cli():
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger_sh = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    logger_sh.setFormatter(console_formatter)
    logger.addHandler(logger_sh)

    # If --debug-log parameter was passed, set up the file handler here instead
    # of in CLI.py, so logs are captured from the very beginning.
    debug_log_path = None
    for i, arg in enumerate(sys.argv):
        # --debug-log /path/file format (space delimited)
        if arg == '--debug-log' and i + 1 < len(sys.argv):
            debug_log_path = sys.argv[i + 1]
            break
        # --debug-log=/path/file format (delimited with equals sign)
        if arg.startswith('--debug-log='):
            debug_log_path = arg.split('=', 1)[1]
            break

    if debug_log_path:
        file_handler = logging.FileHandler(debug_log_path)
        # Always use DEBUG level for log file.
        file_handler.setLevel(logging.DEBUG)
        # removed: %(name)s
        file_formatter = logging.Formatter(
            '%(asctime)s -  %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.debug('Debug log file initialized at %s', debug_log_path)

    return logger


def set_root_log_level(is_debug=False):
    """Adjust the root log level

    This runs later in the application's startup process when the
    configuration is loaded or after a change via the GUI.
    """
    root_logger = logging.getLogger('bleachbit')
    is_debug_effective = is_debug or is_debugging_enabled_via_cli()
    root_logger.setLevel(logging.DEBUG if is_debug_effective else logging.INFO)


class GtkLoggerHandler(logging.Handler):
    def __init__(self, append_text):
        logging.Handler.__init__(self)
        self.append_text = append_text
        self.msg = ''
        self.update_log_level()

    def update_log_level(self):
        """Set the log level"""
        from bleachbit.Options import options
        if is_debugging_enabled_via_cli() or options.get('debug'):
            self.min_level = logging.DEBUG
        else:
            self.min_level = logging.WARNING

    def emit(self, record):
        if record.levelno < self.min_level:
            return
        tag = 'error' if record.levelno >= logging.WARNING else None
        msg = record.getMessage()
        if record.exc_text:
            msg = msg + '\n' + record.exc_text
        self.append_text(msg + '\n', tag)

    def write(self, msg):
        self.msg += msg
        if self.msg[-1] == '\n':
            tag = None
            self.append_text(msg, tag)
            self.msg = ''
