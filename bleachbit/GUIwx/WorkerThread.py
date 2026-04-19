# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Threaded adapter for :class:`bleachbit.Worker.Worker`.

``Worker.run()`` is a generator.  The GTK front-end pumps it on the
GLib idle loop; the CLI pumps it in a tight loop.  The wx front-end
runs it on a background thread and marshals UI callbacks onto the
wx main thread via :func:`wx.CallAfter`.

The interface that :class:`bleachbit.Worker.Worker` expects on its
``ui`` argument is:

* ``append_text(msg, tag=None)``
* ``update_progress_bar(value)`` where ``value`` is a ``float`` fraction
  or a ``str`` status message
* ``update_total_size(size)``
* ``update_item_size(op, opid, size)``
* ``worker_done(worker, really_delete)``

:class:`WxUIProxy` implements these methods and forwards them to an
arbitrary target object on the main thread.
"""

import logging
import threading

import wx

from bleachbit import Worker

logger = logging.getLogger(__name__)


class WxUIProxy:
    """Thread-safe proxy that forwards Worker UI callbacks to the main thread.

    All attribute access returns a callable that, when invoked from the
    worker thread, schedules the matching method on ``target`` via
    :func:`wx.CallAfter`.
    """

    _FORWARDED = (
        'append_text',
        'update_progress_bar',
        'update_total_size',
        'update_item_size',
        'worker_done',
    )

    def __init__(self, target):
        self._target = target

    def __getattr__(self, name):
        if name not in self._FORWARDED:
            raise AttributeError(name)
        target = self._target
        method = getattr(target, name)

        def _forward(*args, **kwargs):
            wx.CallAfter(method, *args, **kwargs)
        return _forward


class WorkerThread(threading.Thread):
    """Run a :class:`bleachbit.Worker.Worker` generator on a thread."""

    def __init__(self, ui_target, really_delete, operations):
        super().__init__(name='BleachBitWorker', daemon=True)
        self._ui_proxy = WxUIProxy(ui_target)
        self._really_delete = really_delete
        self._operations = operations
        self.worker = None

    def abort(self):
        """Request the worker to stop at the next safe point."""
        if self.worker is not None:
            self.worker.abort()

    def run(self):  # noqa: D401 - threading.Thread API
        try:
            self.worker = Worker.Worker(
                self._ui_proxy, self._really_delete, self._operations)
        except Exception:
            logger.exception('Error constructing Worker')
            return
        try:
            gen = self.worker.run()
            # The generator yields True periodically so a GUI loop can
            # refresh.  In a thread we simply drain it.
            for _ in gen:
                if self.worker.is_aborted:
                    break
        except StopIteration:
            pass
        except Exception:
            logger.exception('Worker raised unexpectedly')
