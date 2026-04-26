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
Tests for the GTK threaded Worker adapter.

These tests do not require a GTK main loop: a synchronous scheduler is
injected into :class:`GtkUIProxy` so flushes happen inline.  This lets
us verify FIFO order, batching, ``begin_batch``/``end_batch`` hooks,
and end-to-end behaviour of :class:`GtkWorkerThread` without GTK.
"""

import os
import tempfile
import threading
import unittest

from tests import common

from bleachbit.Cleaner import backends
from bleachbit.WorkerThread import GtkUIProxy, GtkWorkerThread


class _RecordingTarget:
    """Records UI callbacks delivered by the proxy."""

    def __init__(self, with_batch=False):
        self.calls = []
        self.batch_events = []
        if with_batch:
            self.begin_batch = self._begin
            self.end_batch = self._end

    def _begin(self):
        self.batch_events.append('begin')

    def _end(self):
        self.batch_events.append('end')

    def append_text(self, msg, tag=None):
        self.calls.append(('append_text', msg, tag))

    def append_row(self, op, label, size, path):
        self.calls.append(('append_row', op, label, size, path))

    def update_progress_bar(self, value):
        self.calls.append(('update_progress_bar', value))

    def update_total_size(self, size):
        self.calls.append(('update_total_size', size))

    def update_item_size(self, op, opid, size):
        self.calls.append(('update_item_size', op, opid, size))

    def worker_done(self, worker, really_delete):
        self.calls.append(('worker_done', really_delete))


class GtkUIProxyTestCase(common.BleachbitTestCase):
    """Test :class:`GtkUIProxy` queueing and dispatch."""

    def _make_sync_scheduler(self):
        """Return a scheduler that invokes the callback immediately.

        This emulates a GTK main loop that drains every idle callback
        the moment it is posted, which is the simplest model for unit
        tests.
        """
        def scheduler(callback):
            callback()
        return scheduler

    def test_forwarded_methods_only(self):
        """Only documented methods are forwarded; others raise."""
        proxy = GtkUIProxy(_RecordingTarget(),
                           scheduler=self._make_sync_scheduler())
        # Documented methods must exist:
        for name in ('append_text', 'append_row', 'update_progress_bar',
                     'update_total_size', 'update_item_size', 'worker_done'):
            self.assertTrue(callable(getattr(proxy, name)))
        # Undocumented attribute access raises AttributeError.
        with self.assertRaises(AttributeError):
            _ = proxy.not_a_real_method

    def test_optional_target_methods_feature_detect(self):
        """Forwarded names absent on the target must report as absent.

        The Worker uses ``getattr(ui, 'append_row', None)`` to feature-
        detect optional callbacks.  The GTK MainWindow does not
        implement ``append_row``, so the proxy must propagate the
        absence rather than enqueue calls that will fail at flush.
        """
        class MinimalTarget:
            # Implements only the mandatory subset (no append_row).
            def append_text(self, msg, tag=None):
                pass

            def update_progress_bar(self, value):
                pass

            def update_total_size(self, size):
                pass

            def update_item_size(self, op, opid, size):
                pass

            def worker_done(self, worker, really_delete):
                pass

        proxy = GtkUIProxy(MinimalTarget(),
                           scheduler=self._make_sync_scheduler())
        # Implemented methods are exposed.
        self.assertTrue(callable(proxy.append_text))
        # Unimplemented optional method must NOT appear on the proxy.
        self.assertIsNone(getattr(proxy, 'append_row', None))

    def test_fifo_delivery_with_sync_scheduler(self):
        """Calls are delivered in the order they were enqueued."""
        target = _RecordingTarget()
        proxy = GtkUIProxy(target, scheduler=self._make_sync_scheduler())
        proxy.append_text('first')
        proxy.update_progress_bar(0.5)
        proxy.append_text('second', 'error')
        proxy.update_total_size(123)
        self.assertEqual(target.calls, [
            ('append_text', 'first', None),
            ('update_progress_bar', 0.5),
            ('append_text', 'second', 'error'),
            ('update_total_size', 123),
        ])

    def test_begin_end_batch_called_around_chunks(self):
        """``begin_batch``/``end_batch`` wrap each flush chunk.

        Use a deferred scheduler so multiple enqueues coalesce into a
        single chunk, exactly as they would on a real GTK main loop.
        """
        target = _RecordingTarget(with_batch=True)
        scheduled = []

        def deferred_scheduler(callback):
            scheduled.append(callback)

        proxy = GtkUIProxy(target, scheduler=deferred_scheduler)
        proxy.append_text('a')
        proxy.append_text('b')
        proxy.append_text('c')
        # One flush is scheduled; the next two enqueues piggyback.
        self.assertEqual(len(scheduled), 1)
        scheduled.pop(0)()
        # Exactly one begin/end pair around the single chunk.
        self.assertEqual(target.batch_events, ['begin', 'end'])
        self.assertEqual([c[0] for c in target.calls],
                         ['append_text', 'append_text', 'append_text'])

    def test_chunking_for_large_bursts(self):
        """A burst exceeding ``_CHUNK_SIZE`` is split across flushes."""
        target = _RecordingTarget(with_batch=True)

        scheduled = []

        def deferred_scheduler(callback):
            scheduled.append(callback)

        proxy = GtkUIProxy(target, scheduler=deferred_scheduler)
        # Enqueue more than one chunk worth of events.
        burst = GtkUIProxy._CHUNK_SIZE + 5
        for i in range(burst):
            proxy.append_text('msg %d' % i)
        # Exactly one flush has been scheduled so far (subsequent
        # enqueues piggybacked on the first schedule).
        self.assertEqual(len(scheduled), 1)
        # Run the first flush; it should drain _CHUNK_SIZE events and
        # schedule a follow-up for the rest.
        scheduled.pop(0)()
        self.assertEqual(len(target.calls), GtkUIProxy._CHUNK_SIZE)
        self.assertEqual(len(scheduled), 1)
        # Run the follow-up flush; it should drain the remainder and
        # not schedule again.
        scheduled.pop(0)()
        self.assertEqual(len(target.calls), burst)
        self.assertEqual(scheduled, [])
        # Each chunk gets its own begin/end pair.
        self.assertEqual(target.batch_events, ['begin', 'end', 'begin', 'end'])

    def test_target_callback_exception_is_logged_not_raised(self):
        """A failing target callback must not stop later callbacks."""
        class Boom:
            def __init__(self):
                self.calls = []

            def append_text(self, msg, tag=None):
                self.calls.append(msg)
                if msg == 'boom':
                    raise RuntimeError('ka-boom')
        target = Boom()
        proxy = GtkUIProxy(target, scheduler=self._make_sync_scheduler())
        with self.assertLogs(
                'bleachbit.WorkerThread', level='ERROR') as ctx:
            proxy.append_text('ok-1')
            proxy.append_text('boom')
            proxy.append_text('ok-2')
        self.assertEqual(target.calls, ['ok-1', 'boom', 'ok-2'])
        # The exception was logged, including the method name.
        self.assertTrue(any('append_text' in line for line in ctx.output))

    def test_discard_pending_drops_queued_events(self):
        """``discard_pending`` clears the queue but lets future enqueues flow.

        Models the abort scenario: ~200K events are queued on the proxy
        but not yet flushed; abort drops them so the GUI can stop
        rendering, while the worker's post-abort summary lines still
        get delivered.
        """
        target = _RecordingTarget()
        scheduled = []

        def deferred_scheduler(callback):
            scheduled.append(callback)

        proxy = GtkUIProxy(target, scheduler=deferred_scheduler)
        # Queue a large burst (no flush yet).
        for i in range(5000):
            proxy.append_text('pre-abort %d' % i)
        self.assertEqual(len(scheduled), 1)
        # Abort: drop everything queued so far.
        proxy.discard_pending()
        # New events posted after discard still queue normally.
        proxy.append_text('summary line')
        proxy.worker_done(object(), False)
        # Drain the (still-scheduled) flush plus any follow-ups.
        while scheduled:
            scheduled.pop(0)()
        # Only the post-discard events were delivered.
        self.assertEqual(target.calls, [
            ('append_text', 'summary line', None),
            ('worker_done', False),
        ])

    def test_thread_safe_concurrent_enqueue(self):
        """Concurrent enqueues do not lose events (FIFO per producer)."""
        target = _RecordingTarget()
        # Use a deferred scheduler so no flush happens during enqueue.
        scheduled = []

        def deferred_scheduler(callback):
            scheduled.append(callback)

        proxy = GtkUIProxy(target, scheduler=deferred_scheduler)
        n_threads = 4
        per_thread = 250

        def producer(tid):
            for i in range(per_thread):
                proxy.append_text('t%d-%d' % (tid, i))

        threads = [threading.Thread(target=producer, args=(t,))
                   for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Exactly one flush was scheduled regardless of producer count.
        self.assertEqual(len(scheduled), 1)
        # Drain (synchronously, as on the main thread).
        while scheduled:
            scheduled.pop(0)()
        self.assertEqual(len(target.calls), n_threads * per_thread)
        # Per-thread FIFO order is preserved (the lock serializes
        # enqueue, so each thread's events stay in submission order).
        for tid in range(n_threads):
            seen = [c[1] for c in target.calls
                    if c[1].startswith('t%d-' % tid)]
            expected = ['t%d-%d' % (tid, i) for i in range(per_thread)]
            self.assertEqual(seen, expected)


class _DummyCleaner:
    """A trivial cleaner exposing one option that yields one delete cmd."""

    def __init__(self, path):
        self._path = path

    def get_id(self):
        return 'dummy'

    def get_name(self):
        return 'Dummy'

    def is_process_running(self):
        return False

    def get_options(self):
        return [('only', 'Only')]

    def get_warning(self, _option_id):
        return None

    def get_commands(self, _option_id):
        from bleachbit import Command
        yield Command.Delete(self._path)

    def get_deep_scan(self, _option_id):
        return iter([])


class GtkWorkerThreadTestCase(common.BleachbitTestCase):
    """End-to-end test of :class:`GtkWorkerThread`.

    Runs the worker thread for real and uses a thread-safe synchronous
    scheduler that simply invokes flushes from the calling thread.
    Because the scheduler runs on the worker thread, the recording
    target must itself be thread-safe; we only assert post-join state.
    """

    def test_thread_runs_worker_to_completion(self):
        # Create a real file the dummy cleaner will delete.
        fd, path = tempfile.mkstemp(prefix='bleachbit-tt-', dir=self.tempdir)
        os.write(fd, b'abc')
        os.close(fd)
        self.assertExists(path)

        # Inject a fake cleaner.
        backends['dummy'] = _DummyCleaner(path)
        try:
            target = _RecordingTarget()
            # Synchronous scheduler: flushes execute on the worker
            # thread.  GTK normally executes them on the main thread,
            # but for a unit test that just observes call counts and
            # final state, in-thread dispatch is fine.

            def scheduler(callback):
                callback()
            wt = GtkWorkerThread(target, True,
                                 {'dummy': ['only']}, scheduler=scheduler)
            wt.start()
            wt.join(timeout=10)
            self.assertFalse(wt.is_alive(), 'worker thread did not finish')
        finally:
            del backends['dummy']

        self.assertNotExists(path)
        # worker_done must have been delivered exactly once.
        done = [c for c in target.calls if c[0] == 'worker_done']
        self.assertEqual(len(done), 1, 'worker_done not delivered exactly once')
        self.assertEqual(done[0][1], True)  # really_delete
        # The underlying Worker should have been created and reachable.
        self.assertIsNotNone(wt.worker)
        self.assertEqual(wt.worker.total_errors, 0)
        self.assertEqual(wt.worker.total_deleted, 1)

    def test_abort_calls_discard_pending(self):
        """``GtkWorkerThread.abort()`` drops pending UI events.

        Constructs the thread but does not start it, then mocks the
        proxy and the underlying worker to verify abort wires both
        signals.  This is the unit-level guarantee behind the GTK
        responsiveness fix; the deferred-scheduler proxy test above
        already verifies the queue-drop behaviour itself.
        """
        from unittest import mock
        wt = GtkWorkerThread(
            _RecordingTarget(), False, {'dummy': ['only']})
        wt._ui_proxy = mock.Mock(spec=['discard_pending'])
        wt.worker = mock.Mock()
        wt.abort()
        wt.worker.abort.assert_called_once_with()
        wt._ui_proxy.discard_pending.assert_called_once_with()

    def test_abort_stops_worker(self):
        # Build many files so the loop has work to abort partway through.
        paths = []
        for _ in range(50):
            fd, p = tempfile.mkstemp(prefix='bleachbit-tt-abort-',
                                     dir=self.tempdir)
            os.close(fd)
            paths.append(p)

        class _ManyDelete(_DummyCleaner):
            def __init__(self, paths):
                self._paths = paths

            def get_commands(self, _option_id):
                from bleachbit import Command
                for p in self._paths:
                    yield Command.Delete(p)

        backends['dummy'] = _ManyDelete(paths)
        try:
            target = _RecordingTarget()
            # Abort early: flip the worker's flag the first time we see
            # any UI callback.
            done_evt = threading.Event()
            wt_holder = {}

            def scheduler(callback):
                callback()
                if wt_holder.get('wt') is not None and not done_evt.is_set():
                    wt_holder['wt'].abort()

            wt = GtkWorkerThread(target, True,
                                 {'dummy': ['only']}, scheduler=scheduler)
            wt_holder['wt'] = wt
            wt.start()
            wt.join(timeout=10)
            done_evt.set()
            self.assertFalse(wt.is_alive())
        finally:
            del backends['dummy']

        # is_aborted is reflected by the thread wrapper.
        self.assertTrue(wt.is_aborted)


if __name__ == '__main__':
    unittest.main()
