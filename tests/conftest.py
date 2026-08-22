# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Under plain `pytest`, tests.TestAll's temp-dir wrapper never runs, so
subprocess-spawning tests (e.g. TestCLI.py) would otherwise inherit the
real BleachBit config dir. Set per-worker config and temporary directories
before any test module (and therefore bleachbit) is imported.

The worker-specific directory is also removed at interpreter exit
(pytest_sessionfinish is not called for --collect-only or when the session
is interrupted).
"""

import atexit
import logging
import os
import shutil
import tempfile

# BleachBit's atexit handlers (delete-lock cleanup, GTK nonce cleanup) log
# after pytest has closed its capture streams, printing harmless
# "I/O operation on closed file" errors. Don't surface those.
logging.raiseExceptions = False

_worker = os.environ.get('PYTEST_XDIST_WORKER')
_options_dir = os.environ.get('BLEACHBIT_TEST_OPTIONS_DIR')
# The controller sets the env var before spawning workers, so every worker
# inherits it. Without keying on the worker id they would all share one
# config dir and race on the same bleachbit.ini.
if _worker:
    if not _options_dir or _worker not in os.path.basename(_options_dir):
        _options_dir = tempfile.mkdtemp(
            prefix=f'bleachbit-test-{_worker}-', dir=_options_dir or None)
        os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = _options_dir
    # Give each worker a private temporary directory so that tests
    # spawning subprocesses and Windows %TEMP%-based cleaners do
    # not race on the shared system temp.
    for _env_var in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[_env_var] = _options_dir
    tempfile.tempdir = _options_dir
elif not _options_dir:
    _options_dir = tempfile.mkdtemp(prefix='bleachbit-test-master-')
    os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = _options_dir


def _remove_options_dir():
    """Remove the temporary directory created for this process."""
    if _options_dir and os.path.isdir(_options_dir):
        shutil.rmtree(_options_dir, ignore_errors=True)


# The interpreter exits without a session when pytest is interrupted or
# invoked with --collect-only, so sessionfinish alone would leak the
# directory. Clean up here as a fallback (sessionfinish below handles the
# normal case; a second removal is a no-op).
atexit.register(_remove_options_dir)


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temporary directory after the test session."""
    _remove_options_dir()
