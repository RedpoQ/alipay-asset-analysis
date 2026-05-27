from __future__ import annotations

from ..market_data import market_data_from_asset
from ..models import AssetHolding, FetchError
from .base import BaseDataSource


class MockDataSource(BaseDataSource):
    name = "mock"

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"fund", "etf", "stock"}

    def fetch_quote(self, asset: AssetHolding):
        try:
            if "FAIL" in asset.code.upper():
                raise RuntimeError("Simulated data fetch failure for testing.")

            base = asset.unit_cost or 1.0
            multipliers = {
                "fund": 1.02,
                "etf": 0.98,
                "stock": 1.05,
            }
            code_factor = (sum(ord(ch) for ch in asset.code) % 5) * 0.005
            effective = round(base * (multipliers.get(asset.type, 1.0) + code_factor), 4)
            previous_nav = round(effective * 0.995, 4) if asset.type == "fund" else None
            daily_change_rate = (
                round((effective - previous_nav) / previous_nav, 6)
                if previous_nav not in (None, 0)
                else None
            )
            return market_data_from_asset(
                asset,
                current_price=effective if asset.type != "fund" else effective,
                current_nav=effective if asset.type == "fund" else None,
                previous_nav=previous_nav,
                daily_change_rate=daily_change_rate,
                source=self.name,
                raw={"mode": "deterministic_offline"},
            )
        except Exception as exc:
            return market_data_from_asset(
                asset,
                source=self.name,
                error=FetchError(code="FETCH_ERROR", message=str(exc)),
                raw={"mode": "deterministic_offline"},
            )
