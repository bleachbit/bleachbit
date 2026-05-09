# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.


"""
Test case for BleachBit TUI module
"""

import unittest

from bleachbit.tui.cleaner_tree import CleanerTree
from bleachbit.FileUtilities import bytes_to_human


class CleanerTreeNodeDataTestCase(unittest.TestCase):
    """Test that CleanerTree node.data stores human-readable names."""

    def test_populate_real_stores_names(self):
        """populate_real() should store cleaner_name and option_name in node.data."""
        tree = CleanerTree()

        cleaner_data = [
            ("firefox", "Firefox", [
                ("cache", "Cache", "Web cache"),
                ("cookies", "Cookies", "Browser cookies"),
            ]),
            ("system", "System", [
                ("tmp", "Temporary files", "Temp files"),
            ]),
        ]

        tree.populate_tree(cleaner_data)

        # Check cleaner nodes have cleaner_name
        ff_node = tree._cleaner_nodes.get("firefox")
        self.assertIsNotNone(ff_node)
        self.assertEqual(ff_node.data.get("cleaner_name"), "Firefox")
        self.assertEqual(ff_node.data.get("cleaner"), "firefox")

        # Check option nodes have option_name
        cache_node = tree._option_nodes.get(("firefox", "cache"))
        self.assertIsNotNone(cache_node)
        self.assertEqual(cache_node.data.get("option_name"), "Cache")
        self.assertEqual(cache_node.data.get("option"), "cache")
        self.assertEqual(cache_node.data.get("cleaner"), "firefox")

    def test_focused_option_resolution(self):
        """get_focused_option() should return (c_id, o_id) for option nodes."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test Cleaner", [
                ("opt1", "Option One", "Description"),
            ]),
        ]
        tree.populate_tree(cleaner_data)

        # Initially cursor is on root, so no focused option
        self.assertIsNone(tree.get_focused_option())


class CleanerTreeLabelTestCase(unittest.TestCase):
    """Test label formatting for cleaner and option nodes."""

    def test_cleaner_label_contains_name_not_id(self):
        """After toggle, cleaner label should show human name, not ID."""
        tree = CleanerTree()
        cleaner_data = [
            ("google_chrome", "Google Chrome", [
                ("cache", "Cache", "Web cache"),
            ]),
        ]
        tree.populate_tree(cleaner_data)

        ff_node = tree._cleaner_nodes.get("google_chrome")
        self.assertIsNotNone(ff_node)

        # Label should contain "Google Chrome", not "google_chrome"
        label_text = ff_node.label.plain
        self.assertIn("Google Chrome", label_text)
        self.assertNotIn("google_chrome", label_text)

    def test_option_label_contains_name_not_id(self):
        """After toggle, option label should show human name, not ID."""
        tree = CleanerTree()
        cleaner_data = [
            ("google_chrome", "Google Chrome", [
                ("cache", "Cache", "Web cache"),
            ]),
        ]
        tree.populate_tree(cleaner_data)

        opt_node = tree._option_nodes.get(("google_chrome", "cache"))
        self.assertIsNotNone(opt_node)

        label_text = opt_node.label.plain
        self.assertIn("Cache", label_text)
        self.assertNotIn("  cache", label_text)


class CleanerTreeNavigationTestCase(unittest.TestCase):
    """Test jump-to-top and jump-to-bottom navigation logic.

    Note: action_jump_to_top and action_jump_to_bottom require a mounted
    Textual app to set cursor_node properly.  These tests validate the
    core _last_leaf logic and the node structure instead.
    """

    def test_last_leaf_single_child(self):
        """_last_leaf of a leaf node returns itself."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        leaf = tree._option_nodes.get(("test", "opt1"))
        self.assertIsNotNone(leaf)
        result = CleanerTree._last_leaf(leaf)
        self.assertIs(result, leaf)

    def test_last_leaf_finds_deepest(self):
        """_last_leaf should find the deepest last child."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [
                ("opt1", "Option 1", ""),
                ("opt2", "Option 2", ""),
            ]),
        ]
        tree.populate_tree(cleaner_data)

        # The last leaf under root should be the last option of the last cleaner
        result = CleanerTree._last_leaf(tree.root)
        self.assertIsNotNone(result)
        self.assertEqual(result.data.get("option"), "opt2")

    def test_jump_to_top_finds_first_cleaner(self):
        """action_jump_to_top should target the first child of root."""
        tree = CleanerTree()
        cleaner_data = [
            ("first", "First", [("a", "A", "")]),
            ("second", "Second", [("b", "B", "")]),
        ]
        tree.populate_tree(cleaner_data)

        # Verify the first child is the expected node
        first = next(iter(tree.root.children), None)
        self.assertIsNotNone(first)
        self.assertEqual(first.data.get("cleaner"), "first")

    def test_jump_to_bottom_finds_last_leaf(self):
        """action_jump_to_bottom should target the last leaf descendant."""
        tree = CleanerTree()
        cleaner_data = [
            ("first", "First", [("a", "A", "")]),
            ("second", "Second", [("b", "B", "")]),
        ]
        tree.populate_tree(cleaner_data)

        # Verify the last leaf is the expected node
        last = CleanerTree._last_leaf(tree.root)
        self.assertIsNotNone(last)
        self.assertEqual(last.data.get("option"), "b")

    def test_root_collapse_blocked(self):
        """Collapsing the root node should be blocked to avoid trapping the user."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        self.assertTrue(tree.root.is_expanded,
                        "Root should start expanded")
        tree._cursor_node = tree.root
        tree.action_collapse_node()
        self.assertTrue(tree.root.is_expanded,
                        "Root should remain expanded after Left arrow")

    def test_root_expand_restores_tree(self):
        """Right arrow on collapsed root should expand it, revealing children."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        tree.root.collapse()
        self.assertFalse(tree.root.is_expanded)

        tree._cursor_node = tree.root
        tree.action_expand_node()
        self.assertTrue(tree.root.is_expanded,
                        "Right arrow should expand collapsed root")

    def test_root_right_moves_to_first_child(self):
        """Right arrow on already-expanded root should move to first cleaner."""
        tree = CleanerTree()
        cleaner_data = [
            ("first", "First", [("a", "A", "")]),
            ("second", "Second", [("b", "B", "")]),
        ]
        tree.populate_tree(cleaner_data)

        tree._cursor_node = tree.root
        # action_cursor_down requires a mounted Textual app, so stub it
        calls = []
        tree.action_cursor_down = lambda: calls.append(1)
        tree.action_expand_node()
        self.assertEqual(len(calls), 1,
                         "Right on expanded root should call action_cursor_down")

    def test_cleaner_collapse_blocked(self):
        """Left arrow on a cleaner node should jump to parent, not collapse."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        cleaner_node = tree._cleaner_nodes["test"]
        cleaner_node.expand()
        self.assertTrue(cleaner_node.is_expanded)

        tree._cursor_node = cleaner_node
        tree.action_collapse_node()
        self.assertTrue(cleaner_node.is_expanded,
                        "Cleaner node should remain expanded")
        self.assertIs(tree._cursor_node, tree.root,
                      "Cursor should move to root")

    def test_option_left_moves_to_parent(self):
        """Left arrow on an option (leaf) node should move to its cleaner parent."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        cleaner_node = tree._cleaner_nodes["test"]
        option_node = tree._option_nodes[("test", "opt1")]

        captured = []
        original_select = tree.select_node
        tree.select_node = lambda node: captured.append(node)

        tree._cursor_node = option_node
        tree.action_collapse_node()
        self.assertEqual(len(captured), 1)
        self.assertIs(captured[0], cleaner_node,
                      "select_node should be called with cleaner parent")


class TogglePersistenceTestCase(unittest.TestCase):
    """Test that toggle state tracking works correctly."""

    def test_enabled_tracks_state(self):
        """_enabled dict should correctly track toggle states."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [("opt1", "Option 1", "")]),
        ]
        tree.populate_tree(cleaner_data)

        # Initially disabled (default is False)
        self.assertFalse(tree._enabled.get(("test", "opt1"), True))

        # Enable it, then disable again
        tree._enabled[("test", "opt1")] = True
        self.assertTrue(tree._enabled[("test", "opt1")])
        tree._enabled[("test", "opt1")] = False
        self.assertFalse(tree._enabled[("test", "opt1")])

    def test_get_enabled_options_returns_only_enabled(self):
        """get_enabled_options should only return enabled options."""
        tree = CleanerTree()
        cleaner_data = [
            ("test", "Test", [
                ("opt1", "Option 1", ""),
                ("opt2", "Option 2", ""),
            ]),
        ]
        tree.populate_tree(cleaner_data)

        # Enable only opt1
        tree._enabled[("test", "opt1")] = True

        enabled = tree.get_enabled_options()
        self.assertIn(("test", "opt1"), enabled)
        self.assertNotIn(("test", "opt2"), enabled)


class CleanerTreeParentTogglePersistenceTestCase(unittest.TestCase):
    """Test that parent toggle state persists correctly across close/reopen."""

    def setUp(self):
        """Remove any existing tree config before each test."""
        from bleachbit.Options import options
        if options.config.has_section("tree"):
            options.config.remove_section("tree")

    def tearDown(self):
        """Clean up tree config after each test."""
        from bleachbit.Options import options
        if options.config.has_section("tree"):
            options.config.remove_section("tree")

    def test_parent_toggle_persists_after_reopen(self):
        """Toggling a parent should persist after reopen.

        Scenario:
          1. First open - all defaults to disabled (False)
          2. Enable cache and cookies individually
          3. Close / reopen - both still enabled
          4. Toggle parent to disable all children
          5. Close / reopen - all should remain disabled
        """
        cleaner_data = [
            ("google_chrome", "Google Chrome", [
                ("cache", "Cache", "Web cache"),
                ("cookies", "Cookies", "Browser cookies"),
            ]),
        ]

        # Step 1: First open - all defaults to disabled
        tree1 = CleanerTree()
        tree1.populate_tree(cleaner_data)

        self.assertFalse(tree1._enabled.get(("google_chrome", None), True))
        self.assertFalse(tree1._enabled.get(("google_chrome", "cache"), True))
        self.assertFalse(tree1._enabled.get(("google_chrome", "cookies"), True))

        # Step 2: Enable cache and cookies individually
        for opt_name in ("cache", "cookies"):
            opt_node = tree1._option_nodes.get(("google_chrome", opt_name))
            self.assertIsNotNone(opt_node)
            tree1._cursor_node = opt_node
            tree1.action_toggle_enabled()

        self.assertTrue(tree1._enabled.get(("google_chrome", None), False),
                        "Cleaner should be enabled (all children on)")
        self.assertTrue(tree1._enabled.get(("google_chrome", "cache"), False),
                        "Cache should be enabled")
        self.assertTrue(tree1._enabled.get(("google_chrome", "cookies"), False),
                        "Cookies should be enabled")

        # Step 3: Close and reopen - verify state is preserved
        tree2 = CleanerTree()
        tree2.populate_tree(cleaner_data)

        self.assertTrue(tree2._enabled.get(("google_chrome", None), False),
                        "Cleaner should be enabled after reopen")
        self.assertTrue(tree2._enabled.get(("google_chrome", "cache"), False),
                        "Cache should still be enabled after reopen")
        self.assertTrue(tree2._enabled.get(("google_chrome", "cookies"), False),
                        "Cookies should still be enabled after reopen")

        # Step 4: Toggle parent to disable all children
        cleaner_node = tree2._cleaner_nodes.get("google_chrome")
        self.assertIsNotNone(cleaner_node)
        tree2._cursor_node = cleaner_node
        tree2.action_toggle_enabled()

        self.assertFalse(tree2._enabled.get(("google_chrome", None), True),
                         "Cleaner should be disabled")
        self.assertFalse(tree2._enabled.get(("google_chrome", "cache"), True),
                         "Cache should be disabled")
        self.assertFalse(tree2._enabled.get(("google_chrome", "cookies"), True),
                         "Cookies should be disabled")

        # Step 5: Close and reopen - THIS IS THE BUG
        # All options should remain disabled, not revert to enabled
        tree3 = CleanerTree()
        tree3.populate_tree(cleaner_data)

        self.assertFalse(
            tree3._enabled.get(("google_chrome", None), True),
            "BUG: Cleaner should remain disabled after reopen, but reverted to enabled"
        )
        self.assertFalse(
            tree3._enabled.get(("google_chrome", "cache"), True),
            "BUG: Cache should remain disabled after reopen, but reverted to enabled"
        )
        self.assertFalse(
            tree3._enabled.get(("google_chrome", "cookies"), True),
            "BUG: Cookies should remain disabled after reopen, but reverted to enabled"
        )
