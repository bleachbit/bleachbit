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
    """Thread-safe, batching proxy for Worker UI callbacks.

    The worker can emit tens of thousands of ``append_text`` /
    ``append_row`` calls in a very short burst (e.g. Firefox cache
    clean).  Forwarding each one through its own :func:`wx.CallAfter`
    floods the wx main-thread event queue and blocks the UI until
    every event has been processed, which appears to the user as a
    frozen window with all rows arriving at once at the end.

    Instead, every call is appended to an in-memory queue, and at most
    one flush is scheduled via ``wx.CallAfter`` at a time.  The flush
    drains the queue in capped chunks so the main thread can repaint
    between chunks; if there are still queued events after a chunk, a
    follow-up flush is scheduled.

    If the ``target`` exposes ``begin_batch()`` / ``end_batch()``, they
    are called around each chunk; :class:`MainFrame` uses them to
    :meth:`wx.Window.Freeze` / :meth:`wx.Window.Thaw` the heavy widgets
    so rapid ``InsertItem`` and ``AppendText`` calls do not trigger a
    re-layout per item.
    """

    _FORWARDED = (
        'append_text',
        'append_row',
        'update_progress_bar',
        'update_total_size',
        'update_item_size',
        'worker_done',
    )

    # Maximum number of queued events to process in one flush before
    # yielding back to the main loop.  Tuned so a 10k-row preview is
    # broken into ~10 repaints rather than a single multi-second block.
    _CHUNK_SIZE = 1000

    def __init__(self, target):
        self._target = target
        self._queue = []
        self._lock = threading.Lock()
        self._scheduled = False

    def __getattr__(self, name):
        if name not in self._FORWARDED:
            raise AttributeError(name)

        def _enqueue(*args, **kwargs):
            with self._lock:
                self._queue.append((name, args, kwargs))
                if self._scheduled:
                    return
                self._scheduled = True
            # Schedule outside the lock to avoid any chance of deadlock
            # with a main-thread path that tries to acquire _lock.
            wx.CallAfter(self._flush)
        return _enqueue

    def _flush(self):
        """Drain up to ``_CHUNK_SIZE`` queued events on the main thread."""
        with self._lock:
            chunk = self._queue[:self._CHUNK_SIZE]
            self._queue = self._queue[self._CHUNK_SIZE:]
            more = bool(self._queue)
            # Keep _scheduled True across the re-schedule so no other
            # thread posts a duplicate CallAfter in between.
            self._scheduled = more

        target = self._target
        begin = getattr(target, 'begin_batch', None)
        end = getattr(target, 'end_batch', None)
        if begin is not None:
            try:
                begin()
            except Exception:  # pylint: disable=broad-except
                logger.exception('begin_batch failed')
        try:
            for name, args, kwargs in chunk:
                try:
                    getattr(target, name)(*args, **kwargs)
                except Exception:  # pylint: disable=broad-except
                    logger.exception('UI callback %s failed', name)
        finally:
            if end is not None:
                try:
                    end()
                except Exception:  # pylint: disable=broad-except
                    logger.exception('end_batch failed')

        if more:
            # Re-schedule via the timer queue (``CallLater``) rather
            # than pushing another pending-event (``CallAfter``).  Back-
            # to-back ``CallAfter`` re-schedules run without returning
            # to the main loop's idle phase, which starves paint and
            # timer events and makes the window appear frozen during a
            # large burst.  A zero-delay timer yields just long enough
            # for pending repaints and timers to interleave.
            wx.CallLater(0, self._flush)


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
