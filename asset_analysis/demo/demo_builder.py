from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..chat_summary.builder import build_chat_summary
from ..chat_summary.formatter import format_chat_summary
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..workflow.daily_run import run_daily_workflow
from ..preflight.checks import run_preflight
from .sanitizer import REALISTIC_DEMO_NAME_MAP, PUBLIC_NAME_MAP, sanitize_report


def build_sanitized_report_payload(source_report_path: str, *, mode: str) -> dict[str, Any]:
    payload = json.loads(Path(source_report_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Source report.json must be a JSON object.")
    return sanitize_report(payload, mode=mode)


def build_builtin_demo_payload(output_dir: str | Path, *, mode: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    output_path = Path(output_dir)
    workflow_root = output_path / "_demo_workflow"
    workflow_root.mkdir(parents=True, exist_ok=True)
    config_path = _write_demo_config(workflow_root)
    preflight_output = output_path / "demo_preflight_report.json"
    preflight_result = run_preflight(str(config_path), json_output=str(preflight_output))
    result = run_daily_workflow(str(config_path))
    if not result.get("ok"):
        raise ValueError(f"Built-in demo workflow failed: {result.get('errors', [])}")
    report_json = result.get("report_json")
    if not report_json:
        raise ValueError("Built-in demo workflow did not generate report.json.")
    return build_sanitized_report_payload(str(report_json), mode=mode), preflight_result


def render_demo_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) or {}
    positions = report.get("positions", []) or []
    signals = report.get("signals", []) or []
    warnings = report.get("portfolio_warnings", []) or []
    lines = [
        "# Sanitized Demo Report",
        "",
        "## Summary",
        "",
        f"- Total cost: {float(summary.get('total_cost', 0.0)):.2f}",
        f"- Total market value: {float(summary.get('total_market_value', 0.0)):.2f}",
        f"- Total profit: {float(summary.get('total_profit', 0.0)):.2f}",
        f"- Total profit rate: {float(summary.get('total_profit_rate', 0.0)):.2%}",
        "",
        "## Positions",
        "",
        "| Code | Name | Market Value | Profit Rate | Target | Current |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    if positions:
        for item in positions:
            lines.append(
                f"| {item.get('code', '')} | {item.get('name', '')} | {float(item.get('market_value', 0.0)):.2f} | {float(item.get('profit_rate', 0.0)):.2%} | {float(item.get('target_position', 0.0)):.2%} | {float(item.get('current_position', 0.0)):.2%} |"
            )
    else:
        lines.append("| - | Positions omitted in minimal mode | 0.00 | 0.00% | 0.00% | 0.00% |")
    lines.extend(["", "## Signals", ""])
    if signals:
        for item in signals:
            lines.append(f"- {item.get('name', '')}（{item.get('code', '')}）：{item.get('signal', '')}")
    else:
        lines.append("- No signal entries included.")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- No portfolio warnings.")
    return "\n".join(lines).strip() + "\n"


def render_demo_readme(
    *,
    mode: str,
    files: dict[str, str],
    chat_summary_text: str,
    source_report_path: str | None,
) -> str:
    source_note = "User-provided report.json source" if source_report_path else "Built-in demo data under examples/demo/"
    lines = [
        "# Public Demo Bundle",
        "",
        "## What This Demo Shows",
        "- A sanitized public export of the local asset_analysis report and chat summary flow.",
        "- Structure, signal labels, and percentages are preserved while private names, paths, and exact amounts are masked or normalized.",
        "",
        "## Input Type",
        f"- Mode: `{mode}`",
        f"- Source: `{source_note}`",
        "",
        "## Report Summary",
        f"- JSON: `reports/demo/{Path(files.get('demo_report_json', '')).name}`",
        f"- Markdown: `reports/demo/{Path(files.get('demo_report_md', '')).name}`",
        "",
        "## Chat Summary Example",
        "```text",
        chat_summary_text.strip(),
        "```",
        "",
        "## Safety Boundary",
        "- Private file paths are replaced with demo paths.",
        "- Exact amounts are normalized or replaced with demo values.",
        "- Signals are preserved from the existing rule engine only.",
        "",
        "## Not Investment Advice",
        "- This demo is for product and workflow showcase only.",
        "",
        "## No Automatic Trading",
        "- No trading execution is included.",
        "",
        "## No Market Prediction",
        "- The exported summary remains rule-driven and does not predict prices.",
        "",
        "## How To Run Locally",
        "- `python -m asset_analysis.demo.cli --output reports/demo --mode realistic_demo`",
        "- `python -m asset_analysis.demo.cli --source path/to/report.json --output reports/demo --mode public`",
        "",
    ]
    return "\n".join(lines)


def _write_demo_config(workflow_root: Path) -> Path:
    config_path = workflow_root / "demo_config.generated.yaml"
    output_dir = workflow_root / "reports" / "daily"
    latest_dir = workflow_root / "reports" / "latest"
    config_path.write_text(
        "\n".join(
            [
                "profile:",
                "  name: balanced",
                "  file: examples/profiles/balanced.profile.yaml",
                "input:",
                "  mode: holdings_yaml",
                "  holdings_yaml: examples/demo/demo_holdings.yaml",
                "output:",
                f"  daily_dir: {output_dir.as_posix()}",
                f"  latest_dir: {latest_dir.as_posix()}",
                "analysis:",
                "  data_source: mock",
                "  reporter: offline",
                "  rules: examples/rules.example.yaml",
                "  asset_groups: examples/asset_groups.example.yaml",
                "  portfolio_template: examples/portfolio_template.example.yaml",
                "  overseas_exposure: examples/overseas_exposure.example.yaml",
                "notification:",
                "  enabled: false",
                "  dry_run: true",
                "preflight:",
                "  enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    return config_path
