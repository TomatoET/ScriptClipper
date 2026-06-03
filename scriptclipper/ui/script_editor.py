from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from scriptclipper.core.i18n import t
from scriptclipper.core.project_model import MIN_CLIP_DURATION, TimelineClip


class ScriptEditor(QWidget):
    clip_changed = Signal(str, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_clip_id: str | None = None
        self.current_clip_type: str | None = None
        self._loading = False

        self.header = QLabel()
        self.header.setObjectName("PanelTitle")
        self.empty_label = QLabel()
        self.empty_label.setObjectName("MutedText")
        self.empty_label.setWordWrap(True)

        self.title_edit = QLineEdit()
        self.text_edit = QPlainTextEdit()
        self.note_edit = QPlainTextEdit()
        self.emotion_edit = QLineEdit()
        self.duration_edit = QDoubleSpinBox()
        self.duration_edit.setRange(MIN_CLIP_DURATION, 9999.0)
        self.duration_edit.setDecimals(1)
        self.duration_edit.setSingleStep(0.5)
        self.duration_edit.setSuffix("s")

        self.title_label = QLabel()
        self.text_label = QLabel()
        self.note_label = QLabel()
        self.emotion_label = QLabel()
        self.duration_label = QLabel()

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self.form.addRow(self.title_label, self.title_edit)
        self.form.addRow(self.text_label, self.text_edit)
        self.form.addRow(self.note_label, self.note_edit)
        self.form.addRow(self.emotion_label, self.emotion_edit)
        self.form.addRow(self.duration_label, self.duration_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.header)
        layout.addWidget(self.empty_label)
        layout.addLayout(self.form)

        self.title_edit.textChanged.connect(self._emit_changed)
        self.text_edit.textChanged.connect(self._emit_changed)
        self.note_edit.textChanged.connect(self._emit_changed)
        self.emotion_edit.textChanged.connect(self._emit_changed)
        self.duration_edit.valueChanged.connect(self._emit_changed)
        self.retranslate()
        self.set_clip(None)

    def retranslate(self) -> None:
        self.header.setText(t("editor.title"))
        self.empty_label.setText(t("editor.empty"))
        self.title_label.setText(t("editor.clip_title"))
        self.note_label.setText(t("editor.note"))
        self.duration_label.setText(t("editor.duration"))
        self._configure_labels(self.current_clip_type or "a_roll")

    def set_clip(self, clip: TimelineClip | None) -> None:
        self._loading = True
        self.current_clip_id = clip.id if clip else None
        self.current_clip_type = clip.type if clip else None
        enabled = self.current_clip_id is not None
        self.empty_label.setVisible(not enabled)
        for widget in (self.title_edit, self.text_edit, self.note_edit, self.emotion_edit, self.duration_edit):
            widget.setEnabled(enabled)

        if enabled and clip:
            self._configure_labels(clip.type)
            self.title_edit.setText(clip.title)
            self.text_edit.setPlainText(clip.text)
            self.note_edit.setPlainText(clip.note)
            self.emotion_edit.setText(clip.emotion)
            self.duration_edit.setValue(float(clip.duration))
        else:
            self._configure_labels("a_roll")
            self.title_edit.clear()
            self.text_edit.clear()
            self.note_edit.clear()
            self.emotion_edit.clear()
            self.duration_edit.setValue(MIN_CLIP_DURATION)
        self._loading = False

    def _configure_labels(self, clip_type: str) -> None:
        if clip_type == "b_roll":
            self.text_label.setText(t("editor.b_content"))
            self.emotion_label.setText(t("editor.sound"))
        else:
            self.text_label.setText(t("editor.a_content"))
            self.emotion_label.setText(t("editor.tone"))

    def _emit_changed(self) -> None:
        if self._loading or not self.current_clip_id:
            return
        details: dict[str, str] = {"note": self.note_edit.toPlainText()}
        if self.current_clip_type == "a_roll":
            details["tone"] = self.emotion_edit.text()
        elif self.current_clip_type == "b_roll":
            details["sound"] = self.emotion_edit.text()
        self.clip_changed.emit(
            self.current_clip_id,
            {
                "title": self.title_edit.text(),
                "text": self.text_edit.toPlainText(),
                "note": self.note_edit.toPlainText(),
                "emotion": self.emotion_edit.text(),
                "duration": self.duration_edit.value(),
                "details": details,
            },
        )
