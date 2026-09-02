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

import gc
import getpass
import logging
import os
import shlex
import shutil
import stat
import subprocess
import sys
import xml.parsers.expat

import bleachbit
from bleachbit import IS_LINUX, IS_POSIX, IS_WINDOWS
from bleachbit.PathUtils import path_startswith

logger = logging.getLogger(__name__)


def _path_dir_is_root_safe(dirpath):
    """Return True if dirpath is absolute, root-owned, and not writable by others."""
    if not os.path.isabs(dirpath):
        return False
    try:
        st = os.stat(dirpath)
    except OSError:
        return False
    if st.st_uid != 0:
        return False
    if st.st_mode & stat.S_IWOTH:
        return False
    if (st.st_mode & stat.S_IWGRP) and st.st_gid != 0:
        return False
    return True


# Environment variables that make a child load code from a location the
# caller chose: the dynamic linker (LD_*, DYLD_*), glibc's loadable modules
# (honored because a sudo'd root process is not AT_SECURE), and the
# interpreters we may exec (dnf and yum are Python, paccache is a shell
# script).
_UNSAFE_ROOT_ENV_PREFIXES = ('LD_', 'DYLD_')
_UNSAFE_ROOT_ENV_VARS = (
    'GCONV_PATH', 'LOCPATH', 'NLSPATH', 'HOSTALIASES',
    'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONEXECUTABLE',
    'BASH_ENV', 'ENV', 'SHELLOPTS', 'BASHOPTS', 'IFS',
    'PERL5LIB', 'PERL5OPT', 'RUBYLIB', 'RUBYOPT', 'NODE_OPTIONS')


def sanitize_root_env(env):
    """Harden a child process's environment when running as root.

    Drop the code-loading variables listed above and PATH entries a non-root
    user could write, so an inherited hostile environment cannot redirect a
    privileged child. No-op unless euid 0.
    """
    if not hasattr(os, 'geteuid') or 0 != os.geteuid():
        return env
    env = {key: value for key, value in env.items()
           if key not in _UNSAFE_ROOT_ENV_VARS
           and not key.startswith(_UNSAFE_ROOT_ENV_PREFIXES)}
    path = env.get('PATH')
    if path:
        env['PATH'] = os.pathsep.join(
            d for d in path.split(os.pathsep) if _path_dir_is_root_safe(d))
    return env


def sanitize_surrogates(text):
    """Replace surrogates so the text can be encoded.

    Surrogates (like \\udcd6) come from filenames the filesystem returned
    as undecodable, and raise UnicodeEncodeError in GTK and on stdout.
    """
    return text.encode('utf-8', errors='replace').decode('utf-8')


_STANDARD_EXE_DIRS = ('/usr/bin', '/usr/sbin', '/bin', '/sbin')


def resolve_exe(name, *candidates):
    """Return an absolute path to an executable, or name if none is found.

    Checks the standard directories, or the given candidates instead, before
    falling back to PATH for layouts that put the tool somewhere else (NixOS,
    Alpine, an unmerged /usr). Skips user-writable PATH entries when root.
    """
    if not candidates:
        candidates = tuple(os.path.join(d, name) for d in _STANDARD_EXE_DIRS)
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    search_path = os.environ.get('PATH') or os.defpath
    if hasattr(os, 'geteuid') and 0 == os.geteuid():
        search_path = os.pathsep.join(
            d for d in search_path.split(os.pathsep)
            if _path_dir_is_root_safe(d))
    return shutil.which(name, path=search_path) or name


#
# XML
#
def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
    if 'false' == value.lower():
        return False
    raise RuntimeError(f"Invalid boolean: '{value}'")


def getText(nodelist):
    """Return the text data in an XML node
    http://docs.python.org/library/xml.dom.minidom.html"""
    return "".join(
        node.data for node in nodelist if node.nodeType == node.TEXT_NODE
    )


def reject_xml_dtd(data, description='XML'):
    """Raise ValueError if data declares a DTD with an internal subset, to block entity-expansion attacks"""
    def on_doctype(_name, _sysid, _pubid, has_internal_subset):
        # external-only doctype (e.g. fontconfig's fonts.conf) is harmless: no ExternalEntityRefHandler is registered, so expat never fetches it
        if has_internal_subset:
            raise ValueError(
                f'DTD with an internal subset is not allowed in {description}')
    parser = xml.parsers.expat.ParserCreate()
    parser.StartDoctypeDeclHandler = on_doctype
    parser.Parse(data, True)


#
# General
#
class WindowsError(Exception):
    """Dummy class for non-Windows systems"""

    def __init__(self, winerror=None, *args, **kwargs):
        self.winerror = winerror
        super().__init__(*args, **kwargs)

    def __str__(self):
        return 'this is a dummy class for non-Windows systems'


def chownself(path):
    """Set path owner to real self when running in sudo.
    If sudo creates a path and the owner isn't changed, the
    owner may not be able to access the path."""
    if not IS_POSIX:
        return
    uid = get_real_uid()
    logger.debug('chown(%s, uid=%s)', path, uid)
    normalized_path = os.path.normpath(os.path.abspath(path))
    if normalized_path == '/root' or path_startswith(normalized_path, '/root'):
        logger.info('chown for path /root aborted')
        return
    try:
        # follow_symlinks=False (lchown) so a symlink planted at this path
        # cannot redirect the ownership change to its target.
        os.chown(path, uid, -1, follow_symlinks=False)
    except Exception:
        logger.exception('Error in chown() under chownself()')


def gc_collect():
    """Collect garbage

    On Windows after updating from Python 3.11 to Python 3.12 calling
        os.unlink() would fail on a file processed by SQLite3.
    PermissionError: [WinError 32] The process cannot access the file because it is being used
    by another process: '[...].sqlite'
    """
    if not IS_WINDOWS:
        return

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
    except OSError:
        logger.debug('/proc/self/exe is unreadable, so falling back to PATH')
    for py in ['python3', 'python']:
        py_which = shutil.which(py)
        if py_which:
            return py_which
    raise RuntimeError('Cannot find Python executable')


def get_real_username():
    """Get the real username when running in sudo mode

    On GitHub Actions, os.getlogin() returns
    OSError: [Errno 25] Inappropriate ioctl for device

    In Docker containers, getpass.getuser() may fail with KeyError.
    """
    if not IS_POSIX:
        raise RuntimeError('get_real_username() requires POSIX')
    sudo_user = os.getenv('SUDO_USER')
    if sudo_user:
        return sudo_user

    try:
        login = os.getlogin()
    except OSError:
        login = None

    # On macOS (e.g., GitHub Actions), os.getlogin() may return 'root'
    # because it reflects the owner of the controlling terminal rather
    # than the effective user.  Don't trust it in that case; fall through
    # to getpass.getuser(), which checks environment variables and pwd.
    # This mirrors the 'root' != login guard in get_real_uid().
    if login and 'root' != login:
        return login

    try:
        return getpass.getuser()
    except (KeyError, OSError):
        # Happens inside containers when UID lacks an /etc/passwd entry or
        # when getpass gives up because no username-related env vars exist.
        pass

    for env_var in ('LOGNAME', 'USER'):
        fallback = os.getenv(env_var)
        if fallback:
            return fallback

    return str(os.getuid())


def get_real_uid():
    """Get the real user ID when running in sudo mode"""

    if not IS_POSIX:
        raise RuntimeError('get_real_uid() requires POSIX')

    sudo_uid = os.getenv('SUDO_UID')
    if sudo_uid:
        if sudo_uid.isdecimal():
            return int(sudo_uid)
        logger.warning('ignoring non-numeric SUDO_UID: %r', sudo_uid)

    try:
        login = os.getlogin()
        # On Ubuntu 9.04 and 25.04, getlogin() under sudo returns non-root user.
        # On Fedora 11, getlogin() under sudo returns 'root'.
        # On Fedora 41, getlogin() under sudo returns non-root user.
        # On Fedora 11 and 41, getlogin() under su returns non-root user.
    except Exception:
        login = os.getenv('LOGNAME')

    if login:
        login = login.strip()

    if login and 'root' != login:
        # pwd does not exist on Windows, so global unconditional import
        # would cause a ModuleNotFoundError.
        import pwd  # pylint: disable=import-outside-toplevel
        try:
            return pwd.getpwnam(login).pw_uid
        except KeyError:
            # Docker containers may set LOGNAME to a raw UID that lacks a passwd entry.
            if login.isdecimal():
                return int(login)

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


def os_match(os_str, platform=sys.platform):
    """Return boolean whether operating system matches

    Keyword arguments:
    os_str -- the required operating system as written in XML
    platform -- used only for unit tests
    """
    # If blank, return true.
    if not os_str:
        return True
    # "darwin" is accepted as a deprecated alias for "macos"
    if os_str == 'darwin':
        logger.warning(
            'The os="darwin" attribute is deprecated; use os="macos" instead.')
        os_str = 'macos'
    # Otherwise, check platform.
    # Define the current operating system.
    if platform == 'darwin':
        current_os = ('macos', 'bsd', 'unix')
    elif platform == 'linux':
        current_os = ('linux', 'unix')
    elif platform.startswith('openbsd'):
        current_os = ('bsd', 'openbsd', 'unix')
    elif platform.startswith('netbsd'):
        current_os = ('bsd', 'netbsd', 'unix')
    elif platform.startswith('freebsd'):
        current_os = ('bsd', 'freebsd', 'unix')
    elif platform == 'win32':
        current_os = ('windows',)
    else:
        raise RuntimeError(f'Unknown operating system: {sys.platform}')
    # Compare current OS against required OS.
    return os_str in current_os


def _set_detached_kwargs(kwargs):
    """Add the Popen keywords that detach the child from this process."""
    if IS_WINDOWS:
        kwargs['creationflags'] = (
            kwargs.get('creationflags', 0) |
            subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        kwargs['start_new_session'] = True
    kwargs['close_fds'] = True


def run_external_nowait(args, env=None, kwargs=None):
    """Run an external program in the background. Return immediately.

    Do not issue a ResourceWarning.
    Ignore the output of the new process.

    Returns a boolean whether the process was started successfully.

    """
    if kwargs is None:
        kwargs = {}
    else:
        kwargs = dict(kwargs)
    if IS_POSIX:
        # Sanitized here too (not just in run_external()) since this
        # function is also called directly, bypassing that sanitization.
        env = sanitize_root_env(dict(os.environ) if env is None else env)
    try:
        _set_detached_kwargs(kwargs)
        process = subprocess.Popen(args,
                                   stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   env=env, **kwargs)
        process.returncode = 0
        if IS_WINDOWS:
            process._handle.Close()
            process._handle = None
        return True
    except Exception as e:
        logger.warning('Failed to start process %s: %s', args, e)
        return False


def run_external(args, stdout=None, env=None, clean_env=True, timeout=None, wait=True):
    """Run external command and return (return code, stdout, stderr)

    The caller must expand environment variables before calling this function.

    timeout is in seconds. On timeout, this function raises subprocess.TimeoutExpired.
    No tuple is returned in this case.

    If wait=False, the process will be started but not waited for, and (0, '', '') will be returned.
    """
    assert args is not None
    assert isinstance(args, (list, tuple))
    for arg in args:
        if arg is None:
            raise ValueError("Command argument cannot be None")
    assert args
    if not args[0]:
        raise ValueError("First command argument cannot be empty")
    if clean_env and isinstance(env, dict) and env:
        raise ValueError(
            "Cannot set environment variables when clean_env is True")
    logger.debug('running cmd %s', ' '.join(args))
    if stdout is None:
        stdout = subprocess.PIPE
    kwargs = {}
    encoding = bleachbit.stdout_encoding
    if IS_WINDOWS:
        # hide the 'DOS box' window
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        encoding = 'mbcs'
    if clean_env and IS_POSIX:
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

    if IS_POSIX:
        # When root, do not let an inherited PATH/LD_* redirect the child
        env = sanitize_root_env(dict(os.environ) if env is None else env)

    if not wait:
        if run_external_nowait(args, env=env, kwargs=kwargs):
            return (0, '', '')
        # Use fallback method.
        _set_detached_kwargs(kwargs)
        process = subprocess.Popen(args,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   stdin=subprocess.DEVNULL,
                                   env=env, **kwargs)
        process.returncode = 0
        return (0, '', '')

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

        return (process.returncode,
                str(out[0], encoding=encoding) if out[0] else '',
                str(out[1], encoding=encoding) if out[1] else '')


def shell_split(cmd):
    """Split a shell command into a list of arguments"""
    args0 = shlex.split(cmd, posix=IS_POSIX)
    args = []
    for arg in args0:
        if IS_WINDOWS and arg.startswith('"') and arg.endswith('"'):
            arg = arg[1:-1]
        args.append(arg)
    return args


def sudo_mode():
    """Return whether running in sudo mode"""
    if not IS_LINUX:
        return False

    # if 'root' == os.getenv('USER'):
        # gksu in Ubuntu 9.10 changes the username.  If the username is root,
        # we're practically not in sudo mode.
        # Fedora 13: os.getenv('USER') = 'root' under sudo
        # return False

    return os.getenv('SUDO_UID') is not None
