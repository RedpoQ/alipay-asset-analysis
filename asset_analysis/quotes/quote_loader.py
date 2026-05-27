from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like


def load_manual_quotes(path: str | Path) -> dict[str, dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Manual quotes file not found: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix in {".yaml", ".yml", ".json"}:
        return _load_yaml_quotes(file_path)
    return _load_csv_quotes(file_path)


def _load_csv_quotes(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = str((row.get("code") or "").strip())
            if not code:
                continue
            records[code] = _normalize_quote_record(row)
    return records


def _load_yaml_quotes(path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_yaml_like(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual quote file root must be a mapping.")
    items = payload.get("quotes", []) or []
    if not isinstance(items, list):
        raise ValueError("Manual quote file must contain a 'quotes' list.")
    records: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        records[code] = _normalize_quote_record(item)
    return records


def _normalize_quote_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": str(row.get("code", "")).strip(),
        "name": str(row.get("name", "")).strip(),
        "type": str(row.get("type", "")).strip() or "fund",
        "current_nav": _to_float(row.get("current_nav")),
        "current_price": _to_float(row.get("current_price")),
        "as_of": _to_optional_str(row.get("as_of")),
        "source": _to_optional_str(row.get("source")) or "manual_nav",
        "currency": _to_optional_str(row.get("currency")),
        "notes": _to_optional_str(row.get("notes")),
    }


def _to_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def _to_optional_str(value: Any) -> str | None:
    if value in ("", None):
        return None
    return str(value).strip()
