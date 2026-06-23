from pathlib import Path


def resolve_within(base_directory, candidate):
    """Resolve candidate and require it to remain inside base_directory."""
    base = Path(base_directory).resolve(strict=True)
    target = (base / candidate).resolve(strict=True)
    try:
        target.relative_to(base)
    except ValueError as error:
        raise ValueError(f"Access denied: {candidate}") from error
    return target


def resolve_cli_map(candidate, base_directory=None):
    """Validate an agent-controlled CLI map path before file-system access."""
    base = Path.cwd() if base_directory is None else Path(base_directory)
    target = resolve_within(base, candidate)
    if target.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("The map path must have a .yaml or .yml extension")
    if not target.is_file():
        raise ValueError("The map path must point to a regular file")
    return target
