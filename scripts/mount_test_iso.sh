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
archive_hash='0d827b61fed9fc5983fe4639e3d383e40b9d5d6c2335ee00ca9b2229280ebb38'
expected_hash='71f284d46636bc11d2d02dcf1da4a87003e30056db59cc696f040163bfa28ffb'

command -v 7z >/dev/null || { echo "7z is required" >&2; exit 1; }

archive="${iso_path}.7z"
curl -fsSL --retry 3 --retry-connrefused -o "$archive" "$archive_url"
echo "$archive_hash  $archive" | sha256sum -c
7z x -y -o"$(dirname "$iso_path")" "$archive" >/dev/null
extracted="$(dirname "$iso_path")/bleachbit_test.iso"
if [[ "$extracted" != "$iso_path" ]]; then mv -f "$extracted" "$iso_path"; fi
echo "$expected_hash  $iso_path" | sha256sum -c
sudo mkdir -p "$mount_point"
sudo mount -o loop,ro "$iso_path" "$mount_point"
echo "Mounted $iso_path at $mount_point"
