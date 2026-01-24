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
GTK graphical user interface
"""

# standard library
import logging

# third party import (via centralized shim)
from bleachbit.GtkShim import require_gtk

# Ensure GTK is available for this GUI module
require_gtk()

# local
from bleachbit.Log import set_root_log_level
from bleachbit.Options import options # keep

# Now that the configuration is loaded, honor the debug preference there.
set_root_log_level(options.get('debug'))
logger = logging.getLogger(__name__)
