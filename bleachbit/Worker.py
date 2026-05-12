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

# standard imports
import logging
import math
import os
import re
import stat
import sys
import traceback

# first party imports
from bleachbit import DeepScan, FileUtilities
from bleachbit.Cleaner import backends
from bleachbit.Constant import EMPTY_SPACE_WARNING
from bleachbit.Language import get_text as _, nget_text as ngettext
from bleachbit.FileUtilities import close_delete_parent_lock

logger = logging.getLogger(__name__)

# DEBUG BUILD for issue #2046: cap detailed access denied diagnostics
_MAX_ACCESS_DENIED_DIAGNOSTICS = 10


def _get_file_permission_diagnostics(filepath):
    """Return list of diagnostic strings for file permission issues."""
    lines = []
    if not filepath:
        lines.append('No filename available for diagnostics.')
        return lines
    lines.append(f'Diagnostics for: {filepath}')
    if not os.path.exists(filepath):
        lines.append('File does not exist')
        return lines
    try:
        fstat = os.stat(filepath)
        mode = stat.filemode(fstat.st_mode)
        lines.append(
            f'File permissions: {mode} ({oct(stat.S_IMODE(fstat.st_mode))})')
    except OSError as e:
        lines.append(f'Cannot stat file: {e}')
        return lines
    if os.name == 'posix':
        import pwd
        from bleachbit.General import get_real_uid
        try:
            file_owner = pwd.getpwuid(fstat.st_uid).pw_name
        except (KeyError, OverflowError):
            file_owner = str(fstat.st_uid)
        current_uid = get_real_uid()
        lines.append(f'File owner: {file_owner} (uid {fstat.st_uid})')
        lines.append(f'Current user uid: {current_uid}')
        if fstat.st_uid != current_uid:
            lines.append('File owner does not match current user')
        lines.append(f'os.access R_OK: {os.access(filepath, os.R_OK)}')
        lines.append(f'os.access W_OK: {os.access(filepath, os.W_OK)}')
    elif os.name == 'nt':
        try:
            import win32security
            import win32api
            import win32file
            file_sd = win32security.GetFileSecurity(
                filepath, win32security.OWNER_SECURITY_INFORMATION)
            file_owner_sid = file_sd.GetSecurityDescriptorOwner()
            file_owner_name = win32security.LookupAccountSid(
                None, file_owner_sid)[0]
            file_owner_sid_str = win32security.ConvertSidToStringSid(
                file_owner_sid)
            lines.append(
                f'File owner: {file_owner_name} (SID: {file_owner_sid_str})')
            process_token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
            current_sid = win32security.GetTokenInformation(
                process_token, win32security.TokenUser)[0]
            current_name = win32security.LookupAccountSid(
                None, current_sid)[0]
            current_sid_str = win32security.ConvertSidToStringSid(current_sid)
            win32file.CloseHandle(process_token)
            lines.append(
                f'Current user: {current_name} (SID: {current_sid_str})')
            if file_owner_sid_str != current_sid_str:
                lines.append('File owner does not match current user')
        except Exception as e:
            lines.append(f'Could not check Windows file ownership: {e}')
    return lines


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
        self.access_denied_diag_count = 0
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
            if isinstance(e, OSError) and e.errno == ENOENT:
                # ENOENT (Error NO ENTry) means file not found.
                # Normalize Windows extended paths (\\?\) before logging
                # so the user sees the canonical form and tests avoid
                # double-backslash sequences.
                filename = e.filename
                if os.name == 'nt' and filename:
                    filename = FileUtilities.extended_path_undo(filename)
                # Do not show traceback.
                logger.error(_("File not found: %s"), filename)
            elif isinstance(e, OSError) and e.errno == EACCES:
                # EACCES (Error ACCESS) means access denied.
                # Do not show traceback.
                if e.strerror == "Access denied in delete_locked_file()":
                    # This comes from Windows.delete_locked_file()
                    logger.error(
                        _("Access denied when flagging file for later delete: %s"), e.filename)
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
                # DEBUG BUILD: enhanced diagnostics for issue #2046
                if self.access_denied_diag_count < _MAX_ACCESS_DENIED_DIAGNOSTICS:
                    self.access_denied_diag_count += 1
                    diag_lines = []
                    diag_lines.append(
                        f'--- Access denied diagnostic #{self.access_denied_diag_count} ---')
                    diag_lines.append(f'Error: {e}')
                    if e.filename:
                        diag_lines.append(f'Path: {e.filename}')
                    diag_lines.append(f'strerror: {e.strerror}')
                    # 2A: traceback to show where in the code
                    diag_lines.append('Traceback:')
                    diag_lines.append(traceback.format_exc())
                    # 2B: file permission diagnostics
                    if e.filename:
                        diag_lines.extend(
                            _get_file_permission_diagnostics(e.filename))
                    # 2D: issue reference
                    diag_lines.append('--- End diagnostic ---')
                    diag_text = '\n'.join(diag_lines)
                    self.ui.append_text(diag_text + '\n', 'error')
                elif self.access_denied_diag_count == _MAX_ACCESS_DENIED_DIAGNOSTICS:
                    cap_msg = 'Access denied diagnostics capped at %d. Further access denied errors will not show detailed diagnostics.' % _MAX_ACCESS_DENIED_DIAGNOSTICS
                    self.ui.append_text(cap_msg + '\n', 'error')
                    self.access_denied_diag_count += 1
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

    def run_delayed_op(self, operation, option_id):
        """Run one delayed operation"""
        self.ui.update_progress_bar(0.0)
        if 'empty_space' == option_id:
            # TRANSLATORS: 'empty' means 'unallocated'
            msg = _("Please wait. Wiping empty space.")
            self.ui.append_text(EMPTY_SPACE_WARNING)
            self.ui.append_text('\n\n')
            self.ui.append_text(
                _('To stop this process, press the abort button on the toolbar and wait.'))
            self.ui.append_text('\n\n')
            self.ui.append_text(
                _('If the application is force closed before the process is complete, '
                  'large files may remain on the disk, and they may use all available space. '
                  'To remove them, start BleachBit again.'))
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
                            'While wiping empty space, unexpected phase %d' % phase)
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
        4. Empty space"""
        self.deepscans = {}
        # prioritize
        self.delayed_ops = []
        for operation in self.operations:
            delayables = ['empty_space', 'memory']
            for delayable in delayables:
                if operation not in ('system', '_gui'):
                    continue
                if delayable in self.operations[operation]:
                    i = self.operations[operation].index(delayable)
                    del self.operations[operation][i]
                    priority = 99
                    if 'empty_space' == delayable:
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

        # After standard operations and deep scan, close the lock
        # of the parent directory.
        close_delete_parent_lock()

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

        # DEBUG BUILD: end-of-run diagnostics for issue #2046
        try:
            from bleachbit.SystemInformation import get_system_information
            sysinfo = get_system_information()
            diag_msg = '\n--- System Information ---\n%s\n--- End System Information ---\n' % sysinfo
            self.ui.append_text(diag_msg)
        except Exception as e:
            logger.error('Error getting system information: %s', e)

        try:
            from bleachbit.Process import enumerate_processes
            proc_lines = ['\n--- Running Processes (filtered) ---']
            match_count = 0
            for proc in enumerate_processes():
                if not re.search(r'fox|edge|chrom', proc.name, re.IGNORECASE):
                    continue
                match_count += 1
                user_flag = 'same_user' if proc.same_user else 'other_user'
                proc_lines.append(
                    f'{proc.pid}: {proc.name} ({user_flag})')
            if match_count == 0:
                proc_lines.append('(no matching processes found)')
            proc_lines.append('--- End Running Processes ---')
            proc_msg = '\n'.join(proc_lines)
            self.ui.append_text(proc_msg + '\n')
        except Exception as e:
            logger.error('Error enumerating processes: %s', e)

        self.ui.append_text(
            'Please share this information to help troubleshoot at https://github.com/bleachbit/bleachbit/issues/2046\n', 'error')

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
