from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AssetHolding

SUPPORTED_GROUPS = ("funds", "etfs", "stocks")


def parse_holdings_file(path: str | Path) -> list[AssetHolding]:
    file_path = Path(path)
    raw_text = file_path.read_text(encoding="utf-8")
    return parse_holdings_text(raw_text, suffix=file_path.suffix)


def parse_holdings_text(text: str, suffix: str | None = None) -> list[AssetHolding]:
    suffix = (suffix or "").lower()
    data: dict[str, Any]
    if suffix == ".json" or _looks_like_json(text):
        data = json.loads(text)
    else:
        data = _load_yaml_like(text)
    return _normalize_holdings(data)


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


def _load_yaml_like(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("YAML holdings root must be a mapping.")
        return loaded
    except ModuleNotFoundError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    result: dict[str, list[dict[str, Any]]] = {}
    current_group: str | None = None
    current_item: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" ") and stripped.endswith(":"):
            current_group = stripped[:-1]
            result.setdefault(current_group, [])
            current_item = None
            continue

        if current_group is None:
            raise ValueError("Invalid YAML format: item found before group header.")

        if stripped.startswith("- "):
            item: dict[str, Any] = {}
            result[current_group].append(item)
            current_item = item
            remainder = stripped[2:].strip()
            if remainder:
                key, value = _split_key_value(remainder)
                item[key] = _coerce_scalar(value)
            continue

        if current_item is None:
            raise ValueError("Invalid YAML format: field found before list item.")

        key, value = _split_key_value(stripped)
        current_item[key] = _coerce_scalar(value)

    return result


def _split_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"Invalid key/value line: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def _coerce_scalar(value: str) -> Any:
    if not value:
        return ""
    if value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(ch in value for ch in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _normalize_holdings(data: dict[str, Any]) -> list[AssetHolding]:
    holdings: list[AssetHolding] = []
    for group_name in SUPPORTED_GROUPS:
        group = data.get(group_name, [])
        if group is None:
            continue
        if not isinstance(group, list):
            raise ValueError(f"Group '{group_name}' must be a list.")
        for item in group:
            if not isinstance(item, dict):
                raise ValueError(f"Each item in '{group_name}' must be a mapping.")
            normalized = _normalize_item(item, default_type=group_name[:-1] if group_name != "etfs" else "etf")
            holdings.append(normalized)
    return holdings


def _normalize_item(item: dict[str, Any], default_type: str) -> AssetHolding:
    asset_type = str(item.get("type", default_type)).lower()
    code = str(item["code"])
    name = str(item["name"])
    amount = float(item["amount"])
    target_position = float(item["target_position"])
    cost_price = float(item["cost_price"]) if item.get("cost_price") is not None else None
    cost_nav = float(item["cost_nav"]) if item.get("cost_nav") is not None else None
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else None
    return AssetHolding(
        code=code,
        name=name,
        type=asset_type,
        amount=amount,
        target_position=target_position,
        cost_price=cost_price,
        cost_nav=cost_nav,
        metadata=metadata,
    )
