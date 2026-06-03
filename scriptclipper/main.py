from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from scriptclipper.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ScriptClipper")

    style_path = Path(__file__).resolve().parent / "resources" / "style.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
