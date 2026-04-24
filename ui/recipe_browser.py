"""Recipe Browser — modeless dialog for browsing and loading built-in / user recipes.

Opens alongside the main window.  Signals emitted:
    recipeLoadRequested(slot: int, name: str, values: PresetUIValues)
        → main window loads values into panel (no write)
    recipeWriteRequested(slot: int, name: str, values: PresetUIValues)
        → main window loads values into panel AND writes to camera

Part-3 additions
----------------
* Recently Used pinned section — shown at the top of the list when no search
  query / film-sim filter is active and the view is not "My Recipes".
* Export Card… button — renders a 900×540 PNG recipe card via recipe_card.py.
"""

from __future__ import annotations

import re
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

import recipes.user_store as user_store
from profile.enums import (
    DynRangeLabels,
    FilmSimLabels,
    GrainEffectLabels,
    SIM_COLORS,
    WBModeLabels,
)
from profile.preset_translate import PresetUIValues
from recipes.loader import Recipe, SENSOR_LABELS, load_catalog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OWS = {0: "Off", 1: "Weak", 2: "Strong"}

# Sentinel — not a real folder, handled specially
_MY_RECIPES_KEY = "my-recipes"

# All film sims in display order for the filter dropdown
_FILM_SIM_FILTER_ITEMS: list[tuple[str, Optional[int]]] = [
    ("All Film Sims", None),
] + [(label, value) for value, label in FilmSimLabels.items()]

# Maximum number of "Recently Used" items shown in the pinned section
_MAX_PINNED_RECENT = 8

# Dim colour for section-header items (non-selectable list rows)
_SECTION_HDR_COLOR = QColor("#888894")
_SECTION_HDR_BG    = QColor("#1a1a1e")


def _ows(val: int) -> str:
    return _OWS.get(val, "—")


def _short_title(title: str) -> str:
    """Strip the '— Fujifilm X100VI Film Simulation Recipe' suffix."""
    return re.sub(r"\s*[—\-–]+\s*Fujifilm.*", "", title).strip() or title


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class RecipeBrowserDialog(QDialog):
    """Modeless recipe browser dialog."""

    # slot (1-7), display name, PresetUIValues
    recipeLoadRequested  = pyqtSignal(int, str, object)
    recipeWriteRequested = pyqtSignal(int, str, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Recipe Browser")
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.resize(960, 640)
        self.setModal(False)

        self._recipes: list[Recipe] = []          # full catalog for current sensor
        self._visible: list[Recipe] = []          # after search + film-sim filter
        self._recent:  list[Recipe] = []          # recently-used entries (Part 3)

        # Maps each QListWidget row index → Recipe (or None for header/separator rows)
        self._item_map: list[Optional[Recipe]] = []

        self._current_pixmap: Optional[QPixmap] = None  # for resize rescaling
        self._is_user_view = False  # True when "My Recipes" is active

        self._build_ui()
        self._wire_events()
        self._load_sensor("x-trans-v")

    # ------------------------------------------------------------------ build

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        lbl_sensor = QLabel("Sensor:")
        self.sensorCombo = QComboBox()
        self.sensorCombo.setFixedWidth(130)
        for label in SENSOR_LABELS:
            self.sensorCombo.addItem(label, userData=SENSOR_LABELS[label])
        # "My Recipes" is a special local source — always last
        self.sensorCombo.addItem("My Recipes", userData=_MY_RECIPES_KEY)

        # Film simulation filter
        lbl_sim = QLabel("Film Sim:")
        self.filmSimFilter = QComboBox()
        self.filmSimFilter.setFixedWidth(160)
        for label, value in _FILM_SIM_FILTER_ITEMS:
            self.filmSimFilter.addItem(label, userData=value)

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Search recipes…")
        self.searchEdit.setClearButtonEnabled(True)

        self.countLabel = QLabel()
        self.countLabel.setProperty("role", "dim")

        # "+ New Recipe" button — only meaningful for My Recipes view
        self.newRecipeBtn = QPushButton("+ New Recipe")
        self.newRecipeBtn.setVisible(False)

        top.addWidget(lbl_sensor)
        top.addWidget(self.sensorCombo)
        top.addSpacing(4)
        top.addWidget(lbl_sim)
        top.addWidget(self.filmSimFilter)
        top.addSpacing(8)
        top.addWidget(self.searchEdit, 1)
        top.addWidget(self.countLabel)
        top.addSpacing(4)
        top.addWidget(self.newRecipeBtn)
        root.addLayout(top)

        # ── Splitter: list | detail ───────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left — recipe list
        self.recipeList = QListWidget()
        self.recipeList.setObjectName("RecipeList")
        self.recipeList.setMinimumWidth(200)
        self.recipeList.setMaximumWidth(320)
        self.recipeList.setIconSize(QSize(48, 48))
        self.recipeList.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        splitter.addWidget(self.recipeList)

        # Right — detail panel
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(12, 0, 0, 0)
        detail_layout.setSpacing(10)

        # Sample image
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setMinimumHeight(160)
        self.imageLabel.setMaximumHeight(280)
        self.imageLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.imageLabel.setObjectName("RecipeImage")
        detail_layout.addWidget(self.imageLabel)

        # Recipe title
        self.titleLabel = QLabel()
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setObjectName("RecipeTitle")
        detail_layout.addWidget(self.titleLabel)

        # Source link (dim)
        self.sourceLabel = QLabel()
        self.sourceLabel.setProperty("role", "dim")
        self.sourceLabel.setWordWrap(True)
        self.sourceLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        detail_layout.addWidget(self.sourceLabel)

        # Params grid inside a scroll area
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        params_host = QWidget()
        self._params_grid = QGridLayout(params_host)
        self._params_grid.setHorizontalSpacing(16)
        self._params_grid.setVerticalSpacing(3)
        self._params_grid.setColumnStretch(1, 1)
        scroll.setWidget(params_host)
        detail_layout.addWidget(scroll, 1)

        # ── Action bar ───────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("role", "divider")
        detail_layout.addWidget(divider)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        # Delete button — only visible for user recipes
        self.deleteBtn = QPushButton("Delete")
        self.deleteBtn.setVisible(False)
        action_bar.addWidget(self.deleteBtn)

        # Export Card button — always present, enabled when a recipe is selected
        self.exportCardBtn = QPushButton("Export Card…")
        self.exportCardBtn.setEnabled(False)
        action_bar.addWidget(self.exportCardBtn)

        action_bar.addStretch(1)
        action_bar.addWidget(QLabel("Slot:"))

        self.slotCombo = QComboBox()
        self.slotCombo.setFixedWidth(60)
        for i in range(1, 8):
            self.slotCombo.addItem(f"C{i}", userData=i)
        action_bar.addWidget(self.slotCombo)

        self.loadBtn = QPushButton("Load into Slot")
        self.loadBtn.setEnabled(False)
        action_bar.addWidget(self.loadBtn)

        self.writeBtn = QPushButton("Write to Camera")
        self.writeBtn.setProperty("role", "primary")
        self.writeBtn.setEnabled(False)
        action_bar.addWidget(self.writeBtn)

        detail_layout.addLayout(action_bar)

        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

    # ------------------------------------------------------------------ wire

    def _wire_events(self) -> None:
        self.sensorCombo.currentIndexChanged.connect(self._on_sensor_changed)
        self.filmSimFilter.currentIndexChanged.connect(self._apply_filter)
        self.searchEdit.textChanged.connect(self._apply_filter)
        self.recipeList.currentRowChanged.connect(self._on_row_changed)
        self.loadBtn.clicked.connect(self._on_load_clicked)
        self.writeBtn.clicked.connect(self._on_write_clicked)
        self.newRecipeBtn.clicked.connect(self._on_new_recipe_clicked)
        self.deleteBtn.clicked.connect(self._on_delete_clicked)
        self.exportCardBtn.clicked.connect(self._on_export_card_clicked)

    # ------------------------------------------------------------------ data

    def _load_sensor(self, sensor_folder: str) -> None:
        self._is_user_view = (sensor_folder == _MY_RECIPES_KEY)
        self.newRecipeBtn.setVisible(self._is_user_view)

        if self._is_user_view:
            self._recipes = user_store.list_recipes()
            # No recently-used pinning inside the My Recipes view
        else:
            self._recipes = load_catalog(sensor_folder)
            self._recent  = user_store.load_recent()[:_MAX_PINNED_RECENT]

        self._apply_filter()

    def _apply_filter(self) -> None:
        query      = self.searchEdit.text().strip().lower()
        sim_filter: Optional[int] = self.filmSimFilter.currentData()

        filtered = self._recipes
        if sim_filter is not None:
            filtered = [r for r in filtered if r.ui_values.filmSimulation == sim_filter]
        if query:
            filtered = [
                r for r in filtered
                if query in r.title.lower() or query in r.slug
            ]

        self._visible = filtered

        # Show recently-used pinned section only when no active filter/search
        show_recent = (
            not query
            and sim_filter is None
            and not self._is_user_view
            and bool(self._recent)
        )

        # ── Rebuild QListWidget + item_map ───────────────────────────────────
        self._item_map = []
        self.recipeList.blockSignals(True)
        self.recipeList.clear()

        if show_recent:
            # Section header (non-selectable)
            self._item_map.append(None)
            hdr = QListWidgetItem("  Recently Used")
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)
            hdr.setForeground(QBrush(_SECTION_HDR_COLOR))
            hdr.setBackground(QBrush(_SECTION_HDR_BG))
            hdr_font = QFont()
            hdr_font.setPixelSize(10)
            hdr.setFont(hdr_font)
            hdr.setSizeHint(QSize(0, 22))
            self.recipeList.addItem(hdr)

            for r in self._recent:
                self._item_map.append(r)
                item = QListWidgetItem()
                item.setIcon(self._make_thumb(r))
                item.setText(f"{_short_title(r.title)}\n{FilmSimLabels.get(r.ui_values.filmSimulation, '')}")
                item.setSizeHint(QSize(0, 64))
                item.setToolTip(r.source)
                self.recipeList.addItem(item)

            # Thin separator
            self._item_map.append(None)
            sep = QListWidgetItem()
            sep.setFlags(Qt.ItemFlag.NoItemFlags)
            sep.setSizeHint(QSize(0, 8))
            self.recipeList.addItem(sep)

        for r in filtered:
            self._item_map.append(r)
            item = QListWidgetItem()
            item.setIcon(self._make_thumb(r))
            item.setText(f"{_short_title(r.title)}\n{FilmSimLabels.get(r.ui_values.filmSimulation, '')}")
            item.setSizeHint(QSize(0, 64))
            item.setToolTip(r.source)
            self.recipeList.addItem(item)

        self.recipeList.blockSignals(False)

        n = len(self._visible)
        self.countLabel.setText(f"{n} recipe{'s' if n != 1 else ''}")

        # Select the first real (non-header) item
        first_idx = next(
            (i for i, r in enumerate(self._item_map) if r is not None), -1
        )
        if first_idx >= 0:
            self.recipeList.setCurrentRow(first_idx)
            self._show_detail(self._item_map[first_idx])   # type: ignore[arg-type]
        else:
            self._clear_detail()

    # --------------------------------------------------------- thumbnails

    _THUMB = 48   # thumbnail edge length in pixels

    def _make_thumb(self, recipe: Recipe) -> QIcon:
        """Return a 48×48 QIcon for *recipe*.

        If the recipe has a photo, it is centre-cropped to a square.
        Otherwise a small dark swatch with a film-sim accent stripe is used
        so that all list items stay the same height regardless of whether an
        image is available.
        """
        T = self._THUMB
        pix: Optional[QPixmap] = None

        if recipe.image_path is not None:
            try:
                src = QPixmap(str(recipe.image_path))
                if not src.isNull():
                    scaled = src.scaled(
                        T, T,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    sx = (scaled.width()  - T) // 2
                    sy = (scaled.height() - T) // 2
                    pix = scaled.copy(sx, sy, T, T)
            except Exception:
                pass

        if pix is None:
            # Coloured accent swatch — dark bg + 4 px film-sim stripe at bottom
            accent_hex = SIM_COLORS.get(recipe.ui_values.filmSimulation, '#444450')
            pix = QPixmap(T, T)
            pix.fill(QColor('#1e1e26'))
            painter = QPainter(pix)
            painter.fillRect(0, T - 4, T, 4, QColor(accent_hex))
            painter.end()

        return QIcon(pix)

    # --------------------------------------------------------- event handlers

    def _on_sensor_changed(self) -> None:
        folder = self.sensorCombo.currentData()
        if folder:
            self._load_sensor(folder)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._item_map):
            recipe = self._item_map[row]
            if recipe is not None:
                self._show_detail(recipe)
                self.loadBtn.setEnabled(True)
                self.writeBtn.setEnabled(True)
                return
        self._clear_detail()

    def _get_selected_recipe(self) -> Optional[Recipe]:
        """Return the Recipe for the currently selected list row, or None."""
        row = self.recipeList.currentRow()
        if 0 <= row < len(self._item_map):
            return self._item_map[row]
        return None

    def _on_load_clicked(self) -> None:
        recipe = self._get_selected_recipe()
        if recipe is None:
            return
        slot = self.slotCombo.currentData()
        name = _short_title(recipe.title)
        user_store.record_used(recipe.slug, name, recipe.ui_values)
        self.recipeLoadRequested.emit(slot, name, recipe.ui_values)

    def _on_write_clicked(self) -> None:
        recipe = self._get_selected_recipe()
        if recipe is None:
            return
        slot = self.slotCombo.currentData()
        name = _short_title(recipe.title)
        user_store.record_used(recipe.slug, name, recipe.ui_values)
        self.recipeWriteRequested.emit(slot, name, recipe.ui_values)

    def _on_new_recipe_clicked(self) -> None:
        from .recipe_creator import RecipeCreatorDialog
        dlg = RecipeCreatorDialog(parent=self)
        dlg.recipeSaved.connect(self._on_recipe_saved)
        dlg.exec()

    def _on_recipe_saved(self, slug: str, name: str, values) -> None:
        """Called after a recipe is saved from RecipeCreatorDialog."""
        idx = self.sensorCombo.findData(_MY_RECIPES_KEY)
        if idx >= 0:
            self.sensorCombo.blockSignals(True)
            self.sensorCombo.setCurrentIndex(idx)
            self.sensorCombo.blockSignals(False)
        self._load_sensor(_MY_RECIPES_KEY)
        for i, r in enumerate(self._item_map):
            if r is not None and r.slug == slug:
                self.recipeList.setCurrentRow(i)
                break

    def _on_delete_clicked(self) -> None:
        recipe = self._get_selected_recipe()
        if recipe is None:
            return
        name = _short_title(recipe.title)
        answer = QMessageBox.question(
            self,
            "Delete recipe",
            f'Permanently delete "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        user_store.delete_recipe(recipe.slug)
        self._load_sensor(_MY_RECIPES_KEY)

    def _on_export_card_clicked(self) -> None:
        recipe = self._get_selected_recipe()
        if recipe is None:
            return

        from .recipe_card import generate_recipe_card

        name      = _short_title(recipe.title)
        safe_name = re.sub(r"[^\w\s\-]", "", name).strip().replace(" ", "_") or "recipe"
        path, _   = QFileDialog.getSaveFileName(
            self,
            "Export Recipe Card",
            f"{safe_name}_card.png",
            "PNG Image (*.png)",
        )
        if not path:
            return

        pix = generate_recipe_card(recipe)
        if not pix.save(path, "PNG"):
            QMessageBox.warning(self, "Export failed", f"Could not save to:\n{path}")

    # --------------------------------------------------------- detail display

    def _clear_detail(self) -> None:
        self._current_pixmap = None
        self.imageLabel.clear()
        self.imageLabel.setText("No recipe selected")
        self.titleLabel.clear()
        self.sourceLabel.clear()
        self._clear_params_grid()
        self.loadBtn.setEnabled(False)
        self.writeBtn.setEnabled(False)
        self.exportCardBtn.setEnabled(False)
        self.deleteBtn.setVisible(False)

    def _show_detail(self, recipe: Recipe) -> None:
        # Image
        if recipe.image_path and recipe.image_path.exists():
            pix = QPixmap(str(recipe.image_path))
            if not pix.isNull():
                self._current_pixmap = pix
                self._refresh_image()
            else:
                self._current_pixmap = None
                self.imageLabel.setText("[image unavailable]")
        else:
            self._current_pixmap = None
            self.imageLabel.setText("[no image]")

        self.titleLabel.setText(_short_title(recipe.title))
        self.sourceLabel.setText(recipe.source)

        # Delete button — only for user recipes (not for recently-used entries
        # even if they originated from My Recipes, as sensor=="recent" here)
        self.deleteBtn.setVisible(recipe.sensor == _MY_RECIPES_KEY)

        # Params
        self._clear_params_grid()
        v = recipe.ui_values
        rows = [
            ("Film Simulation",  FilmSimLabels.get(v.filmSimulation, "—")),
            ("Dynamic Range",    DynRangeLabels.get(v.dynamicRange, "—")),
            ("Grain Effect",     GrainEffectLabels.get(v.grainEffect, "—")),
            ("Color Chrome",     _ows(v.colorChrome)),
            ("CC FX Blue",       _ows(v.colorChromeFxBlue)),
            ("White Balance",    WBModeLabels.get(v.whiteBalance, "—")),
            ("WB Shift R / B",   f"{v.wbShiftR:+d} / {v.wbShiftB:+d}"),
            ("Highlight",        f"{v.highlightTone:+.1f}"),
            ("Shadow",           f"{v.shadowTone:+.1f}"),
            ("Color",            f"{v.color:+.1f}"),
            ("Sharpness",        f"{v.sharpness:+.1f}"),
            ("Noise Reduction",  f"{v.noiseReduction:+d}"),
            ("Clarity",          f"{v.clarity:+.1f}"),
        ]
        for i, (label, value) in enumerate(rows):
            lbl = QLabel(label + ":")
            lbl.setProperty("role", "paramLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val = QLabel(str(value))
            val.setProperty("role", "paramValue")
            self._params_grid.addWidget(lbl, i, 0)
            self._params_grid.addWidget(val, i, 1)

        self.loadBtn.setEnabled(True)
        self.writeBtn.setEnabled(True)
        self.exportCardBtn.setEnabled(True)

    def _clear_params_grid(self) -> None:
        while self._params_grid.count():
            item = self._params_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_image(self) -> None:
        if self._current_pixmap is None:
            return
        w = self.imageLabel.width() or 500
        h = self.imageLabel.maximumHeight()
        scaled = self._current_pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.imageLabel.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_image()

    # ------------------------------------------------------------------ public

    def refresh_user_recipes(self) -> None:
        """Reload user recipes if the My Recipes view is currently active."""
        if self._is_user_view:
            self._load_sensor(_MY_RECIPES_KEY)
