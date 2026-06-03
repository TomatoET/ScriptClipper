from __future__ import annotations

import math

from PySide6.QtCore import QByteArray, QDataStream, QIODevice, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget

from scriptclipper.core.project_model import ProjectModel, TimelineClip
from scriptclipper.ui.asset_panel import A_ROLL_MIME_TYPE, B_ROLL_MIME_TYPE


TIMELINE_CLIP_MIME_TYPE = "application/x-scriptclipper-timeline-clip"


class RhythmPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: ProjectModel | None = None
        self.setMinimumHeight(150)

    def set_project(self, project: ProjectModel) -> None:
        self.project = project
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        grid_color = bg.lighter(145) if bg.lightness() < 128 else bg.darker(118)
        painter.fillRect(self.rect(), bg.darker(108) if bg.lightness() < 128 else bg.lighter(103))
        painter.setPen(text_color)
        painter.drawText(16, 26, "节奏波形图")

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
    asset_dropped = Signal(str, str)
    clip_reordered = Signal(str, int, int)
    clip_moved = Signal(str, float)
    status_message = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: ProjectModel | None = None
        self.selected_clip_id: str | None = None
        self.clip_rects: dict[str, tuple[str, int, QRect]] = {}
        self.drag_clip_id: str | None = None
        self.drag_start_pos = None
        self.drag_original_start_time = 0.0
        self.drag_preview_start_time: float | None = None
        self.drag_started = False
        self.pixels_per_second = 52
        self.label_w = 112
        self.ruler_h = 36
        self.track_h = 68
        self.track_gap = 10
        self.setAcceptDrops(True)
        self.setMinimumHeight(222)
        self.setMouseTracking(True)

    def set_project(self, project: ProjectModel) -> None:
        self.project = project
        self._resize_for_zoom()
        self.update()

    def set_zoom(self, value: int) -> None:
        self.pixels_per_second = value
        self._resize_for_zoom()
        self.update()

    def set_selected_clip(self, clip_id: str | None) -> None:
        self.selected_clip_id = clip_id
        self.update()

    def _resize_for_zoom(self) -> None:
        if not self.project:
            return
        width = self.label_w + int(self.project.timeline_duration() * self.pixels_per_second) + 120
        self.setMinimumWidth(max(900, width))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        grid_color = bg.lighter(145) if bg.lightness() < 128 else bg.darker(118)
        track_color = bg.lighter(118) if bg.lightness() < 128 else bg.darker(104)
        header_color = bg.lighter(108) if bg.lightness() < 128 else bg.darker(108)
        painter.fillRect(self.rect(), bg)
        if not self.project:
            return

        self.clip_rects.clear()
        top = self.ruler_h
        track_h = self.track_h
        gap = self.track_gap
        content_w = int(self.project.timeline_duration() * self.pixels_per_second)

        self._draw_ruler(painter, grid_color, text_color)
        self._draw_playhead(painter)

        self._draw_track(painter, "B-roll", "b_roll", self.project.b_roll, self.label_w, top, content_w, track_h, QColor("#36b7ff"))
        self._draw_track(
            painter,
            "A-roll",
            "a_roll",
            self.project.a_roll,
            self.label_w,
            top + track_h + gap,
            content_w,
            track_h,
            QColor("#f1b545"),
        )

    def _draw_ruler(self, painter: QPainter, grid_color: QColor, text_color: QColor) -> None:
        if not self.project:
            return
        duration = int(math.ceil(self.project.timeline_duration()))
        painter.fillRect(0, 0, self.width(), self.ruler_h, self.palette().window().color().darker(105))
        painter.fillRect(0, 0, self.label_w - 4, self.ruler_h, self.palette().window().color().darker(112))
        painter.setFont(QFont("Segoe UI", 9))
        for second in range(duration + 1):
            x = self.label_w + int(second * self.pixels_per_second)
            major = second % 5 == 0
            line_h = 22 if major else 11
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(x, self.ruler_h - line_h, x, self.height() - 12 if major else self.ruler_h)
            if major:
                painter.setPen(text_color)
                painter.drawText(x + 5, 22, _format_time(second))

    def _draw_playhead(self, painter: QPainter) -> None:
        x = self.label_w
        painter.setPen(QPen(QColor("#6aa5ff"), 2))
        painter.drawLine(x, 0, x, self.height() - 10)
        painter.setBrush(QColor("#6aa5ff"))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon([
            self._point(x - 7, 2),
            self._point(x + 7, 2),
            self._point(x, 12),
        ])

    def _point(self, x: int, y: int):
        from PySide6.QtCore import QPoint

        return QPoint(x, y)

    def _draw_track(
        self,
        painter: QPainter,
        label: str,
        track_name: str,
        clips: list[TimelineClip],
        label_w: int,
        y: int,
        content_w: int,
        track_h: int,
        color: QColor,
    ) -> None:
        bg = self.palette().window().color()
        text_color = self.palette().windowText().color()
        track_color = bg.lighter(118) if bg.lightness() < 128 else bg.darker(104)
        header_color = bg.lighter(108) if bg.lightness() < 128 else bg.darker(108)
        border_color = bg.lighter(160) if bg.lightness() < 128 else bg.darker(125)
        painter.setPen(border_color)
        painter.setBrush(track_color)
        painter.drawRect(0, y, max(self.width(), label_w + content_w + 40), track_h)
        painter.fillRect(0, y, label_w - 4, track_h, header_color)
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(16, y + 34, label)

        overlaps = self._overlap_ids(clips)
        for index, clip in enumerate(clips):
            width = max(52, int(clip.duration * self.pixels_per_second))
            start_time = self._draw_start_time(clip)
            cursor = label_w + int(start_time * self.pixels_per_second)
            rect = QRect(cursor + 3, y + 9, width - 6, track_h - 18)
            self.clip_rects[clip.id] = (track_name, index, rect)

            selected = clip.id == self.selected_clip_id
            overlapped = clip.id in overlaps
            painter.setBrush(color.lighter(125) if selected else color)
            if overlapped:
                pen = QPen(QColor("#ff5a5f"), 3)
            else:
                pen = QPen(QColor("#ffffff") if selected else border_color, 2 if selected else 1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#0f1115"))
            title = clip.title or clip.text or "clip"
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(rect.adjusted(8, 4, -6, -18), Qt.AlignLeft | Qt.AlignVCenter, title[:28])
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(
                rect.adjusted(8, 24, -6, -4),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{start_time:.1f}s / {clip.duration:.1f}s",
            )

    def _draw_start_time(self, clip: TimelineClip) -> float:
        if clip.id == self.drag_clip_id and self.drag_preview_start_time is not None:
            return self.drag_preview_start_time
        return clip.start_time

    def _overlap_ids(self, clips: list[TimelineClip]) -> set[str]:
        overlaps: set[str] = set()
        sorted_clips = sorted(clips, key=lambda item: item.start_time)
        for index, clip in enumerate(sorted_clips):
            clip_start = self._draw_start_time(clip)
            clip_end = clip_start + clip.duration
            for other in sorted_clips[index + 1:]:
                other_start = self._draw_start_time(other)
                if other_start >= clip_end:
                    break
                overlaps.add(clip.id)
                overlaps.add(other.id)
        return overlaps

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton:
            return
        for clip_id, (_, _, rect) in self.clip_rects.items():
            if rect.contains(event.position().toPoint()):
                self.selected_clip_id = clip_id
                self.drag_clip_id = clip_id
                self.drag_start_pos = event.position().toPoint()
                clip = self.project.find_clip(clip_id) if self.project else None
                self.drag_original_start_time = clip.start_time if clip else 0.0
                self.drag_preview_start_time = self.drag_original_start_time
                self.drag_started = False
                self.setCursor(Qt.ClosedHandCursor)
                self.clip_selected.emit(clip_id)
                self.update()
                return
        self.selected_clip_id = None
        self.drag_clip_id = None
        self.drag_preview_start_time = None
        self.drag_started = False
        self.clip_selected.emit("")
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if not self.drag_clip_id or not self.drag_start_pos:
            self._update_hover_cursor(pos)
            return
        if not event.buttons() & Qt.LeftButton:
            self._update_hover_cursor(pos)
            return
        if (pos - self.drag_start_pos).manhattanLength() < 4 and not self.drag_started:
            return
        self.drag_started = True
        delta_seconds = (pos.x() - self.drag_start_pos.x()) / max(1, self.pixels_per_second)
        next_start = self._snap_time(self.drag_original_start_time + delta_seconds)
        self.drag_preview_start_time = max(0.0, next_start)
        self.status_message.emit(f"移动到 {self.drag_preview_start_time:.1f}s", 0)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.drag_clip_id:
            clip_id = self.drag_clip_id
            next_start = self.drag_preview_start_time if self.drag_preview_start_time is not None else self.drag_original_start_time
            moved = self.drag_started and abs(next_start - self.drag_original_start_time) >= 0.001
            self.drag_clip_id = None
            self.drag_start_pos = None
            self.drag_preview_start_time = None
            self.drag_started = False
            self.unsetCursor()
            if moved:
                self.clip_moved.emit(clip_id, next_start)
            self.update()
            return
        self.unsetCursor()

    def leaveEvent(self, event) -> None:  # noqa: N802
        if not self.drag_clip_id:
            self.unsetCursor()

    def _update_hover_cursor(self, pos) -> None:
        for _, _, rect in self.clip_rects.values():
            if rect.contains(pos):
                self.setCursor(Qt.OpenHandCursor)
                return
        self.unsetCursor()

    def _snap_time(self, seconds: float) -> float:
        return round(max(0.0, seconds) * 2) / 2

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        formats = (A_ROLL_MIME_TYPE, B_ROLL_MIME_TYPE, TIMELINE_CLIP_MIME_TYPE)
        if any(event.mimeData().hasFormat(fmt) for fmt in formats):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        if event.mimeData().hasFormat(A_ROLL_MIME_TYPE) and self._track_at_y(pos.y()) == "a_roll":
            self.asset_dropped.emit("a_roll", self._read_payload(event.mimeData().data(A_ROLL_MIME_TYPE)))
            event.acceptProposedAction()
            return

        if event.mimeData().hasFormat(B_ROLL_MIME_TYPE) and self._track_at_y(pos.y()) == "b_roll":
            self.asset_dropped.emit("b_roll", self._read_payload(event.mimeData().data(B_ROLL_MIME_TYPE)))
            event.acceptProposedAction()
            return

    def _read_payload(self, payload: QByteArray) -> str:
        stream = QDataStream(payload, QIODevice.ReadOnly)
        return stream.readQString()

    def _track_at_y(self, y: int) -> str | None:
        top = self.ruler_h
        track_h = self.track_h
        gap = self.track_gap
        if top <= y <= top + track_h:
            return "b_roll"
        if top + track_h + gap <= y <= top + track_h + gap + track_h:
            return "a_roll"
        return None

    def _index_at_position(self, track_name: str, x: int) -> int:
        indexes = [(index, rect) for _, (name, index, rect) in self.clip_rects.items() if name == track_name]
        if not indexes:
            return 0
        for index, rect in sorted(indexes):
            if x < rect.center().x():
                return index
        return len(indexes) - 1


class TimelineWidget(QWidget):
    add_broll_requested = Signal()
    delete_requested = Signal()
    clip_selected = Signal(str)
    asset_dropped = Signal(str, str)
    clip_reordered = Signal(str, int, int)
    clip_moved = Signal(str, float)
    status_message = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.canvas = TimelineCanvas()
        self.add_broll_button = QPushButton("+ B-roll 占位")
        self.delete_button = QPushButton("删除选中")
        self.duration_label = QLabel("总时长 00:15")
        self.zoom_label = QLabel("缩放 100%")
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
        self.canvas.clip_selected.connect(self.clip_selected)
        self.canvas.asset_dropped.connect(self.asset_dropped)
        self.canvas.clip_reordered.connect(self.clip_reordered)
        self.canvas.clip_moved.connect(self.clip_moved)
        self.canvas.status_message.connect(self.status_message)

    def set_project(self, project: ProjectModel) -> None:
        self.canvas.set_project(project)
        self.duration_label.setText(f"总时长 {_format_time(project.timeline_duration())}")

    def set_selected_clip(self, clip_id: str | None) -> None:
        self.canvas.set_selected_clip(clip_id)

    def _set_zoom(self, value: int) -> None:
        percent = round(value / 52 * 100)
        self.zoom_label.setText(f"缩放 {percent}%")
        self.canvas.set_zoom(value)


def _format_time(seconds: float) -> str:
    total = int(round(seconds))
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"
