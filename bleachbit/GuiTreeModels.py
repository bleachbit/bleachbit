# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

from bleachbit import GuiBasic
from bleachbit.Cleaner import backends
from bleachbit.GUI import logger
from bleachbit.GtkShim import GObject, Gtk
from bleachbit.Language import get_text as _
from bleachbit.Options import options


class TreeDisplayModel:
    """Displays the info model in a view"""

    def make_view(self, model, parent, context_menu_event):
        """Create and return a TreeView object"""
        self.view = Gtk.TreeView.new_with_model(model)

        # hide headers
        self.view.set_headers_visible(False)

        # listen for right click (context menu)
        self.view.connect("button_press_event", context_menu_event)

        # first column: cleaner name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn(_("Name"), renderer_name, text=0)
        self.view.append_column(column_name)
        self.view.set_search_column(0)

        # second column: alert icon
        renderer_alert = Gtk.CellRendererPixbuf()
        column_alert = Gtk.TreeViewColumn("", renderer_alert)
        column_alert.add_attribute(renderer_alert, "icon-name", 4)
        self.view.append_column(column_alert)

        # third column: checkbox
        renderer_active = Gtk.CellRendererToggle()
        renderer_active.set_property('activatable', True)
        renderer_active.connect('toggled', self.col1_toggled_cb, model, parent)
        column_active = Gtk.TreeViewColumn(_("Active"), renderer_active)
        column_active.add_attribute(renderer_active, "active", 1)
        self.view.append_column(column_active)

        # fourth column: size
        renderer_size = Gtk.CellRendererText()
        renderer_size.set_alignment(1.0, 0.0)
        # TRANSLATORS: Size is the label for the column that shows how
        # much space an option would clean or did clean
        column_size = Gtk.TreeViewColumn(_("Size"), renderer_size, text=3)
        column_size.set_alignment(1.0)
        self.view.append_column(column_size)

        # finish
        self.view.expand_all()
        return self.view

    def set_cleaner(self, path, model, parent_window, value):
        """Activate or deactivate option of cleaner."""
        assert isinstance(value, bool)
        assert isinstance(model, Gtk.TreeStore)
        cleaner_id = None
        i = path
        if isinstance(i, str):
            # type is either str or gtk.TreeIter
            i = model.get_iter(path)
        parent = model.iter_parent(i)
        if parent:
            # this is an option (child), not a cleaner (parent)
            cleaner_id = model[parent][2]
            option_id = model[path][2]
        if cleaner_id and value:
            # When enabling an option, present any warnings.
            # (When disabling an option, there is no need to present warnings.)
            warning = backends[cleaner_id].get_warning(option_id)
            if warning and not options.get('expert_mode'):
                if hasattr(parent_window, 'show_infobar'):
                    parent_window.show_infobar(
                        _("This option is protected. To bypass protection, enable expert mode."))
                # Show an alert icon by the option name.
                model[path][4] = "dialog-warning"
                return
            warning_key = 'cleaner:' + cleaner_id + ':' + option_id
            if warning and not options.get_warning_preference(warning_key):
                # TRANSLATORS: %(cleaner) may be Firefox, System, etc.
                # %(option) may be cache, logs, cookies, etc.
                option_name = _("%(cleaner)s - %(option)s") % {
                    'cleaner': model[parent][0],
                    'option': model[path][0],
                }
                confirmed, remember_choice = GuiBasic.warning_confirm_dialog(
                    parent_window, option_name, warning)
                if not confirmed:
                    # user cancelled, so don't toggle option
                    return
                if remember_choice:
                    options.remember_warning_preference(warning_key)
        model[path][1] = value
        model[path][4] = ""

    def col1_toggled_cb(self, cell, path, model, parent_window):
        """Callback for toggling cleaners"""
        is_toggled_on = not model[path][1]  # Is the new state enabled?
        self.set_cleaner(path, model, parent_window, is_toggled_on)
        i = model.get_iter(path)
        parent = model.iter_parent(i)
        if parent and is_toggled_on:
            # If child is enabled, then also enable the parent.
            model[parent][1] = True
        # If all siblings were toggled off, then also disable the parent.
        if parent and not is_toggled_on:
            sibling = model.iter_nth_child(parent, 0)
            any_sibling_enabled = False
            while sibling:
                if model[sibling][1]:
                    any_sibling_enabled = True
                sibling = model.iter_next(sibling)
            if not any_sibling_enabled:
                model[parent][1] = False
        # If toggled and has children, then do the same for each child.
        child = model.iter_children(i)
        while child:
            self.set_cleaner(child, model, parent_window, is_toggled_on)
            child = model.iter_next(child)
        return


class TreeInfoModel:
    """Model holds information to be displayed in the tree view"""

    def __init__(self):
        self.tree_store = Gtk.TreeStore(
            GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_PYOBJECT, GObject.TYPE_STRING, GObject.TYPE_STRING)
        if not self.tree_store:
            raise Exception("cannot create tree store")
        self.row_changed_handler_id = None
        self.refresh_rows()
        self.tree_store.set_sort_func(3, self.sort_func)
        self.tree_store.set_sort_column_id(3, Gtk.SortType.ASCENDING)

    def get_model(self):
        """Return the tree store"""
        return self.tree_store

    def on_row_changed(self, __treemodel, path, __iter):
        """Event handler for when a row changes"""
        parent = self.tree_store[path[0]][2]
        child = None
        if len(path) == 2:
            child = self.tree_store[path][2]
        value = self.tree_store[path][1]
        options.set_tree(parent, child, value)

    def refresh_rows(self):
        """Clear rows (cleaners) and add them fresh"""
        if self.row_changed_handler_id:
            self.tree_store.disconnect(self.row_changed_handler_id)
        self.tree_store.clear()
        hidden_cleaners = []
        for key in sorted(backends):
            if not any(backends[key].get_options()):
                # localizations has no options, so it should be hidden
                # https://github.com/az0/bleachbit/issues/110
                continue
            c_name = backends[key].get_name()
            c_id = backends[key].get_id()
            c_value = options.get_tree(c_id, None)
            if not c_value and options.get('auto_hide') and backends[key].auto_hide():
                hidden_cleaners.append(c_id)
                continue
            parent = self.tree_store.append(
                None, (c_name, c_value, c_id, "", ""))
            for (o_id, o_name) in backends[key].get_options():
                o_value = options.get_tree(c_id, o_id)
                self.tree_store.append(parent, (o_name, o_value, o_id, "", ""))
        if hidden_cleaners:
            logger.debug("automatically hid %d cleaners: %s", len(
                hidden_cleaners), ', '.join(hidden_cleaners))
        self.row_changed_handler_id = self.tree_store.connect("row-changed",
                                                              self.on_row_changed)

    def sort_func(self, model, iter1, iter2, _user_data):
        """Sort the tree by the id

        Index 0 is the display name
        Index 2 is the ID (e.g., cookies, vacuum).

        Sorting by ID is functionally important, so that vacuuming is done
        last, even for other languages. See https://github.com/bleachbit/bleachbit/issues/441
        """
        value1 = model[iter1][2].lower()
        value2 = model[iter2][2].lower()
        if value1 == value2:
            return 0
        if value1 > value2:
            return 1
        return -1
