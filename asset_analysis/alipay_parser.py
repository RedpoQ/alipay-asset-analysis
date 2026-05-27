from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .alipay.normalizer import RowIssue, TabularNormalizationResult, is_missing_value, normalize_tabular_records, normalize_text_value, parse_numeric_value


class ImportResult:
    def __init__(
        self,
        *,
        holdings: dict[str, list[dict[str, Any]]],
        warnings: list[RowIssue] | None = None,
        errors: list[RowIssue] | None = None,
        normalized_rows: list[dict[str, Any]] | None = None,
        detected_columns: list[str] | None = None,
        canonical_mapping: dict[str, str] | None = None,
        unknown_columns: list[str] | None = None,
    ) -> None:
        self.holdings = holdings
        self.warnings = warnings or []
        self.errors = errors or []
        self.normalized_rows = normalized_rows or []
        self.detected_columns = detected_columns or []
        self.canonical_mapping = canonical_mapping or {}
        self.unknown_columns = unknown_columns or []

    @property
    def valid_count(self) -> int:
        return len(self.holdings.get("funds", []))


def parse_alipay_file(path: str | Path, default_target_position: float = 0.0) -> ImportResult:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8-sig")
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        records = _load_csv_records(text)
    elif suffix == ".json":
        records = _load_json_records(text)
    else:
        raise ValueError(f"Unsupported input format: {suffix or 'unknown'}")
    return convert_records_to_holdings(records, default_target_position=default_target_position)


def convert_records_to_holdings(
    records: list[dict[str, Any]], default_target_position: float = 0.0
) -> ImportResult:
    table = normalize_tabular_records(records)
    holdings: list[dict[str, Any]] = []
    normalized_rows: list[dict[str, Any]] = []
    warnings: list[RowIssue] = []
    errors: list[RowIssue] = []

    if table.unknown_columns:
        warnings.append(
            RowIssue(
                row=0,
                level="warning",
                message=f"Unrecognized columns preserved in metadata: {', '.join(table.unknown_columns)}",
            )
        )

    for index, normalized_record in enumerate(table.records, start=1):
        try:
            normalized_row, holding, row_warnings = _convert_record(
                normalized_record,
                row_number=index,
                default_target_position=default_target_position,
            )
            normalized_rows.append(normalized_row)
            holdings.append(holding)
            warnings.extend(row_warnings)
        except ValueError as exc:
            errors.append(RowIssue(row=index, level="error", message=str(exc)))

    return ImportResult(
        holdings={"funds": holdings},
        warnings=warnings,
        errors=errors,
        normalized_rows=normalized_rows,
        detected_columns=table.detected_columns,
        canonical_mapping=table.canonical_mapping,
        unknown_columns=table.unknown_columns,
    )


def write_converted_holdings(result: ImportResult, output_path: str | Path, output_format: str | None = None) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fmt = (output_format or destination.suffix.lstrip(".") or "yaml").lower()
    data = result.holdings
    if fmt == "json":
        destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    elif fmt in {"yaml", "yml"}:
        destination.write_text(_dump_simple_yaml(data), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported output format: {fmt}")
    return destination


def _load_csv_records(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(text.splitlines())
    return [dict(row) for row in reader]


def _load_json_records(text: str) -> list[dict[str, Any]]:
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise ValueError("JSON input must be a list of holding records.")
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("JSON input records must be objects.")
    return payload

def _convert_record(
    record: dict[str, Any],
    row_number: int,
    default_target_position: float,
) -> tuple[dict[str, Any], dict[str, Any], list[RowIssue]]:
    warnings: list[RowIssue] = []
    code = _require_text(record.get("code"), "Missing fund code.")
    name = _require_text(record.get("name"), "Missing fund name.")

    amount = _parse_numeric(record, "amount", row_number, warnings)
    market_value = _parse_numeric(record, "market_value", row_number, warnings)
    shares = _parse_numeric(record, "shares", row_number, warnings)
    cost_nav = _parse_numeric(record, "cost_nav", row_number, warnings)
    current_nav = _parse_numeric(record, "current_nav", row_number, warnings)
    profit_rate = _parse_numeric(record, "profit_rate", row_number, warnings)
    target_position = _parse_numeric(record, "target_position", row_number, warnings)

    if amount is None and market_value is not None:
        amount = market_value
        warnings.append(RowIssue(row=row_number, level="warning", message="Mapped market_value to amount for standard holdings output."))
    if amount is None:
        raise ValueError("Missing amount or market_value; cannot build standard holding.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if target_position is None:
        target_position = default_target_position
        warnings.append(RowIssue(row=row_number, level="warning", message="Missing target_position; default value was applied."))

    if cost_nav is None and shares and shares > 0 and market_value is not None and market_value > 0:
        cost_nav = round(market_value / shares, 6)
        warnings.append(RowIssue(row=row_number, level="warning", message="Derived approximate cost_nav from market_value and shares."))

    if cost_nav is None and current_nav is not None and current_nav > 0:
        cost_nav = current_nav
        warnings.append(RowIssue(row=row_number, level="warning", message="Used current_nav as fallback cost_nav because no historical cost was provided."))

    if cost_nav is None:
        raise ValueError("Missing cost_nav and no safe derivation path available.")

    metadata = {
        "source": "alipay_import",
        "raw_market_value": market_value,
        "raw_shares": shares,
        "raw_current_nav": current_nav,
        "raw_profit_rate": profit_rate,
    }
    metadata.update(record.get("metadata", {}))

    normalized_row = {
        "code": code,
        "name": name,
        "market_value": market_value,
        "amount": amount,
        "shares": shares,
        "cost_nav": cost_nav,
        "current_nav": current_nav,
        "profit_rate": profit_rate,
        "target_position": target_position,
        "metadata": {key: value for key, value in metadata.items() if value not in (None, "")},
    }

    holding = {
        "code": code,
        "name": name,
        "type": "fund",
        "cost_nav": round(cost_nav, 6),
        "amount": round(amount, 6),
        "target_position": round(target_position, 6),
        "metadata": {key: value for key, value in metadata.items() if value not in (None, "")},
    }
    return normalized_row, holding, warnings


def _require_text(value: Any, error_message: str) -> str:
    text = normalize_text_value(value)
    if not text or is_missing_value(text):
        raise ValueError(error_message)
    return text


def _parse_numeric(record: dict[str, Any], field_name: str, row_number: int, warnings: list[RowIssue]) -> float | None:
    value = record.get(field_name)
    if value is None:
        return None
    if is_missing_value(value):
        warnings.append(RowIssue(row=row_number, level="warning", message=f"Missing {field_name}; source value treated as empty."))
        return None
    try:
        return parse_numeric_value(value, field_name=field_name)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _dump_simple_yaml(data: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = []
    for group_name, items in data.items():
        lines.append(f"{group_name}:")
        for item in items:
            lines.append(f'  - code: "{item["code"]}"')
            lines.append(f'    name: "{_escape_yaml_string(item["name"])}"')
            lines.append(f'    type: "{item["type"]}"')
            lines.append(f"    cost_nav: {item['cost_nav']}")
            lines.append(f"    amount: {item['amount']}")
            lines.append(f"    target_position: {item['target_position']}")
            metadata = item.get("metadata") or {}
            if metadata:
                lines.append("    metadata:")
                for key, value in metadata.items():
                    if isinstance(value, str):
                        lines.append(f'      {key}: "{_escape_yaml_string(value)}"')
                    else:
                        lines.append(f"      {key}: {json.dumps(value, ensure_ascii=False)}")
        if not items:
            lines.append("  []")
    return "\n".join(lines) + "\n"


def _escape_yaml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Alipay-style holdings into standard asset_analysis holdings.")
    parser.add_argument("--input", required=True, help="CSV or JSON holdings export path.")
    parser.add_argument("--output", required=True, help="Path to converted YAML or JSON holdings file.")
    parser.add_argument("--format", choices=("yaml", "json"), help="Explicit output format override.")
    parser.add_argument("--default-target-position", type=float, default=0.0, help="Default target position when missing in input rows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = parse_alipay_file(args.input, default_target_position=args.default_target_position)
        if result.valid_count == 0:
            for issue in result.errors:
                print(f"Row {issue.row} [{issue.level}]: {issue.message}", file=sys.stderr)
            print("Alipay import failed: no valid rows were converted.", file=sys.stderr)
            return 1
        output_path = write_converted_holdings(result, args.output, output_format=args.format)
    except Exception as exc:
        print(f"Alipay import failed: {exc}", file=sys.stderr)
        return 1

    for issue in result.warnings:
        print(f"Row {issue.row} [warning]: {issue.message}", file=sys.stderr)
    for issue in result.errors:
        print(f"Row {issue.row} [error]: {issue.message}", file=sys.stderr)
    print(f"Converted holdings written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
