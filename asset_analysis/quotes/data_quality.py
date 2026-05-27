from __future__ import annotations

from typing import Any


def build_data_quality(data_source: str, positions) -> dict[str, Any]:
    quote_count = len(list(positions))
    missing_quote_count = 0
    stale_quote_count = 0
    fresh_quote_count = 0
    warnings: list[str] = []
    limitations: list[str] = ["本报告不预测价格。"]

    statuses = []
    any_successful_quote = False
    any_quote_error = False
    for position in positions:
        quote = position.quote or {}
        freshness = quote.get("freshness", {}) or {}
        status = freshness.get("status", "unknown")
        statuses.append(status)
        if quote.get("error"):
            any_quote_error = True
            missing_quote_count += 1
            warnings.append(f"{position.code} 缺少可用行情/净值数据。")
        elif status == "fresh":
            fresh_quote_count += 1
            any_successful_quote = True
        elif status in {"stale", "missing_date", "future_date", "unknown"}:
            stale_quote_count += 1
            any_successful_quote = True
            if status == "stale":
                warnings.append(f"{position.code} 的净值/报价日期已过期。")
            elif status == "missing_date":
                warnings.append(f"{position.code} 缺少净值日期。")
            elif status == "future_date":
                warnings.append(f"{position.code} 的净值日期晚于今天。")

    if data_source == "mock":
        analysis_scope = "structure_only"
        has_realtime_quote = False
        limitations.insert(0, "当前使用 mock 数据，仅做结构检查，不做实时行情判断。")
    elif data_source == "manual":
        analysis_scope = "manual_quote"
        has_realtime_quote = False
        limitations.insert(0, "当前使用手工净值数据，净值日期以你导入的 manual_quotes 为准，不代表实时行情。")
    elif any_quote_error and not any_successful_quote:
        analysis_scope = "failed"
        has_realtime_quote = False
    elif any_quote_error or any(status in {"stale", "missing_date", "future_date"} for status in statuses):
        analysis_scope = "mixed"
        has_realtime_quote = data_source in {"public_fund", "auto"}
        limitations.insert(0, "部分净值数据已过期，今日结果更适合做结构检查，不适合做短线判断。")
    else:
        analysis_scope = "quote_based"
        has_realtime_quote = data_source in {"public_fund", "auto"}
        limitations.insert(0, "本次包含行情/净值数据，但仍不做价格预测。")

    if any("QDII" in list(getattr(position, "exposure_tags", []) or []) for position in positions):
        limitations.append("QDII基金可能存在净值更新滞后和汇率影响，短线判断需谨慎。")

    return {
        "data_source": data_source,
        "has_realtime_quote": has_realtime_quote,
        "analysis_scope": analysis_scope,
        "quote_count": quote_count,
        "missing_quote_count": missing_quote_count,
        "stale_quote_count": stale_quote_count,
        "fresh_quote_count": fresh_quote_count,
        "warnings": _dedupe(warnings),
        "limitations": _dedupe(limitations),
    }


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
