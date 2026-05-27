from __future__ import annotations

import argparse
import json

from .bundle import build_demo_bundle


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a sanitized public demo bundle from a report.json or built-in demo data.")
    parser.add_argument("--source", default=None, help="Optional source report.json path to sanitize.")
    parser.add_argument("--output", default="reports/demo", help="Output directory for the demo bundle.")
    parser.add_argument("--mode", choices=("public", "realistic_demo", "minimal"), default="public", help="Demo sanitization mode.")
    parser.add_argument("--json-only", action=argparse.BooleanOptionalAction, default=False, help="Print only JSON result.")
    parser.add_argument("--force", action=argparse.BooleanOptionalAction, default=False, help="Overwrite existing demo bundle files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = build_demo_bundle(
        source_report_path=args.source,
        output_dir=args.output,
        mode=args.mode,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
