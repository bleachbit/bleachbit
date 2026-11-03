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

if [[ "$python_version" == "3.9" ]]; then
    suite="make -C po tests && make tests-pytest && make tests-nsis"
elif [[ "$python_version" == "3.12" || "$python_version" == "3.15" ]]; then
    suite="make tests-pytest"
else
    suite="make -C cleaners tests && make tests-pytest && make tests-nsis && make tests-with-sudo"
fi
# xvfb-run discards the server's stderr, which hides the harmless
# xkbcomp keysym warnings on ubuntu-24.04
dbus-run-session -- xvfb-run -a bash -c "/usr/lib/notification-daemon/notification-daemon & sleep 2 && $suite"
