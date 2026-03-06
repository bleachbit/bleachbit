# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""Constants"""

from bleachbit.Language import get_text as _

# This module centralizes constants.
# By reducing imports, this module avoids circular dependencies.



# TRANSLATORS: Button label on (1) the headerbar and (2) the chaff dialog.
# 'Abort' is a verb.
ABORT_BUTTON_LABEL = _('Abort')

# This string is used several times. Listing it here helps with translation.
# TRANSLATORS: This is the name of a cleaning action. 'Clean' is a verb.
# It shows in the log of actions that would be performed (preview mode) or
# in the log of actions that are performed (clean mode).
CLEAN_FILE_LABEL = _('Clean file')

# TRANSLATORS: This message is used in three places (1) label at top of the
# preferences dialog (2) confirmation dialog when enabling the cleaning option
# (3) log message when starting to clean empty space.
EMPTY_SPACE_WARNING = _("Wiping empty space removes traces of files that were "
    "deleted without shredding, but it will not free additional disk space. The "
    "process can take a very long time and may temporarily slow your computer. "
    "It is not necessary if your drive is protected with full-disk encryption. "
    "The method works best on traditional hard drives. On solid-state drives, it "
    "is less reliable, and frequent use contributes to wear.")
