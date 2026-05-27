from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_preflight_reports(payload: dict[str, Any], json_path: str | Path, markdown_path: str | Path | None = None) -> tuple[Path, Path | None]:
    json_file = Path(json_path)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_file: Path | None = None
    if markdown_path is not None:
        md_file = Path(markdown_path)
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text(build_preflight_markdown(payload), encoding="utf-8")
    return json_file, md_file


def build_preflight_markdown(payload: dict[str, Any]) -> str:
    checks = payload.get("checks", []) or []
    critical_failed = [item for item in checks if not item.get("ok") and item.get("severity") == "critical"]
    warning_failed = [item for item in checks if not item.get("ok") and item.get("severity") == "warning"]
    sections = [
        "# Preflight Summary",
        f"- Final Decision: {'PASS' if payload.get('ok') else 'BLOCKED'}",
        f"- Total Checks: {payload.get('summary', {}).get('total', 0)}",
        f"- Passed: {payload.get('summary', {}).get('passed', 0)}",
        f"- Failed: {payload.get('summary', {}).get('failed', 0)}",
        f"- Warnings: {payload.get('summary', {}).get('warnings', 0)}",
        "",
        "## Critical Checks",
    ]
    sections.extend(_render_check_lines(critical_failed) or ["- None"])
    sections.append("")
    sections.append("## Warnings")
    sections.extend(_render_check_lines(warning_failed) or ["- None"])
    sections.append("")
    sections.append("## Holdings Checks")
    sections.extend(_render_check_lines([item for item in checks if item.get("name", "").startswith("holdings_")]) or ["- None"])
    sections.append("")
    sections.append("## Quote Checks")
    sections.extend(_render_check_lines([item for item in checks if item.get("name", "").startswith("manual_quotes_")]) or ["- None"])
    sections.append("")
    sections.append("## Config Safety Checks")
    sections.extend(_render_check_lines([item for item in checks if item.get("name") not in {item.get("name") for item in checks if str(item.get("name", "")).startswith("holdings_") or str(item.get("name", "")).startswith("manual_quotes_")} and not str(item.get("name", "")).startswith("holdings_") and not str(item.get("name", "")).startswith("manual_quotes_")]) or ["- None"])
    sections.append("")
    sections.append("## Final Decision")
    sections.append("- PASS" if payload.get("ok") else "- BLOCKED")
    return "\n".join(sections).strip() + "\n"


def _render_check_lines(items: list[dict[str, Any]]) -> list[str]:
    return [f"- [{item.get('severity')}] {item.get('name')}: {item.get('message')}" for item in items]
