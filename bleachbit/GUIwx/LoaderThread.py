# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Threaded adapter for :func:`bleachbit.Cleaner.register_cleaners`.

``register_cleaners()`` is a generator that loads built-in cleaners,
CleanerML XML cleaners, and (on Windows) Winapp2.ini cleaners.  On
Windows the Winapp2 step can take several seconds.  Running it on the
wx main thread would freeze the UI until it completes, so this module
drains the generator on a background thread and forwards progress
messages onto the main thread via :func:`wx.CallAfter`.
"""

import logging
import threading

import wx

from bleachbit.Cleaner import backends, register_cleaners

logger = logging.getLogger(__name__)


def _post_on_main(callable_obj, *args, **kwargs):
    """Marshal ``callable_obj`` to the wx main thread if an app exists.

    :func:`wx.CallAfter` asserts that a :class:`wx.App` is present, so
    calling it from a background thread after the app has been torn down
    (e.g. the user closed the window while cleaners were still loading,
    or during test teardown) raises ``AssertionError`` and spams the log
    with an unhandled-thread traceback.  Guard against that by checking
    :func:`wx.GetApp` first; if there is no app, drop the callback
    silently -- there is nothing on the main thread to receive it.
    """
    if wx.GetApp() is None:
        return
    wx.CallAfter(callable_obj, *args, **kwargs)


class LoaderThread(threading.Thread):
    """Run :func:`register_cleaners` on a background thread."""

    def __init__(self, on_progress, on_done, on_error):
        """Create the loader.

        ``on_progress(msg)`` is called with a status string (e.g.
        "Loading native cleaners\u2026") on the main thread.
        ``on_done()`` is called on the main thread when registration
        finishes successfully.  ``on_error(exc)`` is called on the main
        thread if registration raises.
        """
        super().__init__(name='BleachBitCleanerLoader', daemon=True)
        self._on_progress = on_progress
        self._on_done = on_done
        self._on_error = on_error

    def _progress_cb(self, msg):
        # ``register_cleaners`` calls cb_progress with either a string
        # (status message) or a float (unused by this front-end).  Only
        # forward strings; they are the user-visible messages.
        if isinstance(msg, str):
            _post_on_main(self._on_progress, msg)

    def run(self):  # noqa: D401 - threading.Thread API
        try:
            for _step in register_cleaners(
                    cb_progress=self._progress_cb,
                    cb_done=lambda: None):
                # Drain the generator; progress is delivered via the
                # callback.  The yielded values are not meaningful here.
                pass
            # Compute the set of cleaner IDs that should be auto-hidden
            # here on the background thread: Cleaner.auto_hide() can be
            # slow because it invokes get_commands().execute(False),
            # which walks globs and the filesystem.  Doing it here keeps
            # the wx main thread responsive when _populate_tree runs.
            _post_on_main(self._on_progress,
                          'Detecting usable cleaners\u2026')
            hidden = _compute_auto_hidden()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception('register_cleaners failed')
            _post_on_main(self._on_error, exc)
            return
        _post_on_main(self._on_done, hidden)


def _compute_auto_hidden():
    """Return a ``set`` of cleaner IDs that have nothing to clean.

    Mirrors the GTK behavior in
    :meth:`bleachbit.GuiTreeModels.TreeInfoModel.refresh_rows`:
    skip cleaners with no options at all, and hide those whose
    ``auto_hide()`` reports they would do nothing on this system.
    """
    hidden = set()
    for cid in list(backends):
        if cid == '_gui':
            continue
        cleaner = backends[cid]
        try:
            if not any(cleaner.get_options()):
                hidden.add(cid)
                continue
            if cleaner.auto_hide():
                hidden.add(cid)
        except Exception:  # pylint: disable=broad-except
            logger.exception('auto_hide probe failed for %s', cid)
    return hidden
