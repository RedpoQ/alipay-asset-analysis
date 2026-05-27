from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .alipay_parser import parse_alipay_file, write_converted_holdings
from .pipeline import run_asset_pipeline
from .schema.adapter_schema import merge_adapter_contract
from .schema.errors import make_error
from .schema.validators import validate_adapter_result_schema


def run_asset_analysis_skill(
    holdings_path: str,
    output_dir: str,
    data_source: str = "mock",
    rules_path: str | None = None,
    reporter: str = "offline",
    alipay_input_path: str | None = None,
    alipay_output_path: str | None = None,
    alipay_output_format: str = "yaml",
    archive: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[dict[str, str]] = []
    output_path = Path(output_dir)
    converted_holdings_path: Path | None = None

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return _failure("unknown", "OUTPUT_DIR_ERROR", f"Failed to prepare output directory: {exc}", warnings=warnings)

    standard_holdings_path = Path(holdings_path) if holdings_path else None

    if alipay_input_path:
        try:
            import_result = parse_alipay_file(alipay_input_path)
        except FileNotFoundError:
            return _failure("convert", "ALIPAY_INPUT_NOT_FOUND", f"Alipay input file not found: {alipay_input_path}", warnings=warnings)
        except Exception as exc:
            return _failure("convert", "ALIPAY_CONVERT_ERROR", f"Failed to convert Alipay input: {exc}", warnings=warnings)

        warnings.extend(_format_import_warnings(import_result.warnings))
        if import_result.valid_count == 0:
            errors.extend(_format_import_errors(import_result.errors, stage="convert"))
            return _failure_payload(errors=errors, warnings=warnings)

        converted_holdings_path = (
            Path(alipay_output_path)
            if alipay_output_path
            else output_path / f"converted_holdings.{alipay_output_format.lower()}"
        )
        try:
            write_converted_holdings(import_result, converted_holdings_path, output_format=alipay_output_format)
        except Exception as exc:
            return _failure("convert", "ALIPAY_WRITE_ERROR", f"Failed to write converted holdings: {exc}", warnings=warnings)
        standard_holdings_path = converted_holdings_path

    if standard_holdings_path is None:
        return _failure("parse", "MISSING_HOLDINGS", "No holdings path was provided.", warnings=warnings)

    if not standard_holdings_path.exists():
        return _failure("parse", "HOLDINGS_NOT_FOUND", f"Holdings file not found: {standard_holdings_path}", warnings=warnings)

    if rules_path and not Path(rules_path).exists():
        return _failure("parse", "RULES_NOT_FOUND", f"Rules file not found: {rules_path}", warnings=warnings)

    try:
        result = run_asset_pipeline(
            input_path=standard_holdings_path,
            output_dir=output_path,
            data_source=data_source,
            rules_path=rules_path,
            reporter_mode=reporter,
            archive=archive,
        )
    except Exception as exc:
        return _failure("pipeline", "PIPELINE_ERROR", str(exc), warnings=warnings)

    report_json = output_path / "report.json"
    report_md = output_path / "report.md"
    if not report_json.exists() or not report_md.exists():
        return _failure("read_report", "MISSING_REPORT_FILES", "Pipeline finished but expected report files were not generated.", warnings=warnings)

    for position in result.positions:
        if position.error:
            warnings.append(f"{position.code}: {position.error['message']}")

    payload = merge_adapter_contract(
        {
        "ok": True,
        "report_json": str(report_json),
        "report_md": str(report_md),
        "converted_holdings": str(converted_holdings_path) if converted_holdings_path else None,
        "summary": result.summary.to_dict(),
        "signals": [signal.to_dict() for signal in result.signals],
        "portfolio_warnings": list(result.portfolio_warnings),
        "reporter": dict(result.reporter),
        "errors": [],
        "warnings": warnings,
        }
    )
    payload["schema_errors"] = validate_adapter_result_schema(payload)
    return payload


def _format_import_warnings(items: list[Any]) -> list[str]:
    return [f"row {item.row}: {item.message}" for item in items]


def _format_import_errors(items: list[Any], stage: str) -> list[dict[str, str]]:
    return [make_error(stage, "ROW_ERROR", f"row {item.row}: {item.message}") for item in items]


def _failure(stage: str, code: str, message: str, warnings: list[str] | None = None) -> dict[str, Any]:
    return _failure_payload(errors=[make_error(stage, code, message)], warnings=warnings or [])


def _failure_payload(errors: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    payload = merge_adapter_contract(
        {
        "ok": False,
        "report_json": None,
        "report_md": None,
        "converted_holdings": None,
        "summary": None,
        "signals": [],
        "portfolio_warnings": [],
        "reporter": None,
        "errors": errors,
        "warnings": warnings,
        }
    )
    payload["schema_errors"] = validate_adapter_result_schema(payload)
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the asset_analysis OpenClaw-compatible adapter.")
    parser.add_argument("--holdings", required=False, default="", help="Path to standard holdings YAML/JSON.")
    parser.add_argument("--output", required=True, help="Directory for generated reports.")
    parser.add_argument("--data-source", choices=("mock", "auto", "public_fund"), default="mock")
    parser.add_argument("--rules", default=None, help="Optional rules config path.")
    parser.add_argument("--reporter", choices=("offline", "auto", "llm"), default="offline")
    parser.add_argument("--archive", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--alipay-input", default=None, help="Optional Alipay CSV/JSON input path.")
    parser.add_argument("--alipay-output", default=None, help="Optional converted holdings output path.")
    parser.add_argument("--alipay-output-format", choices=("yaml", "json"), default="yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_asset_analysis_skill(
        holdings_path=args.holdings,
        output_dir=args.output,
        data_source=args.data_source,
        rules_path=args.rules,
        reporter=args.reporter,
        alipay_input_path=args.alipay_input,
        alipay_output_path=args.alipay_output,
        alipay_output_format=args.alipay_output_format,
        archive=args.archive,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
