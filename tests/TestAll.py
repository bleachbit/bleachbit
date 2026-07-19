# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Run all test suites

Usage:
    python3 -m tests.TestAll
"""

import os
import unittest
import sys
import tempfile
import time


try:
    from tests import common
except ImportError as e:
    print(f'Error importing tests: {e}')
    print('try python3 -m tests.TestAll')
    sys.exit(1)


def main():
    """Run all tests"""
    print("""You should use the unittest discovery, it's much nicer:
    python -m unittest discover -p Test*.py                       # run all tests
    python -m unittest tests.TestCLI                              # run only the CLI tests
    python -m unittest tests.TestCLI.CLITestCase.test_encoding    # run only a single test

    Or use pytest for more features:
    pytest -n auto tests/                                         # run all tests in parallel
    pytest tests/TestCLI.py                                       # run only the CLI tests
    pytest tests/TestCLI.py::CLITestCase::test_encoding           # run only a single test""")

    start_time = time.time()
    with tempfile.TemporaryDirectory(prefix='TestAll ' + __name__) as testdir:
        with common.set_temporary_env('BLEACHBIT_TEST_OPTIONS_DIR', testdir):
            suite = unittest.defaultTestLoader.discover(
                os.getcwd(), pattern='Test*.py')
            success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    print(f"\nTotal test time: {minutes} minutes {seconds:.2f} seconds")
    sys.exit(success is False)


if __name__ == '__main__':
    main()
