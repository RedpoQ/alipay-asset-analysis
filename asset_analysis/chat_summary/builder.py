from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..localization import (
    build_asset_name_map,
    localize_data_status_copy,
    localize_group_name,
    localize_signal_entry,
    localize_signal_label,
    localize_warning_entry,
)
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION


def build_chat_summary(
    report_path: str,
    max_signals: int = 3,
    max_warnings: int = 5,
    style: str = "wechat",
    extra_warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[dict[str, Any]] = []
    path = Path(report_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _failure(report_path, f"Failed to read report.json: {exc}")

    summary = payload.get("summary", {}) or {}
    signals = payload.get("signals", []) or []
    positions = payload.get("positions", []) or []
    portfolio_warnings = [str(item) for item in payload.get("portfolio_warnings", []) if item]
    group_analysis = payload.get("group_analysis", {}) or {}
    exposure_analysis = payload.get("exposure_analysis", {}) or {}
    group_warnings = [str(item) for item in group_analysis.get("warnings", []) if item]
    exposure_warnings = [str(item) for item in exposure_analysis.get("warnings", []) if item]
    tag_concentration = group_analysis.get("tag_concentration", []) or []
    tag_warnings = []
    for item in tag_concentration:
        tag_warnings.extend(str(warning) for warning in item.get("warnings", []) if warning)

    signal_counts = _count_signals(signals)
    asset_name_map = build_asset_name_map(payload)
    top_signals = [localize_signal_entry(item) for item in signals[:max_signals]]
    exposure_risk_notes = [str(item) for item in exposure_analysis.get("risk_notes", []) if item]
    all_warnings = _dedupe(portfolio_warnings + group_warnings + tag_warnings + exposure_warnings + exposure_risk_notes)
    top_warnings = [localize_warning_entry(item, asset_name_map=asset_name_map) for item in all_warnings[:max_warnings]]

    data_status = _build_data_status(payload, positions)
    if extra_warnings:
        data_status["limitations"] = _dedupe(list(data_status.get("limitations", [])) + [str(item) for item in extra_warnings if item])
    if payload.get("schema_errors"):
        warnings.append("report.json 含有 schema_errors，摘要可能不完整。")
        data_status["limitations"] = _dedupe(
            list(data_status.get("limitations", [])) + localize_data_status_copy(
                str((payload.get("run", {}) or {}).get("data_source", "unknown")),
                positions,
                schema_errors=payload.get("schema_errors", []),
            )
        )

    one_line = _build_one_line(summary, signal_counts, top_warnings, data_status)
    sections = _build_sections(summary, top_signals, top_warnings, data_status, payload)
    text = _render_text(title="每日基金分析", one_line=one_line, sections=sections)

    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_report": str(path),
        "title": "每日基金分析",
        "one_line": one_line,
        "data_status": data_status,
        "signals_summary": signal_counts,
        "top_signals": top_signals,
        "warnings_localized": top_warnings,
        "sections": sections,
        "text": text,
        "errors": errors,
        "warnings": warnings,
        "style": style,
    }


def _build_data_status(payload: dict[str, Any], positions: list[dict[str, Any]]) -> dict[str, Any]:
    if isinstance(payload.get("data_quality"), dict) and payload.get("data_quality"):
        quality = payload.get("data_quality", {})
        return {
            "data_source": str(quality.get("data_source", "unknown")),
            "analysis_scope": str(quality.get("analysis_scope", "structure_only")),
            "has_realtime_quote": bool(quality.get("has_realtime_quote", False)),
            "limitations": _dedupe(
                [str(item) for item in quality.get("limitations", []) if item]
                + [str(item) for item in quality.get("warnings", []) if item]
            ),
        }
    run = payload.get("run", {}) or {}
    data_source = str(run.get("data_source", "unknown"))
    has_quote_error = any((position.get("quote") or {}).get("error") for position in positions)
    if data_source == "mock" or has_quote_error:
        analysis_scope = "structure_only"
    else:
        analysis_scope = "quote_based"
    has_realtime_quote = analysis_scope == "quote_based" and any(
        (position.get("quote") or {}).get("source") not in {"", "mock", "fallback"}
        for position in positions
    )
    return {
        "data_source": data_source,
        "analysis_scope": analysis_scope,
        "has_realtime_quote": has_realtime_quote,
        "limitations": _dedupe(localize_data_status_copy(data_source, positions, schema_errors=payload.get("schema_errors", []))),
    }


def _build_one_line(summary: dict[str, Any], signal_counts: dict[str, int], warnings: list[dict[str, str]], data_status: dict[str, Any]) -> str:
    warning_text = warnings[0]["text"].rstrip("。；;,. ") if warnings else "暂无明显新增风险"
    return (
        f"收益率 {float(summary.get('total_profit_rate', 0)):.2%}，"
        f"{localize_signal_label('add')} {signal_counts['add']} 个 / "
        f"{localize_signal_label('reduce')} {signal_counts['reduce']} 个 / "
        f"{localize_signal_label('hold')} {signal_counts['hold']} 个。"
        f"主要风险是{warning_text}。"
        "规则驱动，不预测。"
    )


def _build_sections(
    summary: dict[str, Any],
    top_signals: list[dict[str, Any]],
    warnings: list[dict[str, str]],
    data_status: dict[str, Any],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[str] = []
    if top_signals:
        for item in top_signals:
            actions.append(f"{item['name']}（{item['code']}）：{item['signal_label']}。")
    else:
        actions.append("今日没有可提炼的重点信号。")
    group_lines = _build_group_lines(payload.get("group_analysis", {}) or {})
    exposure_lines = _build_exposure_lines(payload.get("exposure_analysis", {}) or {})
    return [
        {
            "title": "总览",
            "items": [
                f"总收益率：{float(summary.get('total_profit_rate', 0)):.2%}",
                f"总收益：{float(summary.get('total_profit', 0)):.2f}",
                f"总市值：{float(summary.get('total_market_value', 0)):.2f}",
            ],
        },
        {
            "title": "重点信号",
            "items": [
                f"{item['name']}（{item['code']}）：{item['signal_label']}"
                + (f"\n  原因：{item['reason_cn']}" if item.get("reason_cn") else "")
                for item in top_signals
            ] or ["暂无重点信号。"],
        },
        {
            "title": "组合风险",
            "items": [item["text"] for item in warnings] or ["暂无明显组合风险提醒。"],
        },
        {
            "title": "分组观察",
            "items": group_lines or ["暂无明显分组偏离。"],
        },
        {
            "title": "海外 / QDII 曝险",
            "items": exposure_lines or ["暂无明显海外/QDII曝险提醒。"],
        },
        {
            "title": "今日动作",
            "items": actions,
        },
        {
            "title": "数据状态",
            "items": list(data_status.get("limitations", [])) or ["本次数据状态未知，请以原始报告为准。"],
        },
        {
            "title": "限制说明",
            "items": _dedupe(
                [
                    "规则驱动，不预测价格。",
                    "不构成投资建议，不包含自动交易指令。",
                    "本摘要只复用既有 report.json 结果。",
                    "信号来自规则引擎，不新增、不覆盖。",
                ]
            ),
        },
    ]


def _build_group_lines(group_analysis: dict[str, Any]) -> list[str]:
    groups = group_analysis.get("groups", []) or []
    lines: list[str] = []
    for group in groups[:3]:
        group_name = localize_group_name(str(group.get("group", "other")))
        current_position = float(group.get("current_position", 0))
        target_position = group.get("target_position")
        line = f"{group_name} 当前占比 {current_position:.2%}"
        if target_position is not None:
            line += f"，目标 {float(target_position):.2%}"
        warnings = group.get("warnings", []) or []
        if warnings:
            warning_text = localize_warning_entry(str(warnings[0])).get("text", "").rstrip("。；;,. ")
            line += f"，提示：{warning_text}"
        lines.append(line + "。")
    return lines


def _build_exposure_lines(exposure_analysis: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    overlap_groups = exposure_analysis.get("overlap_groups", []) or []
    for item in overlap_groups:
        for warning in item.get("warnings", []):
            lines.append(str(warning))
    role_analysis = exposure_analysis.get("role_analysis", []) or []
    for item in role_analysis:
        for warning in item.get("warnings", []):
            lines.append(str(warning))
    for warning in exposure_analysis.get("warnings", []) or []:
        if warning not in lines:
            lines.append(str(warning))
    for note in exposure_analysis.get("risk_notes", []) or []:
        if note not in lines:
            lines.append(str(note))
    return lines[:5]


def _render_text(title: str, one_line: str, sections: list[dict[str, Any]]) -> str:
    lines = [title, one_line]
    for section in sections:
        lines.append(f"\n{section['title']}")
        for item in section.get("items", []):
            lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def _count_signals(signals: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"add": 0, "reduce": 0, "hold": 0}
    for signal in signals:
        name = str(signal.get("signal", "")).lower()
        if name in counts:
            counts[name] += 1
    return counts


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _failure(report_path: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_report": report_path,
        "title": "每日基金分析",
        "one_line": "无法生成聊天摘要，请先检查 report.json 是否可读。",
        "data_status": {
            "data_source": "unknown",
            "analysis_scope": "structure_only",
            "has_realtime_quote": False,
            "limitations": ["无法读取源报告，本次无法生成聊天摘要。"],
        },
        "signals_summary": {"add": 0, "reduce": 0, "hold": 0},
        "top_signals": [],
        "warnings_localized": [],
        "sections": [{"title": "限制说明", "items": ["无法读取 report.json，因此本次不输出聊天摘要。"]}],
        "text": "每日基金分析\n无法读取 report.json，因此本次不输出聊天摘要。\n",
        "errors": [{"stage": "read_report", "message": message}],
        "warnings": [],
        "style": "wechat",
    }
