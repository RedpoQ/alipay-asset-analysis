from __future__ import annotations

from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like


def load_overseas_exposure_config(path: str | None = None) -> dict[str, Any]:
    if not path:
        return {
            "asset_patterns": {},
            "overlap_groups": {},
            "role_limits": {},
            "risk_notes": {},
        }
    payload = _load_yaml_like(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Overseas exposure config must be a mapping.")
    return {
        "asset_patterns": payload.get("asset_patterns", {}) or {},
        "overlap_groups": payload.get("overlap_groups", {}) or {},
        "role_limits": payload.get("role_limits", {}) or {},
        "risk_notes": payload.get("risk_notes", {}) or {},
    }


def classify_overseas_asset(
    *,
    holding,
    group: str,
    tags: list[str] | None,
    exposure_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exposure_config = exposure_config or {}
    metadata = holding.metadata or {}
    explicit_tags = list(metadata.get("exposure_tags", []) or [])
    explicit_role = str(metadata.get("exposure_role", "") or "").strip()
    explicit_overlap_key = str(metadata.get("overlap_key", "") or "").strip()
    if explicit_tags or explicit_role or explicit_overlap_key:
        return {
            "tags": _dedupe(explicit_tags),
            "role": explicit_role or "other",
            "overlap_key": explicit_overlap_key or None,
        }

    name = str(holding.name or "")
    asset_patterns = exposure_config.get("asset_patterns", {}) or {}
    for key, pattern in asset_patterns.items():
        if any(keyword and keyword in name for keyword in pattern.get("keywords", []) or []):
            tags = _dedupe(list(pattern.get("tags", []) or []))
            if "QDII" in tags and "海外资产" not in tags:
                tags.append("海外资产")
            return {
                "tags": tags,
                "role": str(pattern.get("role", "other")),
                "overlap_key": str(key),
            }

    current_tags = list(tags or [])
    if group == "overseas" or any(tag in {"QDII", "海外资产", "美股", "标普500", "纳斯达克100"} for tag in current_tags):
        fallback_tags = _dedupe(current_tags + ["QDII", "海外资产"])
        return {"tags": fallback_tags, "role": "other", "overlap_key": "overseas"}

    fallback_keywords = ["QDII", "海外", "全球", "纳斯达克", "标普", "美元"]
    if any(keyword in name for keyword in fallback_keywords):
        return {"tags": ["QDII", "海外资产"], "role": "other", "overlap_key": "overseas"}

    return {"tags": [], "role": "other", "overlap_key": None}


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
