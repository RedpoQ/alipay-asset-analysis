from __future__ import annotations

from ..models import AssetPosition, SignalResult
from .config import RuleConfig
from .rule_result import RuleReason


def evaluate_position_rules(position: AssetPosition, config: RuleConfig) -> SignalResult:
    reasons: list[RuleReason] = []
    warnings: list[str] = []
    blocked_by: list[str] = []
    confidence = "low"
    severity = "normal"
    signal = "hold"

    if position.error:
        warnings.append("Quote data failed, so the signal is conservative.")
        reasons.append(
            RuleReason(
                rule="quote_error_conservative_hold",
                level="warning",
                message="Quote data is unavailable, so the engine keeps a conservative hold signal.",
            )
        )
        return SignalResult(
            code=position.code,
            name=position.name,
            type=position.type,
            signal="hold",
            confidence="low",
            severity="warning",
            reason="Hold because quote data failed and the signal engine is conservative.",
            reasons=[item.to_dict() for item in reasons],
            warnings=warnings,
            blocked_by=blocked_by,
        )

    gap = position.target_position - position.current_position
    if gap > config.position.rebalance_band:
        signal = "add"
        confidence = "medium"
        reasons.append(
            RuleReason(
                rule="target_position_gap",
                level="positive",
                message=(
                    f"Current position {position.current_position:.2%} is below target "
                    f"{position.target_position:.2%} by more than the rebalance band."
                ),
            )
        )
    elif -gap > config.position.overweight_band:
        signal = "reduce"
        confidence = "medium"
        reasons.append(
            RuleReason(
                rule="target_position_gap",
                level="negative",
                message=(
                    f"Current position {position.current_position:.2%} is above target "
                    f"{position.target_position:.2%} by more than the overweight band."
                ),
            )
        )
    else:
        reasons.append(
            RuleReason(
                rule="target_position_gap",
                level="neutral",
                message="Current position is within the configured rebalance band.",
            )
        )

    if gap > config.position.strong_underweight_band:
        confidence = "high"
        severity = "warning"
        reasons.append(
            RuleReason(
                rule="strong_underweight",
                level="positive",
                message="The position is materially under target, so urgency is elevated.",
            )
        )

    if (
        signal == "add"
        and position.profit_rate <= config.profit.deep_loss_threshold
        and config.risk.forbid_add_when_deep_loss
    ):
        blocked_by.append("deep_loss_protection")
        reasons.append(
            RuleReason(
                rule="deep_loss_protection",
                level="warning",
                message=(
                    f"Profit rate {position.profit_rate:.2%} is below the deep loss threshold, "
                    "so add is blocked."
                ),
            )
        )
        signal = "hold"
        confidence = "low"
        severity = "warning"

    if signal != "reduce" and position.profit_rate >= config.profit.take_profit_threshold and position.current_position > position.target_position:
        signal = "reduce"
        confidence = "high"
        severity = "warning"
        reasons.append(
            RuleReason(
                rule="take_profit_overweight",
                level="negative",
                message=(
                    f"Profit rate {position.profit_rate:.2%} exceeds the take-profit threshold "
                    "while the position is overweight."
                ),
            )
        )

    if position.current_position >= config.portfolio.max_single_position:
        warnings.append(
            f"Single-position weight {position.current_position:.2%} exceeds max_single_position {config.portfolio.max_single_position:.2%}."
        )
        reasons.append(
            RuleReason(
                rule="max_single_position",
                level="warning",
                message="This holding exceeds the configured maximum single-position concentration.",
            )
        )
        if config.risk.reduce_when_extreme_overweight and position.current_position > position.target_position:
            signal = "reduce"
            confidence = "high"
            severity = "critical"
            reasons.append(
                RuleReason(
                    rule="extreme_overweight_reduce",
                    level="warning",
                    message="Extreme concentration plus overweight status prefers a reduce signal.",
                )
            )

    reason = _summarize(signal, reasons, blocked_by)
    return SignalResult(
        code=position.code,
        name=position.name,
        type=position.type,
        signal=signal,
        confidence=confidence,
        severity=severity,
        reason=reason,
        reasons=[item.to_dict() for item in reasons],
        warnings=warnings,
        blocked_by=blocked_by,
    )


def _summarize(signal: str, reasons: list[RuleReason], blocked_by: list[str]) -> str:
    if signal == "add":
        return next((item.message for item in reasons if item.rule == "target_position_gap"), "Add based on rule evaluation.")
    if signal == "reduce":
        return next((item.message for item in reasons if item.rule in {"take_profit_overweight", "extreme_overweight_reduce", "target_position_gap"}), "Reduce based on rule evaluation.")
    if blocked_by:
        return "Hold because a protective rule blocked a more aggressive rebalance action."
    return "Hold because the position is close to target or risk rules favor caution."
