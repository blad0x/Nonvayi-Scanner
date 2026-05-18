import math

from PyQt6.QtWidgets import QPushButton, QLabel, QWidget, QProgressBar, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath

import utils.constants as C


# =========================================================
# SMOOTH 60FPS ANIMATED BUTTON
# =========================================================
class HzLockedButton(QPushButton):
    def __init__(self, text, base_color, hover_color, pressed_color, parent=None):
        super().__init__(text, parent)
        self.base_rgba    = QColor(base_color)
        self.hover_rgba   = QColor(hover_color)
        self.pressed_rgba = QColor(pressed_color)
        self.current_rgba = QColor(base_color)
        self.target_rgba  = QColor(base_color)

        self.timer = QTimer(self)
        self.timer.setInterval(C.DISPLAY_MS)
        self.timer.timeout.connect(self.interpolate_color)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.update_stylesheet()

    def set_target_color(self, color):
        self.target_rgba = color
        if not self.timer.isActive():
            self.timer.start()

    def interpolate_color(self):
        curr = self.current_rgba
        targ = self.target_rgba

        def approach(c, t):
            step = 18
            if abs(c - t) <= step: return t
            return c + step if c < t else c - step

        r = approach(curr.red(),   targ.red())
        g = approach(curr.green(), targ.green())
        b = approach(curr.blue(),  targ.blue())

        self.current_rgba = QColor(r, g, b)
        self.update_stylesheet()

        if self.current_rgba == self.target_rgba:
            self.timer.stop()

    def update_stylesheet(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_rgba.name()};
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
                color: white;
                border: none;
                padding: 0px 12px;
                text-align: center;
            }}
            QPushButton:disabled {{
                background-color: #22222a;
                color: #555555;
            }}
        """)

    def enterEvent(self, event):
        if self.isEnabled(): self.set_target_color(self.hover_rgba)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled(): self.set_target_color(self.base_rgba)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.set_target_color(self.pressed_rgba)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.set_target_color(self.hover_rgba)
        super().mouseReleaseEvent(event)


# =========================================================
# SMOOTH ANIMATED GRADIENT TITLE LABEL
# =========================================================
class GradientLabel(QLabel):
    def __init__(self, text, font_size=32, parent=None):
        super().__init__(text, parent)
        self._font_size = font_size
        self.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._time_counter = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(C.DISPLAY_MS)
        self._timer.timeout.connect(self._animate_gradient)
        self._timer.start()

    def _animate_gradient(self):
        self._time_counter += 0.012
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text())
        text_h = fm.height()

        rect   = self.rect()
        x_base = (rect.width() - text_w) // 2
        y_base = fm.ascent() + (rect.height() - text_h) // 2
        w      = text_w if text_w > 0 else 1

        shift = (math.sin(self._time_counter) * 0.4 + math.cos(self._time_counter * 0.7) * 0.3) * w

        grad = QLinearGradient(x_base + shift, 0, x_base + w + shift, 0)
        grad.setSpread(QLinearGradient.Spread.ReflectSpread)
        grad.setColorAt(0.0,  QColor("#3b0764"))
        grad.setColorAt(0.25, QColor("#6d28d9"))
        grad.setColorAt(0.5,  QColor("#a78bfa"))
        grad.setColorAt(0.75, QColor("#5b21b6"))
        grad.setColorAt(1.0,  QColor("#3b0764"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)

        path = QPainterPath()
        path.addText(x_base, y_base, self.font(), self.text())
        painter.drawPath(path)
        painter.end()

    def sizeHint(self):
        fm = self.fontMetrics()
        return fm.boundingRect(self.text()).size() + QSize(4, 8)


# =========================================================
# SIDE SWITCH TOGGLE (PING MODE <-> TLS MODE)
# =========================================================
class SideSwitchToggle(QWidget):
    from PyQt6.QtCore import pyqtSignal
    switched = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tls_active    = True
        self._knob_x        = 1.0
        self._target_x      = 1.0

        self._ping_color    = QColor("#10b981")
        self._tls_color     = QColor("#7c3aed")
        self._current_color = QColor("#7c3aed")
        self._target_color  = QColor("#7c3aed")

        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._timer = QTimer(self)
        self._timer.setInterval(C.DISPLAY_MS)
        self._timer.timeout.connect(self._animate)

    def is_tls(self):
        return self._tls_active

    def set_tls(self, value: bool):
        self._tls_active  = value
        self._target_x    = 1.0 if value else 0.0
        self._target_color = self._tls_color if value else self._ping_color
        if not self._timer.isActive():
            self._timer.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._tls_active   = not self._tls_active
            self._target_x     = 1.0 if self._tls_active else 0.0
            self._target_color = self._tls_color if self._tls_active else self._ping_color
            if not self._timer.isActive():
                self._timer.start()
            self.switched.emit(self._tls_active)
        super().mousePressEvent(event)

    def _animate(self):
        step_x = 0.07
        diff_x = self._target_x - self._knob_x
        if abs(diff_x) <= step_x:
            self._knob_x = self._target_x
        else:
            self._knob_x += step_x if diff_x > 0 else -step_x

        step_c = 14
        def approach(c, t):
            if abs(c - t) <= step_c: return t
            return c + step_c if c < t else c - step_c

        r = approach(self._current_color.red(),   self._target_color.red())
        g = approach(self._current_color.green(), self._target_color.green())
        b = approach(self._current_color.blue(),  self._target_color.blue())
        self._current_color = QColor(r, g, b)

        self.update()
        if self._knob_x == self._target_x and self._current_color == self._target_color:
            self._timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w   = self.width()
        h   = self.height()
        pad = 4

        track_color  = QColor("#16161a")
        border_color = QColor("#2a2a35")
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, h // 2, h // 2)

        knob_w      = w // 2 - pad
        knob_h      = h - pad * 2
        knob_travel = w - pad * 2 - knob_w
        knob_x      = int(pad + self._knob_x * knob_travel)
        knob_y      = pad
        radius      = knob_h // 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._current_color)
        painter.drawRoundedRect(knob_x, knob_y, knob_w, knob_h, radius, radius)

        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        half = w // 2

        ping_alpha = int(255 * (1.0 - self._knob_x) * 0.9 + 60)
        ping_color = QColor(255, 255, 255, min(255, ping_alpha + 120))
        painter.setPen(ping_color)
        painter.drawText(0, 0, half, h, Qt.AlignmentFlag.AlignCenter, "PING")

        tls_alpha = int(255 * self._knob_x * 0.9 + 60)
        tls_color = QColor(255, 255, 255, min(255, tls_alpha + 120))
        painter.setPen(tls_color)
        painter.drawText(half, 0, half, h, Qt.AlignmentFlag.AlignCenter, "TLS")
        painter.end()


# =========================================================
# SMOOTH INDETERMINATE PROGRESS BAR
# =========================================================
class SmoothProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(False)
        self._height = 8
        self.setFixedHeight(self._height)

        self._animation_pos  = 0.0
        self._timer          = QTimer(self)
        self._timer.setInterval(C.DISPLAY_MS)
        self._timer.timeout.connect(self._update_animation)

        self._speed        = 3.6 * (C.DISPLAY_HZ / 60.0)
        self._window_ratio = 0.28

    def start_animation(self):
        self._animation_pos = 0.0
        self._timer.start()

    def stop_animation(self):
        self._timer.stop()
        self._animation_pos = 0.0
        self.setValue(0)
        self.update()

    def _update_animation(self):
        rect      = self.rect()
        total_w   = max(1, rect.width())
        window_w  = max(6, int(total_w * self._window_ratio))
        cycle_len = total_w + window_w
        self._animation_pos = (self._animation_pos + self._speed) % cycle_len
        leading_pct = (self._animation_pos / cycle_len) * 100.0
        self.setValue(int(leading_pct))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect   = self.rect()
        radius = rect.height() // 2

        border_color = QColor("#27272b")
        bg_color     = QColor("#131316")
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), radius, radius)

        total_w  = max(1, rect.width())
        window_w = max(6, int(total_w * self._window_ratio))

        x_pos      = int(self._animation_pos) - window_w
        chunk_x    = rect.x() + x_pos
        chunk_rect = QRect(chunk_x, rect.y(), window_w, rect.height())

        visible_chunk = chunk_rect.intersected(rect)
        if visible_chunk.width() > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#a855f7")))
            painter.drawRoundedRect(visible_chunk, radius, radius)
