from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_release_gate_reports(payload: dict[str, Any], output_dir: str | Path, json_only: bool = False) -> tuple[Path, Path | None]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "release_gate_report.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if json_only:
        return json_path, None
    md_path = destination / "release_gate_report.md"
    md_path.write_text(render_release_gate_markdown(payload), encoding="utf-8")
    return json_path, md_path


def render_release_gate_markdown(payload: dict[str, Any]) -> str:
    checks = payload.get("checks", [])
    critical = [item for item in checks if item.get("severity") == "critical"]
    warnings = [item for item in checks if item.get("severity") == "warning"]
    lines = [
        "# Release Gate Report",
        "",
        "## Release Gate Summary",
        "",
        f"- Final decision: {'PASS' if payload.get('ok') else 'BLOCKED'}",
        f"- Total checks: {payload.get('summary', {}).get('total', 0)}",
        f"- Passed: {payload.get('summary', {}).get('passed', 0)}",
        f"- Failed: {payload.get('summary', {}).get('failed', 0)}",
        f"- Warning-level issues: {payload.get('summary', {}).get('warnings', 0)}",
        "",
        "## Critical Checks",
        "",
    ]
    if critical:
        for item in critical:
            lines.append(f"- [{'OK' if item.get('ok') else 'FAIL'}] {item.get('name')}: {item.get('message')}")
    else:
        lines.append("- No critical checks were recorded.")

    lines.extend(["", "## Warning Checks", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- [{'OK' if item.get('ok') else 'WARN'}] {item.get('name')}: {item.get('message')}")
    else:
        lines.append("- No warning checks were recorded.")

    lines.extend(["", "## Smoke Test Results", ""])
    for item in checks:
        if "smoke" in str(item.get("name")):
            lines.append(f"- {item.get('name')}: {item.get('message')}")

    lines.extend(
        [
            "",
            "## Privacy Protection",
            "",
            "- The gate verifies .gitignore protections for private holdings and local reports.",
            "- Example files must remain trackable while real local files stay ignored.",
            "",
            "## Default Safety Configuration",
            "",
            "- The gate verifies `data_source: mock`, `reporter: offline`, `notification.enabled: false`, and `notification.dry_run: true` in the local example config.",
            "",
            "## Schema Contract",
            "",
            "- The gate verifies that `ASSET_ANALYSIS_SCHEMA_VERSION` exists and remains `1.0.0`.",
            "",
            "## OpenClaw / Hermes Compatibility",
            "",
            "- The gate runs deterministic offline smoke checks for both adapters.",
            "",
            "## Notification Safety",
            "",
            "- The gate verifies `notify` dry-run and notification orchestrator dry-run without network access.",
            "",
            "## History Layer",
            "",
            "- The gate verifies that history indexing and trend reporting do not crash even when local history is limited.",
            "",
            "## Known Limitations",
            "",
            "- This gate does not verify external APIs or network channels.",
            "- This gate does not add charts, backtesting, or trading automation.",
            "- History smoke check may warn instead of fail when not enough local history exists.",
            "",
            "## Final Decision",
            "",
            f"- {'PASS' if payload.get('ok') else 'BLOCKED'}",
        ]
    )
    return "\n".join(lines) + "\n"
