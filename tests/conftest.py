# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""pytest configuration shared by all test modules."""

import pytest


def _has_surrogate(value):
    """Return True if *value* is a str with a lone UTF-16 surrogate."""
    return isinstance(value, str) and any(
        '\ud800' <= c <= '\udfff' for c in value)


def _sanitize(value):
    """Replace lone UTF-16 surrogates with their ``\\uXXXX`` escape.

    Lone surrogates appear on Windows when filenames decoded with the
    ``surrogateescape`` error handler end up in test-failure tracebacks or
    captured log output.  They cannot be encoded as UTF-8, which breaks
    pytest-xdist's worker-to-master report serialization (execnet uses
    strict UTF-8) and aborts the whole session with INTERNALERROR.
    Sanitizing at the report level keeps the surrogate-filename test
    coverage while letting xdist transport the reports, so the real
    failure is surfaced instead of swallowed.
    """
    if not _has_surrogate(value):
        return value
    return ''.join(
        c if not ('\ud800' <= c <= '\udfff') else f'\\u{ord(c):04x}'
        for c in value)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # pylint: disable=unused-argument
    """Sanitize lone surrogates in test reports before xdist serializes them.

    This is the single chokepoint through which all test-report data
    (traceback, captured logs, captured stdout/stderr) flows before
    execnet serializes it with strict UTF-8.  Replacing the structured
    longrepr with a sanitized plain string is sufficient because a
    string longrepr serializes trivially and still displays the full
    traceback text on the xdist master.
    """
    outcome = yield
    report = outcome.get_result()
    if report.longrepr is not None:
        longrepr = str(report.longrepr)
        if _has_surrogate(longrepr):
            report.longrepr = _sanitize(longrepr)
    report.sections = [
        (name, _sanitize(content)) for name, content in report.sections]
