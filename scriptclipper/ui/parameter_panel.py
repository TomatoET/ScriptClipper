from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from scriptclipper.core.i18n import t
from scriptclipper.core.project_model import MIN_CLIP_DURATION, TimelineClip


class ParameterPanel(QWidget):
    clip_changed = Signal(str, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_clip_id: str | None = None
        self.current_clip_type: str | None = None
        self._loading = False
        self._rows: dict[str, tuple[QLabel, QWidget]] = {}

        self.title = QLabel()
        self.title.setObjectName("PanelTitle")
        self.empty_label = QLabel()
        self.empty_label.setObjectName("MutedText")
        self.empty_label.setWordWrap(True)

        self.title_edit = QLineEdit()
        self.content_edit = QPlainTextEdit()
        self.tone_edit = QLineEdit()
        self.speed_edit = QLineEdit()
        self.pause_hint_edit = QLineEdit()
        self.subtitle_focus_edit = QPlainTextEdit()
        self.shot_size_edit = QLineEdit()
        self.camera_move_edit = QLineEdit()
        self.action_edit = QPlainTextEdit()
        self.keywords_edit = QLineEdit()
        self.sound_edit = QLineEdit()
        self.duration_edit = QDoubleSpinBox()
        self.duration_edit.setRange(MIN_CLIP_DURATION, 9999.0)
        self.duration_edit.setDecimals(1)
        self.duration_edit.setSingleStep(0.5)
        self.duration_edit.setSuffix("s")
        self.note_edit = QPlainTextEdit()

        for editor in (self.content_edit, self.subtitle_focus_edit, self.action_edit, self.note_edit):
            editor.setMaximumHeight(86)

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self._add_row("title", self.title_edit)
        self._add_row("content", self.content_edit)
        self._add_row("tone", self.tone_edit)
        self._add_row("speed", self.speed_edit)
        self._add_row("pauseHint", self.pause_hint_edit)
        self._add_row("subtitleFocus", self.subtitle_focus_edit)
        self._add_row("shotSize", self.shot_size_edit)
        self._add_row("cameraMove", self.camera_move_edit)
        self._add_row("action", self.action_edit)
        self._add_row("keywords", self.keywords_edit)
        self._add_row("sound", self.sound_edit)
        self._add_row("duration", self.duration_edit)
        self._add_row("note", self.note_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.title)
        layout.addWidget(self.empty_label)
        layout.addLayout(self.form)
        layout.addStretch()

        self.title_edit.textChanged.connect(self._emit_changed)
        self.content_edit.textChanged.connect(self._emit_changed)
        self.tone_edit.textChanged.connect(self._emit_changed)
        self.speed_edit.textChanged.connect(self._emit_changed)
        self.pause_hint_edit.textChanged.connect(self._emit_changed)
        self.subtitle_focus_edit.textChanged.connect(self._emit_changed)
        self.shot_size_edit.textChanged.connect(self._emit_changed)
        self.camera_move_edit.textChanged.connect(self._emit_changed)
        self.action_edit.textChanged.connect(self._emit_changed)
        self.keywords_edit.textChanged.connect(self._emit_changed)
        self.sound_edit.textChanged.connect(self._emit_changed)
        self.duration_edit.valueChanged.connect(self._emit_changed)
        self.note_edit.textChanged.connect(self._emit_changed)
        self.retranslate()
        self.set_clip(None)

    def _add_row(self, key: str, widget: QWidget) -> None:
        label = QLabel()
        self.form.addRow(label, widget)
        self._rows[key] = (label, widget)

    def retranslate(self) -> None:
        self.title.setText(t("detail.title"))
        self.empty_label.setText(t("detail.empty"))
        labels = {
            "title": t("detail.clip_title"),
            "tone": t("detail.tone"),
            "speed": t("detail.speed"),
            "pauseHint": t("detail.pause_hint"),
            "subtitleFocus": t("detail.subtitle_focus"),
            "shotSize": t("detail.shot_size"),
            "cameraMove": t("detail.camera_move"),
            "action": t("detail.action"),
            "keywords": t("detail.keywords"),
            "sound": t("detail.sound"),
            "duration": t("detail.duration"),
            "note": t("detail.note"),
        }
        for key, text in labels.items():
            self._rows[key][0].setText(text)
        self._configure_rows(self.current_clip_type or "")

    def set_settings(self, settings: dict) -> None:
        return

    def set_clip(self, clip: TimelineClip | None) -> None:
        self._loading = True
        self.current_clip_id = clip.id if clip else None
        self.current_clip_type = clip.type if clip else None
        enabled = clip is not None
        self.empty_label.setVisible(not enabled)

        if clip:
            clip.ensure_detail_defaults()
            self.title_edit.setText(clip.title)
            self.content_edit.setPlainText(clip.text)
            self.tone_edit.setText(str(clip.details.get("tone", "")))
            self.speed_edit.setText(str(clip.details.get("speed", "")))
            self.pause_hint_edit.setText(str(clip.details.get("pauseHint", "")))
            self.subtitle_focus_edit.setPlainText(str(clip.details.get("subtitleFocus", "")))
            self.shot_size_edit.setText(str(clip.details.get("shotSize", "")))
            self.camera_move_edit.setText(str(clip.details.get("cameraMove", "")))
            self.action_edit.setPlainText(str(clip.details.get("action", "")))
            self.keywords_edit.setText(str(clip.details.get("keywords", "")))
            self.sound_edit.setText(str(clip.details.get("sound", "")))
            self.duration_edit.setValue(float(clip.duration))
            self.note_edit.setPlainText(str(clip.details.get("note", clip.note)))
        else:
            self.title_edit.clear()
            self.content_edit.clear()
            self.tone_edit.clear()
            self.speed_edit.clear()
            self.pause_hint_edit.clear()
            self.subtitle_focus_edit.clear()
            self.shot_size_edit.clear()
            self.camera_move_edit.clear()
            self.action_edit.clear()
            self.keywords_edit.clear()
            self.sound_edit.clear()
            self.duration_edit.setValue(MIN_CLIP_DURATION)
            self.note_edit.clear()

        self._configure_rows(clip.type if clip else "")
        for _, widget in self._rows.values():
            widget.setEnabled(enabled)
        self._loading = False

    def _configure_rows(self, clip_type: str) -> None:
        a_roll_rows = {"title", "content", "tone", "speed", "pauseHint", "subtitleFocus", "duration", "note"}
        b_roll_rows = {"title", "content", "shotSize", "cameraMove", "action", "keywords", "sound", "duration", "note"}
        visible_rows = a_roll_rows if clip_type == "a_roll" else b_roll_rows if clip_type == "b_roll" else set()
        self._rows["content"][0].setText(t("detail.b_content") if clip_type == "b_roll" else t("detail.a_content"))
        for key, (label, widget) in self._rows.items():
            visible = key in visible_rows
            label.setVisible(visible)
            widget.setVisible(visible)

    def _emit_changed(self) -> None:
        if self._loading or not self.current_clip_id or not self.current_clip_type:
            return
        if self.current_clip_type == "a_roll":
            details = {
                "tone": self.tone_edit.text(),
                "speed": self.speed_edit.text(),
                "pauseHint": self.pause_hint_edit.text(),
                "subtitleFocus": self.subtitle_focus_edit.toPlainText(),
                "note": self.note_edit.toPlainText(),
            }
            emotion = self.tone_edit.text()
        else:
            details = {
                "shotSize": self.shot_size_edit.text(),
                "cameraMove": self.camera_move_edit.text(),
                "action": self.action_edit.toPlainText(),
                "keywords": self.keywords_edit.text(),
                "sound": self.sound_edit.text(),
                "note": self.note_edit.toPlainText(),
            }
            emotion = self.sound_edit.text()
        self.clip_changed.emit(
            self.current_clip_id,
            {
                "title": self.title_edit.text(),
                "text": self.content_edit.toPlainText(),
                "duration": self.duration_edit.value(),
                "note": self.note_edit.toPlainText(),
                "emotion": emotion,
                "details": details,
            },
        )
