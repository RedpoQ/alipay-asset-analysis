from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .constants import ASSET_ANALYSIS_SCHEMA_VERSION


def build_report_run(
    *,
    input_path: str,
    output_dir: str,
    data_source: str,
    rules_source: str,
    reporter_mode: str,
) -> dict[str, Any]:
    return {
        "input": input_path,
        "output_dir": output_dir,
        "data_source": data_source,
        "rules_source": rules_source,
        "reporter_mode": reporter_mode,
    }


def generated_at_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def base_report_contract() -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "generated_at": generated_at_now(),
        "run": {},
        "schema_errors": [],
    }
