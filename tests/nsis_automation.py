# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

r"""Deterministic pywinauto driver for BleachBit NSIS setup/uninstall wizards.

Requires Windows, pywinauto, and Pillow:
    pip install pywinauto pillow

Run as a normal user; the script re-launches itself elevated and logs to
%TEMP%\bleachbit_nsis_test. Needs an interactive desktop session.
The installer language is forced to English for text-based page detection.

WARNING: destructive. Every mode first removes any existing BleachBit
install (per-machine and per-user), including its registry keys and
shortcuts, and the run ends by removing it again (use --keep to skip the
final cleanup). Run it in a VM or on a disposable machine.

Not covered: scenarios that need an unelevated standard user (per-user
upgrade without elevation, per-machine to per-user migration) because
the script always runs elevated, and uninstalling while the app is
running because it leaves pending delete-at-reboot entries that would
remove a later install.
Runs stop if an operation queues a rename or deletion in an install directory.
Existing unrelated pending operations, including NSIS temp cleanup, are ignored.

Usage:
    python nsis_automation.py basic|per_user|uninstall_keep_files|reinstall --new C:\path\new-setup.exe
    python nsis_automation.py upgrade|cross_arch|upgrade_running|upgrade_components|silent_upgrade|all --old C:\path\old-setup.exe --new C:\path\new-setup.exe
    Several modes may be listed. Options: --keep, --alert once|multiple

basic:    install --new (per-machine), then uninstall; verify registry,
          files, and shortcuts.
per_user: install --new (per-user), then uninstall; verify HKCU registry,
          HKCU shred verb, %LOCALAPPDATA%\BleachBit, and user shortcuts.
upgrade:  install --old, upgrade to --new; verify version bump and keys.
cross_arch:
          install --old, upgrade to --new of the other architecture (x86
          and x64 setups, either way); verify the old folder is gone and
          only the new architecture's Uninstall key is left.
upgrade_running:
          install --old, upgrade to --new while the app runs: canceling
          the locked-file prompt keeps the old install; closing the app
          and retrying lets the upgrade through.
upgrade_components:
          install --old without Desktop shortcut, translations, or shred
          verb; upgrade to --new and verify component selection is kept.
uninstall_keep_files:
          install --new, add a custom file in the install dir, uninstall;
          verify no reboot prompt and the custom file is kept.
silent_upgrade:
          install --old, then run --new /S /allusers: aborts while the
          app runs and upgrades silently once it is closed.
reinstall: install --new, then reinstall --new over itself.
all:      run every mode but cross_arch in sequence.
"""

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import winsound
import winreg
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab
from pywinauto import Desktop, findwindows

RESULTS_DIR = Path(tempfile.gettempdir()) / "bleachbit_nsis_test"
TITLE_RE = re.compile(r"(?i)bleachbit")
UNPACK_RE = re.compile(
    r"unpacking data:|verifying installer:|please wait while setup is loading",
    re.I)
# Per-machine folders of the x86 and the x64 build
PER_MACHINE_INSTALL_DIRS = tuple(
    Path(os.environ.get(var, default)) / "BleachBit"
    for var, default in (("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                         ("ProgramW6432", r"C:\Program Files")))
PER_USER_INSTALL_DIR = (
    Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"))
    / "BleachBit"
)
UNINST_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\BleachBit"
SHRED_KEY = r"Software\Classes\AllFilesystemObjects\shell\shred.bleachbit"
APP_EXES = ("bleachbit.exe", "bleachbit_console.exe")

# ---------------------------------------------------------------- elevation


class SHELLEXECUTEINFOW(ctypes.Structure):
    """Input for shell32.ShellExecuteExW."""

    _fields_ = [
        ("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


def is_admin():
    """Return True when running with admin rights."""
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def relaunch_elevated(argv):
    """Re-run this script elevated, wait for it, return its exit code."""
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    params = subprocess.list2cmdline(
        [os.path.abspath(__file__), *argv, "--elevated"])
    if _alert_mode != "off":
        alert_popup("About to request elevation.\n"
                    "When the UAC dialog appears, accept it.")
    sei = SHELLEXECUTEINFOW()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = 0x40  # SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb = "runas"
    sei.lpFile = sys.executable
    sei.lpParameters = params
    sei.lpDirectory = os.getcwd()
    sei.nShow = 1  # SW_SHOWNORMAL
    if not shell32.ShellExecuteExW(ctypes.byref(sei)):
        err = ctypes.get_last_error()
        if err == 1223:  # ERROR_CANCELLED
            print("elevation declined (UAC canceled); nothing ran")
            return 2
        raise ctypes.WinError(err)
    kernel32.WaitForSingleObject(sei.hProcess, 0xFFFFFFFF)
    code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(code))
    kernel32.CloseHandle(sei.hProcess)
    return code.value

# ------------------------------------------------------------------ logging


_log_file = None

# --------------------------------------------------------------- user alert

ALERT_BEEPS = 5            # beeps per consent prompt in 'multiple' mode
ALERT_BEEP_INTERVAL = 5.0  # seconds between repeated beeps
_alert_mode = "off"


def alert_popup(text, timeout_ms=3000):
    """Auto-dismissing popup; falls back to a normal MessageBox."""
    try:
        ctypes.windll.user32.MessageBoxTimeoutW(
            0, text, "bleachbit_nsis_test", 0x40, 0, timeout_ms)
    except AttributeError:
        ctypes.windll.user32.MessageBoxW(0, text, "bleachbit_nsis_test", 0x40)
    except Exception:
        # the alert is best-effort, never fail the run over it
        pass


def beep():
    """Play a short tone; ignore audio errors."""
    try:
        winsound.Beep(880, 300)
    except Exception:
        # no sound device
        pass


def consent_exe_running():
    """Return True while a UAC consent.exe process is running."""
    out = subprocess.run(
        ["tasklist", "/fi", "IMAGENAME eq consent.exe", "/fo", "csv", "/nh"],
        capture_output=True, check=False, text=True).stdout
    return "consent.exe" in out.lower()


class ConsentWatcher(threading.Thread):
    """Beeps whenever a UAC consent.exe process appears."""

    def __init__(self, mode):
        super().__init__(daemon=True)
        self.mode = mode  # 'once' or 'multiple'

    def run(self):
        """Beep each time a UAC consent prompt appears."""
        seen = False
        while True:
            running = consent_exe_running()
            if running and not seen:
                seen = True
                if self.mode == "once":
                    beep()
                else:
                    for _ in range(ALERT_BEEPS):
                        beep()
                        time.sleep(ALERT_BEEP_INTERVAL)
                        if not consent_exe_running():
                            break
            elif not running:
                seen = False
            time.sleep(1.0)


def log(msg):
    """Print a timestamped line and append it to the log file."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()

# ------------------------------------------------------------------- driver


def proc_image_path(pid):
    """Full image path of a process, or '' if not queryable."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h = kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
    finally:
        kernel32.CloseHandle(h)
    return ""


CLICK_PRIORITY = [
    "i &agree", "&next", "&install", "&uninstall", "&retry",
    "ok", "&yes", "&finish", "&close",
]
SAFE_ON_REBOOT_DEFER = ["&no", "no", "&cancel", "cancel"]
SAFE_ON_REBOOT_COMMIT = ["&close", "&finish"]
REBOOT_LATER_RE = re.compile(r"later|manually|do not|don't|skip", re.I)


class StuckError(RuntimeError):
    """The driver could not make progress or found no safe action."""


class PendingFileOperationError(StuckError):
    """An install directory has pending operations that make testing unsafe."""


def _enabled(b):
    """Return b.is_enabled(), or False when not queryable."""
    try:
        return b.is_enabled()
    except Exception:
        return False


def _button_by_id(buttons, *control_ids):
    """Find an enabled push button without depending on its translated label."""
    for control_id in control_ids:
        for b in buttons:
            if b.control_id() == control_id and _enabled(b):
                return b, (b.window_text() or "").strip().lower()
    return None, None


def _is_window(hwnd):
    """Return True if hwnd is an existing, visible Win32 window."""
    user32 = ctypes.windll.user32
    return bool(user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd))


def all_dialogs():
    """Return all visible top-level #32770 dialog wrappers."""
    wins = []
    for hwnd in findwindows.find_windows(class_name="#32770"):
        if not _is_window(hwnd):
            continue
        try:
            # Resolve wrapper_object() immediately: a lazy WindowSpecification
            # blocks for 5s per attribute access once its hwnd closes.
            w = Desktop(backend="win32").window(handle=hwnd).wrapper_object()
            if w.is_visible():
                wins.append(w)
        except Exception:
            continue
    return wins


def _nsis_owned_path(path):
    """True if an image path looks like our installer/uninstaller copy.

    NSIS re-runs uninstallers from %TEMP% (~nsu*.tmp\\Un.exe) and the
    upgrade path executes a copy in $PLUGINSDIR (ns*.tmp); their dialog
    titles (language picker, uninstall wizard) need not contain
    'BleachBit'. Excludes the installed application executables.
    """
    if not path:
        return False
    path = os.path.normcase(path)
    base = os.path.basename(path)
    if base in APP_EXES:
        return False
    for d in (*PER_MACHINE_INSTALL_DIRS, PER_USER_INSTALL_DIR,
              install_dir("all_users"), install_dir("current_user")):
        if path.startswith(os.path.normcase(str(d)) + os.sep):
            return True
    temp = os.path.normcase(tempfile.gettempdir()) + os.sep
    if not path.startswith(temp):
        return False
    parent = os.path.basename(os.path.dirname(path)).lower()
    return ((parent.endswith(".tmp")
             and parent.startswith(("ns", "~nsu")))
            or bool(GENERIC_NAME_RE.search(base)))


def _is_unpack_banner(win):
    """Return True if win is the transient NSIS unpacking splash dialog."""
    try:
        texts = [
            (c.window_text() or "").strip()
            for c in win.descendants()
        ]
    except Exception:
        return True
    joined = " ".join(t for t in texts if t)
    return not joined or bool(UNPACK_RE.search(joined))


def find_setup_window():
    """Return the BleachBit wizard dialog, or None."""
    for w in all_dialogs():
        try:
            pid = w.process_id()
            path = proc_image_path(pid)
            if os.path.basename(path).lower() in APP_EXES:
                continue
            matched = (
                bool(TITLE_RE.search(w.window_text() or ""))
                or bool(TITLE_RE.search(os.path.basename(path)))
                or _nsis_owned_path(path)
            )
            if matched and not _is_unpack_banner(w):
                return w
        except Exception:
            continue
    return None


def _any_nsis_proc_running():
    """Return True if any NSIS installer or uninstaller stub is running."""
    return any(_nsis_owned_path(proc_image_path(pid))
               for pid in tasklist_names())


# Name match safe to kill anywhere: only our own processes match.
KILL_NAME_RE = re.compile(r"bleachbit", re.I)
# Generic names shared with other installers: kill only when the image
# lives in the install dir or %TEMP% (NSIS temp uninstaller stubs).
GENERIC_NAME_RE = re.compile(
    r"uninst|un_a|^un\.exe$|^[ab]u_.*\.exe$", re.I)


def tasklist_names():
    """Return {pid: image name} for all processes."""
    out = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                         capture_output=True, check=False, text=True).stdout
    names = {}
    for line in out.splitlines():
        m = re.match(r'"([^"]+)","(\d+)"', line)
        if m:
            names[int(m.group(2))] = m.group(1)
    return names


def preflight(exe_path, keep=None):
    """Kill leftover installer processes and close stale wizard windows.

    A process whose image path equals keep is spared; the upgrade tests
    keep the installed app running on purpose.
    """
    wanted = os.path.normcase(str(exe_path)) if exe_path else ""
    keep = os.path.normcase(str(keep)) if keep else None
    dirs = [os.path.normcase(str(d)) + os.sep for d in (
        *PER_MACHINE_INSTALL_DIRS, PER_USER_INSTALL_DIR,
        install_dir("all_users"), install_dir("current_user"),
        tempfile.gettempdir())]
    for pid, name in tasklist_names().items():
        path = os.path.normcase(proc_image_path(pid))
        if keep and path == keep:
            continue
        kill = bool(KILL_NAME_RE.search(name))
        if not kill:
            if wanted and path == wanted:
                kill = True
            elif GENERIC_NAME_RE.search(name):
                kill = any(path.startswith(d) for d in dirs)
        if kill:
            log(f"  preflight kill: {name} pid={pid}")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, check=False)
    for _ in range(30):
        if not find_setup_window():
            return
        for w in all_dialogs():
            try:
                if TITLE_RE.search(w.window_text() or ""):
                    w.close()
            except Exception:
                # window closed under us; the loop rechecks
                pass
        time.sleep(0.5)
    raise StuckError("leftover BleachBit window would not close")


class WizardDriver:
    """Steps through any NSIS #32770 wizard whose title mentions BleachBit."""

    # The installer's fc-cache step can take ten minutes, as its text says
    def __init__(self, shots_dir, idle_timeout=660, first_timeout=120,
                 cancel_locked=False, locked_callback=None, proc=None,
                 scope="all_users"):
        self.shots_dir = shots_dir
        self.idle_timeout = idle_timeout
        self.first_timeout = first_timeout
        self.cancel_locked = cancel_locked
        self.locked_callback = locked_callback
        self._locked_cb_fired = False
        self.proc = proc
        self.scope = scope
        self.flags = set()
        self.step = 0
        self.last_sig = None
        self.same_sig_count = 0

    def find_window(self):
        """Return the BleachBit wizard dialog, or None."""
        return find_setup_window()

    def wait_window(self, timeout):
        """Poll up to timeout seconds for the wizard dialog."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            w = self.find_window()
            if w:
                return w
            time.sleep(0.5)
        return None

    @staticmethod
    def page_texts(win):
        """Return non-empty text of all descendant controls."""
        if not _is_window(win.handle):
            return []
        texts = []
        try:
            for c in win.descendants():
                t = (c.window_text() or "").strip()
                if t:
                    texts.append(t)
        except Exception:
            # page changed mid-walk; return what was read
            pass
        return texts

    def snapshot(self, win):
        """Save a screenshot of the wizard window."""
        if not _is_window(win.handle):
            return
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        try:
            r = win.rectangle()
            img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
            img.save(self.shots_dir / f"step{self.step:02d}.png")
        except Exception as e:
            log(f"  screenshot failed: {e}")

    def _reboot_click(self, buttons, labels, texts):
        """Pick a safe click on a reboot prompt, or raise."""
        # Never permit a real reboot: Finish/Close execute whichever
        # radio is checked, so allow them only after a 'later' option is
        # selected. Defer/cancel buttons are always safe on their own.
        button, label = _button_by_id(labels.values(), 7, 2)  # IDNO, IDCANCEL
        if button:
            return button, label
        later_selected = False
        for b in buttons:
            t = (b.window_text() or "").lower()
            if (b.friendly_class_name() != "Button"
                    and REBOOT_LATER_RE.search(t)):
                try:
                    if not b.is_checked():
                        b.click()
                except Exception:
                    b.click()
                later_selected = True
                log(f"  reboot page: selected {b.window_text()!r}")
                time.sleep(0.5)
                break
        wants = list(SAFE_ON_REBOOT_DEFER)
        if later_selected:
            wants += SAFE_ON_REBOOT_COMMIT
        for want in wants:
            for label, b in labels.items():
                if _enabled(b) and (label.startswith(want)
                                    or REBOOT_LATER_RE.search(label)):
                    return b, label
        raise StuckError(f"reboot prompt without safe option: {texts[:8]}")

    def _select_install_mode(self, buttons):
        """Select the 'All users' or 'For me' radio button on Choose Users."""
        needle = ("for me" if self.scope == "current_user"
                  else "all users")
        for b in buttons:
            if b.friendly_class_name() == "Button":
                continue
            norm = (b.window_text() or "").replace("&", "").lower()
            if needle in norm:
                try:
                    if not b.is_checked():
                        b.click()
                        log(f"  selected {b.window_text()!r}")
                except Exception:
                    b.click()
                    log(f"  clicked {b.window_text()!r}")
                time.sleep(0.5)
                break

    def drive(self):
        """Click through the wizard until no BleachBit window remains."""
        win = self.wait_window(self.first_timeout)
        if not win:
            raise StuckError("no setup window appeared")
        gone_since = None
        while True:
            texts = self.page_texts(win)
            if not texts:
                nxt = self.wait_window(5.0)
                if nxt:
                    win = nxt
                    continue
            joined = " ".join(texts).lower()
            sig = hash(joined)
            buttons = []
            try:
                for c in win.descendants():
                    if c.friendly_class_name() in (
                            "Button", "RadioButton", "CheckBox"):
                        buttons.append(c)
            except Exception:
                # page changed mid-walk; keep what was found
                pass
            btn_joined = " ".join(
                (b.window_text() or "").lower() for b in buttons)
            # Reboot detection must look at controls, not body text: the
            # Welcome page itself mentions "reboot" in its blurb.
            reboot_page = (
                "reboot now" in joined
                or "reboot" in btn_joined or "restart" in btn_joined
                or (("reboot" in joined or "restart" in joined)
                    and len(texts) <= 4))
            if reboot_page:
                self.flags.add("saw_reboot")
            if "already installed" in joined:
                self.flags.add("saw_already_installed")
            # the installer asks to close BleachBit before any file is written
            locked_page = ("error opening file for writing" in joined
                           or "bleachbit is running" in joined)
            if locked_page:
                self.flags.add("saw_locked_file")
                if self.locked_callback and not self._locked_cb_fired:
                    self._locked_cb_fired = True
                    self.locked_callback()
            if "finish" in joined:
                self.flags.add("saw_finish")
            log(f"  page {self.step}: {texts[:6]}")
            self.snapshot(win)
            self.step += 1

            if sig == self.last_sig:
                self.same_sig_count += 1
                if self.same_sig_count >= 10:
                    raise StuckError(f"stuck on page: {texts[:8]}")
            else:
                self.same_sig_count = 0
            self.last_sig = sig

            # Select the requested install mode radio on "Choose Users".
            # Skip push buttons: clicking one may advance the page and
            # invalidate the controls list used below.
            self._select_install_mode(buttons)

            # License pages gate Next behind an "accept" radio.
            # Skip push buttons for the same reason as above.
            for b in buttons:
                t = (b.window_text() or "").lower()
                if (b.friendly_class_name() != "Button"
                        and re.search(r"accept|agree", t)
                        and not re.search(r"not|decline", t)):
                    try:
                        if not b.is_checked():
                            b.click()
                            log(f"  selected {b.window_text()!r}")
                    except Exception:
                        b.click()
                        log(f"  clicked {b.window_text()!r}")
                    time.sleep(0.5)
                    break

            # Uncheck 'run/launch app' boxes: launching bleachbit.exe at the
            # end triggers its own UAC prompt via consent.exe.
            for b in buttons:
                t = (b.window_text() or "").strip().lower()
                if (b.friendly_class_name() in ("CheckBox", "Button")
                        and re.search(r"\b(run|launch|open|view)\b", t)
                        and "shortcut" not in t and "menu" not in t):
                    try:
                        if b.is_checked():
                            b.click()
                            log(f"  unchecked {b.window_text()!r}")
                    except Exception as e:
                        log(f"  could not uncheck {t!r}: {e}")
                    break

            labels = {(b.window_text() or "").strip().lower(): b
                      for b in buttons
                      if b.friendly_class_name() == "Button"}
            clicked = None
            clicked_label = None
            if reboot_page:
                clicked, clicked_label = self._reboot_click(
                    buttons, labels, texts)
            elif locked_page:
                # Native MessageBox labels follow Windows' UI language.
                control_id = 2 if self.cancel_locked else 4  # IDCANCEL, IDRETRY
                clicked, clicked_label = _button_by_id(
                    labels.values(), control_id)
                if not clicked:
                    log(f"  locked-file page lacks button {control_id}; "
                        "waiting")
            elif buttons:
                for want in CLICK_PRIORITY:
                    for label, b in labels.items():
                        if _enabled(b) and label.startswith(want):
                            clicked, clicked_label = b, label
                            break
                    if clicked:
                        break
                if not clicked:
                    clicked, clicked_label = _button_by_id(
                        labels.values(), 1, 6)  # IDOK, IDYES
                if not clicked:
                    log("  no enabled actionable button; waiting")
            if clicked:
                log(f"  click: {clicked_label!r}")
                try:
                    clicked.click()
                except Exception:
                    clicked.click_input()
                gone_since = None

            # Wait for the page to change or the window to vanish.
            time.sleep(0.8)
            deadline = time.time() + self.idle_timeout
            advanced = False
            while time.time() < deadline and not advanced:
                nxt = self.find_window()
                if not nxt:
                    # A live installer or temp uninstaller stub with no
                    # matching window is busy (e.g. unpacking $PLUGINSDIR).
                    if ((self.proc is not None and self.proc.poll() is None)
                            or _any_nsis_proc_running()):
                        gone_since = None
                    else:
                        if gone_since is None:
                            gone_since = time.time()
                        if time.time() - gone_since > 3.0:
                            return  # process gone and quiet -> wizard done
                else:
                    gone_since = None
                    nxt_texts = self.page_texts(nxt)
                    if nxt_texts:
                        new_sig = hash(" ".join(nxt_texts).lower())
                        if nxt.handle != win.handle or new_sig != sig:
                            win = nxt
                            advanced = True
                time.sleep(0.5)
            if not advanced:
                raise StuckError(
                    f"timed out waiting for next page; texts={texts[:8]} "
                    f"labels={list(labels)}")


def run_wizard(exe_path, shots_dir, keep=None, expected_exit=0, **driver_kwargs):
    """Launch exe_path, drive its wizard to completion, return page flags."""
    exe_path = Path(exe_path)
    if not exe_path.is_file():
        raise StuckError(f"executable not found: {exe_path}")
    with watch_pending_file_operations():
        preflight(exe_path, keep=keep)
        force_english()
        log(f"launching {exe_path.name}")
        return _drive_wizard(exe_path, shots_dir, expected_exit, driver_kwargs)


def _drive_wizard(exe_path, shots_dir, expected_exit, driver_kwargs):
    """Drive the launched process, including an explicitly expected exit code."""
    with subprocess.Popen([str(exe_path)]) as proc:
        d = WizardDriver(shots_dir, proc=proc, **driver_kwargs)
        err = None
        try:
            d.drive()
        except Exception as e:
            err = e
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            log("  killing lingering installer process tree")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, check=False)
            if err is None:
                err = StuckError("installer process did not exit cleanly")
        log(f"  exit code: {proc.returncode} (expected {expected_exit})")
        if err is None and proc.returncode != expected_exit:
            err = StuckError(
                f"installer exited {proc.returncode}; expected {expected_exit}")
        log(f"  wizard flags: {sorted(d.flags)}")
    if err:
        raise err
    return d.flags

# -------------------------------------------------------------- inspection


def read_reg(root, path, value_name=None):
    """Return {view: value_or_True} for each registry view where key exists."""
    out = {}
    for tag, flag in (("64", winreg.KEY_WOW64_64KEY),
                      ("32", winreg.KEY_WOW64_32KEY)):
        try:
            k = winreg.OpenKey(root, path, 0, winreg.KEY_READ | flag)
        except OSError:
            continue
        try:
            if value_name is None:
                out[tag] = True
            else:
                try:
                    out[tag] = winreg.QueryValueEx(k, value_name)[0]
                except OSError:
                    out[tag] = None
        finally:
            winreg.CloseKey(k)
    return out


def delete_reg_tree(root, subkey):
    """Recursively delete subkey in both 32-bit and 64-bit registry views."""
    for flag in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
        try:
            with winreg.OpenKey(
                    root, subkey, 0,
                    winreg.KEY_READ | winreg.KEY_WRITE | flag) as k:
                children = []
                try:
                    while True:
                        children.append(winreg.EnumKey(k, len(children)))
                except OSError:
                    pass
            for child in children:
                delete_reg_tree(root, f"{subkey}\\{child}")
            winreg.DeleteKeyEx(root, subkey, flag, 0)
        except OSError:
            continue


def safe_rmtree(path):
    """Remove an install dir, refusing anything not named BleachBit.

    The path may come from the registry, so never trust it blindly.
    """
    path = Path(path)
    if path.name.lower() != "bleachbit" or len(path.parts) < 3:
        log(f"  refusing to delete unexpected directory: {path}")
        return
    shutil.rmtree(path, ignore_errors=True)


def sha256(path):
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _scope_root(scope):
    """Return the registry hive root for scope."""
    return (winreg.HKEY_CURRENT_USER if scope == "current_user"
            else winreg.HKEY_LOCAL_MACHINE)


def install_dir(scope="all_users"):
    """Return the install dir from the registry for scope, or the default."""
    loc = read_reg(_scope_root(scope), UNINST_KEY, "InstallLocation")
    for v in loc.values():
        if v:
            return Path(v)
    if scope == "current_user":
        return PER_USER_INSTALL_DIR
    return next((d for d in PER_MACHINE_INSTALL_DIRS if d.exists()),
                PER_MACHINE_INSTALL_DIRS[0])


def all_install_dirs(scope="all_users"):
    """Return registered and default install dirs for scope, both arches."""
    loc = read_reg(_scope_root(scope), UNINST_KEY, "InstallLocation")
    dirs = [Path(v) for v in loc.values() if v]
    dirs += ([PER_USER_INSTALL_DIR] if scope == "current_user"
             else PER_MACHINE_INSTALL_DIRS)
    return list(dict.fromkeys(dirs))


def _shell_folder(csidl):
    """Return a shell folder path, honoring redirection (e.g., OneDrive)."""
    buf = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf):
        raise OSError(f"SHGetFolderPathW failed for CSIDL {csidl:#x}")
    return Path(buf.value)


def shortcut_dirs(scope="all_users"):
    """Return (start_menu_programs_dir, desktop_dir) for scope."""
    # CSIDL_PROGRAMS, CSIDL_DESKTOPDIRECTORY and their COMMON_ variants
    if scope == "current_user":
        return _shell_folder(0x02), _shell_folder(0x10)
    return _shell_folder(0x17), _shell_folder(0x19)


def shortcuts_found(scope="all_users"):
    """Return BleachBit shortcuts on Start Menu and Desktop for scope."""
    found = []
    for b in shortcut_dirs(scope):
        if b.exists():
            found += [str(p) for p in b.rglob("*bleachbit*.lnk")]
    return found


def system_state(scope="all_users", idir=None):
    """Return a dict of the on-disk and registry install state for scope."""
    idir = install_dir(scope) if idir is None else Path(idir)
    root = _scope_root(scope)
    uninst = idir / "uninstall.exe"
    return {
        "scope": scope,
        "install_dir": str(idir),
        "install_dir_exists": idir.exists(),
        "exe": (idir / "bleachbit.exe").exists(),
        "uninstall_exe": uninst.exists(),
        "uninstall_sha": sha256(uninst) if uninst.exists() else None,
        "reg_uninstall_version": read_reg(root, UNINST_KEY, "DisplayVersion"),
        "reg_uninstall_present": bool(read_reg(root, UNINST_KEY)),
        "shred_hklm": read_reg(winreg.HKEY_LOCAL_MACHINE, SHRED_KEY),
        "shred_hkcu": read_reg(winreg.HKEY_CURRENT_USER, SHRED_KEY),
        "shortcuts": shortcuts_found(scope),
    }


def check(results, name, ok, detail=""):
    """Record a check result and log it as PASS or FAIL."""
    results.append((name, bool(ok), detail))
    log(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")


def force_english():
    """Set the language consumed by NSIS' language picker and uninstaller."""
    with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, r"Software\BleachBit", 0,
            winreg.KEY_SET_VALUE | winreg.KEY_WOW64_32KEY) as key:
        winreg.SetValueEx(key, "Installer Language", 0, winreg.REG_SZ, "1033")


def pending_file_operations(dirs):
    """Return pending source/destination pairs affecting the given directories."""
    try:
        with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager") as key:
            paths, _ = winreg.QueryValueEx(key, "PendingFileRenameOperations")
    except FileNotFoundError:
        return set()

    def normalized(path):
        # Windows can prefix pending paths with flags, followed by an NT prefix.
        path = re.sub(r"^\*\d+", "", path).lstrip("!")
        if path.startswith(("\\??\\", "\\\\?\\")):
            path = path[4:]
        return os.path.normcase(path)

    roots = [os.path.normcase(str(d)).rstrip("\\") for d in dirs]

    def related(path):
        path = normalized(path)
        return any(path == root or path.startswith(root + "\\") for root in roots)

    return {(source, dest) for source, dest in zip(paths[::2], paths[1::2])
            if related(source) or related(dest)}


@contextmanager
def watch_pending_file_operations():
    """Reject existing or newly queued operations that could damage an install."""
    # Retain custom paths even if uninstall removes their registry entries.
    dirs = {*PER_MACHINE_INSTALL_DIRS, PER_USER_INSTALL_DIR,
            install_dir("all_users"), install_dir("current_user")}
    before = pending_file_operations(dirs)
    if before:
        raise PendingFileOperationError(
            f"existing pending install-file operations: {sorted(before)}; "
            "reboot the test machine before retrying")
    try:
        yield
    finally:
        dirs.update((install_dir("all_users"), install_dir("current_user")))
        added = pending_file_operations(dirs) - before
        if added:
            raise PendingFileOperationError(
                f"new pending install-file operations: {sorted(added)}; "
                "stopping without further cleanup; reboot before retrying")

# ----------------------------------------------------------- app & silent


def proc_running(exe_path):
    """Return True if a process with this image path is running."""
    wanted = os.path.normcase(str(exe_path))
    return any(os.path.normcase(proc_image_path(pid)) == wanted
               for pid in tasklist_names())


def launch_app(exe_path, settle=3.0):
    """Launch the installed app; return True while it stays running."""
    exe_path = Path(exe_path)
    if not exe_path.exists():
        log(f"  app not found: {exe_path}")
        return False
    log(f"launching {exe_path}")
    # pylint: disable-next=consider-using-with
    subprocess.Popen([str(exe_path)])
    time.sleep(settle)
    ok = proc_running(exe_path)
    if not ok:
        log("  app process exited or never started")
    return ok


def kill_path(exe_path):
    """Kill every process whose image path equals exe_path."""
    wanted = os.path.normcase(str(exe_path))
    for pid in tasklist_names():
        if os.path.normcase(proc_image_path(pid)) == wanted:
            log(f"  killing pid={pid} ({exe_path})")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, check=False)


def wait_for(pred, desc, timeout=60):
    """Poll pred once a second; return False when timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(1)
    log(f"  timeout waiting for {desc}")
    return False


def run_silent(exe_path, extra_args=(), keep=None, timeout=900):
    """Run an installer with /S; return its exit code (None on timeout)."""
    exe_path = Path(exe_path)
    if not exe_path.is_file():
        raise StuckError(f"executable not found: {exe_path}")
    with watch_pending_file_operations():
        preflight(exe_path, keep=keep)
        force_english()
        cmd = [str(exe_path), "/S", *extra_args]
        log("running silently: " + " ".join(cmd))
        try:
            rc = subprocess.run(cmd, timeout=timeout, check=False).returncode
        except subprocess.TimeoutExpired:
            log(f"  silent run did not exit within {timeout}s")
            return None
        time.sleep(3)  # let registry and files settle
        log(f"  exit code: {rc}")
        return rc


def ensure_uninstalled():
    """Remove any existing per-machine or per-user BleachBit installation."""
    with watch_pending_file_operations():
        preflight(None)
        for scope, flag in (("all_users", "/allusers"),
                            ("current_user", "/currentuser")):
            for idir in all_install_dirs(scope):
                uninst = idir / "uninstall.exe"
                if uninst.exists():
                    log(f"  cleanup: running existing uninstaller ({scope})")
                    tmp_uninst = (Path(tempfile.gettempdir())
                                  / "bb_cleanup_uninst.exe")
                    try:
                        shutil.copy(uninst, tmp_uninst)
                        subprocess.run(
                            [str(tmp_uninst), flag, "/S", f"_?={idir}"],
                            timeout=120, check=False)
                    except Exception as e:
                        log(f"  cleanup uninstaller error: {e}")
                    finally:
                        tmp_uninst.unlink(missing_ok=True)
                if idir.exists():
                    safe_rmtree(idir)
            delete_reg_tree(_scope_root(scope), UNINST_KEY)
            delete_reg_tree(_scope_root(scope), SHRED_KEY)
            start_dir, desktop_dir = shortcut_dirs(scope)
            shutil.rmtree(start_dir / "BleachBit", ignore_errors=True)
            (desktop_dir / "BleachBit.lnk").unlink(missing_ok=True)


def install_baseline(exe_path, results, label="old installed"):
    """Clean the system, silently install exe_path (/allusers), return state."""
    ensure_uninstalled()
    rc = run_silent(Path(exe_path), ["/allusers"])
    wait_for(lambda: os.path.exists(install_dir() / "bleachbit.exe"),
             "baseline bleachbit.exe", timeout=60)
    st = system_state()
    log("baseline state: " + json.dumps(st, indent=2, default=str))
    check(results, label,
          rc == 0 and st["exe"] and st["uninstall_exe"], f"rc={rc}")
    return st


def verify_old_intact(results, st_old, st, label):
    """Check that an aborted/canceled upgrade left the old install intact."""
    check(results, label,
          st["exe"] and st["reg_uninstall_present"]
          and st["uninstall_sha"] == st_old["uninstall_sha"]
          and st["reg_uninstall_version"] == st_old["reg_uninstall_version"],
          f"exe={st['exe']} reg={st['reg_uninstall_present']}")


def verify_upgraded(results, st_old, st):
    """Check standard post-upgrade invariants against st_old."""
    check(results, "install dir exists", st["install_dir_exists"])
    check(results, "bleachbit.exe present", st["exe"])
    check(results, "uninstall.exe replaced",
          st["uninstall_sha"]
          and st["uninstall_sha"] != st_old["uninstall_sha"])
    ver = [v for v in st["reg_uninstall_version"].values() if v]
    check(results, "version bumped", any(
        str(v) != str(o)
        for v in ver for o in st_old["reg_uninstall_version"].values() if o),
        f"old={st_old['reg_uninstall_version']} "
        f"new={st['reg_uninstall_version']}")
    check(results, "shred context menu intact",
          bool(st["shred_hklm"] or st["shred_hkcu"]),
          f"HKLM={st['shred_hklm']} HKCU={st['shred_hkcu']}")
    check(results, "shortcuts intact",
          bool(st["shortcuts"]), str(st["shortcuts"]))

# -------------------------------------------------------------------- modes


def _install_and_uninstall(exe_path, scope, tag):
    """Install exe_path in scope, then uninstall; return check results."""
    results = []
    ensure_uninstalled()
    log(f"== install ({tag}, {scope}) ==")
    flags = run_wizard(Path(exe_path), RESULTS_DIR / f"{tag}-install",
                       scope=scope)
    check(results, "wizard finished", "saw_finish" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    st = system_state(scope)
    log("state: " + json.dumps(st, indent=2, default=str))
    check(results, "install dir exists",
          st["install_dir_exists"], st["install_dir"])
    check(results, "bleachbit.exe present", st["exe"])
    check(results, "uninstall.exe present", st["uninstall_exe"])
    check(results, "Uninstall reg key", st["reg_uninstall_present"],
          str(st["reg_uninstall_version"]))
    if scope == "current_user":
        check(results, "HKLM Uninstall key absent",
              not read_reg(winreg.HKEY_LOCAL_MACHINE, UNINST_KEY))
        check(results, "shred context menu key in HKCU only",
              bool(st["shred_hkcu"]) and not st["shred_hklm"],
              f"HKLM={st['shred_hklm']} HKCU={st['shred_hkcu']}")
    else:
        check(results, "shred context menu key",
              bool(st["shred_hklm"] or st["shred_hkcu"]),
              f"HKLM={st['shred_hklm']} HKCU={st['shred_hkcu']}")
    check(results, "shortcuts present",
          bool(st["shortcuts"]), str(st["shortcuts"]))

    idir = Path(st["install_dir"])
    uninst = idir / "uninstall.exe"
    if not uninst.exists():
        check(results, "uninstaller available", False, str(uninst))
        return results
    log(f"== uninstall ({tag}, {scope}) ==")
    flags = run_wizard(uninst, RESULTS_DIR / f"{tag}-uninstall", scope=scope)
    check(results, "uninstall wizard finished", "saw_finish" in flags)
    check(results, "no reboot prompt on uninstall", "saw_reboot" not in flags)
    st = system_state(scope, idir=idir)
    log("state: " + json.dumps(st, indent=2, default=str))
    check(results, "install dir removed", not st["install_dir_exists"])
    check(results, "Uninstall reg key removed",
          not st["reg_uninstall_present"])
    check(results, "shred key removed",
          not st["shred_hklm"] and not st["shred_hkcu"])
    check(results, "shortcuts removed",
          not st["shortcuts"], str(st["shortcuts"]))
    return results


def mode_basic(a):
    """Install --new (per-machine), then uninstall; verify system state."""
    return _install_and_uninstall(a.new, "all_users", "basic")


def mode_per_user(a):
    """Install --new (per-user), then uninstall; verify HKCU and files."""
    return _install_and_uninstall(a.new, "current_user", "per_user")


def mode_upgrade(a):
    """Install --old via GUI, upgrade with --new, verify the upgrade state."""
    results = []
    ensure_uninstalled()
    log("== install (old) ==")
    flags_old = run_wizard(Path(a.old), RESULTS_DIR / "upgrade-old-install")
    st_old = system_state()
    log("old state: " + json.dumps(st_old, indent=2, default=str))
    check(results, "old installed",
          "saw_finish" in flags_old
          and st_old["exe"] and st_old["uninstall_exe"])

    log("== upgrade (new over old) ==")
    flags = run_wizard(Path(a.new), RESULTS_DIR / "upgrade-new-install")
    check(results, "'already installed' prompt seen",
          "saw_already_installed" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    check(results, "wizard finished", "saw_finish" in flags)
    st = system_state()
    log("new state: " + json.dumps(st, indent=2, default=str))
    verify_upgraded(results, st_old, st)
    return results


def mode_cross_arch(a):
    """Upgrade --old with a --new of the other architecture."""
    results = []
    log("== install (old) ==")
    st_old = install_baseline(a.old, results)
    old_dir = Path(st_old["install_dir"])
    # The x86 build registers in the 32-bit view, the x64 build in the 64-bit
    old_names = read_reg(winreg.HKEY_LOCAL_MACHINE, UNINST_KEY, "DisplayName")

    log("== upgrade (new arch over old) ==")
    flags = run_wizard(Path(a.new), RESULTS_DIR / "cross_arch-new-install")
    check(results, "'already installed' prompt seen",
          "saw_already_installed" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    check(results, "wizard finished", "saw_finish" in flags)
    st = system_state()
    log("new state: " + json.dumps(st, indent=2, default=str))
    check(results, "install dir changed",
          Path(st["install_dir"]) != old_dir, st["install_dir"])
    check(results, "old install dir removed", not old_dir.exists(),
          str(old_dir))
    check(results, "bleachbit.exe present", st["exe"])
    names = read_reg(winreg.HKEY_LOCAL_MACHINE, UNINST_KEY, "DisplayName")
    check(results, "one Uninstall reg key, in the other view",
          names in ({"32": "BleachBit"}, {"64": "BleachBit (64-bit)"})
          and names.keys() != old_names.keys(),
          f"old={old_names} new={names}")
    check(results, "shred context menu intact",
          bool(st["shred_hklm"] or st["shred_hkcu"]),
          f"HKLM={st['shred_hklm']} HKCU={st['shred_hkcu']}")
    check(results, "shortcuts intact",
          bool(st["shortcuts"]), str(st["shortcuts"]))
    return results


def mode_upgrade_running(a):
    """Upgrade --old to --new while the app is running.

    First run cancels the locked-file prompt and expects the old install
    to survive untouched; second run kills the app when the prompt
    appears, so the driver's retry lets the upgrade through.
    """
    results = []
    log("== install (old) ==")
    st_old = install_baseline(a.old, results)
    app_exe = Path(st_old["install_dir"]) / "bleachbit.exe"

    log("== upgrade, app running, cancel ==")
    check(results, "app running (cancel run)", launch_app(app_exe))
    flags = run_wizard(Path(a.new), RESULTS_DIR / "upgrade_running-cancel",
                       keep=app_exe, cancel_locked=True, expected_exit=2)
    check(results, "'already installed' prompt seen",
          "saw_already_installed" in flags)
    check(results, "locked-file prompt seen", "saw_locked_file" in flags)
    kill_path(app_exe)
    verify_old_intact(results, st_old, system_state(),
                      "old install intact after cancel")

    log("== upgrade, app running, retry after close ==")
    check(results, "app running (retry run)", launch_app(app_exe))
    flags = run_wizard(Path(a.new), RESULTS_DIR / "upgrade_running-retry",
                       keep=app_exe,
                       locked_callback=lambda: kill_path(app_exe))
    check(results, "locked-file prompt seen", "saw_locked_file" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    check(results, "wizard finished", "saw_finish" in flags)
    st = system_state()
    log("new state: " + json.dumps(st, indent=2, default=str))
    verify_upgraded(results, st_old, st)
    return results


def mode_upgrade_components(a):
    """Verify ReadOldComponents preserves deselected optional components.

    Installs --old, strips the Desktop shortcut, share\\locale, and the
    shred registry key (leaving Start Menu shortcuts in place), then runs
    --new via the GUI wizard and checks that only the Start Menu
    shortcuts and core files are installed.
    """
    results = []
    log("== install (old) and strip optional components ==")
    st_old = install_baseline(a.old, results)
    idir = Path(st_old["install_dir"])
    start_dir, desktop_dir = shortcut_dirs("all_users")
    desktop_lnk = desktop_dir / "BleachBit.lnk"
    locale_dir = idir / "share" / "locale"

    desktop_lnk.unlink(missing_ok=True)
    shutil.rmtree(locale_dir, ignore_errors=True)
    delete_reg_tree(winreg.HKEY_LOCAL_MACHINE, SHRED_KEY)
    delete_reg_tree(winreg.HKEY_CURRENT_USER, SHRED_KEY)
    check(results, "old optional components stripped",
          not desktop_lnk.exists() and not locale_dir.exists()
          and not read_reg(winreg.HKEY_LOCAL_MACHINE, SHRED_KEY))

    log("== upgrade (new over stripped old) ==")
    flags = run_wizard(
        Path(a.new), RESULTS_DIR / "upgrade_components-new-install")
    check(results, "'already installed' prompt seen",
          "saw_already_installed" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    check(results, "wizard finished", "saw_finish" in flags)
    st = system_state()
    log("new state: " + json.dumps(st, indent=2, default=str))
    check(results, "bleachbit.exe present", st["exe"])
    check(results, "uninstall.exe replaced",
          st["uninstall_sha"]
          and st["uninstall_sha"] != st_old["uninstall_sha"])
    check(results, "Start Menu shortcut preserved",
          (start_dir / "BleachBit" / "BleachBit.lnk").exists())
    check(results, "Desktop shortcut stayed unselected",
          not desktop_lnk.exists())
    check(results, "Translations stayed unselected",
          not locale_dir.exists())
    check(results, "Shred verb stayed unselected",
          not st["shred_hklm"] and not st["shred_hkcu"])
    return results


def mode_uninstall_keep_files(a):
    """Verify uninstall keeps user-added files without asking for a reboot."""
    results = []
    log("== install (new) ==")
    st_init = install_baseline(a.new, results, label="new installed")
    idir = Path(st_init["install_dir"])
    custom_file = idir / "custom_cleaner.xml"
    custom_file.write_text("<cleaner id='custom'/>\n", encoding="utf-8")
    check(results, "custom file created", custom_file.exists())

    log("== uninstall with custom file present ==")
    uninst = idir / "uninstall.exe"
    flags = run_wizard(uninst, RESULTS_DIR / "uninstall_keep_files")
    check(results, "uninstall wizard finished", "saw_finish" in flags)
    check(results, "no reboot prompt on uninstall", "saw_reboot" not in flags)
    st = system_state(idir=idir)
    log("post-uninstall state: " + json.dumps(st, indent=2, default=str))
    check(results, "bleachbit.exe removed", not st["exe"])
    check(results, "uninstall.exe removed", not st["uninstall_exe"])
    check(results, "custom file kept", custom_file.exists())
    check(results, "Uninstall reg key removed",
          not st["reg_uninstall_present"])
    check(results, "shred key removed",
          not st["shred_hklm"] and not st["shred_hkcu"])
    check(results, "shortcuts removed",
          not st["shortcuts"], str(st["shortcuts"]))

    safe_rmtree(idir)
    return results


def mode_silent_upgrade(a):
    """Silent /allusers upgrade of --old to --new.

    A silent upgrade must abort while the app is running (NSIS answers
    the locked-file prompt with its /SD IDCANCEL default and Abort
    exits nonzero), leaving the old install intact; rerun after the app
    closes to verify the silent upgrade itself.
    """
    results = []
    log("== install (old) ==")
    st_old = install_baseline(a.old, results)
    app_exe = Path(st_old["install_dir"]) / "bleachbit.exe"

    log("== silent upgrade while app runs ==")
    check(results, "app running", launch_app(app_exe))
    rc = run_silent(Path(a.new), ["/allusers"], keep=app_exe)
    check(results, "silent upgrade aborted while running",
          rc is not None and rc != 0, f"rc={rc}")
    verify_old_intact(results, st_old, system_state(),
                      "old install intact after abort")
    kill_path(app_exe)

    log("== silent upgrade after app closed ==")
    rc = run_silent(Path(a.new), ["/allusers"], keep=app_exe)
    check(results, "silent upgrade succeeded", rc == 0, f"rc={rc}")
    wait_for(lambda: os.path.exists(install_dir() / "bleachbit.exe"),
             "new bleachbit.exe", timeout=120)
    st = system_state()
    log("new state: " + json.dumps(st, indent=2, default=str))
    verify_upgraded(results, st_old, st)
    return results


def mode_reinstall(a):
    """Reinstall the same --new version over itself via the GUI wizard."""
    results = []
    log("== first install (new) ==")
    install_baseline(a.new, results, label="first install succeeded")

    log("== reinstall (new over new) ==")
    flags = run_wizard(Path(a.new), RESULTS_DIR / "reinstall")
    check(results, "'already installed' prompt seen",
          "saw_already_installed" in flags)
    check(results, "no reboot prompt", "saw_reboot" not in flags)
    check(results, "wizard finished", "saw_finish" in flags)
    st = system_state()
    log("reinstall state: " + json.dumps(st, indent=2, default=str))
    check(results, "install dir exists", st["install_dir_exists"])
    check(results, "bleachbit.exe present", st["exe"])
    check(results, "uninstall.exe present", st["uninstall_exe"])
    check(results, "Uninstall reg key", st["reg_uninstall_present"])
    check(results, "shred context menu intact",
          bool(st["shred_hklm"] or st["shred_hkcu"]))
    check(results, "shortcuts intact", bool(st["shortcuts"]))
    return results

# --------------------------------------------------------------------- main


MODES = {
    "basic": mode_basic,
    "per_user": mode_per_user,
    "upgrade": mode_upgrade,
    "cross_arch": mode_cross_arch,
    "upgrade_running": mode_upgrade_running,
    "upgrade_components": mode_upgrade_components,
    "uninstall_keep_files": mode_uninstall_keep_files,
    "silent_upgrade": mode_silent_upgrade,
    "reinstall": mode_reinstall,
}
NEEDS_OLD = {"upgrade", "cross_arch", "upgrade_running",
             "upgrade_components", "silent_upgrade"}


def installer_path(value):
    """Validate installer inputs before any elevation or destructive cleanup."""
    path = Path(value).absolute()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"installer is not a file: {value}")
    return path


def main():
    """Run _main and log any uncaught crash to %TEMP%."""
    try:
        _main()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            RESULTS_DIR.mkdir(exist_ok=True)
            (RESULTS_DIR / "crash.log").write_text(tb, encoding="utf-8")
        except Exception:
            # still printed below
            pass
        print(tb)
        sys.exit(1)


def _main():
    """Parse args, elevate if needed, run the requested mode(s), and exit."""
    p = argparse.ArgumentParser()
    p.add_argument("mode", nargs="+", choices=[*MODES, "all"])
    p.add_argument("--old", type=installer_path)
    p.add_argument("--new", type=installer_path)
    p.add_argument("--keep", action="store_true",
                   help="skip the final uninstall so state can be inspected")
    p.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--alert", choices=["off", "once", "multiple"],
                   default="off",
                   help="beep when a UAC consent prompt needs a human click")
    a = p.parse_args()
    # cross_arch needs --old and --new of different architectures
    modes = ([m for m in MODES if m != "cross_arch"] if "all" in a.mode
             else a.mode)
    if not a.new:
        p.error("--new is required")
    need_old = [m for m in modes if m in NEEDS_OLD]
    if need_old and not a.old:
        p.error(f"{', '.join(need_old)} requires --old")

    global _alert_mode  # pylint: disable=global-statement
    _alert_mode = a.alert

    if not a.elevated:
        if is_admin():
            log("already elevated; running directly")
        else:
            log("not elevated; re-launching (expect one UAC prompt)")
            sys.exit(relaunch_elevated(sys.argv[1:]))

    if a.alert != "off":
        ConsentWatcher(a.alert).start()

    global _log_file  # pylint: disable=global-statement
    RESULTS_DIR.mkdir(exist_ok=True)
    tag = "all" if "all" in a.mode else "-".join(modes)
    log_path = RESULTS_DIR / f"{tag}-{int(time.time())}.log"
    all_results = []
    pending_reboot = False
    with open(log_path, "w", encoding="utf-8") as log_f:
        _log_file = log_f
        for m in modes:
            log(f"================ mode: {m} ================")
            try:
                res = MODES[m](a)
            except StuckError as e:
                log(f"DRIVER ERROR ({m}): {e}")
                res = [(f"{m}: driver completed", False, str(e))]
                pending_reboot = isinstance(e, PendingFileOperationError)
            except Exception:
                import traceback
                log(f"UNEXPECTED ERROR ({m}):\n" + traceback.format_exc())
                res = [(f"{m}: driver completed", False,
                        "unexpected exception")]
            all_results.extend((f"{m}: {name}", ok, detail)
                               for name, ok, detail in res)
            if pending_reboot:
                break
        if not a.keep and not pending_reboot:
            try:
                ensure_uninstalled()
            except PendingFileOperationError as e:
                check(all_results, "final cleanup: no pending install-file operations",
                      False, str(e))

        failed = [r for r in all_results if not r[1]]
        passed = len(all_results) - len(failed)
        log(f"== done: {passed}/{len(all_results)} checks passed ==")
        for name, _, detail in failed:
            log(f"  FAILED: {name}  {detail}")
        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
