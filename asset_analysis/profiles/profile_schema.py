from __future__ import annotations

from typing import Any


REQUIRED_PROFILE_FIELDS = ("name", "display_name", "version", "description")


def validate_profile_schema(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Profile payload root must be a mapping."]
    profile = data.get("profile")
    if not isinstance(profile, dict):
        return ["Profile file must contain a 'profile' mapping."]
    for field in REQUIRED_PROFILE_FIELDS:
        value = profile.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"profile.{field} is required.")
    for section in ("analysis", "preflight", "chat_summary"):
        value = data.get(section, {})
        if value not in ({}, None) and not isinstance(value, dict):
            errors.append(f"{section} must be a mapping when present.")
    risk_notes = data.get("risk_notes", [])
    if risk_notes not in (None, []) and not isinstance(risk_notes, list):
        errors.append("risk_notes must be a list when present.")
    return errors
