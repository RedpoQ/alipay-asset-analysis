from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .checks import (
    check_default_safety_config,
    check_docs_release_package,
    check_gitignore_privacy,
    check_hermes_prompt_templates,
    check_required_files,
    check_schema_constants,
    run_alipay_preview_smoke_check,
    run_chat_summary_smoke_check,
    run_daily_workflow_smoke_check,
    run_demo_bundle_smoke_check,
    run_hermes_cronjob_runner_smoke_check,
    run_hermes_smoke_check,
    run_history_smoke_check,
    run_manual_quote_smoke_check,
    run_onboarding_init_smoke_check,
    run_notify_dry_run_smoke_check,
    run_notification_orchestrator_dry_run_smoke_check,
    run_openclaw_smoke_check,
    run_pipeline_smoke_check,
    run_profile_files_check,
    run_profile_loader_check,
    run_profile_resolver_check,
    run_profile_workflow_smoke_check,
    run_preflight_smoke_check,
    run_python_tests_check,
    run_setup_repair_hints_smoke_check,
    run_setup_check_smoke_check,
)
from .report import write_release_gate_reports


def run_release_gate(output_dir: str = "reports/release_gate", skip_tests: bool = False, no_smoke: bool = False, json_only: bool = False) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = [
        check_required_files(),
        check_docs_release_package(),
        check_gitignore_privacy(),
        check_default_safety_config(),
        check_schema_constants(),
        check_hermes_prompt_templates(),
        run_profile_files_check(),
        run_profile_loader_check(),
        run_profile_resolver_check(),
        run_python_tests_check(skip=skip_tests),
    ]

    if not no_smoke:
        checks.extend(
            [
                run_pipeline_smoke_check(output),
                run_manual_quote_smoke_check(output),
                run_preflight_smoke_check(output),
                run_profile_workflow_smoke_check(output),
                run_setup_check_smoke_check(output),
                run_onboarding_init_smoke_check(output),
                run_alipay_preview_smoke_check(output),
                run_setup_repair_hints_smoke_check(output),
                run_hermes_cronjob_runner_smoke_check(output),
                run_demo_bundle_smoke_check(output),
                run_daily_workflow_smoke_check(output),
                run_notify_dry_run_smoke_check(output),
                run_notification_orchestrator_dry_run_smoke_check(output),
                run_chat_summary_smoke_check(output),
                run_openclaw_smoke_check(output),
                run_hermes_smoke_check(output),
                run_history_smoke_check(),
            ]
        )

    summary = _summarize_checks(checks)
    payload = {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": summary["critical_failed"] == 0,
        "generated_at": datetime.now().astimezone().isoformat(),
        "checks": checks,
        "summary": summary,
        "errors": [],
        "warnings": [item["message"] for item in checks if not item.get("ok") and item.get("severity") == "warning"],
    }
    json_path, md_path = write_release_gate_reports(payload, output, json_only=json_only)
    payload["report_json"] = str(json_path)
    payload["report_md"] = str(md_path) if md_path else None
    return payload


def _summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(checks), "passed": 0, "failed": 0, "warnings": 0, "critical_failed": 0}
    for item in checks:
        if item.get("ok"):
            summary["passed"] += 1
        else:
            summary["failed"] += 1
            if item.get("severity") == "critical":
                summary["critical_failed"] += 1
            if item.get("severity") == "warning":
                summary["warnings"] += 1
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local asset_analysis release gate.")
    parser.add_argument("--output", default="reports/release_gate", help="Directory for release gate outputs.")
    parser.add_argument("--skip-tests", action=argparse.BooleanOptionalAction, default=False, help="Skip running the unittest suite.")
    parser.add_argument("--no-smoke", action=argparse.BooleanOptionalAction, default=False, help="Skip smoke test execution.")
    parser.add_argument("--json-only", action=argparse.BooleanOptionalAction, default=False, help="Write only JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = run_release_gate(output_dir=args.output, skip_tests=args.skip_tests, no_smoke=args.no_smoke, json_only=args.json_only)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
