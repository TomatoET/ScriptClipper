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

from scriptclipper.core.app_settings import load_app_settings, save_app_settings
from scriptclipper.core.file_io import export_json, load_project, read_text_file, save_project
from scriptclipper.core.i18n import current_language, set_language, t
from scriptclipper.core.project_model import MIN_CLIP_DURATION, ProjectModel
from scriptclipper.core.script_exporter import export_script_table
from scriptclipper.resources.themes import THEMES
from scriptclipper.ui.asset_panel import AssetPanel
from scriptclipper.ui.parameter_panel import ParameterPanel
from scriptclipper.ui.script_editor import ScriptEditor
from scriptclipper.ui.timeline_widget import RhythmPreview, TimelineWidget, detect_overlap


DEFAULT_MAIN_SPLITTER_RATIO = (22, 54, 24)
DEFAULT_ROOT_SPLITTER_RATIO = (72, 28)
MIN_LEFT_WIDTH = 260
MIN_CENTER_WIDTH = 480
MIN_RIGHT_WIDTH = 280
MIN_TOP_HEIGHT = 360
MIN_TIMELINE_HEIGHT = 180


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project = ProjectModel()
        self.selected_clip_id: str | None = None
        self.theme_actions = {}
        self.language_actions = {}
        self.app_settings = load_app_settings()
        set_language(str(self.app_settings.get("language", "zh-CN")))

        self.resize(1440, 900)
        self._build_actions()
        self._build_layout()
        self._connect_signals()
        self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
        self.refresh_all()
        self.retranslate()
        self.statusBar().showMessage(t("common.ready"))

    def _build_actions(self) -> None:
        self.file_menu = self.menuBar().addMenu("")
        self.new_action = self.file_menu.addAction("")
        self.open_action = self.file_menu.addAction("")
        self.save_action = self.file_menu.addAction("")
        self.save_as_action = self.file_menu.addAction("")
        self.file_menu.addSeparator()
        self.import_txt_action = self.file_menu.addAction("")
        self.export_json_action = self.file_menu.addAction("")
        self.export_script_action = self.file_menu.addAction("")

        self.edit_menu = self.menuBar().addMenu("")
        self.undo_action = self.edit_menu.addAction("")
        self.redo_action = self.edit_menu.addAction("")
        self.delete_action = self.edit_menu.addAction("")
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)

        self.view_menu = self.menuBar().addMenu("")
        self.reset_layout_action = self.view_menu.addAction("")
        self.normalize_aroll_action = self.view_menu.addAction("")
        self.normalize_broll_action = self.view_menu.addAction("")
        self.view_menu.addSeparator()
        self.theme_menu = self.view_menu.addMenu("")
        for theme_name in THEMES:
            action = self.theme_menu.addAction(theme_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=theme_name: self.apply_theme(name))
            self.theme_actions[theme_name] = action

        self.language_menu = self.view_menu.addMenu("")
        self.zh_action = self.language_menu.addAction("")
        self.zh_action.setCheckable(True)
        self.en_action = self.language_menu.addAction("")
        self.en_action.setCheckable(True)
        self.zh_action.triggered.connect(lambda checked=False: self.change_language("zh-CN"))
        self.en_action.triggered.connect(lambda checked=False: self.change_language("en-US"))
        self.language_actions = {"zh-CN": self.zh_action, "en-US": self.en_action}

        self.help_menu = self.menuBar().addMenu("")
        self.about_action = self.help_menu.addAction("")

        self.new_action.triggered.connect(self.new_project)
        self.open_action.triggered.connect(self.open_project)
        self.save_action.triggered.connect(self.save_current_project)
        self.save_as_action.triggered.connect(self.save_project_as)
        self.import_txt_action.triggered.connect(self.import_txt)
        self.export_json_action.triggered.connect(self.export_project_json)
        self.export_script_action.triggered.connect(self.export_traditional_script)
        self.delete_action.triggered.connect(self.delete_selected_clip)
        self.reset_layout_action.triggered.connect(self.reset_layout)
        self.normalize_aroll_action.triggered.connect(lambda checked=False: self.normalize_track_spacing("a_roll"))
        self.normalize_broll_action.triggered.connect(lambda checked=False: self.normalize_track_spacing("b_roll"))
        self.about_action.triggered.connect(self.show_about)

    def _build_layout(self) -> None:
        self.asset_panel = AssetPanel()
        self.rhythm_preview = RhythmPreview()
        self.script_editor = ScriptEditor()
        self.parameter_panel = ParameterPanel()
        self.timeline = TimelineWidget()
        self.setStatusBar(QStatusBar())

        center = QWidget()
        self.center_panel = center
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        center_layout.addWidget(self.rhythm_preview, 3)
        center_layout.addWidget(self.script_editor, 4)

        self.asset_panel.setMinimumWidth(MIN_LEFT_WIDTH)
        self.center_panel.setMinimumWidth(MIN_CENTER_WIDTH)
        self.parameter_panel.setMinimumWidth(MIN_RIGHT_WIDTH)
        self.timeline.setMinimumHeight(MIN_TIMELINE_HEIGHT)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.asset_panel)
        self.main_splitter.addWidget(center)
        self.main_splitter.addWidget(self.parameter_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.setMinimumHeight(MIN_TOP_HEIGHT)

        self.root_splitter = QSplitter(Qt.Vertical)
        self.root_splitter.addWidget(self.main_splitter)
        self.root_splitter.addWidget(self.timeline)
        self.root_splitter.setStretchFactor(0, 1)
        self.root_splitter.setStretchFactor(1, 0)
        self.root_splitter.setChildrenCollapsible(False)
        self.root_splitter.setHandleWidth(8)
        self.main_splitter.splitterMoved.connect(self.save_layout_state)
        self.root_splitter.splitterMoved.connect(self.save_layout_state)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.root_splitter, 1)
        self.setCentralWidget(root)
        self.restore_layout_state()

    def _connect_signals(self) -> None:
        self.asset_panel.asset_selected.connect(self.select_clip_from_asset)
        self.parameter_panel.clip_changed.connect(self.update_clip_fields)
        self.timeline.add_aroll_requested.connect(self.add_aroll_clip)
        self.timeline.add_broll_requested.connect(self.add_broll_clip)
        self.timeline.delete_requested.connect(self.delete_selected_clip)
        self.timeline.clip_selected.connect(self.select_clip)
        self.timeline.asset_dropped.connect(self.add_clip_from_asset)
        self.timeline.clip_moved.connect(self.move_clip_to_time)
        self.timeline.clip_resized.connect(self.resize_clip)
        self.timeline.status_message.connect(self.show_status_message)
        self.script_editor.clip_changed.connect(self.update_clip_fields)

    def retranslate(self) -> None:
        self.file_menu.setTitle(t("menu.file"))
        self.new_action.setText(t("menu.new_project"))
        self.open_action.setText(t("menu.open_project"))
        self.save_action.setText(t("menu.save_project"))
        self.save_as_action.setText(t("menu.save_as"))
        self.import_txt_action.setText(t("menu.import_txt"))
        self.export_json_action.setText(t("menu.export_json"))
        self.export_script_action.setText(t("menu.export_script"))
        self.edit_menu.setTitle(t("menu.edit"))
        self.undo_action.setText(t("menu.undo"))
        self.redo_action.setText(t("menu.redo"))
        self.delete_action.setText(t("menu.delete_selected"))
        self.view_menu.setTitle(t("menu.view"))
        self.reset_layout_action.setText(t("menu.reset_layout"))
        self.normalize_aroll_action.setText(t("menu.normalize_aroll"))
        self.normalize_broll_action.setText(t("menu.normalize_broll"))
        self.theme_menu.setTitle(t("menu.theme"))
        self.language_menu.setTitle(t("menu.language"))
        self.zh_action.setText(t("menu.language.zh"))
        self.en_action.setText(t("menu.language.en"))
        self.help_menu.setTitle(t("menu.help"))
        self.about_action.setText(t("menu.about"))
        self.asset_panel.retranslate()
        self.rhythm_preview.retranslate()
        self.script_editor.retranslate()
        self.parameter_panel.retranslate()
        self.timeline.retranslate()
        self._update_language_checks()
        self._update_theme_checks()
        self._update_window_title()

    def refresh_all(self) -> None:
        self.asset_panel.set_assets(self.project.asset_pool, self.project.broll_asset_pool)
        self.parameter_panel.set_settings(self.project.settings)
        self.timeline.set_project(self.project)
        self.rhythm_preview.set_project(self.project)
        self.select_clip(self.selected_clip_id or "", update_canvas=False)
        self._update_theme_checks()
        self._update_language_checks()
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

    def change_language(self, language: str) -> None:
        set_language(language)
        self.app_settings["language"] = current_language()
        save_app_settings(self.app_settings)
        self.retranslate()
        self.statusBar().showMessage(t("status.language_changed", language=t(f"menu.language.{ 'zh' if current_language() == 'zh-CN' else 'en'}")), 3000)

    def _update_theme_checks(self) -> None:
        active = self.project.settings.get("theme", "Dark")
        for theme_name, action in self.theme_actions.items():
            action.blockSignals(True)
            action.setChecked(theme_name == active)
            action.blockSignals(False)

    def _update_language_checks(self) -> None:
        active = current_language()
        for language, action in self.language_actions.items():
            action.blockSignals(True)
            action.setChecked(language == active)
            action.blockSignals(False)

    def _update_window_title(self) -> None:
        marker = "*" if self.project.dirty else ""
        path = self.project.path or t("common.unsaved")
        self.setWindowTitle(f"{t('app.title')} - {self.project.project_name}{marker} ({path})")

    def new_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.project.reset()
        self.selected_clip_id = None
        self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
        self.refresh_all()
        self.statusBar().showMessage(t("status.new_project"), 4000)

    def open_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, t("dialog.open_project"), "", "ScriptClipper Project (*.sclip);;JSON (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.selected_clip_id = None
            self.apply_theme(self.project.settings.get("theme", "Dark"), mark_dirty=False)
            self.refresh_all()
            self.statusBar().showMessage(t("status.opened", path=path), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.open_failed"), str(exc))

    def save_current_project(self) -> None:
        if not self.project.path:
            self.save_project_as()
            return
        try:
            save_project(self.project, self.project.path)
            self.refresh_all()
            self.statusBar().showMessage(t("status.saved", path=self.project.path), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.save_failed"), str(exc))

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, t("dialog.save_project_as"), "", "ScriptClipper Project (*.sclip)")
        if not path:
            return
        try:
            save_project(self.project, path)
            self.refresh_all()
            self.statusBar().showMessage(t("status.saved", path=self.project.path), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.save_failed"), str(exc))

    def import_txt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, t("dialog.import_txt"), "", "Text Files (*.txt);;All Files (*.*)")
        if not path:
            return
        try:
            count = self.project.import_txt(read_text_file(path))
            self.selected_clip_id = None
            self.refresh_all()
            self.statusBar().showMessage(t("status.imported", count=count, name=Path(path).name), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.import_failed"), str(exc))

    def export_project_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, t("dialog.export_json"), "", "JSON (*.json)")
        if not path:
            return
        try:
            export_json(self.project, path)
            self.statusBar().showMessage(t("status.exported", path=path), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.export_failed"), str(exc))

    def export_traditional_script(self) -> None:
        default_name = f"{self.project.project_name or 'Untitled'}_script.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("dialog.export_script"),
            default_name,
            "Excel Workbook (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return
        try:
            target = export_script_table(self.project, path)
            self.statusBar().showMessage(t("status.exported_script", path=target), 5000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("dialog.export_script_failed"), str(exc))

    def add_clip_from_asset(self, clip_type: str, asset_id: str, start_time: float = 0.0) -> None:
        if clip_type == "a_roll":
            clip = self.project.add_a_roll_clip(asset_id, start_time=start_time)
            message = t("status.added_aroll")
        else:
            clip = self.project.add_b_roll_clip(asset_id, start_time=start_time)
            message = t("status.added_broll")
        if not clip:
            self.statusBar().showMessage(t("status.source_not_found"), 4000)
            return
        self.selected_clip_id = clip.id
        self.refresh_all()
        self.statusBar().showMessage(message, 3000)
        self._show_overlap_warning(clip.type)

    def add_broll_clip(self) -> None:
        clip = self.project.add_b_roll_placeholder(t("placeholder.broll.title"), t("placeholder.broll.content"))
        self.selected_clip_id = clip.id
        self.refresh_all()
        self.statusBar().showMessage(t("status.added_broll_placeholder"), 3000)

    def add_aroll_clip(self) -> None:
        clip = self.project.add_a_roll_placeholder(t("placeholder.aroll.title"), t("placeholder.aroll.content"))
        self.selected_clip_id = clip.id
        self.refresh_all()
        self.statusBar().showMessage(t("status.added_aroll_placeholder"), 3000)

    def select_clip(self, clip_id: str, update_canvas: bool = True) -> None:
        self.selected_clip_id = clip_id or None
        clip = self.project.find_clip(self.selected_clip_id)
        self.script_editor.set_clip(clip)
        self.parameter_panel.set_clip(clip)
        self.asset_panel.select_asset(clip.source_id if clip else None)
        if update_canvas:
            self.timeline.set_selected_clip(self.selected_clip_id)

    def select_clip_from_asset(self, asset_id: str) -> None:
        clip = next((item for item in self.project.a_roll + self.project.b_roll if item.source_id == asset_id), None)
        if not clip:
            self.statusBar().showMessage(t("status.asset_not_on_timeline"), 3000)
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
            clip.duration = max(MIN_CLIP_DURATION, float(fields["duration"]))
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

    def delete_selected_clip(self) -> None:
        if not self.selected_clip_id:
            self.statusBar().showMessage(t("status.no_clip_selected"), 3000)
            return
        if self.project.delete_clip(self.selected_clip_id):
            self.selected_clip_id = None
            self.refresh_all()
            self.statusBar().showMessage(t("status.deleted_clip"), 3000)

    def move_clip_to_time(self, clip_id: str, start_time: float) -> None:
        clip = self.project.move_clip_to_time(clip_id, start_time)
        if not clip:
            self.statusBar().showMessage(t("status.no_clip_selected"), 3000)
            return
        self._refresh_after_timeline_change(clip.id)
        self.statusBar().showMessage(t("timeline.moved_clip", title=clip.title or clip.id, time=clip.start_time), 4000)
        self._show_overlap_warning(clip.type)

    def resize_clip(self, clip_id: str, start_time: float, duration: float) -> None:
        clip = self.project.resize_clip(clip_id, start_time, duration)
        if not clip:
            self.statusBar().showMessage(t("status.no_clip_selected"), 3000)
            return
        self._refresh_after_timeline_change(clip.id)
        self.statusBar().showMessage(
            t("timeline.resized_clip", title=clip.title or clip.id, start=clip.start_time, duration=clip.duration),
            4000,
        )
        self._show_overlap_warning(clip.type)

    def _refresh_after_timeline_change(self, clip_id: str) -> None:
        self.selected_clip_id = clip_id
        clip = self.project.find_clip(clip_id)
        self.timeline.set_project(self.project)
        self.timeline.set_selected_clip(clip_id)
        self.rhythm_preview.set_project(self.project)
        self.script_editor.set_clip(clip)
        self.parameter_panel.set_clip(clip)
        self.asset_panel.select_asset(clip.source_id if clip else None)
        self._update_window_title()

    def _show_overlap_warning(self, clip_type: str) -> None:
        track = self.project.a_roll if clip_type == "a_roll" else self.project.b_roll
        if detect_overlap(track):
            self.statusBar().showMessage(t("timeline.overlap_warning"), 4000)

    def show_status_message(self, message: str, timeout: int = 0) -> None:
        self.statusBar().showMessage(message, timeout)

    def reset_layout(self) -> None:
        self._apply_default_layout()
        self.save_layout_state()
        self.timeline.zoom_slider.setValue(52)
        self.statusBar().showMessage(t("status.layout_reset"), 3000)

    def normalize_track_spacing(self, track_name: str) -> None:
        self.project.normalize_track_spacing(track_name)
        self.refresh_all()
        status_key = "status.normalized_aroll" if track_name == "a_roll" else "status.normalized_broll"
        self.statusBar().showMessage(t(status_key), 3000)

    def _apply_default_layout(self) -> None:
        self._set_splitter_by_ratio(self.main_splitter, DEFAULT_MAIN_SPLITTER_RATIO, 1440)
        self._set_splitter_by_ratio(self.root_splitter, DEFAULT_ROOT_SPLITTER_RATIO, 860)

    def restore_layout_state(self) -> None:
        layout = self.app_settings.get("layout")
        if not isinstance(layout, dict):
            self._apply_default_layout()
            return
        main_sizes = self._valid_sizes(layout.get("main_splitter_sizes"), 3)
        root_sizes = self._valid_sizes(layout.get("root_splitter_sizes"), 2)
        if main_sizes:
            self.main_splitter.setSizes(main_sizes)
        else:
            self._set_splitter_by_ratio(self.main_splitter, DEFAULT_MAIN_SPLITTER_RATIO, 1440)
        if root_sizes:
            self.root_splitter.setSizes(root_sizes)
        else:
            self._set_splitter_by_ratio(self.root_splitter, DEFAULT_ROOT_SPLITTER_RATIO, 860)

    def save_layout_state(self, *args: object) -> None:
        self.app_settings["layout"] = {
            "main_splitter_sizes": self.main_splitter.sizes(),
            "root_splitter_sizes": self.root_splitter.sizes(),
        }
        save_app_settings(self.app_settings)

    def _set_splitter_by_ratio(self, splitter: QSplitter, ratio: tuple[int, ...], total: int) -> None:
        ratio_total = sum(ratio) or 1
        splitter.setSizes([max(1, round(total * value / ratio_total)) for value in ratio])

    def _valid_sizes(self, sizes: object, count: int) -> list[int] | None:
        if not isinstance(sizes, list) or len(sizes) != count:
            return None
        try:
            normalized = [int(size) for size in sizes]
        except (TypeError, ValueError):
            return None
        if any(size <= 0 for size in normalized):
            return None
        return normalized

    def show_about(self) -> None:
        QMessageBox.information(self, t("dialog.about_title"), t("dialog.about_body"))

    def _confirm_discard_changes(self) -> bool:
        if not self.project.dirty:
            return True
        result = QMessageBox.question(
            self,
            t("dialog.unsaved_title"),
            t("dialog.unsaved_body"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes
