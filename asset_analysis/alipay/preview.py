from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..alipay_parser import convert_records_to_holdings
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .normalizer import normalize_tabular_records


def build_preview_payload(input_path: str | Path, default_target_position: float = 0.0) -> dict[str, Any]:
    from ..alipay_parser import _load_csv_records, _load_json_records

    path = Path(input_path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        raw_records = _load_json_records(text)
    else:
        raw_records = _load_csv_records(text)
    table = normalize_tabular_records(raw_records)
    conversion = convert_records_to_holdings(raw_records, default_target_position=default_target_position)
    warnings = [issue.to_dict() for issue in conversion.warnings]
    warnings.extend({"row": 0, "level": "warning", "message": f"Unrecognized columns: {', '.join(table.unknown_columns)}"} for _ in [0] if table.unknown_columns)
    next_command = (
        f"python -m asset_analysis.alipay_parser --input {path.as_posix()} --output private/holdings.local.yaml"
    )
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": conversion.valid_count > 0,
        "input": str(path),
        "detected_columns": table.detected_columns,
        "canonical_field_mapping": table.canonical_mapping,
        "unknown_columns": table.unknown_columns,
        "valid_rows_count": conversion.valid_count,
        "invalid_rows_count": len(conversion.errors),
        "warnings": warnings,
        "errors": [issue.to_dict() for issue in conversion.errors],
        "first_normalized_rows": conversion.normalized_rows[:3],
        "suggested_next_command": next_command,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview Alipay CSV field mapping and normalization before conversion.")
    parser.add_argument("--input", required=True, help="CSV or JSON holdings export path.")
    parser.add_argument("--json", action=argparse.BooleanOptionalAction, default=False, help="Print JSON only.")
    parser.add_argument("--default-target-position", type=float, default=0.0, help="Default target position used during validation.")
    return parser


def _render_text_preview(payload: dict[str, Any]) -> str:
    lines = [
        f"Detected columns: {', '.join(payload.get('detected_columns', [])) or '(none)'}",
        f"Canonical mapping: {json.dumps(payload.get('canonical_field_mapping', {}), ensure_ascii=False)}",
        f"Valid rows: {payload.get('valid_rows_count', 0)}",
        f"Invalid rows: {payload.get('invalid_rows_count', 0)}",
        "Warnings:",
    ]
    warning_items = payload.get("warnings", []) or []
    if warning_items:
        lines.extend(f"- Row {item.get('row')}: {item.get('message')}" for item in warning_items)
    else:
        lines.append("- None")
    lines.append("First 3 normalized rows:")
    preview_rows = payload.get("first_normalized_rows", []) or []
    if preview_rows:
        lines.extend(f"- {json.dumps(row, ensure_ascii=False)}" for row in preview_rows)
    else:
        lines.append("- None")
    lines.append(f"Suggested next command: {payload.get('suggested_next_command', '')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = build_preview_payload(args.input, default_target_position=args.default_target_position)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text_preview(payload))
    return 0 if payload.get("valid_rows_count", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
