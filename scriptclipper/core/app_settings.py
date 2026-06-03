from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scriptclipper.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


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
        return {"language": DEFAULT_LANGUAGE}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"language": DEFAULT_LANGUAGE}
    language = data.get("language", DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    return {"language": language}


def save_app_settings(settings: dict[str, Any]) -> None:
    path = settings_path()
    language = settings.get("language", DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    payload = {"language": language}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return
