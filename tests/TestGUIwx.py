# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
wxPython GUI tests
"""

import logging
import unittest
from unittest import mock

from bleachbit.Options import options
from tests import common

try:
    import wx
except ImportError:
    wx = None
    HAVE_WX = False
else:
    HAVE_WX = True


WX_SMOKE_EXIT_MS = 500

BROWSER1_ID = '_fauxfox'
BROWSER2_ID = '_pseudromium'


@unittest.skipUnless(HAVE_WX, 'requires wxPython')
class GUIwxTestCase(common.BleachbitTestCase):
    app = None
    frame = None

    @classmethod
    def setUpClass(cls):
        """Create the shared wx App and main frame for all tests."""
        super().setUpClass()
        try:
            from bleachbit.GUIwx import MainFrame as MainFrameModule
            from bleachbit.GUIwx import PreferencesDialog as PreferencesModule
            from bleachbit.GUIwx import WorkerThread as WorkerThreadModule
            from bleachbit.GUIwx.App import BleachBitWxApp
            cls.MainFrameModule = MainFrameModule
            cls.PreferencesModule = PreferencesModule
            cls.WorkerThreadModule = WorkerThreadModule
            cls.BleachBitWxApp = BleachBitWxApp
            cls.app = wx.GetApp() or BleachBitWxApp(False)
            cls.frame = cls.app.GetTopWindow()
            if cls.frame is not None:
                cls.frame.Hide()
        except (Exception, SystemExit) as exc:
            super().tearDownClass()
            raise unittest.SkipTest(
                'requires wx display support: %s' % (exc,)) from exc

    @classmethod
    def tearDownClass(cls):
        """Destroy the shared frame and clean up wx resources."""
        app = getattr(cls, 'app', None)
        frame = getattr(cls, 'frame', None)
        if frame is not None:
            loader = getattr(frame, '_loader_thread', None)
            if loader is not None:
                loader.join(timeout=5.0)
            handler = getattr(frame, '_log_handler', None)
            if handler is not None:
                logging.getLogger('bleachbit').removeHandler(handler)
                frame._log_handler = None
            frame.Destroy()
            cls.frame = None
        if app is not None:
            # Flush pending events so no stale callbacks access destroyed
            # widgets during app teardown.
            try:
                app.ProcessPendingEvents()
            except Exception:
                pass
            # Exit the app's main loop if it is still running (e.g. after
            # the smoke test).  This releases internal wx threading state
            # (mutexes) that would otherwise segfault on interpreter exit.
            try:
                app.ExitMainLoop()
            except Exception:
                pass
            cls.app = None
        super().tearDownClass()

    def setUp(self):
        """Reset tree option state before each test."""
        super().setUp()
        for cleaner_id, option_id in (
                (BROWSER1_ID, 'cache'), (BROWSER1_ID, 'cookies'),
                (BROWSER2_ID, 'logs')):
            options.set_tree(cleaner_id, option_id, False)

    def _children(self, model, parent=None):
        """Return object children of a model item."""
        if parent is None:
            parent = self.MainFrameModule.dv.NullDataViewItem
        children = []
        count = model.GetChildren(parent, children)
        self.assertEqual(count, len(children))
        return [model.ItemToObject(child) for child in children]

    def test_bleachbit_wx_app_smoke_mainloop(self):
        """Run the wx App MainLoop briefly and exit."""
        self.assertIsInstance(self.app, self.BleachBitWxApp)
        self.assertIsNotNone(self.frame)
        wx.CallLater(WX_SMOKE_EXIT_MS, self.app.ExitMainLoop)
        self.app.MainLoop()
        # Drain any callbacks that were queued during the MainLoop but
        # not yet dispatched (e.g. pending CallAfter from worker threads).
        self.app.ProcessPendingEvents()
        loader = getattr(self.frame, '_loader_thread', None)
        if loader is not None:
            loader.join(timeout=5.0)
        self.assertIs(self.app.GetTopWindow(), self.frame)

    def test_cleaner_tree_model_filters_and_toggles(self):
        """Test _CleanerTreeModel filtering and check-state toggles."""
        model = self.MainFrameModule._CleanerTreeModel()
        model.set_data([
            (BROWSER1_ID, 'Fauxfox', [
                ('cache', 'Cache'),
                ('cookies', 'Cookies'),
            ]),
            (BROWSER2_ID, 'Pseudromium', [
                ('logs', 'Logs'),
            ]),
        ])

        self.assertEqual(
            [BROWSER1_ID, BROWSER2_ID],
            [node.cleaner_id for node in self._children(model)])

        model.set_filter('cook')
        visible_cleaners = self._children(model)
        self.assertEqual([BROWSER1_ID], [node.cleaner_id for node in visible_cleaners])
        b1_item = model.ObjectToItem(visible_cleaners[0])
        self.assertEqual(
            ['cookies'],
            [node.option_id for node in self._children(model, b1_item)])

        model.set_filter('faux')
        visible_cleaners = self._children(model)
        b1_item = model.ObjectToItem(visible_cleaners[0])
        self.assertEqual(
            ['cache', 'cookies'],
            [node.option_id for node in self._children(model, b1_item)])

        cache_item = model.ObjectToItem(model.option_node(BROWSER1_ID, 'cache'))
        self.assertTrue(model.SetValue(True, cache_item, 0))
        self.assertTrue(options.get_tree(BROWSER1_ID, 'cache'))
        self.assertTrue(model.GetValue(b1_item, 0))
        self.assertTrue(model.is_cleaner_partial(BROWSER1_ID))

        cleaner_attr = self.MainFrameModule.dv.DataViewItemAttr()
        self.assertTrue(model.GetAttr(b1_item, 1, cleaner_attr))

        self.assertTrue(model.SetValue(True, b1_item, 0))
        self.assertTrue(options.get_tree(BROWSER1_ID, 'cache'))
        self.assertTrue(options.get_tree(BROWSER1_ID, 'cookies'))
        self.assertFalse(model.is_cleaner_partial(BROWSER1_ID))

        self.assertTrue(model.SetValue(False, b1_item, 0))
        self.assertFalse(options.get_tree(BROWSER1_ID, 'cache'))
        self.assertFalse(options.get_tree(BROWSER1_ID, 'cookies'))
        self.assertFalse(model.GetValue(b1_item, 0))

    def test_results_rows_filter_and_sort(self):
        """Test results row filtering, errors-only, and sorting."""
        main_frame = self.MainFrameModule.MainFrame

        class FakeResults:
            def __init__(self):
                self.item_count = None
                self.refresh_count = 0

            def SetItemCount(self, count):
                self.item_count = count

            def Refresh(self):
                self.refresh_count += 1

        class ResultsOwner:
            _row_visible = main_frame._row_visible
            _refresh_results = main_frame._refresh_results
            _on_result_col_click = main_frame._on_result_col_click

        class Event:
            def __init__(self, column):
                self._column = column

            def GetColumn(self):
                return self._column

        owner = ResultsOwner()
        owner._errors_only = False
        owner._filter_text = ''
        owner.results = FakeResults()
        owner._rows = [
            {
                'cleaner_name': 'System', 'option_name': 'Cache',
                'path': '/tmp/b', 'size': 20, 'size_human': '20 B',
                'action': 'delete',
            },
            {
                'cleaner_name': 'Firefox', 'option_name': 'Cache',
                'path': '/home/user/.mozilla/cache', 'size': 5,
                'size_human': '5 B', 'action': 'truncate',
            },
            {
                'cleaner_name': 'Chromium', 'option_name': 'History',
                'path': '/home/user/.config/chromium', 'size': 10,
                'size_human': '10 B', 'action': 'delete',
            },
        ]
        owner._visible = owner._rows

        owner._refresh_results()
        self.assertIs(owner._visible, owner._rows)
        self.assertEqual(3, owner.results.item_count)

        owner._filter_text = 'mozilla'
        owner._refresh_results()
        self.assertEqual(
            ['/home/user/.mozilla/cache'],
            [row['path'] for row in owner._visible])

        owner._errors_only = True
        owner._refresh_results()
        self.assertEqual([], owner._visible)
        self.assertEqual(0, owner.results.item_count)

        owner._errors_only = False
        owner._filter_text = ''
        owner._on_result_col_click(Event(self.MainFrameModule.COL_SIZE))
        self.assertEqual([5, 10, 20], [row['size'] for row in owner._rows])
        self.assertEqual(4, owner.results.refresh_count)

    def test_wx_ui_proxy_batches_callbacks(self):
        """Test WxUIProxy event batching and rescheduling."""
        class Target:
            def __init__(self):
                self.calls = []
                self.batches = []

            def begin_batch(self):
                self.batches.append('begin')

            def end_batch(self):
                self.batches.append('end')

            def append_text(self, *args, **kwargs):
                self.calls.append(('append_text', args, kwargs))

        scheduled_after = []
        scheduled_later = []

        def call_after(func, *args, **kwargs):
            scheduled_after.append((func, args, kwargs))

        def call_later(delay, func, *args, **kwargs):
            scheduled_later.append((delay, func, args, kwargs))

        proxy_class = self.WorkerThreadModule.WxUIProxy
        target = Target()
        with mock.patch.object(proxy_class, '_CHUNK_SIZE', 2), \
                mock.patch.object(self.WorkerThreadModule.wx, 'CallAfter', call_after), \
                mock.patch.object(self.WorkerThreadModule.wx, 'CallLater', call_later):
            proxy = proxy_class(target)
            proxy.append_text('one')
            proxy.append_text('two')
            proxy.append_text('three', tag='error')
            self.assertEqual(1, len(scheduled_after))
            scheduled_after[0][0](*scheduled_after[0][1], **scheduled_after[0][2])
            self.assertEqual(['one', 'two'], [call[1][0] for call in target.calls])
            self.assertEqual(1, len(scheduled_later))
            # Second flush drains the queue; no further reschedule needed.
            scheduled_later[0][1](*scheduled_later[0][2], **scheduled_later[0][3])

        self.assertEqual(
            ['one', 'two', 'three'],
            [call[1][0] for call in target.calls])
        self.assertEqual(['begin', 'end', 'begin', 'end'], target.batches)
        self.assertEqual([], proxy.errors)
        with self.assertRaises(AttributeError):
            getattr(proxy, 'not_forwarded')

    def test_preferences_dialog_persists_options(self):
        """Test PreferencesDialog commits general and location options."""
        prefs = self.PreferencesModule
        saved = {key: options.get(key) for key, _label in prefs._PREFS}
        saved_whitelist = options.get_whitelist_paths()
        saved_custom = options.get_custom_paths()
        persistent_keys = [key for key in saved if key != 'debug']
        dialog = None
        try:
            for key in saved:
                options.set(key, False)
            options.set_whitelist_paths([])
            options.set_custom_paths([])
            dialog = prefs.PreferencesDialog(self.frame)
            for key, checkbox in dialog._checkboxes.items():
                if key in persistent_keys:
                    self.assertFalse(checkbox.GetValue(), key)
                checkbox.SetValue(True)
            dialog.commit()
            for key in persistent_keys:
                self.assertTrue(options.get(key))
            self.assertTrue(options.config.getboolean('bleachbit', 'debug'))

            keep_panel = prefs._LocationsPanel(dialog, prefs.LOCATIONS_WHITELIST)
            custom_panel = prefs._LocationsPanel(dialog, prefs.LOCATIONS_CUSTOM)
            keep_panel._add('/tmp/bleachbit-wx-keep', 'file')
            custom_panel._add('/tmp/bleachbit-wx-custom', 'folder')
            self.assertEqual(
                [('file', '/tmp/bleachbit-wx-keep')],
                options.get_whitelist_paths())
            self.assertEqual(
                [('folder', '/tmp/bleachbit-wx-custom')],
                options.get_custom_paths())
        finally:
            if dialog is not None:
                dialog.Destroy()
            for key, value in saved.items():
                options.set(key, value)
            options.set_whitelist_paths(saved_whitelist)
            options.set_custom_paths(saved_custom)
