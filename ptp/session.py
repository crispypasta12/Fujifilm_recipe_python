"""PTP session management for Fujifilm cameras."""

from __future__ import annotations

import struct
from typing import Optional

from .constants import FujiPropNames, PTPOp
from .transport import PTPError, PTPTransport
from profile.preset_translate import (
    PresetUIValues,
    RawProp,
    translateUIToPresetProps,
)

# Preset property ID range (read these after writing slot selector D18C)
PRESET_NAME_PROP = 0xD18D
PRESET_SLOT_SELECTOR = 0xD18C
PRESET_PROP_START = 0xD18E
PRESET_PROP_END = 0xD1A5


def _decode_ptp_string(data: bytes, offset: int) -> tuple[str, int]:
    """Decode a PTP string: 1-byte length (chars incl NUL) + UTF-16LE chars.
    Returns (string, bytes_consumed).
    """
    if offset >= len(data):
        return '', 0
    n_chars = data[offset]
    consumed = 1 + n_chars * 2
    if n_chars == 0:
        return '', consumed
    raw = data[offset + 1 : offset + 1 + n_chars * 2]
    try:
        s = raw.decode('utf-16-le').rstrip('\x00')
    except UnicodeDecodeError:
        s = ''
    return s, consumed


def _encode_ptp_string(s: str) -> bytes:
    """Encode a PTP string (1-byte char count including NUL + UTF-16LE)."""
    if not s:
        return bytes([0])
    encoded = s.encode('utf-16-le') + b'\x00\x00'
    n_chars = len(encoded) // 2
    return bytes([n_chars & 0xFF]) + encoded


class FujiCamera:
    """High-level PTP session for a Fujifilm camera."""

    SESSION_ID = 1

    def __init__(self, transport: Optional[PTPTransport] = None):
        self.transport = transport or PTPTransport()
        self._txn_id = 0
        self._connected = False

    # ----------------------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------------------

    def connect(self) -> None:
        self.transport.open()
        self._txn_id = 0
        # OpenSession(sessionID)
        self.transport.transact(
            PTPOp.OpenSession, params=[self.SESSION_ID], transaction_id=self._next_txn()
        )
        self._connected = True

    def disconnect(self) -> None:
        if self._connected:
            try:
                self.transport.transact(PTPOp.CloseSession, transaction_id=self._next_txn())
            except PTPError:
                pass
            self._connected = False
        self.transport.close()

    def __enter__(self) -> 'FujiCamera':
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()

    def _next_txn(self) -> int:
        self._txn_id = (self._txn_id + 1) & 0xFFFFFFFF
        return self._txn_id

    # ----------------------------------------------------------------------
    # Property I/O
    # ----------------------------------------------------------------------

    def get_prop(self, prop_id: int) -> bytes:
        """GetDevicePropValue(propID) -> raw data bytes."""
        _code, _params, data = self.transport.transact(
            PTPOp.GetDevicePropValue,
            params=[prop_id],
            transaction_id=self._next_txn(),
        )
        return data

    def set_prop(self, prop_id: int, data: bytes) -> None:
        """SetDevicePropValue(propID, data)."""
        self.transport.transact(
            PTPOp.SetDevicePropValue,
            params=[prop_id],
            transaction_id=self._next_txn(),
            data=data,
        )

    # ----------------------------------------------------------------------
    # Helpers: decode preset property values
    # ----------------------------------------------------------------------

    @staticmethod
    def _decode_prop_value(prop_id: int, data: bytes) -> int:
        """Decode preset prop raw bytes as int16 (preset props use 2-byte values).
        For variable-length like name, handle separately.
        """
        if len(data) >= 2:
            return struct.unpack('<h', data[:2])[0]
        if len(data) == 1:
            return data[0]
        return 0

    # ----------------------------------------------------------------------
    # Preset slot read / write
    # ----------------------------------------------------------------------

    def read_preset_slot(self, slot: int) -> dict:
        """Read a preset slot (1-7). Returns a dict:
            {
              'slot': int, 'name': str,
              'props': list[RawProp],
              'ui': PresetUIValues,
            }
        """
        if not (1 <= slot <= 7):
            raise ValueError(f'slot must be 1-7, got {slot}')

        # Select slot
        self.set_prop(PRESET_SLOT_SELECTOR, struct.pack('<H', slot))

        # Read preset name (D18D) - PTP string
        name_data = self.get_prop(PRESET_NAME_PROP)
        name, _ = _decode_ptp_string(name_data, 0)

        # Read all preset props D18E..D1A5
        props: list[RawProp] = []
        for pid in range(PRESET_PROP_START, PRESET_PROP_END + 1):
            try:
                raw = self.get_prop(pid)
            except PTPError:
                continue
            value = self._decode_prop_value(pid, raw)
            props.append(RawProp(
                id=pid,
                name=FujiPropNames.get(pid, f'0x{pid:04X}'),
                bytes=raw,
                value=value,
            ))

        from profile.preset_translate import translatePresetToUI
        ui = translatePresetToUI(props)

        return {'slot': slot, 'name': name, 'props': props, 'ui': ui}

    def write_preset_slot(
        self,
        slot: int,
        values: PresetUIValues,
        name: str,
        base: Optional[list[RawProp]] = None,
    ) -> None:
        """Write a preset slot. Selects slot, writes name, writes all props in
        the order returned by translateUIToPresetProps().
        """
        if not (1 <= slot <= 7):
            raise ValueError(f'slot must be 1-7, got {slot}')

        # Select slot
        self.set_prop(PRESET_SLOT_SELECTOR, struct.pack('<H', slot))

        # Write name (D18D) - PTP string
        self.set_prop(PRESET_NAME_PROP, _encode_ptp_string(name))

        # Write props in exact order from translateUIToPresetProps
        props = translateUIToPresetProps(values, base=base)
        for p in props:
            try:
                self.set_prop(p.id, p.bytes)
            except PTPError as exc:
                # Re-raise with the property ID so the user knows exactly what failed
                raise PTPError(
                    f'Writing prop 0x{p.id:04X} '
                    f'({p.name or "unknown"}) = {p.bytes.hex()}: {exc}'
                ) from exc
