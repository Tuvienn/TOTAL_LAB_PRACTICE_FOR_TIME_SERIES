from pathlib import Path


def find_practice_root(start: Path | None = None) -> Path:
    """Locate the Practice 2 root from a working directory or nested path."""
    candidate = (start or Path.cwd()).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").is_file() and (directory / "datasets" / "raw").is_dir():
            return directory
    raise FileNotFoundError("Could not locate the Practice 2 root")
