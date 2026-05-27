from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..ux.setup_check import run_setup_check
from ..workflow.daily_run import run_daily_workflow
from .result_reader import build_failure_message, read_chat_summary, read_latest_result


def run_hermes_daily_job(
    config_path: str = "private/config.local.yaml",
    latest_dir: str = "reports/private/latest",
) -> dict[str, Any]:
    try:
        workflow_result = run_daily_workflow(config_path=config_path)
    except Exception as exc:
        return _failure("unknown", f"Unexpected Hermes daily job error: {exc}")

    if not workflow_result.get("ok"):
        return _failure(*_classify_workflow_failure(workflow_result, config_path))

    try:
        latest = read_latest_result(latest_dir)
        chat_summary_path = latest.get("chat_summary_path")
        if not chat_summary_path:
            return _failure("read_summary", f"chat_summary.txt was not generated under {latest_dir}")
        chat_summary = read_chat_summary(chat_summary_path)
    except Exception as exc:
        return _failure("read_summary", str(exc))

    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": True,
        "job": "daily_fund_analysis",
        "chat_summary": chat_summary,
        "chat_summary_path": str(Path(latest_dir) / "chat_summary.txt"),
        "report_json": str(Path(latest_dir) / "report.json"),
        "preflight_report": str(Path(latest_dir) / "preflight_report.json"),
        "errors": [],
        "warnings": list(workflow_result.get("warnings", [])),
    }


def _classify_workflow_failure(workflow_result: dict[str, Any], config_path: str) -> tuple[str, str]:
    errors = workflow_result.get("errors", []) or []
    preflight = workflow_result.get("preflight")
    first_error = errors[0] if errors else {}
    message = str(first_error.get("message", "Hermes daily workflow failed.") or "Hermes daily workflow failed.")
    code = str(first_error.get("code", "") or "")
    if code in {"CONFIG_NOT_FOUND", "CONFIG_ERROR"}:
        setup_result = run_setup_check(config_path=config_path)
        hints = setup_result.get("repair_hints", []) or []
        if hints:
            return "setup", f"{message} Suggested fix: {hints[0].get('suggestion')}"
        return "setup", message
    if preflight and not preflight.get("ok"):
        return "preflight", _build_preflight_failure_message(preflight, message)
    if "chat_summary" in message.lower():
        return "read_summary", message
    return "workflow", message


def _build_preflight_failure_message(preflight: dict[str, Any], fallback_message: str) -> str:
    checks = preflight.get("checks", []) or []
    failed = [item for item in checks if not item.get("ok")]
    if not failed:
        return fallback_message
    first = failed[0]
    return f"{first.get('name')}: {first.get('message')}"


def _failure(stage: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": False,
        "job": "daily_fund_analysis",
        "chat_summary": "",
        "chat_summary_path": None,
        "report_json": None,
        "preflight_report": None,
        "errors": [{"stage": stage, "message": message}],
        "warnings": [],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deterministic Hermes daily fund cronjob wrapper.")
    parser.add_argument("--config", default="private/config.local.yaml", help="Path to local workflow config.")
    parser.add_argument("--latest-dir", default="reports/private/latest", help="Latest result directory to read.")
    parser.add_argument("--json-only", action=argparse.BooleanOptionalAction, default=False, help="Print full JSON result.")
    parser.add_argument("--summary-only", action=argparse.BooleanOptionalAction, default=False, help="Print only the chat summary text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_hermes_daily_job(config_path=args.config, latest_dir=args.latest_dir)
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.summary_only:
        print(result.get("chat_summary", "").strip())
    elif result.get("ok"):
        print(result.get("chat_summary", "").strip())
        print(f"Report path: {result.get('report_json')}")
    else:
        print(build_failure_message(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
