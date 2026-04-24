"""Translate camera preset properties (D18E-D1A5) to/from UI-compatible values.

Preset encoding differs from d185 profile / UI encoding:
  Effects:  preset 1/2/3 -> UI 0/1/2
  Grain:    preset flat enum 1-5 -> UI GrainEffect combined value
  DynRange: preset raw % 100/200/400 -> UI enum 1/2/3
  WB:       preset uint16 (read as int16) -> mask 0xFFFF
  Tone:     preset x10 -> UI integer (/10)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field, replace
from typing import Optional

from .enums import GrainEffect, MONOCHROME_SIMS, WBMode


# --------------------------------------------------------------------------
# Data types
# --------------------------------------------------------------------------

@dataclass
class RawProp:
    """A single preset property with id, raw bytes, and decoded value."""
    id: int
    name: str = ''
    bytes: bytes = b''
    value: int = 0


@dataclass
class PresetUIValues:
    """UI-ready values extracted from a camera preset."""
    filmSimulation: int = 0
    dynamicRange: int = 0
    grainEffect: int = 0
    smoothSkin: int = 0
    colorChrome: int = 0
    colorChromeFxBlue: int = 0
    whiteBalance: int = 0
    wbShiftR: int = 0
    wbShiftB: int = 0
    wbColorTemp: int = 6500
    highlightTone: float = 0.0
    shadowTone: float = 0.0
    color: float = 0.0
    sharpness: float = 0.0
    noiseReduction: int = 0
    clarity: float = 0.0
    exposure: float = 0.0
    dRangePriority: int = 0
    monoWC: float = 0.0
    monoMG: float = 0.0


@dataclass(frozen=True)
class PresetSnapshot:
    """Frozen snapshot of a preset's state at load time."""
    name: str
    values: PresetUIValues


PRESET_DEFAULTS = PresetUIValues()


# --------------------------------------------------------------------------
# Binary helpers
# --------------------------------------------------------------------------

def packU16(v: int) -> bytes:
    return struct.pack('<H', v & 0xFFFF)


def packI16(v: int) -> bytes:
    return struct.pack('<h', max(-32768, min(32767, int(v))))


# --------------------------------------------------------------------------
# Encoding tables
# --------------------------------------------------------------------------

# Preset DR percentage -> d185 enum
DR_MAP = {100: 1, 200: 2, 400: 3}

# Preset grain flat enum -> UI GrainEffect combined value
GRAIN_MAP = {
    1: GrainEffect.Off,
    2: GrainEffect.WeakSmall,
    3: GrainEffect.StrongSmall,
    4: GrainEffect.WeakLarge,
    5: GrainEffect.StrongLarge,
}

# Decode Fuji proprietary HighIsoNR encoding -> -4..+4 integer
NR_DECODE = {
    0x8000: -4, 0x7000: -3, 0x4000: -2, 0x3000: -1,
    0x2000: 0,  0x1000: 1,  0x0000: 2,  0x6000: 3, 0x5000: 4,
}

# Encode UI NR value (-4..+4) -> Fuji proprietary HighIsoNR encoding
NR_ENCODE = {
    -4: 0x8000, -3: 0x7000, -2: 0x4000, -1: 0x3000,
    0:  0x2000, 1:  0x1000, 2:  0x0000, 3:  0x6000, 4: 0x5000,
}


def decodeTone(raw: int) -> float:
    """Decode a x10-encoded tone value, treating 0x8000 / -32768 as sentinel -> 0."""
    if raw == 0x8000 or raw == -32768:
        return 0.0
    return raw / 10.0


def decodeNR(raw: int) -> int:
    """raw comes as int16; mask to uint16 for NR_DECODE lookup."""
    u16 = raw & 0xFFFF
    return NR_DECODE.get(u16, 0)


# --------------------------------------------------------------------------
# Camera preset -> UI
# --------------------------------------------------------------------------

def _prop(settings: list[RawProp], pid: int) -> Optional[int]:
    for s in settings:
        if s.id == pid:
            return s.value
    return None


def translatePresetToUI(settings: list[RawProp]) -> PresetUIValues:
    """Translate camera preset settings to UI-compatible values."""
    v = PresetUIValues()

    filmSim = _prop(settings, 0xD192)
    if filmSim is not None:
        v.filmSimulation = filmSim

    dr = _prop(settings, 0xD190)
    if dr is not None:
        v.dynamicRange = DR_MAP.get(dr, 0)

    grain = _prop(settings, 0xD195)
    if grain is not None:
        v.grainEffect = GRAIN_MAP.get(grain, 0)

    # Effects: preset 1=Off,2=Weak,3=Strong -> UI 0/1/2
    skin = _prop(settings, 0xD198)
    if skin is not None:
        v.smoothSkin = max(0, skin - 1)

    cc = _prop(settings, 0xD196)
    if cc is not None:
        v.colorChrome = max(0, cc - 1)

    ccBlue = _prop(settings, 0xD197)
    if ccBlue is not None:
        v.colorChromeFxBlue = max(0, ccBlue - 1)

    # D193/D194: Monochromatic WC/MG - x10 encoding, only for B&W film sims
    if v.filmSimulation in MONOCHROME_SIMS:
        monoWC = _prop(settings, 0xD193)
        if monoWC is not None:
            v.monoWC = monoWC / 10.0
        monoMG = _prop(settings, 0xD194)
        if monoMG is not None:
            v.monoMG = monoMG / 10.0

    # WB: mask to uint16 (read as int16)
    wb = _prop(settings, 0xD199)
    if wb is not None:
        v.whiteBalance = wb & 0xFFFF

    wbR = _prop(settings, 0xD19A)
    if wbR is not None:
        v.wbShiftR = wbR

    wbB = _prop(settings, 0xD19B)
    if wbB is not None:
        v.wbShiftB = wbB

    ct = _prop(settings, 0xD19C)
    if ct is not None and ct > 0:
        v.wbColorTemp = ct

    # x10 tone params -> float (0x8000 sentinel = use default)
    ht = _prop(settings, 0xD19D)
    if ht is not None:
        v.highlightTone = decodeTone(ht)

    st = _prop(settings, 0xD19E)
    if st is not None:
        v.shadowTone = decodeTone(st)

    col = _prop(settings, 0xD19F)
    if col is not None:
        v.color = decodeTone(col)

    shp = _prop(settings, 0xD1A0)
    if shp is not None:
        v.sharpness = decodeTone(shp)

    nr = _prop(settings, 0xD1A1)
    if nr is not None:
        v.noiseReduction = decodeNR(nr)

    cla = _prop(settings, 0xD1A2)
    if cla is not None:
        v.clarity = decodeTone(cla)

    return v


def createSnapshot(name: str, settings: list[RawProp]) -> PresetSnapshot:
    """Create a frozen snapshot from preset data."""
    return PresetSnapshot(name=name, values=translatePresetToUI(settings))


# --------------------------------------------------------------------------
# d185 profile -> PresetUIValues bridge
# --------------------------------------------------------------------------

def cameraProfileToUIValues(profileData: bytes) -> PresetUIValues:
    """Extract PresetUIValues from the camera's native d185 base profile.

    Field mapping confirmed via X100VI test images (C1-C7 presets, 2026-03):
      [6]  DynamicRange%     [8]  FilmSimulation   [9]  GrainEffect (flat enum)
      [10] ColorChrome (1-idx) [11] SmoothSkin (1-idx) [13] WBShiftR [14] WBShiftB
      [15] WBColorTemp(K)    [16] HighlightTonex10 [17] ShadowTonex10
      [18] Colorx10 (sentinel) [19] Sharpnessx10   [25] CCFxBlue (1-idx) [27] Clarityx10
    """
    numParams = struct.unpack('<H', profileData[0:2])[0]
    offset = len(profileData) - numParams * 4

    def p(idx: int) -> int:
        return struct.unpack('<i', profileData[offset + idx * 4 : offset + idx * 4 + 4])[0]

    drRaw = p(6)
    cc = p(10)
    skin = p(11)
    ccBlue = p(25)

    return PresetUIValues(
        filmSimulation=p(8),
        dynamicRange=DR_MAP.get(drRaw, 0),
        grainEffect=GRAIN_MAP.get(p(9), 0),
        smoothSkin=max(0, skin - 1),
        colorChrome=max(0, cc - 1),
        colorChromeFxBlue=max(0, ccBlue - 1),
        whiteBalance=0,  # sentinel in camera profile
        wbShiftR=p(13),
        wbShiftB=p(14),
        wbColorTemp=p(15) or 6500,
        highlightTone=decodeTone(p(16)),
        shadowTone=decodeTone(p(17)),
        color=decodeTone(p(18)),
        sharpness=decodeTone(p(19)),
        noiseReduction=decodeNR(p(20)),
        clarity=decodeTone(p(27)),
        exposure=p(4) / 1000.0,
        dRangePriority=p(7),
        monoWC=0.0,
        monoMG=0.0,
    )


# --------------------------------------------------------------------------
# UI values -> camera preset properties (write path)
# --------------------------------------------------------------------------

UI_DR_TO_PRESET = {1: 100, 2: 200, 3: 400}

UI_GRAIN_TO_PRESET = {
    GrainEffect.Off:         1,
    GrainEffect.WeakSmall:   2,
    GrainEffect.StrongSmall: 3,
    GrainEffect.WeakLarge:   4,
    GrainEffect.StrongLarge: 5,
}

# Observed defaults for unknown/uneditable properties (from camera scans)
UNKNOWN_DEFAULTS = {
    0xD18E: 7,       # ImageSize (L 3:2)
    0xD18F: 4,       # ImageQuality
    0xD191: 0,       # Unknown
    0xD1A1: 0x4000,  # HighIsoNR - Fuji-specific
    0xD1A3: 1,       # LongExpNR = On
    0xD1A4: 1,       # ColorSpace = sRGB
    0xD1A5: 7,       # Unknown
}


def translateUIToPresetProps(
    values: PresetUIValues,
    base: Optional[list[RawProp]] = None,
) -> list[RawProp]:
    """Reverse-translate UI values to camera preset properties (D18E-D1A5).

    Returns a list of RawProp ready for writing. Conditional properties
    (D193/D194, D19C, D19F) are omitted entirely when they shouldn't be written.
    """
    base_map = {p.id: p for p in (base or [])}

    def makeRaw(pid: int, computed: Optional[bytes] = None) -> RawProp:
        if computed is not None:
            data = computed
        elif pid in base_map and base_map[pid].bytes:
            data = base_map[pid].bytes
        else:
            data = packU16(UNKNOWN_DEFAULTS.get(pid, 0))
        return RawProp(id=pid, name='', bytes=data, value=0)

    props: list[RawProp] = []
    isMono = values.filmSimulation in MONOCHROME_SIMS

    # D18E-D18F: ImageSize, ImageQuality
    props.append(makeRaw(0xD18E))
    props.append(makeRaw(0xD18F))

    # D190: DynamicRange%
    props.append(makeRaw(0xD190, packU16(UI_DR_TO_PRESET.get(values.dynamicRange, 100))))

    # D191: Unknown
    props.append(makeRaw(0xD191))

    # D192: FilmSimulation
    props.append(makeRaw(0xD192, packU16(values.filmSimulation or 1)))

    # D193-D194: Monochromatic WC/MG - x10. Only for B&W, reject value=0
    if isMono and values.monoWC != 0:
        props.append(makeRaw(0xD193, packI16(round(values.monoWC * 10))))
    if isMono and values.monoMG != 0:
        props.append(makeRaw(0xD194, packI16(round(values.monoMG * 10))))

    # D195: GrainEffect (flat enum)
    props.append(makeRaw(0xD195, packU16(UI_GRAIN_TO_PRESET.get(values.grainEffect, 1))))

    # D196: ColorChrome (1-indexed)
    props.append(makeRaw(0xD196, packU16(values.colorChrome + 1)))

    # D197: ColorChromeFxBlue (1-indexed)
    props.append(makeRaw(0xD197, packU16(values.colorChromeFxBlue + 1)))

    # D198: SmoothSkin (1-indexed)
    props.append(makeRaw(0xD198, packU16(values.smoothSkin + 1)))

    # D199: WhiteBalance
    props.append(makeRaw(0xD199, packU16(values.whiteBalance)))

    # D19C: WB Color Temp (K) - must be written right after D199.
    # Only include when WB mode is ColorTemp; camera rejects otherwise.
    if values.whiteBalance == WBMode.ColorTemp and values.wbColorTemp > 0:
        props.append(makeRaw(0xD19C, packU16(values.wbColorTemp)))

    # D19A-D19B: WB Shift R/B
    props.append(makeRaw(0xD19A, packI16(values.wbShiftR)))
    props.append(makeRaw(0xD19B, packI16(values.wbShiftB)))

    # D19D-D1A0: Tone params (x10)
    props.append(makeRaw(0xD19D, packI16(round(values.highlightTone * 10))))
    props.append(makeRaw(0xD19E, packI16(round(values.shadowTone * 10))))

    # D19F: Colorx10 - only for non-monochrome film sims
    if not isMono:
        props.append(makeRaw(0xD19F, packI16(round(values.color * 10))))

    props.append(makeRaw(0xD1A0, packI16(round(values.sharpness * 10))))

    # D1A1: HighIsoNR - Fuji proprietary encoding
    encoded = NR_ENCODE.get(values.noiseReduction)
    if encoded is not None:
        props.append(makeRaw(0xD1A1, packU16(encoded)))
    else:
        props.append(makeRaw(0xD1A1))

    # D1A2: Clarity (x10)
    props.append(makeRaw(0xD1A2, packI16(round(values.clarity * 10))))

    # D1A3-D1A5: LongExpNR, ColorSpace, Unknown
    props.append(makeRaw(0xD1A3))
    props.append(makeRaw(0xD1A4))
    props.append(makeRaw(0xD1A5))

    return props
