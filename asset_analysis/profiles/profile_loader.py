from __future__ import annotations

from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like
from .profile_schema import validate_profile_schema


BUILTIN_PROFILES = {
    "conservative": "examples/profiles/conservative.profile.yaml",
    "balanced": "examples/profiles/balanced.profile.yaml",
    "growth": "examples/profiles/growth.profile.yaml",
    "qdii_growth": "examples/profiles/qdii_growth.profile.yaml",
    "cash_defensive": "examples/profiles/cash_defensive.profile.yaml",
}


def list_builtin_profiles() -> list[str]:
    return list(BUILTIN_PROFILES.keys())


def resolve_builtin_profile_path(name: str) -> str | None:
    return BUILTIN_PROFILES.get(name)


def load_profile(profile_path: str | Path) -> dict[str, Any]:
    path = Path(profile_path)
    payload = _load_yaml_like(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Profile file root must be a mapping.")
    errors = validate_profile_schema(payload)
    if errors:
        raise ValueError("; ".join(errors))
    return payload
