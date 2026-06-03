# Contributing

Thank you for considering a contribution to ScriptClipper.

## Development Workflow

- Do not work directly on `main`.
- Create a feature branch for each change.
- Open a pull request for review before merging.
- Keep changes scoped and avoid unrelated refactors.
- Do not commit secrets, credentials, `.env` files, generated caches, or machine-specific paths.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Code Guidelines

- Prefer small, readable changes.
- Keep UI behavior consistent with the existing PySide6 structure.
- Keep file I/O local and explicit.
- Avoid adding online services, telemetry, or cloud dependencies without a clear proposal.
- Add tests when changing shared logic or project file behavior.

## Pull Request Checklist

- The app starts locally with `python main.py`.
- The working tree does not include generated files such as `__pycache__/`.
- The change does not include secrets or local credentials.
- Documentation is updated when behavior changes.
- The pull request explains what changed and how it was checked.

## Commit Messages

Use concise conventional-style messages when possible:

- `docs: update README`
- `fix: handle empty script import`
- `feat: add timeline export option`
- `chore: update project metadata`
