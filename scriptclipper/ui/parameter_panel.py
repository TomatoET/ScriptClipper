from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget


class ParameterPanel(QWidget):
    settings_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._loading = False

        self.title = QLabel("参数调节")
        self.title.setObjectName("PanelTitle")
        self.aspect_ratio = self._combo(["16:9", "9:16", "1:1"])
        self.platform = self._combo(["抖音", "B站", "小红书", "视频号"])

        form = QFormLayout()
        form.addRow("视频比例", self.aspect_ratio)
        form.addRow("目标平台", self.platform)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.title)
        layout.addLayout(form)
        layout.addStretch()

        self.aspect_ratio.currentTextChanged.connect(self._emit_changed)
        self.platform.currentTextChanged.connect(self._emit_changed)

    def _combo(self, values: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        return combo

    def set_settings(self, settings: dict) -> None:
        self._loading = True
        self.aspect_ratio.setCurrentText(settings.get("aspect_ratio", "9:16"))
        self.platform.setCurrentText(settings.get("platform", "抖音"))
        self._loading = False

    def current_settings(self) -> dict:
        return {
            "aspect_ratio": self.aspect_ratio.currentText(),
            "platform": self.platform.currentText(),
        }

    def _emit_changed(self) -> None:
        if not self._loading:
            self.settings_changed.emit(self.current_settings())
