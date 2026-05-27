from __future__ import annotations

import json

from .base import BaseReporter, ReporterOutput


class OfflineReporter(BaseReporter):
    name = "offline"

    def __init__(self, mode: str = "offline", fallback_warning: str | None = None, error: str | None = None):
        self.mode = mode
        self.fallback_warning = fallback_warning
        self.error = error

    def render(self, result) -> ReporterOutput:
        warning_lines: list[str] = []
        lines = [
            "# Asset Analysis Report",
            "",
            "## Summary",
            "",
            f"- Data source mode: {result.data_source}",
            f"- Rules source: {result.rules.get('source', 'default')}",
            f"- Reporter mode: {self.mode}",
            f"- Total cost: {result.summary.total_cost:.2f}",
            f"- Total market value: {result.summary.total_market_value:.2f}",
            f"- Total profit: {result.summary.total_profit:.2f}",
            f"- Total profit rate: {result.summary.total_profit_rate:.2%}",
        ]
        if self.fallback_warning:
            lines.extend(["", "## Reporter Warning", "", f"- {self.fallback_warning}"])

        lines.extend(
            [
                "",
                "## Positions",
                "",
                "| Code | Name | Type | Cost | Market Value | Profit | Profit Rate | Target | Current | Quote Source | Quote As Of |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for position in result.positions:
            quote = position.quote or {}
            lines.append(
                "| {code} | {name} | {type} | {cost:.2f} | {market_value:.2f} | "
                "{profit:.2f} | {profit_rate:.2%} | {target_position:.2%} | {current_position:.2%} | {quote_source} | {quote_as_of} |".format(
                    quote_source=quote.get("source", ""),
                    quote_as_of=quote.get("as_of", ""),
                    **position.to_dict(),
                )
            )
            if position.error:
                warning_lines.append(f"- `{position.code}`: {position.error['message']}")
            elif quote.get("source") == "fallback":
                warning_lines.append(f"- `{position.code}`: primary data source failed, mock fallback was used.")

        lines.extend(
            [
                "",
                "## Signals",
                "",
                "| Code | Signal | Confidence | Severity | Reason |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for signal in result.signals:
            lines.append(f"| {signal.code} | {signal.signal} | {signal.confidence} | {signal.severity} | {signal.reason} |")
            for warning in signal.warnings:
                warning_lines.append(f"- `{signal.code}`: {warning}")

        lines.extend(["", "## Portfolio Warnings", ""])
        if result.portfolio_warnings:
            for item in result.portfolio_warnings:
                lines.append(f"- {item}")
        else:
            lines.append("- No portfolio concentration warnings under the current rule set.")

        group_analysis = result.group_analysis or {}
        lines.extend(["", "## Group Analysis", ""])
        groups = group_analysis.get("groups", [])
        if groups:
            lines.append("")
            lines.append("| Group | Market Value | Current | Target | Max | Profit | Profit Rate | Assets | Tags |")
            lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
            for item in groups:
                tags_text = ", ".join(item.get("tags", []))
                lines.append(
                    "| {group} | {market_value:.2f} | {current_position:.2%} | {target_position:.2%} | {max_position:.2%} | {profit:.2f} | {profit_rate:.2%} | {asset_count} | {tags} |".format(**{**item, "tags": tags_text})
                )
        else:
            lines.append("- No group analysis config was provided or no grouped assets were detected.")

        lines.extend(["", "## Group Warnings", ""])
        if group_analysis.get("warnings"):
            for item in group_analysis["warnings"]:
                lines.append(f"- {item}")
        else:
            lines.append("- No group-level warnings.")

        lines.extend(["", "## Tag Concentration", ""])
        if group_analysis.get("tag_concentration"):
            lines.append("")
            lines.append("| Tag | Current | Assets | Warnings |")
            lines.append("| --- | ---: | ---: | --- |")
            for item in group_analysis["tag_concentration"]:
                warnings_text = "; ".join(item.get("warnings", []))
                lines.append(
                    "| {tag} | {current_position:.2%} | {asset_count} | {warnings} |".format(**{**item, "warnings": warnings_text})
                )
        else:
            lines.append("- No tag concentration data.")

        exposure_analysis = result.exposure_analysis or {}
        lines.extend(["", "## Overseas / QDII Exposure", ""])
        overseas = exposure_analysis.get("overseas", {}) or {}
        if overseas.get("asset_count", 0):
            lines.append(f"- Market value: {float(overseas.get('market_value', 0)):.2f}")
            lines.append(f"- Current position: {float(overseas.get('current_position', 0)):.2%}")
            lines.append(f"- Asset count: {int(overseas.get('asset_count', 0))}")
            lines.append(f"- Tags: {', '.join(overseas.get('tags', []))}")
        else:
            lines.append("- No overseas / QDII exposure config was matched.")

        lines.extend(["", "## Overlap Groups", ""])
        overlap_groups = exposure_analysis.get("overlap_groups", []) or []
        if overlap_groups:
            for item in overlap_groups:
                lines.append(
                    f"- {item.get('display_name', item.get('group', ''))}: assets={item.get('asset_count', 0)}, position={float(item.get('current_position', 0)):.2%}"
                )
                for warning in item.get("warnings", []):
                    lines.append(f"  - {warning}")
        else:
            lines.append("- No overlap groups were triggered.")

        lines.extend(["", "## Core / Satellite Role Analysis", ""])
        role_analysis = exposure_analysis.get("role_analysis", []) or []
        if role_analysis:
            for item in role_analysis:
                lines.append(
                    f"- {item.get('display_name', item.get('role', ''))}: {float(item.get('current_position', 0)):.2%}"
                )
                for warning in item.get("warnings", []):
                    lines.append(f"  - {warning}")
        else:
            lines.append("- No overseas role analysis entries.")

        lines.extend(["", "## QDII Risk Notes", ""])
        if exposure_analysis.get("risk_notes"):
            for item in exposure_analysis["risk_notes"]:
                lines.append(f"- {item}")
        else:
            lines.append("- No QDII-specific risk notes.")

        lines.extend(["", "## Recommendations", ""])
        if result.recommendations:
            for recommendation in result.recommendations:
                lines.append(f"- {recommendation}")
        else:
            lines.append("- Keep following the deterministic rebalance signals above. No price prediction is included.")

        if warning_lines:
            lines.extend(["", "## Data Warnings", ""])
            lines.extend(warning_lines)

        data_quality = result.data_quality or {}
        lines.extend(["", "## Data Quality", ""])
        if data_quality:
            lines.append(f"- Data source: {data_quality.get('data_source', '')}")
            lines.append(f"- Analysis scope: {data_quality.get('analysis_scope', '')}")
            lines.append(f"- Quote count: {data_quality.get('quote_count', 0)}")
            lines.append(f"- Fresh quotes: {data_quality.get('fresh_quote_count', 0)}")
            lines.append(f"- Stale quotes: {data_quality.get('stale_quote_count', 0)}")
            lines.append(f"- Missing quotes: {data_quality.get('missing_quote_count', 0)}")
        else:
            lines.append("- No data quality summary was generated.")

        lines.extend(["", "## Quote Freshness", ""])
        freshness_lines = []
        for position in result.positions:
            quote = position.quote or {}
            freshness = quote.get("freshness", {}) or {}
            if freshness:
                freshness_lines.append(
                    f"- {position.code}: {freshness.get('status', 'unknown')} / as_of={freshness.get('as_of')} / age_days={freshness.get('age_days')}"
                )
        if freshness_lines:
            lines.extend(freshness_lines)
        else:
            lines.append("- No quote freshness metadata.")

        lines.extend(["", "## Missing / Stale Quote Warnings", ""])
        if data_quality.get("warnings"):
            for item in data_quality["warnings"]:
                lines.append(f"- {item}")
        else:
            lines.append("- No missing or stale quote warnings.")

        lines.extend(["", "## Rules / Config", ""])
        lines.append("```json")
        lines.append(json.dumps(result.rules, ensure_ascii=False, indent=2))
        lines.append("```")

        lines.extend(
            [
                "",
                "## Notes / Limitations",
                "",
                "- Default mode uses deterministic mock quotes and does not require network access.",
                "- Public data adapters are optional reference sources and may fail without stopping the whole pipeline.",
                "- Failed fetches are preserved as structured per-asset errors and do not stop the whole pipeline.",
                "- Signals remain deterministic and rule-based; there is no price prediction or trading automation.",
                "- LLM reporter, when enabled, explains existing signals only and does not override them.",
            ]
        )
        return ReporterOutput(mode=self.mode, used="offline", error=self.error, report_md="\n".join(lines) + "\n")
