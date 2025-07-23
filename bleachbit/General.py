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
General code
"""

import getpass
import logging
import os
import shlex
import shutil
import subprocess
import sys

import bleachbit

logger = logging.getLogger(__name__)


#
# XML
#
def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError("Invalid boolean: '%s'" % value)


def getText(nodelist):
    """Return the text data in an XML node
    http://docs.python.org/library/xml.dom.minidom.html"""
    rc = "".join(
        node.data for node in nodelist if node.nodeType == node.TEXT_NODE
    )
    return rc


#
# General
#
class WindowsError(Exception):
    """Dummy class for non-Windows systems"""

    def __init__(self, winerror=None, *args, **kwargs):
        self.winerror = winerror
        super(WindowsError, self).__init__(*args, **kwargs)

    def __str__(self):
        return 'this is a dummy class for non-Windows systems'


def chownself(path):
    """Set path owner to real self when running in sudo.
    If sudo creates a path and the owner isn't changed, the
    owner may not be able to access the path."""
    if 'posix' != os.name:
        return
    uid = get_real_uid()
    logger.debug('chown(%s, uid=%s)', path, uid)
    if 0 == path.find('/root'):
        logger.info('chown for path /root aborted')
        return
    try:
        os.chown(path, uid, -1)
    except:
        logger.exception('Error in chown() under chownself()')


def gc_collect():
    """Collect garbage

    On Windows after updating from Python 3.11 to Python 3.12 calling
        os.unlink() would fail on a file processed by SQLite3.
    PermissionError: [WinError 32] The process cannot access the file because it is being used
    by another process: '[...].sqlite'
    """
    if not os.name == 'nt':
        return

    import gc
    gc.collect()


def get_executable():
    """Return the absolute path to the executable

    The executable is either Python or, if frozen, then
    bleachbit.exe.

    When running under `env -i`, sys.executable is an empty string.
    """
    if sys.executable:
        # example: /usr/bin/python3
        return sys.executable
    # When running as unittest, sys.argv may look like this:
    # [' -m unittest', '-v', 'tests.TestGeneral']
    try:
        # example: /usr/bin/python3.12
        # Notice it ends with .12.
        return os.readlink('/proc/self/exe')
    except Exception:
        pass
    for py in ['python3', 'python']:
        py_which = shutil.which(py)
        if py_which:
            return py_which
    raise RuntimeError('Cannot find Python executable')


def get_real_username():
    """Get the real username when running in sudo mode

    On GitHub Actions, os.getlogin() returns
    OSError: [Errno 25] Inappropriate ioctl for device
    """
    if 'posix' != os.name:
        raise RuntimeError('get_real_username() requires POSIX')
    try:
        return os.getenv('SUDO_USER') or os.getlogin()
    except OSError:
        return getpass.getuser()


def get_real_uid():
    """Get the real user ID when running in sudo mode"""

    if 'posix' != os.name:
        raise RuntimeError('get_real_uid() requires POSIX')

    if os.getenv('SUDO_UID'):
        return int(os.getenv('SUDO_UID'))

    try:
        login = os.getlogin()
        # On Ubuntu 9.04 and 25.04, getlogin() under sudo returns non-root user.
        # On Fedora 11, getlogin() under sudo returns 'root'.
        # On Fedora 41, getlogin() under sudo returns non-root user.
        # On Fedora 11 and 41, getlogin() under su returns non-root user.
    except:
        login = os.getenv('LOGNAME')

    if login and 'root' != login:
        # pwd does not exist on Windows, so global unconditional import
        # would cause a ModuleNotFoundError.
        import pwd  # pylint: disable=import-outside-toplevel
        return pwd.getpwnam(login).pw_uid

    # os.getuid() returns 0 for sudo, so use it as a last resort.
    return os.getuid()


def makedirs(path):
    """Make directory recursively considering sudo permissions.
    'Path' should not end in a delimiter."""
    logger.debug('makedirs(%s)', path)
    if os.path.lexists(path):
        return
    parentdir = os.path.split(path)[0]
    if not os.path.lexists(parentdir):
        makedirs(parentdir)
    os.mkdir(path, 0o700)
    if sudo_mode():
        chownself(path)


def run_external_nowait(args, env=None, kwargs=None):
    """Run an external program in the background. Return immediately.

    Do not issue a ResourceWarning.
    Ignore the output of the new process.

    Returns a boolean whether the process was started successfully.

    """
    try:
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            # Set close_fds to True to prevent Python from tracking the process
            # Also prevents ResourceWarnings
            kwargs['close_fds'] = True
            try:
                # Start the process with explicit None for stdio to prevent handle inheritance
                process = subprocess.Popen(args,
                                           stdin=None,
                                           stdout=None,
                                           stderr=None,
                                           env=env, **kwargs)
                # Close the process handle to prevent ResourceWarning
                process.returncode = 0
                # This prevents the ResourceWarning in __del__
                process._handle.Close()
                process._handle = None
                return True
            except Exception as e:
                logger.warning('Failed to start process %s: %s', args, e)
                return False

        # Unix/Linux
        pid = os.fork()
        if pid == 0:
            # Child process
            try:
                # Detach from parent session
                os.setsid()
                # Redirect standard streams to devnull
                with open(os.devnull, 'w', encoding=bleachbit.stdout_encoding) as devnull:
                    os.dup2(devnull.fileno(), sys.stdout.fileno())
                    os.dup2(devnull.fileno(), sys.stderr.fileno())
                with open(os.devnull, 'r', encoding=bleachbit.stdout_encoding) as devnull:
                    os.dup2(devnull.fileno(), sys.stdin.fileno())
                # Set environment if needed
                if env:
                    os.environ.clear()
                    os.environ.update(env)
                os.execvp(args[0], args)
            except Exception:
                os._exit(1)
        else:
            return True
    except subprocess.TimeoutExpired:
        # This is good on Windows.
        return True
    except Exception as e:
        logger.warning('Failed to start process %s: %s', args, e)
        return False


def run_external(args, stdout=None, env=None, clean_env=True, timeout=None, wait=True):
    """Run external command and return (return code, stdout, stderr)

    The caller must expand environment variables before calling this function.

    If wait=False, the process will be started but not waited for, and (0, '', '') will be returned.
    """
    assert args is not None
    assert isinstance(args, (list, tuple))
    for arg in args:
        if arg is None:
            raise ValueError("Command argument cannot be None")
    assert len(args) > 0
    if not args[0]:
        raise ValueError("First command argument cannot be empty")
    if clean_env and isinstance(env, dict) and len(env) > 0:
        raise ValueError(
            "Cannot set environment variables when clean_env is True")
    logger.debug('running cmd %s', ' '.join(args))
    if stdout is None:
        stdout = subprocess.PIPE
    kwargs = {}
    encoding = bleachbit.stdout_encoding
    if sys.platform == 'win32':
        # hide the 'DOS box' window
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        encoding = 'mbcs'
    if clean_env and 'posix' == os.name:
        # Clean environment variables so that that subprocesses use English
        # instead of translated text. This helps when checking for certain
        # strings in the output.
        # https://github.com/bleachbit/bleachbit/issues/167
        # https://github.com/bleachbit/bleachbit/issues/168
        # dconf reset requires DISPLAY
        # https://github.com/bleachbit/bleachbit/issues/1096
        keep_env = ('PATH', 'HOME', 'LD_LIBRARY_PATH', 'TMPDIR',
                    'BLEACHBIT_TEST_OPTIONS_DIR', 'DISPLAY', 'DBUS_SESSION_BUS_ADDRESS')
        env = {key: value for key, value in os.environ.items()
               if key in keep_env}
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'

    if not wait:
        if run_external_nowait(args, env=env, kwargs=kwargs):
            return (0, '', '')
        # Use fallback method.
        kwargs['start_new_session'] = True

    with subprocess.Popen(args, stdout=stdout,
                          stderr=subprocess.PIPE, env=env, **kwargs) as process:
        try:
            out = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=timeout)
            raise
        except KeyboardInterrupt:
            out = process.communicate()
            print(out[0])
            print(out[1])
            raise

        if not wait:
            return (0, '', '')

        return (process.returncode,
                str(out[0], encoding=encoding) if out[0] else '',
                str(out[1], encoding=encoding) if out[1] else '')


def shell_split(cmd):
    """Split a shell command into a list of arguments"""
    args0 = shlex.split(cmd, posix=os.name == 'posix')
    args = []
    for arg in args0:
        if os.name == 'nt' and arg.startswith('"') and arg.endswith('"'):
            arg = arg[1:-1]
        args.append(arg)
    return args


def sudo_mode():
    """Return whether running in sudo mode"""
    if not sys.platform == 'linux':
        return False

    # if 'root' == os.getenv('USER'):
        # gksu in Ubuntu 9.10 changes the username.  If the username is root,
        # we're practically not in sudo mode.
        # Fedora 13: os.getenv('USER') = 'root' under sudo
        # return False

    return os.getenv('SUDO_UID') is not None
