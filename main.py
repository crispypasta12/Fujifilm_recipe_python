"""FujiRecipe — desktop editor for Fujifilm film simulation recipes."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when launched from anywhere
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import STYLESHEET


def _load_fonts() -> None:
    """Load bundled Inter font if present in assets/fonts/."""
    fonts_dir = ROOT / 'assets' / 'fonts'
    for ttf in fonts_dir.glob('Inter*.ttf') if fonts_dir.exists() else []:
        QFontDatabase.addApplicationFont(str(ttf))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName('FujiRecipe')
    app.setStyle('Fusion')

    _load_fonts()

    # Use Inter if it was loaded; the stylesheet font-family stack falls back
    # to Segoe UI automatically if Inter is not available.
    if 'Inter' in QFontDatabase.families():
        app.setFont(QFont('Inter', 10))

    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
