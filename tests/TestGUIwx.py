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
            from bleachbit.GUIwx import Accessibility as AccessibilityModule
            from bleachbit.GUIwx import MainFrame as MainFrameModule
            from bleachbit.GUIwx import PreferencesDialog as PreferencesModule
            from bleachbit.GUIwx import WorkerThread as WorkerThreadModule
            from bleachbit.GUIwx.App import BleachBitWxApp
            cls.AccessibilityModule = AccessibilityModule
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
        saved_whitelist = options.get_whitelist_paths()
        saved_custom = options.get_custom_paths()
        dialog = None
        saved = {}
        try:
            dialog = prefs.PreferencesDialog(self.frame)
            keys = list(dialog._checkboxes)
            saved = {key: options.get(key) for key in keys}
            dialog.Destroy()
            dialog = None
            # The pages and checkboxes of the GTK dialog, minus the
            # GTK rendering options.
            for key in ('shred', 'exit_done', 'delete_confirmation',
                        'auto_hide', 'units_iec', 'remember_geometry',
                        'debug', 'expert_mode', 'check_online_updates',
                        'check_beta'):
                self.assertIn(key, keys)
            self.assertNotIn('win10_theme', keys)
            self.assertNotIn('use_fontconfig_backend', keys)

            for key in keys:
                options.set(key, False)
            options.set_whitelist_paths([])
            options.set_custom_paths([])
            dialog = prefs.PreferencesDialog(self.frame)
            self.assertEqual(
                ['general', 'updates', 'languages', 'cookies', 'keep-list',
                 'custom', 'drives'], dialog._page_ids)
            for key, checkbox in dialog._checkboxes.items():
                if key != 'debug':
                    self.assertFalse(checkbox.GetValue(), key)
                checkbox.SetValue(True)
            with mock.patch(
                    'bleachbit.DesktopMenuOptions.install_kde_service_menu_file'):
                changed = dialog.commit()
            for key in keys:
                if key != 'debug':
                    self.assertTrue(options.get(key), key)
            self.assertTrue(options.config.getboolean('bleachbit', 'debug'))
            self.assertIn('auto_hide', changed)
            # Hiding irrelevant cleaners needs the tree to be reloaded.
            self.assertTrue(dialog.refresh_operations)

            keep_panel = prefs._LocationsPanel(dialog, prefs.LOCATIONS_WHITELIST)
            custom_panel = prefs._LocationsPanel(dialog, prefs.LOCATIONS_CUSTOM)
            keep_panel._add('/tmp/bleachbit-wx-keep', 'file')
            self.assertIn('/tmp/bleachbit-wx-keep',
                          dialog._infobar.get_message())
            with mock.patch.object(prefs.ProtectedPath,
                                   'check_protected_path', return_value=None):
                custom_panel._add('/tmp/bleachbit-wx-custom', 'folder')
            self.assertEqual(
                [('file', '/tmp/bleachbit-wx-keep')],
                options.get_whitelist_paths())
            self.assertEqual(
                [('folder', '/tmp/bleachbit-wx-custom')],
                options.get_custom_paths())
            # A path cannot be in both lists.
            custom_panel._add('/tmp/bleachbit-wx-keep', 'file')
            self.assertEqual(1, len(options.get_custom_paths()))
            keep_panel._list.Select(0)
            keep_panel._on_remove(None)
            self.assertEqual([], options.get_whitelist_paths())
        finally:
            if dialog is not None:
                dialog.Destroy()
            for key, value in saved.items():
                options.set(key, value)
            from bleachbit.Log import set_root_log_level
            set_root_log_level(options.get('debug'))
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
                panel = dialog.get_page('languages')
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

    def test_preferences_dependent_options(self):
        """Sub-options follow the option they depend on, as in GTK."""
        prefs = self.PreferencesModule
        keys = ('expert_mode', 'delete_confirmation', 'check_online_updates',
                'check_beta')
        saved = {key: options.get(key) for key in keys}
        dialog = None
        try:
            options.set('expert_mode', False)
            options.set('check_online_updates', False)
            dialog = prefs.PreferencesDialog(self.frame)
            boxes = dialog._checkboxes
            self.assertFalse(boxes['delete_confirmation'].IsEnabled())
            self.assertFalse(dialog._btn_reset_warnings.IsEnabled())
            self.assertFalse(boxes['check_beta'].IsEnabled())

            # Turning on expert mode asks first; Cancel keeps it off.
            boxes['expert_mode'].SetValue(True)
            with mock.patch.object(prefs, 'warning_confirm_dialog',
                                   return_value=(False, False)) as confirm:
                dialog._on_checkbox('expert_mode')
            confirm.assert_called_once()
            self.assertFalse(confirm.call_args.kwargs['show_checkbox'])
            self.assertFalse(boxes['expert_mode'].GetValue())
            self.assertFalse(boxes['delete_confirmation'].IsEnabled())

            boxes['expert_mode'].SetValue(True)
            with mock.patch.object(prefs, 'warning_confirm_dialog',
                                   return_value=(True, False)):
                dialog._on_checkbox('expert_mode')
            self.assertTrue(boxes['expert_mode'].GetValue())
            self.assertTrue(dialog.is_expert_mode())
            self.assertTrue(boxes['delete_confirmation'].IsEnabled())
            self.assertTrue(dialog._btn_reset_warnings.IsEnabled())
            # Not saved until OK.
            self.assertFalse(options.get('expert_mode'))

            boxes['check_online_updates'].SetValue(True)
            dialog._on_checkbox('check_online_updates')
            self.assertTrue(boxes['check_beta'].IsEnabled())

            options.remember_warning_preference('cleaner:a:b')
            dialog._on_reset_warnings(None)
            self.assertFalse(options.get_warning_preference('cleaner:a:b'))
            self.assertEqual(prefs._('Warning confirmations reset.'),
                             dialog._infobar.get_message())
        finally:
            if dialog is not None:
                dialog.Destroy()
            for key, value in saved.items():
                options.set(key, value)

    def test_custom_list_protected_path(self):
        """Protected paths need expert mode and a confirmation."""
        prefs = self.PreferencesModule
        saved_custom = options.get_custom_paths()
        saved_expert = options.get('expert_mode')
        dialog = None
        match = {'case_sensitive': True}
        path = '/tmp/bleachbit-wx-protected'
        try:
            options.set_custom_paths([])
            options.set('expert_mode', False)
            options.clear_warning_preferences()
            dialog = prefs.PreferencesDialog(self.frame)
            panel = dialog.get_page('custom')
            with mock.patch.object(prefs.ProtectedPath, 'check_protected_path',
                                   return_value=match), \
                    mock.patch.object(prefs.ProtectedPath, 'calculate_impact',
                                      return_value={}), \
                    mock.patch.object(prefs.ProtectedPath, 'get_warning_message',
                                      return_value='careful'):
                panel._add(path, 'folder')
                self.assertEqual([], options.get_custom_paths())
                self.assertEqual(
                    prefs._('This path is protected. To bypass protection, '
                            'enable expert mode.'),
                    dialog._infobar.get_message())

                dialog._checkboxes['expert_mode'].SetValue(True)
                with mock.patch.object(prefs, 'warning_confirm_dialog',
                                       return_value=(False, False)):
                    panel._add(path, 'folder')
                self.assertEqual([], options.get_custom_paths())

                with mock.patch.object(prefs, 'warning_confirm_dialog',
                                       return_value=(True, True)) as confirm:
                    panel._add(path, 'folder')
                self.assertEqual('careful', confirm.call_args.args[2])
                self.assertEqual([('folder', path)],
                                 options.get_custom_paths())
                key = 'protected_path:' + prefs.normalize_path(
                    path, case_sensitive=True)
                self.assertTrue(options.get_warning_preference(key))
        finally:
            if dialog is not None:
                dialog.Destroy()
            options.clear_warning_preferences()
            options.set('expert_mode', saved_expert)
            options.set_custom_paths(saved_custom)

    def test_drives_page_saves_shred_drives(self):
        """The Drives page edits shred_drives immediately."""
        prefs = self.PreferencesModule
        saved = options.get_list('shred_drives')
        dialog = None
        try:
            options.set_list('shred_drives', ['/tmp/b'])
            dialog = prefs.PreferencesDialog(self.frame, 'drives')
            self.assertEqual(
                dialog._page_ids.index('drives'),
                dialog._notebook.GetSelection())
            panel = dialog.get_page('drives')
            self.assertEqual(['/tmp/b'], panel._list.GetItems())
            panel.add_drive('/tmp/a')
            self.assertEqual(['/tmp/b', '/tmp/a'],
                             options.get_list('shred_drives'))
            panel._list.SetSelection(0)
            panel._on_remove(None)
            self.assertEqual(['/tmp/a'], options.get_list('shred_drives'))
            self.assertEqual(['/tmp/a'], panel._list.GetItems())
        finally:
            if dialog is not None:
                dialog.Destroy()
            options.set_list('shred_drives', saved or [])

    def test_cookies_page_keeps_selected_hosts(self):
        """The Cookies page saves the checked hosts to the keep list."""
        import json
        import os
        import tempfile
        prefs = self.PreferencesModule

        class Event:
            def __init__(self, index):
                self._index = index

            def GetIndex(self):
                return self._index

        dialog = None
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                dialog = prefs.PreferencesDialog(self.frame)
                panel = dialog.get_page('cookies')
                self.assertFalse(panel._loaded)
                panel.keep_list_path = os.path.join(tmpdir, 'keep.json')
                panel.saved_domains = {'b.example'}
                panel._finish_populate(['a.example', 'C.example', ''])
                self.assertEqual(
                    ['a.example', 'b.example', 'C.example'],
                    [panel._list.GetItemText(i)
                     for i in range(panel._list.GetItemCount())])
                self.assertTrue(panel._list.IsItemChecked(1))
                # The plural form follows the kept count, as in GTK.
                self.assertEqual(
                    prefs._n('%(selected)d of %(total)d cookie kept',
                             '%(selected)d of %(total)d cookies kept', 1)
                    % {'selected': 1, 'total': 3},
                    panel._stat_label.GetLabel())

                panel._on_item_toggled(Event(0), True)
                with open(panel.keep_list_path, encoding='utf-8') as f:
                    self.assertEqual(['a.example', 'b.example'], json.load(f))

                panel._search.SetValue('c.')
                self.assertEqual(1, panel._list.GetItemCount())
                self.assertEqual(
                    prefs._n('%(selected)d of %(total)d cookie kept (%(visible)d visible)',
                             '%(selected)d of %(total)d cookies kept (%(visible)d visible)',
                             2) % {'selected': 2, 'total': 3, 'visible': 1},
                    panel._stat_label.GetLabel())
                panel._set_visible_selection(True)
                panel._search.SetValue('')
                with open(panel.keep_list_path, encoding='utf-8') as f:
                    self.assertEqual(
                        ['C.example', 'a.example', 'b.example'], json.load(f))

                # A checkbox, so screen readers report it as on or off.
                self.assertIsInstance(panel._selected_toggle, wx.CheckBox)
                panel._selected_toggle.SetValue(True)
                panel._on_selected_toggle(None)
                self.assertEqual(3, panel._list.GetItemCount())
                panel._set_visible_selection(False)
                self.assertEqual(0, panel._list.GetItemCount())
                with open(panel.keep_list_path, encoding='utf-8') as f:
                    self.assertEqual([], json.load(f))
            finally:
                if dialog is not None:
                    dialog.Destroy()

    def test_cookie_notice_link_markup(self):
        """The GTK link markup is split for a native link control."""
        split = self.PreferencesModule._split_link_markup
        self.assertEqual(
            ('Only cookies. ', 'Learn more', ''),
            split("Only cookies. <a href='{url}'>Learn more</a>"))
        self.assertEqual(
            ('A & B', None, ''), split('A &amp; B'))

    def test_notice_bar_is_announced(self):
        """Notices and tooltips are exposed to screen readers."""
        acc_module = self.AccessibilityModule
        frame = wx.Frame(None)
        try:
            bar = acc_module.NoticeBar(frame)
            checkbox = wx.CheckBox(frame, label='Exit after cleaning')
            acc_module.set_tooltip(checkbox, 'More details')
            listbox = wx.ListBox(frame)
            acc_module.set_accessible_name(listbox, 'Drives')
            with mock.patch.object(wx.Accessible, 'NotifyEvent',
                                   create=True) as notify:
                bar.show_notice('Restart BleachBit for full effect.')
                bar.show_notice('Restart BleachBit for full effect.')
            self.assertEqual('Restart BleachBit for full effect.',
                             bar.get_message())
            self.assertEqual('More details', checkbox.GetToolTipText())
            self.assertEqual('Drives', listbox.GetName())
            if not acc_module._HAVE_MSAA:
                return
            # Announced once, as an alert carrying the message.
            notify.assert_called_once()
            self.assertEqual(wx.ACC_EVENT_SYSTEM_ALERT,
                             notify.call_args.args[0])
            acc = bar._alert_window._bb_accessible
            self.assertEqual((wx.ACC_OK, wx.ROLE_SYSTEM_ALERT),
                             acc.GetRole(wx.ACC_SELF))
            self.assertEqual(
                (wx.ACC_OK, 'Restart BleachBit for full effect.'),
                acc.GetName(wx.ACC_SELF))
            self.assertEqual(
                (wx.ACC_OK, 'More details'),
                checkbox._bb_accessible.GetDescription(wx.ACC_SELF))
            self.assertEqual(
                (wx.ACC_OK, 'Drives'),
                listbox._bb_accessible.GetName(wx.ACC_SELF))
        finally:
            frame.Destroy()

    def test_described_checkbox_is_still_a_checkbox(self):
        """A checkbox with a description reads as a checkbox, not a button.

        In dark mode wx draws checkboxes itself, so the system reports
        them as push buttons unless the accessible object says otherwise.
        """
        acc_module = self.AccessibilityModule
        if not acc_module._HAVE_MSAA:
            self.skipTest('MSAA is only available on Windows')
        frame = wx.Frame(None)
        try:
            checkbox = wx.CheckBox(frame, label='Expert mode')
            acc_module.set_tooltip(checkbox, 'More details')
            acc = checkbox._bb_accessible
            self.assertEqual((wx.ACC_OK, wx.ROLE_SYSTEM_CHECKBUTTON),
                             acc.GetRole(wx.ACC_SELF))
            status, state = acc.GetState(wx.ACC_SELF)
            self.assertEqual(wx.ACC_OK, status)
            self.assertTrue(state & wx.ACC_STATE_SYSTEM_FOCUSABLE)
            self.assertFalse(state & wx.ACC_STATE_SYSTEM_CHECKED)
            checkbox.SetValue(True)
            checkbox.Disable()
            _status, state = acc.GetState(wx.ACC_SELF)
            self.assertTrue(state & wx.ACC_STATE_SYSTEM_CHECKED)
            self.assertTrue(state & wx.ACC_STATE_SYSTEM_UNAVAILABLE)
            # Other controls keep the system role.
            button = wx.Button(frame, label='Reset')
            acc_module.set_tooltip(button, 'More details')
            self.assertEqual(
                wx.ACC_NOT_IMPLEMENTED,
                button._bb_accessible.GetRole(wx.ACC_SELF)[0])
        finally:
            frame.Destroy()

    def _register_fake_cleaner(self):
        """Register a cleaner whose 'cache' option has a warning."""
        from bleachbit.Cleaner import backends

        class FakeCleaner:
            auto_hide_result = True

            def get_name(self):
                return 'Fauxfox'

            def get_options(self):
                return [('cache', 'Cache'), ('cookies', 'Cookies')]

            def get_warning(self, option_id):
                return 'Risky' if option_id == 'cache' else None

            def has_action_key(self, option_id, action_key):
                return option_id == 'cookies' and action_key == 'cookie'

            def auto_hide(self):
                return self.auto_hide_result

        saved = backends.get(BROWSER1_ID)
        backends[BROWSER1_ID] = FakeCleaner()

        def restore():
            if saved is None:
                backends.pop(BROWSER1_ID, None)
            else:
                backends[BROWSER1_ID] = saved
        self.addCleanup(restore)
        return backends[BROWSER1_ID]

    def test_expert_mode_guards_warning_options(self):
        """Warning options need expert mode, as in the GTK GUI."""
        frame = self.frame
        module = self.MainFrameModule
        self._register_fake_cleaner()
        saved_expert = options.get('expert_mode')
        try:
            options.set('expert_mode', False)
            options.clear_warning_preferences()
            # Checking a protected option is refused.
            self.assertFalse(frame._allow_enable(BROWSER1_ID, 'cache'))
            self.assertEqual(
                module._('This option is protected. To bypass protection, '
                         'enable expert mode.'),
                frame.infobar.get_message())
            self.assertTrue(frame._allow_enable(BROWSER1_ID, 'cookies'))
            # Cleaning drops it and logs why; preview keeps it.
            ops = {BROWSER1_ID: ['cache', 'cookies']}
            self.assertEqual(
                {BROWSER1_ID: ['cookies']},
                frame._filter_operations_for_expert_mode(ops))
            self.assertIn('Fauxfox - Cache', frame._log_entries[-1][0])
            self.assertEqual('error', frame._log_entries[-1][1])
            with mock.patch.object(module, 'WorkerThread') as worker:
                frame._start_worker(True, {BROWSER1_ID: ['cache']})
                worker.assert_not_called()
            self.assertEqual(module.REQUIRES_EXPERT_MODE,
                             frame.infobar.get_message())
            # "Clean only" from the tree menu is blocked too.
            with mock.patch.object(frame, '_start_worker') as start:
                frame._run_single_option(BROWSER1_ID, 'cache', True)
                start.assert_not_called()

            # In expert mode, the warning is confirmed after the click.
            options.set('expert_mode', True)
            self.assertEqual(ops, frame._filter_operations_for_expert_mode(ops))
            with mock.patch.object(module.wx, 'CallAfter') as call_after:
                self.assertFalse(frame._allow_enable(BROWSER1_ID, 'cache'))
            call_after.assert_called_once()
            with mock.patch.object(module, 'warning_confirm_dialog',
                                   return_value=(True, True)) as confirm:
                frame._confirm_pending_warnings()
            self.assertEqual('Fauxfox - Cache', confirm.call_args.args[1])
            self.assertTrue(options.get_tree(BROWSER1_ID, 'cache'))
            # The remembered choice skips the dialog next time.
            self.assertTrue(frame._allow_enable(BROWSER1_ID, 'cache'))
        finally:
            frame._pending_warnings = []
            frame._confirming_warnings = False
            options.clear_warning_preferences()
            options.set('expert_mode', saved_expert)

    def test_delete_confirmation_needs_expert_mode(self):
        """Only expert mode can skip the delete confirmation."""
        frame = self.frame
        module = self.MainFrameModule
        saved = {key: options.get(key)
                 for key in ('expert_mode', 'delete_confirmation')}
        try:
            for expert, confirm, asks in ((False, False, True),
                                          (False, True, True),
                                          (True, True, True),
                                          (True, False, False)):
                options.set('expert_mode', expert)
                options.set('delete_confirmation', confirm)
                with mock.patch.object(module, 'delete_confirmation_dialog',
                                       return_value=False) as dialog:
                    result = frame._confirm_delete(True)
                self.assertEqual(asks, dialog.called)
                self.assertEqual(not asks, result)
        finally:
            for key, value in saved.items():
                options.set(key, value)

    def test_exit_after_cleaning(self):
        """'Exit after cleaning' closes the window after a clean."""
        frame = self.frame
        saved = options.get('exit_done')

        class Worker:
            is_aborted = False

        try:
            options.set('exit_done', True)
            with mock.patch.object(frame, 'Close') as close:
                frame.worker_done(Worker(), False)
                close.assert_not_called()
                frame.worker_done(Worker(), True)
                close.assert_called_once()
        finally:
            options.set('exit_done', saved)
            frame.btn_preview.Enable()
            frame.btn_clean.Enable()

    def test_window_geometry_is_remembered(self):
        """The window geometry is saved on close and restored."""
        frame = self.frame
        keys = ('remember_geometry', 'window_x', 'window_y', 'window_width',
                'window_height', 'window_maximized')
        saved = {key: options.config.get('bleachbit', key, fallback=None)
                 for key in keys}
        try:
            with mock.patch.object(frame, 'IsMaximized', return_value=False), \
                    mock.patch.object(frame, 'GetRect',
                                      return_value=wx.Rect(10, 20, 800, 600)):
                frame._save_geometry()
            self.assertEqual((10, 20, 800, 600), tuple(
                options.get(key) for key in keys[1:5]))
            self.assertFalse(options.get('window_maximized'))

            options.set('remember_geometry', True)
            options.set('window_maximized', True)
            with mock.patch.object(frame, 'SetRect') as set_rect, \
                    mock.patch.object(frame, 'Maximize') as maximize, \
                    mock.patch.object(self.MainFrameModule.wx.Display,
                                      'GetFromPoint', return_value=0):
                frame._restore_geometry()
            set_rect.assert_called_once_with(wx.Rect(10, 20, 800, 600))
            maximize.assert_called_once()

            options.set('remember_geometry', False)
            with mock.patch.object(frame, 'SetRect') as set_rect:
                frame._restore_geometry()
            set_rect.assert_not_called()
        finally:
            for key, value in saved.items():
                if value is None:
                    options.config.remove_option('bleachbit', key)
                else:
                    options.config.set('bleachbit', key, value)

    def test_auto_hide_option(self):
        """'Hide irrelevant cleaners' controls which cleaners are hidden."""
        from bleachbit.GUIwx import LoaderThread
        self._register_fake_cleaner()
        saved = options.get('auto_hide')
        try:
            options.set('auto_hide', True)
            self.assertIn(BROWSER1_ID, LoaderThread._compute_auto_hidden())
            # A cleaner with a checked option is not hidden.
            options.set_tree(BROWSER1_ID, 'cookies', True)
            self.assertNotIn(BROWSER1_ID, LoaderThread._compute_auto_hidden())
            options.set_tree(BROWSER1_ID, 'cookies', False)
            options.set('auto_hide', False)
            self.assertNotIn(BROWSER1_ID, LoaderThread._compute_auto_hidden())
        finally:
            options.set('auto_hide', saved)

    def test_tree_menu_opens_preferences_pages(self):
        """The tree menu opens the Cookies page for cookie options."""
        frame = self.frame
        self._register_fake_cleaner()
        option = self.MainFrameModule._OptionNode(
            BROWSER1_ID, 'cookies', 'Cookies')
        labels = []

        def popup_menu(menu, *_args):
            labels.extend(mi.GetItemLabelText()
                          for mi in menu.GetMenuItems())
            return True

        with mock.patch.object(frame.tree, 'PopupMenu',
                               side_effect=popup_menu):
            frame._show_tree_context_menu(
                frame._tree_model.ObjectToItem(option))
        self.assertIn(
            self.MainFrameModule._('Manage cookies to keep…'), labels)

    def test_languages_page_keep_list(self):
        """On POSIX, the Languages page lists language files to keep."""
        prefs = self.PreferencesModule
        langs = {'en_US': 'English', 'es': 'Español'}
        saved = {lang: options.get_language(lang) for lang in langs}
        dialog = None
        try:
            options.set_language('es', False)
            with mock.patch.object(prefs, 'IS_POSIX', True), \
                    mock.patch.object(
                        prefs, 'get_supported_language_code_name_dict',
                        return_value=langs):
                dialog = prefs.PreferencesDialog(self.frame, 'languages')
            panel = dialog.get_page('languages')
            keep = panel._keep_list
            self.assertIsNotNone(keep)
            self.assertEqual(2, keep.GetItemCount())
            self.assertEqual('es', keep.GetTextValue(1, 1))
            self.assertFalse(keep.GetToggleValue(1, 0))
            # Toggling Keep saves the language at once.
            keep.SetToggleValue(True, 1, 0)

            class Event:
                def GetColumn(self):
                    return 0

                def GetItem(self):
                    return keep.RowToItem(1)

            panel._on_keep_language(Event())
            self.assertTrue(options.get_language('es'))
        finally:
            if dialog is not None:
                dialog.Destroy()
            for lang, value in saved.items():
                options.set_language(lang, value)

    def test_confirmation_dialogs(self):
        """Confirmations default to Cancel, which Escape also chooses."""
        from bleachbit.GUIwx import Dialogs
        saved = {key: options.get(key)
                 for key in ('expert_mode', 'delete_confirmation')}
        created = []

        class FakeDialog:
            result = wx.ID_OK
            checked = False

            def __init__(self, parent, message, caption, style):
                self.message = message
                self.caption = caption
                self.style = style
                self.labels = None
                self.checkbox = None
                created.append(self)

            def SetOKCancelLabels(self, ok, cancel):
                self.labels = (ok, cancel)
                return True

            def ShowCheckBox(self, label, checked=False):
                self.checkbox = (label, checked)

            def IsCheckBoxChecked(self):
                return FakeDialog.checked

            def ShowModal(self):
                return FakeDialog.result

            def Destroy(self):
                pass

        try:
            with mock.patch.object(Dialogs.wx, 'RichMessageDialog',
                                   FakeDialog):
                options.set('expert_mode', False)
                self.assertTrue(Dialogs.delete_confirmation_dialog(None, True))
                dlg = created[-1]
                self.assertTrue(dlg.style & wx.CANCEL)
                self.assertTrue(dlg.style & wx.CANCEL_DEFAULT)
                self.assertNotIn('_', dlg.labels[0])
                self.assertIsNone(dlg.checkbox)

                # In expert mode the dialog can turn the confirmation off.
                options.set('expert_mode', True)
                options.set('delete_confirmation', True)
                FakeDialog.result = wx.ID_CANCEL
                self.assertFalse(Dialogs.delete_confirmation_dialog(None, False))
                self.assertEqual(True, created[-1].checkbox[1])
                self.assertFalse(options.get('delete_confirmation'))

                FakeDialog.result = wx.ID_OK
                FakeDialog.checked = True
                self.assertEqual(
                    (True, True),
                    Dialogs.warning_confirm_dialog(None, 'X', 'Risky'))
                self.assertIsNotNone(created[-1].checkbox)
                self.assertEqual(
                    (True, False),
                    Dialogs.warning_confirm_dialog(None, 'X', 'Risky',
                                                   show_checkbox=False))
                self.assertIsNone(created[-1].checkbox)
                FakeDialog.result = wx.ID_CANCEL
                self.assertEqual(
                    (False, False),
                    Dialogs.warning_confirm_dialog(None, 'X', 'Risky'))
        finally:
            for key, value in saved.items():
                options.set(key, value)
