from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from scriptclipper.core.project_model import ProjectModel, TimelineClip


HEADERS = ["主题", "场景", "文案内容", "画面内容", "音效"]


def build_script_rows(project: ProjectModel) -> list[dict[str, str]]:
    a_roll = sorted(project.a_roll, key=lambda clip: clip.start_time)
    b_roll = sorted(project.b_roll, key=lambda clip: clip.start_time)
    row_count = max(len(a_roll), len(b_roll), 1)
    rows: list[dict[str, str]] = []
    theme = project.project_name or "Untitled"
    for index in range(row_count):
        a_clip = a_roll[index] if index < len(a_roll) else None
        b_clip = b_roll[index] if index < len(b_roll) else None
        rows.append(
            {
                "主题": theme if index == 0 else "",
                "场景": _scene_text(index, a_clip, b_clip),
                "文案内容": _copy_text(a_clip),
                "画面内容": _visual_text(a_clip, b_clip),
                "音效": _sound_text(a_clip, b_clip),
            }
        )
    return rows


def export_script_table(project: ProjectModel, path: str | Path) -> Path:
    target = Path(path)
    if target.suffix.lower() == ".csv":
        export_script_csv(project, target)
        return target
    if target.suffix.lower() != ".xlsx":
        target = target.with_suffix(".xlsx")
    export_script_xlsx(project, target)
    return target


def export_script_csv(project: ProjectModel, path: str | Path) -> None:
    target = Path(path)
    if target.suffix.lower() != ".csv":
        target = target.with_suffix(".csv")
    rows = build_script_rows(project)
    with target.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def export_script_xlsx(project: ProjectModel, path: str | Path) -> None:
    target = Path(path)
    rows = build_script_rows(project)
    sheet_xml = _worksheet_xml(rows)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        archive.writestr("xl/styles.xml", _styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _scene_text(index: int, a_clip: TimelineClip | None, b_clip: TimelineClip | None) -> str:
    title = (a_clip.title if a_clip else "") or (b_clip.title if b_clip else "")
    return title or f"场景 {index + 1}"


def _copy_text(a_clip: TimelineClip | None) -> str:
    if not a_clip:
        return ""
    parts = [a_clip.text.strip()]
    if a_clip.note.strip():
        parts.append(f"备注：{a_clip.note.strip()}")
    return "\n".join(part for part in parts if part)


def _visual_text(a_clip: TimelineClip | None, b_clip: TimelineClip | None) -> str:
    parts: list[str] = []
    if b_clip:
        title = b_clip.title.strip()
        text = b_clip.text.strip()
        note = b_clip.note.strip()
        if title:
            parts.append(title)
        if text:
            parts.append(text)
        if note:
            parts.append(note)
    if a_clip and a_clip.note.strip():
        parts.append(f"口播画面备注：{a_clip.note.strip()}")
    return "\n".join(parts)


def _sound_text(a_clip: TimelineClip | None, b_clip: TimelineClip | None) -> str:
    parts: list[str] = []
    if a_clip and a_clip.emotion.strip():
        parts.append(f"节奏/情绪：{a_clip.emotion.strip()}")
    if b_clip and b_clip.emotion.strip():
        parts.append(f"音效：{b_clip.emotion.strip()}")
    return "\n".join(parts)


def _worksheet_xml(rows: list[dict[str, str]]) -> str:
    sheet_rows = [_row_xml(1, HEADERS, style=1)]
    for row_index, row in enumerate(rows, start=2):
        sheet_rows.append(_row_xml(row_index, [row[header] for header in HEADERS], style=2))
    dimension_end = f"E{len(rows) + 1}"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="A1:{dimension_end}"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="28"/>
  <cols>
    <col min="1" max="1" width="16" customWidth="1"/>
    <col min="2" max="2" width="18" customWidth="1"/>
    <col min="3" max="3" width="58" customWidth="1"/>
    <col min="4" max="4" width="68" customWidth="1"/>
    <col min="5" max="5" width="22" customWidth="1"/>
  </cols>
  <sheetData>
    {''.join(sheet_rows)}
  </sheetData>
</worksheet>"""


def _row_xml(row_index: int, values: list[str], style: int) -> str:
    height = 34 if row_index == 1 else 72
    cells = []
    for offset, value in enumerate(values):
        col = chr(ord("A") + offset)
        cells.append(_cell_xml(f"{col}{row_index}", value, style))
    return f'<row r="{row_index}" ht="{height}" customHeight="1">{"".join(cells)}</row>'


def _cell_xml(ref: str, value: str, style: int) -> str:
    safe_value = escape(value or "")
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{safe_value}</t></is></c>'


def _content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""


def _root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""


def _workbook_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="传统视频脚本" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""


def _workbook_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="12"/><name val="Microsoft YaHei"/></font>
    <font><b/><sz val="13"/><name val="Microsoft YaHei"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFEFF1F4"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color rgb="FFD9DEE8"/></left><right style="thin"><color rgb="FFD9DEE8"/></right><top style="thin"><color rgb="FFD9DEE8"/></top><bottom style="thin"><color rgb="FFD9DEE8"/></bottom><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""
