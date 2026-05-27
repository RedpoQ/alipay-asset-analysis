from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .compare import compare_reports
from .indexer import build_history_index


def build_trend_report(
    index_path: str | None = None,
    output_path: str | None = None,
    reports_dir: str | None = None,
) -> dict[str, Any]:
    if reports_dir:
        index_output = index_path or str(Path("reports") / "history_index.json")
        index_payload = build_history_index(reports_dir=reports_dir, output_path=index_output)
    else:
        if not index_path:
            raise ValueError("index_path is required when reports_dir is not provided.")
        index_payload = json.loads(Path(index_path).read_text(encoding="utf-8"))

    items = index_payload.get("items", [])
    compare_payload = None
    if len(items) >= 2:
        compare_payload = compare_reports(items[-1]["report_json"], items[-2]["report_json"])

    markdown = _render_trend_markdown(index_payload, compare_payload)
    if output_path:
        destination = Path(output_path)
        if destination.suffix.lower() == ".md":
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(markdown, encoding="utf-8")
            markdown_path = destination
        else:
            destination.mkdir(parents=True, exist_ok=True)
            markdown_path = destination / "latest_trend.md"
            markdown_path.write_text(markdown, encoding="utf-8")
        if compare_payload:
            compare_path = markdown_path.with_name("latest_compare.json")
            compare_path.write_text(json.dumps(compare_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        markdown_path = None

    return {
        "index": index_payload,
        "compare": compare_payload,
        "report_md": markdown,
        "output_path": str(markdown_path) if markdown_path else None,
    }


def _render_trend_markdown(index_payload: dict[str, Any], compare_payload: dict[str, Any] | None) -> str:
    lines = [
        "# 历史趋势报告",
        "",
        "## 历史报告概览",
        "",
        f"- 历史报告数量: {index_payload.get('count', 0)}",
    ]
    items = index_payload.get("items", [])
    if items:
        latest = items[-1]
        lines.append(f"- 最新报告日期: {latest.get('date', '')}")
        lines.append(f"- 最新收益率: {float((latest.get('summary') or {}).get('total_profit_rate', 0)):.2%}")
    else:
        lines.append("- 目前没有可用的历史日报。")

    lines.extend(["", "## 今日 vs 上次变化", ""])
    if compare_payload:
        delta = compare_payload.get("summary_delta", {})
        lines.append(f"- 总市值变化: {float(delta.get('total_market_value_delta', 0)):.2f}")
        lines.append(f"- 总收益变化: {float(delta.get('total_profit_delta', 0)):.2f}")
        lines.append(f"- 总收益率变化: {float(delta.get('total_profit_rate_delta', 0)):.2%}")
    else:
        lines.append("- 历史报告不足 2 份，暂时无法比较。")

    lines.extend(["", "## 信号变化", ""])
    if compare_payload and compare_payload.get("signal_changes"):
        for item in compare_payload["signal_changes"]:
            lines.append(f"- {item['code']} {item['name']}: {item.get('previous_signal')} -> {item.get('current_signal')}")
    else:
        lines.append("- 没有检测到信号变化。")

    lines.extend(["", "## 分组变化", ""])
    if compare_payload and compare_payload.get("group_changes"):
        rendered = False
        for item in compare_payload["group_changes"]:
            if item.get("group_position_delta") or item.get("new_group_warnings") or item.get("resolved_group_warnings"):
                rendered = True
                lines.append(f"- {item['group']}: 仓位变化 {float(item.get('group_position_delta', 0)):.2%}")
        if not rendered:
            lines.append("- 没有显著分组变化。")
    else:
        lines.append("- 没有分组变化数据。")

    lines.extend(["", "## 新增风险提醒", ""])
    if compare_payload and compare_payload.get("warning_changes", {}).get("new"):
        for item in compare_payload["warning_changes"]["new"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 没有新增风险提醒。")

    lines.extend(["", "## 已解除风险提醒", ""])
    if compare_payload and compare_payload.get("warning_changes", {}).get("resolved"):
        for item in compare_payload["warning_changes"]["resolved"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 没有已解除的风险提醒。")

    lines.extend(
        [
            "",
            "## 限制说明",
            "",
            "- 这里只做历史快照对比，不进行市场预测。",
            "- 这里只读取已有 report.json，不生成新的交易信号。",
            "- 这里不提供自动交易指令，也不替代原有规则引擎。",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic historical trend markdown report.")
    parser.add_argument("--index", default=None, help="Existing history_index.json path.")
    parser.add_argument("--reports-dir", default=None, help="Optional reports/daily directory to rebuild index first.")
    parser.add_argument("--output", required=True, help="Trend markdown file or output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = build_trend_report(index_path=args.index, output_path=args.output, reports_dir=args.reports_dir)
    print(json.dumps({"output_path": payload.get("output_path")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
