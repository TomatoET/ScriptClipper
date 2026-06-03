from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass, field
from typing import Any


MIN_CLIP_DURATION = 0.5

DEFAULT_SETTINGS = {
    "aspect_ratio": "9:16",
    "platform": "抖音",
    "speech_speed": "中",
    "subtitle_style": "白字黑边",
    "broll_default_duration": 3,
    "rhythm_density": "中",
    "theme": "Dark",
}

DEFAULT_AROLL_ASSETS = [
    {
        "id": "a001",
        "type": "a_roll",
        "title": "开场钩子",
        "text": "准备好看一个更清晰、更有节奏的项目展示了吗？",
        "duration": 2.4,
        "note": "正面口播，快速进入主题",
        "emotion": "明快",
    },
    {
        "id": "a002",
        "type": "a_roll",
        "title": "项目介绍",
        "text": "这部分用于说明项目是什么、解决什么问题，以及最值得观众记住的亮点。",
        "duration": 3.6,
        "note": "搭配产品或流程画面",
        "emotion": "稳",
    },
    {
        "id": "a003",
        "type": "a_roll",
        "title": "结尾引导",
        "text": "如果你想看完整过程，可以继续关注后面的演示和拆解。",
        "duration": 2.8,
        "note": "镜头回到口播，留出收尾停顿",
        "emotion": "收束",
    },
]

DEFAULT_BROLL_ASSETS = [
    {"id": "b001", "type": "b_roll", "title": "产品特写", "duration": 3.0, "note": "展示产品或关键物体细节"},
    {"id": "b002", "type": "b_roll", "title": "人物操作", "duration": 3.0, "note": "展示手部、表情或使用过程"},
    {"id": "b003", "type": "b_roll", "title": "场景建立", "duration": 4.0, "note": "交代空间、环境或氛围"},
    {"id": "b004", "type": "b_roll", "title": "数据/图表", "duration": 3.0, "note": "用于解释数字、对比或结论"},
]


def make_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def estimate_duration(text: str) -> float:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_words = len(re.findall(r"[A-Za-z0-9]+", text))
    units = chinese_chars + other_words
    return max(MIN_CLIP_DURATION, round(units / 5.0, 1))


def split_script_text(text: str) -> list[str]:
    parts = re.split(r"[\r\n。！？!?；;]+", text)
    return [part.strip() for part in parts if part.strip()]


def normalize_clip_type(value: str) -> str:
    normalized = value.replace("-", "_")
    if normalized in {"a_roll", "b_roll"}:
        return normalized
    return "a_roll"


@dataclass
class ARollAsset:
    id: str
    text: str
    duration: float
    type: str = "a_roll"
    title: str = ""
    note: str = ""
    emotion: str = ""

    @classmethod
    def from_text(cls, text: str, index: int) -> "ARollAsset":
        return cls(
            id=f"a{index:03d}",
            text=text,
            duration=estimate_duration(text),
            title=f"台词 {index}",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ARollAsset":
        return cls(
            id=str(data.get("id", make_id("a"))),
            type="a_roll",
            title=str(data.get("title", "")),
            text=str(data.get("text", data.get("content", ""))),
            duration=max(MIN_CLIP_DURATION, float(data.get("duration", 1.0))),
            note=str(data.get("note", "")),
            emotion=str(data.get("emotion", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "text": self.text,
            "duration": self.duration,
            "note": self.note,
            "emotion": self.emotion,
        }


@dataclass
class BRollAsset:
    id: str
    title: str
    duration: float
    note: str = ""
    type: str = "b_roll"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BRollAsset":
        return cls(
            id=str(data.get("id", make_id("b"))),
            type="b_roll",
            title=str(data.get("title", "画面占位")),
            duration=max(MIN_CLIP_DURATION, float(data.get("duration", 3.0))),
            note=str(data.get("note", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "duration": self.duration,
            "note": self.note,
        }


@dataclass
class TimelineClip:
    id: str
    type: str
    duration: float
    title: str = ""
    source_id: str = ""
    text: str = ""
    note: str = ""
    emotion: str = ""
    start_time: float = 0.0
    track: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_a_asset(cls, asset: ARollAsset) -> "TimelineClip":
        clip = cls(
            id=make_id("clip"),
            type="a_roll",
            source_id=asset.id,
            title=asset.title or asset.id,
            text=asset.text,
            duration=max(MIN_CLIP_DURATION, asset.duration),
            note=asset.note,
            emotion=asset.emotion,
            track="a_roll",
        )
        clip.ensure_detail_defaults()
        return clip

    @classmethod
    def from_b_asset(cls, asset: BRollAsset, number: int) -> "TimelineClip":
        clip = cls(
            id=make_id("clip"),
            type="b_roll",
            source_id=asset.id,
            title=asset.title or f"画面{number}",
            duration=max(MIN_CLIP_DURATION, float(asset.duration)),
            note=asset.note,
            track="b_roll",
        )
        clip.ensure_detail_defaults()
        return clip

    @classmethod
    def new_broll(cls, duration: float, number: int) -> "TimelineClip":
        clip = cls(
            id=make_id("clip"),
            type="b_roll",
            title=f"画面{number}",
            duration=max(MIN_CLIP_DURATION, float(duration)),
            note="画面占位",
            track="b_roll",
        )
        clip.ensure_detail_defaults()
        return clip

    @classmethod
    def from_dict(cls, data: dict[str, Any], clip_type: str, default_start: float = 0.0) -> "TimelineClip":
        normalized_type = normalize_clip_type(str(data.get("type", clip_type)))
        details = data.get("details") if isinstance(data.get("details"), dict) else {}
        note = str(data.get("note", details.get("note", "")))
        emotion_key = "tone" if normalized_type == "a_roll" else "sound"
        clip = cls(
            id=str(data.get("id", make_id("clip"))),
            type=normalized_type,
            source_id=str(data.get("source_id", "")),
            title=str(data.get("title", "")),
            text=str(data.get("text", data.get("content", ""))),
            duration=max(MIN_CLIP_DURATION, float(data.get("duration", MIN_CLIP_DURATION))),
            note=note,
            emotion=str(data.get("emotion", details.get(emotion_key, ""))),
            start_time=max(0.0, float(data.get("startTime", data.get("start_time", default_start)))),
            track=normalize_clip_type(str(data.get("track", normalized_type))),
            details=dict(details),
        )
        clip.ensure_detail_defaults()
        return clip

    def ensure_detail_defaults(self) -> None:
        if self.type == "a_roll":
            defaults = {
                "tone": self.emotion,
                "speed": "",
                "pauseHint": "",
                "subtitleFocus": "",
                "note": self.note,
            }
        else:
            defaults = {
                "shotSize": "",
                "cameraMove": "",
                "action": "",
                "keywords": "",
                "sound": self.emotion,
                "note": self.note,
            }
        merged = dict(defaults)
        merged.update(self.details or {})
        self.details = merged
        self.track = self.track or self.type

    def to_dict(self) -> dict[str, Any]:
        self.ensure_detail_defaults()
        return {
            "id": self.id,
            "type": self.type,
            "source_id": self.source_id,
            "track": self.track or self.type,
            "title": self.title,
            "content": self.text,
            "text": self.text,
            "startTime": round(float(self.start_time), 3),
            "duration": round(float(self.duration), 3),
            "note": self.note,
            "emotion": self.emotion,
            "details": self.details,
        }


@dataclass
class ProjectModel:
    project_name: str = "Untitled"
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    asset_pool: list[ARollAsset] = field(
        default_factory=lambda: [ARollAsset.from_dict(item) for item in DEFAULT_AROLL_ASSETS]
    )
    broll_asset_pool: list[BRollAsset] = field(
        default_factory=lambda: [BRollAsset.from_dict(item) for item in DEFAULT_BROLL_ASSETS]
    )
    a_roll: list[TimelineClip] = field(default_factory=list)
    b_roll: list[TimelineClip] = field(default_factory=list)
    path: str | None = None
    dirty: bool = False

    def reset(self) -> None:
        self.project_name = "Untitled"
        self.settings = dict(DEFAULT_SETTINGS)
        self.asset_pool = [ARollAsset.from_dict(item) for item in DEFAULT_AROLL_ASSETS]
        self.broll_asset_pool = [BRollAsset.from_dict(item) for item in DEFAULT_BROLL_ASSETS]
        self.a_roll = []
        self.b_roll = []
        self.path = None
        self.dirty = False

    def import_txt(self, text: str) -> int:
        self.asset_pool = [
            ARollAsset.from_text(part, index)
            for index, part in enumerate(split_script_text(text), start=1)
        ]
        self.dirty = True
        return len(self.asset_pool)

    def add_a_roll_clip(self, source_id: str, start_time: float | None = None) -> TimelineClip | None:
        asset = next((item for item in self.asset_pool if item.id == source_id), None)
        if not asset:
            return None
        clip = TimelineClip.from_a_asset(asset)
        clip.start_time = self._clip_start("a_roll", start_time)
        self.a_roll.append(clip)
        self.dirty = True
        return clip

    def add_b_roll_clip(self, source_id: str | None = None, start_time: float | None = None) -> TimelineClip:
        if source_id:
            asset = next((item for item in self.broll_asset_pool if item.id == source_id), None)
            if asset:
                clip = TimelineClip.from_b_asset(asset, len(self.b_roll) + 1)
            else:
                clip = TimelineClip.new_broll(self.settings.get("broll_default_duration", 3), len(self.b_roll) + 1)
        else:
            clip = TimelineClip.new_broll(self.settings.get("broll_default_duration", 3), len(self.b_roll) + 1)
        clip.start_time = self._clip_start("b_roll", start_time)
        self.b_roll.append(clip)
        self.dirty = True
        return clip

    def _clip_start(self, track_name: str, start_time: float | None) -> float:
        if start_time is None:
            return self.next_start_time(track_name)
        return max(0.0, round(float(start_time), 1))

    def find_clip(self, clip_id: str | None) -> TimelineClip | None:
        if not clip_id:
            return None
        for clip in self.a_roll + self.b_roll:
            if clip.id == clip_id:
                return clip
        return None

    def delete_clip(self, clip_id: str) -> bool:
        for track in (self.a_roll, self.b_roll):
            for index, clip in enumerate(track):
                if clip.id == clip_id:
                    del track[index]
                    self.dirty = True
                    return True
        return False

    def move_clip(self, track_name: str, from_index: int, to_index: int) -> None:
        track = self.a_roll if track_name == "a_roll" else self.b_roll
        if from_index < 0 or from_index >= len(track):
            return
        to_index = max(0, min(to_index, len(track) - 1))
        clip = track.pop(from_index)
        track.insert(to_index, clip)
        self.dirty = True

    def move_clip_to_time(self, clip_id: str, start_time: float) -> TimelineClip | None:
        clip = self.find_clip(clip_id)
        if not clip:
            return None
        clip.start_time = max(0.0, round(float(start_time), 1))
        self.dirty = True
        return clip

    def resize_clip(self, clip_id: str, start_time: float, duration: float) -> TimelineClip | None:
        clip = self.find_clip(clip_id)
        if not clip:
            return None
        clip.start_time = max(0.0, round(float(start_time), 1))
        clip.duration = max(MIN_CLIP_DURATION, round(float(duration), 1))
        self.dirty = True
        return clip

    def next_start_time(self, track_name: str) -> float:
        track = self.a_roll if track_name == "a_roll" else self.b_roll
        return round(max((clip.start_time + clip.duration for clip in track), default=0.0), 1)

    def timeline_duration(self) -> float:
        return max(
            max((clip.start_time + clip.duration for clip in self.a_roll), default=0.0),
            max((clip.start_time + clip.duration for clip in self.b_roll), default=0.0),
            15.0,
        )

    def tick_count(self) -> int:
        return int(math.ceil(self.timeline_duration() / 5.0)) + 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectModel":
        settings = dict(DEFAULT_SETTINGS)
        settings.update(data.get("settings") or {})
        timeline = data.get("timeline") or {}
        aroll_assets = data.get("asset_pool")
        broll_assets = data.get("broll_asset_pool") or DEFAULT_BROLL_ASSETS
        return cls(
            project_name=str(data.get("project_name", "Untitled")),
            settings=settings,
            asset_pool=[ARollAsset.from_dict(item) for item in (aroll_assets if aroll_assets is not None else DEFAULT_AROLL_ASSETS)],
            broll_asset_pool=[BRollAsset.from_dict(item) for item in broll_assets],
            a_roll=_clips_from_track(timeline.get("a_roll", []), "a_roll"),
            b_roll=_clips_from_track(timeline.get("b_roll", []), "b_roll"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "settings": self.settings,
            "asset_pool": [item.to_dict() for item in self.asset_pool],
            "broll_asset_pool": [item.to_dict() for item in self.broll_asset_pool],
            "timeline": {
                "a_roll": [clip.to_dict() for clip in self.a_roll],
                "b_roll": [clip.to_dict() for clip in self.b_roll],
            },
        }


def _clips_from_track(items: list[dict[str, Any]], clip_type: str) -> list[TimelineClip]:
    clips: list[TimelineClip] = []
    cursor = 0.0
    for item in items:
        clip = TimelineClip.from_dict(item, clip_type, default_start=cursor)
        clips.append(clip)
        cursor = clip.start_time + clip.duration
    return clips
