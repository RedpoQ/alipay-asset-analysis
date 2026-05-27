from __future__ import annotations

from collections import defaultdict
from typing import Any

from .group_config import PortfolioTemplate


def build_group_analysis(positions, portfolio_template: PortfolioTemplate | None = None) -> dict[str, Any]:
    portfolio_template = portfolio_template or PortfolioTemplate()
    groups: dict[str, dict[str, Any]] = {}
    tag_values: dict[str, dict[str, Any]] = defaultdict(lambda: {"market_value": 0.0, "asset_count": 0})
    warnings: list[str] = []
    total_market_value = sum(position.market_value for position in positions) or 0.0

    for position in positions:
        group_name = getattr(position, "group", "other") or "other"
        tags = list(getattr(position, "tags", []) or [])
        entry = groups.setdefault(
            group_name,
            {
                "group": group_name,
                "market_value": 0.0,
                "current_position": 0.0,
                "target_position": 0.0,
                "max_position": 1.0,
                "profit": 0.0,
                "profit_rate": 0.0,
                "asset_count": 0,
                "tags": set(),
                "warnings": [],
            },
        )
        entry["market_value"] += position.market_value
        entry["profit"] += position.profit
        entry["asset_count"] += 1
        entry["tags"].update(tags)
        for tag in tags:
            tag_values[tag]["market_value"] += position.market_value
            tag_values[tag]["asset_count"] += 1

    group_items = []
    for group_name, entry in groups.items():
        template = portfolio_template.groups.get(group_name)
        if template:
            entry["target_position"] = template.target_position
            entry["max_position"] = template.max_position
        entry["current_position"] = round(entry["market_value"] / total_market_value, 6) if total_market_value else 0.0
        entry["profit_rate"] = round(entry["profit"] / entry["market_value"], 6) if entry["market_value"] else 0.0
        entry["tags"] = sorted(entry["tags"])
        if (
            template
            and portfolio_template.rules.warn_when_group_over_max
            and entry["current_position"] > template.max_position
        ):
            message = (
                f"Group {group_name} current position {entry['current_position']:.2%} exceeds max_position {template.max_position:.2%}."
            )
            entry["warnings"].append(message)
            warnings.append(message)
        if template and template.target_position - entry["current_position"] > portfolio_template.rules.warn_when_group_under_target_by:
            message = (
                f"Group {group_name} current position {entry['current_position']:.2%} is below target_position {template.target_position:.2%} by more than the configured threshold."
            )
            entry["warnings"].append(message)
            warnings.append(message)
        group_items.append(entry)

    tag_concentration = []
    for tag, entry in tag_values.items():
        current_position = round(entry["market_value"] / total_market_value, 6) if total_market_value else 0.0
        tag_warning_list: list[str] = []
        if current_position > portfolio_template.rules.warn_when_single_tag_concentration_over:
            message = (
                f"Tag {tag} concentration {current_position:.2%} exceeds configured threshold {portfolio_template.rules.warn_when_single_tag_concentration_over:.2%}."
            )
            tag_warning_list.append(message)
            warnings.append(message)
        tag_concentration.append(
            {
                "tag": tag,
                "current_position": current_position,
                "asset_count": entry["asset_count"],
                "warnings": tag_warning_list,
            }
        )

    return {
        "groups": sorted(group_items, key=lambda item: item["current_position"], reverse=True),
        "tag_concentration": sorted(tag_concentration, key=lambda item: item["current_position"], reverse=True),
        "warnings": warnings,
    }
