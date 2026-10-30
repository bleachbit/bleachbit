#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# For CI, install the Ubuntu packages the Linux tests need. Extra packages
# can be given in $PYTHON_EXTRA_DEP, separated by spaces.

set -euo pipefail

read -ra extra <<< "${PYTHON_EXTRA_DEP:-}"

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    appstream \
    dbus \
    dbus-x11 \
    gettext \
    gir1.2-gtk-3.0 \
    gir1.2-notify-0.7 \
    gnome-keyring \
    libcairo2-dev \
    libgirepository1.0-dev \
    libnotify-bin \
    libxml2-utils \
    notification-daemon \
    p7zip-full \
    python3-venv \
    xvfb \
    "${extra[@]}"
# for tests.TestLanguage
sudo locale-gen es_ES.UTF-8
sudo locale-gen pl_PL.UTF-8
sudo locale-gen en_AU.UTF-8
sudo update-locale
