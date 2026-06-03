from __future__ import annotations

import json
from pathlib import Path

from .project_model import ProjectModel


def load_project(path: str | Path) -> ProjectModel:
    source = Path(path)
    with source.open("r", encoding="utf-8") as file:
        data = json.load(file)
    project = ProjectModel.from_dict(data)
    project.path = str(source)
    project.dirty = False
    return project


def save_project(project: ProjectModel, path: str | Path) -> None:
    target = Path(path)
    if target.suffix.lower() != ".sclip":
        target = target.with_suffix(".sclip")
    project.project_name = target.stem
    with target.open("w", encoding="utf-8") as file:
        json.dump(project.to_dict(), file, ensure_ascii=False, indent=2)
    project.path = str(target)
    project.dirty = False


def export_json(project: ProjectModel, path: str | Path) -> None:
    target = Path(path)
    if target.suffix.lower() != ".json":
        target = target.with_suffix(".json")
    with target.open("w", encoding="utf-8") as file:
        json.dump(project.to_dict(), file, ensure_ascii=False, indent=2)


def read_text_file(path: str | Path) -> str:
    source = Path(path)
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return source.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return source.read_text(encoding="utf-8", errors="ignore")
