"""D185 profile patching.

Patches the camera's native base profile (625 bytes) with user changes.
Only modifies fields the user explicitly set - sentinels for unset fields
are preserved so the camera uses EXIF values for untouched parameters.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional

from .preset_translate import NR_ENCODE


@dataclass
class ConversionParams:
    """User-friendly parameters for conversion."""
    filmSimulation: Optional[int] = None
    exposureBias: Optional[int] = None      # millistops (1000 = +1.0 EV)
    highlightTone: Optional[int] = None     # -4..+4
    shadowTone: Optional[int] = None
    color: Optional[int] = None
    sharpness: Optional[int] = None
    noiseReduction: Optional[int] = None
    clarity: Optional[int] = None           # -5..+5
    dynamicRange: Optional[int] = None
    whiteBalance: Optional[int] = None
    wbShiftR: Optional[int] = None
    wbShiftB: Optional[int] = None
    wbColorTemp: Optional[int] = None
    grainEffect: Optional[int] = None
    smoothSkinEffect: Optional[int] = None
    wideDRange: Optional[int] = None
    colorChromeEffect: Optional[int] = None
    colorChromeFxBlue: Optional[int] = None
    imageQuality: Optional[int] = None


# Native d185 profile field indices (camera's 625-byte format).
class NativeIdx:
    ExposureBias    = 4
    DynamicRange    = 6    # raw percentage: 100/200/400
    WideDRange      = 7
    FilmSimulation  = 8
    GrainEffect     = 9    # flat enum: 1=Off 2=WkSm 3=StrSm 4=WkLg 5=StrLg
    ColorChrome     = 10   # 1-indexed
    SmoothSkin      = 11   # 1-indexed
    WhiteBalance    = 12   # 0 = use EXIF (sentinel)
    WBShiftR        = 13
    WBShiftB        = 14
    WBColorTemp     = 15
    HighlightTone   = 16   # x10
    ShadowTone      = 17   # x10
    Color           = 18   # x10 (often sentinel 0)
    Sharpness       = 19   # x10
    NoiseReduction  = 20   # sentinel 0x8000
    CCFxBlue        = 25   # 1-indexed
    Clarity         = 27   # x10


# UI GrainEffect combined value -> native flat enum
GRAIN_TO_NATIVE = {
    0x0000: 1,  # Off
    0x0002: 2,  # WeakSmall
    0x0003: 3,  # StrongSmall
    0x0102: 4,  # WeakLarge
    0x0103: 5,  # StrongLarge
}

# UI DR enum -> native raw percentage
DR_TO_NATIVE = {1: 100, 2: 200, 3: 400}


def patchProfile(baseProfile: bytes, changes: ConversionParams) -> bytes:
    """Patch the camera's native base profile with user changes."""
    patched = bytearray(baseProfile)
    numParams = struct.unpack('<H', patched[0:2])[0]
    off = len(patched) - numParams * 4

    def _set(idx: int, val: int) -> None:
        pos = off + idx * 4
        struct.pack_into('<i', patched, pos, int(val))

    if changes.filmSimulation is not None:
        _set(NativeIdx.FilmSimulation, changes.filmSimulation)
    if changes.exposureBias is not None:
        _set(NativeIdx.ExposureBias, changes.exposureBias)
    if changes.dynamicRange is not None:
        _set(NativeIdx.DynamicRange, DR_TO_NATIVE.get(changes.dynamicRange, 0))
    if changes.wideDRange is not None:
        _set(NativeIdx.WideDRange, changes.wideDRange)

    if changes.grainEffect is not None:
        _set(NativeIdx.GrainEffect, GRAIN_TO_NATIVE.get(changes.grainEffect, 1))

    # Effects: UI 0/1/2 -> native 1-indexed
    if changes.colorChromeEffect is not None:
        _set(NativeIdx.ColorChrome, changes.colorChromeEffect + 1)
    if changes.colorChromeFxBlue is not None:
        _set(NativeIdx.CCFxBlue, changes.colorChromeFxBlue + 1)
    if changes.smoothSkinEffect is not None:
        _set(NativeIdx.SmoothSkin, changes.smoothSkinEffect + 1)

    if changes.whiteBalance is not None:
        _set(NativeIdx.WhiteBalance, changes.whiteBalance)
    if changes.wbShiftR is not None:
        _set(NativeIdx.WBShiftR, changes.wbShiftR)
    if changes.wbShiftB is not None:
        _set(NativeIdx.WBShiftB, changes.wbShiftB)
    if changes.wbColorTemp is not None:
        _set(NativeIdx.WBColorTemp, changes.wbColorTemp)

    # Tone params: UI integer * 10 -> native x10
    if changes.highlightTone is not None:
        _set(NativeIdx.HighlightTone, int(changes.highlightTone * 10))
    if changes.shadowTone is not None:
        _set(NativeIdx.ShadowTone, int(changes.shadowTone * 10))
    if changes.color is not None:
        _set(NativeIdx.Color, int(changes.color * 10))
    if changes.sharpness is not None:
        _set(NativeIdx.Sharpness, int(changes.sharpness * 10))
    # NR: proprietary encoding (not x10)
    if changes.noiseReduction is not None:
        nr_encoded = NR_ENCODE.get(changes.noiseReduction)
        if nr_encoded is not None:
            _set(NativeIdx.NoiseReduction, nr_encoded)
    if changes.clarity is not None:
        _set(NativeIdx.Clarity, int(changes.clarity * 10))

    return bytes(patched)
