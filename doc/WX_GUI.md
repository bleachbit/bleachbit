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
    Accessibility.py            # screen reader names, descriptions, NoticeBar
    App.py                      # wx.App entry point
    Dialogs.py                  # delete/warning confirmations (GuiBasic counterparts)
    MainFrame.py                # main window, tree, results table, log
    LoaderThread.py             # threads bleachbit.Cleaner.register_cleaners
    PreferencesDialog.py        # preferences: the seven pages of the GTK dialog
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
- `File → Preferences…` opens `PreferencesDialog`, which has the
  pages of the GTK dialog (`bleachbit/GuiPreferences.py`) in the same
  order, as `wx.Notebook` tabs.  The options are the same `Options`
  keys, so a choice made in one front-end carries over to the other.
  Strings reuse the GTK msgids (including `pgettext` contexts such as
  `_p('button', 'Add')`), so existing translations apply.
  - **General** has three groups, as in GTK:
    - *Cleaning*: `shred`, `exit_done`, `delete_confirmation` (enabled
      only in expert mode), a *Reset warning confirmations* button
      (expert mode only), `auto_hide`, `units_iec`.
    - *Interface*: `remember_geometry` and, when wxPython has
      `wx.App.SetAppearance` (wxPython 4.3 / wxWidgets 3.3), `dark_mode`.
    - *Integration and advanced*: `kde_shred_menu_option` (not on
      Windows), `debug`, `expert_mode`.
  - **Updates** (when `online_update_notification_enabled`):
    `check_online_updates`, with `check_beta` and, on Windows,
    `update_winapp2` indented below it and enabled only while it is
    checked.  The wx front-end does not check for updates itself yet;
    these settings are shared with the GTK front-end.
  - **Languages**: see *Interface language* below.
  - **Cookies**: the cookie keep list (see *Cookies to keep* below).
  - **Keep list** and **Custom** edit `Options.whitelist_paths` and
    `Options.custom_paths`.  Adding a path already in either list, or
    adding or removing a path, shows a notice.  Adding a protected path
    (`bleachbit.ProtectedPath`) to Custom needs expert mode and a
    confirmation, which can be remembered, as in GTK.
  - **Drives** edits the `shred_drives` list: one writable folder per
    drive whose empty space the *Free disk space* option wipes.
- The GTK options `win10_theme` and `use_fontconfig_backend` only
  affect GTK rendering on Windows, so the wx dialog does not show them.
- Checkboxes on the General and Updates pages are saved when the
  dialog closes with OK (`PreferencesDialog.commit`), which then
  applies the side effects GTK applies on toggle: `debug` sets the log
  level, `kde_shred_menu_option` installs the KDE service menu,
  `dark_mode` changes the appearance, and `auto_hide` reloads the
  cleaner tree.  If the KDE service menu cannot be added or removed,
  the main window shows the error and the option keeps its old value.  While the dialog is open, dependent controls follow
  the checkboxes (e.g. checking *Expert mode* enables *Confirm before
  delete*).  The other pages save changes immediately, as in GTK.
- Notices appear in a `NoticeBar` at the top of the dialog, the
  counterpart of the GTK info bar.
- `MainFrame._show_preferences(page)` opens the dialog at a page.  The
  tree's context menu adds *Manage cookies to keep…* for options
  that clean cookies and *Manage custom paths…* for
  *System → Custom*, as in GTK.
- *Hide irrelevant cleaners* (`auto_hide`) controls whether
  `LoaderThread` hides cleaners whose `auto_hide()` reports nothing to
  clean.  As in GTK, a cleaner with a checked option is never hidden;
  `_populate_tree` checks this again, in case an option was checked
  after the loader read it.
- *Exit after cleaning* (`exit_done`) closes the window when a clean
  (not a preview) finishes.
- *Remember window geometry*: the window position, size and maximized
  state are saved to `window_x`, `window_y`, `window_width`,
  `window_height` and `window_maximized` on close, and restored at
  startup when the option is on and the saved corner is on a connected
  display.  A maximized window saves the size it is restored to, not
  its maximized size.  A window that starts maximized keeps the saved
  size until it is maximized, because wxGTK reports other sizes before
  then, such as the saved size plus the window frame.  The wx window
  has no full screen mode, so `window_fullscreen` is left alone.
- *Dark mode*: `PreferencesDialog.apply_appearance` maps `dark_mode` to
  `wx.App.SetAppearance` (`Dark`; otherwise the system default).  On
  GTK and macOS it applies at once.  On Windows, wx dark mode applies
  to windows created afterwards, so `App.OnInit` applies it before the
  main window is created, and changing it shows *Restart BleachBit for
  full effect.*

## Cookies to keep

The **Cookies** page is the counterpart of `GuiCookie.CookieManagerPane`.
It lists the cookie hosts found in the browsers
(`Cookie.list_unique_cookies`) plus those already kept, and saves the
checked hosts to the same JSON keep list (`Cookie.COOKIE_KEEP_LIST_FILENAME`
in the options directory) as soon as one is toggled.  The list is
written to a temporary file that then replaces the old one, so a failed
save (such as a full disk) keeps the old list, and the page shows the
hosts as they were and the error.  Finding hosts
opens every browser cookie database, so it runs on a background thread
the first time the page is shown, with a *Loading cookies…* label.
There is a search box, a *Show Selected* checkbox (a toggle button in
GTK; a checkbox reads as on/off in screen readers), *Select All* and
*Deselect All* (for the visible hosts), a count of kept hosts, and a
*Learn more* link.  If the keep list cannot be read, the page stays
disabled rather than overwrite it.

## Expert mode

*Expert mode* (`expert_mode`) works as in GTK:

- Checking it asks for confirmation (`Dialogs.warning_confirm_dialog`).
- Without it, an option with a warning (marked ⚠ in the tree) cannot
  be checked: the tree refuses and a notice says *This option is
  protected. To bypass protection, enable expert mode.*  *Clean* skips
  such options and logs an error for each; *Clean only* from the tree
  menu is refused with a notice.  Preview is always allowed.
- With it, checking an option with a warning shows the warning first;
  *Remember my choice* stores it (`Options.remember_warning_preference`),
  and *Reset warning confirmations* clears these choices.  The
  confirmation is shown after the tree has handled the click or key
  press (`MainFrame._allow_enable`), one at a time.
- Only expert mode can turn off the delete confirmation
  (`MainFrame._confirm_delete`); the confirmation then has a *Confirm
  before delete* checkbox, as in `GuiBasic.delete_confirmation_dialog`.
- After the first cleaner load, the Log shows the GTK startup notices
  when checked options need expert mode, or when the delete
  confirmation is off without expert mode.

## Interface language

`File → Preferences… → Languages` chooses the language of the
BleachBit interface.  The page sits right after **General**, as in
the GTK UI, and works the same way:

- The **BleachBit interface language** section has an
  *Auto-detect language* checkbox (on by default) and, indented below
  it, a *Language:* dropdown.  The dropdown is disabled while
  auto-detect is on.
- On POSIX systems, a **Language files to keep when cleaning
  applications** section follows, as in GTK: a
  `wx.dataview.DataViewListCtrl` (the native, accessible `GtkTreeView`
  on Linux) with *Keep*, *Code* and *Name* columns.  Toggling *Keep*
  calls `Options.set_language` at once.  Windows has no localizations
  cleaner, so the section is not shown there.
- The dropdown lists every language that has a compiled translation
  in `locale_dir`, plus `en` and `en_US`, as *Native name (code)*,
  for example `中文 (zh_TW)` or `United States English (en_US)`.  It
  shows the language in use now, and is updated when auto-detect is
  toggled, so it never shows a forced language that no longer applies.
- Changes are saved immediately, like the GTK UI, so OK and Cancel
  do not affect them.  They use the same `[bleachbit]` options as the
  GTK UI, so the choice carries across both front-ends:
  - unchecking *Auto-detect language* sets `auto_detect_lang = False`;
  - picking a language sets `forced_language` to its code;
  - checking *Auto-detect language* again sets
    `auto_detect_lang = True` and clears `forced_language`;
  - unchecking it keeps the detected language as `forced_language`,
    like GTK (the dropdown matches the language with
    `find_supported_language_code` and falls back to English).
- After a change, an info bar at the top of the dialog says
  *Restart BleachBit for full effect.*, already in the newly chosen
  language, and hides itself after 15 seconds.  When the dialog closes, the cleaner tree reloads so
  cleaner and option names use the new language (the main window
  calls `_reload_cleaners`, the counterpart of the GTK
  `cb_refresh_operations`).  The reload is skipped while cleaners are
  still loading or a preview or clean is running.  While cleaners load,
  `backends` is cleared and rebuilt, so Preview, Clean and the tree's
  *Preview only* / *Clean only* menu items are unavailable,
  `_start_worker` refuses to run cleaners, and options in the tree
  cannot be checked (a notice says cleaners are loading; unchecking
  still works); shredding files or folders still works.  Menus, buttons and the rest of the window change
  language after a restart.
- The language is applied at startup by
  `bleachbit.Language.setup_translation()`, which reads
  `get_active_language_code()`.  The portable build stores the
  options in `BleachBit.ini` next to `bleachbit-wx.exe`.

To test it, open **Preferences → Languages**, uncheck
*Auto-detect language*, pick a language (for example
`United States English (en_US)`), close the dialog, and check that the cleaner
names in the tree change.  Restart BleachBit to see the whole window
in the new language, then check *Auto-detect language* again to go
back to the system language.

## Shredding arbitrary files or folders

`File → Shred files…` opens a multi-select `wx.FileDialog`.
`File → Shred folders…` opens `wx.DirDialog` repeatedly until the user
cancels, allowing multiple folders to be picked.  Both feed into the
same path used by the GTK UI and CLI:

```python
Cleaner.backends['_gui'] = Cleaner.create_simple_cleaner(paths)
self._start_worker(really_delete=True, operations={'_gui': ['files']})
```

As before cleaning, a confirmation dialog is shown before shredding
(`MainFrame._confirm_delete`); only expert mode can turn it off with
`delete_confirmation`.

## Aborting a long-running operation

The **Abort** toolbar button sets `Worker.is_aborted = True`.  The
worker generator checks that flag at every yield point, including the
2-second yield inside `Wipe.wipe_path` used for `system.empty_space`,
so pressing Abort during a free-space wipe causes the wipe to stop
and clean up its temporary files at the next checkpoint (up to a
couple of seconds later).  The temporary files have an `atexit` hook
as a safety net even if the process is killed outright.

## Known MVP limitations

- The wx front-end does not check for software updates; the Updates
  page only edits the shared settings.
- The Cookies list is a `wx.ListCtrl`, which is native (and read by
  NVDA as checkable items) on Windows but generic on GTK.
- Chaff generator is not wired up.
- wx reuses the same gettext catalog and translated msgids as the GTK
  front-end. Keyboard shortcuts remain outside translatable strings and
  are defined explicitly with `wx.AcceleratorTable` and menu labels.

## Accessibility

The wx front-end aims to be usable by blind users via screen readers
(NVDA / Narrator on Windows, Orca on Linux):

- Every interactive control has either a visible label or an
  accessible name set via `SetName`, including the gauge, status
  text, results list, log, tree, and the two search/filter boxes.
- On Windows, `SetName` does not change the MSAA name of a *native*
  control (a list, edit box or list box), and a tooltip is not its
  MSAA description.  `Accessibility.set_accessible_name`,
  `set_accessible_description` and `set_tooltip` attach a small
  `wx.Accessible` that answers only the name or description; role,
  state and children still come from the system.  The Preferences
  dialog uses them for every new control: lists are named after their
  page and described by the page's notice, and every tooltip is also
  the description, so NVDA reads it when the control gets focus.
- Checkboxes are the exception.  In dark mode wx draws checkboxes
  itself (`BS_OWNERDRAW`), which the system reports as a *push button*
  with no checked state; wx's own accessible object corrects that, but
  `SetAccessible` replaces it.  So the `wx.Accessible` above reports
  the checkbox role and its checked, unavailable and focused state
  for every `wx.CheckBox`.  Use a `wx.CheckBox`, not a
  `wx.ToggleButton`, for on/off settings.
- `Accessibility.NoticeBar` (a `wx.InfoBar`) exposes its message as an
  MSAA *alert* and raises `EVENT_SYSTEM_ALERT` when it shows one, so
  NVDA speaks the notice without moving the focus.  The main window and
  the Preferences dialog use it for the GTK info bar messages.
- Option groups are `wx.StaticBox`es whose controls are their
  children, so NVDA announces the group name.  Confirmation dialogs are
  `wx.RichMessageDialog`s, which are native task dialogs on Windows.
  They use relabelled OK/Cancel buttons (e.g. *Delete* / *Cancel*)
  rather than Yes/No, with Cancel as the default, so Escape cancels.
- Checkable lists use native checkboxes where NVDA runs: the Cookies
  list is a `wx.ListCtrl` with `EnableCheckBoxes`, whose rows NVDA
  reads as checkable items.  (A generic `DataViewListCtrl` toggle only
  appears in the row description.)
- Buttons (Preview, Clean, Abort) have tooltips that name their
  keyboard shortcut.
- Tab and Shift+Tab move focus into and out of every control,
  including the cleaner tree and the Results list.  On Windows the
  tree hands Tab back to standard navigation (the generic
  `DataViewCtrl` would otherwise use it to move between cells), and
  the Results list sits on a `wx.Panel` notebook page so Tab can
  leave it.
- Shift+F10 and the Menu key open the context menu of the focused
  cleaner tree item or the selected Results rows, like a right-click,
  next to the focused row.  Both controls handle the keyboard
  `wx.EVT_CONTEXT_MENU` (the one whose position is
  `wx.DefaultPosition`).
- Global keyboard shortcuts (see `MainFrame._build_accelerators`):
  - **F5** — Preview
  - **Ctrl+Enter** — Clean
  - **Esc** — Abort
  - **Ctrl+F** — focus the results/log filter
  - **Ctrl+L** — focus the tree search
- Menu shortcuts: **Ctrl+Q** Exit, **Ctrl+,** Preferences,
  **Ctrl+Shift+F** Shred files, **Ctrl+Shift+D** Shred folders,
  **F1** About.

### Tree control

The cleaner/option tree is a `wx.dataview.DataViewCtrl` driven by a
custom `wx.dataview.PyDataViewModel` (`_CleanerTreeModel` in
`bleachbit/GUIwx/MainFrame.py`).  Two columns: a
`DataViewToggleRenderer` for the checkbox and a
`DataViewTextRenderer` for the cleaner / option label.

Why this control rather than `wx.lib.agw.customtreectrl.CustomTreeCtrl`
or `wx.TreeCtrl`:

- `CustomTreeCtrl` is owner-drawn and does **not** expose itself to
  MSAA/UIA on Windows, so screen readers cannot read individual rows
  or announce check state.
- `wx.TreeCtrl.EnableCheckBoxes` (the native checkbox path added in
  wxWidgets 3.1.5) is **not** bound in wxPython 4.2.3 Phoenix at the
  time of writing, so the native-checkbox approach is unavailable.
- `DataViewCtrl` maps to a native UIA Grid on Windows; a toggle
  column exposes the *Toggle* pattern, so NVDA/JAWS/Narrator
  announce the per-row check state and the space bar toggles it.
  This is the actual accessibility win for blind users.

The model holds no check state of its own: `GetValue` reads from
`Options.get_tree(cleaner_id, option_id)` and `SetValue` writes via
`Options.set_tree(...)`, the same `[tree]` section the GTK UI uses.
Cascading parent <-> children semantics live in `SetValue` and
`GetAttr` (a partially-checked cleaner row is rendered bold).
Filtering is implemented in the model: `set_filter` updates the
substring needle and calls `Cleared()`, after which the view asks
the model again for visible children.

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
