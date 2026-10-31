#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# For CI, run the Linux tests under Xvfb with a notification daemon. The
# Python version picks the suite.

set -euo pipefail

python_version="$1"

export DISPLAY=":1.0"
# shellcheck disable=SC2046 # dbus-launch prints NAME=value lines to export
export $(dbus-launch)
sudo Xvfb :1 -screen 0 800x600x24 &
sleep 5
if [[ "$python_version" == "3.9" ]]; then
    suite="make -C po tests && make tests-pytest && make tests-nsis"
elif [[ "$python_version" == "3.12" || "$python_version" == "3.15" ]]; then
    suite="make tests-pytest"
else
    suite="make -C cleaners tests && make tests-pytest && make tests-nsis && make tests-with-sudo"
fi
dbus-run-session -- bash -c "/usr/lib/notification-daemon/notification-daemon & sleep 2 && xvfb-run -a bash -c '$suite'"
