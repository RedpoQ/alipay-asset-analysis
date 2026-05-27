from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..schema.errors import make_error
from ..workflow.config import DailyWorkflowConfig, load_workflow_config
from .config_check import run_config_safety_checks
from .holdings_check import run_holdings_checks
from .quotes_check import run_quotes_checks
from .report import write_preflight_reports


def run_preflight(
    config_path: str = "private/config.local.yaml",
    *,
    json_output: str | None = None,
    markdown_output: str | None = None,
) -> dict[str, Any]:
    try:
        config = load_workflow_config(config_path)
    except FileNotFoundError:
        return _payload(config_path, [], [make_error("input", "CONFIG_NOT_FOUND", f"Workflow config not found: {config_path}")], [])
    except Exception as exc:
        return _payload(config_path, [], [make_error("input", "CONFIG_ERROR", str(exc))], [])

    checks, errors, warnings = _collect_checks(config)
    payload = _payload(config_path, checks, errors, warnings)
    if json_output:
        write_preflight_reports(payload, json_output, markdown_output)
    return payload


def _collect_checks(config: DailyWorkflowConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    holdings_checks, holdings = run_holdings_checks(config)
    checks.extend(holdings_checks)
    checks.extend(run_quotes_checks(config, holdings))
    checks.extend(run_config_safety_checks(config))
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    for item in checks:
        if item.get("ok"):
            continue
        if item.get("severity") == "critical":
            errors.append(make_error("preflight", f"PREFLIGHT_{str(item.get('name', 'UNKNOWN')).upper()}", str(item.get("message", "Preflight failed.")), dict(item.get("details", {}))))
        elif item.get("severity") == "warning":
            warnings.append(str(item.get("message", "")))
    return checks, errors, warnings


def _payload(config_path: str, checks: list[dict[str, Any]], errors: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    summary = _summarize_checks(checks)
    ok = summary["critical_failed"] == 0 and not errors
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": ok,
        "generated_at": datetime.now().astimezone().isoformat(),
        "config": config_path,
        "checks": checks,
        "summary": summary,
        "errors": errors,
        "warnings": warnings,
    }


def _summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(checks), "passed": 0, "failed": 0, "warnings": 0, "critical_failed": 0}
    for item in checks:
        if item.get("ok"):
            summary["passed"] += 1
        else:
            summary["failed"] += 1
            if item.get("severity") == "warning":
                summary["warnings"] += 1
            if item.get("severity") == "critical":
                summary["critical_failed"] += 1
    return summary

