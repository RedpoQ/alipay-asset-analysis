from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_report_snapshot(report_path: str | Path) -> dict[str, Any]:
    path = Path(report_path)
    return json.loads(path.read_text(encoding="utf-8"))


def signals_summary_from_report(report: dict[str, Any]) -> dict[str, int]:
    counts = {"add": 0, "reduce": 0, "hold": 0}
    for signal in report.get("signals", []):
        signal_name = str(signal.get("signal", ""))
        if signal_name in counts:
            counts[signal_name] += 1
    return counts


def group_warnings_from_report(report: dict[str, Any]) -> list[str]:
    group_analysis = report.get("group_analysis") or {}
    warnings = group_analysis.get("warnings", [])
    return [str(item) for item in warnings if item]


def compact_index_item(report: dict[str, Any], report_json_path: str | Path) -> dict[str, Any]:
    report_path = Path(report_json_path)
    run = report.get("run", {}) or {}
    summary = report.get("summary", {}) or {}
    portfolio_warnings = [str(item) for item in report.get("portfolio_warnings", [])]
    group_warnings = group_warnings_from_report(report)
    date_value = report_path.parent.name
    report_md = report_path.with_name("report.md")
    return {
        "date": date_value,
        "generated_at": report.get("generated_at"),
        "report_json": str(report_path),
        "report_md": str(report_md),
        "summary": {
            "total_cost": summary.get("total_cost", 0),
            "total_market_value": summary.get("total_market_value", 0),
            "total_profit": summary.get("total_profit", 0),
            "total_profit_rate": summary.get("total_profit_rate", 0),
        },
        "signals_summary": signals_summary_from_report(report),
        "portfolio_warnings_count": len(portfolio_warnings),
        "group_warnings_count": len(group_warnings),
        "top_warnings": (portfolio_warnings[:2] + [item for item in group_warnings if item not in portfolio_warnings][:1])[:3],
    }
