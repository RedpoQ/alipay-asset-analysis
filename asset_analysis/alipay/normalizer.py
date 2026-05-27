from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .field_aliases import CANONICAL_FIELDS, resolve_canonical_field

MISSING_VALUE_MARKERS = {"", "--", "—", "暂无", "n/a", "na", "null", "none"}
_NUMBER_TRANSLATION = str.maketrans(
    {
        "\ufeff": "",
        "\u3000": " ",
        "（": "(",
        "）": ")",
        "，": ",",
        "－": "-",
        "％": "%",
        "￥": "¥",
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
        "．": ".",
    }
)


@dataclass
class RowIssue:
    row: int
    level: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"row": self.row, "level": self.level, "message": self.message}


@dataclass
class TabularNormalizationResult:
    records: list[dict[str, Any]]
    detected_columns: list[str] = field(default_factory=list)
    canonical_mapping: dict[str, str] = field(default_factory=dict)
    unknown_columns: list[str] = field(default_factory=list)


def normalize_tabular_records(records: list[dict[str, Any]]) -> TabularNormalizationResult:
    detected_columns: list[str] = []
    seen_headers: set[str] = set()
    canonical_mapping: dict[str, str] = {}
    unknown_columns: list[str] = []
    normalized_records: list[dict[str, Any]] = []

    for raw_record in records:
        for raw_key in raw_record.keys():
            if raw_key is None:
                continue
            key = str(raw_key)
            if key not in seen_headers:
                seen_headers.add(key)
                detected_columns.append(key)
            canonical_field = resolve_canonical_field(key)
            if canonical_field:
                canonical_mapping.setdefault(canonical_field, key)
            elif key not in unknown_columns:
                unknown_columns.append(key)

    known_fields = set(CANONICAL_FIELDS)
    for raw_record in records:
        normalized: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for raw_key, value in raw_record.items():
            if raw_key is None:
                continue
            canonical_field = resolve_canonical_field(str(raw_key))
            if canonical_field and canonical_field in known_fields:
                normalized[canonical_field] = value
            else:
                extras[str(raw_key).strip()] = value
        if extras:
            normalized["metadata"] = extras
        normalized_records.append(normalized)

    return TabularNormalizationResult(
        records=normalized_records,
        detected_columns=detected_columns,
        canonical_mapping=canonical_mapping,
        unknown_columns=unknown_columns,
    )


def normalize_text_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).translate(_NUMBER_TRANSLATION).strip()


def is_missing_value(value: Any) -> bool:
    text = normalize_text_value(value)
    return text.lower() in MISSING_VALUE_MARKERS


def parse_numeric_value(value: Any, *, field_name: str) -> float | None:
    text = normalize_text_value(value)
    if text.lower() in MISSING_VALUE_MARKERS:
        return None
    text = text.replace(" ", "")
    if text.startswith(("¥", "￥")):
        text = text[1:]
    for prefix in ("RMB", "rmb", "CNY", "cny"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    percent = text.endswith("%")
    if percent:
        text = text[:-1]
    text = text.replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for {field_name}: {value}") from exc
    if field_name in {"profit_rate", "target_position"} and percent:
        return number / 100
    return number
