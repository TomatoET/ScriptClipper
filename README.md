# ScriptClipper

ScriptClipper is a local desktop application for editing video scripts and related project data. The current implementation is a Python application built with PySide6.

## Requirements

- Windows
- Python 3.11 or newer
- Dependencies listed in `requirements.txt`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script activation, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

On Windows, `run_as_admin.bat` can also launch the app with administrator elevation when needed.

## Project Layout

```text
.
├── main.py
├── requirements.txt
├── run_as_admin.bat
└── scriptclipper/
    ├── core/
    ├── resources/
    └── ui/
```

## Notes

- Keep generated caches such as `__pycache__/` out of version control.
- Do not commit secrets, tokens, local credentials, `.env` files, or machine-specific paths.
- Future changes should be developed on a branch and submitted through a pull request.
