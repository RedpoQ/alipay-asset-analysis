from __future__ import annotations

from typing import Any


ROLE_DISPLAY_NAMES = {
    "core": "核心仓",
    "satellite": "卫星仓",
    "diversifier": "分散补充仓",
    "other": "其他仓位",
}


def build_role_analysis(positions, role_limits: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    role_limits = role_limits or {}
    role_map: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for position in positions:
        role = str(getattr(position, "exposure_role", "other") or "other")
        exposure_tags = list(getattr(position, "exposure_tags", []) or [])
        if not exposure_tags:
            continue
        entry = role_map.setdefault(
            role,
            {
                "role": role,
                "display_name": ROLE_DISPLAY_NAMES.get(role, role),
                "current_position": 0.0,
                "assets": [],
                "warnings": [],
            },
        )
        entry["current_position"] += float(position.current_position)
        entry["assets"].append(
            {
                "code": position.code,
                "name": position.name,
                "current_position": position.current_position,
            }
        )

    ordered_roles = []
    for role, entry in role_map.items():
        entry["current_position"] = round(entry["current_position"], 6)
        limit = role_limits.get(role, {}) or {}
        max_position = limit.get("max_position")
        min_position = limit.get("min_position")
        if max_position is not None and entry["current_position"] > float(max_position):
            message = f"{entry['display_name']}当前占比 {entry['current_position']:.2%}，超过建议上限 {float(max_position):.2%}。"
            entry["warnings"].append(message)
            warnings.append(message)
        if role == "core" and min_position is not None and entry["current_position"] < float(min_position):
            message = f"{entry['display_name']}当前占比 {entry['current_position']:.2%}，低于建议下限 {float(min_position):.2%}。"
            entry["warnings"].append(message)
            warnings.append(message)
        ordered_roles.append(entry)

    satellite_position = next((item["current_position"] for item in ordered_roles if item["role"] == "satellite"), 0.0)
    core_position = next((item["current_position"] for item in ordered_roles if item["role"] == "core"), 0.0)
    if satellite_position > 0 and core_position <= 0:
        warnings.append("当前存在卫星仓，但核心仓不足，组合波动可能偏高。")

    return sorted(ordered_roles, key=lambda item: item["current_position"], reverse=True), warnings
