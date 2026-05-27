from __future__ import annotations

from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like


def load_asset_group_config(path: str | None = None) -> dict[str, Any]:
    if path is None:
        return {"mappings": {}, "keyword_rules": {}}
    payload = _load_yaml_like(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Asset group config must be a mapping.")
    return {
        "mappings": payload.get("mappings", {}) or {},
        "keyword_rules": payload.get("keyword_rules", {}) or {},
    }


def classify_holding(holding, group_config: dict[str, Any] | None = None) -> tuple[str, list[str]]:
    metadata = holding.metadata or {}
    if metadata.get("group"):
        return str(metadata["group"]), list(metadata.get("tags", []))

    group_config = group_config or {"mappings": {}, "keyword_rules": {}}
    mapping = group_config.get("mappings", {}).get(holding.code)
    if isinstance(mapping, dict) and mapping.get("group"):
        return str(mapping["group"]), list(mapping.get("tags", []))

    name = holding.name or ""
    for group_name, keywords in (group_config.get("keyword_rules", {}) or {}).items():
        if any(keyword in name for keyword in keywords):
            return str(group_name), [keyword for keyword in keywords if keyword in name]

    fallback_rules = {
        "broad_index": ["沪深300", "中证500", "创业板", "红利"],
        "sector_theme": ["白酒", "消费", "新能源", "医药", "半导体"],
        "bond": ["债券", "纯债"],
        "money_market": ["货币", "现金"],
        "overseas": ["QDII", "纳斯达克", "标普", "海外"],
    }
    for group_name, keywords in fallback_rules.items():
        if any(keyword in name for keyword in keywords):
            return group_name, [keyword for keyword in keywords if keyword in name]

    return "other", list(metadata.get("tags", []))
