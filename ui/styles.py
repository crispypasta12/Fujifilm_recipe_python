"""Dark theme stylesheet for FujiRecipe — Part 4 visual overhaul."""

ACCENT    = '#E8840A'
BG        = '#1a1a1a'
PANEL     = '#242424'
PANEL_ALT = '#2c2c2c'
BORDER    = '#3a3a3a'
TEXT      = '#e8e8e8'
TEXT_DIM  = '#9a9a9a'
DANGER    = '#d94343'
OK        = '#3ab873'

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {TEXT};
}}

QMainWindow, QDialog {{
    background-color: {BG};
}}

QWidget#PresetPanel, QWidget#TopBar, QStatusBar {{
    background-color: {PANEL};
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel[role="heading"] {{
    font-size: 14pt;
    font-weight: 600;
    color: {ACCENT};
}}

/* Slot tag — left accent stripe only, no surrounding box */
QLabel[role="slotTag"] {{
    font-size: 15pt;
    font-weight: 700;
    color: {ACCENT};
    padding: 2px 8px 2px 14px;
    border: none;
    border-left: 3px solid {ACCENT};
    background: transparent;
}}

QLabel[role="dim"] {{
    color: {TEXT_DIM};
}}

/* Recipe browser — param table */
QLabel[role="paramLabel"] {{
    color: {TEXT_DIM};
    font-size: 9pt;
}}

QLabel[role="paramValue"] {{
    color: {TEXT};
    font-weight: 600;
}}

/* Recipe image placeholder in browser */
QLabel#RecipeImage {{
    background-color: #111116;
    border: 1px solid {BORDER};
    border-radius: 3px;
    color: {TEXT_DIM};
}}

/* Recipe title in browser */
QLabel#RecipeTitle {{
    font-size: 13pt;
    font-weight: 700;
    color: {TEXT};
}}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 6px;
    min-height: 18px;
    selection-background-color: {ACCENT};
    selection-color: #000;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #000;
}}

QPushButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 6px 14px;
    color: {TEXT};
}}

QPushButton:hover {{
    border: 1px solid {ACCENT};
    color: {ACCENT};
}}

QPushButton:pressed {{
    background-color: {BG};
}}

QPushButton[role="primary"] {{
    background-color: {ACCENT};
    color: #000;
    font-weight: 600;
    border: 1px solid {ACCENT};
}}

QPushButton[role="primary"]:hover {{
    background-color: #ff9620;
}}

QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: {BORDER};
    background-color: {BG};
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    background-color: {PANEL};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {BG};
    color: {TEXT_DIM};
    padding: 8px 18px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    margin-right: 2px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {PANEL};
    color: {ACCENT};
    border-bottom: 1px solid {PANEL};
}}

QTabBar::tab:hover:!selected {{
    color: {TEXT};
}}

QStatusBar {{
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
}}

QFrame[role="divider"] {{
    background: {BORDER};
    max-height: 1px;
    min-height: 1px;
}}

QLabel#connDot[state="off"] {{
    color: {DANGER};
}}
QLabel#connDot[state="on"] {{
    color: {OK};
}}

/* GroupBox — accent title, stronger visual section */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 18px;
    padding-top: 12px;
    padding-left: 4px;
    padding-right: 4px;
    padding-bottom: 6px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {ACCENT};
    font-weight: 700;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {PANEL};
}}

QScrollBar:vertical {{
    background: {BG};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

/* Recipe list — no border, dark bg, accent selection strip */
QListWidget#RecipeList {{
    background-color: {BG};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
}}

QListWidget#RecipeList::item {{
    padding: 6px 8px;
    border-bottom: 1px solid #202024;
    color: {TEXT};
}}

QListWidget#RecipeList::item:selected {{
    background-color: #252535;
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    padding-left: 5px;
}}

QListWidget#RecipeList::item:hover:!selected {{
    background-color: #1f1f28;
}}

/* File menu tool button — matches regular QPushButton style */
QToolButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 6px 14px;
    color: {TEXT};
}}

QToolButton:hover {{
    border: 1px solid {ACCENT};
    color: {ACCENT};
}}

QToolButton:pressed {{
    background-color: {BG};
}}

QMenu {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    padding: 4px 0;
}}

QMenu::item {{
    padding: 6px 20px 6px 12px;
    color: {TEXT};
}}

QMenu::item:selected {{
    background-color: {ACCENT};
    color: #000;
}}

QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 0;
}}
"""
