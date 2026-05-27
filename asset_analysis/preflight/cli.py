from __future__ import annotations

import argparse
import json

from .checks import run_preflight


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic local preflight checks before the daily workflow.")
    parser.add_argument("--config", default="private/config.local.yaml", help="Path to local workflow config.")
    parser.add_argument("--output", required=True, help="Output path for preflight_report.json")
    parser.add_argument("--markdown", help="Optional output path for preflight_report.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = run_preflight(config_path=args.config, json_output=args.output, markdown_output=args.markdown)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
