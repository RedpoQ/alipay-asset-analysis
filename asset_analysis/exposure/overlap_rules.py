from __future__ import annotations

from typing import Any


def build_overlap_group_entries(positions, overlap_groups: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for group_key, config in (overlap_groups or {}).items():
        matched = _match_positions(positions, group_key, config)
        if not matched:
            continue
        current_position = round(sum(item.current_position for item in matched), 6)
        entry = {
            "group": group_key,
            "display_name": str(config.get("display_name", group_key)),
            "asset_count": len(matched),
            "current_position": current_position,
            "assets": [
                {
                    "code": item.code,
                    "name": item.name,
                    "current_position": item.current_position,
                }
                for item in matched
            ],
            "warnings": [],
        }
        warning_threshold = config.get("warning_when_more_than")
        if warning_threshold is not None and len(matched) > int(warning_threshold):
            entry["warnings"].append(
                f"检测到 {len(matched)} 只{entry['display_name']}相关基金，底层资产高度重叠，不建议同时重仓或同时新增。"
            )
        max_position = config.get("max_position")
        if max_position is not None and current_position > float(max_position):
            entry["warnings"].append(
                str(
                    config.get(
                        "warning",
                        f"{entry['display_name']}相关资产占比较高，组合受对应市场波动影响较大。",
                    )
                )
            )
        entries.append(entry)
    return entries


def _match_positions(positions, group_key: str, config: dict[str, Any]) -> list[Any]:
    tags_any = list(config.get("tags_any", []) or [])
    matched = []
    for position in positions:
        overlap_key = getattr(position, "overlap_key", None)
        exposure_tags = list(getattr(position, "exposure_tags", []) or [])
        if overlap_key == group_key:
            matched.append(position)
        elif tags_any and any(tag in exposure_tags for tag in tags_any):
            matched.append(position)
    return matched
