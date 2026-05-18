STYLESHEET = """
QMainWindow { background-color: #09090b; }
QLabel { color: #fafafa; }
QLabel#SubTitle { color: #71717a; }

/* Control Panel Card */
QFrame#ControlsCard {
    background-color: #121216;
    border-radius: 16px;
}

/* Stylish Dropdowns */
QComboBox {
    background-color: #16161a;
    border: 1px solid #222227;
    border-radius: 8px;
    color: #fafafa;
    padding: 6px 12px;
    font-weight: bold;
    font-size: 13px;
    outline: none;
}
QComboBox:focus {
    outline: none;
}
QComboBox:hover {
    border: 1px solid #7c3aed;
    background-color: #1c1c24;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox QAbstractItemView {
    background-color: #121216;
    border: 1px solid #7c3aed;
    border-radius: 8px;
    selection-background-color: #7c3aed;
    selection-color: white;
    color: #fafafa;
    padding: 5px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    border: none;
    outline: none;
}
QComboBox QAbstractItemView::item:focus {
    outline: none;
    border: none;
}

/* Progress Bar - Sleek & Modernized */
QProgressBar {
    background-color: transparent;
    border: none;
}

/* Output Console */
QFrame#ConsoleCard {
    background-color: #030303;
    border: 1px solid #1a1a22;
    border-radius: 16px;
}
QPlainTextEdit {
    background-color: transparent;
    border: none;
    color: #fafafa;
}

/* Purple Scrollbar */
QScrollBar:vertical {
    border: none;
    background: #0a0a0c;
    width: 10px;
    margin: 4px 0 4px 0;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #7c3aed;
    min-height: 25px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: #8b5cf6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""
