from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..holdings_parser import _load_yaml_like
from .profile_loader import list_builtin_profiles
from .resolver import resolve_profile_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List or resolve asset_analysis portfolio profiles.")
    parser.add_argument("--list", action=argparse.BooleanOptionalAction, default=False, help="List built-in profiles.")
    parser.add_argument("--profile", help="Profile file path.")
    parser.add_argument("--config", help="Optional workflow config to merge on top of the profile.")
    parser.add_argument("--output", help="Optional JSON output path for resolved profile config.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.list:
        for name in list_builtin_profiles():
            print(name)
        return 0
    workflow_config: dict = {}
    if args.config:
        workflow_config = _load_yaml_like(Path(args.config).read_text(encoding="utf-8"))
    result = resolve_profile_config(workflow_config, profile_path=args.profile)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
