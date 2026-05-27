from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_chat_summary(path: str | Path) -> str:
    summary_path = Path(path)
    if not summary_path.exists():
        raise FileNotFoundError(f"chat_summary.txt not found: {summary_path}")
    text = summary_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"chat_summary.txt is empty: {summary_path}")
    return text


def read_latest_result(latest_dir: str | Path) -> dict[str, Any]:
    base = Path(latest_dir)
    chat_summary_path = base / "chat_summary.txt"
    report_json_path = base / "report.json"
    preflight_report_path = base / "preflight_report.json"
    run_json_path = base / "run.json"
    return {
        "latest_dir": str(base),
        "chat_summary_path": str(chat_summary_path) if chat_summary_path.exists() else None,
        "report_json": str(report_json_path) if report_json_path.exists() else None,
        "preflight_report": str(preflight_report_path) if preflight_report_path.exists() else None,
        "run_json": str(run_json_path) if run_json_path.exists() else None,
        "report_payload": _read_optional_json(report_json_path),
        "preflight_payload": _read_optional_json(preflight_report_path),
        "run_payload": _read_optional_json(run_json_path),
    }


def build_failure_message(result: dict[str, Any]) -> str:
    error = ((result.get("errors") or [{}])[0]) if isinstance(result.get("errors"), list) else {}
    stage = str(error.get("stage", "unknown") or "unknown")
    message = str(error.get("message", "Hermes daily job failed.") or "Hermes daily job failed.")
    detail = _infer_failure_detail(stage, message)
    fix_command = _suggest_fix_command(stage, message)
    lines = [
        "Hermes daily fund analysis did not complete.",
        f"Failure stage: {detail}",
        f"Reason: {message}",
        f"Fix command: {fix_command}",
        "No fund analysis was generated manually.",
    ]
    return "\n".join(lines)


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _infer_failure_detail(stage: str, message: str) -> str:
    haystack = f"{stage} {message}".lower()
    if "chat_summary" in haystack or "read_summary" in haystack:
        return "chat_summary"
    if "manual quote" in haystack or "manual_quotes" in haystack or "quotes" in haystack:
        return "manual quotes"
    if "convert" in haystack or "alipay" in haystack:
        return "conversion"
    if "preflight" in haystack:
        return "preflight"
    if "config" in haystack or "setup" in haystack:
        return "setup_check"
    if "pipeline" in haystack or "report" in haystack:
        return "pipeline"
    return stage


def _suggest_fix_command(stage: str, message: str) -> str:
    haystack = f"{stage} {message}".lower()
    if "config not found" in haystack or "missing config" in haystack or stage == "setup":
        return "python -m asset_analysis.onboarding.init_project"
    if "manual quote" in haystack or "manual_quotes" in haystack or "quotes" in haystack:
        return r"copy private\manual_quotes.local.example.csv private\manual_quotes.local.csv"
    if "alipay" in haystack or "convert" in haystack or "header" in haystack:
        return "python -m asset_analysis.alipay.preview --input private/alipay_holdings.local.csv"
    return "python -m asset_analysis.ux.setup_check --config private/config.local.yaml"
