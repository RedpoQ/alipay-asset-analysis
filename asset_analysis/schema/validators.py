from __future__ import annotations

from typing import Any

from .constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .errors import make_error


def validate_report_schema(report: dict) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return [make_error("schema", "INVALID_TYPE", "Report payload must be a dict.", {})]

    errors: list[dict[str, Any]] = []
    required = [
        "schema_version",
        "generated_at",
        "run",
        "summary",
        "positions",
        "signals",
        "portfolio_warnings",
        "group_analysis",
        "rules",
        "reporter",
        "recommendations",
        "report_md",
    ]
    for field in required:
        if field not in report:
            errors.append(make_error("schema", "MISSING_FIELD", f"Missing report field: {field}", {"field": field}))

    if report.get("schema_version") != ASSET_ANALYSIS_SCHEMA_VERSION:
        errors.append(make_error("schema", "INVALID_SCHEMA_VERSION", "Invalid schema_version.", {"expected": ASSET_ANALYSIS_SCHEMA_VERSION}))

    if not isinstance(report.get("run"), dict):
        errors.append(make_error("schema", "INVALID_FIELD", "run must be a dict.", {"field": "run"}))
    if not isinstance(report.get("positions"), list):
        errors.append(make_error("schema", "INVALID_FIELD", "positions must be a list.", {"field": "positions"}))
    if not isinstance(report.get("signals"), list):
        errors.append(make_error("schema", "INVALID_FIELD", "signals must be a list.", {"field": "signals"}))
    if not isinstance(report.get("portfolio_warnings"), list):
        errors.append(make_error("schema", "INVALID_FIELD", "portfolio_warnings must be a list.", {"field": "portfolio_warnings"}))
    if "group_analysis" in report and not isinstance(report.get("group_analysis"), dict):
        errors.append(make_error("schema", "INVALID_FIELD", "group_analysis must be a dict.", {"field": "group_analysis"}))
    if "exposure_analysis" in report and not isinstance(report.get("exposure_analysis"), dict):
        errors.append(make_error("schema", "INVALID_FIELD", "exposure_analysis must be a dict.", {"field": "exposure_analysis"}))
    if "data_quality" in report and not isinstance(report.get("data_quality"), dict):
        errors.append(make_error("schema", "INVALID_FIELD", "data_quality must be a dict.", {"field": "data_quality"}))
    if "profile" in report and not isinstance(report.get("profile"), dict):
        errors.append(make_error("schema", "INVALID_FIELD", "profile must be a dict.", {"field": "profile"}))

    for signal in report.get("signals", []):
        if not isinstance(signal, dict):
            errors.append(make_error("schema", "INVALID_SIGNAL", "Signal item must be a dict.", {}))
            continue
        for key in ("code", "name", "type", "signal", "confidence", "severity", "reason", "reasons", "warnings", "blocked_by"):
            if key not in signal:
                errors.append(make_error("schema", "MISSING_SIGNAL_FIELD", f"Missing signal field: {key}", {"field": key}))

    for position in report.get("positions", []):
        if not isinstance(position, dict):
            errors.append(make_error("schema", "INVALID_POSITION", "Position item must be a dict.", {}))
            continue
        for key in ("code", "name", "type", "cost", "market_value", "profit", "profit_rate", "target_position", "current_position", "quote", "group", "tags"):
            if key not in position:
                errors.append(make_error("schema", "MISSING_POSITION_FIELD", f"Missing position field: {key}", {"field": key}))
        if "quote" in position and not isinstance(position["quote"], dict):
            errors.append(make_error("schema", "INVALID_QUOTE", "quote must be a dict.", {"field": "quote"}))
    return errors


def validate_adapter_result_schema(result: dict) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return [make_error("schema", "INVALID_TYPE", "Adapter result must be a dict.", {})]

    errors: list[dict[str, Any]] = []
    required = [
        "schema_version",
        "generated_at",
        "ok",
        "report_json",
        "report_md",
        "warnings",
        "errors",
        "schema_errors",
    ]
    for field in required:
        if field not in result:
            errors.append(make_error("schema", "MISSING_FIELD", f"Missing adapter field: {field}", {"field": field}))

    if result.get("schema_version") != ASSET_ANALYSIS_SCHEMA_VERSION:
        errors.append(make_error("schema", "INVALID_SCHEMA_VERSION", "Invalid schema_version.", {"expected": ASSET_ANALYSIS_SCHEMA_VERSION}))
    if not isinstance(result.get("errors"), list):
        errors.append(make_error("schema", "INVALID_FIELD", "errors must be a list.", {"field": "errors"}))
    if not isinstance(result.get("warnings"), list):
        errors.append(make_error("schema", "INVALID_FIELD", "warnings must be a list.", {"field": "warnings"}))
    return errors
