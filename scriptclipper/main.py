from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from scriptclipper.core.resources import resource_path
from scriptclipper.ui.main_window import MainWindow


def app_icon_path():
    return resource_path("assets", "icons", "app-icon.ico")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ScriptClipper")
    icon_path = app_icon_path()
    app_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    style_path = resource_path("scriptclipper", "resources", "style.qss")
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    window = MainWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
