"""Load and parse built-in film simulation recipes from scraped JSON files.

Each sensor generation lives in its own subfolder under recipes/builtin/:
    recipes/builtin/x-trans-v/      ← X-Trans V (scraped from fujixweekly.com)
    recipes/builtin/x-trans-iv/     ← add later
    ...

Each recipe JSON has the shape produced by scrape_recipes.py:
    { slug, title, source, image, params: { filmSimulation, dynamicRange, ... } }

The params values are human-readable strings ("Classic Negative", "DR200",
"Weak, Small", "Auto, +1 Red & -2 Blue", …).  This module converts them to the
integer enum values used by PresetUIValues so the rest of the app doesn't need
to know about the text format.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from profile.enums import (
    FilmSim,
    GrainEffect,
    WBMode,
)
from profile.preset_translate import PresetUIValues

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BUILTIN_DIR = Path(__file__).resolve().parent / "builtin"

# Human-readable sensor names shown in the browser UI
SENSOR_LABELS: dict[str, str] = {
    "X-Trans V":  "x-trans-v",
    # "X-Trans IV": "x-trans-iv",   # uncomment once data is scraped
}


# ---------------------------------------------------------------------------
# Public data type
# ---------------------------------------------------------------------------

@dataclass
class Recipe:
    slug: str
    title: str
    source: str
    sensor: str
    image_path: Optional[Path]   # absolute, or None if file is missing
    ui_values: PresetUIValues


# ---------------------------------------------------------------------------
# Text → enum lookup tables
# ---------------------------------------------------------------------------

_FILM_SIM_MAP: dict[str, int] = {
    "provia":                FilmSim.Provia,
    "provia/standard":       FilmSim.Provia,
    "standard":              FilmSim.Provia,
    "velvia":                FilmSim.Velvia,
    "velvia/vivid":          FilmSim.Velvia,
    "vivid":                 FilmSim.Velvia,
    "astia":                 FilmSim.Astia,
    "astia/soft":            FilmSim.Astia,
    "soft":                  FilmSim.Astia,
    "pro neg hi":            FilmSim.ProNegHi,
    "pro neg. hi":           FilmSim.ProNegHi,
    "pro neg std":           FilmSim.ProNegStd,
    "pro neg. std":          FilmSim.ProNegStd,
    "monochrome":            FilmSim.Monochrome,
    "monochrome+ye":         FilmSim.MonochromeYe,
    "monochrome+y":          FilmSim.MonochromeYe,
    "monochrome+yellow":     FilmSim.MonochromeYe,
    "monochrome+r":          FilmSim.MonochromeR,
    "monochrome+red":        FilmSim.MonochromeR,
    "monochrome+g":          FilmSim.MonochromeG,
    "monochrome+green":      FilmSim.MonochromeG,
    "sepia":                 FilmSim.Sepia,
    "classic chrome":        FilmSim.ClassicChrome,
    "acros":                 FilmSim.Acros,
    "acros+ye":              FilmSim.AcrosYe,
    "acros+y":               FilmSim.AcrosYe,
    "acros+yellow":          FilmSim.AcrosYe,
    "acros+r":               FilmSim.AcrosR,
    "acros+red":             FilmSim.AcrosR,
    "acros+g":               FilmSim.AcrosG,
    "acros+green":           FilmSim.AcrosG,
    "eterna":                FilmSim.Eterna,
    "eterna/cinema":         FilmSim.Eterna,
    "eterna cinema":         FilmSim.Eterna,
    "eterna bleach bypass":  FilmSim.EternaBleach,
    "bleach bypass":         FilmSim.EternaBleach,
    "nostalgic neg":         FilmSim.NostalgicNeg,
    "nostalgic neg.":        FilmSim.NostalgicNeg,
    "reala ace":             FilmSim.RealaAce,
    "classic negative":      FilmSim.ClassicNeg,
    "classic neg":           FilmSim.ClassicNeg,
    "classic neg.":          FilmSim.ClassicNeg,
}

_GRAIN_MAP: dict[str, int] = {
    "off":           GrainEffect.Off,
    "weak, small":   GrainEffect.WeakSmall,
    "weak small":    GrainEffect.WeakSmall,
    "weak,small":    GrainEffect.WeakSmall,
    "strong, small": GrainEffect.StrongSmall,
    "strong small":  GrainEffect.StrongSmall,
    "strong,small":  GrainEffect.StrongSmall,
    "weak, large":   GrainEffect.WeakLarge,
    "weak large":    GrainEffect.WeakLarge,
    "weak,large":    GrainEffect.WeakLarge,
    "strong, large": GrainEffect.StrongLarge,
    "strong large":  GrainEffect.StrongLarge,
    "strong,large":  GrainEffect.StrongLarge,
}

_OFF_WEAK_STRONG: dict[str, int] = {"off": 0, "weak": 1, "strong": 2}

_DR_MAP: dict[str, int] = {
    "dr100": 1, "dr100%": 1, "100": 1,
    "dr200": 2, "dr200%": 2, "200": 2,
    "dr400": 3, "dr400%": 3, "400": 3,
}

_DR_PRIORITY_MAP: dict[str, int] = {
    "off": 0, "auto": 1, "weak": 2, "strong": 3,
    "dr-p auto": 1, "dr-p weak": 2, "dr-p strong": 3,
}

_DR_AUTO_FALLBACK = 2   # "DR-Auto" → DR200 as a safe middle ground

_WB_MODE_MAP: dict[str, int] = {
    "auto":               WBMode.Auto,
    "automatic":          WBMode.Auto,
    "daylight":           WBMode.Daylight,
    "shade":              WBMode.Shade,
    "shadow":             WBMode.Shade,
    "incandescent":       WBMode.Incandescent,
    "tungsten":           WBMode.Incandescent,
    "fluorescent 1":      WBMode.Fluorescent1,
    "fluorescent1":       WBMode.Fluorescent1,
    "fluorescent 2":      WBMode.Fluorescent2,
    "fluorescent2":       WBMode.Fluorescent2,
    "fluorescent 3":      WBMode.Fluorescent3,
    "fluorescent3":       WBMode.Fluorescent3,
    "underwater":         WBMode.Underwater,
    "ambience priority":  WBMode.AmbiencePriority,
    "ambience":           WBMode.AmbiencePriority,
    "as shot":            WBMode.AsShot,
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_film_sim(text: str) -> int:
    key = text.strip().lower()
    if key in _FILM_SIM_MAP:
        return _FILM_SIM_MAP[key]
    # try without trailing period
    stripped = key.rstrip(".")
    if stripped in _FILM_SIM_MAP:
        return _FILM_SIM_MAP[stripped]
    # prefix match for truncated strings like "Acros (" or "Nostalgic Neg"
    for k, v in _FILM_SIM_MAP.items():
        if key.startswith(k) or k.startswith(key):
            return v
    return FilmSim.Provia


def _clean_enum_text(text: str) -> str:
    """Strip parenthetical qualifiers and multi-value separators.

    E.g. "Off (X-Trans V); Weak (X-Trans IV)" → "off"
         "Strong (X-Trans V)" → "strong"
    """
    # Take first segment before ';'
    text = text.split(";")[0]
    # Drop anything in parentheses
    text = re.sub(r"\(.*?\)", "", text)
    return text.strip().lower()


def _parse_num(text: str, default: float = 0.0) -> float:
    """Return the first signed number found in text, e.g. '+1', '-2.5', '0'."""
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else default


def _parse_wb(text: str) -> tuple[int, int, int, int]:
    """Parse WB string → (mode, colorTemp_K, shiftR, shiftB)."""
    text = text.strip()

    # Shifts like "+1 Red & -2 Blue"
    shift_r = shift_b = 0
    sm = re.search(
        r"([+-]?\d+)\s*Red\s*[&,]\s*([+-]?\d+)\s*Blue", text, re.IGNORECASE
    )
    if sm:
        shift_r = int(sm.group(1))
        shift_b = int(sm.group(2))

    # Color temperature like "5900K"
    ctm = re.search(r"(\d{4,5})\s*K\b", text)
    if ctm:
        return WBMode.ColorTemp, int(ctm.group(1)), shift_r, shift_b

    # WB mode from text before the first comma
    mode_key = text.split(",")[0].strip().lower()
    mode = _WB_MODE_MAP.get(mode_key, WBMode.Auto)
    return mode, 0, shift_r, shift_b


def _params_to_ui(params: dict[str, str]) -> PresetUIValues:
    """Convert a scraped params dict (string values) to PresetUIValues."""
    v = PresetUIValues()

    if fs := params.get("filmSimulation"):
        v.filmSimulation = _parse_film_sim(fs)

    if dr := params.get("dynamicRange"):
        key = dr.strip().lower().replace(" ", "").replace("%", "")
        if "dr-p" in key or "drp" in key:
            # Site sometimes writes "Dynamic Range: DR-P Strong/Weak/Auto"
            # meaning D-Range Priority, not a manual DR% value.
            # Remap: leave dynamicRange at its default (0 → DR100 fallback)
            # and set dRangePriority from the suffix.
            for label, val in _DR_PRIORITY_MAP.items():
                if label.split()[-1] in key:  # match "strong"/"weak"/"auto"
                    v.dRangePriority = val
                    break
        elif key == "dr-auto" or key == "drauto":
            v.dynamicRange = _DR_AUTO_FALLBACK
        else:
            v.dynamicRange = _DR_MAP.get(key, 1)

    if ge := params.get("grainEffect"):
        v.grainEffect = _GRAIN_MAP.get(_clean_enum_text(ge), GrainEffect.Off)

    if cc := params.get("colorChrome"):
        v.colorChrome = _OFF_WEAK_STRONG.get(_clean_enum_text(cc), 0)

    if ccb := params.get("colorChromeFxBlue"):
        v.colorChromeFxBlue = _OFF_WEAK_STRONG.get(_clean_enum_text(ccb), 0)

    if ss := params.get("smoothSkin"):
        v.smoothSkin = _OFF_WEAK_STRONG.get(_clean_enum_text(ss), 0)

    if drp := params.get("dRangePriority"):
        v.dRangePriority = _DR_PRIORITY_MAP.get(drp.strip().lower(), 0)

    if wb := params.get("whiteBalance"):
        mode, ct, shift_r, shift_b = _parse_wb(wb)
        v.whiteBalance = mode
        if ct:
            v.wbColorTemp = ct
        v.wbShiftR = shift_r
        v.wbShiftB = shift_b

    if ht := params.get("highlight"):
        v.highlightTone = _parse_num(ht)

    if st := params.get("shadow"):
        v.shadowTone = _parse_num(st)

    if col := params.get("color"):
        v.color = _parse_num(col)

    if shp := params.get("sharpness"):
        v.sharpness = _parse_num(shp)

    if nr := params.get("noiseReduction"):
        v.noiseReduction = int(_parse_num(nr))

    if cla := params.get("clarity"):
        v.clarity = _parse_num(cla)

    return v


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_catalog(sensor_folder: str = "x-trans-v") -> list[Recipe]:
    """Load all recipes for the given sensor folder.

    Returns an empty list (not an error) if the folder or index doesn't exist yet.
    """
    sensor_dir = BUILTIN_DIR / sensor_folder
    index_file = sensor_dir / "_index.json"
    images_dir = sensor_dir / "images"

    if not index_file.exists():
        return []

    try:
        slugs: list[str] = json.loads(index_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    recipes: list[Recipe] = []
    for slug in slugs:
        json_path = sensor_dir / f"{slug}.json"
        if not json_path.exists():
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            img_file = data.get("image", "")
            img_path: Optional[Path] = None
            if img_file:
                candidate = images_dir / img_file
                img_path = candidate if candidate.exists() else None

            ui = _params_to_ui(data.get("params", {}))
            recipes.append(Recipe(
                slug=slug,
                title=data.get("title", slug.replace("-", " ").title()),
                source=data.get("source", ""),
                sensor=sensor_folder,
                image_path=img_path,
                ui_values=ui,
            ))
        except Exception:
            pass  # silently skip malformed entries

    return recipes
