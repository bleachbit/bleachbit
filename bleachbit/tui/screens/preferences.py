# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Preferences modal — edit all bleachbit.ini settings."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Switch, Label, Button
from textual.binding import Binding

from bleachbit.Options import options, OPTION_DEFAULTS
from bleachbit.Language import get_text as _


# Preferences exposed to the user (key → display label)
VISIBLE_PREFS = [
    ("auto_hide", _("Auto-hide unusable cleaners")),
    ("check_online_updates", _("Check for online updates")),
    ("dark_mode", _("Dark mode")),
    ("debug", _("Debug mode")),
    ("delete_confirmation", _("Delete confirmation dialog")),
    ("shred", _("Shred (overwrite) files")),
    ("units_iec", _("Use IEC units (MiB vs MB)")),
]


class PreferencesScreen(ModalScreen):
    """Modal screen for editing BleachBit preferences."""

    BINDINGS = [
        Binding("escape", "dismiss", _("Close")),
        Binding("q", "dismiss", _("Close")),
    ]

    CSS = """
    PreferencesScreen {
        align: center middle;
    }

    #prefs-dialog {
        width: 54;
        height: auto;
        max-height: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #prefs-title {
        text-align: center;
        padding: 0 0 1 0;
        text-style: bold;
    }

    .pref-row {
        height: 3;
        padding: 0 1;
    }

    .pref-row Label {
        width: 36;
        padding: 0 1;
        content-align: left middle;
    }

    .pref-row Switch {
        margin: 1 0;
    }

    #prefs-footer {
        height: 1;
        padding: 1 0 0 0;
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="prefs-dialog"):
            yield Static(_("Preferences"), id="prefs-title")
            with VerticalScroll():
                for key, label in VISIBLE_PREFS:
                    current = bool(options.get(key))
                    with Horizontal(classes="pref-row"):
                        yield Label(label)
                        yield Switch(value=current, id=f"pref-{key}", animate=False)
            yield Static(f"[dim]{_('Changes are saved immediately')}[/dim]", id="prefs-footer")

    def on_switch_changed(self, event: Switch.Changed):
        """Save preference immediately when toggled."""
        switch_id = event.switch.id or ""
        if switch_id.startswith("pref-"):
            key = switch_id[5:]  # remove "pref-" prefix
            options.set(key, event.value)

    async def action_dismiss(self, result=None):
        self.dismiss(result)