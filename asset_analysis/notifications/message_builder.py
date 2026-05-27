from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..schema.errors import make_error
from ..schema.validators import validate_report_schema


def load_report_payload(report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Report payload must be a JSON object.")
    schema_errors = validate_report_schema(payload)
    if schema_errors and "schema_errors" not in payload:
        payload["schema_errors"] = schema_errors
    return payload


def build_notification_message(report_path: str | Path, report_md_path: str | Path | None = None) -> dict[str, Any]:
    report_path_obj = Path(report_path)
    payload = load_report_payload(report_path_obj)
    resolved_report_md = Path(report_md_path) if report_md_path else report_path_obj.with_name("report.md")
    report_md = str(resolved_report_md)
    chat_summary_json = report_path_obj.with_name("chat_summary.json")
    chat_summary_txt = report_path_obj.with_name("chat_summary.txt")
    chat_summary_payload = _load_optional_chat_summary(chat_summary_json)
    chat_summary_text = chat_summary_txt.read_text(encoding="utf-8").strip() if chat_summary_txt.exists() else ""
    signals = payload.get("signals", [])
    portfolio_warnings = payload.get("portfolio_warnings", [])
    group_analysis = payload.get("group_analysis", {})
    group_warnings = list(group_analysis.get("warnings", []))
    signals_summary = _count_signals(signals)
    top_signals = [
        {
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "signal": item.get("signal", ""),
            "reason": item.get("reason", ""),
        }
        for item in signals[:3]
    ]
    summary = payload.get("summary", {})
    summary_text = str(chat_summary_payload.get("one_line", "")) if chat_summary_payload else ""
    if not summary_text:
        summary_text = (
            f"收益率 {summary.get('total_profit_rate', 0):.2%}；"
            f"可补仓观察 {signals_summary['add']}，建议减仓观察 {signals_summary['reduce']}，继续持有观察 {signals_summary['hold']}；"
            f"组合风险提醒 {len(portfolio_warnings)} 条；"
            f"分组风险提醒 {len(group_warnings)} 条；"
            "规则驱动，不是价格预测。"
        )
    return {
        "title": "Daily Asset Analysis",
        "summary": summary_text,
        "chat_summary_text": chat_summary_text,
        "signals_summary": signals_summary,
        "top_signals": top_signals,
        "portfolio_warnings": portfolio_warnings,
        "group_warnings": group_warnings,
        "top_group_warning": group_warnings[0] if group_warnings else "",
        "report_json": str(report_path),
        "report_md": report_md,
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
    }


def _load_optional_chat_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _count_signals(signals: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"add": 0, "reduce": 0, "hold": 0}
    for signal in signals:
        name = str(signal.get("signal", "")).lower()
        if name in counts:
            counts[name] += 1
    return counts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a notification message from a report.json file.")
    parser.add_argument("--report", required=True, help="Path to report.json.")
    parser.add_argument("--report-md", default=None, help="Optional path to report.md.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        payload = build_notification_message(args.report, args.report_md)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [make_error("read_report", "READ_REPORT_ERROR", str(exc))]}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
