"""Dark theme stylesheet for FujiRecipe — Visual Overhaul v4.

Single source of truth: every hex code in the app routes through PALETTE.
Other UI modules (main_window, recipe_browser, preset_panel) import PALETTE
rather than hard-coding hex values inline.

macOS sizing pass: bumped base font to 13pt, increased control heights,
padding, and touch targets throughout for Retina / native macOS feel.
"""

from typing import Final
import sys

IS_MAC = sys.platform == "darwin"


# ---------------------------------------------------------------------------
# Token palette
# ---------------------------------------------------------------------------

PALETTE: Final[dict[str, str]] = {
    # Brand
    'accent':         '#F2A23A',
    'accentHover':    '#ffb85c',
    'onAccent':       '#000000',

    # Surfaces — deeper contrast ramp for layered glass feel
    'bg':             '#0b0b10',   # absolute floor — window/rail backgrounds
    'bgDeep':         '#070709',   # deepest shade — image placeholder bg
    'panel':          '#191926',   # card surface — group boxes, panels
    'panelAlt':       '#1f2030',   # control background — inputs, combos
    'panelRaised':    '#232337',   # elevated elements — toasts, menus

    # Borders / hairlines
    'border':         '#26263e',
    'borderSoft':     '#151520',

    # Text
    'text':           '#e2e2f0',
    'textBright':     '#c4c4d8',
    'textDim':        '#6a6a82',
    'textMute':       '#5a5a72',

    # Status
    'danger':         '#d94343',
    'dangerHover':    '#c0392b',
    'ok':             '#3ab873',
    'white':          '#ffffff',

    # Slot rail states
    'slotSel':        '#1e1e30',
    'slotHover':      '#161626',
    'slotSep':        '#1a1a28',

    # Recipe list row states
    'rowSel':         '#212138',
    'rowHover':       '#1c1c2e',

    # Section headers
    'sectionHdr':     '#888894',
    'sectionHdrBg':   '#16162a',

    # Swatches / fallbacks
    'swatchFallback': '#444450',
    'simDefault':     '#666670',

    # Value pills (recipe-browser detail)
    'pillBg':         '#1e1e30',
    'pillBorder':     '#2a2a42',
    'pillText':       '#f0f0fa',
}


PALETTE.update({
    'bg': '#11100e',
    'bgDeep': '#090908',
    'panel': '#1d1b18',
    'panelAlt': '#28241f',
    'panelRaised': '#302b25',
    'border': '#373126',
    'borderSoft': '#211e19',
    'text': '#f0ece4',
    'textBright': '#d8d0c4',
    'textDim': '#91887a',
    'textMute': '#70685f',
    'slotSel': '#2a251f',
    'slotHover': '#211e1a',
    'slotSep': '#242019',
    'rowSel': '#332b22',
    'rowHover': '#26221d',
    'sectionHdr': '#91887a',
    'sectionHdrBg': '#211d18',
    'swatchFallback': '#524b43',
    'simDefault': '#8a8176',
    'pillBg': '#28231d',
    'pillBorder': '#3a3228',
    'pillText': '#fff7ec',
})


# ---------------------------------------------------------------------------
# Back-compat module-level shortcuts
# ---------------------------------------------------------------------------

ACCENT    = PALETTE['accent']
BG        = PALETTE['bg']
PANEL     = PALETTE['panel']
PANEL_ALT = PALETTE['panelAlt']
BORDER    = PALETTE['border']
TEXT      = PALETTE['text']
TEXT_DIM  = PALETTE['textDim']
DANGER    = PALETTE['danger']
OK        = PALETTE['ok']

P = PALETTE  # local shortcut for stylesheet f-string

MONO_FONT = '"JetBrains Mono", "Cascadia Mono", "Consolas", "Menlo", monospace'

# ---------------------------------------------------------------------------
# macOS-aware size tokens
# On macOS, Qt renders at logical pixels on Retina so we need larger pt sizes
# and taller controls compared to Windows.
# ---------------------------------------------------------------------------
if IS_MAC:
    BASE_PT       = 13    # was 10
    SMALL_PT      = 11    # was 9
    HEADING_PT    = 17    # was 14
    SLOT_TAG_PT   = 18    # was 15
    RECIPE_TTL_PT = 22    # was 18
    TITLE_PT      = 13    # was 11
    DOT_PT        = 11    # was 9
    WIN_BTN_W     = 40    # was 32
    WIN_BTN_H     = 34    # was 28
    WIN_BTN_PT    = 14    # was 12
    CTRL_HEIGHT   = 30    # was 24  (min-height for inputs)
    BTN_PAD       = "9px 18px"  # was "7px 14px"
    GROUP_TOP     = 22    # was 18
    GROUP_PAD_TOP = 18    # was 14
    PILL_PAD      = "4px 12px"  # was "3px 10px"
    BADGE_RADIUS  = 13    # was 11
    BADGE_PT      = 9     # was 8
    GROUP_TITLE_PT= 9     # was 8
    SCROLL_W      = 7     # was 5
else:
    BASE_PT       = 10
    SMALL_PT      = 9
    HEADING_PT    = 14
    SLOT_TAG_PT   = 15
    RECIPE_TTL_PT = 18
    TITLE_PT      = 11
    DOT_PT        = 9
    WIN_BTN_W     = 32
    WIN_BTN_H     = 28
    WIN_BTN_PT    = 12
    CTRL_HEIGHT   = 24
    BTN_PAD       = "7px 14px"
    PILL_PAD      = "3px 10px"
    BADGE_RADIUS  = 11
    BADGE_PT      = 8
    GROUP_TITLE_PT= 8
    GROUP_TOP     = 18
    GROUP_PAD_TOP = 14
    SCROLL_W      = 5

STYLESHEET = f"""
* {{
    font-family: "Inter", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    font-size: {BASE_PT}pt;
    color: {P['text']};
    font-weight: 500;
}}

/* ── Exclude native file/folder dialogs from custom styling (macOS fix) ── */

QFileDialog * {{
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 13pt;
    color: initial;
    background-color: initial;
    border: initial;
    padding: initial;
    font-weight: initial;
}}

QMainWindow {{
    background-color: {P['bg']};
    border: 1px solid {P['border']};
}}

QDialog {{
    background-color: {P['bg']};
}}

/* ── Custom title bar ──────────────────────────────────────────────────── */

QWidget#TitleBar {{
    background-color: {P['panel']};
    border-bottom: 1px solid {P['border']};
}}

QLabel#titleLabel {{
    font-size: {TITLE_PT}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: {P['text']};
    background: transparent;
}}

QLabel#titleDot {{
    color: {P['accent']};
    font-size: {DOT_PT}pt;
    background: transparent;
}}

QPushButton#winCtrlBtn {{
    background: transparent;
    border: none;
    border-radius: 5px;
    color: {P['textDim']};
    font-size: {WIN_BTN_PT}pt;
    font-weight: 500;
    padding: 0;
    min-width: {WIN_BTN_W}px;
    max-width: {WIN_BTN_W}px;
    min-height: {WIN_BTN_H}px;
    max-height: {WIN_BTN_H}px;
}}

QPushButton#winCtrlBtn:hover {{
    background: rgba(255, 255, 255, 0.07);
    color: {P['text']};
}}

QPushButton#winCtrlBtn[role="close"]:hover {{
    background: {P['dangerHover']};
    color: {P['white']};
}}

/* ── Top toolbar ───────────────────────────────────────────────────────── */

QWidget#TopBar {{
    background-color: {P['panel']};
    border-bottom: 1px solid {P['border']};
}}

QWidget#PresetHeader {{
    background-color: {P['panelRaised']};
    border: 1px solid {P['border']};
    border-radius: 8px;
}}

/* ── Slot rail ─────────────────────────────────────────────────────────── */

QListWidget#SlotRail {{
    background-color: {P['bg']};
    border: none;
    border-right: 1px solid {P['border']};
    outline: none;
    padding: 8px 0;
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
    color: {P['text']};
    background: transparent;
    font-weight: 500;
}}

QLabel[role="heading"] {{
    font-size: {HEADING_PT}pt;
    font-weight: 600;
    color: {P['accent']};
}}

QLabel[role="slotTag"] {{
    font-size: {SLOT_TAG_PT}pt;
    font-weight: 700;
    color: {P['accent']};
    padding: 2px 10px 2px 16px;
    border: none;
    border-left: 3px solid {P['accent']};
    background: transparent;
}}

QLabel[role="simBadge"] {{
    color: {P['textBright']};
    background-color: {P['panelAlt']};
    border: 1px solid {P['border']};
    border-radius: {BADGE_RADIUS}px;
    padding: 4px 12px;
    font-size: {BADGE_PT}pt;
    font-weight: 800;
    letter-spacing: 0.8px;
}}

QLabel[role="dim"] {{
    color: {P['textDim']};
    font-weight: 500;
}}

QLabel[role="paramLabel"] {{
    color: {P['textDim']};
    font-size: {SMALL_PT}pt;
    font-weight: 500;
    letter-spacing: 0.3px;
}}

QLabel[role="paramValue"] {{
    color: {P['text']};
    font-weight: 600;
}}

QLabel[role="valuePill"] {{
    background-color: {P['pillBg']};
    color: {P['pillText']};
    font-family: {MONO_FONT};
    font-weight: 600;
    font-size: {SMALL_PT}pt;
    padding: {PILL_PAD};
    border: 1px solid {P['pillBorder']};
    border-radius: 10px;
}}

QLabel#RecipeImage {{
    background-color: {P['bgDeep']};
    border: 1px solid {P['border']};
    border-radius: 8px;
    color: {P['textDim']};
}}

QLabel#RecipeTitle {{
    font-size: {RECIPE_TTL_PT}pt;
    font-weight: 700;
    color: {P['text']};
    letter-spacing: 0.2px;
}}

/* ── Inputs ────────────────────────────────────────────────────────────── */

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {P['panelAlt']};
    border: 1px solid {P['border']};
    border-radius: 7px;
    padding: 6px 10px;
    min-height: {CTRL_HEIGHT}px;
    font-weight: 600;
    selection-background-color: {P['accent']};
    selection-color: {P['onAccent']};
}}

/* Accent halo on focus — border + subtle background tint */
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid {P['accent']};
    padding: 5px 9px;
    background-color: rgba(232, 132, 10, 0.06);
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {P['panelRaised']};
    border: 1px solid {P['border']};
    border-radius: 6px;
    selection-background-color: {P['accent']};
    selection-color: {P['onAccent']};
    padding: 4px;
}}

/* ── Buttons ───────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {P['panelAlt']};
    border: 1px solid {P['border']};
    border-radius: 7px;
    padding: {BTN_PAD};
    color: {P['text']};
    font-weight: 600;
}}

QPushButton:hover {{
    border: 1px solid {P['accent']};
    color: {P['accent']};
    background-color: rgba(232, 132, 10, 0.06);
}}

QPushButton:pressed {{
    background-color: {P['bg']};
}}

QPushButton[role="primary"] {{
    background-color: {P['accent']};
    color: {P['onAccent']};
    font-weight: 700;
    border: 1px solid {P['accent']};
    border-radius: 6px;
}}

QPushButton[role="primary"]:hover {{
    background-color: {P['accentHover']};
    color: {P['onAccent']};
}}

QPushButton:disabled {{
    color: {P['textMute']};
    border-color: {P['borderSoft']};
    background-color: {P['bg']};
}}

/* ── Status bar ────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {P['panel']};
    color: {P['textDim']};
    border-top: 1px solid {P['border']};
    font-size: {SMALL_PT}pt;
    font-weight: 500;
}}

/* ── Dividers ──────────────────────────────────────────────────────────── */

QFrame[role="divider"] {{
    background: {P['border']};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

/* ── Connection dot ────────────────────────────────────────────────────── */

QLabel#connDot[state="off"] {{
    color: {P['danger']};
}}

QLabel#connDot[state="connecting"] {{
    color: {P['accent']};
}}

QLabel#connDot[state="on"] {{
    color: {P['ok']};
}}

/* ── Group boxes — card surface with subtle glass overlay ──────────────── */

QGroupBox {{
    border: 1px solid {P['border']};
    border-radius: 8px;
    margin-top: {GROUP_TOP}px;
    padding-top: {GROUP_PAD_TOP}px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 12px;
    background-color: {P['panel']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    color: {P['accent']};
    font-weight: 700;
    font-size: {GROUP_TITLE_PT}pt;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: transparent;
}}

/* ── Scroll areas ──────────────────────────────────────────────────────── */

QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {P['bg']};
}}

QScrollBar:vertical {{
    background: {P['bg']};
    width: {SCROLL_W}px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {P['border']};
    border-radius: 3px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {P['accent']};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

/* ── Recipe list ───────────────────────────────────────────────────────── */

QListWidget#RecipeList {{
    background-color: {P['bg']};
    border: none;
    border-right: 1px solid {P['border']};
    outline: none;
    padding: 10px;
}}

QListWidget#RecipeList::item {{
    padding: 0;
    margin: 4px 0;
    border: none;
    border-radius: 8px;
}}

QListWidget#RecipeList::item:selected {{
    background-color: transparent;
}}

QListWidget#RecipeList::item:hover:!selected {{
    background-color: transparent;
}}

/* ── File / tool buttons ───────────────────────────────────────────────── */

QToolButton {{
    background-color: {P['panelAlt']};
    border: 1px solid {P['border']};
    border-radius: 7px;
    padding: {BTN_PAD};
    color: {P['text']};
    font-weight: 600;
}}

QToolButton::menu-indicator {{
    image: none;
}}

QToolButton:hover {{
    border: 1px solid {P['accent']};
    color: {P['accent']};
    background-color: rgba(232, 132, 10, 0.06);
}}

QToolButton:pressed {{
    background-color: {P['bg']};
}}

QMenu {{
    background-color: {P['panelRaised']};
    border: 1px solid {P['border']};
    border-radius: 8px;
    padding: 4px 4px;
}}

QMenu::item {{
    padding: 6px 20px 6px 12px;
    color: {P['text']};
    font-weight: 500;
    border-radius: 5px;
}}

QMenu::item:selected {{
    background-color: rgba(232, 132, 10, 0.15);
    color: {P['accent']};
}}

QMenu::separator {{
    height: 1px;
    background: {P['border']};
    margin: 4px 0;
}}
"""
