"""Dark theme stylesheet for FujiRecipe — Visual Overhaul v2.

Colour palette shifted to cool blue-black.  QTabWidget rules removed
(replaced by vertical SlotRail).  TitleBar + window-control rules added.
"""

ACCENT    = '#E8840A'
BG        = '#0e0e14'   # cool blue-black (was #1a1a1a)
PANEL     = '#14141c'   # (was #242424)
PANEL_ALT = '#1c1c28'   # (was #2c2c2c)
BORDER    = '#2a2a3a'   # (was #3a3a3a)
TEXT      = '#e2e2f0'   # slight cool tint (was #e8e8e8)
TEXT_DIM  = '#6a6a82'   # (was #9a9a9a)
DANGER    = '#d94343'
OK        = '#3ab873'

STYLESHEET = f"""
* {{
    font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {TEXT};
}}

QMainWindow {{
    background-color: {BG};
    border: 1px solid {BORDER};
}}

QDialog {{
    background-color: {BG};
}}

/* ── Custom title bar ──────────────────────────────────────────────────── */

QWidget#TitleBar {{
    background-color: {PANEL};
    border-bottom: 1px solid {BORDER};
}}

QLabel#titleLabel {{
    font-size: 11pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: {TEXT};
    background: transparent;
}}

QLabel#titleDot {{
    color: {ACCENT};
    font-size: 9pt;
    background: transparent;
}}

QPushButton#winCtrlBtn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {TEXT_DIM};
    font-size: 12pt;
    padding: 0;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
}}

QPushButton#winCtrlBtn:hover {{
    background: rgba(255, 255, 255, 0.07);
    color: {TEXT};
}}

QPushButton#winCtrlBtn[role="close"]:hover {{
    background: #c0392b;
    color: #ffffff;
}}

/* ── Top toolbar ───────────────────────────────────────────────────────── */

QWidget#TopBar {{
    background-color: {PANEL};
    border-bottom: 1px solid {BORDER};
}}

/* ── Slot rail ─────────────────────────────────────────────────────────── */

QListWidget#SlotRail {{
    background-color: {BG};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
    padding: 6px 0;
}}

QListWidget#SlotRail::item {{
    padding: 0;
    border: none;
    background: transparent;
}}

QListWidget#SlotRail::item:selected {{
    background: transparent;
}}

QListWidget#SlotRail::item:hover {{
    background: transparent;
}}

/* ── Labels ────────────────────────────────────────────────────────────── */

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel[role="heading"] {{
    font-size: 14pt;
    font-weight: 600;
    color: {ACCENT};
}}

/* Slot tag — left accent stripe, updated dynamically per sim colour */
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

QLabel[role="paramLabel"] {{
    color: {TEXT_DIM};
    font-size: 9pt;
}}

QLabel[role="paramValue"] {{
    color: {TEXT};
    font-weight: 600;
}}

QLabel#RecipeImage {{
    background-color: #0a0a10;
    border: 1px solid {BORDER};
    border-radius: 3px;
    color: {TEXT_DIM};
}}

QLabel#RecipeTitle {{
    font-size: 13pt;
    font-weight: 700;
    color: {TEXT};
}}

/* ── Inputs ────────────────────────────────────────────────────────────── */

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
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

/* ── Buttons ───────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
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
    border-radius: 4px;
}}

QPushButton[role="primary"]:hover {{
    background-color: #ff9620;
}}

QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: {BORDER};
    background-color: {BG};
}}

/* ── Status bar ────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {PANEL};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    font-size: 9pt;
}}

/* ── Dividers ──────────────────────────────────────────────────────────── */

QFrame[role="divider"] {{
    background: {BORDER};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

/* ── Connection dot ────────────────────────────────────────────────────── */

QLabel#connDot[state="off"] {{
    color: {DANGER};
}}

QLabel#connDot[state="on"] {{
    color: {OK};
}}

/* ── Group boxes ───────────────────────────────────────────────────────── */

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 18px;
    padding-top: 12px;
    padding-left: 4px;
    padding-right: 4px;
    padding-bottom: 6px;
    background-color: {PANEL};
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

/* ── Scroll areas ──────────────────────────────────────────────────────── */

QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {PANEL};
}}

QScrollBar:vertical {{
    background: {BG};
    width: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

/* ── Recipe list ───────────────────────────────────────────────────────── */

QListWidget#RecipeList {{
    background-color: {BG};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
}}

QListWidget#RecipeList::item {{
    padding: 6px 8px;
    border-bottom: 1px solid #18181f;
    color: {TEXT};
}}

QListWidget#RecipeList::item:selected {{
    background-color: #1e1e2c;
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    padding-left: 5px;
}}

QListWidget#RecipeList::item:hover:!selected {{
    background-color: #18182a;
}}

/* ── File / tool buttons ───────────────────────────────────────────────── */

QToolButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
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
