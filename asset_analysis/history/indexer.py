from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .snapshot import compact_index_item, load_report_snapshot


def build_history_index(
    reports_dir: str = "reports/daily",
    output_path: str = "reports/history_index.json",
) -> dict[str, Any]:
    base = Path(reports_dir)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[dict[str, Any]] = []

    if base.exists():
        report_files = sorted(base.glob("*/report.json"))
        for report_file in report_files:
            try:
                report = load_report_snapshot(report_file)
                if not isinstance(report, dict) or "summary" not in report:
                    warnings.append(f"Skipped invalid report payload: {report_file}")
                    continue
                items.append(compact_index_item(report, report_file))
            except Exception as exc:
                warnings.append(f"Skipped unreadable report: {report_file} ({exc})")
    items.sort(key=lambda item: (str(item.get("generated_at") or ""), str(item.get("date") or "")))

    payload = {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "reports_dir": str(base),
        "count": len(items),
        "items": items,
        "errors": errors,
        "warnings": warnings,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact history index from daily asset reports.")
    parser.add_argument("--reports-dir", default="reports/daily", help="Directory containing dated daily report folders.")
    parser.add_argument("--output", default="reports/history_index.json", help="History index output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = build_history_index(reports_dir=args.reports_dir, output_path=args.output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
