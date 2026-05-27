from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..schema.errors import make_error
from .profile_loader import load_profile, resolve_builtin_profile_path


def resolve_profile_config(workflow_config: dict, profile_path: str | None = None) -> dict[str, Any]:
    if not isinstance(workflow_config, dict):
        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "profile": None,
            "effective_config": {},
            "errors": [make_error("profile", "INVALID_CONFIG", "Workflow config root must be a mapping.")],
            "warnings": [],
        }

    requested_profile = workflow_config.get("profile", {}) or {}
    if not isinstance(requested_profile, dict):
        requested_profile = {}
    requested_name = str(requested_profile.get("name") or "balanced").strip() or "balanced"
    resolved_profile_path = profile_path or requested_profile.get("file") or resolve_builtin_profile_path(requested_name)
    if not resolved_profile_path:
        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "profile": None,
            "effective_config": {},
            "errors": [make_error("profile", "PROFILE_NOT_FOUND", f"Unknown profile: {requested_name}")],
            "warnings": [],
        }
    path = Path(str(resolved_profile_path))
    if not path.exists():
        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "profile": None,
            "effective_config": {},
            "errors": [make_error("profile", "PROFILE_FILE_NOT_FOUND", f"Profile file not found: {path}")],
            "warnings": [],
        }

    try:
        loaded = load_profile(path)
    except Exception as exc:
        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "profile": None,
            "effective_config": {},
            "errors": [make_error("profile", "PROFILE_LOAD_ERROR", str(exc), {"path": str(path)})],
            "warnings": [],
        }

    effective = _deep_merge(deepcopy(loaded), deepcopy(workflow_config))
    effective["profile"] = {
        "name": str(loaded.get("profile", {}).get("name", requested_name)),
        "file": str(path),
    }
    errors, warnings = _validate_referenced_files(effective)
    profile_meta = {
        "name": str(loaded.get("profile", {}).get("name", requested_name)),
        "display_name": str(loaded.get("profile", {}).get("display_name", requested_name)),
        "version": str(loaded.get("profile", {}).get("version", "1.0.0")),
        "source": str(path),
    }
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "profile": profile_meta,
        "effective_config": effective,
        "errors": errors,
        "warnings": warnings,
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _validate_referenced_files(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    analysis = config.get("analysis", {}) or {}
    fields = {
        "rules": analysis.get("rules"),
        "asset_groups": analysis.get("asset_groups"),
        "portfolio_template": analysis.get("portfolio_template"),
        "overseas_exposure": analysis.get("overseas_exposure"),
    }
    for key, value in fields.items():
        if value in (None, ""):
            continue
        path = Path(str(value))
        if not path.exists():
            errors.append(make_error("profile", "PROFILE_REFERENCE_MISSING", f"Referenced file not found: {value}", {"field": key, "path": str(value)}))
    quotes_path = analysis.get("quotes")
    if str(analysis.get("data_source", "")).lower() == "manual" and quotes_path in (None, ""):
        errors.append(make_error("profile", "MANUAL_QUOTES_REQUIRED", "data_source=manual requires analysis.quotes in effective config."))
    if str(analysis.get("data_source", "")).lower() == "mock":
        warnings.append("Profile resolves to mock data by default; output remains structure-focused.")
    return errors, warnings
