"""FujiRecipe — desktop editor for Fujifilm film simulation recipes."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when launched from anywhere
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName('FujiRecipe')
    app.setStyle('Fusion')
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
