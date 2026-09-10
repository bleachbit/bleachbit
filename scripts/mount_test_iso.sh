#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# For testing, download and mount an .iso read-only.

set -euo pipefail

iso_path="${1:-/tmp/bleachbit_test.iso}"
mount_point="${2:-/mnt/bleachbit_test_iso}"
archive_url='https://download.bleachbit.org/test/test.iso.7z'
expected_hash='71f284d46636bc11d2d02dcf1da4a87003e30056db59cc696f040163bfa28ffb'

archive="${iso_path}.7z"
curl -fsSL -o "$archive" "$archive_url"
7z x -y -o"$(dirname "$iso_path")" "$archive" >/dev/null
extracted="$(dirname "$iso_path")/bleachbit_test.iso"
if [[ "$extracted" != "$iso_path" ]]; then mv -f "$extracted" "$iso_path"; fi
echo "$expected_hash  $iso_path" | sha256sum -c
sudo mkdir -p "$mount_point"
sudo mount -o loop,ro "$iso_path" "$mount_point"
echo "Mounted $iso_path at $mount_point"
