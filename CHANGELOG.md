# Changelog

This project follows [Semantic Versioning](https://semver.org/) and the
[Keep a Changelog](https://keepachangelog.com/) format.

## [Unreleased]

No unreleased changes.

## [0.1.1] - 2026-06-23

### Added

- Automated CI, coverage, SonarCloud analysis, and tag-based releases.
- Packaging metadata and the `occupancy-grid-editor` command.
- Contributor, security, issue, and pull-request documentation.
- CLI path validation for maps opened from command-line arguments.
- Regression tests for path traversal, PGM/YAML round trips, canvas editing, and UI workflows.

### Changed

- Refactored PGM parsing into smaller reader methods to reduce cognitive complexity.
- Upgraded SonarCloud scanning to the current GitHub Action and removed quality-gate polling
  from the workflow to avoid token-scope failures after report upload.

### Security

- Prevented command-line map paths from escaping the invocation directory.
- Prevented YAML `image` references from resolving outside the map directory.

## [0.1.0] - 2026-06-23

### Added

- Standalone tkinter occupancy-grid editor.
- P2/P5 PGM and map_saver YAML loading and saving.
- Wall, free, and unknown brushes.
- Viewport-bounded zoom, pan, fit, undo, and redo.

[Unreleased]: https://github.com/vdovetzi/oge/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/vdovetzi/oge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vdovetzi/oge/releases/tag/v0.1.0
