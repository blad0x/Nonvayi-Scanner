import sys
import os
import ctypes

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import utils.constants as C
from utils.resource_path import resource_path
from ui.stylesheet import STYLESHEET
from ui.main_window import NonvayiApp


def _detect_refresh_hz():
    try:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                hz = screen.refreshRate()
                if hz and hz > 0:
                    return int(hz)
    except Exception:
        pass
    return 60


if __name__ == "__main__":
    # Windows: fix taskbar & task manager icon
    if os.name == 'nt':
        myappid = 'blad0x.nonvayi.scanner.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)

    # Detect display refresh rate and update constants module so all widgets pick it up
    C.DISPLAY_HZ = _detect_refresh_hz()
    C.DISPLAY_MS = max(1, int(1000 / C.DISPLAY_HZ))

    # App icon
    app_icon_path = resource_path("icon.ico")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    window = NonvayiApp()
    window.show()
    app.exec()

    os._exit(0)
