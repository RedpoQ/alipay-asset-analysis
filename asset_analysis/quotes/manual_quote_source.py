from __future__ import annotations

from ..market_data import market_data_from_asset
from ..models import AssetHolding, FetchError
from .quote_loader import load_manual_quotes


class ManualQuoteDataSource:
    name = "manual"

    def __init__(self, quotes_path: str):
        self.quotes_path = quotes_path
        self.quotes = load_manual_quotes(quotes_path)

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"fund", "etf", "stock"}

    def fetch_quote(self, asset: AssetHolding):
        quote = self.quotes.get(asset.code)
        if not quote:
            return market_data_from_asset(
                asset,
                source="manual_missing",
                error=FetchError(code="MANUAL_QUOTE_MISSING", message=f"Manual quote missing for {asset.code}."),
                raw={"quotes_path": self.quotes_path},
            )
        return market_data_from_asset(
            asset,
            current_price=quote.get("current_price"),
            current_nav=quote.get("current_nav"),
            source=str(quote.get("source") or "manual_nav"),
            as_of=quote.get("as_of"),
            raw={"quotes_path": self.quotes_path},
            currency=quote.get("currency"),
            notes=quote.get("notes"),
        )
