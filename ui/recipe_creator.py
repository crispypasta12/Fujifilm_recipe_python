"""Recipe Creator Dialog — compose and save a custom film simulation recipe.

Opens as a modal dialog.  Pre-populate it with existing values (e.g. from a
camera slot) or start from scratch.

Signal emitted on successful save:
    recipeSaved(slug: str, name: str, values: PresetUIValues)
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import recipes.user_store as user_store
from profile.preset_translate import PresetUIValues
from .preset_panel import PresetPanel


class RecipeCreatorDialog(QDialog):
    """Modal dialog for composing and saving a custom user recipe."""

    # slug, display name, PresetUIValues
    recipeSaved = pyqtSignal(str, str, object)

    def __init__(
        self,
        initial_name: str = "",
        initial_values: Optional[PresetUIValues] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Recipe")
        self.resize(600, 760)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Embedded preset panel ────────────────────────────────────────────
        # Re-use PresetPanel (slot=0 is a dummy — write button is hidden).
        self._panel = PresetPanel(slot=0)
        self._panel.slotTag.hide()
        self._panel.writeButton.hide()
        self._panel.saveRecipeButton.hide()   # hide the panel's own save btn

        if initial_values is not None:
            self._panel.load_values(initial_name, initial_values)
        elif initial_name:
            self._panel.nameEdit.setText(initial_name)

        root.addWidget(self._panel, 1)

        # ── Divider ──────────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("role", "divider")
        root.addWidget(divider)

        # ── Action bar ───────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setContentsMargins(16, 12, 16, 12)
        bar.setSpacing(8)
        bar.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        self._save_btn = QPushButton("Save Recipe")
        self._save_btn.setProperty("role", "primary")
        self._save_btn.clicked.connect(self._on_save)

        bar.addWidget(cancel_btn)
        bar.addWidget(self._save_btn)
        root.addLayout(bar)

    # ------------------------------------------------------------------ slots

    def _on_save(self) -> None:
        name, values = self._panel.dump_values()
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a recipe name.")
            self._panel.nameEdit.setFocus()
            return
        slug = user_store.save_recipe(name, values)
        self.recipeSaved.emit(slug, name, values)
        self.accept()
