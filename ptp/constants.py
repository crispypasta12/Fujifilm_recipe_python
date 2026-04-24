"""PTP protocol constants for Fujifilm cameras.

PTP container format:
  [0-3]  uint32 LE: total length
  [4-5]  uint16 LE: type (1=CMD, 2=DATA, 3=RESPONSE)
  [6-7]  uint16 LE: operation code
  [8-11] uint32 LE: transaction ID
  [...]  params (up to 5 x uint32) or data payload
"""

# PTP standard operation codes (ISO 15740)
class PTPOp:
    GetDeviceInfo      = 0x1001
    OpenSession        = 0x1002
    CloseSession       = 0x1003
    GetStorageIDs      = 0x1004
    GetStorageInfo     = 0x1005
    GetNumObjects      = 0x1006
    GetObjectHandles   = 0x1007
    GetObjectInfo      = 0x1008
    GetObject          = 0x1009
    DeleteObject       = 0x100B
    SendObjectInfo     = 0x100C
    SendObject         = 0x100D
    GetDevicePropDesc  = 0x1014
    GetDevicePropValue = 0x1015
    SetDevicePropValue = 0x1016


# Fujifilm vendor-specific operation codes
class FujiOp:
    SendObjectInfo = 0x900C
    SendObject2    = 0x900D


# PTP response codes
class PTPResp:
    OK                     = 0x2001
    GeneralError           = 0x2002
    SessionNotOpen         = 0x2003
    InvalidTransactionID   = 0x2004
    OperationNotSupported  = 0x2005
    ParameterNotSupported  = 0x2006
    IncompleteTransfer     = 0x2007
    InvalidStorageID       = 0x2008
    InvalidObjectHandle    = 0x2009
    DevicePropNotSupported = 0x200A
    SessionAlreadyOpen     = 0x201E


# PTP container types
class ContainerType:
    Command  = 0x0001
    Data     = 0x0002
    Response = 0x0003
    Event    = 0x0004


# Fujifilm device property codes
class FujiProp:
    RawConvProfile     = 0xD185
    StartRawConversion = 0xD183


# Known Fuji device property names (for display).
#
# Confirmed mapping via cross-referencing 7 camera presets (X100VI, 2026-03).
# Encoding differs from d185 profile format:
#   Effects:  1=Off 2=Weak 3=Strong (not 0/2/3)
#   Grain:    flat enum 1=Off 2=WeakSmall 3=StrongSmall 4=WeakLarge 5=StrongLarge
#   DynRange: raw percentage 100/200/400 (not enum 1/2/3)
#   WB:       uint16 values (read as int16 - mask with 0xFFFF for lookup)
#   Tone:     x10 encoding (same as d185)
#
# RESOLVED via Wireshark captures (2026-03):
#   D193: MonoWC (Warm/Cool) - x10 encoding, rejects writing 0, only for B&W sims
#   D194: MonoMG (Magenta/Green) - same encoding as D193
#   D1A1: HighIsoNR - Fuji-specific encoding (NOT x10): -4->0x8000, 0->0x2000, +4->0x5000
#
# Still unknown:
#   D191: always 0
#   D1A5: always 7
FujiPropNames = {
    0xD001: 'FilmSimulation',
    0xD002: 'FilmSimulationTune',
    0xD003: 'DRangeMode',
    0xD007: 'ColorTemperature',
    0xD008: 'WhiteBalanceFineTune',
    0xD00A: 'NoiseReduction',
    0xD00B: 'ImageQuality',
    0xD00C: 'RecMode',
    0xD00F: 'FocusMode',
    0xD017: 'GrainEffect',
    0xD019: 'ShadowHighlight',
    0xD100: 'ExposureIndex',
    0xD104: 'FocusMeteringMode',
    0xD10A: 'ShutterSpeed',
    0xD10B: 'ImageAspectRatio',
    0xD171: 'RawConversionEdit',
    0xD183: 'StartRawConversion',
    0xD184: 'IOPCodes',
    0xD185: 'RawConvProfile',
    0xD186: 'FirmwareVersion',
    0xD187: 'FirmwareVersion2',

    # Custom preset properties (D18C-D1A5)
    0xD18C: 'PresetSlot',
    0xD18D: 'PresetName',
    0xD18E: 'P:ImageSize',
    0xD18F: 'P:ImageQuality',
    0xD190: 'P:DynamicRange%',
    0xD191: 'P:?D191',
    0xD192: 'P:FilmSimulation',
    0xD193: 'P:MonoWCx10',
    0xD194: 'P:MonoMGx10',
    0xD195: 'P:GrainEffect',
    0xD196: 'P:ColorChrome',
    0xD197: 'P:ColorChromeFxBlue',
    0xD198: 'P:SmoothSkin',
    0xD199: 'P:WhiteBalance',
    0xD19A: 'P:WBShiftR',
    0xD19B: 'P:WBShiftB',
    0xD19C: 'P:ColorTemp(K)',
    0xD19D: 'P:HighlightTonex10',
    0xD19E: 'P:ShadowTonex10',
    0xD19F: 'P:Colorx10',
    0xD1A0: 'P:Sharpnessx10',
    0xD1A1: 'P:HighIsoNR?',
    0xD1A2: 'P:Clarityx10',
    0xD1A3: 'P:LongExpNR',
    0xD1A4: 'P:ColorSpace',
    0xD1A5: 'P:?D1A5',
}


# PTP data type names
PTPDataTypeNames = {
    0x0001: 'INT8',
    0x0002: 'UINT8',
    0x0003: 'INT16',
    0x0004: 'UINT16',
    0x0005: 'INT32',
    0x0006: 'UINT32',
    0x0007: 'INT64',
    0x0008: 'UINT64',
    0x4002: 'UINT8[]',
    0x4004: 'UINT16[]',
    0x4006: 'UINT32[]',
    0xFFFF: 'String',
}


# USB identifiers
FUJI_VENDOR_ID = 0x04CB

FUJI_PRODUCT_IDS = {
    0x02E3: 'X-T30',
    0x02E5: 'X100V',
    0x02E7: 'X-T4',
    0x0305: 'X100VI',
}

X100VI_PRODUCT_ID = 0x0305


def resp_name(code: int) -> str:
    """Human-readable response code name."""
    for name in dir(PTPResp):
        if name.startswith('_'):
            continue
        if getattr(PTPResp, name) == code:
            return name
    return f'0x{code:04X}'
