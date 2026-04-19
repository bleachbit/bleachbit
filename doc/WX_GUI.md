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
- **Log** — the original plain-text log.

## Known MVP limitations

- No expert mode / warning confirmation flow yet (warnings are just
  marked with `⚠` in the tree).
- Preferences, whitelist editor, chaff, shred-files, and empty-space
  wiping are not wired up.
- No menu / keyboard shortcut coverage beyond Exit and About.
- Not translated through the wx machinery yet (strings go through
  `bleachbit.Language.get_text`, but accelerators are missing).

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
