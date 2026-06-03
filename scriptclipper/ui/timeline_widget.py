from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QByteArray, QDataStream, QIODevice, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget

from scriptclipper.core.i18n import t
from scriptclipper.core.project_model import MIN_CLIP_DURATION, ProjectModel, TimelineClip
from scriptclipper.ui.asset_panel import A_ROLL_MIME_TYPE, B_ROLL_MIME_TYPE


TIMELINE_CLIP_MIME_TYPE = "application/x-scriptclipper-timeline-clip"
EDGE_HIT_PX = 8


def seconds_to_pixels(seconds: float, pixels_per_second: int) -> int:
    return int(round(seconds * pixels_per_second))


def pixels_to_seconds(pixels: int, pixels_per_second: int) -> float:
    return pixels / max(1, pixels_per_second)


def snap_time(seconds: float) -> float:
    return round(max(0.0, seconds) * 2) / 2


def format_time(seconds: float) -> str:
    total = int(round(seconds))
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"


def detect_overlap(clips: list[TimelineClip], preview: dict[str, tuple[float, float]] | None = None) -> set[str]:
    overlaps: set[str] = set()
    sorted_clips = sorted(clips, key=lambda item: _preview_range(item, preview)[0])
    for index, clip in enumerate(sorted_clips):
        clip_start, clip_duration = _preview_range(clip, preview)
        clip_end = clip_start + clip_duration
        for other in sorted_clips[index + 1:]:
            other_start, _ = _preview_range(other, preview)
            if other_start >= clip_end:
                break
            overlaps.add(clip.id)
            overlaps.add(other.id)
    return overlaps


def _preview_range(clip: TimelineClip, preview: dict[str, tuple[float, float]] | None) -> tuple[float, float]:
    if preview and clip.id in preview:
        return preview[clip.id]
    return clip.start_time, clip.duration


@dataclass
class DragState:
    clip_id: str
    mode: str
    start_pos: QPoint
    original_start: float
    original_duration: float


class RhythmPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: ProjectModel | None = None
        self.setMinimumHeight(150)

    def set_project(self, project: ProjectModel) -> None:
        self.project = project
        self.update()

    def retranslate(self) -> None:
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        grid_color = bg.lighter(145) if bg.lightness() < 128 else bg.darker(118)
        painter.fillRect(self.rect(), bg.darker(108) if bg.lightness() < 128 else bg.lighter(103))
        painter.setPen(text_color)
        painter.drawText(16, 26, t("timeline.rhythm_preview"))

        if not self.project:
            return
        left, top = 18, 48
        width = max(10, self.width() - 36)
        duration = max(self.project.timeline_duration(), 1.0)

        painter.setPen(QPen(grid_color, 1))
        for tick in range(self.project.tick_count()):
            x = left + int((tick * 5 / duration) * width)
            painter.drawLine(x, top, x, self.height() - 20)

        self._draw_blocks(painter, self.project.b_roll, left, top + 8, width, duration, QColor("#40b7ff"))
        self._draw_blocks(painter, self.project.a_roll, left, top + 50, width, duration, QColor("#ffcc66"))

    def _draw_blocks(
        self,
        painter: QPainter,
        clips: list[TimelineClip],
        left: int,
        y: int,
        total_width: int,
        total_duration: float,
        color: QColor,
    ) -> None:
        for clip in clips:
            cursor = left + int((clip.start_time / total_duration) * total_width)
            width = max(12, int((clip.duration / total_duration) * total_width))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(cursor, y, width - 3, 28), 5, 5)


class TimelineCanvas(QWidget):
    clip_selected = Signal(str)
    asset_dropped = Signal(str, str, float)
    clip_moved = Signal(str, float)
    clip_resized = Signal(str, float, float)
    status_message = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: ProjectModel | None = None
        self.selected_clip_id: str | None = None
        self.clip_rects: dict[str, tuple[str, int, QRect]] = {}
        self.drag_state: DragState | None = None
        self.preview_ranges: dict[str, tuple[float, float]] = {}
        self.pixels_per_second = 52
        self.scroll_x = 0
        self.label_w = 112
        self.ruler_h = 40
        self.track_h = 76
        self.track_gap = 10
        self.setAcceptDrops(True)
        self.setMinimumHeight(236)
        self.setMouseTracking(True)

    def set_project(self, project: ProjectModel) -> None:
        self.project = project
        self._resize_for_zoom()
        self.update()

    def set_zoom(self, value: int) -> None:
        self.pixels_per_second = value
        self._resize_for_zoom()
        self.update()

    def set_scroll_x(self, value: int) -> None:
        self.scroll_x = value
        self.update()

    def set_selected_clip(self, clip_id: str | None) -> None:
        self.selected_clip_id = clip_id
        self.update()

    def _resize_for_zoom(self) -> None:
        if not self.project:
            return
        width = self.label_w + seconds_to_pixels(self.project.timeline_duration(), self.pixels_per_second) + 180
        self.setMinimumWidth(max(900, width))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        grid_color = bg.lighter(145) if bg.lightness() < 128 else bg.darker(118)
        painter.fillRect(self.rect(), bg)
        if not self.project:
            return

        self.clip_rects.clear()
        top = self.ruler_h
        content_w = seconds_to_pixels(self.project.timeline_duration(), self.pixels_per_second)
        self._draw_ruler(painter, grid_color, text_color)
        self._draw_playhead(painter)
        self._draw_track(painter, "B-roll", "b_roll", self.project.b_roll, self.label_w, top, content_w, QColor("#36b7ff"))
        self._draw_track(
            painter,
            "A-roll",
            "a_roll",
            self.project.a_roll,
            self.label_w,
            top + self.track_h + self.track_gap,
            content_w,
            QColor("#f1b545"),
        )

    def _tick_steps(self) -> tuple[float, float]:
        if self.pixels_per_second >= 90:
            return 1.0, 0.5
        if self.pixels_per_second >= 45:
            return 5.0, 1.0
        return 10.0, 5.0

    def _draw_ruler(self, painter: QPainter, grid_color: QColor, text_color: QColor) -> None:
        if not self.project:
            return
        bg = self.palette().window().color()
        major_step, minor_step = self._tick_steps()
        duration = self.project.timeline_duration()
        painter.fillRect(0, 0, self.width(), self.ruler_h, bg.darker(105))
        painter.setFont(QFont("Segoe UI", 9))

        minor_count = int(math.ceil(duration / minor_step)) + 1
        for tick in range(minor_count):
            second = tick * minor_step
            x = self.label_w + seconds_to_pixels(second, self.pixels_per_second)
            is_major = abs((second / major_step) - round(second / major_step)) < 0.001
            line_h = 24 if is_major else 10
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(x, self.ruler_h - line_h, x, self.height() - 12 if is_major else self.ruler_h)
            if is_major:
                painter.setPen(text_color)
                painter.drawText(x + 5, 23, format_time(second))

        self._draw_fixed_label_header(painter, bg)

    def _draw_fixed_label_header(self, painter: QPainter, bg: QColor) -> None:
        x = self.scroll_x
        painter.fillRect(x, 0, self.label_w - 4, self.height(), bg.darker(112))

    def _draw_playhead(self, painter: QPainter) -> None:
        x = self.label_w
        bg = self.palette().window().color()
        playhead_color = bg.lighter(175) if bg.lightness() < 128 else bg.darker(135)
        painter.setPen(QPen(playhead_color, 1))
        painter.drawLine(x, 0, x, self.height() - 10)

    def _draw_track(
        self,
        painter: QPainter,
        label: str,
        track_name: str,
        clips: list[TimelineClip],
        label_w: int,
        y: int,
        content_w: int,
        color: QColor,
    ) -> None:
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        track_color = bg.lighter(118) if bg.lightness() < 128 else bg.darker(104)
        header_color = bg.lighter(108) if bg.lightness() < 128 else bg.darker(108)
        border_color = bg.lighter(160) if bg.lightness() < 128 else bg.darker(125)
        painter.setPen(border_color)
        painter.setBrush(track_color)
        painter.drawRect(0, y, max(self.width(), label_w + content_w + 40), self.track_h)

        overlaps = detect_overlap(clips, self.preview_ranges)
        for index, clip in enumerate(clips):
            start_time, duration = _preview_range(clip, self.preview_ranges)
            width = max(seconds_to_pixels(MIN_CLIP_DURATION, self.pixels_per_second), seconds_to_pixels(duration, self.pixels_per_second))
            x = label_w + seconds_to_pixels(start_time, self.pixels_per_second)
            rect = QRect(x + 3, y + 10, width - 6, self.track_h - 20)
            self.clip_rects[clip.id] = (track_name, index, rect)

            selected = clip.id == self.selected_clip_id
            painter.setBrush(color.lighter(135) if selected else color)
            if clip.id in overlaps:
                pen = QPen(QColor("#ff5a5f"), 3)
            else:
                pen = QPen(QColor("#ffffff") if selected else border_color, 2 if selected else 1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 6, 6)
            if self.drag_state and clip.id == self.drag_state.clip_id:
                painter.setPen(QPen(QColor("#ffffff"), 1, Qt.DashLine))
                painter.drawRect(rect.adjusted(-2, -2, 2, 2))
            painter.setPen(QColor("#0f1115"))
            title = clip.title or clip.text or "clip"
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(rect.adjusted(8, 4, -6, -22), Qt.AlignLeft | Qt.AlignVCenter, title[:28])
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(rect.adjusted(8, 26, -6, -4), Qt.AlignLeft | Qt.AlignVCenter, f"{start_time:.1f}s / {duration:.1f}s")

        fixed_x = self.scroll_x
        painter.fillRect(fixed_x, y, label_w - 4, self.track_h, header_color)
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(fixed_x + 16, y + 40, label)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton or not self.project:
            return
        pos = event.position().toPoint()
        for clip_id, (_, _, rect) in self.clip_rects.items():
            if rect.contains(pos):
                clip = self.project.find_clip(clip_id)
                if not clip:
                    return
                self.selected_clip_id = clip_id
                self.clip_selected.emit(clip_id)
                mode = self._interaction_mode(rect, pos)
                self.drag_state = DragState(clip_id, mode, pos, clip.start_time, clip.duration)
                self.preview_ranges = {clip_id: (clip.start_time, clip.duration)}
                self.setCursor(Qt.SizeHorCursor if mode != "move" else Qt.ClosedHandCursor)
                self.update()
                return
        self.selected_clip_id = None
        self.drag_state = None
        self.preview_ranges = {}
        self.clip_selected.emit("")
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if not self.drag_state or not self.project:
            self._update_hover_cursor(pos)
            return
        if not event.buttons() & Qt.LeftButton:
            self._update_hover_cursor(pos)
            return
        delta_seconds = pixels_to_seconds(pos.x() - self.drag_state.start_pos.x(), self.pixels_per_second)
        start, duration = self._preview_from_delta(delta_seconds)
        self.preview_ranges = {self.drag_state.clip_id: (start, duration)}
        if start <= 0.0 and self.drag_state.original_start + delta_seconds < 0:
            self.status_message.emit(t("timeline.before_zero"), 2000)
        else:
            self.status_message.emit(t("timeline.resizing", start=start, duration=duration) if self.drag_state.mode != "move" else t("timeline.move_to", time=start), 0)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton or not self.drag_state:
            self.unsetCursor()
            return
        state = self.drag_state
        start, duration = self.preview_ranges.get(state.clip_id, (state.original_start, state.original_duration))
        self.drag_state = None
        self.preview_ranges = {}
        self.unsetCursor()
        if state.mode == "move":
            if abs(start - state.original_start) >= 0.001:
                self.clip_moved.emit(state.clip_id, start)
        elif abs(start - state.original_start) >= 0.001 or abs(duration - state.original_duration) >= 0.001:
            self.clip_resized.emit(state.clip_id, start, duration)
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        if not self.drag_state:
            self.unsetCursor()

    def _interaction_mode(self, rect: QRect, pos: QPoint) -> str:
        if abs(pos.x() - rect.left()) <= EDGE_HIT_PX:
            return "resize_left"
        if abs(pos.x() - rect.right()) <= EDGE_HIT_PX:
            return "resize_right"
        return "move"

    def _preview_from_delta(self, delta_seconds: float) -> tuple[float, float]:
        assert self.drag_state is not None
        state = self.drag_state
        if state.mode == "move":
            return snap_time(state.original_start + delta_seconds), state.original_duration
        if state.mode == "resize_right":
            duration = max(MIN_CLIP_DURATION, snap_time(state.original_duration + delta_seconds))
            if duration <= MIN_CLIP_DURATION:
                self.status_message.emit(t("timeline.min_duration"), 2000)
            return state.original_start, duration
        right_edge = state.original_start + state.original_duration
        next_start = min(snap_time(state.original_start + delta_seconds), right_edge - MIN_CLIP_DURATION)
        next_start = max(0.0, next_start)
        duration = max(MIN_CLIP_DURATION, snap_time(right_edge - next_start))
        return next_start, duration

    def _update_hover_cursor(self, pos: QPoint) -> None:
        for _, _, rect in self.clip_rects.values():
            if rect.contains(pos):
                self.setCursor(Qt.SizeHorCursor if self._interaction_mode(rect, pos) != "move" else Qt.OpenHandCursor)
                return
        self.unsetCursor()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        formats = (A_ROLL_MIME_TYPE, B_ROLL_MIME_TYPE, TIMELINE_CLIP_MIME_TYPE)
        if any(event.mimeData().hasFormat(fmt) for fmt in formats):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        track = self._track_at_y(pos.y())
        start_time = self._time_at_x(pos.x())
        if event.mimeData().hasFormat(A_ROLL_MIME_TYPE):
            if track != "a_roll":
                self.status_message.emit(t("timeline.drop_wrong_track"), 3000)
                return
            self.asset_dropped.emit("a_roll", self._read_payload(event.mimeData().data(A_ROLL_MIME_TYPE)), start_time)
            event.acceptProposedAction()
            return

        if event.mimeData().hasFormat(B_ROLL_MIME_TYPE):
            if track != "b_roll":
                self.status_message.emit(t("timeline.drop_wrong_track"), 3000)
                return
            self.asset_dropped.emit("b_roll", self._read_payload(event.mimeData().data(B_ROLL_MIME_TYPE)), start_time)
            event.acceptProposedAction()

    def _read_payload(self, payload: QByteArray) -> str:
        stream = QDataStream(payload, QIODevice.ReadOnly)
        return stream.readQString()

    def _time_at_x(self, x: int) -> float:
        return snap_time(pixels_to_seconds(max(0, x - self.label_w), self.pixels_per_second))

    def _track_at_y(self, y: int) -> str | None:
        top = self.ruler_h
        if top <= y <= top + self.track_h:
            return "b_roll"
        a_top = top + self.track_h + self.track_gap
        if a_top <= y <= a_top + self.track_h:
            return "a_roll"
        return None


class TimelineWidget(QWidget):
    add_broll_requested = Signal()
    delete_requested = Signal()
    clip_selected = Signal(str)
    asset_dropped = Signal(str, str, float)
    clip_moved = Signal(str, float)
    clip_resized = Signal(str, float, float)
    status_message = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.canvas = TimelineCanvas()
        self.add_broll_button = QPushButton()
        self.delete_button = QPushButton()
        self.duration_label = QLabel()
        self.zoom_label = QLabel()
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(28, 120)
        self.zoom_slider.setValue(52)
        self.zoom_slider.setFixedWidth(180)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.canvas)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.add_broll_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.duration_label)
        button_layout.addWidget(self.zoom_label)
        button_layout.addWidget(self.zoom_slider)

        layout.addWidget(button_row)
        layout.addWidget(self.scroll_area)

        self.add_broll_button.clicked.connect(self.add_broll_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.zoom_slider.valueChanged.connect(self._set_zoom)
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.canvas.set_scroll_x)
        self.canvas.clip_selected.connect(self.clip_selected)
        self.canvas.asset_dropped.connect(self.asset_dropped)
        self.canvas.clip_moved.connect(self.clip_moved)
        self.canvas.clip_resized.connect(self.clip_resized)
        self.canvas.status_message.connect(self.status_message)
        self.retranslate()

    def retranslate(self) -> None:
        self.add_broll_button.setText(t("timeline.add_broll"))
        self.delete_button.setText(t("timeline.delete_selected"))
        self._update_zoom_label(self.zoom_slider.value())
        if self.canvas.project:
            self.duration_label.setText(t("timeline.total_duration", time=format_time(self.canvas.project.timeline_duration())))

    def set_project(self, project: ProjectModel) -> None:
        self.canvas.set_project(project)
        self.duration_label.setText(t("timeline.total_duration", time=format_time(project.timeline_duration())))

    def set_selected_clip(self, clip_id: str | None) -> None:
        self.canvas.set_selected_clip(clip_id)

    def _set_zoom(self, value: int) -> None:
        self._update_zoom_label(value)
        self.canvas.set_zoom(value)

    def _update_zoom_label(self, value: int) -> None:
        percent = round(value / 52 * 100)
        self.zoom_label.setText(t("timeline.zoom", percent=percent))
