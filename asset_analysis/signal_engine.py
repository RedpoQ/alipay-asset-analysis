from __future__ import annotations

from .models import AssetPosition, SignalResult
from .rules.config import RuleConfig
from .rules.portfolio_rules import evaluate_portfolio_warnings
from .rules.position_rules import evaluate_position_rules


class SignalEngine:
    def __init__(self, config: RuleConfig | None = None):
        self.config = config or RuleConfig()

    def evaluate(self, position: AssetPosition) -> SignalResult:
        return evaluate_position_rules(position, self.config)

    def evaluate_many(self, positions: list[AssetPosition]) -> tuple[list[SignalResult], list[str]]:
        signals = [self.evaluate(position) for position in positions]
        portfolio_warnings = evaluate_portfolio_warnings(positions, self.config)
        return signals, portfolio_warnings
