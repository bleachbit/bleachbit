# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""CleanerTree — custom Textual Tree widget for the TUI.

Provides two-axis keyboard navigation (↑↓ within depth, ←→ change depth),
enable/disable toggles (Space), file list display (Enter), and live counters.

Toggle states are persisted via Options.options.get_tree/set_tree.
"""

from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from textual.binding import Binding
from textual.message import Message
from rich.text import Text

from bleachbit.FileUtilities import bytes_to_human
from bleachbit.Options import options
from bleachbit.Language import get_text as _, nget_text as ngettext


class CleanerTree(Tree):
    """Custom tree widget for navigating cleaners and options.

    Three-level tree:
      Level 0 (root)   — Total: X files, Y MB
      Level 1          — Cleaner (e.g., Chrome): X files, Y MB  [enabled/disabled]
      Level 2          — Option (e.g., Cache): X files, Y MB    [enabled/disabled] [errors]

    Key bindings:
      - Right / Left — expand / collapse the focused node
      - Space toggles enable/disable
      - Enter shows file list for option nodes
    """

    BINDINGS = [
        Binding("space", "toggle_enabled", _("Toggle enable/disable"), show=True),
        Binding("enter", "show_file_list", _("Show file list"), show=True),
        Binding("right", "expand_node", _("Expand"), show=False),
        Binding("left", "collapse_node", _("Collapse"), show=False),
        Binding("g", "jump_to_top", _("Jump to top"), show=False),
        Binding("G", "jump_to_bottom", _("Jump to bottom"), show=False),
        Binding("home", "jump_to_top", _("Jump to top"), show=False),
        Binding("end", "jump_to_bottom", _("Jump to bottom"), show=False),
    ]

    class OptionSelected(Message):
        """Posted when user presses Enter on an option node."""
        def __init__(self, cleaner_name: str, option_name: str):
            super().__init__()
            self.cleaner_name = cleaner_name
            self.option_name = option_name

    def __init__(self):
        super().__init__(_("BleachBit Cleaners"))
        self.root.allow_expand = False
        self._enabled: dict[tuple, bool] = {}  # (cleaner_id, option_id) -> bool
        self._cleaner_nodes: dict[str, TreeNode] = {}  # cleaner_id -> TreeNode
        self._option_nodes: dict[tuple[str, str], TreeNode] = {}  # (c_id, o_id) -> TreeNode
        self._option_errors: dict[tuple[str, str], int] = {}  # (c_id, o_id) -> error count
        self._option_sizes: dict[tuple[str, str], int] = {}  # (c_id, o_id) -> bytes
        self._all_cleaner_data: list[tuple] = []  # stored for filter restore
        self.show_root = True

    def populate_tree(self, cleaner_data: list[tuple]):
        """Populate the tree from cleaner data.

        *cleaner_data* is a list of (cleaner_id, cleaner_name,
        [(option_id, option_name, description)]).

        Toggle states are loaded from persisted config via
        Options.options.get_tree().
        """
        self._all_cleaner_data = cleaner_data
        self._build_tree(cleaner_data)

    def _build_tree(self, cleaner_data: list[tuple], is_filtered: bool = False):
        """Internal: build tree nodes from cleaner data, preserving toggle state."""
        # Preserve existing toggle/error/size state before clearing node maps
        old_enabled = self._enabled.copy()
        old_errors = self._option_errors.copy()
        old_sizes = self._option_sizes.copy()

        self.root.remove_children()
        self._enabled.clear()
        self._cleaner_nodes.clear()
        self._option_nodes.clear()
        self._option_errors.clear()
        self._option_sizes.clear()

        self.root.label = Text.from_markup(
            f"[bold]{_('Total:')}[/bold] 0 files, 0 KB"
        )

        for c_id, c_name, opts in cleaner_data:
            if not opts:
                continue

            cleaner_node = self.root.add(
                "", expand=is_filtered,
                data={"cleaner": c_id, "cleaner_name": c_name}
            )
            self._cleaner_nodes[c_id] = cleaner_node

            # Load cleaner toggle: prefer old in-memory state, fall back to config
            old_c_enabled = old_enabled.get((c_id, None))
            if old_c_enabled is not None:
                c_enabled = old_c_enabled
            else:
                c_enabled = options.get_tree(c_id, None)
            self._enabled[(c_id, None)] = c_enabled
            self._update_cleaner_label(cleaner_node, c_id, c_name)

            any_child_enabled = False
            for o_id, o_name, _desc in opts:
                option_node = cleaner_node.add(
                    "", data={"cleaner": c_id, "option": o_id,
                              "option_name": o_name}
                )
                self._option_nodes[(c_id, o_id)] = option_node
                # Restore old sizes/errors if available
                self._option_sizes[(c_id, o_id)] = old_sizes.get((c_id, o_id), 0)
                self._option_errors[(c_id, o_id)] = old_errors.get((c_id, o_id), 0)

                # Load option toggle: prefer old in-memory state, fall back to config
                old_o_enabled = old_enabled.get((c_id, o_id))
                if old_o_enabled is not None:
                    o_enabled = old_o_enabled
                elif c_enabled:
                    o_enabled = options.get_tree(c_id, o_id)
                else:
                    o_enabled = False
                self._enabled[(c_id, o_id)] = o_enabled
                if o_enabled:
                    any_child_enabled = True
                self._update_option_label(option_node, c_id, o_id, o_name)

            # If all children are disabled, mark the cleaner disabled too
            if not any_child_enabled:
                self._enabled[(c_id, None)] = False
                self._update_cleaner_label(cleaner_node, c_id, c_name)

        self.root.expand()

    def filter_tree(self, query: str):
        """Filter tree to show only cleaners/options matching *query* (case-insensitive)."""
        if not query.strip():
            self.clear_filter()
            return

        q = query.lower()
        filtered = []
        for c_id, c_name, opts in self._all_cleaner_data:
            c_match = q in c_name.lower()
            matching_opts = [
                (o_id, o_name, desc)
                for o_id, o_name, desc in opts
                if q in o_name.lower() or q in o_id.lower()
            ]
            if c_match:
                # Cleaner name matches: show all options
                filtered.append((c_id, c_name, opts))
            elif matching_opts:
                # Only some options match: show cleaner with matching options
                filtered.append((c_id, c_name, matching_opts))

        self._build_tree(filtered, is_filtered=True)

    def clear_filter(self):
        """Restore the full unfiltered tree."""
        self._build_tree(self._all_cleaner_data)

    def _update_cleaner_label(self, node: TreeNode, c_id: str, c_name: str):
        """Update a cleaner node's label with name and toggle state."""
        enabled = self._enabled.get((c_id, None), False)
        toggle = "[green][X][/green]" if enabled else "[red][ ][/red]"
        node.label = Text.from_markup(
            f"{toggle} [bold]{c_name}[/bold]"
        )

    def _update_option_label(
        self, node: TreeNode, c_id: str, o_id: str, o_name: str
    ):
        """Update an option node's label with name, toggle state, and errors."""
        enabled = self._enabled.get((c_id, o_id), False)
        toggle = "[green][X][/green]" if enabled else "[red][ ][/red]"
        errors = self._option_errors.get((c_id, o_id), 0)
        error_badge = f" [yellow]:warning: {errors}[/yellow]" if errors else ""
        size = self._option_sizes.get((c_id, o_id), 0)
        size_str = f" — {bytes_to_human(size)}" if size else ""
        node.label = Text.from_markup(
            f"{toggle}   {o_name}{size_str}{error_badge}"
        )

    # --- Expand / collapse (right / left arrows) ---

    def action_expand_node(self):
        """Expand the currently focused node (Right arrow).

        Cleaner nodes (Level 1) expand to reveal option children.
        Already-expanded nodes move cursor to the first child.
        Root node is also handled so users never get trapped.
        """
        node = self.cursor_node
        if node is None:
            return
        c_id, o_id = self._resolve_node(node)
        if c_id is not None and o_id is None:
            # Cleaner node: expand or move into first child
            if not node.is_expanded:
                node.expand()
            else:
                self.action_cursor_down()
        elif c_id is not None and o_id is not None:
            # Option node: nothing to expand (leaf)
            pass
        else:
            # Root node: expand or move into first cleaner
            if not node.is_expanded:
                node.expand()
            else:
                self.action_cursor_down()

    def action_collapse_node(self):
        """Collapse the currently focused node or move to parent (Left arrow).

        The root node is never collapsed so the tree remains navigable.
        Any expanded node collapses, otherwise the cursor moves to its parent.
        """
        node = self.cursor_node
        if node is None:
            return
        if node.parent is None:
            # Root node: already at the top; do nothing
            return
        if node.is_expanded:
            node.collapse()
        else:
            self.select_node(node.parent)

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        """Prevent root node from being collapsed."""
        if event.node is self.root:
            event.node.expand()

    def action_jump_to_top(self):
        """Jump to the first node in the tree (g or HOME)."""
        first = next(iter(self.root.children), None)
        if first is not None:
            self.select_node(first)

    def action_jump_to_bottom(self):
        """Jump to the last leaf node in the tree (G or END)."""
        last = self._last_leaf(self.root)
        if last is not None and last is not self.root:
            self.select_node(last)

    @staticmethod
    def _last_leaf(node: TreeNode) -> TreeNode | None:
        """Find the last leaf descendant of *node*."""
        if not node.children:
            return node
        # Recurse into the last child
        children = list(node.children)
        return CleanerTree._last_leaf(children[-1])

    def select_node(self, node: TreeNode) -> None:
        """Select *node*, expanding all ancestors so it becomes visible."""
        # Expand ancestors first
        ancestor = node.parent
        while ancestor is not None:
            if not ancestor.is_expanded:
                ancestor.expand()
            ancestor = ancestor.parent
        super().select_node(node)

    # --- Real-time updates from worker ---

    def update_root_total(self, total_bytes: int):
        """Update root node with running total from worker."""
        total_word = _("Total:")
        self.root.label = Text.from_markup(
            f"[bold]{total_word}[/bold] {bytes_to_human(total_bytes)}"
        )

    def update_root_total_full(self, total_files: int, total_bytes: int):
        """Update root node with final file count and byte total."""
        total_word = _("Total:")
        files_word = ngettext("%d file", "%d files", total_files) % total_files
        self.root.label = Text.from_markup(
            f"[bold]{total_word}[/bold] {files_word}, {bytes_to_human(total_bytes)}"
        )

    def update_option_size(self, operation: str, option_id: str, size: int):
        """Update the size display for a specific option node."""
        key = (operation, option_id)
        self._option_sizes[key] = size
        node = self._option_nodes.get(key)
        if node:
            o_name = node.data.get("option_name", option_id)
            self._update_option_label(node, operation, option_id, o_name)

    def set_errors_for_active_operations(self, total_errors: int):
        """Mark error count on root after worker finishes with errors."""
        if total_errors > 0:
            current = self.root.label.plain
            self.root.label = Text.from_markup(
                f"[bold]{current}[/bold] [yellow]:warning: {total_errors}[/yellow]"
            )

    # --- Node resolution ---

    def _resolve_node(self, node: TreeNode) -> tuple:
        """Resolve a tree node to (cleaner_id, option_id) using node.data."""
        if node is self.root or node.data is None:
            return (None, None)
        cleaner = node.data.get("cleaner")
        option = node.data.get("option")
        return (cleaner, option)

    # --- Toggle enable/disable ---

    def action_toggle_enabled(self):
        """Toggle enable/disable on the currently focused node (Space key).

        Persists the change to Options.options.set_tree().
        """
        node = self.cursor_node
        if node is None:
            return

        c_id, o_id = self._resolve_node(node)
        if c_id is None:
            return  # root node

        key = (c_id, o_id)
        current = self._enabled.get(key, False)
        new_state = not current
        self._enabled[key] = new_state

        if o_id is None:
            # Toggling a cleaner: cascade to all its options and persist
            options.set_tree(c_id, None, new_state)
            for child_node in node.children:
                child_opt = child_node.data.get("option") if child_node.data else None
                if child_opt:
                    self._enabled[(c_id, child_opt)] = new_state
                    options.set_tree(c_id, child_opt, new_state)
                    self._refresh_option_node(child_node, c_id, child_opt)
            self._refresh_cleaner_node(node, c_id)
        else:
            # Toggling an option: persist and sync parent
            options.set_tree(c_id, o_id, new_state)
            self._refresh_option_node(node, c_id, o_id)
            parent = node.parent
            if parent and parent is not self.root:
                self._sync_cleaner_from_children(parent, c_id)

    def _refresh_cleaner_node(self, node: TreeNode, c_id: str):
        """Refresh the label of a cleaner node."""
        c_name = node.data.get("cleaner_name", c_id)
        self._update_cleaner_label(node, c_id, c_name)

    def _refresh_option_node(self, node: TreeNode, c_id: str, o_id: str):
        """Refresh the label of an option node."""
        o_name = node.data.get("option_name", o_id)
        self._update_option_label(node, c_id, o_id, o_name)

    def _sync_cleaner_from_children(self, cleaner_node: TreeNode, c_id: str):
        """Set cleaner toggle state based on its children's states. Persist it."""
        any_enabled = False
        for child_node in cleaner_node.children:
            opt = child_node.data.get("option") if child_node.data else None
            if opt and self._enabled.get((c_id, opt), False):
                any_enabled = True
        self._enabled[(c_id, None)] = any_enabled
        options.set_tree(c_id, None, any_enabled)
        self._refresh_cleaner_node(cleaner_node, c_id)

    # --- Show file list ---

    def action_show_file_list(self):
        """Show file list for the currently focused option node (Enter key)."""
        node = self.cursor_node
        if node is None or node is self.root:
            return

        c_id, o_id = self._resolve_node(node)
        if c_id is None or o_id is None:
            return

        self.post_message(self.OptionSelected(c_id, o_id))

    # --- Query helpers (used by app for confirmation / operations) ---

    def get_focused_option(self) -> tuple[str, str] | None:
        """Return (cleaner_id, option_id) for the focused option node, or None."""
        node = self.cursor_node
        if node is None:
            return None
        c_id, o_id = self._resolve_node(node)
        if c_id is None or o_id is None:
            return None
        return (c_id, o_id)

    def get_enabled_options(self) -> list[tuple[str, str]]:
        """Return list of (cleaner_id, option_id) for enabled option nodes."""
        result = []
        for (c_id, o_id), enabled in self._enabled.items():
            if o_id is not None and enabled:
                result.append((c_id, o_id))
        return result

    def get_enabled_cleaner_count(self) -> int:
        """Count how many cleaners have at least one enabled option."""
        cleaners = set()
        for (c_id, o_id), enabled in self._enabled.items():
            if o_id is not None and enabled:
                cleaners.add(c_id)
        return len(cleaners)

    def get_enabled_option_count(self) -> int:
        """Count enabled option nodes."""
        return len(self.get_enabled_options())
