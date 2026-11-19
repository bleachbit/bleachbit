# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Screen reader helpers for the experimental wxPython GUI.

On Windows, screen readers such as NVDA read native controls through
MSAA.  ``wx.Window.SetName`` does not change the MSAA name of a native
control, and a tooltip is not its MSAA description, so this module
attaches a small :class:`wx.Accessible` to a control when it needs an
accessible name or description.  Everything the ``wx.Accessible`` does
not answer (children, actions, ...) falls back to the standard system
implementation, so a list view still reports its rows.

A checkbox is the exception: in dark mode wx draws checkboxes itself
(``BS_OWNERDRAW``), and the standard implementation then reports a
push button with no checked state.  wx normally fixes this with its
own accessible object, which ``SetAccessible`` replaces, so the
``wx.Accessible`` here reports the checkbox role and state itself.

:class:`NoticeBar` is a :class:`wx.InfoBar` that screen readers
announce when it shows a message, like the GTK info bar.
"""

import time

import wx

# ``wx.Accessible`` is only implemented on Windows (MSAA).
_HAVE_MSAA = wx.Platform == '__WXMSW__' and hasattr(wx, 'Accessible')

# Milliseconds before a notice hides itself, as in the GTK GUI.
NOTICE_TIMEOUT_MS = 15000

# A notice repeated within this many seconds is not announced again.
_REPEAT_SECONDS = 1.0


def _resolve(value):
    return value() if callable(value) else value


if _HAVE_MSAA:
    class _LabelledAccessible(wx.Accessible):
        """Give a window an accessible name, description and role.

        ``name`` and ``description`` may be strings or callables that
        return the current text.  Anything left as ``None`` falls back
        to the system's standard accessible object, except that a
        ``wx.CheckBox`` always reports the checkbox role and state.
        """

        def __init__(self, window):
            super().__init__(window)
            self.name = None
            self.description = None
            self.role = None

        def GetName(self, childId):  # noqa: N802 - wx API
            if childId == wx.ACC_SELF and self.name is not None:
                return (wx.ACC_OK, _resolve(self.name))
            return super().GetName(childId)

        def GetDescription(self, childId):  # noqa: N802 - wx API
            if childId == wx.ACC_SELF and self.description is not None:
                return (wx.ACC_OK, _resolve(self.description))
            return super().GetDescription(childId)

        def GetRole(self, childId):  # noqa: N802 - wx API
            if childId == wx.ACC_SELF:
                if self.role is not None:
                    return (wx.ACC_OK, self.role)
                if isinstance(self.GetWindow(), wx.CheckBox):
                    return (wx.ACC_OK, wx.ROLE_SYSTEM_CHECKBUTTON)
            return super().GetRole(childId)

        def GetState(self, childId):  # noqa: N802 - wx API
            window = self.GetWindow()
            if childId == wx.ACC_SELF and isinstance(window, wx.CheckBox):
                return (wx.ACC_OK, _checkbox_state(window))
            return super().GetState(childId)

    def _checkbox_state(checkbox):
        """Return the MSAA state of a checkbox, as a native one reports it."""
        state = wx.ACC_STATE_SYSTEM_FOCUSABLE
        if not checkbox.IsEnabled():
            state |= wx.ACC_STATE_SYSTEM_UNAVAILABLE
        if not checkbox.IsShownOnScreen():
            state |= wx.ACC_STATE_SYSTEM_INVISIBLE
        if wx.Window.FindFocus() is checkbox:
            state |= wx.ACC_STATE_SYSTEM_FOCUSED
        value = checkbox.Get3StateValue()
        if value == wx.CHK_CHECKED:
            state |= wx.ACC_STATE_SYSTEM_CHECKED
        elif value == wx.CHK_UNDETERMINED:
            state |= wx.ACC_STATE_SYSTEM_MIXED
        return state


def _accessible(window):
    """Return the window's ``_LabelledAccessible``, creating it."""
    acc = getattr(window, '_bb_accessible', None)
    if acc is None:
        acc = _LabelledAccessible(window)
        window.SetAccessible(acc)
        # SetAccessible takes ownership; keep the Python wrapper alive.
        window._bb_accessible = acc
    return acc


def set_accessible_name(window, name):
    """Name a control that has no visible label next to it.

    ``name`` may be a string or a callable returning the current name.
    """
    if not callable(name):
        window.SetName(name)
    if _HAVE_MSAA:
        _accessible(window).name = name


def set_accessible_description(window, description):
    """Give a control a description that screen readers read on focus.

    ``description`` may be a string or a callable returning the
    current description.
    """
    if _HAVE_MSAA:
        _accessible(window).description = description


def set_tooltip(window, text):
    """Set a tooltip and make screen readers read it on focus too.

    A tooltip appears only on mouse hover, so keyboard and screen
    reader users would otherwise never hear it.
    """
    window.SetToolTip(text)
    set_accessible_description(window, text)


class NoticeBar(wx.InfoBar):
    """Non-blocking notice, like the GTK info bar.

    The message hides itself after ``NOTICE_TIMEOUT_MS``.  On Windows
    the message text is exposed as an MSAA *alert*, and an alert event
    is raised whenever a message is shown, so NVDA (and other screen
    readers) speak the message without moving the focus.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._message = ''
        self._shown_at = 0.0
        self._timer = None
        self._alert_window = None
        if _HAVE_MSAA:
            # Expose the message on the text child: it has no focusable
            # descendants, so a screen reader speaks only the message,
            # not the close button too.
            self._alert_window = next(
                (child for child in self.GetChildren()
                 if isinstance(child, wx.StaticText)), self)
            acc = _accessible(self._alert_window)
            acc.role = wx.ROLE_SYSTEM_ALERT
            acc.name = lambda: self._message
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

    def show_notice(self, message, flags=wx.ICON_INFORMATION):
        """Show ``message`` and announce it to screen readers."""
        # One user action can raise the same notice several times (e.g.
        # checking a cleaner with several protected options); speak it
        # once.
        now = time.monotonic()
        repeated = (message == self._message and self.IsShown()
                    and now - self._shown_at < _REPEAT_SECONDS)
        self._message = message
        self._shown_at = now
        self.ShowMessage(message, flags)
        if self._timer is None:
            self._timer = wx.CallLater(NOTICE_TIMEOUT_MS, self._dismiss)
        else:
            self._timer.Restart(NOTICE_TIMEOUT_MS)
        if self._alert_window is not None and not repeated:
            wx.Accessible.NotifyEvent(
                wx.ACC_EVENT_SYSTEM_ALERT, self._alert_window,
                wx.OBJID_CLIENT, wx.ACC_SELF)

    def get_message(self):
        """Return the last message shown."""
        return self._message

    def _dismiss(self):
        self._timer = None
        if self:
            self.Dismiss()

    def _on_destroy(self, evt):
        if evt.GetEventObject() is self and self._timer is not None:
            self._timer.Stop()
            self._timer = None
        evt.Skip()
