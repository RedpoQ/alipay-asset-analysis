from __future__ import annotations

from .data_sources.mock_source import MockDataSource
from .data_sources.registry import get_data_source
from .market_data import market_data_from_asset, MarketData
from .models import AssetHolding, FetchError


class AssetDataFetcher:
    """Market data fetcher with explicit source selection and safe fallback behavior."""

    def __init__(self, data_source: str = "mock", mock_mode: bool | None = None, quotes_path: str | None = None):
        if mock_mode is not None:
            data_source = "mock" if mock_mode else "auto"
        self.data_source_name = data_source
        self.quotes_path = quotes_path
        self.mock_source = MockDataSource()
        self.primary_source = get_data_source(data_source, quotes_path=quotes_path)

    def fetch_asset(self, holding: AssetHolding) -> MarketData:
        if self.data_source_name == "mock":
            return self.mock_source.fetch_quote(holding)

        if self.data_source_name == "manual":
            return self._safe_fetch(self.primary_source, holding)

        if self.data_source_name == "public_fund":
            return self._safe_fetch(self.primary_source, holding)

        if self.data_source_name == "auto":
            if self.primary_source.supports(holding.type):
                primary_quote = self._safe_fetch(self.primary_source, holding)
                if primary_quote.error is None and primary_quote.effective_price() is not None:
                    return primary_quote
                fallback_quote = self.mock_source.fetch_quote(holding)
                fallback_quote.source = "fallback"
                fallback_quote.raw = {
                    **fallback_quote.raw,
                    "fallback_from": self.primary_source.name,
                    "fallback_error": primary_quote.error.message if primary_quote.error else None,
                }
                if primary_quote.error and fallback_quote.error is None:
                    fallback_quote.error = FetchError(
                        code="FALLBACK_USED",
                        message=f"Primary source '{self.primary_source.name}' failed; mock fallback was used.",
                    )
                return fallback_quote
            return self.mock_source.fetch_quote(holding)

        return self._safe_fetch(self.primary_source, holding)

    def _safe_fetch(self, source, holding: AssetHolding) -> MarketData:
        try:
            return source.fetch_quote(holding)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return market_data_from_asset(
                holding,
                source=getattr(source, "name", "unknown"),
                error=FetchError(code="FETCH_ERROR", message=str(exc)),
                raw={"wrapper": "AssetDataFetcher"},
            )
