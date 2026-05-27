from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .template_writer import choose_existing_template, render_config_template


def init_local_project(
    *,
    project_root: str | Path = ".",
    force: bool = False,
    dry_run: bool = False,
    profile: str = "balanced",
    data_source: str = "mock",
) -> dict[str, Any]:
    root = Path(project_root)
    private_dir = root / "private"
    created: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    next_steps: list[str] = []

    if dry_run:
        warnings.append("Dry-run mode: no files were written.")
    else:
        private_dir.mkdir(parents=True, exist_ok=True)

    try:
        _write_text(
            root / "private" / "config.local.yaml",
            render_config_template(profile=profile, data_source=data_source),
            created=created,
            skipped=skipped,
            force=force,
            dry_run=dry_run,
        )
        _copy_template(
            root / "private" / "alipay_holdings.local.csv",
            choose_existing_template(
                root / "private" / "alipay_holdings.local.example.csv",
                root / "examples" / "alipay_holdings.example.csv",
            ),
            created=created,
            skipped=skipped,
            force=force,
            dry_run=dry_run,
        )
        _copy_template(
            root / "private" / "manual_quotes.local.csv",
            choose_existing_template(
                root / "private" / "manual_quotes.local.example.csv",
                root / "examples" / "manual_quotes.example.csv",
            ),
            created=created,
            skipped=skipped,
            force=force,
            dry_run=dry_run,
        )
        _copy_template(
            root / "private" / "holdings.local.yaml",
            choose_existing_template(root / "private" / "holdings.local.example.yaml"),
            created=created,
            skipped=skipped,
            force=force,
            dry_run=dry_run,
        )
    except Exception as exc:
        errors.append(str(exc))

    next_steps.append("python -m asset_analysis.ux.setup_check --config private/config.local.yaml")
    next_steps.append("python -m asset_analysis.alipay.preview --input private/alipay_holdings.local.csv")
    if data_source == "manual":
        next_steps.append("Edit private/manual_quotes.local.csv before the first manual data run.")
    next_steps.append("python -m asset_analysis.workflow.daily_run --config private/config.local.yaml")

    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": not errors,
        "created": created,
        "skipped": skipped,
        "warnings": warnings,
        "errors": errors,
        "next_steps": next_steps,
    }


def _write_text(
    destination: Path,
    content: str,
    *,
    created: list[str],
    skipped: list[str],
    force: bool,
    dry_run: bool,
) -> None:
    if destination.exists() and not force:
        skipped.append(str(destination))
        return
    if dry_run:
        created.append(str(destination))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    created.append(str(destination))


def _copy_template(
    destination: Path,
    template_path: Path | None,
    *,
    created: list[str],
    skipped: list[str],
    force: bool,
    dry_run: bool,
) -> None:
    if template_path is None:
        raise FileNotFoundError(f"Template not found for {destination}")
    _write_text(
        destination,
        template_path.read_text(encoding="utf-8"),
        created=created,
        skipped=skipped,
        force=force,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize local private templates for the single-channel Alipay workflow.")
    parser.add_argument("--force", action=argparse.BooleanOptionalAction, default=False, help="Overwrite existing local files.")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False, help="Preview file creation without writing.")
    parser.add_argument("--profile", default="balanced", help="Profile name used for config template generation.")
    parser.add_argument("--data-source", choices=("mock", "manual"), default="mock", help="Default data source for the generated config.")
    parser.add_argument("--json", action=argparse.BooleanOptionalAction, default=False, help="Print JSON only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = init_local_project(
        force=args.force,
        dry_run=args.dry_run,
        profile=args.profile,
        data_source=args.data_source,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not args.json:
        print("")
        print("Next steps:")
        for item in payload.get("next_steps", []):
            print(f"- {item}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
