from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scriptclipper.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

DEFAULT_LAYOUT = {
    "main_splitter_sizes": [22, 54, 24],
    "root_splitter_sizes": [72, 28],
}


def settings_path() -> Path:
    override = os.environ.get("SCRIPTCLIPPER_SETTINGS_PATH")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".scriptclipper"
    return root / "ScriptClipper" / "settings.json"


def load_app_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return {"language": DEFAULT_LANGUAGE, "layout": dict(DEFAULT_LAYOUT)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"language": DEFAULT_LANGUAGE, "layout": dict(DEFAULT_LAYOUT)}
    language = data.get("language", DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    return {"language": language, "layout": _normalized_layout(data.get("layout"))}


def save_app_settings(settings: dict[str, Any]) -> None:
    path = settings_path()
    language = settings.get("language", DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    payload = {"language": language}
    payload["layout"] = _normalized_layout(settings.get("layout"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _normalized_layout(layout: Any) -> dict[str, list[int]]:
    if not isinstance(layout, dict):
        return dict(DEFAULT_LAYOUT)
    main_sizes = _normalized_sizes(layout.get("main_splitter_sizes"), 3, DEFAULT_LAYOUT["main_splitter_sizes"])
    root_sizes = _normalized_sizes(layout.get("root_splitter_sizes"), 2, DEFAULT_LAYOUT["root_splitter_sizes"])
    return {
        "main_splitter_sizes": main_sizes,
        "root_splitter_sizes": root_sizes,
    }


def _normalized_sizes(value: Any, count: int, fallback: list[int]) -> list[int]:
    if not isinstance(value, list) or len(value) != count:
        return list(fallback)
    try:
        sizes = [int(item) for item in value]
    except (TypeError, ValueError):
        return list(fallback)
    if any(size <= 0 for size in sizes):
        return list(fallback)
    return sizes
