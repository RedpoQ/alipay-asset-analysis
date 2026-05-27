from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like


@dataclass
class GroupRuleConfig:
    warn_when_group_over_max: bool = True
    warn_when_group_under_target_by: float = 0.10
    warn_when_single_tag_concentration_over: float = 0.30


@dataclass
class GroupTargetConfig:
    target_position: float = 0.0
    max_position: float = 1.0


@dataclass
class PortfolioTemplate:
    groups: dict[str, GroupTargetConfig] = field(default_factory=dict)
    rules: GroupRuleConfig = field(default_factory=GroupRuleConfig)


def load_portfolio_template(path: str | None = None) -> PortfolioTemplate:
    if path is None:
        return PortfolioTemplate()
    payload = _load_yaml_like(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Portfolio template must be a mapping.")
    groups_raw = payload.get("groups", {}) or {}
    rules_raw = payload.get("rules", {}) or {}
    groups = {
        key: GroupTargetConfig(
            target_position=float(value.get("target_position", 0.0)),
            max_position=float(value.get("max_position", 1.0)),
        )
        for key, value in groups_raw.items()
        if isinstance(value, dict)
    }
    rules = GroupRuleConfig(
        warn_when_group_over_max=bool(rules_raw.get("warn_when_group_over_max", True)),
        warn_when_group_under_target_by=float(rules_raw.get("warn_when_group_under_target_by", 0.10)),
        warn_when_single_tag_concentration_over=float(rules_raw.get("warn_when_single_tag_concentration_over", 0.30)),
    )
    return PortfolioTemplate(groups=groups, rules=rules)
