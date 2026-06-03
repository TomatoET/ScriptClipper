from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from scriptclipper.core.file_io import export_json, load_project, read_text_file, save_project
from scriptclipper.core.project_model import ProjectModel
from scriptclipper.core.script_exporter import export_script_table
from scriptclipper.resources.themes import THEMES
from scriptclipper.ui.asset_panel import AssetPanel
from scriptclipper.ui.parameter_panel import ParameterPanel
from scriptclipper.ui.script_editor import ScriptEditor
from scriptclipper.ui.timeline_widget import RhythmPreview, TimelineWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project = ProjectModel()
        self.selected_clip_id: str | None = None
        self.theme_actions = {}

        self.setWindowTitle("ScriptClipper 视频脚本剪辑助手")
        self.resize(1440, 900)
        self._build_actions()
        self._build_layout()
        self._connect_signals()
        self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
        self.refresh_all()
        self.statusBar().showMessage("Ready")

    def _build_actions(self) -> None:
        self.file_menu = self.menuBar().addMenu("File")
        self.new_action = self.file_menu.addAction("New Project")
        self.open_action = self.file_menu.addAction("Open Project")
        self.save_action = self.file_menu.addAction("Save Project")
        self.save_as_action = self.file_menu.addAction("Save As")
        self.file_menu.addSeparator()
        self.import_txt_action = self.file_menu.addAction("Import TXT")
        self.export_json_action = self.file_menu.addAction("Export JSON")
        self.export_script_action = self.file_menu.addAction("Export Script Table")

        self.edit_menu = self.menuBar().addMenu("Edit")
        self.undo_action = self.edit_menu.addAction("Undo")
        self.redo_action = self.edit_menu.addAction("Redo")
        self.delete_action = self.edit_menu.addAction("Delete Selected")
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)

        self.view_menu = self.menuBar().addMenu("View")
        self.reset_layout_action = self.view_menu.addAction("Reset Layout")
        self.theme_menu = self.view_menu.addMenu("Theme")
        for theme_name in THEMES:
            action = self.theme_menu.addAction(theme_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=theme_name: self.apply_theme(name))
            self.theme_actions[theme_name] = action

        self.help_menu = self.menuBar().addMenu("Help")
        self.about_action = self.help_menu.addAction("About")

        self.new_action.triggered.connect(self.new_project)
        self.open_action.triggered.connect(self.open_project)
        self.save_action.triggered.connect(self.save_current_project)
        self.save_as_action.triggered.connect(self.save_project_as)
        self.import_txt_action.triggered.connect(self.import_txt)
        self.export_json_action.triggered.connect(self.export_project_json)
        self.export_script_action.triggered.connect(self.export_traditional_script)
        self.delete_action.triggered.connect(self.delete_selected_clip)
        self.reset_layout_action.triggered.connect(self.reset_layout)
        self.about_action.triggered.connect(self.show_about)

    def _build_layout(self) -> None:
        self.asset_panel = AssetPanel()
        self.rhythm_preview = RhythmPreview()
        self.script_editor = ScriptEditor()
        self.parameter_panel = ParameterPanel()
        self.timeline = TimelineWidget()
        self.setStatusBar(QStatusBar())

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        center_layout.addWidget(self.rhythm_preview, 3)
        center_layout.addWidget(self.script_editor, 4)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.asset_panel)
        self.main_splitter.addWidget(center)
        self.main_splitter.addWidget(self.parameter_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.main_splitter.setSizes([330, 790, 320])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)
        root_layout.addWidget(self.main_splitter, 1)
        root_layout.addWidget(self.timeline, 0)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.asset_panel.asset_selected.connect(self.select_clip_from_asset)
        self.parameter_panel.clip_changed.connect(self.update_clip_fields)
        self.timeline.add_broll_requested.connect(self.add_broll_clip)
        self.timeline.delete_requested.connect(self.delete_selected_clip)
        self.timeline.clip_selected.connect(self.select_clip)
        self.timeline.asset_dropped.connect(self.add_clip_from_asset)
        self.timeline.clip_reordered.connect(self.reorder_clip)
        self.timeline.clip_moved.connect(self.move_clip_to_time)
        self.timeline.status_message.connect(self.show_status_message)
        self.script_editor.clip_changed.connect(self.update_clip_fields)

    def refresh_all(self) -> None:
        self.asset_panel.set_assets(self.project.asset_pool, self.project.broll_asset_pool)
        self.parameter_panel.set_settings(self.project.settings)
        self.timeline.set_project(self.project)
        self.rhythm_preview.set_project(self.project)
        self.select_clip(self.selected_clip_id or "", update_canvas=False)
        self._update_theme_checks()
        self._update_window_title()

    def apply_theme(self, theme_name: str, mark_dirty: bool = True) -> None:
        theme_name = theme_name if theme_name in THEMES else "Dark"
        app = QApplication.instance()
        if app:
            app.setStyleSheet(THEMES[theme_name])
        self.project.settings["theme"] = theme_name
        self._update_theme_checks()
        if mark_dirty:
            self.project.dirty = True
            self._update_window_title()

    def _update_theme_checks(self) -> None:
        active = self.project.settings.get("theme", "Dark")
        for theme_name, action in self.theme_actions.items():
            action.blockSignals(True)
            action.setChecked(theme_name == active)
            action.blockSignals(False)

    def _update_window_title(self) -> None:
        marker = "*" if self.project.dirty else ""
        path = self.project.path or "未保存"
        self.setWindowTitle(f"ScriptClipper 视频脚本剪辑助手 - {self.project.project_name}{marker} ({path})")

    def new_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.project.reset()
        self.selected_clip_id = None
        self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
        self.refresh_all()
        self.statusBar().showMessage("New project created", 4000)

    def open_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "ScriptClipper Project (*.sclip);;JSON (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.selected_clip_id = None
            self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
            self.refresh_all()
            self.statusBar().showMessage(f"Opened {path}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Open failed", str(exc))

    def save_current_project(self) -> None:
        if not self.project.path:
            self.save_project_as()
            return
        try:
            save_project(self.project, self.project.path)
            self.refresh_all()
            self.statusBar().showMessage(f"Saved {self.project.path}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "ScriptClipper Project (*.sclip)")
        if not path:
            return
        try:
            save_project(self.project, path)
            self.refresh_all()
            self.statusBar().showMessage(f"Saved {self.project.path}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))

    def import_txt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import TXT", "", "Text Files (*.txt);;All Files (*.*)")
        if not path:
            return
        try:
            count = self.project.import_txt(read_text_file(path))
            self.selected_clip_id = None
            self.refresh_all()
            self.statusBar().showMessage(f"Imported {count} A-roll fragments from {Path(path).name}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Import failed", str(exc))

    def export_project_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON (*.json)")
        if not path:
            return
        try:
            export_json(self.project, path)
            self.statusBar().showMessage(f"Exported {path}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export failed", str(exc))

    def export_traditional_script(self) -> None:
        default_name = f"{self.project.project_name or 'Untitled'}_传统视频脚本.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Script Table",
            default_name,
            "Excel Workbook (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return
        try:
            target = export_script_table(self.project, path)
            self.statusBar().showMessage(f"Exported script table {target}", 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export script failed", str(exc))

    def add_clip_from_asset(self, clip_type: str, asset_id: str) -> None:
        if clip_type == "a_roll":
            clip = self.project.add_a_roll_clip(asset_id)
            message = "Added A-roll clip to timeline"
        else:
            clip = self.project.add_b_roll_clip(asset_id)
            message = "Added B-roll clip to timeline"
        if not clip:
            self.statusBar().showMessage("Source asset not found", 4000)
            return
        self.selected_clip_id = clip.id
        self.refresh_all()
        self.statusBar().showMessage(message, 3000)

    def add_broll_clip(self) -> None:
        clip = self.project.add_b_roll_clip()
        self.selected_clip_id = clip.id
        self.refresh_all()
        self.statusBar().showMessage("Added B-roll placeholder", 3000)

    def select_clip(self, clip_id: str, update_canvas: bool = True) -> None:
        self.selected_clip_id = clip_id or None
        clip = self.project.find_clip(self.selected_clip_id)
        self.script_editor.set_clip(clip)
        self.parameter_panel.set_clip(clip)
        if update_canvas:
            self.timeline.set_selected_clip(self.selected_clip_id)

    def select_clip_from_asset(self, asset_id: str) -> None:
        clip = next((item for item in self.project.a_roll + self.project.b_roll if item.source_id == asset_id), None)
        if not clip:
            self.statusBar().showMessage("该素材尚未加入时间轴，请先拖入对应轨道", 3000)
            return
        self.select_clip(clip.id)

    def update_clip_fields(self, clip_id: str, fields: dict) -> None:
        clip = self.project.find_clip(clip_id)
        if not clip:
            return
        clip.title = fields.get("title", clip.title)
        clip.text = fields.get("text", clip.text)
        clip.note = fields.get("note", clip.note)
        clip.emotion = fields.get("emotion", clip.emotion)
        if "duration" in fields:
            clip.duration = max(0.1, float(fields["duration"]))
        if isinstance(fields.get("details"), dict):
            clip.details.update(fields["details"])
            if clip.type == "a_roll":
                clip.details["tone"] = clip.emotion
            else:
                clip.details["sound"] = clip.emotion
            clip.details["note"] = clip.note
        clip.ensure_detail_defaults()
        self.project.dirty = True
        self.script_editor.set_clip(clip)
        self.parameter_panel.set_clip(clip)
        self.timeline.set_project(self.project)
        self.timeline.set_selected_clip(self.selected_clip_id)
        self.rhythm_preview.update()
        self._update_window_title()

    def update_settings(self, settings: dict) -> None:
        existing_theme = self.project.settings.get("theme", "Dark")
        self.project.settings.update(settings)
        self.project.settings["theme"] = existing_theme
        self.project.dirty = True
        self._update_window_title()

    def delete_selected_clip(self) -> None:
        if not self.selected_clip_id:
            self.statusBar().showMessage("No clip selected", 3000)
            return
        if self.project.delete_clip(self.selected_clip_id):
            self.selected_clip_id = None
            self.refresh_all()
            self.statusBar().showMessage("Deleted selected clip", 3000)

    def reorder_clip(self, track_name: str, from_index: int, to_index: int) -> None:
        self.project.move_clip(track_name, from_index, to_index)
        self.refresh_all()
        self.statusBar().showMessage("Reordered timeline clip", 2500)

    def move_clip_to_time(self, clip_id: str, start_time: float) -> None:
        clip = self.project.move_clip_to_time(clip_id, start_time)
        if not clip:
            self.statusBar().showMessage("移动失败：片段不存在", 3000)
            return
        self.selected_clip_id = clip.id
        self.timeline.set_project(self.project)
        self.timeline.set_selected_clip(clip.id)
        self.rhythm_preview.set_project(self.project)
        self.script_editor.set_clip(clip)
        self.parameter_panel.set_clip(clip)
        self._update_window_title()
        self.statusBar().showMessage(f"已移动片段：{clip.title or clip.id}，开始时间 {clip.start_time:.1f}s", 4000)

    def show_status_message(self, message: str, timeout: int = 0) -> None:
        self.statusBar().showMessage(message, timeout)

    def reset_layout(self) -> None:
        self.main_splitter.setSizes([330, 790, 320])
        self.timeline.zoom_slider.setValue(52)
        self.statusBar().showMessage("Layout reset", 3000)

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "ScriptClipper 视频脚本剪辑助手\n\n短视频脚本、节奏与 A-roll/B-roll 时间轴结构化编辑 MVP。",
        )

    def _confirm_discard_changes(self) -> bool:
        if not self.project.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Unsaved changes",
            "当前工程尚未保存，是否继续并丢弃这些修改？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes
