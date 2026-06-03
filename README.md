# ScriptClipper

[简体中文](./README.zh-CN.md) | English

ScriptClipper is a local desktop application for editing video scripts and related project data. It is built with Python and PySide6, with an offline-first workflow for importing text, organizing A-Roll and B-Roll material, editing clip metadata, and exporting script tables.

## Download

Please download the Windows package from GitHub Releases:

```text
ScriptClipper-v0.1.0-windows-x64.zip
```

Extract the archive and double-click `ScriptClipper.exe`.

## Features

- Local PySide6 desktop interface.
- A-Roll / B-Roll dual-track timeline.
- Structured script editor.
- Content detail panel for narration and visual clips.
- Clip dragging and duration resizing.
- Simplified Chinese / English UI switching.
- `.sclip` project save and open workflow.
- TXT import.
- Export support for project JSON and script tables.
- Windows portable package.

## Local Development

### Requirements

- Windows
- Python 3.11 or newer
- Dependencies listed in `requirements.txt`

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script activation, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Run

```powershell
python main.py
```

## Packaging

Build the Windows portable package with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The build output is generated under `release/`. Do not commit `release/`, `build/`, or `dist/` to the source repository. Release artifacts should be uploaded only as GitHub Release attachments.

## Project Layout

```text
.
├── assets/
├── scriptclipper/
│   ├── core/
│   ├── resources/
│   └── ui/
├── scripts/
├── main.py
├── ScriptClipper.spec
├── README.md
└── README.zh-CN.md
```

## FAQ

### Is ScriptClipper cloud-based?

No. The current version is a local desktop application.

### Does the project include AI or online services?

No. `v0.1.0` does not include cloud services, online APIs, or AI backends.

### Where are projects stored?

Projects are saved to local `.sclip` files through the app's save/open workflow.

### Can I install it as a standalone app?

The current Windows release is a portable package. Download the zip from GitHub Releases, extract it, and run `ScriptClipper.exe`.

## Roadmap

- Improve timeline interactions and zoom behavior.
- Add richer asset management.
- Add more export formats.
- Explore video preview and FFmpeg support.

## Notes

- Keep generated caches such as `__pycache__/` out of version control.
- Do not commit secrets, tokens, local credentials, `.env` files, or machine-specific paths.
- Future changes should be developed on a branch and submitted through a pull request.
