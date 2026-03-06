# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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


# standard library
import json
import logging
import os
import threading
import time

# third party
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

# local import
import bleachbit
from bleachbit.Cookie import list_unique_cookies, COOKIE_KEEP_LIST_FILENAME
from bleachbit.Language import get_text as _, nget_text as _n

logger = logging.getLogger(__name__)


COOKIE_DISCOVERY_WARN_THRESHOLD = 2.0  # seconds


class CookieManagerPane(Gtk.Box):
    """Widget for managing cookies to keep when cleaning."""

    def __init__(self, bottom_widget=None):
        Gtk.Box.__init__(
            self, orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Instructions label
        instructions = Gtk.Label()
        instructions.set_markup(
            # TRANSLATORS: Instruction label in the manage cookies dialog.
            "<b>" + _("Select the cookies to keep when cleaning cookies across browsers.") + "</b>")
        instructions.set_line_wrap(True)
        instructions.set_xalign(0)
        self.pack_start(instructions, False, False, 0)

        # Search box
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pack_start(search_box, False, False, 0)

        # TRANSLATORS: Label for the search entry in the manage cookies dialog.
        search_label = Gtk.Label(label=_("Search:"))
        search_box.pack_start(search_label, False, False, 0)

        self.search_entry = Gtk.Entry()
        # TRANSLATORS: Placeholder text in the search entry in the manage cookies dialog.
        # 'Filter' is a verb meaning to narrow down the list by typing.
        self.search_entry.set_placeholder_text(_("Filter cookies..."))
        self.search_entry.connect("changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)

        # TRANSLATORS: Toggle button label in the manage cookies dialog.
        # "Show" is a command (imperative).
        # 'Selected' refers to selected cookies (the noun "cookies" is implied).
        self.selected_toggle = Gtk.ToggleButton(label=_("Show Selected"))
        self.selected_toggle.set_tooltip_text(
            # TRANSLATORS: Tooltip for the "Show Selected" toggle button.
            _("Only show cookies that are currently selected"))
        self.selected_toggle.connect("toggled", self.on_selected_toggle)
        search_box.pack_start(self.selected_toggle, False, False, 0)

        self.show_selected_only = False

        # Create scrollable window for cookie list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.pack_start(scrolled, True, True, 0)

        self.keep_list_path = os.path.join(
            bleachbit.options_dir, COOKIE_KEEP_LIST_FILENAME)
        self.saved_domains = self._load_saved_domains()

        # Create cookie list store: checkbox, domain
        self.cookie_store = Gtk.ListStore(bool, str)

        # Create filter for the list store
        self.cookie_filter = self.cookie_store.filter_new()
        self.cookie_filter.set_visible_func(self.filter_cookies)

        # Create the TreeView
        self.treeview = Gtk.TreeView(model=self.cookie_filter)

        # Create columns
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=0)
        self.treeview.append_column(column_toggle)

        renderer_text = Gtk.CellRendererText()
        # TRANSLATORS: Column header in the manage cookies dialog.
        # 'Host' is a noun meaning the website hostname (domain name) of the cookie.
        column_domain = Gtk.TreeViewColumn(_("Host"), renderer_text, text=1)
        column_domain.set_sort_column_id(1)
        column_domain.set_resizable(True)
        column_domain.set_expand(True)
        self.treeview.append_column(column_domain)

        scrolled.add(self.treeview)

        # Button box
        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        self.pack_start(button_box, False, False, 0)

        # Stat label
        self.stat_label = Gtk.Label()
        self.update_stat_label()
        button_box.pack_start(self.stat_label, True, True, 0)

        # Select all / Deselect all buttons
        # TRANSLATORS: Button label in the manage cookies dialog.
        self.select_all_btn = Gtk.Button.new_with_label(_("Select All"))
        self.select_all_btn.connect("clicked", self.on_select_all_clicked)
        button_box.pack_start(self.select_all_btn, False, False, 0)

        # TRANSLATORS: Button label in the manage cookies dialog.
        self.deselect_all_btn = Gtk.Button.new_with_label(_("Deselect All"))
        self.deselect_all_btn.connect("clicked", self.on_deselect_all_clicked)
        button_box.pack_start(self.deselect_all_btn, False, False, 0)

        if bottom_widget is not None:
            self.pack_start(bottom_widget, False, False, 0)

        self._populate_cookie_store()

    def save_changes(self):
        """Save choices to a JSON file."""
        keep_list = sorted(self._iter_selected_domains())

        try:
            with open(self.keep_list_path, "w", encoding="utf-8") as f:
                json.dump(keep_list, f, indent=2)
            self.saved_domains = set(keep_list)
            return True
        except OSError as exc:
            logger.error("Failed to save cookie keep list %s: %s",
                         self.keep_list_path, exc)
            return False

    def update_stat_label(self):
        """Update the stat label: how many selected"""
        total = len(self.cookie_store)
        selected = sum(1 for row in self.cookie_store if row[0])
        visible = sum(1 for _row in self.cookie_filter)
        if visible < total:
            # TRANSLATORS: %(selected)d is the count of selected cookies,
            # %(total)d is the total count, %(visible)d is the visible count
            self.stat_label.set_text(
                _n("%(selected)d of %(total)d cookie kept (%(visible)d visible)",
                   "%(selected)d of %(total)d cookies kept (%(visible)d visible)",
                   selected) % {'selected': selected, 'total': total, 'visible': visible})
        else:
            # TRANSLATORS: %(selected)d is the count of selected cookies,
            # %(total)d is the total count
            self.stat_label.set_text(
                _n("%(selected)d of %(total)d cookie kept",
                   "%(selected)d of %(total)d cookies kept",
                   selected) % {'selected': selected, 'total': total})

    def on_cell_toggled(self, _widget, path):
        """Toggle the checkbox in the child model"""
        # Convert path from filter model to child model
        filter_path = Gtk.TreePath.new_from_string(path)
        child_path = self.cookie_filter.convert_path_to_child_path(filter_path)

        # Toggle the checkbox in the child model
        self.cookie_store[child_path][0] = not self.cookie_store[child_path][0]
        self.save_changes()
        self.update_stat_label()

    def on_select_all_clicked(self, _widget):
        """Select all cookies"""
        self._set_filtered_selection(True)
        self.save_changes()
        self.update_stat_label()

    def on_deselect_all_clicked(self, _widget):
        """Deselect all cookies"""
        self._set_filtered_selection(False)
        self.save_changes()
        self.update_stat_label()

    def _set_filtered_selection(self, is_selected):
        """Set selection state only for rows visible in the current filter."""
        # Collect paths first to prevent iterator invalidation when rows disappear
        # from the filter (e.g., deselecting while 'Show Selected' is active).
        paths = []
        tree_iter = self.cookie_filter.get_iter_first()
        while tree_iter:
            child_iter = self.cookie_filter.convert_iter_to_child_iter(
                tree_iter)
            if child_iter:
                paths.append(self.cookie_store.get_path(child_iter))
            tree_iter = self.cookie_filter.iter_next(tree_iter)

        for path in paths:
            self.cookie_store[path][0] = is_selected

    def filter_cookies(self, model, tree_iter, _data):
        """Filter function for the cookie list"""
        search_text = self.search_entry.get_text().lower()
        if not search_text:
            matches_search = True
        else:
            domain = model[tree_iter][1].lower()
            matches_search = search_text in domain

        if not matches_search:
            return False

        if self.show_selected_only:
            return bool(model[tree_iter][0])

        return True

    def on_selected_toggle(self, widget):
        """Toggle whether only selected cookies should be visible."""
        self.show_selected_only = widget.get_active()
        self.cookie_filter.refilter()
        self.update_stat_label()

    def on_search_changed(self, _widget):
        """Called when the search text changes"""
        self.cookie_filter.refilter()
        self.update_stat_label()

    def _populate_cookie_store(self):
        """Populate the list store with discovered and saved cookie hosts."""
        self._spinner = Gtk.Spinner()
        self._spinner.set_size_request(24, 24)
        self._spinner.start()
        # Insert spinner row placeholder so the button_box area is not empty
        # while loading; we embed the spinner above the treeview instead.
        self.treeview.set_sensitive(False)
        # Find the scrolled window's parent vbox and insert a spinner overlay
        scrolled = self.treeview.get_parent()
        vbox = scrolled.get_parent()
        spinner_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.pack_start(self._spinner, False, False, 0)
        # TRANSLATORS: Status message shown while the cookie list is loading
        # in the cookie manager dialog window.
        # "Loading" is a present participle (ongoing action).
        # To indicate an ongoing operation, include the ellipsis as literal
        # Unicode (…) or as Unicode escape (\u2026).
        self._loading_label = Gtk.Label(label=_("Loading cookies\u2026"))
        spinner_box.pack_start(self._loading_label, False, False, 0)
        vbox.pack_start(spinner_box, False, False, 0)
        vbox.reorder_child(spinner_box, vbox.get_children().index(scrolled))
        self._spinner_box = spinner_box
        self.show_all()

        def _worker():
            start = time.monotonic()
            discovered = []
            try:
                discovered = list_unique_cookies()
            except (OSError, RuntimeError, ValueError) as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to enumerate cookies: %s", exc)
            duration = time.monotonic() - start
            if duration >= COOKIE_DISCOVERY_WARN_THRESHOLD:
                logger.warning("Enumerating cookie hosts took %.2fs", duration)
            GLib.idle_add(self._finish_populate, discovered)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _finish_populate(self, discovered):
        """Called on the GTK main thread after cookie discovery finishes."""
        self._spinner.stop()
        self._spinner_box.destroy()
        self.treeview.set_sensitive(True)

        all_hosts = {h.strip() for h in discovered if h}
        all_hosts.update(self.saved_domains)
        sorted_hosts = sorted(all_hosts, key=lambda host: host.lower())

        for host in sorted_hosts:
            is_saved = host in self.saved_domains
            self.cookie_store.append([is_saved, host])

        self.update_stat_label()
        return False

    def _iter_selected_domains(self):
        """Yield domain names for all selected (checked) cookies."""
        for row in self.cookie_store:
            if row[0]:
                yield row[1]

    def _load_saved_domains(self):
        """Load saved cookie hostnames from disk."""
        try:
            with open(self.keep_list_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return set()
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read cookie keep list %s: %s",
                           self.keep_list_path, exc)
            return set()

        domains = set()
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    candidate = item
                elif isinstance(item, dict):
                    candidate = item.get("domain")
                else:
                    candidate = None
                if isinstance(candidate, str) and candidate:
                    domains.add(candidate.strip())
        return domains
