from __future__ import annotations

from typing import Any

from .overlap_rules import build_overlap_group_entries
from .role_analysis import build_role_analysis


def build_exposure_analysis(positions, exposure_config: dict[str, Any] | None = None) -> dict[str, Any]:
    exposure_config = exposure_config or {}
    overseas_positions = [position for position in positions if list(getattr(position, "exposure_tags", []) or [])]
    total_market_value = sum(position.market_value for position in positions) or 0.0
    overseas_market_value = sum(position.market_value for position in overseas_positions)
    overseas_position = round(overseas_market_value / total_market_value, 6) if total_market_value else 0.0
    tags = sorted({tag for position in overseas_positions for tag in list(getattr(position, "exposure_tags", []) or [])})

    overlap_entries = build_overlap_group_entries(overseas_positions, exposure_config.get("overlap_groups", {}) or {})
    role_analysis, role_warnings = build_role_analysis(overseas_positions, exposure_config.get("role_limits", {}) or {})
    overlap_warnings = [warning for entry in overlap_entries for warning in entry.get("warnings", [])]
    risk_notes = list((exposure_config.get("risk_notes", {}) or {}).get("qdii", []) or []) if overseas_positions else []

    warnings = _dedupe(overlap_warnings + role_warnings)
    short_portfolio_warnings = []
    for warning in warnings[:3]:
        if warning not in short_portfolio_warnings:
            short_portfolio_warnings.append(warning)
    if risk_notes:
        risk_summary = "QDII存在净值滞后、汇率波动和海外市场波动风险。"
        if risk_summary not in short_portfolio_warnings:
            short_portfolio_warnings.append(risk_summary)

    return {
        "overseas": {
            "market_value": round(overseas_market_value, 4),
            "current_position": overseas_position,
            "asset_count": len(overseas_positions),
            "tags": tags,
            "warnings": warnings,
            "risk_notes": risk_notes,
        },
        "overlap_groups": overlap_entries,
        "role_analysis": role_analysis,
        "warnings": warnings,
        "risk_notes": risk_notes,
        "portfolio_warnings": short_portfolio_warnings,
    }


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
