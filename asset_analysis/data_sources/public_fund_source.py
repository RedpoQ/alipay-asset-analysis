from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import urlopen

from ..market_data import market_data_from_asset
from ..models import AssetHolding, FetchError
from .base import BaseDataSource


class PublicFundDataSource(BaseDataSource):
    name = "public_fund"

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    def supports(self, asset_type: str) -> bool:
        return asset_type == "fund"

    def fetch_quote(self, asset: AssetHolding):
        if not self.supports(asset.type):
            return market_data_from_asset(
                asset,
                source=self.name,
                error=FetchError(code="UNSUPPORTED_ASSET", message=f"Asset type '{asset.type}' is not supported by public_fund."),
                raw={"todo": "Add non-fund public adapters in a future module."},
            )

        # TODO: replace with a stable public adapter once a vetted endpoint is chosen.
        # Current implementation is intentionally best-effort and fully optional.
        url = f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key={asset.code}"
        try:
            with urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            records = payload.get("Datas") or []
            if not records:
                raise ValueError("No public fund records returned.")
            raw_record = records[0]
            nav_text = raw_record.get("PRICE_DATE") or raw_record.get("NAV") or raw_record.get("GSZ")
            # Public adapter may not always expose NAV in a normalized way; graceful failure is acceptable here.
            if raw_record.get("GSZ"):
                current_nav = float(raw_record["GSZ"])
            elif raw_record.get("DWJZ"):
                current_nav = float(raw_record["DWJZ"])
            else:
                raise ValueError("Current NAV field is unavailable in public response.")
            return market_data_from_asset(
                asset,
                current_price=current_nav,
                current_nav=current_nav,
                source=self.name,
                as_of=str(nav_text) if nav_text else None,
                raw=raw_record,
            )
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            return market_data_from_asset(
                asset,
                source=self.name,
                error=FetchError(code="PUBLIC_FETCH_FAILED", message=str(exc)),
                raw={"url": url},
            )
