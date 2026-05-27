from __future__ import annotations

from pathlib import Path


def find_project_root(start: str | Path | None = None) -> Path:
    current = Path(start or __file__).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "asset_analysis").exists() and (candidate / "README.md").exists():
            return candidate
    raise FileNotFoundError("Project root could not be located from the given start path.")
