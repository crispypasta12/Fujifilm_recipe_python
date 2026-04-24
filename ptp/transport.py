"""Raw USB PTP transport layer using pyusb.

Handles USB device discovery, interface claim, and PTP container
pack/unpack for the Fujifilm X100VI.
"""

from __future__ import annotations

import struct
from typing import Optional

import usb.backend.libusb1
import usb.core
import usb.util

from .constants import (
    FUJI_VENDOR_ID,
    X100VI_PRODUCT_ID,
    ContainerType,
    PTPResp,
)


class PTPError(Exception):
    """Raised on PTP protocol errors (unexpected container, bad response code)."""


class PTPTransport:
    """Low-level PTP transport over USB bulk endpoints."""

    READ_CHUNK = 512
    DEFAULT_TIMEOUT = 5000  # ms

    def __init__(self, vendor_id: int = FUJI_VENDOR_ID, product_id: int = X100VI_PRODUCT_ID):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device: Optional[usb.core.Device] = None
        self.interface = None
        self.ep_in = None
        self.ep_out = None

    # ----------------------------------------------------------------------
    # Connection management
    # ----------------------------------------------------------------------

    @staticmethod
    def _get_backend():
        try:
            import libusb
            return usb.backend.libusb1.get_backend(find_library=lambda x: libusb.dll._name)
        except Exception:
            return None

    def open(self) -> None:
        """Find camera, detach kernel driver (non-Windows), claim interface."""
        backend = self._get_backend()
        dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id, backend=backend)
        if dev is None:
            raise PTPError(
                f'Camera not found (vid=0x{self.vendor_id:04X}, pid=0x{self.product_id:04X}). '
                'On Windows, use Zadig to install WinUSB/libusb driver for the camera.'
            )

        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except (NotImplementedError, usb.core.USBError):
            pass

        try:
            dev.set_configuration()
        except usb.core.USBError:
            pass

        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        ep_in = None
        ep_out = None
        for ep in intf:
            is_bulk = usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK
            if not is_bulk:
                continue
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                ep_in = ep
            else:
                ep_out = ep

        if ep_in is None or ep_out is None:
            raise PTPError('Could not find bulk IN/OUT endpoints on camera.')

        usb.util.claim_interface(dev, intf.bInterfaceNumber)

        self.device = dev
        self.interface = intf
        self.ep_in = ep_in
        self.ep_out = ep_out

    def close(self) -> None:
        if self.device is not None and self.interface is not None:
            try:
                usb.util.release_interface(self.device, self.interface.bInterfaceNumber)
            except usb.core.USBError:
                pass
            try:
                usb.util.dispose_resources(self.device)
            except Exception:
                pass
        self.device = None
        self.interface = None
        self.ep_in = None
        self.ep_out = None

    # ----------------------------------------------------------------------
    # Container pack / unpack
    # ----------------------------------------------------------------------

    @staticmethod
    def pack_container(ctype: int, code: int, txn_id: int,
                       params: Optional[list[int]] = None,
                       payload: bytes = b'') -> bytes:
        params = params or []
        if payload:
            body = payload
        else:
            body = b''.join(struct.pack('<I', p & 0xFFFFFFFF) for p in params)
        length = 12 + len(body)
        header = struct.pack('<IHHI', length, ctype, code, txn_id)
        return header + body

    @staticmethod
    def unpack_container_header(buf: bytes) -> tuple[int, int, int, int]:
        if len(buf) < 12:
            raise PTPError(f'Container too short: {len(buf)} bytes')
        length, ctype, code, txn_id = struct.unpack('<IHHI', buf[:12])
        return length, ctype, code, txn_id

    # ----------------------------------------------------------------------
    # Bulk I/O
    # ----------------------------------------------------------------------

    def _write(self, data: bytes, timeout: int = DEFAULT_TIMEOUT) -> None:
        if self.ep_out is None:
            raise PTPError('Transport not open')
        self.ep_out.write(data, timeout=timeout)

    def _read_one(self, timeout: int = DEFAULT_TIMEOUT) -> bytes:
        """Read a single container (full reassembly)."""
        if self.ep_in is None:
            raise PTPError('Transport not open')

        buf = bytes(self.ep_in.read(self.READ_CHUNK, timeout=timeout))
        if len(buf) < 12:
            raise PTPError(f'Short container read: {len(buf)} bytes')
        total_len = struct.unpack('<I', buf[:4])[0]
        while len(buf) < total_len:
            chunk = bytes(self.ep_in.read(self.READ_CHUNK, timeout=timeout))
            if not chunk:
                raise PTPError('Bulk read returned empty before container complete')
            buf += chunk
        return buf[:total_len]

    # ----------------------------------------------------------------------
    # High-level PTP transaction
    # ----------------------------------------------------------------------

    def send_ptp_command(
        self,
        op_code: int,
        params: Optional[list[int]] = None,
        transaction_id: int = 0,
        data: bytes = b'',
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Send a command container; if `data` is non-empty, follow with a data container."""
        cmd = self.pack_container(ContainerType.Command, op_code, transaction_id, params or [])
        self._write(cmd, timeout=timeout)

        if data:
            dc = self.pack_container(
                ContainerType.Data, op_code, transaction_id, payload=data
            )
            self._write(dc, timeout=timeout)

    def read_ptp_response(
        self, timeout: int = DEFAULT_TIMEOUT
    ) -> tuple[int, list[int], bytes]:
        """Read response + optional data container.

        Returns (response_code, params, data_payload). If the device sends a
        data container before the response, the payload is returned; otherwise
        data_payload is b''.
        """
        data_payload = b''
        params: list[int] = []

        while True:
            buf = self._read_one(timeout=timeout)
            length, ctype, code, _txn = self.unpack_container_header(buf)
            body = buf[12:length]

            if ctype == ContainerType.Data:
                data_payload = body
                continue
            if ctype == ContainerType.Response:
                # parse up to 5 uint32 params from body
                n_params = len(body) // 4
                if n_params > 0:
                    params = list(struct.unpack('<' + 'I' * n_params, body[: n_params * 4]))
                return code, params, data_payload
            # Ignore event containers; continue reading
            if ctype == ContainerType.Event:
                continue
            raise PTPError(f'Unexpected container type 0x{ctype:04X}')

    def transact(
        self,
        op_code: int,
        params: Optional[list[int]] = None,
        transaction_id: int = 0,
        data: bytes = b'',
        timeout: int = DEFAULT_TIMEOUT,
    ) -> tuple[int, list[int], bytes]:
        """Send command (+ optional data) and read response."""
        self.send_ptp_command(op_code, params, transaction_id, data, timeout=timeout)
        code, resp_params, resp_data = self.read_ptp_response(timeout=timeout)
        if code != PTPResp.OK:
            from .constants import resp_name
            raise PTPError(f'PTP op 0x{op_code:04X} failed: {resp_name(code)} (0x{code:04X})')
        return code, resp_params, resp_data
