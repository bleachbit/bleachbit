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

    def test_gtk_menu_mnemonics_are_converted_for_wx(self):
        """GTK catalog labels retain mnemonics without leaking syntax."""
        convert = self.MainFrameModule._gtk_mnemonic_to_wx
        self.assertEqual('&Shred Files', convert('_Shred Files'))
        self.assertEqual('Sh&red Folders', convert('Sh_red Folders'))
        self.assertEqual(
            'Literal _ underscore && ampersand',
            convert('Literal __ underscore & ampersand'))
        self.assertEqual('Trailing_', convert('Trailing_'))

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

    def _record_navigation(self, window):
        """Capture navigation events that reach ``window``.

        The events are not skipped, so keyboard focus does not move.
        """
        seen = []

        def on_navigate(evt):
            seen.append((evt.GetDirection(), evt.GetCurrentFocus()))

        window.Bind(wx.EVT_NAVIGATION_KEY, on_navigate)
        self.addCleanup(window.Unbind, wx.EVT_NAVIGATION_KEY,
                        handler=on_navigate)
        return seen

    @unittest.skipUnless(
        HAVE_WX and wx.Platform == '__WXMSW__', 'requires wxMSW')
    def test_tab_leaves_cleaner_tree(self):
        """Tab in the cleaner tree moves focus away (issue #2344)."""
        tree = self.frame.tree
        seen = self._record_navigation(tree.GetParent())
        for shift, key_code in ((False, wx.WXK_TAB), (True, wx.WXK_TAB),
                                (False, wx.WXK_RIGHT)):
            # Go through the real binding, as the key would on Windows.
            evt = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
            evt.SetKeyCode(key_code)
            evt.SetShiftDown(shift)
            evt.SetEventObject(tree.GetMainWindow())
            tree.GetMainWindow().GetEventHandler().ProcessEvent(evt)
        # Tab goes forward, Shift+Tab backward; Right stays in the tree.
        self.assertEqual([True, False], [fwd for fwd, _focus in seen])

    @unittest.skipUnless(
        HAVE_WX and wx.Platform == '__WXMSW__', 'requires wxMSW')
    def test_tab_leaves_results_list(self):
        """Tab in the Results list moves focus away (issue #2344)."""
        notebook = self.frame.notebook
        seen = self._record_navigation(notebook.GetParent())
        # On Windows the nearest ancestor with wx.TAB_TRAVERSAL turns
        # Tab into a navigation event it sends to itself.
        handler = self.frame.results
        while not handler.HasFlag(wx.TAB_TRAVERSAL):
            handler = handler.GetParent()
        evt = wx.NavigationKeyEvent()
        evt.SetDirection(True)
        evt.SetFromTab(True)
        evt.SetEventObject(handler)
        handler.GetEventHandler().ProcessEvent(evt)
        # The notebook passes Tab on to its parent instead of putting
        # focus back into the page.
        self.assertEqual([(True, notebook)], seen)

    def _send_context_menu(self, window, pos):
        """Send ``wx.EVT_CONTEXT_MENU`` from ``window`` at ``pos``."""
        evt = wx.ContextMenuEvent(
            wx.wxEVT_CONTEXT_MENU, window.GetId(), pos)
        evt.SetEventObject(window)
        window.GetEventHandler().ProcessEvent(evt)

    def test_keyboard_opens_tree_context_menu(self):
        """Shift+F10 in the cleaner tree opens its menu (issue #2352)."""
        tree = self.frame.tree
        option = self.MainFrameModule._OptionNode(
            BROWSER1_ID, 'cache', 'Cache')
        current = self.frame._tree_model.ObjectToItem(option)
        labels = []

        def popup_menu(menu, *_args):
            labels.extend(mi.GetItemLabelText()
                          for mi in menu.GetMenuItems())
            return True

        with mock.patch.object(tree, 'PopupMenu',
                               side_effect=popup_menu) as popup, \
                mock.patch.object(
                    tree, 'GetCurrentItem', return_value=current), \
                mock.patch.object(
                    tree, 'GetItemRect',
                    return_value=wx.Rect(10, 20, 30, 15)):
            # A mouse click is left to EVT_DATAVIEW_ITEM_CONTEXT_MENU.
            # wxOSX sends that from its own EVT_CONTEXT_MENU handler,
            # so the skipped event can still open one menu there.
            self._send_context_menu(tree.GetMainWindow(), wx.Point(5, 5))
            if wx.Platform == '__WXMAC__':
                self.assertLessEqual(popup.call_count, 1)
            else:
                popup.assert_not_called()
            popup.reset_mock()
            del labels[:]
            # Shift+F10 and the Menu key have no position; the menu is
            # for the focused option and opens at its row's rect.
            self._send_context_menu(
                tree.GetMainWindow(), wx.DefaultPosition)
            popup.assert_called_once()
            self.assertEqual(
                wx.Point(10, 35), popup.call_args[0][1])
        self.assertTrue(
            any(BROWSER1_ID in label for label in labels), labels)

    def test_keyboard_opens_results_context_menu(self):
        """Shift+F10 in the Results list opens its menu (issue #2352)."""
        results = self.frame.results
        row = {'path': 'C:\\a.txt', 'cleaner_id': BROWSER1_ID,
               'option_id': 'cache', 'cleaner_name': 'Browser',
               'option_name': 'Cache'}
        results.SetItemCount(1)
        results.Focus(0)
        rect = results.GetItemRect(0)
        pos = wx.Point(rect.GetLeft(), rect.GetBottom() + 1)
        with mock.patch.object(results, 'PopupMenu') as popup, \
                mock.patch.object(
                    self.frame, '_selected_rows', return_value=[row]):
            # A mouse click is left to EVT_LIST_ITEM_RIGHT_CLICK.
            self._send_context_menu(results, wx.Point(5, 5))
            popup.assert_not_called()
            # Shift+F10 and the Menu key have no position; the menu
            # opens at the focused row's rect.
            self._send_context_menu(results, wx.DefaultPosition)
            popup.assert_called_once()
            self.assertEqual(pos, popup.call_args[0][1])
        results.SetItemCount(0)

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

    def test_preferences_dialog_selects_interface_language(self):
        """Test the Languages page saves the interface language."""
        prefs = self.PreferencesModule
        langs = {'en_US': 'English', 'es': 'Español', 'zh_TW': '中文'}

        def active_language():
            # get_active_language_code() on an en_US system.
            if (not options.get('auto_detect_lang')
                    and options.get('forced_language')):
                return options.get('forced_language')
            return 'en_US'

        dialog = None
        try:
            options.set('auto_detect_lang', True)
            options.set('forced_language', '', section='bleachbit')
            with mock.patch.object(
                    prefs, 'get_supported_language_code_name_dict',
                    return_value=langs),                     mock.patch.object(
                        prefs, 'get_active_language_code',
                        side_effect=active_language),                     mock.patch.object(prefs, 'setup_translation') as setup:
                dialog = prefs.PreferencesDialog(self.frame)
                panel = next(
                    child for child in dialog.GetChildren()
                    if isinstance(child, wx.Notebook)).GetPage(1)
                self.assertIsInstance(panel, prefs._LanguagesPanel)
                self.assertFalse(dialog.language_changed)
                self.assertTrue(panel._cb_auto.GetValue())
                self.assertFalse(panel._choice.IsEnabled())
                self.assertEqual(
                    ['English (en_US)', 'Español (es)', '中文 (zh_TW)'],
                    panel._choice.GetItems())
                self.assertEqual(0, panel._choice.GetSelection())

                # Turning auto-detect off enables the dropdown.
                panel._cb_auto.SetValue(False)
                panel._on_auto_detect(None)
                self.assertFalse(options.get('auto_detect_lang'))
                self.assertTrue(panel._choice.IsEnabled())
                self.assertTrue(dialog.language_changed)

                # Choosing a language forces it.
                panel._choice.SetSelection(1)
                panel._on_language(None)
                self.assertEqual('es', options.get('forced_language'))

                # Turning auto-detect back on clears the forced language
                # and shows the system language again.
                panel._cb_auto.SetValue(True)
                panel._on_auto_detect(None)
                self.assertTrue(options.get('auto_detect_lang'))
                self.assertEqual('', options.get('forced_language'))
                self.assertFalse(panel._choice.IsEnabled())
                self.assertEqual(0, panel._choice.GetSelection())

                # Turning it off again keeps the system language, so the
                # dropdown must not show the old forced language.
                panel._cb_auto.SetValue(False)
                panel._on_auto_detect(None)
                self.assertEqual(0, panel._choice.GetSelection())
                self.assertEqual(4, setup.call_count)
        finally:
            if dialog is not None:
                dialog.Destroy()

    def test_cleaners_do_not_run_while_loading(self):
        """Cleaners cannot run while they are registered again."""
        frame = self.frame
        saved_loader = frame._loader_thread
        saved_buttons = [(btn, btn.IsEnabled()) for btn in (
            frame.btn_preview, frame.btn_clean, frame.btn_abort)]
        option = self.MainFrameModule._OptionNode(
            BROWSER1_ID, 'cache', 'Cache')
        items = []

        def popup_menu(menu, *_args):
            items.extend(mi.IsEnabled() for mi in menu.GetMenuItems())
            return True

        try:
            frame._loader_thread = object()
            with mock.patch.object(
                    self.MainFrameModule, 'WorkerThread') as worker:
                frame._start_worker(False, {BROWSER1_ID: ['cache']})
                worker.assert_not_called()
                # Shredding has its own cleaner, so it still runs (the
                # startup shred starts while cleaners load).
                frame._start_worker(True, {'_gui': ['files']})
                worker.assert_called_once()
            with mock.patch.object(
                    frame.tree, 'PopupMenu', side_effect=popup_menu):
                frame._show_tree_context_menu(
                    frame._tree_model.ObjectToItem(option))
        finally:
            frame._loader_thread = saved_loader
            frame._worker_thread = None
            for btn, enabled in saved_buttons:
                btn.Enable(enabled)
        # "Preview only" and "Clean only" are disabled; "Filter log by"
        # is not.
        self.assertEqual([False, False, True], items[:3])
