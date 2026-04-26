# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2026 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Threaded adapter for :class:`bleachbit.Worker.Worker` (GTK front-end).

``Worker.run()`` is a generator.  Historically the GTK GUI pumped it on
the GLib idle loop on the main thread, which blocks paint and timer
events whenever a single ``cmd.execute()`` step runs longer than a
GLib idle slice (e.g. wiping empty space).

This module runs the generator on a background thread and marshals
every UI callback back to the GTK main thread via ``GLib.idle_add``.
The same pattern is used by the wx front-end in
``bleachbit/GUIwx/WorkerThread.py``; this is the GTK twin.

The interface that :class:`bleachbit.Worker.Worker` expects on its
``ui`` argument is:

* ``append_text(msg, tag=None)``
* ``update_progress_bar(value)`` where ``value`` is a ``float`` or ``str``
* ``update_total_size(size)``
* ``update_item_size(op, opid, size)``
* ``worker_done(worker, really_delete)``

:class:`GtkUIProxy` implements these methods and forwards them to an
arbitrary target object on the GTK main thread.
"""

import logging
import threading

logger = logging.getLogger(__name__)


def _default_scheduler(callback):
    """Schedule ``callback`` to run on the GTK main thread.

    Imported lazily so this module is importable in headless tests
    that do not have GTK available.
    """
    from bleachbit.GtkShim import GLib
    if GLib is None:
        raise RuntimeError(
            'GLib is not available; GtkWorkerThread requires GTK')
    GLib.idle_add(callback)


class GtkUIProxy:
    """Thread-safe, batching proxy for Worker UI callbacks (GTK).

    The worker can emit tens of thousands of ``append_text`` /
    ``append_row`` calls in a very short burst (e.g. Firefox cache
    clean).  Forwarding each one through its own ``GLib.idle_add``
    floods the main loop and blocks the UI until every event has been
    drained, which appears to the user as a frozen window with all
    rows arriving at once at the end.

    Instead, every call is appended to an in-memory queue, and at most
    one flush is scheduled at a time.  The flush drains the queue in
    capped chunks so the main loop can repaint between chunks; if
    there are still queued events after a chunk, a follow-up flush is
    scheduled.

    If the ``target`` exposes ``begin_batch()`` / ``end_batch()`` they
    are called around each chunk so heavy widgets can freeze/thaw
    layout once per chunk instead of once per event.
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

    def __init__(self, target, scheduler=None):
        """Create a proxy.

        ``target``: object whose methods will be invoked on the main
        thread.  ``scheduler``: callable accepting a zero-arg callback
        that schedules it for the main thread (default: GLib.idle_add).
        Tests may pass a synchronous scheduler.
        """
        self._target = target
        self._queue = []
        self._lock = threading.Lock()
        self._scheduled = False
        self._scheduler = scheduler or _default_scheduler

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
            self._scheduler(self._flush)
        return _enqueue

    def _flush(self):
        """Drain up to ``_CHUNK_SIZE`` queued events on the main thread."""
        with self._lock:
            chunk = self._queue[:self._CHUNK_SIZE]
            self._queue = self._queue[self._CHUNK_SIZE:]
            more = bool(self._queue)
            # Keep _scheduled True across the re-schedule so no other
            # thread posts a duplicate idle_add in between.
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
            # Re-schedule via the scheduler so paints and timers can
            # interleave with the next chunk.
            self._scheduler(self._flush)
        # idle_add expects False to mean "do not run me again".
        return False


class GtkWorkerThread(threading.Thread):
    """Run a :class:`bleachbit.Worker.Worker` generator on a thread.

    The thread constructs the ``Worker`` (so any error is surfaced via
    the logger and does not crash the GUI), then iterates the
    generator.  All UI callbacks emitted by the worker are routed
    through :class:`GtkUIProxy` to the GTK main thread.
    """

    def __init__(self, ui_target, really_delete, operations, scheduler=None):
        super().__init__(name='BleachBitWorker', daemon=True)
        self._ui_proxy = GtkUIProxy(ui_target, scheduler=scheduler)
        self._really_delete = really_delete
        self._operations = operations
        self.worker = None

    def abort(self):
        """Request the worker to stop at the next safe point."""
        if self.worker is not None:
            self.worker.abort()

    @property
    def is_aborted(self):
        """Return True if abort was requested and the worker observed it."""
        return self.worker is not None and self.worker.is_aborted

    def run(self):  # noqa: D401 - threading.Thread API
        # Imported here so this module is loadable without registering
        # cleaners (which Worker pulls in transitively).
        from bleachbit import Worker
        try:
            self.worker = Worker.Worker(
                self._ui_proxy, self._really_delete, self._operations)
        except Exception:  # pylint: disable=broad-except
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
        except Exception:  # pylint: disable=broad-except
            logger.exception('Worker raised unexpectedly')
