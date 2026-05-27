from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like


@dataclass
class PortfolioRuleConfig:
    max_single_position: float = 0.35
    max_fund_position: float = 0.80
    min_cash_position: float = 0.05


@dataclass
class PositionRuleConfig:
    rebalance_band: float = 0.05
    strong_underweight_band: float = 0.10
    overweight_band: float = 0.08


@dataclass
class ProfitRuleConfig:
    deep_loss_threshold: float = -0.15
    mild_loss_threshold: float = -0.05
    take_profit_threshold: float = 0.20


@dataclass
class RiskRuleConfig:
    forbid_add_when_deep_loss: bool = True
    reduce_when_extreme_overweight: bool = True


@dataclass
class RuleConfig:
    portfolio: PortfolioRuleConfig = field(default_factory=PortfolioRuleConfig)
    position: PositionRuleConfig = field(default_factory=PositionRuleConfig)
    profit: ProfitRuleConfig = field(default_factory=ProfitRuleConfig)
    risk: RiskRuleConfig = field(default_factory=RiskRuleConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_rule_config(path: str | Path | None = None) -> tuple[RuleConfig, str]:
    if path is None:
        return RuleConfig(), "default"

    file_path = Path(path)
    try:
        data = _load_yaml_like(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to load rules config from '{file_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Rules config '{file_path}' must be a mapping.")

    return _build_rule_config(data), str(file_path)


def _build_rule_config(data: dict[str, Any]) -> RuleConfig:
    try:
        portfolio = data.get("portfolio", {})
        position = data.get("position", {})
        profit = data.get("profit", {})
        risk = data.get("risk", {})
        if not all(isinstance(section, dict) for section in (portfolio, position, profit, risk)):
            raise ValueError("Each rules section must be a mapping.")
        return RuleConfig(
            portfolio=PortfolioRuleConfig(
                max_single_position=_as_float(portfolio.get("max_single_position", 0.35), "portfolio.max_single_position"),
                max_fund_position=_as_float(portfolio.get("max_fund_position", 0.80), "portfolio.max_fund_position"),
                min_cash_position=_as_float(portfolio.get("min_cash_position", 0.05), "portfolio.min_cash_position"),
            ),
            position=PositionRuleConfig(
                rebalance_band=_as_float(position.get("rebalance_band", 0.05), "position.rebalance_band"),
                strong_underweight_band=_as_float(position.get("strong_underweight_band", 0.10), "position.strong_underweight_band"),
                overweight_band=_as_float(position.get("overweight_band", 0.08), "position.overweight_band"),
            ),
            profit=ProfitRuleConfig(
                deep_loss_threshold=_as_float(profit.get("deep_loss_threshold", -0.15), "profit.deep_loss_threshold"),
                mild_loss_threshold=_as_float(profit.get("mild_loss_threshold", -0.05), "profit.mild_loss_threshold"),
                take_profit_threshold=_as_float(profit.get("take_profit_threshold", 0.20), "profit.take_profit_threshold"),
            ),
            risk=RiskRuleConfig(
                forbid_add_when_deep_loss=_as_bool(risk.get("forbid_add_when_deep_loss", True), "risk.forbid_add_when_deep_loss"),
                reduce_when_extreme_overweight=_as_bool(risk.get("reduce_when_extreme_overweight", True), "risk.reduce_when_extreme_overweight"),
            ),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid rules config fields: {exc}") from exc


def _as_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def _as_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise ValueError(f"{field_name} must be a boolean")
