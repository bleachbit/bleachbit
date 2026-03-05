# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

"""
Windows-focused Qt frontend for accessibility.

This module is intentionally optional: when PySide6 is unavailable, callers
should fall back to the GTK frontend.
"""

from __future__ import annotations

from bleachbit import Options, Worker
from bleachbit.Cleaner import backends, register_cleaners
from bleachbit.Language import get_active_language_code, get_text as _

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)


class _QtCallback:
    """Worker callback adapter used by the Qt frontend."""

    def __init__(self, app: "BleachbitQt") -> None:
        self.app = app

    def append_text(self, msg, _tag=None):
        self.app.append_log(msg)
        QApplication.processEvents()

    def update_progress_bar(self, status):
        self.app.update_progress(status)

    def update_total_size(self, size):
        self.app.update_total_size(size)

    def update_item_size(self, operation, option_id, size):
        self.app.update_item_size(operation, option_id, size)

    def worker_done(self, _worker, _really_delete):
        return


class BleachbitQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BleachBit (Qt, Windows)")
        self.resize(980, 680)

        self._running = False
        self._progress_last_announced = -10
        self._cleaner_items = {}
        self._option_items = {}
        self._setup_ui()
        self._load_cleaners()

    def _t(self, english: str, polish: str) -> str:
        """Return a Polish-first text when active locale is Polish."""
        lang = (get_active_language_code() or "").lower()
        if lang.startswith("pl"):
            return polish
        return _(english)

    def _setup_menu(self):
        menu = self.menuBar()
        menu.setNativeMenuBar(False)
        menu.setAccessibleName(self._t("Main menu", "Menu główne"))

        m_file = menu.addMenu(self._t("&File", "&Plik"))
        m_edit = menu.addMenu(self._t("&Edit", "&Edycja"))
        m_actions = menu.addMenu(self._t("&Actions", "&Akcje"))
        m_view = menu.addMenu(self._t("&View", "&Widok"))
        m_help = menu.addMenu(self._t("&Help", "&Pomoc"))

        a_exit = QAction(self._t("E&xit", "&Zakończ"), self)
        a_exit.setShortcut("Alt+F4")
        a_exit.triggered.connect(self.close)
        m_file.addAction(a_exit)

        a_select_all = QAction(self._t("Select &All", "&Zaznacz wszystko"), self)
        a_select_all.setShortcut("Ctrl+A")
        a_select_all.triggered.connect(self._select_all)
        m_edit.addAction(a_select_all)

        a_clear_all = QAction(self._t("&Clear All", "&Wyczyść zaznaczenie"), self)
        a_clear_all.setShortcut("Ctrl+Shift+A")
        a_clear_all.triggered.connect(self._clear_all)
        m_edit.addAction(a_clear_all)

        a_preview = QAction(self._t("&Preview", "&Podgląd"), self)
        a_preview.setShortcut("F5")
        a_preview.triggered.connect(lambda: self._run_worker(False))
        m_actions.addAction(a_preview)

        a_clean = QAction(self._t("&Clean", "&Czyść"), self)
        a_clean.setShortcut("Ctrl+Return")
        a_clean.triggered.connect(lambda: self._run_worker(True))
        m_actions.addAction(a_clean)

        a_focus_tree = QAction(self._t("Focus &List", "Przejdź do &listy"), self)
        a_focus_tree.setShortcut("Ctrl+L")
        a_focus_tree.triggered.connect(self.tree.setFocus)
        m_view.addAction(a_focus_tree)

        a_focus_log = QAction(self._t("Focus &Log", "Przejdź do &logu"), self)
        a_focus_log.setShortcut("Ctrl+G")
        a_focus_log.triggered.connect(self.log.setFocus)
        m_view.addAction(a_focus_log)

        a_about = QAction(self._t("&About", "&O programie"), self)
        a_about.triggered.connect(self._show_about)
        m_help.addAction(a_about)

    def _setup_ui(self):
        root = QWidget(self)
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        title = QLabel(self._t(
            "Select items to clean, then preview or clean.",
            "Wybierz elementy do czyszczenia, a następnie użyj podglądu lub czyszczenia.",
        ))
        title.setAccessibleName(self._t("Instructions", "Instrukcje"))
        title.setAccessibleDescription(
            self._t(
                "Instructions for selecting cleaner options and running actions.",
                "Instrukcja wyboru opcji czyszczenia oraz uruchamiania akcji.",
            ))
        main_layout.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self._t("Cleaner", "Moduł"),
            self._t("Description", "Opis"),
        ])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAccessibleName(self._t("Cleaner options", "Opcje czyszczenia"))
        self.tree.setAccessibleDescription(
            self._t(
                "Tree of cleaners and options with checkboxes.",
                "Drzewo modułów i opcji z polami wyboru.",
            ))
        self.tree.itemChanged.connect(self._on_item_changed)
        main_layout.addWidget(self.tree, stretch=3)

        button_layout = QHBoxLayout()
        self.btn_select_all = QPushButton(self._t("&Select All", "&Zaznacz wszystko"))
        self.btn_clear = QPushButton(self._t("&Clear All", "&Wyczyść zaznaczenie"))
        self.btn_preview = QPushButton(self._t("&Preview", "&Podgląd"))
        self.btn_clean = QPushButton(self._t("&Clean", "&Czyść"))

        self.btn_select_all.setAccessibleName(self._t("Select all options", "Zaznacz wszystkie opcje"))
        self.btn_clear.setAccessibleName(self._t("Clear all options", "Wyczyść wszystkie opcje"))
        self.btn_preview.setAccessibleName(self._t("Preview selected options", "Podgląd wybranych opcji"))
        self.btn_clean.setAccessibleName(self._t("Clean selected options", "Czyść wybrane opcje"))

        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_preview.clicked.connect(lambda: self._run_worker(False))
        self.btn_clean.clicked.connect(lambda: self._run_worker(True))

        button_layout.addWidget(self.btn_select_all)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_preview)
        button_layout.addWidget(self.btn_clean)
        main_layout.addLayout(button_layout)

        progress_layout = QHBoxLayout()
        self.status_label = QLabel(self._t("Ready", "Gotowe"))
        self.status_label.setAccessibleName(self._t("Status", "Status"))
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setTextVisible(True)
        self.progress.setAccessibleName(self._t("Progress", "Postęp"))
        self.progress.setAccessibleDescription(
            self._t("Progress of current operation", "Postęp bieżącej operacji"))
        progress_layout.addWidget(self.status_label, stretch=2)
        progress_layout.addWidget(self.progress, stretch=3)
        main_layout.addLayout(progress_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setAccessibleName(self._t("Log output", "Log operacji"))
        self.log.setAccessibleDescription(
            self._t(
                "Output log for preview and cleaning operations.",
                "Log wyjściowy dla podglądu i czyszczenia.",
            ))
        main_layout.addWidget(self.log, stretch=2)

        # Predictable keyboard flow for screen readers and keyboard users.
        QWidget.setTabOrder(self.tree, self.btn_select_all)
        QWidget.setTabOrder(self.btn_select_all, self.btn_clear)
        QWidget.setTabOrder(self.btn_clear, self.btn_preview)
        QWidget.setTabOrder(self.btn_preview, self.btn_clean)
        QWidget.setTabOrder(self.btn_clean, self.progress)
        QWidget.setTabOrder(self.progress, self.log)

        # Build menu after target widgets exist.
        self._setup_menu()

    def _load_cleaners(self):
        list(register_cleaners())
        for key in sorted(backends):
            backend = backends[key]
            cleaner_id = backend.get_id()
            cleaner_name = backend.get_name()
            cleaner_item = QTreeWidgetItem(self.tree, [cleaner_name, cleaner_id])
            cleaner_item.setData(0, Qt.UserRole, ("cleaner", cleaner_id))
            cleaner_item.setFlags(cleaner_item.flags() | Qt.ItemIsUserCheckable)
            cleaner_item.setCheckState(0, Qt.Unchecked)
            self._cleaner_items[cleaner_id] = cleaner_item

            for option_id, option_name in backend.get_options():
                desc = ""
                if option_id in backend.options:
                    desc = backend.options[option_id][1] or ""
                child = QTreeWidgetItem(cleaner_item, [option_name, desc])
                child.setData(0, Qt.UserRole, ("option", cleaner_id, option_id))
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                checked = Options.options.get_tree(cleaner_id, option_id)
                child.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                self._option_items[(cleaner_id, option_id)] = child

            self._sync_cleaner_state(cleaner_id)
            cleaner_item.setExpanded(False)

    def _on_item_changed(self, item: QTreeWidgetItem, _column: int):
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        if payload[0] == "cleaner":
            cleaner_id = payload[1]
            state = item.checkState(0)
            self.tree.blockSignals(True)
            for (cid, _oid), opt_item in self._option_items.items():
                if cid == cleaner_id:
                    opt_item.setCheckState(0, state)
            self.tree.blockSignals(False)
            return

        cleaner_id = payload[1]
        self._sync_cleaner_state(cleaner_id)

    def _sync_cleaner_state(self, cleaner_id: str):
        parent = self._cleaner_items[cleaner_id]
        states = []
        for (cid, _oid), opt_item in self._option_items.items():
            if cid == cleaner_id:
                states.append(opt_item.checkState(0))
        if not states:
            return
        if all(state == Qt.Checked for state in states):
            parent.setCheckState(0, Qt.Checked)
        elif all(state == Qt.Unchecked for state in states):
            parent.setCheckState(0, Qt.Unchecked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)

    def _iter_option_items(self):
        for (cleaner_id, option_id), item in self._option_items.items():
            yield cleaner_id, option_id, item

    def _select_all(self):
        self.tree.blockSignals(True)
        for _cid, _oid, item in self._iter_option_items():
            item.setCheckState(0, Qt.Checked)
        self.tree.blockSignals(False)
        for cleaner_id in self._cleaner_items:
            self._sync_cleaner_state(cleaner_id)

    def _clear_all(self):
        self.tree.blockSignals(True)
        for _cid, _oid, item in self._iter_option_items():
            item.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)
        for cleaner_id in self._cleaner_items:
            self._sync_cleaner_state(cleaner_id)

    def _collect_operations(self):
        operations = {}
        for cleaner_id, option_id, item in self._iter_option_items():
            if item.checkState(0) != Qt.Checked:
                continue
            operations.setdefault(cleaner_id, []).append(option_id)
        return operations

    def _set_running(self, running: bool):
        self._running = running
        self.btn_select_all.setEnabled(not running)
        self.btn_clear.setEnabled(not running)
        self.btn_preview.setEnabled(not running)
        self.btn_clean.setEnabled(not running)
        self.tree.setEnabled(not running)

    def append_log(self, text: str):
        text = text.rstrip("\n")
        if not text:
            return
        self.log.append(text)

    def _set_status(self, text: str):
        self.status_label.setText(text)
        self.status_label.setAccessibleDescription(text)

    def update_progress(self, status):
        if isinstance(status, (int, float)):
            pct = max(0, min(100, int(status * 100)))
            self.progress.setValue(pct)
            self._set_status(self._t("Progress: %d%%", "Postęp: %d%%") % pct)
            # Add periodic textual updates to improve screen reader feedback.
            if pct >= self._progress_last_announced + 10:
                self._progress_last_announced = pct
                self.append_log(self._t("Progress: %d%%", "Postęp: %d%%") % pct)
            return
        if isinstance(status, str):
            self._set_status(status)
            self.append_log(status)

    def update_total_size(self, size):
        self._set_status(self._t("Recovered: %s", "Odzyskano: %s") % size)

    def update_item_size(self, operation, option_id, size):
        if option_id == -1:
            return
        if size:
            self.append_log(
                self._t(
                    "Item %s.%s: %s bytes",
                    "Element %s.%s: %s bajtów",
                ) % (operation, option_id, size)
            )

    def _show_about(self):
        QMessageBox.information(
            self,
            self._t("About", "O programie"),
            self._t(
                "BleachBit Qt frontend for Windows accessibility.",
                "Frontend Qt BleachBit dla dostępności na Windows.",
            ),
        )

    def _run_worker(self, really_clean: bool):
        if self._running:
            return

        operations = self._collect_operations()
        if not operations:
            QMessageBox.warning(
                self,
                self._t("No operations selected", "Nie wybrano operacji"),
                self._t("Select at least one cleaner option.",
                        "Wybierz przynajmniej jedną opcję czyszczenia."),
            )
            return

        self.log.clear()
        self.progress.setValue(0)
        self._progress_last_announced = -10
        self._set_running(True)
        mode = self._t("Cleaning", "Czyszczenie") if really_clean else self._t("Preview", "Podgląd")
        self.append_log(f"{mode}...")
        self._set_status(f"{mode}...")

        cb = _QtCallback(self)
        worker_iter = Worker.Worker(cb, really_clean, operations).run()

        def step():
            try:
                next(worker_iter)
                QTimer.singleShot(0, step)
            except StopIteration:
                self.progress.setValue(100)
                self._set_status(self._t("Done.", "Gotowe."))
                self.append_log(self._t("Done.", "Gotowe."))
                self._set_running(False)
            except Exception as exc:  # pragma: no cover (best effort UI guard)
                self.append_log(str(exc))
                self._set_running(False)
                QMessageBox.critical(
                    self,
                    self._t("Error", "Błąd"),
                    self._t(
                        "An error occurred while running the operation.",
                        "Wystąpił błąd podczas wykonywania operacji.",
                    ),
                )

        QTimer.singleShot(0, step)

    def run(self):
        self.show()
        return QApplication.instance().exec()


def run_qt_gui(auto_exit: bool = False):
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("BleachBit")
    window = BleachbitQt()
    if auto_exit:
        QTimer.singleShot(0, app.quit)
    return window.run()
