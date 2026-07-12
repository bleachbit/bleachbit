# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Low-level path comparison, normalization, and expansion helpers.

This module is a leaf module: it depends only on the standard library
and on the constants exported by the `bleachbit` package (e.g., IS_WINDOWS).

This module avoids importing internal modules (e.g., Options) to prevent
circular imports.
"""

import os
import re

from bleachbit import FS_CASE_SENSITIVE


_ENV_VAR_ONLY_PATTERN = re.compile(
    r"""
    ^
    (?:
        \$(?P<unix>[A-Za-z_][A-Za-z0-9_]*)
        |
        \${(?P<brace>[A-Za-z_][A-Za-z0-9_]*)}
        |
        %(?P<windows>[A-Za-z_][A-Za-z0-9_]*)%
    )
    $
    """,
    re.VERBOSE,
)


def path_equal(path1, path2, case_sensitive=None):
    """Compare two paths respecting file-system case sensitivity.

    This is a raw string comparison; it does not normalize paths. For
    example, "/home/foo" equals neither "/home/foo/" nor "/home/.foo".
    Instead, the caller is responsible for normalization: see normalize_path.

    Args:
        path1: First path string.
        path2: Second path string.
        case_sensitive: If `None`, defaults to `FS_CASE_SENSITIVE`.
            Pass an explicit bool to override per call.
    """
    if case_sensitive is None:
        case_sensitive = FS_CASE_SENSITIVE
    if case_sensitive:
        return path1 == path2
    return path1.lower() == path2.lower()


def path_startswith(path, prefix, case_sensitive=None):
    """Check whether `path` is a child of `prefix`.

    Strict path-component-boundary check: `prefix` matches `path`
    only when `path` is `prefix` followed by `os.sep` and at
    least one more component. This means `/home/folder` does **not**
    match `/home/folder2`.

    This is a raw string comparison; it does not normalize paths. The
    caller is responsible for normalization (see `normalize_path`).

    Args:
        path: The path to test.
        prefix: The directory prefix to test against.
        case_sensitive: If `None`, defaults to `FS_CASE_SENSITIVE`.
            Pass an explicit bool to override per call.
    """
    if case_sensitive is None:
        case_sensitive = FS_CASE_SENSITIVE
    if case_sensitive:
        return path.startswith(prefix + os.sep)
    return path.lower().startswith(prefix.lower() + os.sep)


def normalize_path(path, case_sensitive=None):
    """Normalize a path for comparison.

    Args:
        path: The path to normalize.
        case_sensitive: If `None`, defaults to `FS_CASE_SENSITIVE`.
            When `False`, the normalized path is lowercased so that
            case-insensitive comparisons match.
    """
    if case_sensitive is None:
        case_sensitive = FS_CASE_SENSITIVE
    normalized = os.path.normpath(path)
    if not case_sensitive:
        normalized = normalized.lower()
    return normalized


def expand_path(raw_path):
    """Expand environment variables, user home, and normalize path.

    Returns one string.
    """
    assert isinstance(raw_path, str)
    # Expand user home (~)
    path = os.path.expanduser(raw_path)
    # Expand environment variables
    path = os.path.expandvars(path)
    # Normalize path separators
    if path:
        path = os.path.normpath(path)
    return path


def expand_path_entries(raw_path):
    """Expand a raw path into one or more normalized paths.

    Handles environment variables whose values are lists separated by
    `os.pathsep` (e.g., "XDG_DATA_DIRS" = "/usr/share:/usr/local/share")
    by returning a separate entry per value when the raw path consists
    of the environment variable placeholder alone.

    Returns a tuple of strings.
    """
    expanded = expand_path(raw_path)
    if not expanded:
        return tuple()

    if (_ENV_VAR_ONLY_PATTERN.match(raw_path)
            and os.pathsep in expanded):
        candidates = [segment.strip()
                      for segment in expanded.split(os.pathsep)]
        normalized = [os.path.normpath(segment)
                      for segment in candidates if segment]
        if normalized:
            return tuple(normalized)

    return (expanded,)
