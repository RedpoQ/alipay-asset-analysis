from __future__ import annotations

from .base import BaseDataSource
from .mock_source import MockDataSource
from .public_fund_source import PublicFundDataSource
from ..quotes.manual_quote_source import ManualQuoteDataSource


def get_data_source(name: str, **kwargs) -> BaseDataSource:
    normalized = name.lower()
    if normalized == "mock":
        return MockDataSource()
    if normalized == "manual":
        quotes_path = kwargs.get("quotes_path")
        if not quotes_path:
            raise ValueError("Manual data source requires a quotes file path.")
        return ManualQuoteDataSource(quotes_path=quotes_path)
    if normalized == "public_fund":
        return PublicFundDataSource()
    if normalized == "auto":
        # Auto orchestration is handled by AssetDataFetcher; the concrete public adapter is still useful here.
        return PublicFundDataSource()
    raise ValueError(f"Unsupported data source: {name}")
