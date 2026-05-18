from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QFont

from ui.widgets import HzLockedButton


# =========================================================
# BASE DIALOG (fade-in, frameless, dark style)
# =========================================================
class BaseCustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #121216;
                border: 2px solid #7c3aed;
                border-radius: 16px;
            }
            QLabel { color: #fafafa; }
        """)
        self.setWindowOpacity(0.0)
        self.fade_anim = QVariantAnimation(self)
        self.fade_anim.setDuration(180)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.valueChanged.connect(self.setWindowOpacity)

    def showEvent(self, event):
        super().showEvent(event)
        self.fade_anim.start()


# =========================================================
# NUMERIC INPUT DIALOG (CIDR count)
# =========================================================
class CustomInputDialog(BaseCustomDialog):
    def __init__(self, title, label_text, parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(label_text)
        desc_lbl.setFont(QFont("Segoe UI", 11))
        desc_lbl.setStyleSheet("color: #71717a;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        self.entry = QLineEdit()
        self.entry.setText("10000")
        self.entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entry.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.entry.setStyleSheet("""
            QLineEdit {
                background-color: #09090b;
                border: 1px solid #272732;
                border-radius: 8px;
                color: white;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #7c3aed;
            }
        """)
        layout.addWidget(self.entry)

        btn_layout = QHBoxLayout()
        self.btn_cancel  = HzLockedButton("CANCEL",  "#1e1e24", "#2b2b34", "#1a1a22")
        self.btn_confirm = HzLockedButton("CONFIRM", "#7c3aed", "#8b5cf6", "#6d28d9")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_confirm.setMinimumHeight(40)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        self.value = None

    def validate_and_accept(self):
        try:
            val = int(self.entry.text().strip())
            if 1 <= val <= 100000:
                self.value = val
                self.accept()
            else:
                raise ValueError
        except Exception:
            self.entry.setStyleSheet(
                "QLineEdit { background-color: #09090b; border: 1px solid #ef4444; "
                "border-radius: 8px; color: white; padding: 10px; }"
            )


# =========================================================
# OVERWRITE / APPEND DIALOG
# =========================================================
class CustomQuestionDialog(BaseCustomDialog):
    def __init__(self, title, text, parent=None, overwrite_only=False):
        super().__init__(parent)
        self.setFixedSize(440, 220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(text)
        desc_lbl.setFont(QFont("Segoe UI", 11))
        desc_lbl.setStyleSheet("color: #71717a;")
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        btn_layout = QHBoxLayout()
        self.btn_overwrite = HzLockedButton("OVERWRITE FRESH", "#be123c", "#f43f5e", "#9f1239")
        self.btn_overwrite.setMinimumHeight(40)
        self.btn_overwrite.clicked.connect(self.choose_overwrite)

        if not overwrite_only:
            self.btn_append = HzLockedButton("APPEND SAFELY", "#7c3aed", "#8b5cf6", "#6d28d9")
            self.btn_append.setMinimumHeight(40)
            self.btn_append.clicked.connect(self.choose_append)
            btn_layout.addWidget(self.btn_append)

        btn_layout.addWidget(self.btn_overwrite)
        layout.addLayout(btn_layout)
        self.overwrite = None

    def choose_append(self):
        self.overwrite = False
        self.accept()

    def choose_overwrite(self):
        self.overwrite = True
        self.accept()
