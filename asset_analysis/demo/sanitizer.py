from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

PUBLIC_NAME_MAP = {
    "000001": "示例核心基金A",
    "110022": "示例主动权益基金B",
    "161725": "示例行业主题基金C",
}

REALISTIC_DEMO_NAME_MAP = {
    "000001": "华夏成长混合",
    "110022": "易方达消费行业股票",
    "161725": "招商中证白酒指数(LOF)A",
}

SENSITIVE_STRING_MARKERS = (
    "C:/Users/",
    "C:\\Users\\",
    "private/",
    "private\\",
    "config.local.yaml",
    "alipay_holdings.local.csv",
    "manual_quotes.local.csv",
)

_WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:[/\\]Users[/\\][^ \n\r\t\"']+")
_REPORT_PRIVATE_PATH = re.compile(r"reports[/\\]private[/\\]latest[/\\]?")


def sanitize_report(report: dict, mode: str = "public") -> dict:
    mode = (mode or "public").strip().lower()
    if mode not in {"public", "realistic_demo", "minimal"}:
        raise ValueError(f"Unsupported demo sanitize mode: {mode}")

    sanitized = copy.deepcopy(report)
    name_map = _build_name_map(sanitized, mode=mode)
    _drop_private_metadata(sanitized)
    sanitized = _sanitize_strings(sanitized, name_map=name_map)
    _sanitize_summary(sanitized, mode=mode)
    _sanitize_positions(sanitized, mode=mode, name_map=name_map)
    _sanitize_signals(sanitized, name_map=name_map)
    _sanitize_group_analysis(sanitized)
    _sanitize_reporter(sanitized)

    if mode == "minimal":
        sanitized["positions"] = []
        if isinstance(sanitized.get("group_analysis"), dict):
            sanitized["group_analysis"]["groups"] = []

    sanitized["schema_version"] = str(report.get("schema_version", sanitized.get("schema_version", "1.0.0")))
    return sanitized


def scan_text_for_sensitive_strings(text: str) -> list[str]:
    findings: list[str] = []
    haystack = text or ""
    for item in SENSITIVE_STRING_MARKERS:
        if item in haystack and item not in findings:
            findings.append(item)
    return findings


def sanitize_generic_payload(payload: Any) -> Any:
    return _sanitize_strings(copy.deepcopy(payload), name_map={})


def sanitize_public_text(text: str) -> str:
    return _sanitize_string(text, name_map={})


def _build_name_map(report: dict[str, Any], *, mode: str) -> dict[str, str]:
    target_map = REALISTIC_DEMO_NAME_MAP if mode == "realistic_demo" else PUBLIC_NAME_MAP
    name_map: dict[str, str] = {}
    for entry in report.get("positions", []) or []:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "") or "")
        name = str(entry.get("name", "") or "")
        if code and name and code in target_map:
            name_map[name] = target_map[code]
    for entry in report.get("signals", []) or []:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "") or "")
        name = str(entry.get("name", "") or "")
        if code and name and code in target_map:
            name_map[name] = target_map[code]
    return name_map


def _drop_private_metadata(node: Any) -> None:
    if isinstance(node, dict):
        for key in list(node.keys()):
            if key in {"metadata", "raw"}:
                node.pop(key, None)
                continue
            if key == "notes":
                node[key] = None
                continue
            _drop_private_metadata(node[key])
    elif isinstance(node, list):
        for item in node:
            _drop_private_metadata(item)


def _sanitize_strings(node: Any, *, name_map: dict[str, str]) -> Any:
    if isinstance(node, dict):
        return {key: _sanitize_strings(value, name_map=name_map) for key, value in node.items()}
    if isinstance(node, list):
        return [_sanitize_strings(item, name_map=name_map) for item in node]
    if isinstance(node, str):
        return _sanitize_string(node, name_map=name_map)
    return node


def _sanitize_string(text: str, *, name_map: dict[str, str]) -> str:
    value = text
    value = _WINDOWS_USER_PATH.sub("demo/", value)
    value = _REPORT_PRIVATE_PATH.sub("reports/demo/", value)
    value = value.replace("reports\\private\\latest", "reports/demo")
    value = value.replace("reports/private/latest", "reports/demo")
    value = value.replace("private\\", "demo\\")
    value = value.replace("private/", "demo/")
    value = value.replace("config.local.yaml", "demo_config.yaml")
    value = value.replace("alipay_holdings.local.csv", "demo_holdings.csv")
    value = value.replace("manual_quotes.local.csv", "demo_manual_quotes.csv")
    value = value.replace("holdings.local.yaml", "demo_holdings.yaml")
    for original_name, replacement in name_map.items():
        value = value.replace(original_name, replacement)
    return value


def _sanitize_summary(report: dict[str, Any], *, mode: str) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return
    total_market_value = 10000.0 if mode in {"public", "minimal"} else 18888.0
    total_profit_rate = float(summary.get("total_profit_rate", 0.0) or 0.0)
    if total_profit_rate <= -0.95:
        total_cost = total_market_value
        total_profit = 0.0
    else:
        total_cost = round(total_market_value / (1 + total_profit_rate), 2)
        total_profit = round(total_market_value - total_cost, 2)
    summary["total_market_value"] = round(total_market_value, 2)
    summary["total_cost"] = round(total_cost, 2)
    summary["total_profit"] = round(total_profit, 2)


def _sanitize_positions(report: dict[str, Any], *, mode: str, name_map: dict[str, str]) -> None:
    positions = report.get("positions")
    if not isinstance(positions, list):
        return
    total_market_value = float(((report.get("summary") or {}).get("total_market_value")) or (18888.0 if mode == "realistic_demo" else 10000.0))
    fallback_weight = round(1 / len(positions), 6) if positions else 0.0
    for index, position in enumerate(positions, start=1):
        if not isinstance(position, dict):
            continue
        code = str(position.get("code", "") or "")
        target_name = (REALISTIC_DEMO_NAME_MAP if mode == "realistic_demo" else PUBLIC_NAME_MAP).get(code)
        if target_name:
            position["name"] = target_name
        current_position = float(position.get("current_position", fallback_weight) or fallback_weight)
        profit_rate = float(position.get("profit_rate", 0.0) or 0.0)
        market_value = round(total_market_value * current_position, 2)
        if profit_rate <= -0.95:
            cost = market_value
            profit = 0.0
        else:
            cost = round(market_value / (1 + profit_rate), 2)
            profit = round(market_value - cost, 2)
        position["market_value"] = market_value
        position["cost"] = cost
        position["profit"] = profit
        quote = position.get("quote")
        if isinstance(quote, dict):
            quote["name"] = position.get("name", quote.get("name"))
            base_price = round(1.0 + index * 0.173, 4)
            quote["current_price"] = base_price
            quote["current_nav"] = base_price
            daily_change_rate = float(quote.get("daily_change_rate", 0.0) or 0.0)
            previous_value = round(base_price / (1 + daily_change_rate), 4) if daily_change_rate > -0.95 else base_price
            quote["previous_nav"] = previous_value
            quote.pop("raw", None)
            quote["notes"] = None


def _sanitize_signals(report: dict[str, Any], *, name_map: dict[str, str]) -> None:
    signals = report.get("signals")
    if not isinstance(signals, list):
        return
    for entry in signals:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "") or "")
        if name in name_map:
            entry["name"] = name_map[name]
        if isinstance(entry.get("reason"), str):
            entry["reason"] = _sanitize_string(entry["reason"], name_map=name_map)
        if isinstance(entry.get("reason_cn"), str):
            entry["reason_cn"] = _sanitize_string(entry["reason_cn"], name_map=name_map)


def _sanitize_group_analysis(report: dict[str, Any]) -> None:
    group_analysis = report.get("group_analysis")
    if not isinstance(group_analysis, dict):
        return
    groups = group_analysis.get("groups")
    total_market_value = float(((report.get("summary") or {}).get("total_market_value")) or 10000.0)
    if isinstance(groups, list):
        for item in groups:
            if not isinstance(item, dict):
                continue
            if "market_value" in item and isinstance(item.get("current_position"), (int, float)):
                item["market_value"] = round(total_market_value * float(item.get("current_position", 0.0) or 0.0), 2)


def _sanitize_reporter(report: dict[str, Any]) -> None:
    reporter = report.get("reporter")
    if isinstance(reporter, dict):
        reporter["report_md"] = "Sanitized demo report. See reports/demo/demo_report.md for the public markdown version."
    if "report_md" in report:
        report["report_md"] = "Sanitized demo report. See reports/demo/demo_report.md for the public markdown version."
