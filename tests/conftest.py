# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Under plain `pytest`, tests.TestAll's temp-dir wrapper never runs, so
subprocess-spawning tests (e.g. TestCLI.py) would otherwise inherit the
real BleachBit config dir. Set a per-worker one before any test module
(and therefore bleachbit, which reads this at import time) is imported.
"""

import logging
import os
import shutil
import tempfile

# BleachBit's atexit handlers (delete-lock cleanup, GTK nonce cleanup) log
# after pytest has closed its capture streams, printing harmless
# "I/O operation on closed file" errors. Don't surface those.
logging.raiseExceptions = False

_worker = os.environ.get('PYTEST_XDIST_WORKER')
_dir = os.environ.get('BLEACHBIT_TEST_OPTIONS_DIR')
# The controller sets the env var before spawning workers, so every worker
# inherits it. Without keying on the worker id they would all share one
# config dir and race on the same bleachbit.ini.
if _worker and (not _dir or _worker not in os.path.basename(_dir)):
    os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = tempfile.mkdtemp(
        prefix=f'bleachbit-test-{_worker}-', dir=_dir or None)
elif not _dir:
    os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = tempfile.mkdtemp(
        prefix='bleachbit-test-master-')


def pytest_sessionfinish(session, exitstatus):
    options_dir = os.environ.get('BLEACHBIT_TEST_OPTIONS_DIR')
    if options_dir and os.path.isdir(options_dir):
        shutil.rmtree(options_dir, ignore_errors=True)
