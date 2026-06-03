from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from scriptclipper.core.project_model import TimelineClip


class ScriptEditor(QWidget):
    clip_changed = Signal(str, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_clip_id: str | None = None
        self.current_clip_type: str | None = None
        self._loading = False

        self.header = QLabel("结构化脚本编辑区")
        self.header.setObjectName("PanelTitle")
        self.empty_label = QLabel("选择时间轴中的 A-roll 或 B-roll 片段后可编辑脚本细节")
        self.empty_label.setObjectName("MutedText")

        self.title_edit = QLineEdit()
        self.text_edit = QPlainTextEdit()
        self.note_edit = QPlainTextEdit()
        self.emotion_edit = QLineEdit()
        self.duration_edit = QDoubleSpinBox()
        self.duration_edit.setRange(0.1, 9999.0)
        self.duration_edit.setDecimals(1)
        self.duration_edit.setSingleStep(0.5)
        self.duration_edit.setSuffix("s")

        self.title_label = QLabel("标题")
        self.text_label = QLabel("口播文案")
        self.note_label = QLabel("画面备注")
        self.emotion_label = QLabel("语气/节奏/音效")

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self.form.addRow(self.title_label, self.title_edit)
        self.form.addRow(self.text_label, self.text_edit)
        self.form.addRow(self.note_label, self.note_edit)
        self.form.addRow(self.emotion_label, self.emotion_edit)
        self.form.addRow("预计时长", self.duration_edit)

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
        self.set_clip(None)

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
            self.duration_edit.setValue(1.0)
        self._loading = False

    def _configure_labels(self, clip_type: str) -> None:
        if clip_type == "b_roll":
            self.text_label.setText("画面内容")
            self.note_label.setText("备注")
            self.emotion_label.setText("音效 / 音乐")
            self.text_edit.setPlaceholderText("补充镜头、景别、动作等画面内容")
            self.note_edit.setPlaceholderText("补充导出脚本表的画面备注")
        else:
            self.text_label.setText("口播文案")
            self.note_label.setText("备注")
            self.emotion_label.setText("语气")
            self.text_edit.setPlaceholderText("导出到传统脚本表的文案内容")
            self.note_edit.setPlaceholderText("口播对应画面、字幕或动作提示")

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
