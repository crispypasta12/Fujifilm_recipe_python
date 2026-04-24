"""Background worker for all camera I/O — runs on a dedicated QThread."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from ptp.session import FujiCamera
from ptp.transport import PTPError

NUM_SLOTS = 7


class CameraWorker(QObject):
    """Owns the FujiCamera and runs all PTP operations off the main thread."""

    # signals emitted toward the main thread
    connected = pyqtSignal(str)              # camera model
    connectionFailed = pyqtSignal(str)       # error message
    disconnected = pyqtSignal()
    slotRead = pyqtSignal(int, str, object)      # slot, name, PresetUIValues
    allSlotsRead = pyqtSignal(int, int)          # ok_count, total
    slotWritten = pyqtSignal(int, str, object)   # slot, name, PresetUIValues
    writeFailed = pyqtSignal(int, str)           # slot, error message
    statusMessage = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._camera: FujiCamera | None = None
        self._base_props: dict[int, list] = {}

    # ------------------------------------------------------------------ slots

    @pyqtSlot()
    def connect_camera(self) -> None:
        try:
            cam = FujiCamera()
            cam.connect()
            self._camera = cam
            self._base_props.clear()
            self.connected.emit(cam.transport.model)
            self._do_read_all()
        except Exception as e:
            self._camera = None
            self.connectionFailed.emit(f'{type(e).__name__}: {e}')

    @pyqtSlot()
    def disconnect_camera(self) -> None:
        if self._camera is not None:
            try:
                self._camera.disconnect()
            except Exception:
                pass
            self._camera = None
        self._base_props.clear()
        self.disconnected.emit()

    @pyqtSlot()
    def read_all_slots(self) -> None:
        self._do_read_all()

    @pyqtSlot(int, str, object)
    def write_slot(self, slot: int, name: str, values) -> None:
        if self._camera is None:
            self.writeFailed.emit(slot, 'Not connected')
            return
        try:
            base = self._base_props.get(slot)
            self._camera.write_preset_slot(slot, values, name, base=base)
            result = self._camera.read_preset_slot(slot)
            self._base_props[slot] = result['props']
            self.slotWritten.emit(slot, result['name'], result['ui'])
        except Exception as e:
            self.writeFailed.emit(slot, f'{type(e).__name__}: {e}')

    # ----------------------------------------------------------------- private

    def _do_read_all(self) -> None:
        if self._camera is None:
            return
        ok = 0
        for slot in range(1, NUM_SLOTS + 1):
            try:
                result = self._camera.read_preset_slot(slot)
                self._base_props[slot] = result['props']
                self.slotRead.emit(slot, result['name'], result['ui'])
                ok += 1
            except Exception as e:
                self.statusMessage.emit(f'Slot {slot} read error: {e}')
        self.allSlotsRead.emit(ok, NUM_SLOTS)
