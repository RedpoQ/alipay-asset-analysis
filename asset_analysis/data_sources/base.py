from __future__ import annotations

from abc import ABC, abstractmethod

from ..market_data import MarketData
from ..models import AssetHolding


class BaseDataSource(ABC):
    name = "base"

    @abstractmethod
    def supports(self, asset_type: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch_quote(self, asset: AssetHolding) -> MarketData:
        raise NotImplementedError
