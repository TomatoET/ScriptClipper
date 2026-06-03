# ScriptClipper

ScriptClipper is a local desktop application for editing video scripts and related project data. It is built with Python and PySide6, with an offline-first workflow for importing text, organizing A-Roll and B-Roll material, editing clip metadata, and exporting script tables.

## Features

- Local PySide6 desktop interface.
- TXT import that splits script text into editable A-Roll assets.
- A-Roll and B-Roll asset panels with drag-and-drop timeline placement.
- Timeline view with zoom controls, clip selection, and simple rhythm preview.
- Clip metadata editing for script copy, visual notes, sound notes, and duration.
- Project save and open support using local JSON project data.
- Export support for project JSON and script tables.
- Theme selection for the desktop UI.

## Installation

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

## Running

```powershell
python main.py
```

On Windows, `run_as_admin.bat` can also launch the app with administrator elevation when needed.

## Packaging

The project does not have a finalized packaging pipeline yet. For `v0.1.0`, the GitHub Release is source-only.

A future Windows build can use PyInstaller or a similar packager. A starting point is:

```powershell
pip install pyinstaller
pyinstaller --windowed --name ScriptClipper --icon assets/icons/app-icon.ico main.py
```

That command is not yet validated as an official release build. Before publishing binaries, verify the generated app launches correctly, includes the Qt resources, and can save, open, import, and export files.

## Screenshots

Screenshots are not included yet. When available, place them under:

```text
docs/screenshots/
```

Recommended files:

- `main-window.png`
- `timeline.png`
- `export-dialog.png`

## Project Layout

```text
.
├── AGENTS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── main.py
├── requirements.txt
├── run_as_admin.bat
└── scriptclipper/
    ├── core/
    ├── resources/
    └── ui/
```

## FAQ

### Is ScriptClipper cloud-based?

No. The current version is a local desktop application.

### Does the project include AI or online services?

No. `v0.1.0` does not include cloud services, online APIs, or AI backends.

### Where are projects stored?

Projects are saved to local files through the app's save/open workflow.

### Can I install it as a standalone app?

Not yet. `v0.1.0` is source-only and requires Python plus the dependencies in `requirements.txt`.

### Why does the project include `run_as_admin.bat`?

It is a Windows helper for launching the application with administrator elevation when needed. Most development runs should use `python main.py`.

## Roadmap

- `v0.1.x`: improve documentation, add screenshots, and validate basic packaging.
- `v0.2.x`: add automated tests and CI.
- `v0.3.x`: improve project file compatibility and export workflows.
- Future: publish a validated Windows executable or installer.

## Notes

- Keep generated caches such as `__pycache__/` out of version control.
- Do not commit secrets, tokens, local credentials, `.env` files, or machine-specific paths.
- Future changes should be developed on a branch and submitted through a pull request.
