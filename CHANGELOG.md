# Changelog

All notable changes to this project will be documented in this file.

## v0.1.0 - 2026-06-03

Initial preview release of ScriptClipper.

### Added

- Python/PySide6 desktop application entrypoint.
- ScriptClipper package structure with core project model, file I/O, script export helpers, resources, and UI modules.
- Main window, asset panel, parameter panel, script editor, and timeline widget.
- Windows launch helper via `run_as_admin.bat`.
- Project documentation, MIT license, release changelog, repository instructions, and Git ignore rules.

### Usage

- Install dependencies with `pip install -r requirements.txt`.
- Run the application with `python main.py`.

### Known Issues

- No packaged installer, standalone executable, or release ZIP is available yet.
- Release is source-only and requires a local Python environment.
- Automated tests and CI are not configured yet.
