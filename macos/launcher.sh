#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.
#
# Start BleachBit from inside the application bundle. macos/build_dmg.py
# copies this file to Contents/MacOS/BleachBit.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FW="$HERE/Frameworks"
export DYLD_LIBRARY_PATH="$FW/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
export GI_TYPELIB_PATH="$FW/girepository-1.0"
export XDG_DATA_DIRS="$HERE/Resources/share"
export GSETTINGS_SCHEMA_DIR="$HERE/Resources/share/glib-2.0/schemas"
export PYTHONNOUSERSITE=1
# The OpenSSL certificates of Homebrew are not in the bundle, so give the ssl
# module those of certifi, unless the user chose others.
export SSL_CERT_FILE="${SSL_CERT_FILE:-$FW/Python.framework/Versions/3.12/lib/python3.12/site-packages/certifi/cacert.pem}"
export PYTHONPYCACHEPREFIX="$HOME/Library/Caches/org.bleachbit.BleachBit/pycache"

# The gdk-pixbuf loaders cache must contain absolute paths, which depend on
# where the user put the application, so create it at each start.
CACHE="${TMPDIR:-/tmp}/bleachbit-pixbuf-$(id -u).cache"
sed "s|@LIB@|$FW/lib|g" "$HERE/Resources/share/gdk-pixbuf-loaders.cache.in" > "$CACHE"
export GDK_PIXBUF_MODULE_FILE="$CACHE"

exec "$FW/Python.framework/Versions/3.12/bin/python3.12" "$HERE/Resources/bleachbit.py" "$@"
