"""Main application window for FujiRecipe."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from profile.enums import (
    ColorChromeFxBlueLabels,
    ColorChromeLabels,
    DRangePriorityLabels,
    DynRangeLabels,
    FilmSimLabels,
    GrainEffectLabels,
    SmoothSkinLabels,
    WBModeLabels,
    label_to_value,
)
from profile.preset_translate import PresetUIValues

from .camera_worker import CameraWorker
from .preset_panel import PresetPanel
from .recipe_browser import RecipeBrowserDialog
from .recipe_creator import RecipeCreatorDialog


PRESETS_DIR = Path(__file__).resolve().parent.parent / 'recipes' / 'presets'


class MainWindow(QMainWindow):
    """FujiRecipe main window."""

    NUM_SLOTS = 7

    # signals to worker (queued across thread boundary automatically)
    _connectRequested    = pyqtSignal()
    _disconnectRequested = pyqtSignal()
    _readAllRequested    = pyqtSignal()
    _writeSlotRequested  = pyqtSignal(int, str, object)  # slot, name, PresetUIValues

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('FujiRecipe — Fujifilm Film Simulation Editor')
        self.resize(720, 900)

        self._connected = False
        self._busy = False
        self._browser: Optional[RecipeBrowserDialog] = None

        self._build_ui()
        self._setup_worker()
        self._set_connected(False)

    # ------------------------------------------------------------ build UI

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = QWidget()
        top.setObjectName('TopBar')
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(12, 8, 12, 8)
        top_l.setSpacing(8)

        self.title = QLabel('FujiRecipe')
        self.title.setProperty('role', 'heading')

        self.connDot = QLabel('●')
        self.connDot.setObjectName('connDot')
        self.connDot.setProperty('state', 'off')
        self.connStatus = QLabel('Disconnected')
        self.connStatus.setProperty('role', 'dim')

        # File ▾ menu button (Import / Export)
        self.fileBtn = QToolButton()
        self.fileBtn.setText('File ▾')
        self.fileBtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.fileBtn.setStyleSheet('QToolButton::menu-indicator { image: none; }')
        file_menu = QMenu(self.fileBtn)
        file_menu.addAction('Import Recipe…',    self._on_import_clicked)
        file_menu.addAction('Import All…',        self._on_import_all_clicked)
        file_menu.addSeparator()
        file_menu.addAction('Export Slot…',       self._on_export_clicked)
        file_menu.addAction('Export All…',        self._on_export_all_clicked)
        file_menu.addSeparator()
        file_menu.addAction('Export Card…',       self._on_export_card_clicked)
        self.fileBtn.setMenu(file_menu)

        self.browseBtn = QPushButton('Browse Recipes')
        self.browseBtn.setProperty('role', 'primary')
        self.browseBtn.clicked.connect(self._on_browse_clicked)

        self.readAllBtn = QPushButton('Read All')
        self.readAllBtn.clicked.connect(self._on_read_all_clicked)

        self.connectBtn = QPushButton('Connect')
        self.connectBtn.clicked.connect(self._on_connect_clicked)

        top_l.addWidget(self.title)
        top_l.addStretch(1)
        top_l.addWidget(self.connDot)
        top_l.addWidget(self.connStatus)
        top_l.addSpacing(8)
        top_l.addWidget(self.fileBtn)
        top_l.addWidget(self.browseBtn)
        top_l.addWidget(self.readAllBtn)
        top_l.addWidget(self.connectBtn)
        root.addWidget(top)

        # ── Tabs ─────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.panels: list[PresetPanel] = []
        for slot in range(1, self.NUM_SLOTS + 1):
            panel = PresetPanel(slot)
            panel.writeRequested.connect(self._on_write_slot)
            panel.dirtyChanged.connect(self._on_panel_dirty_changed)
            panel.saveAsRecipeRequested.connect(self._on_save_as_recipe)
            self.tabs.addTab(panel, f'C{slot}')
            self.panels.append(panel)
        root.addWidget(self.tabs, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage('Ready')

    # ---------------------------------------------------------- worker setup

    def _setup_worker(self) -> None:
        self._thread = QThread(self)
        self._worker = CameraWorker()
        self._worker.moveToThread(self._thread)

        self._worker.connected.connect(self._on_connected)
        self._worker.connectionFailed.connect(self._on_connection_failed)
        self._worker.disconnected.connect(self._on_disconnected)
        self._worker.slotRead.connect(self._on_slot_read)
        self._worker.allSlotsRead.connect(self._on_all_slots_read)
        self._worker.slotWritten.connect(self._on_slot_written)
        self._worker.writeFailed.connect(self._on_write_failed)
        self._worker.statusMessage.connect(self.statusBar().showMessage)

        self._connectRequested.connect(self._worker.connect_camera)
        self._disconnectRequested.connect(self._worker.disconnect_camera)
        self._readAllRequested.connect(self._worker.read_all_slots)
        self._writeSlotRequested.connect(self._worker.write_slot)

        self._thread.start()

    # --------------------------------------------------------- connection UI

    def _set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.connDot.setProperty('state', 'on' if connected else 'off')
        self.connStatus.setText('Connected — X100VI' if connected else 'Disconnected')
        self.connectBtn.setText('Disconnect' if connected else 'Connect')
        self.readAllBtn.setEnabled(connected and not self._busy)
        for p in self.panels:
            p.writeButton.setEnabled(connected and not self._busy)
        self.connDot.style().unpolish(self.connDot)
        self.connDot.style().polish(self.connDot)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.connectBtn.setEnabled(not busy)
        self.readAllBtn.setEnabled(not busy and self._connected)
        for p in self.panels:
            p.writeButton.setEnabled(not busy and self._connected)

    def _on_connect_clicked(self) -> None:
        if self._connected:
            self._set_connected(False)
            self._disconnectRequested.emit()
            self.statusBar().showMessage('Disconnected')
        else:
            self._set_busy(True)
            self.statusBar().showMessage('Connecting...')
            self._connectRequested.emit()

    # --------------------------------------------------------- worker responses

    def _on_connected(self, model: str) -> None:
        self._set_connected(True)
        self._set_busy(True)  # still busy — read is in progress
        self.statusBar().showMessage('Connected. Reading presets...')

    def _on_connection_failed(self, msg: str) -> None:
        self._set_busy(False)
        self._set_connected(False)
        QMessageBox.critical(self, 'Connection failed', msg)
        self.statusBar().showMessage('Connection failed')

    def _on_disconnected(self) -> None:
        self._set_busy(False)
        if self._connected:
            self._set_connected(False)
            self.statusBar().showMessage('Disconnected')

    def _on_slot_read(self, slot: int, name: str, values) -> None:
        self.panels[slot - 1].load_values(name, values)

    def _on_all_slots_read(self, ok: int, total: int) -> None:
        self._set_busy(False)
        msg = f'Read {ok}/{total} slots'
        if ok < total:
            msg += f' ({total - ok} errors)'
        self.statusBar().showMessage(msg)

    def _on_slot_written(self, slot: int, name: str, values) -> None:
        self._set_busy(False)
        self.panels[slot - 1].load_values(name, values)
        self.statusBar().showMessage(f'Wrote slot C{slot}')

    def _on_write_failed(self, slot: int, msg: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, 'Write failed', msg)
        self.statusBar().showMessage(f'Write to C{slot} failed')

    # --------------------------------------------------------- read / write

    def _on_read_all_clicked(self) -> None:
        if not self._connected:
            return
        self._set_busy(True)
        self.statusBar().showMessage('Reading presets...')
        self._readAllRequested.emit()

    def _on_write_slot(self, slot: int) -> None:
        if not self._connected:
            QMessageBox.warning(self, 'Not connected', 'Connect the camera first.')
            return
        panel = self.panels[slot - 1]
        name, values = panel.dump_values()
        confirm = QMessageBox.question(
            self,
            'Confirm write',
            f'Write changes to slot C{slot} ("{name}") on the camera?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(True)
        self.statusBar().showMessage(f'Writing slot C{slot}...')
        self._writeSlotRequested.emit(slot, name, values)

    # --------------------------------------------------------- recipe browser

    def _on_browse_clicked(self) -> None:
        if self._browser is None:
            self._browser = RecipeBrowserDialog(self)
            self._browser.recipeLoadRequested.connect(self._on_recipe_load_requested)
            self._browser.recipeWriteRequested.connect(self._on_recipe_write_requested)
            self._browser.destroyed.connect(self._on_browser_destroyed)
        self._browser.show()
        self._browser.raise_()
        self._browser.activateWindow()

    def _on_recipe_load_requested(self, slot: int, name: str, values) -> None:
        self.panels[slot - 1].load_values(name, values)
        self.tabs.setCurrentIndex(slot - 1)
        self.statusBar().showMessage(
            f'Loaded "{name}" into C{slot} — press Write to send to camera'
        )

    def _on_recipe_write_requested(self, slot: int, name: str, values) -> None:
        """Load recipe into slot then immediately write to camera."""
        if not self._connected:
            QMessageBox.warning(self, 'Not connected', 'Connect the camera first.')
            return
        confirm = QMessageBox.question(
            self,
            'Confirm write',
            f'Write "{name}" to slot C{slot} on the camera?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.panels[slot - 1].load_values(name, values)
        self.tabs.setCurrentIndex(slot - 1)
        self._set_busy(True)
        self.statusBar().showMessage(f'Writing "{name}" to C{slot}...')
        self._writeSlotRequested.emit(slot, name, values)

    def _on_browser_destroyed(self) -> None:
        self._browser = None

    # --------------------------------------------------- save slot as recipe

    def _on_save_as_recipe(self, slot: int) -> None:
        """Open the Recipe Creator pre-filled with the current slot values."""
        panel = self.panels[slot - 1]
        name, values = panel.dump_values()
        dlg = RecipeCreatorDialog(initial_name=name, initial_values=values, parent=self)
        dlg.recipeSaved.connect(self._on_recipe_saved_from_panel)
        dlg.exec()

    def _on_recipe_saved_from_panel(self, slug: str, name: str, values) -> None:
        self.statusBar().showMessage(f'Recipe "{name}" saved to My Recipes')
        # Notify the open browser to refresh if it's showing My Recipes
        if self._browser is not None:
            self._browser.refresh_user_recipes()

    # --------------------------------------------------------- recipe card export

    def _on_export_card_clicked(self) -> None:
        """Export a 900×540 PNG recipe card for the current slot."""
        from .recipe_card import generate_recipe_card
        from recipes.loader import Recipe

        panel      = self._current_panel()
        name, values = panel.dump_values()
        recipe = Recipe(
            slug=(_safe_filename(name or f'C{panel.slot}').lower().replace(' ', '-') or 'slot'),
            title=name or f'Slot C{panel.slot}',
            source=f'Slot C{panel.slot}',
            sensor='slot',
            image_path=None,
            ui_values=values,
        )
        pix = generate_recipe_card(recipe)

        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        safe = _safe_filename(name or f'C{panel.slot}')
        default = str(PRESETS_DIR / f'{safe}_card.png')
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export Recipe Card', default, 'PNG Image (*.png)'
        )
        if not path:
            return
        if pix.save(path, 'PNG'):
            self.statusBar().showMessage(f'Card exported: {os.path.basename(path)}')
        else:
            QMessageBox.critical(self, 'Export failed', f'Could not save to {path}')

    # --------------------------------------------------------- dirty tracking

    def _on_panel_dirty_changed(self, slot: int, dirty: bool) -> None:
        self.tabs.setTabText(slot - 1, f'C{slot} ●' if dirty else f'C{slot}')

    # --------------------------------------------------------- import/export

    def _current_panel(self) -> PresetPanel:
        return self.panels[self.tabs.currentIndex()]

    def _on_export_clicked(self) -> None:
        panel = self._current_panel()
        name, values = panel.dump_values()
        payload = self._values_to_json(values, name=name, slot=panel.slot)

        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_filename(name or f'C{panel.slot}')
        default = str(PRESETS_DIR / f'{safe_name}.json')
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export recipe', default, 'JSON (*.json)'
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f'Exported {os.path.basename(path)}')
        except OSError as e:
            QMessageBox.critical(self, 'Export failed', str(e))

    def _on_export_all_clicked(self) -> None:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        folder = QFileDialog.getExistingDirectory(
            self, 'Export all slots to folder', str(PRESETS_DIR)
        )
        if not folder:
            return
        errors = 0
        for panel in self.panels:
            name, values = panel.dump_values()
            payload = self._values_to_json(values, name=name, slot=panel.slot)
            safe_name = _safe_filename(name or f'C{panel.slot}')
            path = Path(folder) / f'C{panel.slot}_{safe_name}.json'
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
            except OSError:
                errors += 1
        ok = self.NUM_SLOTS - errors
        msg = f'Exported {ok}/{self.NUM_SLOTS} slots to {os.path.basename(folder)}'
        if errors:
            msg += f' ({errors} errors)'
        self.statusBar().showMessage(msg)

    def _on_import_clicked(self) -> None:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self, 'Import recipe', str(PRESETS_DIR), 'JSON (*.json)'
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            name, values = self._json_to_values(payload)
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            QMessageBox.critical(self, 'Import failed', f'{type(e).__name__}: {e}')
            return

        panel = self._current_panel()
        panel.load_values(name, values)
        self.statusBar().showMessage(
            f'Loaded {os.path.basename(path)} into C{panel.slot} (not yet written to camera)'
        )

    def _on_import_all_clicked(self) -> None:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        folder = QFileDialog.getExistingDirectory(
            self, 'Import all slots from folder', str(PRESETS_DIR)
        )
        if not folder:
            return
        files = sorted(Path(folder).glob('*.json'))
        if not files:
            QMessageBox.information(self, 'No files', 'No JSON files found in that folder.')
            return
        loaded = 0
        for i, fpath in enumerate(files[: self.NUM_SLOTS]):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                name, values = self._json_to_values(payload)
                self.panels[i].load_values(name, values)
                loaded += 1
            except Exception as e:
                print(f'Import {fpath.name}: {e}')
        self.statusBar().showMessage(
            f'Imported {loaded} recipe(s) into C1–C{loaded} (not yet written to camera)'
        )

    # --------------------------------------------------------- json schema

    @staticmethod
    def _values_to_json(values: PresetUIValues, *, name: str, slot: int) -> dict:
        return {
            'name': name,
            'camera': 'X100VI',
            'slot': slot,
            'filmSimulation':    FilmSimLabels.get(values.filmSimulation, str(values.filmSimulation)),
            'dynamicRange':      DynRangeLabels.get(values.dynamicRange, str(values.dynamicRange)),
            'grainEffect':       GrainEffectLabels.get(values.grainEffect, str(values.grainEffect)),
            'colorChrome':       ColorChromeLabels.get(values.colorChrome, str(values.colorChrome)),
            'colorChromeFxBlue': ColorChromeFxBlueLabels.get(values.colorChromeFxBlue, str(values.colorChromeFxBlue)),
            'smoothSkin':        SmoothSkinLabels.get(values.smoothSkin, str(values.smoothSkin)),
            'whiteBalance':      WBModeLabels.get(values.whiteBalance, str(values.whiteBalance)),
            'wbShiftR':          values.wbShiftR,
            'wbShiftB':          values.wbShiftB,
            'wbColorTemp':       values.wbColorTemp,
            'highlightTone':     values.highlightTone,
            'shadowTone':        values.shadowTone,
            'color':             values.color,
            'sharpness':         values.sharpness,
            'noiseReduction':    values.noiseReduction,
            'clarity':           values.clarity,
            'dRangePriority':    DRangePriorityLabels.get(values.dRangePriority, str(values.dRangePriority)),
            'monoWC':            values.monoWC,
            'monoMG':            values.monoMG,
        }

    @staticmethod
    def _json_to_values(payload: dict) -> tuple[str, PresetUIValues]:
        def lookup(label_dict: dict, key: str, default: int = 0) -> int:
            raw = payload.get(key, default)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, str):
                return label_to_value(label_dict, raw, default=default)
            return default

        values = PresetUIValues(
            filmSimulation=lookup(FilmSimLabels, 'filmSimulation'),
            dynamicRange=lookup(DynRangeLabels, 'dynamicRange'),
            grainEffect=lookup(GrainEffectLabels, 'grainEffect'),
            colorChrome=lookup(ColorChromeLabels, 'colorChrome'),
            colorChromeFxBlue=lookup(ColorChromeFxBlueLabels, 'colorChromeFxBlue'),
            smoothSkin=lookup(SmoothSkinLabels, 'smoothSkin'),
            whiteBalance=lookup(WBModeLabels, 'whiteBalance'),
            wbShiftR=int(payload.get('wbShiftR', 0)),
            wbShiftB=int(payload.get('wbShiftB', 0)),
            wbColorTemp=int(payload.get('wbColorTemp', 6500)),
            highlightTone=float(payload.get('highlightTone', 0)),
            shadowTone=float(payload.get('shadowTone', 0)),
            color=float(payload.get('color', 0)),
            sharpness=float(payload.get('sharpness', 0)),
            noiseReduction=int(payload.get('noiseReduction', 0)),
            clarity=float(payload.get('clarity', 0)),
            exposure=0.0,
            dRangePriority=lookup(DRangePriorityLabels, 'dRangePriority'),
            monoWC=float(payload.get('monoWC', 0)),
            monoMG=float(payload.get('monoMG', 0)),
        )
        name = str(payload.get('name', ''))
        return name, values

    # ----------------------------------------------------------- teardown

    def closeEvent(self, event) -> None:
        if self._connected:
            self._disconnectRequested.emit()
        self._thread.quit()
        self._thread.wait(3000)
        super().closeEvent(event)


def _safe_filename(name: str) -> str:
    return (
        ''.join(c for c in name if c.isalnum() or c in '-_ ').strip() or 'recipe'
    )
