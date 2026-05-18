# utils/resource_path.py

import sys
import os


def resource_path(relative_path):
    """
    Works in:
    - Development
    - PyInstaller onefile
    - PyInstaller onedir
    """

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, "assets", relative_path)