"""Fujifilm film simulation / effect enums and label dictionaries."""


# ==========================================================================
# Film Simulations
# ==========================================================================

class FilmSim:
    Provia        = 0x01
    Velvia        = 0x02
    Astia         = 0x03
    ProNegHi      = 0x04
    ProNegStd     = 0x05
    Monochrome    = 0x06
    MonochromeYe  = 0x07
    MonochromeR   = 0x08
    MonochromeG   = 0x09
    Sepia         = 0x0A
    ClassicChrome = 0x0B
    Acros         = 0x0C
    AcrosYe       = 0x0D
    AcrosR        = 0x0E
    AcrosG        = 0x0F
    Eterna        = 0x10
    ClassicNeg    = 0x11
    EternaBleach  = 0x12
    NostalgicNeg  = 0x13
    RealaAce      = 0x14


# Film simulations that are monochrome (B&W) - Color adjustment is not applicable
MONOCHROME_SIMS = frozenset({
    FilmSim.Monochrome, FilmSim.MonochromeYe, FilmSim.MonochromeR, FilmSim.MonochromeG,
    FilmSim.Sepia, FilmSim.Acros, FilmSim.AcrosYe, FilmSim.AcrosR, FilmSim.AcrosG,
})

FilmSimLabels = {
    FilmSim.Provia:        'Provia (Standard)',
    FilmSim.Velvia:        'Velvia (Vivid)',
    FilmSim.Astia:         'Astia (Soft)',
    FilmSim.ProNegHi:      'PRO Neg. Hi',
    FilmSim.ProNegStd:     'PRO Neg. Std',
    FilmSim.Monochrome:    'Monochrome',
    FilmSim.MonochromeYe:  'Monochrome + Yellow',
    FilmSim.MonochromeR:   'Monochrome + Red',
    FilmSim.MonochromeG:   'Monochrome + Green',
    FilmSim.Sepia:         'Sepia',
    FilmSim.ClassicChrome: 'Classic Chrome',
    FilmSim.Acros:         'Acros',
    FilmSim.AcrosYe:       'Acros + Yellow',
    FilmSim.AcrosR:        'Acros + Red',
    FilmSim.AcrosG:        'Acros + Green',
    FilmSim.Eterna:        'Eterna (Cinema)',
    FilmSim.EternaBleach:  'Eterna Bleach Bypass',
    FilmSim.NostalgicNeg:  'Nostalgic Neg.',
    FilmSim.RealaAce:      'Reala Ace',
    FilmSim.ClassicNeg:    'Classic Neg.',
}

# Per-simulation accent colours as hex strings (no Qt dependency).
# Shared by the recipe card renderer and the preset panel dot indicator.
SIM_COLORS: dict[int, str] = {
    FilmSim.Provia:        '#a8c5e8',
    FilmSim.Velvia:        '#e8854a',
    FilmSim.Astia:         '#d4c97a',
    FilmSim.ClassicChrome: '#7ab8c8',
    FilmSim.ProNegHi:      '#e87a7a',
    FilmSim.ProNegStd:     '#b8a8e8',
    FilmSim.ClassicNeg:    '#b0b0c0',
    FilmSim.Eterna:        '#8ab88a',
    FilmSim.EternaBleach:  '#e0d098',
    FilmSim.Acros:         '#b0b0b8',
    FilmSim.AcrosYe:       '#c8c890',
    FilmSim.AcrosR:        '#c89090',
    FilmSim.AcrosG:        '#90c890',
    FilmSim.Monochrome:    '#c0c0c8',
    FilmSim.MonochromeYe:  '#c8c090',
    FilmSim.MonochromeR:   '#c89090',
    FilmSim.MonochromeG:   '#90c890',
    FilmSim.Sepia:         '#c8a878',
    FilmSim.NostalgicNeg:  '#c8d8e8',
    FilmSim.RealaAce:      '#e8c890',
}


# ==========================================================================
# White Balance
# ==========================================================================

class WBMode:
    AsShot           = 0x0000
    Auto             = 0x0002
    Daylight         = 0x0004
    Incandescent     = 0x0006
    Underwater       = 0x0008
    Fluorescent1     = 0x8001
    Fluorescent2     = 0x8002
    Fluorescent3     = 0x8003
    Shade            = 0x8006
    ColorTemp        = 0x8007
    AmbiencePriority = 0x8021  # Auto WB sub-mode (confirmed from preset scan)


WBModeLabels = {
    WBMode.AsShot:           'As Shot',
    WBMode.Auto:             'Auto',
    WBMode.Daylight:         'Daylight',
    WBMode.Shade:            'Shade',
    WBMode.Fluorescent1:     'Fluorescent 1',
    WBMode.Fluorescent2:     'Fluorescent 2',
    WBMode.Fluorescent3:     'Fluorescent 3',
    WBMode.Incandescent:     'Incandescent',
    WBMode.Underwater:       'Underwater',
    WBMode.ColorTemp:        'Color Temperature',
    WBMode.AmbiencePriority: 'Ambience Priority',
}


# ==========================================================================
# Dynamic Range
# ==========================================================================

class DynRange:
    DR100 = 0x1
    DR200 = 0x2
    DR400 = 0x3


DynRangeLabels = {
    DynRange.DR100: 'DR 100%',
    DynRange.DR200: 'DR 200%',
    DynRange.DR400: 'DR 400%',
}


# ==========================================================================
# Effects (Off/Weak/Strong triplets)
# ==========================================================================

# Grain effect - combined strength + size as used in d185 profile.
# Encoding: low byte = strength (0=off, 2=weak, 3=strong), high byte = size (0=small, 1=large).
class GrainEffect:
    Off         = 0x0000
    WeakSmall   = 0x0002
    StrongSmall = 0x0003
    WeakLarge   = 0x0102
    StrongLarge = 0x0103


GrainEffectLabels = {
    GrainEffect.Off:         'Off',
    GrainEffect.WeakSmall:   'Weak Small',
    GrainEffect.StrongSmall: 'Strong Small',
    GrainEffect.WeakLarge:   'Weak Large',
    GrainEffect.StrongLarge: 'Strong Large',
}


class GrainStrength:
    Off    = 0
    Weak   = 2
    Strong = 3


GrainStrengthLabels = {
    GrainStrength.Off:    'Off',
    GrainStrength.Weak:   'Weak',
    GrainStrength.Strong: 'Strong',
}


class GrainSize:
    Small = 0
    Large = 1


GrainSizeLabels = {
    GrainSize.Small: 'Small',
    GrainSize.Large: 'Large',
}


class SmoothSkin:
    Off    = 0
    Weak   = 1
    Strong = 2


SmoothSkinLabels = {
    SmoothSkin.Off:    'Off',
    SmoothSkin.Weak:   'Weak',
    SmoothSkin.Strong: 'Strong',
}


class ColorChrome:
    Off    = 0
    Weak   = 1
    Strong = 2


ColorChromeLabels = {
    ColorChrome.Off:    'Off',
    ColorChrome.Weak:   'Weak',
    ColorChrome.Strong: 'Strong',
}


class ColorChromeFxBlue:
    Off    = 0
    Weak   = 1
    Strong = 2


ColorChromeFxBlueLabels = {
    ColorChromeFxBlue.Off:    'Off',
    ColorChromeFxBlue.Weak:   'Weak',
    ColorChromeFxBlue.Strong: 'Strong',
}


class DRangePriority:
    Off    = 0
    Auto   = 1
    Weak   = 2
    Strong = 3


DRangePriorityLabels = {
    DRangePriority.Off:    'Off',
    DRangePriority.Auto:   'Auto',
    DRangePriority.Weak:   'Weak',
    DRangePriority.Strong: 'Strong',
}


def label_to_value(label_dict: dict, label: str, default: int = 0) -> int:
    """Reverse lookup: find value for a label string."""
    for k, v in label_dict.items():
        if v == label:
            return k
    return default
