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
Perform the preview or delete operations
"""

from bleachbit import DeepScan, FileUtilities
from bleachbit.Cleaner import backends
from bleachbit.Language import get_text as _, nget_text as ngettext
from bleachbit.Options import options

import logging
import math
import sys
import os
import psutil
import sqlite3
import stat

logger = logging.getLogger(__name__)


class Worker:

    """Perform the preview or delete operations"""

    def __init__(self, ui, really_delete, operations):
        """Create a Worker

        ui: an instance with methods
            append_text()
            update_progress_bar()
            update_total_size()
            update_item_size()
            worker_done()
        really_delete: (boolean) preview or make real changes?
        operations: dictionary where operation-id is the key and
            operation-id are values
        """
        self.ui = ui
        self.really_delete = really_delete
        assert (isinstance(operations, dict))
        self.operations = operations
        self.size = 0
        self.total_bytes = 0
        self.total_deleted = 0
        self.total_errors = 0
        self.total_special = 0  # special operations
        self.yield_time = None
        self.is_aborted = False
        if 0 == len(self.operations):
            raise RuntimeError("No work to do")

    def abort(self):
        """Stop the preview/cleaning operation"""
        self.is_aborted = True

    def print_exception(self, operation):
        """Display exception"""
        # TRANSLATORS: This indicates an error.  The special keyword
        # %(operation)s will be replaced by 'firefox' or 'opera' or
        # some other cleaner ID.  The special keyword %(msg)s will be
        # replaced by a message such as 'Permission denied.'
        err = _("Exception while running operation '%(operation)s': '%(msg)s'") \
            % {'operation': operation, 'msg': str(sys.exc_info()[1])}

        logger.error(err, exc_info=True)
        self.total_errors += 1

    def execute(self, cmd, operation_option):
        """Execute or preview the command"""
        ret = None
        try:
            for ret in cmd.execute(self.really_delete):
                if True == ret or isinstance(ret, tuple):
                    # Temporarily pass control to the GTK idle loop,
                    # allow user to abort, and
                    # display progress (if applicable).
                    yield ret
                if self.is_aborted:
                    return
        except SystemExit:
            pass
        except Exception as e:
            from errno import ENOENT, EACCES
            if isinstance(e, sqlite3.DatabaseError):
                print(f"!!!SQLite error: {e}")
                self._log_firefox_diagnostics(operation_option, e)
            else:
                print(f"!!!Other error: {type(e).__name__}: {e}")

            if isinstance(e, OSError) and e.errno == ENOENT:
                # ENOENT (Error NO ENTry) means file not found.
                # Do not show traceback.
                logger.error(_("File not found: %s"), e.filename)
            elif isinstance(e, OSError) and e.errno == EACCES:

                # EACCES (Error ACCESS) means access denied.
                # Do not show traceback.
                if e.strerror == "Access denied in delete_locked_file()":
                    # This comes from Windows.delete_locked_file()
                    # The regular delete failed with WindowsError 5 or 32 before this
                    logger.error(
                        _("Access denied when flagging file for later delete: %s"), e.filename)
                    self._log_firefox_diagnostics(
                        operation_option, e,
                        delete_attempt_result='Regular delete failed (winerror 5 or 32), then MoveFileExW for reboot-delete also failed')
                elif e.strerror == "Access denied in delete_registry_value()":
                    # This comes from Windows.delete_registry_value()
                    logger.error(
                        _("Access denied when deleting registry value: %s"), e.filename)
                elif e.strerror == "Access denied in delete_registry_key()":
                    # This comes from Windows.delete_registry_key()
                    logger.error(
                        _("Access denied when deleting registry key: %s"), e.filename)
                else:
                    logger.error(_("Access denied: %s"), e.filename)
                    self._log_firefox_diagnostics(operation_option, e)
            else:
                # For other errors, show the traceback.
                msg = _('Error: {operation_option}: {command}')
                data = {'command': cmd, 'operation_option': operation_option}
                logger.error(msg.format(**data), exc_info=True)
            self.total_errors += 1
        else:
            if ret is None:
                return
            if isinstance(ret['size'], int):
                size = FileUtilities.bytes_to_human(ret['size'])
                self.size += ret['size']
                self.total_bytes += ret['size']
            else:
                size = "?B"

            if ret['path']:
                path = ret['path']
            else:
                path = ''

            line = "%s %s %s\n" % (ret['label'], size, path)
            self.total_deleted += ret['n_deleted']
            self.total_special += ret['n_special']
            if ret['label']:
                # the label may be a hidden operation
                # (e.g., win.shell.change.notify)
                self.ui.append_text(line)

    def clean_operation(self, operation):
        """Perform a single cleaning operation"""
        operation_options = self.operations[operation]
        assert (isinstance(operation_options, list))
        logger.debug("clean_operation('%s'), options = '%s'",
                     operation, operation_options)

        if not operation_options:
            return

        if self.really_delete and backends[operation].is_process_running():
            # TRANSLATORS: %s expands to a name such as 'Firefox' or 'System'.
            err = _("%s cannot be cleaned because it is currently running.  Close it, and try again.") \
                % backends[operation].get_name()
            self.ui.append_text(err + "\n", 'error')
            self.total_errors += 1
            return
        import time
        self.yield_time = time.time()

        total_size = 0
        for option_id in operation_options:
            self.size = 0
            assert (isinstance(option_id, str))
            # normal scan
            for cmd in backends[operation].get_commands(option_id):
                for ret in self.execute(cmd, '%s.%s' % (operation, option_id)):
                    if True == ret:
                        # Return control to PyGTK idle loop to keep
                        # it responding allow the user to abort
                        self.yield_time = time.time()
                        yield True
                if self.is_aborted:
                    break
                if time.time() - self.yield_time > 0.25:
                    if self.really_delete:
                        self.ui.update_total_size(self.total_bytes)
                    yield True
                    self.yield_time = time.time()

            self.ui.update_item_size(operation, option_id, self.size)
            total_size += self.size

            # deep scan
            for (path, search) in backends[operation].get_deep_scan(option_id):
                if '' == path:
                    path = os.path.expanduser('~')
                if search.command not in ('delete', 'shred'):
                    raise NotImplementedError(
                        'Deep scan only supports deleting or shredding now')
                if path not in self.deepscans:
                    self.deepscans[path] = []
                self.deepscans[path].append(search)
        self.ui.update_item_size(operation, -1, total_size)

    def _log_firefox_diagnostics(self, operation_option, exception, delete_attempt_result=None):
        """Emit extra diagnostics for Firefox-specific permission errors.
        
        Args:
            operation_option: The operation string (e.g., 'firefox.url_history')
            exception: The exception that occurred
            delete_attempt_result: For 'flagging file for later delete', what happened with regular delete
        """
        if not self._firefox_diag_enabled():
            return
        if not isinstance(operation_option, str) or not operation_option.startswith('firefox.'):
            return
        target_path = getattr(exception, 'filename', None)
        reason = getattr(exception, 'strerror', repr(exception))
        logger.debug('Firefox diagnostics enabled: operation=%s path=%s reason=%s',
                     operation_option, target_path, reason)

        # Log what happened with regular delete before flagging for later delete
        if delete_attempt_result:
            logger.debug('Firefox diagnostics: regular delete before flagging: %s', delete_attempt_result)

        # Check shredding status
        shred_enabled = options.get('shred')
        logger.debug('Firefox diagnostics: shredding enabled=%s', shred_enabled)

        if not target_path:
            logger.debug('Firefox diagnostics: target path missing')
        else:
            exists = os.path.exists(target_path)
            logger.debug('Firefox diagnostics: exists=%s', exists)
            if exists:
                try:
                    stat_result = os.stat(target_path)
                    size_bytes = stat_result.st_size
                    is_zero_bytes = size_bytes == 0
                    mode_octal = stat_result.st_mode
                    mode_text = stat.filemode(mode_octal)
                    logger.debug('Firefox diagnostics: size=%d bytes, is_zero_bytes=%s, mode=%o (%s), mtime=%d',
                                 size_bytes, is_zero_bytes, mode_octal, mode_text, int(stat_result.st_mtime))
                    if is_zero_bytes:
                        logger.debug('Firefox diagnostics: WARNING - file is 0 bytes!')

                    if os.name == 'nt':
                        file_attrs = getattr(stat_result, 'st_file_attributes', None)
                        if file_attrs is not None:
                            attr_flags = [
                                (0x0001, 'READONLY'),
                                (0x0002, 'HIDDEN'),
                                (0x0004, 'SYSTEM'),
                                (0x0010, 'DIRECTORY'),
                                (0x0020, 'ARCHIVE'),
                                (0x0040, 'DEVICE'),
                                (0x0080, 'NORMAL'),
                                (0x0100, 'TEMPORARY'),
                                (0x0200, 'SPARSE_FILE'),
                                (0x0400, 'REPARSE_POINT'),
                                (0x0800, 'COMPRESSED'),
                                (0x1000, 'OFFLINE'),
                                (0x2000, 'NOT_CONTENT_INDEXED'),
                                (0x4000, 'ENCRYPTED'),
                                (0x8000, 'INTEGRITY_STREAM'),
                                (0x20000, 'NO_SCRUB_DATA'),
                            ]
                            enabled_attrs = [name for mask, name in attr_flags if file_attrs & mask]
                            logger.debug('Firefox diagnostics: Windows file attributes=0x%05X (%s)',
                                         file_attrs,
                                         ', '.join(enabled_attrs) if enabled_attrs else 'none')
                except Exception as exc:
                    logger.debug('Firefox diagnostics: os.stat failed for %s: %s',
                                 target_path, exc)
                try:
                    with open(target_path, 'rb') as handle:
                        handle.read(0)
                    logger.debug('Firefox diagnostics: open() succeeded for %s', target_path)
                except Exception as exc:
                    logger.debug('Firefox diagnostics: open() failed for %s: %s',
                                 target_path, exc)

                # Check if file is a SQLite database and if it's corrupt
                if target_path.endswith('.sqlite'):
                    self._check_sqlite_integrity(target_path)

        # Check for processes that may be locking the file
        self._check_locking_processes(target_path)

        if os.name == 'nt':
            try:
                from win32com.shell import shell  # pylint: disable=import-error,no-name-in-module
                logger.debug('Firefox diagnostics: IsUserAnAdmin=%s', shell.IsUserAnAdmin())
            except Exception as exc:
                logger.debug('Firefox diagnostics: admin detection failed: %s', exc)

    def _check_sqlite_integrity(self, path):
        """Check SQLite database integrity and structure."""
        logger.debug('Firefox diagnostics: checking SQLite database: %s', path)
        try:
            import sqlite3 as sql
            conn = sql.connect(path, timeout=1)
            cursor = conn.cursor()

            # Check integrity
            try:
                cursor.execute('PRAGMA integrity_check')
                integrity_result = cursor.fetchone()
                is_corrupt = integrity_result[0] != 'ok'
                logger.debug('Firefox diagnostics: SQLite integrity_check=%s, is_corrupt=%s',
                             integrity_result[0], is_corrupt)
                if is_corrupt:
                    logger.debug('Firefox diagnostics: WARNING - database appears corrupt!')
            except Exception as exc:
                logger.debug('Firefox diagnostics: integrity_check failed: %s', exc)

            # Check for tables
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                table_names = [t[0] for t in tables]
                has_tables = len(tables) > 0
                logger.debug('Firefox diagnostics: has_tables=%s, table_count=%d, tables=%s',
                             has_tables, len(tables), table_names[:10])  # limit to 10
                if not has_tables:
                    logger.debug('Firefox diagnostics: WARNING - database has no tables!')
            except Exception as exc:
                logger.debug('Firefox diagnostics: table check failed: %s', exc)

            conn.close()
        except Exception as exc:
            logger.debug('Firefox diagnostics: SQLite open/check failed: %s', exc)

    def _check_locking_processes(self, target_path):
        """Check for processes that may be locking the file."""
        # List of Firefox-related process names to check
        firefox_processes = ['firefox.exe', 'firefox', 'plugin-container.exe', 
                             'plugin-container', 'firefox-esr', 'firefox-esr.exe']
        
        try:
            current_username = psutil.Process().username().lower()
        except Exception:
            current_username = None

        # Check for Firefox processes
        found_processes = []
        try:
            for proc in psutil.process_iter(['name', 'username', 'pid']):
                try:
                    name = proc.info.get('name', '').lower()
                    if name in firefox_processes:
                        username = proc.info.get('username', '')
                        if username:
                            username = username.lower()
                        same_user = username == current_username if current_username else 'unknown'
                        found_processes.append({
                            'name': name,
                            'pid': proc.info.get('pid'),
                            'same_user': same_user
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if found_processes:
                logger.debug('Firefox diagnostics: found %d Firefox-related processes: %s',
                             len(found_processes), found_processes)
            else:
                logger.debug('Firefox diagnostics: no Firefox-related processes found')
        except Exception as exc:
            logger.debug('Firefox diagnostics: process enumeration failed: %s', exc)

        # On Windows, try to find processes with open handles to the file
        if os.name == 'nt' and target_path:
            self._check_file_handles_windows(target_path)

    def _check_file_handles_windows(self, target_path):
        """On Windows, check for processes with open handles to the file."""
        try:
            # Normalize path for comparison
            target_lower = os.path.normpath(target_path).lower()
            locking_procs = []

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Check open files for this process
                    open_files = proc.open_files()
                    for f in open_files:
                        if os.path.normpath(f.path).lower() == target_lower:
                            locking_procs.append({
                                'name': proc.info.get('name'),
                                'pid': proc.info.get('pid'),
                                'path': f.path
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            if locking_procs:
                logger.debug('Firefox diagnostics: processes with handles to file: %s', locking_procs)
            else:
                logger.debug('Firefox diagnostics: no processes found with open handles to file')
        except Exception as exc:
            logger.debug('Firefox diagnostics: file handle check failed: %s', exc)

    def _firefox_diag_enabled(self):
        env_flag = os.environ.get('BLEACHBIT_FIREFOX_ACCESS_DIAG', '').lower()
        if env_flag in ('1', 'true', 'yes', 'on'):
            return True
        try:
            return options.get('firefox_access_diag')
        except Exception as exc:
            logger.debug('Firefox diagnostics: options access failed: %s', exc)
            return False

    def run_delayed_op(self, operation, option_id):
        """Run one delayed operation"""
        self.ui.update_progress_bar(0.0)
        if 'free_disk_space' == option_id:
            # TRANSLATORS: 'free' means 'unallocated'
            msg = _("Please wait.  Wiping free disk space.")
            self.ui.append_text(
                _('Wiping free disk space erases remnants of files that were deleted without shredding. It does not free up space.'))
            self.ui.append_text('\n')
        elif 'memory' == option_id:
            msg = _("Please wait.  Cleaning %s.") % _("Memory")
        else:
            raise RuntimeError("Unexpected option_id in delayed ops")
        self.ui.update_progress_bar(msg)
        for cmd in backends[operation].get_commands(option_id):
            for ret in self.execute(cmd, '%s.%s' % (operation, option_id)):
                if isinstance(ret, tuple):
                    # Display progress (for free disk space)
                    phase = ret[0]
                    # A while ago there were other phase numbers. Currently it's just 1
                    if phase != 1:
                        raise RuntimeError(
                            'While wiping free space, unexpected phase %d' % phase)
                    percent_done = ret[1]
                    eta_seconds = ret[2]
                    self.ui.update_progress_bar(percent_done)
                    if isinstance(eta_seconds, int):
                        eta_mins = math.ceil(eta_seconds / 60)
                        msg2 = ngettext("About %d minute remaining.",
                                        "About %d minutes remaining.", eta_mins) \
                            % eta_mins
                        self.ui.update_progress_bar(msg + ' ' + msg2)
                    else:
                        self.ui.update_progress_bar(msg)
                if self.is_aborted:
                    break
                if True == ret or isinstance(ret, tuple):
                    # Return control to PyGTK idle loop to keep
                    # it responding and allow the user to abort.
                    yield True

    def run(self):
        """Perform the main cleaning process which has these phases
        1. General cleaning
        2. Deep scan
        3. Memory
        4. Free disk space"""
        self.deepscans = {}
        # prioritize
        self.delayed_ops = []
        for operation in self.operations:
            delayables = ['free_disk_space', 'memory']
            for delayable in delayables:
                if operation not in ('system', '_gui'):
                    continue
                if delayable in self.operations[operation]:
                    i = self.operations[operation].index(delayable)
                    del self.operations[operation][i]
                    priority = 99
                    if 'free_disk_space' == delayable:
                        priority = 100
                    new_op = (priority, {operation: [delayable]})
                    self.delayed_ops.append(new_op)

        # standard operations
        import warnings
        with warnings.catch_warnings(record=True) as ws:
            # This warning system allows general warnings. Duplicate will
            # be removed, and the warnings will show near the end of
            # the log.

            warnings.simplefilter('once')
            for _dummy in self.run_operations(self.operations):
                # yield to GTK+ idle loop
                yield True
            for w in ws:
                logger.warning(w.message)

        # run deep scan
        if self.deepscans:
            yield from self.run_deep_scan()

        # delayed operations
        for op in sorted(self.delayed_ops):
            operation = list(op[1].keys())[0]
            for option_id in list(op[1].values())[0]:
                for _ret in self.run_delayed_op(operation, option_id):
                    # yield to GTK+ idle loop
                    yield True

        # print final stats
        bytes_delete = FileUtilities.bytes_to_human(self.total_bytes)

        if self.really_delete:
            # TRANSLATORS: This refers to disk space that was
            # really recovered (in other words, not a preview)
            line = _("Disk space recovered: %s") % bytes_delete
        else:
            # TRANSLATORS: This refers to a preview (no real
            # changes were made yet)
            line = _("Disk space to be recovered: %s") % bytes_delete
        self.ui.append_text("\n%s" % line)
        if self.really_delete:
            # TRANSLATORS: This refers to the number of files really
            # deleted (in other words, not a preview).
            line = _("Files deleted: %d") % self.total_deleted
        else:
            # TRANSLATORS: This refers to the number of files that
            # would be deleted (in other words, simply a preview).
            line = _("Files to be deleted: %d") % self.total_deleted
        self.ui.append_text("\n%s" % line)
        if self.total_special > 0:
            line = _("Special operations: %d") % self.total_special
            self.ui.append_text("\n%s" % line)
        if self.total_errors > 0:
            line = _("Errors: %d") % self.total_errors
            self.ui.append_text("\n%s" % line, 'error')
        self.ui.append_text('\n')

        if self.really_delete:
            self.ui.update_total_size(self.total_bytes)
        self.ui.worker_done(self, self.really_delete)

        yield False

    def run_deep_scan(self):
        """Run deep scans"""
        logger.debug(' deepscans=%s' % self.deepscans)
        # TRANSLATORS: The "deep scan" feature searches over broad
        # areas of the file system such as the user's whole home directory
        # or all the system executables.
        self.ui.update_progress_bar(_("Please wait.  Running deep scan."))
        yield True  # allow GTK to update the screen
        ds = DeepScan.DeepScan(self.deepscans)

        for cmd in ds.scan():
            if True == cmd:
                yield True
                continue
            for _ret in self.execute(cmd, 'deepscan'):
                yield True

    def run_operations(self, my_operations):
        """Run a set of operations (general, memory, free disk space)"""
        for count, operation in enumerate(my_operations):
            self.ui.update_progress_bar(1.0 * count / len(my_operations))
            name = backends[operation].get_name()
            if self.really_delete:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Cleaning %s.") % name
            else:
                # TRANSLATORS: %s is replaced with Firefox, System, etc.
                msg = _("Please wait.  Previewing %s.") % name
            self.ui.update_progress_bar(msg)
            yield True  # show the progress bar message now
            try:
                for _dummy in self.clean_operation(operation):
                    yield True
            except:
                self.print_exception(operation)
