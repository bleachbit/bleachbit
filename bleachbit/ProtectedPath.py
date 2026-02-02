# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

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
The protected path warning system is a safety net

This module loads protected path definitions from XML and checks whether
user-specified paths match protected paths, warning users before they
accidentally delete important system or application files.
"""

import logging
import os
import re
import xml.dom.minidom

import bleachbit
from bleachbit import FileUtilities
from bleachbit.General import getText, os_match
from bleachbit.Language import get_text as _

logger = logging.getLogger(__name__)

# Cache for loaded protected paths
_protected_paths_cache = None

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


def _expand_path(raw_path):
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


def _expand_path_entries(raw_path):
    """Expand a raw path into one or more normalized paths.

    Handles environment variables whose values are lists separated by
    os.pathsep (e.g., XDG_DATA_DIRS=/usr/share:/usr/local/share) by
    returning a separate entry per value when the raw path consists of
    the environment variable placeholder alone.
    """

    expanded = _expand_path(raw_path)
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


# this function is used in GuiPreferences.py
def _normalize_for_comparison(path, case_sensitive):
    """Normalize a path for comparison.

    Args:
        path: The path to normalize
        case_sensitive: If False, convert to lowercase for comparison
    """
    normalized = os.path.normpath(path)
    if not case_sensitive:
        normalized = normalized.lower()
    return normalized


def _get_protected_path_xml():
    """Return the path to the protected_path.xml file."""
    share_dir = bleachbit.get_share_dir()
    if share_dir:
        xml_path = os.path.join(share_dir, 'protected_path.xml')
        if os.path.exists(xml_path):
            return xml_path

    return None


def load_protected_paths(force_reload=False):
    """Load protected path definitions from XML.

    Returns a list of dictionaries with keys:
        - path: The expanded, normalized path
        - depth: How many levels deep to protect (0=exact, 1=children, etc.)
        - case_sensitive: Whether matching should be case-sensitive

    Args:
        force_reload: If True, reload from XML even if cached
    """
    global _protected_paths_cache

    if _protected_paths_cache is not None and not force_reload:
        return _protected_paths_cache

    xml_path = _get_protected_path_xml()
    if xml_path is None:
        logger.warning("Protected path XML file not found")
        return []

    protected_paths = []

    try:
        dom = xml.dom.minidom.parse(xml_path)
    except Exception as e:
        logger.error("Error parsing protected path XML: %s", e)
        return []

    for paths_node in dom.getElementsByTagName('paths'):
        # Check OS match for this <paths> group
        os_attr = paths_node.getAttribute('os') or ''
        if not os_match(os_attr):
            continue

        for path_node in paths_node.getElementsByTagName('path'):
            # Get path attributes (inherit from parent <paths> when omitted)
            depth_attr = (path_node.getAttribute('depth') or
                          paths_node.getAttribute('depth') or '0')
            if depth_attr == 'any':
                depth = None
            else:
                try:
                    depth = int(depth_attr)
                except ValueError:
                    depth = 0

            case_attr = (path_node.getAttribute('case') or
                         paths_node.getAttribute('case') or '')
            if case_attr == 'insensitive':
                case_sensitive = False
            elif case_attr == 'sensitive':
                case_sensitive = True
            else:
                # Default: Windows is case-insensitive, others are case-sensitive
                case_sensitive = os.name != 'nt'

            # Get the path text
            raw_path = getText(path_node.childNodes).strip()
            if not raw_path:
                continue

            # Expand the path (possibly into multiple entries)
            for expanded_path in _expand_path_entries(raw_path):
                protected_paths.append({
                    'path': expanded_path,
                    'depth': depth,
                    'case_sensitive': case_sensitive,
                })

    _protected_paths_cache = protected_paths
    logger.debug("Loaded %d protected paths", len(protected_paths))
    return protected_paths


def _check_exempt(user_path):
    """Check if path is exempt from protection

    For ignoring paths like .git under ~/.cache/
    """
    assert isinstance(user_path, str)
    exempt_paths = ('~/.cache', '%temp%', '%tmp%', '/tmp')
    case_sensitive = os.name != 'nt'
    user_path_normalized = _normalize_for_comparison(
        user_path, case_sensitive=case_sensitive)
    for path in exempt_paths:
        exempt_expanded = _expand_path(path)
        if not exempt_expanded:
            continue

        exempt_normalized = _normalize_for_comparison(
            exempt_expanded, case_sensitive=case_sensitive)

        if user_path_normalized == exempt_normalized:
            return True

        exempt_with_sep = exempt_normalized + os.sep
        if user_path_normalized.startswith(exempt_with_sep):
            return True
    return False


def check_protected_path(user_path):
    """Check if a user path matches a protected path.

    Args:
        user_path: The path the user wants to add to delete list

    Returns:
        A dictionary with match info if protected, None otherwise:
        - protected_path: The matched protected path
        - depth: The depth of the protection
        - case_sensitive: Whether the match was case-sensitive
    """
    if _check_exempt(user_path):
        return None
    protected_paths = load_protected_paths()
    if not protected_paths:
        return None

    # Normalize the user path
    user_path_norm = os.path.normpath(user_path)

    for ppath in protected_paths:
        protected = ppath['path']
        depth = ppath['depth']
        case_sensitive = ppath['case_sensitive']

        # Normalize both paths for comparison
        if case_sensitive:
            user_cmp = user_path_norm
            protected_cmp = protected
        else:
            user_cmp = user_path_norm.lower()
            protected_cmp = protected.lower()

        protected_is_absolute = os.path.isabs(ppath['path'])
        if not protected_is_absolute:
            # Relative protected paths should match when user path ends with them
            if user_cmp == protected_cmp:
                return ppath
            relative_suffix = os.sep + protected_cmp.lstrip(os.sep)
            if user_cmp.endswith(relative_suffix):
                return ppath
            continue

        # Exact match
        if user_cmp == protected_cmp:
            return ppath

        # Check if user path is a parent of protected path
        # (user wants to delete a folder that contains protected items)
        protected_with_sep = protected_cmp + os.sep
        user_with_sep = user_cmp + os.sep
        if protected_cmp.startswith(user_with_sep):
            return ppath

        # Check if user path is a child of protected path (within depth)
        if (depth is None or depth > 0) and user_cmp.startswith(protected_with_sep):
            if depth is None:
                return ppath
            # Calculate how many levels deep the user path is
            relative = user_cmp[len(protected_with_sep):]
            levels = relative.count(os.sep) + 1
            if levels <= depth:
                return ppath

    return None


def calculate_impact(path):
    """Calculate the impact of deleting a path.

    Args:
        path: The path to calculate impact for

    Returns:
        A dictionary with:
        - file_count: Number of files
        - total_size: Total size in bytes
        - size_human: Human-readable size string
    """
    if not os.path.exists(path):
        return {
            'file_count': 0,
            'total_size': 0,
            'size_human': '0B',
        }

    file_count = 0
    total_size = 0

    try:
        if os.path.isfile(path):
            file_count = 1
            total_size = FileUtilities.getsize(path)
        elif os.path.isdir(path):
            for child in FileUtilities.children_in_directory(path, list_directories=False):
                file_count += 1
                try:
                    total_size += FileUtilities.getsize(child)
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError) as e:
        logger.debug("Error calculating impact for %s: %s", path, e)

    return {
        'file_count': file_count,
        'total_size': total_size,
        'size_human': FileUtilities.bytes_to_human(total_size),
    }


def get_warning_message(user_path, impact):
    """Generate a warning message for a protected path.

    Args:
        user_path: The path the user wants to add
        impact: The impact info from calculate_impact

    Returns:
        A formatted warning message string
    """

    if impact['file_count'] > 0:
        # TRANSLATORS: Warning shown when user tries to add a protected path.
        # %(path)s is the path, %(files)d is number of files, %(size)s is human-readable size
        msg = _("Warning: '%(path)s' may contain important files.\n\n"
                "Impact: %(files)d file(s), %(size)s\n\n"
                "Are you sure you want to add this path?") % {
            'path': user_path,
            'files': impact['file_count'],
            'size': impact['size_human'],
        }
    else:
        # TRANSLATORS: Warning shown when user tries to add a protected path (no files found)
        msg = _("Warning: '%(path)s' may contain important files.\n\n"
                "Are you sure you want to add this path?") % {
            'path': user_path,
        }

    return msg


def clear_cache():
    """Clear the protected paths cache."""
    global _protected_paths_cache
    _protected_paths_cache = None
