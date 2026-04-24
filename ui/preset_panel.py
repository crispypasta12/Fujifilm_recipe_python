"""Per-slot preset display/edit widget."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# Scroll-safe spin boxes — ignore wheel events unless the widget has focus.
# This prevents accidentally changing values while scrolling the panel.
# ---------------------------------------------------------------------------

class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

from profile.enums import (
    ColorChromeFxBlueLabels,
    ColorChromeLabels,
    DRangePriorityLabels,
    DynRangeLabels,
    FilmSimLabels,
    GrainEffectLabels,
    MONOCHROME_SIMS,
    SIM_COLORS,
    SmoothSkinLabels,
    WBMode,
    WBModeLabels,
)
from profile.preset_translate import PresetUIValues


def _fill_combo(combo: QComboBox, label_dict: dict) -> None:
    for value, label in label_dict.items():
        combo.addItem(label, userData=value)


def _select_combo_value(combo: QComboBox, value: int) -> None:
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return
    if combo.count() > 0:
        combo.setCurrentIndex(0)


class PresetPanel(QWidget):
    """One preset slot (C1..C7) — name + all parameters + write button."""

    writeRequested        = pyqtSignal(int)       # slot number
    dirtyChanged          = pyqtSignal(int, bool)  # slot, is_dirty
    saveAsRecipeRequested = pyqtSignal(int)        # slot number

    def __init__(self, slot: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName('PresetPanel')
        self.slot = slot
        self._dirty = False
        self._build_ui()
        self._wire_events()
        self._update_mono_visibility()
        self._update_color_temp_enabled()
        self._update_sim_dot()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Film-sim accent stripe — 3 px colour bar at the top of the panel.
        # Colour updates dynamically in _update_sim_dot() whenever the
        # film simulation selection changes.
        self.simAccentBar = QFrame()
        self.simAccentBar.setObjectName('simAccentBar')
        self.simAccentBar.setFixedHeight(3)
        self.simAccentBar.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self.simAccentBar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # --- Header: slot tag + name editor
        header = QHBoxLayout()
        header.setSpacing(12)

        self.slotTag = QLabel(f'C{self.slot}')
        self.slotTag.setProperty('role', 'slotTag')

        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText('Preset name')
        self.nameEdit.setMaxLength(32)

        header.addWidget(self.slotTag)
        header.addWidget(self.nameEdit, 1)
        root.addLayout(header)

        divider = QFrame()
        divider.setProperty('role', 'divider')
        divider.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider)

        # --- Film / Base
        gb_base = QGroupBox('Film base')
        base_grid = QGridLayout(gb_base)
        base_grid.setHorizontalSpacing(12)
        base_grid.setVerticalSpacing(8)

        self.filmSimCombo = NoScrollComboBox()
        _fill_combo(self.filmSimCombo, FilmSimLabels)

        self.dynRangeCombo = NoScrollComboBox()
        _fill_combo(self.dynRangeCombo, DynRangeLabels)

        self.dRangePriorityCombo = NoScrollComboBox()
        _fill_combo(self.dRangePriorityCombo, DRangePriorityLabels)

        # Film-sim dot indicator — coloured ● that matches the selected simulation
        self.filmSimDot = QLabel('●')
        self.filmSimDot.setObjectName('filmSimDot')
        self.filmSimDot.setFixedWidth(14)
        self.filmSimDot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sim_label_row = QWidget()
        sim_label_lay = QHBoxLayout(sim_label_row)
        sim_label_lay.setContentsMargins(0, 0, 0, 0)
        sim_label_lay.setSpacing(5)
        sim_label_lay.addWidget(self.filmSimDot)
        sim_label_lay.addWidget(QLabel('Film Simulation'))

        base_grid.addWidget(sim_label_row, 0, 0)
        base_grid.addWidget(self.filmSimCombo, 0, 1)
        base_grid.addWidget(QLabel('Dynamic Range'), 1, 0)
        base_grid.addWidget(self.dynRangeCombo, 1, 1)
        base_grid.addWidget(QLabel('D Range Priority'), 2, 0)
        base_grid.addWidget(self.dRangePriorityCombo, 2, 1)
        root.addWidget(gb_base)

        # --- Effects
        gb_fx = QGroupBox('Effects')
        fx_grid = QGridLayout(gb_fx)
        fx_grid.setHorizontalSpacing(12)
        fx_grid.setVerticalSpacing(8)

        self.grainCombo = NoScrollComboBox()
        _fill_combo(self.grainCombo, GrainEffectLabels)
        self.colorChromeCombo = NoScrollComboBox()
        _fill_combo(self.colorChromeCombo, ColorChromeLabels)
        self.ccFxBlueCombo = NoScrollComboBox()
        _fill_combo(self.ccFxBlueCombo, ColorChromeFxBlueLabels)
        self.smoothSkinCombo = NoScrollComboBox()
        _fill_combo(self.smoothSkinCombo, SmoothSkinLabels)

        fx_grid.addWidget(QLabel('Grain Effect'), 0, 0)
        fx_grid.addWidget(self.grainCombo, 0, 1)
        fx_grid.addWidget(QLabel('Color Chrome'), 1, 0)
        fx_grid.addWidget(self.colorChromeCombo, 1, 1)
        fx_grid.addWidget(QLabel('CC FX Blue'), 2, 0)
        fx_grid.addWidget(self.ccFxBlueCombo, 2, 1)
        fx_grid.addWidget(QLabel('Smooth Skin'), 3, 0)
        fx_grid.addWidget(self.smoothSkinCombo, 3, 1)
        root.addWidget(gb_fx)

        # --- White balance
        gb_wb = QGroupBox('White balance')
        wb_grid = QGridLayout(gb_wb)
        wb_grid.setHorizontalSpacing(12)
        wb_grid.setVerticalSpacing(8)

        self.wbCombo = NoScrollComboBox()
        _fill_combo(self.wbCombo, WBModeLabels)
        self.wbShiftR = NoScrollSpinBox()
        self.wbShiftR.setRange(-9, 9)
        self.wbShiftB = NoScrollSpinBox()
        self.wbShiftB.setRange(-9, 9)
        self.colorTempSpin = NoScrollSpinBox()
        self.colorTempSpin.setRange(2500, 10000)
        self.colorTempSpin.setSingleStep(50)
        self.colorTempSpin.setSuffix(' K')

        wb_grid.addWidget(QLabel('White Balance'), 0, 0)
        wb_grid.addWidget(self.wbCombo, 0, 1)
        wb_grid.addWidget(QLabel('Color Temp'), 1, 0)
        wb_grid.addWidget(self.colorTempSpin, 1, 1)
        wb_grid.addWidget(QLabel('Shift R'), 2, 0)
        wb_grid.addWidget(self.wbShiftR, 2, 1)
        wb_grid.addWidget(QLabel('Shift B'), 3, 0)
        wb_grid.addWidget(self.wbShiftB, 3, 1)
        root.addWidget(gb_wb)

        # --- Tone
        gb_tone = QGroupBox('Tone')
        tone_grid = QGridLayout(gb_tone)
        tone_grid.setHorizontalSpacing(12)
        tone_grid.setVerticalSpacing(8)

        def make_tone() -> NoScrollDoubleSpinBox:
            w = NoScrollDoubleSpinBox()
            w.setRange(-4.0, 4.0)
            w.setSingleStep(0.5)
            w.setDecimals(1)
            return w

        self.highlightSpin = make_tone()
        self.shadowSpin = make_tone()
        self.colorSpin = make_tone()
        self.sharpSpin = make_tone()
        self.claritySpin = make_tone()
        self.claritySpin.setRange(-5.0, 5.0)

        self.nrSpin = NoScrollSpinBox()
        self.nrSpin.setRange(-4, 4)

        tone_grid.addWidget(QLabel('Highlight'), 0, 0)
        tone_grid.addWidget(self.highlightSpin, 0, 1)
        tone_grid.addWidget(QLabel('Shadow'), 1, 0)
        tone_grid.addWidget(self.shadowSpin, 1, 1)
        tone_grid.addWidget(QLabel('Color'), 2, 0)
        tone_grid.addWidget(self.colorSpin, 2, 1)
        tone_grid.addWidget(QLabel('Sharpness'), 3, 0)
        tone_grid.addWidget(self.sharpSpin, 3, 1)
        tone_grid.addWidget(QLabel('Noise Reduction'), 4, 0)
        tone_grid.addWidget(self.nrSpin, 4, 1)
        tone_grid.addWidget(QLabel('Clarity'), 5, 0)
        tone_grid.addWidget(self.claritySpin, 5, 1)
        root.addWidget(gb_tone)

        # --- Monochrome
        self.monoGroup = QGroupBox('Monochromatic')
        mono_grid = QGridLayout(self.monoGroup)
        mono_grid.setHorizontalSpacing(12)
        mono_grid.setVerticalSpacing(8)

        self.monoWCSpin = NoScrollDoubleSpinBox()
        self.monoWCSpin.setRange(-9.0, 9.0)
        self.monoWCSpin.setSingleStep(0.5)
        self.monoWCSpin.setDecimals(1)
        self.monoMGSpin = NoScrollDoubleSpinBox()
        self.monoMGSpin.setRange(-9.0, 9.0)
        self.monoMGSpin.setSingleStep(0.5)
        self.monoMGSpin.setDecimals(1)
        mono_grid.addWidget(QLabel('Warm / Cool'), 0, 0)
        mono_grid.addWidget(self.monoWCSpin, 0, 1)
        mono_grid.addWidget(QLabel('Magenta / Green'), 1, 0)
        mono_grid.addWidget(self.monoMGSpin, 1, 1)
        root.addWidget(self.monoGroup)

        # --- Actions
        root.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.saveRecipeButton = QPushButton('Save as Recipe')
        actions.addWidget(self.saveRecipeButton)
        self.writeButton = QPushButton(f'Write to C{self.slot}')
        self.writeButton.setProperty('role', 'primary')
        actions.addWidget(self.writeButton)
        root.addLayout(actions)

        root.addStretch(1)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _wire_events(self) -> None:
        self.filmSimCombo.currentIndexChanged.connect(self._update_mono_visibility)
        self.filmSimCombo.currentIndexChanged.connect(self._update_sim_dot)
        self.wbCombo.currentIndexChanged.connect(self._update_color_temp_enabled)
        self.writeButton.clicked.connect(lambda: self.writeRequested.emit(self.slot))
        self.saveRecipeButton.clicked.connect(
            lambda: self.saveAsRecipeRequested.emit(self.slot)
        )

        for combo in (
            self.filmSimCombo, self.dynRangeCombo, self.dRangePriorityCombo,
            self.grainCombo, self.colorChromeCombo, self.ccFxBlueCombo,
            self.smoothSkinCombo, self.wbCombo,
        ):
            combo.currentIndexChanged.connect(self._mark_dirty)

        for spin in (self.wbShiftR, self.wbShiftB, self.colorTempSpin, self.nrSpin):
            spin.valueChanged.connect(self._mark_dirty)

        for dspin in (
            self.highlightSpin, self.shadowSpin, self.colorSpin, self.sharpSpin,
            self.claritySpin, self.monoWCSpin, self.monoMGSpin,
        ):
            dspin.valueChanged.connect(self._mark_dirty)

        self.nameEdit.textChanged.connect(self._mark_dirty)

    # --------------------------------------------------------- dirty tracking

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def _mark_dirty(self, *_) -> None:
        if not self._dirty:
            self._dirty = True
            self.dirtyChanged.emit(self.slot, True)

    def _clear_dirty(self) -> None:
        if self._dirty:
            self._dirty = False
            self.dirtyChanged.emit(self.slot, False)

    # --------------------------------------------------------- visibility

    def _current_film_sim(self) -> int:
        data = self.filmSimCombo.currentData()
        return int(data) if data is not None else 0

    def _update_mono_visibility(self) -> None:
        is_mono = self._current_film_sim() in MONOCHROME_SIMS
        self.monoGroup.setVisible(is_mono)
        self.colorSpin.setEnabled(not is_mono)

    def _update_sim_dot(self) -> None:
        """Update all sim-colour indicators to match the selected simulation."""
        color = SIM_COLORS.get(self._current_film_sim(), '#666670')

        # Coloured dot beside the Film Simulation combo label
        self.filmSimDot.setStyleSheet(f'color: {color}; font-size: 11px;')

        # 3 px accent stripe at the top of the panel
        self.simAccentBar.setStyleSheet(f'background-color: {color}; border: none;')

        # Slot tag — left border colour matches the active film sim
        self.slotTag.setStyleSheet(
            f'font-size: 15pt; font-weight: 700; color: {color};'
            f' padding: 2px 8px 2px 14px; border: none;'
            f' border-left: 3px solid {color}; background: transparent;'
        )

    def _update_color_temp_enabled(self) -> None:
        wb = self.wbCombo.currentData()
        self.colorTempSpin.setEnabled(wb == WBMode.ColorTemp)

    # -------------------------------------------------------- load / dump

    def load_values(self, name: str, values: PresetUIValues) -> None:
        """Populate widgets from a PresetUIValues snapshot."""
        blockers = [
            self.nameEdit, self.filmSimCombo, self.dynRangeCombo, self.dRangePriorityCombo,
            self.grainCombo, self.colorChromeCombo, self.ccFxBlueCombo, self.smoothSkinCombo,
            self.wbCombo, self.wbShiftR, self.wbShiftB, self.colorTempSpin,
            self.highlightSpin, self.shadowSpin, self.colorSpin, self.sharpSpin,
            self.nrSpin, self.claritySpin, self.monoWCSpin, self.monoMGSpin,
        ]
        for w in blockers:
            w.blockSignals(True)

        try:
            self.nameEdit.setText(name)
            _select_combo_value(self.filmSimCombo, values.filmSimulation)
            _select_combo_value(self.dynRangeCombo, values.dynamicRange)
            _select_combo_value(self.dRangePriorityCombo, values.dRangePriority)
            _select_combo_value(self.grainCombo, values.grainEffect)
            _select_combo_value(self.colorChromeCombo, values.colorChrome)
            _select_combo_value(self.ccFxBlueCombo, values.colorChromeFxBlue)
            _select_combo_value(self.smoothSkinCombo, values.smoothSkin)
            _select_combo_value(self.wbCombo, values.whiteBalance)
            self.wbShiftR.setValue(int(values.wbShiftR))
            self.wbShiftB.setValue(int(values.wbShiftB))
            self.colorTempSpin.setValue(int(values.wbColorTemp or 6500))
            self.highlightSpin.setValue(float(values.highlightTone))
            self.shadowSpin.setValue(float(values.shadowTone))
            self.colorSpin.setValue(float(values.color))
            self.sharpSpin.setValue(float(values.sharpness))
            self.nrSpin.setValue(int(values.noiseReduction))
            self.claritySpin.setValue(float(values.clarity))
            self.monoWCSpin.setValue(float(values.monoWC))
            self.monoMGSpin.setValue(float(values.monoMG))
        finally:
            for w in blockers:
                w.blockSignals(False)

        self._update_mono_visibility()
        self._update_color_temp_enabled()
        self._update_sim_dot()
        self._clear_dirty()

    def dump_values(self) -> tuple[str, PresetUIValues]:
        """Read widgets back into a (name, PresetUIValues) tuple."""
        v = PresetUIValues(
            filmSimulation=int(self.filmSimCombo.currentData() or 0),
            dynamicRange=int(self.dynRangeCombo.currentData() or 0),
            grainEffect=int(self.grainCombo.currentData() or 0),
            smoothSkin=int(self.smoothSkinCombo.currentData() or 0),
            colorChrome=int(self.colorChromeCombo.currentData() or 0),
            colorChromeFxBlue=int(self.ccFxBlueCombo.currentData() or 0),
            whiteBalance=int(self.wbCombo.currentData() or 0),
            wbShiftR=self.wbShiftR.value(),
            wbShiftB=self.wbShiftB.value(),
            wbColorTemp=self.colorTempSpin.value(),
            highlightTone=self.highlightSpin.value(),
            shadowTone=self.shadowSpin.value(),
            color=self.colorSpin.value(),
            sharpness=self.sharpSpin.value(),
            noiseReduction=self.nrSpin.value(),
            clarity=self.claritySpin.value(),
            exposure=0.0,
            dRangePriority=int(self.dRangePriorityCombo.currentData() or 0),
            monoWC=self.monoWCSpin.value(),
            monoMG=self.monoMGSpin.value(),
        )
        return self.nameEdit.text().strip(), v
