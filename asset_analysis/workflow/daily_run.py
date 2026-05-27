from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from ..chat_summary.builder import build_chat_summary
from ..chat_summary.formatter import format_chat_summary
from ..history.indexer import build_history_index
from ..history.trend_reporter import build_trend_report
from ..alipay_parser import parse_alipay_file, write_converted_holdings
from ..notifications.orchestrator import run_notification_orchestrator
from ..pipeline import run_asset_pipeline
from ..preflight.checks import run_preflight
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..schema.errors import make_error
from ..ux.daily_console import format_daily_console_output
from .config import load_workflow_config_bundle


def run_daily_workflow(config_path: str = "private/config.local.yaml") -> dict[str, Any]:
    workflow_date = date.today().isoformat()
    try:
        bundle = load_workflow_config_bundle(config_path)
        config = bundle.config
    except FileNotFoundError:
        return _failure(config_path, workflow_date, [make_error("input", "CONFIG_NOT_FOUND", f"Workflow config not found: {config_path}")])
    except Exception as exc:
        return _failure(config_path, workflow_date, [make_error("input", "CONFIG_ERROR", str(exc))])

    converted_holdings: str | None = None
    warnings: list[str] = list(bundle.warnings)
    notification_result: dict[str, Any] | None = None
    preflight_result: dict[str, Any] | None = None
    profile_metadata = dict(bundle.profile or {})
    effective_config: dict[str, Any] = dict(bundle.effective_config or {})
    effective_config_path: str | None = None

    try:
        daily_dir = Path(config.output.daily_dir) / workflow_date
        latest_dir = Path(config.output.latest_dir)
        daily_dir.mkdir(parents=True, exist_ok=True)
        latest_dir.mkdir(parents=True, exist_ok=True)
        effective_config_file = daily_dir / "effective_config.json"
        effective_config_file.write_text(json.dumps(effective_config, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.copyfile(effective_config_file, latest_dir / "effective_config.json")
        effective_config_path = str(latest_dir / "effective_config.json")
        preflight_json = daily_dir / "preflight_report.json"
        preflight_md = daily_dir / "preflight_report.md"

        if config.preflight.enabled:
            preflight_result = run_preflight(
                config_path=config_path,
                json_output=str(preflight_json),
                markdown_output=str(preflight_md),
            )
            shutil.copyfile(preflight_json, latest_dir / "preflight_report.json")
            if preflight_md.exists():
                shutil.copyfile(preflight_md, latest_dir / "preflight_report.md")
            warnings.extend(str(item) for item in preflight_result.get("warnings", []))
            if not preflight_result.get("ok"):
                return _failure(
                    config_path,
                    workflow_date,
                    list(preflight_result.get("errors", [])),
                    converted_holdings=converted_holdings,
                    warnings=warnings,
                    latest_dir=str(latest_dir),
                    preflight=preflight_result,
                    effective_config=effective_config_path,
                    profile=profile_metadata,
                )

        holdings_path = Path(config.input.holdings_yaml)
        if config.input.mode == "alipay_csv":
            alipay_path = Path(config.input.alipay_csv)
            result = parse_alipay_file(alipay_path)
            if result.valid_count == 0:
                return _failure(config_path, workflow_date, [make_error("convert", "NO_VALID_ROWS", "No valid holdings rows were converted from Alipay input.")])
            converted_path = holdings_path if holdings_path.suffix.lower() in {".yaml", ".yml", ".json"} else Path(config.output.daily_dir) / workflow_date / "holdings.local.yaml"
            output_format = "json" if converted_path.suffix.lower() == ".json" else "yaml"
            write_converted_holdings(result, converted_path, output_format=output_format)
            converted_holdings = str(converted_path)
            warnings.extend([f"Row {item.row}: {item.message}" for item in result.warnings])
            warnings.extend([f"Row {item.row}: {item.message}" for item in result.errors])
            holdings_path = converted_path
        elif config.input.mode != "holdings_yaml":
            return _failure(config_path, workflow_date, [make_error("input", "INVALID_MODE", f"Unsupported input mode: {config.input.mode}")])

        run_asset_pipeline(
            input_path=holdings_path,
            output_dir=daily_dir,
            data_source=config.analysis.data_source,
            rules_path=config.analysis.rules,
            reporter_mode=config.analysis.reporter,
            asset_groups_path=config.analysis.asset_groups,
            portfolio_template_path=config.analysis.portfolio_template,
            overseas_exposure_path=config.analysis.overseas_exposure,
            quotes_path=config.analysis.quotes,
            profile_metadata=profile_metadata,
        )

        report_json = daily_dir / "report.json"
        report_md = daily_dir / "report.md"
        run_json = daily_dir / "run.json"
        copied_names = ["report.json", "report.md", "run.json"]

        if config.chat_summary.enabled:
            try:
                preflight_warning_count = 0
                if preflight_result:
                    preflight_warning_count = sum(
                        1 for item in preflight_result.get("checks", []) if not item.get("ok") and item.get("severity") == "warning"
                    )
                extra_chat_warnings = []
                if preflight_warning_count:
                    extra_chat_warnings.append(f"数据检查发现 {preflight_warning_count} 条提醒，建议查看 preflight_report.md。")
                chat_summary = build_chat_summary(
                    report_path=str(report_json),
                    max_signals=config.chat_summary.max_signals,
                    max_warnings=config.chat_summary.max_warnings,
                    style=config.chat_summary.style,
                    extra_warnings=extra_chat_warnings,
                )
                (daily_dir / "chat_summary.json").write_text(json.dumps(chat_summary, ensure_ascii=False, indent=2), encoding="utf-8")
                (daily_dir / "chat_summary.txt").write_text(format_chat_summary(chat_summary, format="text"), encoding="utf-8")
                (daily_dir / "chat_summary.md").write_text(format_chat_summary(chat_summary, format="markdown"), encoding="utf-8")
                copied_names.extend(["chat_summary.json", "chat_summary.txt", "chat_summary.md"])
            except Exception as exc:
                warnings.append(f"Chat summary generation failed: {exc}")

        _copy_latest_outputs(daily_dir, latest_dir, names=copied_names)

        if config.notification.enabled:
            notification_result = run_notification_orchestrator(
                report_path=str(report_json),
                config_path=config.notification.config,
                dry_run=config.notification.dry_run,
            )
            if not notification_result.get("ok"):
                warnings.append("Notification orchestration did not fully succeed.")

        if config.history.enabled:
            try:
                history_payload = build_history_index(
                    reports_dir=config.history.reports_dir,
                    output_path=config.history.index_path,
                )
                warnings.extend([f"History: {item}" for item in history_payload.get("warnings", [])])
                if history_payload.get("count", 0) >= 2:
                    build_trend_report(
                        index_path=config.history.index_path,
                        output_path=config.history.trend_output_dir,
                    )
            except Exception as exc:
                warnings.append(f"History generation failed: {exc}")

        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "ok": True,
            "workflow": "daily_local",
            "config": config_path,
            "date": workflow_date,
            "converted_holdings": converted_holdings,
            "report_json": str(report_json),
            "report_md": str(report_md),
            "run_json": str(run_json),
            "latest_dir": str(latest_dir),
            "profile": profile_metadata,
            "effective_config": effective_config_path,
            "preflight": preflight_result,
            "notification": notification_result,
            "errors": [],
            "warnings": warnings,
        }
    except FileNotFoundError as exc:
        return _failure(config_path, workflow_date, [make_error("input", "FILE_NOT_FOUND", str(exc))], converted_holdings=converted_holdings, warnings=warnings, effective_config=effective_config_path, profile=profile_metadata)
    except Exception as exc:
        return _failure(config_path, workflow_date, [make_error("unknown", "WORKFLOW_ERROR", str(exc))], converted_holdings=converted_holdings, warnings=warnings, effective_config=effective_config_path, profile=profile_metadata)


def _copy_latest_outputs(daily_dir: Path, latest_dir: Path, names: list[str] | None = None) -> None:
    for name in (names or ["report.json", "report.md", "run.json"]):
        source = daily_dir / name
        if source.exists():
            shutil.copyfile(source, latest_dir / name)


def _failure(
    config_path: str,
    workflow_date: str,
    errors: list[dict[str, Any]],
    converted_holdings: str | None = None,
    warnings: list[str] | None = None,
    latest_dir: str | None = None,
    preflight: dict[str, Any] | None = None,
    effective_config: str | None = None,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": False,
        "workflow": "daily_local",
        "config": config_path,
        "date": workflow_date,
        "converted_holdings": converted_holdings,
        "report_json": None,
        "report_md": None,
        "run_json": None,
        "latest_dir": latest_dir,
        "profile": profile or {},
        "effective_config": effective_config,
        "preflight": preflight,
        "notification": None,
        "errors": errors,
        "warnings": warnings or [],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local daily asset analysis workflow.")
    parser.add_argument("--config", default="private/config.local.yaml", help="Path to local workflow config.")
    parser.add_argument("--json-only", action=argparse.BooleanOptionalAction, default=False, help="Print only JSON result.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_daily_workflow(config_path=args.config)
    if not args.json_only:
        print(format_daily_console_output(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
