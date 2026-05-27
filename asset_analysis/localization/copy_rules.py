from __future__ import annotations

import re
from typing import Any

from .group_copy import localize_group_name


_BELOW_TARGET_RE = re.compile(
    r"^Current position (?P<current>[\d.]+%) is below target (?P<target>[\d.]+%) by more than the rebalance band\.$"
)
_ABOVE_TARGET_RE = re.compile(
    r"^Current position (?P<current>[\d.]+%) is above target (?P<target>[\d.]+%) by more than the overweight band\.$"
)
_MAX_SINGLE_RE = re.compile(
    r"^(?P<code>[A-Za-z0-9._-]+) exceeds max_single_position with current weight (?P<weight>[\d.]+%)\.$"
)
_MAX_FUND_RE = re.compile(
    r"^Total fund position (?P<weight>[\d.]+%) exceeds max_fund_position (?P<max>[\d.]+%)\.$"
)
_GROUP_MAX_RE = re.compile(
    r"^Group (?P<group>[A-Za-z0-9_]+) current position (?P<weight>[\d.]+%) exceeds max_position (?P<max>[\d.]+%)\.$"
)
_GROUP_BELOW_TARGET_RE = re.compile(
    r"^Group (?P<group>[A-Za-z0-9_]+) current position (?P<weight>[\d.]+%) is below target_position (?P<target>[\d.]+%) by more than the configured threshold\.$"
)
_TAG_CONCENTRATION_RE = re.compile(
    r"^Tag (?P<tag>.+?) concentration (?P<weight>[\d.]+%) exceeds configured threshold (?P<max>[\d.]+%)\.$"
)


def localize_reason_text(reason: str, signal_label: str | None = None) -> str:
    text = str(reason or "").strip()
    if not text:
        return ""
    match = _BELOW_TARGET_RE.match(text)
    if match:
        return f"当前仓位 {match.group('current')}，低于目标仓位 {match.group('target')}，已超过再平衡阈值。"
    match = _ABOVE_TARGET_RE.match(text)
    if match:
        return f"当前仓位 {match.group('current')}，高于目标仓位 {match.group('target')}，已超过超配阈值。"
    if text == "Deep loss blocks add.":
        return "当前亏损较深，规则限制继续补仓。"
    if text == "Quote failed; conservative hold.":
        return "行情数据获取失败，按保守规则继续持有观察。"
    if text.startswith("Hold because the position is close to target"):
        return "当前仓位接近目标区间，或风险规则要求保持谨慎，继续持有观察。"
    if text.startswith("Take profit preference triggered"):
        return "当前已达到止盈观察条件，且仓位偏高，优先关注减仓节奏。"
    if text.startswith("Current profit is strong and the position is above target"):
        return "当前已有一定盈利，且仓位高于目标，适合优先关注减仓观察。"
    prefix = "规则原因："
    if signal_label:
        prefix = f"{signal_label}，规则原因："
    return f"{prefix}{text}"


def localize_warning_text(warning: str, asset_name_map: dict[str, str] | None = None) -> str:
    text = str(warning or "").strip()
    if not text:
        return ""
    match = _MAX_SINGLE_RE.match(text)
    if match:
        code = match.group("code")
        display_name = (asset_name_map or {}).get(code) or code
        return f"{display_name} 当前仓位 {match.group('weight')}，超过单只资产上限。"
    match = _MAX_FUND_RE.match(text)
    if match:
        return f"基金总仓位 {match.group('weight')}，超过组合上限 {match.group('max')}。"
    match = _GROUP_MAX_RE.match(text)
    if match:
        group_cn = localize_group_name(match.group("group"))
        return f"{group_cn} 当前仓位 {match.group('weight')}，超过分组上限 {match.group('max')}。"
    match = _GROUP_BELOW_TARGET_RE.match(text)
    if match:
        group_cn = localize_group_name(match.group("group"))
        return f"{group_cn} 当前仓位 {match.group('weight')}，低于分组目标 {match.group('target')}，已超过分组偏离阈值。"
    match = _TAG_CONCENTRATION_RE.match(text)
    if match:
        return f"{match.group('tag')} 标签集中度 {match.group('weight')}，超过阈值 {match.group('max')}。"
    if text == "Quote data unavailable; keep signal interpretation conservative.":
        return "部分行情数据不可用，本次以持仓结构检查为主。"
    if text == "Schema validation reported errors in the source report.":
        return "源报告存在结构校验问题，摘要内容可能不完整。"
    return text if any(ord(char) > 127 for char in text) else f"规则提醒：{text}"


def localize_data_status_copy(data_source: str, positions: list[dict[str, Any]], schema_errors: list[Any] | None = None) -> list[str]:
    limitations: list[str] = []
    sources = {(position.get("quote") or {}).get("source") for position in positions}
    has_quote_error = any((position.get("quote") or {}).get("error") for position in positions)
    has_fallback = "fallback" in sources or has_quote_error
    if data_source == "mock":
        limitations.append("当前使用 mock 数据，仅做结构检查，不做实时行情判断。")
    elif has_fallback:
        limitations.append("部分行情数据不可用，本次以持仓结构检查为主。")
    else:
        limitations.append("本次包含行情/净值数据，但仍不做价格预测。")
    if schema_errors:
        limitations.append("源报告存在结构校验问题，摘要内容可能不完整。")
    return limitations
