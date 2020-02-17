# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
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


def is_debugging_enabled_via_cli():
    """Return boolean whether user required debugging on the command line"""
    import sys
    return any(arg.startswith('--debug') for arg in sys.argv)


class DelayLog(object):
    def __init__(self):
        self.queue = []
        self.msg = ''

    def read(self):
        for msg in self.queue:
            yield msg
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
    import sys
    # On Microsoft Windows when running frozen without the console,
    # avoid py2exe redirecting stderr to bleachbit.exe.log by not
    # writing to stderr because py2exe redirects stderr to a file.
    #
    # sys.frozen = 'console_exe' means the console is shown, which
    # does not require special handling.
    if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
        sys.stderr = DelayLog()

    # debug if command line asks for it or if this a non-final release
    if is_debugging_enabled_via_cli():
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger_sh = logging.StreamHandler()
    logger.addHandler(logger_sh)
    return logger


def set_root_log_level():
    """Adjust the root log level

    This runs later in the application's startup process when the
    configuration is loaded or after a change via the GUI.
    """
    from bleachbit.Options import options
    is_debug = options.get('debug')
    root_logger = logging.getLogger('bleachbit')
    root_logger.setLevel(logging.DEBUG if is_debug else logging.INFO)


class GtkLoggerHandler(logging.Handler):
    def __init__(self, append_text):
        logging.Handler.__init__(self)
        self.append_text = append_text
        self.msg = ''
        self.update_log_level()

    def update_log_level(self):
        """Set the log level"""
        from bleachbit.Options import options
        if options.get('debug'):
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
