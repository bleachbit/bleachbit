# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Application constants."""

import re

APP_VERSION = "4.7.0"
APP_NAME = "BleachBit"
APP_URL = "https://www.bleachbit.org"

SOCKET_TIMEOUT = 10

# Setting below value to false disables update notification (useful
# for packages in repositories).
ONLINE_UPDATE_NOTIFICATION_ENABLED = True

# The separator between message context and message id. This value is the same as
# the one used in gettext.h, so PO files should be still valid when Python gettext
# module will include pgettext() function.
GETTEXT_CONTEXT_GLUE = "\004"

BASE_URL = "https://update.bleachbit.org"
HELP_CONTENTS_URL = "%s/help/%s" % (BASE_URL, APP_VERSION)
RELEASE_NOTES_URL = "%s/release-notes/%s" % (BASE_URL, APP_VERSION)
UPDATE_CHECK_URL = "%s/update/%s" % (BASE_URL, APP_VERSION)

# Windows-only: case-insensitive file system
FS_SCAN_RE_FLAGS = re.IGNORECASE
