from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .models import AssetHolding, FetchError


def default_as_of() -> str:
    return datetime.now(timezone.utc).date().isoformat()


@dataclass
class MarketData:
    code: str
    name: str
    type: str
    current_price: float | None = None
    current_nav: float | None = None
    previous_nav: float | None = None
    daily_change_rate: float | None = None
    source: str = "mock"
    as_of: str | None = field(default_factory=default_as_of)
    currency: str | None = None
    notes: str | None = None
    freshness: dict[str, Any] | None = None
    error: FetchError | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def effective_price(self) -> float | None:
        if self.type == "fund":
            return self.current_nav if self.current_nav is not None else self.current_price
        return self.current_price if self.current_price is not None else self.current_nav

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.error is not None:
            payload["error"] = asdict(self.error)
        return payload


def market_data_from_asset(
    asset: AssetHolding,
    *,
    current_price: float | None = None,
    current_nav: float | None = None,
    previous_nav: float | None = None,
    daily_change_rate: float | None = None,
    source: str = "mock",
    as_of: str | None = None,
    currency: str | None = None,
    notes: str | None = None,
    freshness: dict[str, Any] | None = None,
    error: FetchError | None = None,
    raw: dict[str, Any] | None = None,
) -> MarketData:
    return MarketData(
        code=asset.code,
        name=asset.name,
        type=asset.type,
        current_price=current_price,
        current_nav=current_nav,
        previous_nav=previous_nav,
        daily_change_rate=daily_change_rate,
        source=source,
        as_of=as_of if as_of is not None else (None if error is not None else default_as_of()),
        currency=currency,
        notes=notes,
        freshness=freshness,
        error=error,
        raw=raw or {},
    )
