from __future__ import annotations

from typing import Any

from .copy_rules import localize_data_status_copy, localize_reason_text, localize_warning_text
from .group_copy import localize_group_name
from .signal_copy import localize_signal_label


def build_asset_name_map(payload: dict[str, Any]) -> dict[str, str]:
    name_map: dict[str, str] = {}
    for collection_name in ("positions", "signals"):
        for item in payload.get(collection_name, []) or []:
            code = str(item.get("code", ""))
            name = str(item.get("name", ""))
            if code and name and code not in name_map:
                name_map[code] = name
    return name_map


def localize_signal_entry(signal: dict[str, Any]) -> dict[str, Any]:
    signal_name = str(signal.get("signal", ""))
    signal_label = localize_signal_label(signal_name)
    reason = str(signal.get("reason", "")).strip()
    localized = dict(signal)
    localized["signal_label"] = signal_label
    localized["reason_cn"] = localize_reason_text(reason, signal_label=signal_label) if reason else ""
    if signal.get("type"):
        localized["type_label"] = _localize_type(str(signal.get("type", "")))
    return localized


def localize_warning_entry(warning: str, asset_name_map: dict[str, str] | None = None) -> dict[str, str]:
    return {
        "raw": str(warning or ""),
        "text": localize_warning_text(str(warning or ""), asset_name_map=asset_name_map),
    }


def localize_data_status(data_source: str, positions: list[dict[str, Any]], schema_errors: list[Any] | None = None) -> dict[str, Any]:
    limitations = localize_data_status_copy(data_source, positions, schema_errors=schema_errors)
    analysis_scope = "structure_only" if data_source == "mock" or any((position.get("quote") or {}).get("error") for position in positions) else "quote_based"
    has_realtime_quote = analysis_scope == "quote_based" and any(
        (position.get("quote") or {}).get("source") not in {"", "mock", "fallback"}
        for position in positions
    )
    return {
        "data_source": data_source,
        "analysis_scope": analysis_scope,
        "has_realtime_quote": has_realtime_quote,
        "limitations": limitations,
    }


def _localize_type(asset_type: str) -> str:
    return {
        "fund": "基金",
        "etf": "ETF",
        "stock": "股票",
    }.get(asset_type, asset_type)


__all__ = [
    "build_asset_name_map",
    "localize_data_status",
    "localize_data_status_copy",
    "localize_group_name",
    "localize_signal_entry",
    "localize_signal_label",
    "localize_warning_entry",
]
