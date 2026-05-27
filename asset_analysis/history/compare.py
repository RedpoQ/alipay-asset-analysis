from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .snapshot import group_warnings_from_report, load_report_snapshot


def compare_reports(current_report_path: str, previous_report_path: str) -> dict[str, Any]:
    current = load_report_snapshot(current_report_path)
    previous = load_report_snapshot(previous_report_path)

    current_summary = current.get("summary", {}) or {}
    previous_summary = previous.get("summary", {}) or {}

    current_signals = {str(item.get("code")): item for item in current.get("signals", [])}
    previous_signals = {str(item.get("code")): item for item in previous.get("signals", [])}

    signal_changes: list[dict[str, Any]] = []
    for code in sorted(set(current_signals) | set(previous_signals)):
        current_signal = current_signals.get(code, {})
        previous_signal = previous_signals.get(code, {})
        current_name = current_signal.get("name") or previous_signal.get("name") or code
        prev_value = previous_signal.get("signal")
        curr_value = current_signal.get("signal")
        if prev_value != curr_value:
            signal_changes.append(
                {
                    "code": code,
                    "name": current_name,
                    "signal_changed": True,
                    "previous_signal": prev_value,
                    "current_signal": curr_value,
                }
            )

    current_positions = {str(item.get("code")): item for item in current.get("positions", [])}
    previous_positions = {str(item.get("code")): item for item in previous.get("positions", [])}
    position_changes: list[dict[str, Any]] = []
    for code in sorted(set(current_positions) | set(previous_positions)):
        current_position = current_positions.get(code, {})
        previous_position = previous_positions.get(code, {})
        if not current_position and not previous_position:
            continue
        position_changes.append(
            {
                "code": code,
                "name": current_position.get("name") or previous_position.get("name") or code,
                "current_position_delta": _round_delta(current_position.get("current_position", 0), previous_position.get("current_position", 0)),
                "profit_rate_delta": _round_delta(current_position.get("profit_rate", 0), previous_position.get("profit_rate", 0)),
            }
        )

    current_groups = {
        str(item.get("group")): item for item in ((current.get("group_analysis") or {}).get("groups", []) or [])
    }
    previous_groups = {
        str(item.get("group")): item for item in ((previous.get("group_analysis") or {}).get("groups", []) or [])
    }
    group_changes: list[dict[str, Any]] = []
    for group_name in sorted(set(current_groups) | set(previous_groups)):
        current_group = current_groups.get(group_name, {})
        previous_group = previous_groups.get(group_name, {})
        current_group_warnings = set(str(item) for item in current_group.get("warnings", []))
        previous_group_warnings = set(str(item) for item in previous_group.get("warnings", []))
        group_changes.append(
            {
                "group": group_name,
                "group_position_delta": _round_delta(current_group.get("current_position", 0), previous_group.get("current_position", 0)),
                "new_group_warnings": sorted(current_group_warnings - previous_group_warnings),
                "resolved_group_warnings": sorted(previous_group_warnings - current_group_warnings),
            }
        )

    current_warnings = set(str(item) for item in current.get("portfolio_warnings", []))
    previous_warnings = set(str(item) for item in previous.get("portfolio_warnings", []))

    result = {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "current": current_report_path,
        "previous": previous_report_path,
        "summary_delta": {
            "total_market_value_delta": _round_delta(current_summary.get("total_market_value", 0), previous_summary.get("total_market_value", 0)),
            "total_profit_delta": _round_delta(current_summary.get("total_profit", 0), previous_summary.get("total_profit", 0)),
            "total_profit_rate_delta": _round_delta(current_summary.get("total_profit_rate", 0), previous_summary.get("total_profit_rate", 0)),
        },
        "signal_changes": signal_changes,
        "position_changes": position_changes,
        "group_changes": group_changes,
        "warning_changes": {
            "new": sorted(current_warnings - previous_warnings),
            "resolved": sorted(previous_warnings - current_warnings),
        },
        "errors": [],
        "warnings": _comparison_warnings(current, previous),
    }
    return result


def _comparison_warnings(current: dict[str, Any], previous: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not current.get("group_analysis") or not previous.get("group_analysis"):
        warnings.append("Group analysis is missing in one or both reports; group comparisons may be partial.")
    return warnings


def _round_delta(current: Any, previous: Any) -> float:
    return round(float(current or 0) - float(previous or 0), 6)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two historical asset report snapshots.")
    parser.add_argument("--current", required=True, help="Current report.json path.")
    parser.add_argument("--previous", required=True, help="Previous report.json path.")
    parser.add_argument("--output", default=None, help="Optional output path for compare JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = compare_reports(args.current, args.previous)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
