from __future__ import annotations

from ..models import AssetPosition
from .config import RuleConfig


def evaluate_portfolio_warnings(positions: list[AssetPosition], config: RuleConfig) -> list[str]:
    warnings: list[str] = []
    for position in positions:
        if position.current_position >= config.portfolio.max_single_position:
            warnings.append(
                f"{position.code} exceeds max_single_position with current weight {position.current_position:.2%}."
            )

    total_fund_position = sum(
        position.current_position for position in positions if position.type == "fund" and position.market_value >= 0
    )
    if total_fund_position > config.portfolio.max_fund_position:
        warnings.append(
            f"Total fund position {total_fund_position:.2%} exceeds max_fund_position {config.portfolio.max_fund_position:.2%}."
        )

    return warnings
