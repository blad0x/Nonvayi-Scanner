import os
import time
import asyncio
import subprocess
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPlainTextEdit, QFileDialog, QFrame, QMenu, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QAction

import utils.constants as C
from utils.resource_path import resource_path
from utils.file_utils import read_ips_from_file

from ui.widgets import HzLockedButton, GradientLabel, SideSwitchToggle, SmoothProgressBar
from ui.dialogs import CustomInputDialog, CustomQuestionDialog
from core.cidr_worker import CIDRWorker
from core.scan_worker import ScanWorker


class NonvayiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nonvayi  ·  blad0x")
        self.resize(1100, 800)
        self.setMinimumSize(950, 700)

        self.stop_event      = threading.Event()
        self.worker          = None
        self.cidr_worker     = None
        self.alive_count     = 0
        self.dead_count      = 0
        self.sound_enabled   = False
        self.tls_enabled     = True
        self.current_log_file = None
        self.last_sound_time = 0.0

        self.init_ui()

    # ─── UI BUILD ─────────────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 20)
        main_layout.setSpacing(15)

        # Header
        header   = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        title = GradientLabel("NONVAYI", font_size=36)
        sub   = QLabel("CDN Fronting Scanner")
        sub.setObjectName("SubTitle")
        sub.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        main_layout.addWidget(header)

        # Controls card
        card        = QFrame()
        card.setObjectName("ControlsCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(25, 20, 25, 20)
        card_layout.setSpacing(15)

        def _sub_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("SubTitle")
            lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #52525b; letter-spacing: 1px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            return lbl

        self.preset_combo = QComboBox()
        self.preset_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_combo.addItems(["Safe (30 Tasks)", "Standard (100 Tasks)", "Turbo (350 Tasks)"])
        self.preset_combo.setCurrentText("Standard (100 Tasks)")

        self.ping_combo = QComboBox()
        self.ping_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ping_combo.addItems(["2", "4", "6", "8", "10", "13.5", "16", "20"])
        self.ping_combo.setCurrentText("13.5")

        self.tls_switch = SideSwitchToggle()
        self.tls_switch.set_tls(True)
        self.tls_switch.switched.connect(self._on_switch)

        card_layout.addWidget(_sub_label("WORKER PRESET"),  0, 0)
        card_layout.addWidget(self.preset_combo,            1, 0)
        card_layout.addWidget(_sub_label("CONNECT TIMEOUT"), 0, 1)
        card_layout.addWidget(self.ping_combo,              1, 1)
        card_layout.addWidget(_sub_label("SCAN ENGINE"),    0, 2)
        card_layout.addWidget(self.tls_switch,              1, 2)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_std   = HzLockedButton("LOAD IP LIST", "#1e1e24", "#2b2b34", "#1a1a22")
        self.btn_range = HzLockedButton("LOAD CIDR",    "#7c3aed", "#8b5cf6", "#6d28d9")
        self.btn_stop  = HzLockedButton("■  STOP",      "#be123c", "#f43f5e", "#9f1239")

        for btn in (self.btn_std, self.btn_range, self.btn_stop):
            btn.setMinimumHeight(40)

        self.btn_std.clicked.connect(lambda: self.start_process("direct"))
        self.btn_range.clicked.connect(lambda: self.start_process("range"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)

        btn_layout.addWidget(self.btn_std)
        btn_layout.addWidget(self.btn_range)
        btn_layout.addWidget(self.btn_stop)
        card_layout.addLayout(btn_layout, 1, 3)

        card_layout.setColumnStretch(0, 2)
        card_layout.setColumnStretch(1, 2)
        card_layout.setColumnStretch(2, 2)
        card_layout.setColumnStretch(3, 3)
        main_layout.addWidget(card)

        # Stats row
        stats        = QWidget()
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(0, 5, 0, 0)

        self.lbl_targets = QLabel("QUEUE  ·  0")
        self.lbl_targets.setObjectName("SubTitle")
        self.lbl_targets.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        self.lbl_alive = QLabel("● ALIVE  0")
        self.lbl_alive.setStyleSheet("color: #10b981;")
        self.lbl_alive.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        self.lbl_dead = QLabel("○ DEAD  0")
        self.lbl_dead.setStyleSheet("color: #ef4444;")
        self.lbl_dead.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        stats_layout.addWidget(self.lbl_targets)
        stats_layout.addSpacing(35)
        stats_layout.addWidget(self.lbl_alive)
        stats_layout.addSpacing(25)
        stats_layout.addWidget(self.lbl_dead)
        stats_layout.addStretch()
        main_layout.addWidget(stats)

        # Progress bar
        pb_layout = QHBoxLayout()
        pb_layout.setContentsMargins(10, 0, 10, 0)
        self.progress = SmoothProgressBar()
        pb_layout.addWidget(self.progress)
        main_layout.addLayout(pb_layout)

        # Console card
        console_frame = QFrame()
        console_frame.setObjectName("ConsoleCard")
        cf_layout = QVBoxLayout(console_frame)
        cf_layout.setContentsMargins(15, 10, 15, 15)

        top_bar   = QWidget()
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(5, 0, 5, 5)

        feed_lbl = QLabel("LIVE  OUTPUT")
        feed_lbl.setObjectName("SubTitle")
        feed_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.btn_sound = HzLockedButton("AUDIO  OFF", "#18181c", "#22222a", "#0a0a0c")
        self.btn_sound.setFixedSize(95, 24)
        self.btn_sound.clicked.connect(self.toggle_sound)

        tb_layout.addWidget(feed_lbl)
        tb_layout.addStretch()
        tb_layout.addWidget(self.btn_sound)
        cf_layout.addWidget(top_bar)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.console.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.console.customContextMenuRequested.connect(self.show_context_menu)
        cf_layout.addWidget(self.console)

        main_layout.addWidget(console_frame, stretch=1)

        # Status footer
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setObjectName("SubTitle")
        main_layout.addWidget(self.lbl_status)

    # ─── CONTEXT MENU ─────────────────────────────────────
    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #121216;
                color: white;
                border: 1px solid #272732;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c3aed;
            }
        """)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_console_text)
        menu.addAction(copy_action)
        menu.exec(self.console.mapToGlobal(pos))

    def copy_console_text(self):
        cursor = self.console.textCursor()
        if not cursor.hasSelection():
            self.console.selectAll()
            self.console.copy()
            cursor.clearSelection()
            self.console.setTextCursor(cursor)
        else:
            self.console.copy()

    # ─── TOGGLE / SOUND ───────────────────────────────────
    def _on_switch(self, tls_active: bool):
        self.tls_enabled = tls_active

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.btn_sound.setText("AUDIO  ON")
            self.btn_sound.base_rgba    = QColor("#7c3aed")
            self.btn_sound.hover_rgba   = QColor("#8b5cf6")
            self.btn_sound.pressed_rgba = QColor("#6d28d9")
        else:
            self.btn_sound.setText("AUDIO  OFF")
            self.btn_sound.base_rgba    = QColor("#18181c")
            self.btn_sound.hover_rgba   = QColor("#22222a")
            self.btn_sound.pressed_rgba = QColor("#0a0a0c")
        self.btn_sound.set_target_color(self.btn_sound.base_rgba)

    def play_sound(self):
        if not self.sound_enabled:
            return
        current_time = time.time()
        if current_time - self.last_sound_time >= 5.0:
            self.last_sound_time = current_time
            try:
                wav_path = resource_path("notification.wav")
                if os.name == 'nt':
                    import winsound
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    subprocess.Popen(['aplay', '-q', wav_path], stderr=subprocess.DEVNULL)
            except Exception:
                pass

    # ─── LOGGING ──────────────────────────────────────────
    def append_log(self, msg, color):
        ft       = time.strftime('%H:%M:%S')
        html_msg = f"<span style='color: {color};'>[{ft}] {msg}</span>"
        self.console.appendHtml(html_msg)

        doc        = self.console.document()
        MAX_BLOCKS = 3000
        TRIM_TO    = 2000
        if doc.blockCount() > MAX_BLOCKS:
            cursor = self.console.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(
                cursor.MoveOperation.Down,
                cursor.MoveMode.KeepAnchor,
                doc.blockCount() - TRIM_TO,
            )
            cursor.removeSelectedText()

        sb = self.console.verticalScrollBar()
        if sb.value() >= sb.maximum() - 30:
            sb.setValue(sb.maximum())

        if self.current_log_file and color == "#10b981":
            try:
                if os.path.getsize(self.current_log_file) < C.MAX_LOG_FILE_SIZE_BYTES:
                    with open(self.current_log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{ft}] [SUCCESS] {msg}\n")
            except OSError:
                pass

    # ─── STATS ────────────────────────────────────────────
    def update_stats(self, is_alive):
        if is_alive:
            self.alive_count += 1
            self.lbl_alive.setText(f"● ALIVE  {self.alive_count}")
            self.play_sound()
        else:
            self.dead_count += 1
            self.lbl_dead.setText(f"○ DEAD  {self.dead_count}")
        total = self.alive_count + self.dead_count
        if hasattr(self, "_total_targets") and self._total_targets > 0:
            pct = min(100, int(total / self._total_targets * 100))
            self.lbl_status.setText(f"Scanning...  Processed: {total} / {self._total_targets}  [{pct}%]")
        else:
            self.lbl_status.setText(f"Scanning...  Processed: {total}")

    # ─── SCAN CONTROL ─────────────────────────────────────
    def stop_scan(self):
        self.stop_event.set()
        self.lbl_status.setText("Stopping...")
        self.append_log("  Halt signal sent — draining active workers...", "#f59e0b")
        self.btn_stop.setEnabled(False)

        if self.worker and self.worker.isRunning():
            try:
                def kill_tasks():
                    for t in asyncio.all_tasks(self.worker.loop):
                        t.cancel()
                if self.worker.loop and self.worker.loop.is_running():
                    self.worker.loop.call_soon_threadsafe(kill_tasks)
            except Exception:
                pass

        if self.cidr_worker and self.cidr_worker.isRunning():
            try:
                self.cidr_worker.requestInterruption()
            except Exception:
                pass

    def start_process(self, mode):
        fp, _ = QFileDialog.getOpenFileName(self, "Open Node Source List", "", "Text Files (*.txt)")
        if not fp:
            return

        self.stop_event.clear()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(C.LOG_DIR, f"scan_log_{ts}.txt")
        try:
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                f.write(f"--- Session Init: {ts} ---\n")
        except Exception:
            pass

        if mode == "range":
            dial = CustomInputDialog("Target Pool Constraints", "Specify generation pool criteria (1 - 100,000):", self)
            if not dial.exec():
                return
            count = dial.value
            if count is None:
                return

            ow = True
            if os.path.exists(C.EXPANDED_IPS_FILE):
                current_size = os.path.getsize(C.EXPANDED_IPS_FILE)
                if current_size >= C.MAX_EXPANDED_FILE_SIZE:
                    size_mb = current_size / (1024 * 1024)
                    q_dial  = CustomQuestionDialog(
                        "File Size Limit Reached",
                        f"expanded_ips.txt is {size_mb:.1f} MB (limit: 30 MB).\nYou must overwrite to continue.",
                        self,
                        overwrite_only=True,
                    )
                    if not q_dial.exec():
                        return
                    ow = True
                else:
                    q_dial = CustomQuestionDialog(
                        "Collision Detected",
                        "Target file database exists. Overwrite or Append?",
                        self,
                    )
                    if not q_dial.exec():
                        return
                    ow = q_dial.overwrite

            self.lbl_status.setText("Expanding CIDR ranges...")
            self.progress.start_animation()

            self.cidr_worker = CIDRWorker(fp, count, ow)
            self.cidr_worker.log_signal.connect(self.append_log)
            self.cidr_worker.error_signal.connect(lambda err: QMessageBox.critical(self, "Error", err))
            self.cidr_worker.finished_signal.connect(self.launch_worker)
            self.cidr_worker.start()
            return

        self.launch_worker(fp)

    def launch_worker(self, fp=None):
        preset  = self.preset_combo.currentText()
        workers = 30 if "Safe" in preset else 350 if "Turbo" in preset else 100
        ping_t  = float(self.ping_combo.currentText())

        self.btn_std.setEnabled(False)
        self.btn_range.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.console.clear()
        self.alive_count    = 0
        self.dead_count     = 0
        self._total_targets = 0
        self.lbl_alive.setText("● ALIVE  0")
        self.lbl_dead.setText("○ DEAD  0")
        self.lbl_targets.setText("QUEUE  ·  0")

        self.progress.start_animation()
        self.lbl_status.setText("Initialising scanner...")

        self.worker = ScanWorker(workers, fp, ping_t, self.tls_enabled, self.stop_event, self.current_log_file)
        self.worker.log_signal.connect(self.append_log)
        self.worker.stat_signal.connect(self.update_stats)

        def _on_targets(t):
            self._total_targets = t
            self.lbl_targets.setText(f"QUEUE  ·  {t}")

        self.worker.targets_signal.connect(_on_targets)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, natural_finish):
        self.btn_std.setEnabled(True)
        self.btn_range.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.stop_animation()
        total = self.alive_count + self.dead_count
        if natural_finish:
            self.append_log(
                f"  Scan complete  ›  {self.alive_count} live nodes found out of {total} scanned.",
                "#f59e0b",
            )
            self.lbl_status.setText(f"Done — {self.alive_count} alive out of {total} scanned")
        else:
            self.lbl_status.setText(f"Stopped — {self.alive_count} alive out of {total} scanned")

    def closeEvent(self, event):
        if (self.worker and self.worker.isRunning()) or \
           (self.cidr_worker and self.cidr_worker.isRunning()):
            self.stop_scan()
        event.accept()
