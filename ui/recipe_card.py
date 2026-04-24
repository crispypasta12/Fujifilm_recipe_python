"""Recipe card renderer — paint a shareable 900×540 recipe card into a QPixmap.

Layout
------
Left  400 px : sample photo (centre-cropped), or a dark gradient placeholder.
Right 500 px : film-sim badge · recipe title · 13-row params table · branding.

Public API
----------
    generate_recipe_card(recipe: Recipe) -> QPixmap
"""

from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)

from profile.enums import (
    DynRangeLabels,
    FilmSim,
    FilmSimLabels,
    GrainEffectLabels,
    SIM_COLORS,
    WBModeLabels,
)
from recipes.loader import Recipe

# ---------------------------------------------------------------------------
# Card geometry
# ---------------------------------------------------------------------------

CARD_W = 900
CARD_H = 540
IMG_W  = 400   # left photo column width
PAD    = 20    # horizontal padding inside the right panel

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

_BG        = QColor("#18181b")   # overall background / fill
_PANEL_BG  = QColor("#1f1f23")   # right panel background
_DIVIDER   = QColor("#2e2e34")   # subtle hairline dividers
_TEXT      = QColor("#f0f0f0")   # primary text
_TEXT_DIM  = QColor("#888894")   # secondary / dim text
_PARAM_LBL = QColor("#9898a8")   # parameter label
_PARAM_VAL = QColor("#e8e8f0")   # parameter value
_BADGE_BG  = QColor("#2e2e3a")   # film-sim badge background

# Per-simulation accent colours — built from the shared SIM_COLORS hex dict.
_SIM_ACCENT: dict[int, QColor] = {k: QColor(v) for k, v in SIM_COLORS.items()}
_ACCENT_DEFAULT = QColor("#888888")

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_OWS = {0: "Off", 1: "Weak", 2: "Strong"}


def _ows(val: int) -> str:
    return _OWS.get(val, "—")


def _fmt(val) -> str:
    """Signed numeric label; zero is shown without a sign."""
    if isinstance(val, float):
        return "0" if val == 0.0 else f"{val:+.1f}"
    return "0" if val == 0 else f"{val:+d}"


def _font(px: int, bold: bool = False) -> QFont:
    """Return a QFont with an absolute pixel size (DPI-independent for off-screen bitmaps)."""
    f = QFont()
    f.setPixelSize(px)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    return f


def _short_title(title: str) -> str:
    return re.sub(r"\s*[—\-–]+\s*Fujifilm.*", "", title).strip() or title


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recipe_card(recipe: Recipe) -> QPixmap:
    """Render a ``CARD_W × CARD_H`` px recipe card and return it as a QPixmap."""
    pix = QPixmap(CARD_W, CARD_H)
    pix.fill(_BG)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    _draw_left(p, recipe)
    _draw_right(p, recipe)

    p.end()
    return pix


# ---------------------------------------------------------------------------
# Left panel — photo
# ---------------------------------------------------------------------------

def _draw_left(p: QPainter, recipe: Recipe) -> None:
    """Fill the left IMG_W columns with the recipe photo (centre-cropped) or a placeholder."""
    drew_image = False

    if recipe.image_path is not None:
        img_path = Path(recipe.image_path)
        if img_path.exists():
            src = QPixmap(str(img_path))
            if not src.isNull():
                # Scale to fill, then centre-crop
                scaled = src.scaled(
                    IMG_W, CARD_H,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                sx = (scaled.width()  - IMG_W) // 2
                sy = (scaled.height() - CARD_H) // 2
                p.drawPixmap(0, 0, scaled, sx, sy, IMG_W, CARD_H)

                # Soft right-edge fade into the panel
                fade = QLinearGradient(IMG_W - 60, 0, IMG_W, 0)
                fade.setColorAt(0.0, QColor(0, 0, 0,   0))
                fade.setColorAt(1.0, QColor(0, 0, 0, 200))
                p.fillRect(IMG_W - 60, 0, 60, CARD_H, QBrush(fade))
                drew_image = True

    if not drew_image:
        # Dark gradient placeholder
        grad = QLinearGradient(0, 0, IMG_W, CARD_H)
        grad.setColorAt(0.0, QColor("#26263a"))
        grad.setColorAt(1.0, QColor("#111116"))
        p.fillRect(0, 0, IMG_W, CARD_H, QBrush(grad))

        p.setPen(_TEXT_DIM)
        p.setFont(_font(13))
        p.drawText(
            QRect(0, 0, IMG_W, CARD_H),
            Qt.AlignmentFlag.AlignCenter,
            "No image",
        )


# ---------------------------------------------------------------------------
# Right panel — metadata
# ---------------------------------------------------------------------------

def _draw_right(p: QPainter, recipe: Recipe) -> None:
    """Draw the right info panel (film-sim badge, title, params table, branding)."""
    x0 = IMG_W
    w  = CARD_W - IMG_W   # 500 px

    p.fillRect(x0, 0, w, CARD_H, _PANEL_BG)

    v      = recipe.ui_values
    accent = _SIM_ACCENT.get(v.filmSimulation, _ACCENT_DEFAULT)

    # ── Film-sim badge ───────────────────────────────────────────────────────
    badge_font = _font(10, bold=True)
    badge_fm   = QFontMetrics(badge_font)
    badge_text = FilmSimLabels.get(v.filmSimulation, "—").upper()
    badge_w    = badge_fm.horizontalAdvance(badge_text) + 20
    badge_h    = 22
    bx, by     = x0 + PAD, PAD

    p.fillRect(bx,     by, 3,            badge_h, accent)    # accent stripe
    p.fillRect(bx + 3, by, badge_w - 3,  badge_h, _BADGE_BG) # body

    p.setPen(accent)
    p.setFont(badge_font)
    p.drawText(
        QRect(bx + 10, by, badge_w - 10, badge_h),
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        badge_text,
    )

    # ── Recipe title ─────────────────────────────────────────────────────────
    title_font = _font(18, bold=True)
    title_fm   = QFontMetrics(title_font)
    title_y    = by + badge_h + 14
    avail_w    = w - PAD * 2
    title_txt  = title_fm.elidedText(
        _short_title(recipe.title), Qt.TextElideMode.ElideRight, avail_w
    )
    p.setPen(_TEXT)
    p.setFont(title_font)
    p.drawText(
        QRect(x0 + PAD, title_y, avail_w, title_fm.height()),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        title_txt,
    )

    # ── Source label ─────────────────────────────────────────────────────────
    src_font = _font(10)
    src_fm   = QFontMetrics(src_font)
    src_y    = title_y + title_fm.height() + 5
    src_txt  = src_fm.elidedText(recipe.source, Qt.TextElideMode.ElideRight, avail_w)
    p.setPen(_TEXT_DIM)
    p.setFont(src_font)
    p.drawText(
        QRect(x0 + PAD, src_y, avail_w, src_fm.height()),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        src_txt,
    )

    # ── Section divider ───────────────────────────────────────────────────────
    div_y = src_y + src_fm.height() + 12
    p.setPen(QPen(_DIVIDER, 1))
    p.drawLine(x0 + PAD, div_y, x0 + w - PAD, div_y)

    # ── Params table (single column, 13 rows) ────────────────────────────────
    params = [
        ("Film Sim",     FilmSimLabels.get(v.filmSimulation, "—")),
        ("Dyn. Range",   DynRangeLabels.get(v.dynamicRange, "—")),
        ("Grain",        GrainEffectLabels.get(v.grainEffect, "—")),
        ("Color Chrome", _ows(v.colorChrome)),
        ("CC FX Blue",   _ows(v.colorChromeFxBlue)),
        ("White Bal.",   WBModeLabels.get(v.whiteBalance, "—")),
        ("WB Shift R/B", f"{v.wbShiftR:+d} / {v.wbShiftB:+d}"),
        ("Highlight",    _fmt(v.highlightTone)),
        ("Shadow",       _fmt(v.shadowTone)),
        ("Color",        _fmt(v.color)),
        ("Sharpness",    _fmt(v.sharpness)),
        ("Noise Reduc.", _fmt(v.noiseReduction)),
        ("Clarity",      _fmt(v.clarity)),
    ]

    lbl_w    = 110
    val_x    = x0 + PAD + lbl_w + 8
    val_w    = avail_w - lbl_w - 8
    row_h    = 28
    params_y = div_y + 10

    lbl_font = _font(10)
    val_font = _font(11, bold=True)

    for i, (label, value) in enumerate(params):
        ry = params_y + i * row_h

        p.setPen(_PARAM_LBL)
        p.setFont(lbl_font)
        p.drawText(
            QRect(x0 + PAD, ry, lbl_w, row_h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            label,
        )

        p.setPen(_PARAM_VAL)
        p.setFont(val_font)
        p.drawText(
            QRect(val_x, ry, val_w, row_h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            str(value),
        )

    # ── Bottom accent bar ────────────────────────────────────────────────────
    bar_h = 3
    p.fillRect(x0, CARD_H - bar_h, w, bar_h, accent)

    # ── Branding ─────────────────────────────────────────────────────────────
    brand_font = _font(9)
    brand_fm   = QFontMetrics(brand_font)
    brand_y    = CARD_H - bar_h - 4 - brand_fm.height()
    p.setPen(QColor("#404048"))
    p.setFont(brand_font)
    p.drawText(
        QRect(x0 + PAD, brand_y, avail_w, brand_fm.height()),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        "FujiRecipe",
    )
