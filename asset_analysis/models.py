from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AssetHolding:
    code: str
    name: str
    type: str
    amount: float
    target_position: float
    cost_price: float | None = None
    cost_nav: float | None = None
    metadata: dict[str, Any] | None = None

    @property
    def unit_cost(self) -> float:
        if self.type == "fund":
            return float(self.cost_nav or 0.0)
        return float(self.cost_price or 0.0)

    @property
    def total_cost(self) -> float:
        return self.unit_cost * self.amount


@dataclass
class FetchError:
    code: str
    message: str


@dataclass
class AssetQuote:
    code: str
    unit_price: float | None = None
    source: str = "mock"
    error: FetchError | None = None


@dataclass
class AssetPosition:
    code: str
    name: str
    type: str
    cost: float
    market_value: float
    profit: float
    profit_rate: float
    target_position: float
    current_position: float = 0.0
    error: dict[str, Any] | None = None
    quote: dict[str, Any] | None = None
    group: str = "other"
    tags: list[str] = field(default_factory=list)
    exposure_tags: list[str] = field(default_factory=list)
    exposure_role: str = "other"
    overlap_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SignalResult:
    code: str
    signal: str
    reason: str
    name: str = ""
    type: str = ""
    confidence: str = "low"
    severity: str = "normal"
    reasons: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisSummary:
    total_cost: float
    total_market_value: float
    total_profit: float
    total_profit_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssetAnalysisResult:
    summary: AnalysisSummary
    positions: list[AssetPosition]
    signals: list[SignalResult]
    schema_version: str = ""
    generated_at: str = ""
    run: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    portfolio_warnings: list[str] = field(default_factory=list)
    group_analysis: dict[str, Any] = field(default_factory=dict)
    exposure_analysis: dict[str, Any] = field(default_factory=dict)
    data_quality: dict[str, Any] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)
    report_md: str = ""
    data_source: str = "mock"
    reporter: dict[str, Any] = field(default_factory=dict)
    profile: dict[str, Any] = field(default_factory=dict)
    schema_errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "run": dict(self.run),
            "summary": self.summary.to_dict(),
            "positions": [position.to_dict() for position in self.positions],
            "signals": [signal.to_dict() for signal in self.signals],
            "recommendations": list(self.recommendations),
            "portfolio_warnings": list(self.portfolio_warnings),
            "group_analysis": dict(self.group_analysis),
            "exposure_analysis": dict(self.exposure_analysis),
            "data_quality": dict(self.data_quality),
            "rules": dict(self.rules),
            "report_md": self.report_md,
            "data_source": self.data_source,
            "reporter": dict(self.reporter),
            "profile": dict(self.profile),
            "schema_errors": list(self.schema_errors),
        }
