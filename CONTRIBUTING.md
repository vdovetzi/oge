# Contributing

Thank you for helping improve Occupancy Grid Editor.

## Setup

1. Fork and clone the repository.
2. Create a branch from `main`.
3. Create a virtual environment and install development tools:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -e ".[dev]"
   ```

## Before Opening a Pull Request

Run the same checks as CI:

```bash
ruff check .
python -m unittest discover -v
python -m build
```

Run GUI tests under Xvfb when no desktop display is available:

```bash
xvfb-run --auto-servernum coverage run -m unittest discover -v
coverage report --fail-under=50
```

## Guidelines

- Keep the runtime dependency-free and compatible with Python 3.10+.
- Add regression tests for bug fixes and tests for new behavior.
- Keep map-format code independent from tkinter.
- Avoid loading a fully zoomed map into memory; rendering must remain bounded
  by the visible viewport.
- Update README and CHANGELOG when behavior visible to users changes.


