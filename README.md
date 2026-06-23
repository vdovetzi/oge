# Occupancy Grid Editor

[![CI](https://github.com/vdovetzi/oge/actions/workflows/ci.yml/badge.svg)](https://github.com/vdovetzi/oge/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=vdovetzi_oge&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=vdovetzi_oge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small standalone desktop editor for occupancy-grid maps stored in the common
ROS `map_saver` format: YAML metadata plus an 8-bit PGM image. ROS itself is
not required. The application uses only Python's standard libraries

## Features

- Open and save relative or absolute `YAML + PGM` map pairs.
- Paint occupied, free, and unknown cells with an adjustable circular brush.

## Requirements

- Python 3.10 or newer.
- Tk 8.6 or newer, normally included with Python.

On Ubuntu/Debian, install Tk when it is not already available:

```bash
sudo apt install python3-tk
```

## Installation

Install directly from GitHub without cloning the repository manually:

```bash
python3 -m pip install "git+https://github.com/vdovetzi/oge.git"
occupancy-grid-editor
```

To install the latest development version from a specific branch:

```bash
python3 -m pip install "git+https://github.com/vdovetzi/oge.git@main"
```

Alternatively, run directly from a clone:

```bash
git clone https://github.com/vdovetzi/oge.git
cd oge
python3 main.py
```

Or install the application command from an existing local checkout:

```bash
python3 -m pip install .
occupancy-grid-editor
```

Open a map immediately by passing its YAML file:

```bash
occupancy-grid-editor path/to/map.yaml
```

For CLI safety, the map path must resolve inside the directory where the
command was invoked, and the referenced PGM must remain inside the YAML file's
directory. Change into the map's parent directory before opening a map stored
elsewhere. Files selected explicitly through the desktop file dialog are not
restricted to the invocation directory.

## Controls

| Action | Mouse / keyboard |
| --- | --- |
| Paint | Left-drag |
| Pan | `Ctrl` + left-drag or middle-drag |
| Zoom | Mouse wheel, `Ctrl++`, `Ctrl+-` |
| Fit map | `Ctrl+0` |
| Undo / redo | `Ctrl+Z`, `Ctrl+Y`, `Ctrl+Shift+Z` |
| Select brush | `1` Wall, `2` Free, `3` Unknown |
| Open / save | `Ctrl+O`, `Ctrl+S` |

## Supported Format

The editor reads binary `P5` and ASCII `P2` PGM images with a maximum value of
255. YAML support intentionally targets the flat `map_saver` schema:

```yaml
image: map.pgm
resolution: 0.05
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
python -m unittest discover -v
```

GUI tests require a display. In a headless Linux environment, use:

```bash
xvfb-run --auto-servernum coverage run -m unittest discover -v
coverage report
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete workflow.

## License

Distributed under the [MIT License](LICENSE).
