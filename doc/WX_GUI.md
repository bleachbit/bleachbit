# Experimental wxPython GUI (MVP)

This is a minimal, experimental wxPython front-end for BleachBit that
coexists with the existing GTK 3 GUI (`bleachbit/GuiApplication.py`)
and the CLI (`bleachbit/CLI.py`).  It is *not* a replacement; both
front-ends share the same backend, configuration, and on-disk state.

## Goals being prototyped

- Better support for Microsoft Windows
- First-class macOS support
- Accessibility for blind users on Windows (GTK 3 has long-standing gaps)
- Path off GTK 3 without yet jumping to GTK 4
- Smaller installers on Windows
- Multi-threaded worker (later: multi-process, and elevated headless
  worker so the GUI does not need to run elevated)

## Running

```
python3 bleachbit-wx.py
```

Requires `wxPython >= 4.2` in addition to the usual BleachBit
dependencies.  On Debian/Ubuntu:

```
sudo apt install python3-wxgtk4.0
```

Or via pip:

```
pip install wxPython
```

## File layout

```
bleachbit-wx.py                 # launcher (top level)
bleachbit/GUIwx/
    __init__.py
    App.py                      # wx.App entry point
    MainFrame.py                # main window, tree, results table, log
    LoaderThread.py             # threads bleachbit.Cleaner.register_cleaners
    PreferencesDialog.py        # minimal preferences dialog
    WorkerThread.py             # threads bleachbit.Worker.Worker
```

The existing GTK modules (`GuiApplication.py`, `GuiWindow.py`, etc.)
are untouched.

## Architecture

- `bleachbit.Cleaner`, `bleachbit.CleanerML`, `bleachbit.Options` and
  `bleachbit.Worker` are reused unchanged apart from one optional hook
  (see below).
- `bleachbit.Worker.Worker` expects a UI object with
  `append_text`, `update_progress_bar`, `update_total_size`,
  `update_item_size`, and `worker_done` methods.  It also calls an
  optional `append_row(operation_option, label, size, path)` when that
  attribute is present, so a UI can build a structured results view
  without parsing the plain-text log.  The GTK front-end does not
  implement `append_row` and is therefore unaffected.
- `WorkerThread.WxUIProxy` implements that interface and forwards every
  call to `MainFrame` via `wx.CallAfter`, so the `Worker` generator can
  be drained on a background thread while all widget updates happen on
  the wx main thread.
- `LoaderThread` drains `Cleaner.register_cleaners()` on a background
  thread so the UI remains responsive while CleanerML and Winapp2.ini
  cleaners are loaded.  Progress messages are forwarded to the status
  bar via `wx.CallAfter`.
- `MainFrame._start_worker()` creates a `WorkerThread`, which is the
  only thing the front-end needs to swap out later to move the worker
  into a subprocess (elevated or not).

## Right pane layout

The right pane is a `wx.Notebook` with two tabs:

- **Results** — a `wx.ListCtrl` in report mode with columns
  *Cleaner*, *Option*, *Path*, *Size*, *Action*.  Click a column
  header to sort (size sort is numeric; all others are case-insensitive
  text).  Right-click one or more rows for a context menu:
  - *Copy path* — join selected paths with newlines on the clipboard.
  - *Open file location* — open the containing folder in the
    platform file manager (Explorer selects the file on Windows,
    Finder reveals it on macOS, `xdg-open` on Linux).
  - *Always skip this path (add to keep list)* — append the selected
    paths to `Options.whitelist_paths` (`folder` entry if the path is
    a directory, otherwise `file`).
  - *Uncheck option: \<Cleaner\> — \<Option\>* — one entry per
    distinct `(cleaner_id, option_id)` across the selection; toggles
    the matching tree checkbox off and persists via `set_tree`.
- **Log** — plain-text log.

A filter bar above the notebook applies to both tabs:

- Text box — case-insensitive substring match against the Cleaner,
  Option, Path and Action columns in Results, and against each log
  line in Log.
- *Errors only* checkbox — hide result rows (which have no error
  concept) and hide any log line whose tag is not `'error'`.  When
  toggled on, the Log tab is automatically selected so the user sees
  the filtered messages immediately.

## Persistence and preferences

- Checkbox state in the cleaner tree is persisted to
  `Options.set_tree(cleaner_id, option_id, value)` on every change and
  restored from `Options.get_tree()` when the tree is populated.  This
  is the same `[tree]` section used by the GTK UI, so selections
  carry across both front-ends.
- `File → Preferences…` opens a minimal `PreferencesDialog` with
  checkboxes for the options most users actually change in the GTK UI:
  `delete_confirmation`, `shred`, `check_online_updates`, `debug`.

## Shredding arbitrary files or folders

`File → Shred files…` opens a multi-select `wx.FileDialog`.
`File → Shred folders…` opens `wx.DirDialog` repeatedly until the user
cancels, allowing multiple folders to be picked.  Both feed into the
same path used by the GTK UI and CLI:

```python
Cleaner.backends['_gui'] = Cleaner.create_simple_cleaner(paths)
self._start_worker(really_delete=True, operations={'_gui': ['files']})
```

When `delete_confirmation` is enabled (the default), a confirmation
dialog is shown before shredding.

## Aborting a long-running operation

The **Abort** toolbar button sets `Worker.is_aborted = True`.  The
worker generator checks that flag at every yield point, including the
2-second yield inside `Wipe.wipe_path` used for `system.empty_space`,
so pressing Abort during a free-space wipe causes the wipe to stop
and clean up its temporary files at the next checkpoint (up to a
couple of seconds later).  The temporary files have an `atexit` hook
as a safety net even if the process is killed outright.

## Known MVP limitations

- No expert mode / warning confirmation flow yet (warnings are just
  marked with `⚠` in the tree).
- Preferences dialog is intentionally minimal: no whitelist editor,
  languages tab, drives selector, or per-cleaner options yet.
- Chaff generator is not wired up.
- Not translated through the wx machinery yet (strings go through
  `bleachbit.Language.get_text`, but accelerators are missing).

## Accessibility

The wx front-end aims to be usable by blind users via screen readers
(NVDA / Narrator on Windows, Orca on Linux):

- Every interactive control has either a visible label or an
  accessible name set via `SetName`, including the gauge, status
  text, results list, log, tree, and the two search/filter boxes.
- Buttons (Preview, Clean, Abort) have tooltips that name their
  keyboard shortcut.
- Global keyboard shortcuts (see `MainFrame._build_accelerators`):
  - **F5** — Preview
  - **Ctrl+Enter** — Clean
  - **Esc** — Abort
  - **Ctrl+F** — focus the results/log filter
  - **Ctrl+L** — focus the tree search
- Menu shortcuts: **Ctrl+Q** Exit, **Ctrl+,** Preferences,
  **Ctrl+Shift+F** Shred files, **Ctrl+Shift+D** Shred folders,
  **F1** About.

Known limitation: the cleaner/option tree uses
`wx.lib.agw.customtreectrl.CustomTreeCtrl`, which is an owner-drawn
generic control and does **not** expose itself to MSAA/UIA on
Windows.  Replacing it with `wx.dataview.DataViewTreeCtrl` (or the
native `wx.TreeCtrl` with state images) is tracked as a follow-up
for full screen-reader support of individual rows.

## Smoke test

```
python3 - <<'PY'
import sys, wx
sys.path.insert(0, '.')
from bleachbit.GUIwx.App import BleachBitWxApp
app = BleachBitWxApp(False)
wx.CallLater(2000, wx.GetApp().ExitMainLoop)
app.MainLoop()
PY
```
