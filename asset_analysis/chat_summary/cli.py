from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build_chat_summary
from .formatter import format_chat_summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a deterministic mobile-friendly chat summary from report.json.")
    parser.add_argument("--report", required=True, help="Path to report.json.")
    parser.add_argument("--output", required=True, help="Path to chat summary text or markdown output.")
    parser.add_argument("--format", choices=("text", "markdown", "wechat"), default="text", help="Formatted output type.")
    parser.add_argument("--json-output", default=None, help="Optional path for chat_summary.json.")
    parser.add_argument("--max-signals", type=int, default=3)
    parser.add_argument("--max-warnings", type=int, default=5)
    parser.add_argument("--style", default="wechat")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = build_chat_summary(
        report_path=args.report,
        max_signals=args.max_signals,
        max_warnings=args.max_warnings,
        style=args.style,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_chat_summary(summary, format=args.format), encoding="utf-8")
    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if not summary.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
