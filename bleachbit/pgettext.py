#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Code released in the Public Domain. You can do whatever you want with this package.
# Originally written by Pierre Métras <pierre@alterna.tv> for the OLPC XO laptop.
#
# Original source: http://dev.laptop.org/git/activities/clock/plain/pgettext.py

from Common import _
from gettext import gettext


# pgettext(msgctxt, msgid) from gettext is not supported in Python implementation < v2.6.
# http://bugs.python.org/issue2504
# Meanwhile we get official support, we have to simulate it.
# See http://www.gnu.org/software/gettext/manual/gettext.html#Ambiguities for
# more information about pgettext.

# The separator between message context and message id.This value is the same as
# the one used in gettext.h, so PO files should be still valid when Python gettext
# module will include pgettext() function.
GETTEXT_CONTEXT_GLUE = "\004"

def pgettext(msgctxt, msgid):
    """A custom implementation of GNU pgettext().
    """
    if msgctxt is not None and msgctxt is not "":
        translation = _(msgctxt + GETTEXT_CONTEXT_GLUE + msgid)
        if translation.startswith(msgctxt + GETTEXT_CONTEXT_GLUE):
            return msgid
        else:
            return translation
    else:
        return _(msgid)

# Map our pgettext() custom function to _p()
_p = lambda msgctxt, msgid: pgettext(msgctxt, msgid)


