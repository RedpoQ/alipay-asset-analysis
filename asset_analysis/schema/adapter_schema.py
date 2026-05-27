from __future__ import annotations

from typing import Any

from .constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .report_schema import generated_at_now


def base_adapter_contract() -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "generated_at": generated_at_now(),
        "schema_errors": [],
    }


def merge_adapter_contract(payload: dict[str, Any]) -> dict[str, Any]:
    base = base_adapter_contract()
    base.update(payload)
    return base
