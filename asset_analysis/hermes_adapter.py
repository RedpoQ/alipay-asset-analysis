from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .chat_summary.builder import build_chat_summary
from .chat_summary.formatter import format_chat_summary
from .openclaw_adapter import run_asset_analysis_skill
from .schema.adapter_schema import merge_adapter_contract
from .schema.errors import make_error
from .schema.validators import validate_adapter_result_schema


def run_daily_asset_analysis_task(
    holdings_path: str | None = None,
    alipay_input_path: str | None = None,
    output_dir: str = "reports/hermes_daily",
    data_source: str = "mock",
    rules_path: str | None = None,
    reporter: str = "offline",
    summarize_markdown: bool = True,
    archive: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []

    if not holdings_path and not alipay_input_path:
        return _failure("input", "MISSING_INPUT", "Either holdings_path or alipay_input_path must be provided.", warnings)

    try:
        adapter_result = run_asset_analysis_skill(
            holdings_path=holdings_path or "",
            output_dir=output_dir,
            data_source=data_source,
            rules_path=rules_path,
            reporter=reporter,
            alipay_input_path=alipay_input_path,
            archive=archive,
        )
    except Exception as exc:
        return _failure("adapter", "ADAPTER_ERROR", str(exc), warnings)

    if not adapter_result.get("ok"):
        payload = merge_adapter_contract(
            {
            "ok": False,
            "task": "daily_asset_analysis",
            "report_json": None,
            "report_md": None,
            "summary": None,
            "signals_summary": {"add": 0, "reduce": 0, "hold": 0},
            "top_signals": [],
            "portfolio_warnings": [],
            "reporter": None,
            "daily_message": "",
            "errors": list(adapter_result.get("errors", [])),
            "warnings": list(adapter_result.get("warnings", [])),
            }
        )
        payload["schema_errors"] = validate_adapter_result_schema(payload)
        return payload

    report_json = adapter_result.get("report_json")
    report_md = adapter_result.get("report_md")
    if not report_json or not report_md:
        return _failure("read_report", "MISSING_REPORT_PATHS", "Adapter completed but report paths are missing.", warnings)

    try:
        payload = json.loads(Path(report_json).read_text(encoding="utf-8"))
    except Exception as exc:
        return _failure("read_report", "READ_REPORT_JSON_ERROR", f"Failed to read report.json: {exc}", warnings)

    try:
        markdown_text = Path(report_md).read_text(encoding="utf-8") if summarize_markdown else ""
    except Exception as exc:
        return _failure("read_report", "READ_REPORT_MD_ERROR", f"Failed to read report.md: {exc}", warnings)

    signals = payload.get("signals", [])
    portfolio_warnings = payload.get("portfolio_warnings", [])
    signals_summary = _count_signals(signals)
    top_signals = _extract_top_signals(signals)
    chat_summary_text = None
    try:
        chat_summary_path = Path(report_json).with_name("chat_summary.txt")
        if chat_summary_path.exists():
            chat_summary_text = chat_summary_path.read_text(encoding="utf-8").strip()
        else:
            chat_summary = build_chat_summary(report_json)
            chat_summary_text = chat_summary.get("one_line") or format_chat_summary(chat_summary, format="text").strip()
    except Exception as exc:
        warnings.append(f"chat summary unavailable: {exc}")
    daily_message = _build_daily_message(
        signals_summary=signals_summary,
        portfolio_warnings=portfolio_warnings,
        report_md=report_md,
        chat_summary_text=chat_summary_text,
    )
    warnings.extend(adapter_result.get("warnings", []))
    if summarize_markdown and not markdown_text.strip():
        warnings.append("report.md was empty when the Hermes summary tried to read it.")

    result = merge_adapter_contract(
        {
        "ok": True,
        "task": "daily_asset_analysis",
        "report_json": report_json,
        "report_md": report_md,
        "summary": payload.get("summary"),
        "signals_summary": signals_summary,
        "top_signals": top_signals,
        "portfolio_warnings": portfolio_warnings,
        "reporter": payload.get("reporter"),
        "chat_summary_text": chat_summary_text,
        "daily_message": daily_message,
        "errors": [],
        "warnings": warnings,
        }
    )
    result["schema_errors"] = validate_adapter_result_schema(result)
    return result


def _count_signals(signals: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"add": 0, "reduce": 0, "hold": 0}
    for signal in signals:
        name = str(signal.get("signal", "")).lower()
        if name in counts:
            counts[name] += 1
    return counts


def _extract_top_signals(signals: list[dict[str, Any]]) -> list[dict[str, str]]:
    ordered = sorted(
        signals,
        key=lambda item: (
            {"critical": 0, "warning": 1, "normal": 2}.get(str(item.get("severity", "normal")), 3),
            {"high": 0, "medium": 1, "low": 2}.get(str(item.get("confidence", "low")), 3),
            {"reduce": 0, "add": 1, "hold": 2}.get(str(item.get("signal", "hold")), 3),
        ),
    )
    top_items = []
    for item in ordered[:3]:
        top_items.append(
            {
                "code": str(item.get("code", "")),
                "name": str(item.get("name", "")),
                "signal": str(item.get("signal", "")),
                "reason": str(item.get("reason", "")),
            }
        )
    return top_items


def _build_daily_message(signals_summary: dict[str, int], portfolio_warnings: list[Any], report_md: str, chat_summary_text: str | None = None) -> str:
    if chat_summary_text:
        return chat_summary_text
    warning_count = len(portfolio_warnings)
    return (
        "今日资产分析完成："
        f"add {signals_summary['add']} 个，"
        f"reduce {signals_summary['reduce']} 个，"
        f"hold {signals_summary['hold']} 个。"
        f"存在 {warning_count} 条组合风险提醒。"
        f"信号均为规则驱动，不包含价格预测。"
        f"报告已生成：{report_md}"
    )


def _failure(stage: str, code: str, message: str, warnings: list[str]) -> dict[str, Any]:
    result = merge_adapter_contract(
        {
        "ok": False,
        "task": "daily_asset_analysis",
        "report_json": None,
        "report_md": None,
        "summary": None,
        "signals_summary": {"add": 0, "reduce": 0, "hold": 0},
        "top_signals": [],
        "portfolio_warnings": [],
        "reporter": None,
        "daily_message": "",
        "errors": [make_error(stage, code, message)],
        "warnings": warnings,
        }
    )
    result["schema_errors"] = validate_adapter_result_schema(result)
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Hermes-friendly daily asset analysis adapter.")
    parser.add_argument("--holdings", default=None, help="Path to standard holdings YAML/JSON.")
    parser.add_argument("--alipay-input", default=None, help="Path to Alipay CSV/JSON input.")
    parser.add_argument("--output", default="reports/hermes_daily", help="Directory for generated reports.")
    parser.add_argument("--data-source", choices=("mock", "auto", "public_fund"), default="mock")
    parser.add_argument("--rules", default=None, help="Optional rules config path.")
    parser.add_argument("--reporter", choices=("offline", "auto", "llm"), default="offline")
    parser.add_argument("--archive", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--summarize-markdown",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Read generated report.md while building the deterministic Hermes summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_daily_asset_analysis_task(
        holdings_path=args.holdings,
        alipay_input_path=args.alipay_input,
        output_dir=args.output,
        data_source=args.data_source,
        rules_path=args.rules,
        reporter=args.reporter,
        summarize_markdown=args.summarize_markdown,
        archive=args.archive,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
