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
    MainFrame.py                # main window, tree, log, toolbar
    WorkerThread.py             # threads bleachbit.Worker.Worker
```

The existing GTK modules (`GuiApplication.py`, `GuiWindow.py`, etc.)
are untouched.

## Architecture

- `bleachbit.Cleaner`, `bleachbit.CleanerML`, `bleachbit.Options` and
  `bleachbit.Worker` are reused unchanged.
- `bleachbit.Worker.Worker` expects a UI object with
  `append_text`, `update_progress_bar`, `update_total_size`,
  `update_item_size`, and `worker_done` methods.
- `WorkerThread.WxUIProxy` implements that interface and forwards every
  call to `MainFrame` via `wx.CallAfter`, so the `Worker` generator can
  be drained on a background thread while all widget updates happen on
  the wx main thread.
- `MainFrame._start_worker()` creates a `WorkerThread`, which is the
  only thing the front-end needs to swap out later to move the worker
  into a subprocess (elevated or not).

## Known MVP limitations

- No expert mode / warning confirmation flow yet (warnings are just
  marked with `⚠` in the tree).
- Log is a plain `wx.TextCtrl`; the
  [`bleachbit_gui_next_gen`](https://github.com/) table view is a
  planned upgrade.
- Preferences, whitelist editor, chaff, shred-files, and empty-space
  wiping are not wired up.
- Cleaner registration runs synchronously at startup.  On Windows with
  Winapp2 this can take a few seconds; should move to a thread.
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
