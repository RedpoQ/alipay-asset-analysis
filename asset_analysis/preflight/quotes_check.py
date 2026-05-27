from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like
from ..models import AssetHolding
from ..quotes.freshness import build_quote_freshness
from ..workflow.config import DailyWorkflowConfig


def run_quotes_checks(config: DailyWorkflowConfig, holdings: list[AssetHolding]) -> list[dict[str, Any]]:
    if config.analysis.data_source != "manual":
        return []

    checks: list[dict[str, Any]] = []
    path = Path(config.analysis.quotes or "")
    checks.append(
        _check(
            "manual_quotes_file_exists",
            path.exists(),
            "critical",
            f"手工净值文件存在：{path}" if path.exists() else f"手工净值文件不存在：{path}",
            {"path": str(path)},
        )
    )
    if not path.exists():
        return checks

    try:
        raw_rows = _load_raw_quotes(path)
    except Exception as exc:
        checks.append(_check("manual_quotes_parse", False, "critical", f"手工净值文件解析失败：{exc}", {"path": str(path)}))
        return checks

    checks.append(
        _check(
            "manual_quotes_parse",
            True,
            "critical",
            "手工净值文件解析成功。",
            {"path": str(path), "count": len(raw_rows)},
        )
    )
    checks.append(
        _check(
            "manual_quotes_not_empty",
            bool(raw_rows),
            "critical",
            "手工净值列表非空。" if raw_rows else "手工净值列表为空。",
            {"count": len(raw_rows)},
        )
    )
    if not raw_rows:
        return checks

    codes_seen: dict[str, int] = {}
    duplicates: list[str] = []
    invalid_codes: list[int] = []
    invalid_values: list[dict[str, Any]] = []
    missing_dates: list[str] = []
    future_dates: list[str] = []
    stale_codes: list[str] = []
    unknown_dates: list[str] = []
    quote_codes: set[str] = set()
    holding_map = {item.code: item for item in holdings}
    for index, row in enumerate(raw_rows, start=1):
        code = str(row.get("code", "")).strip()
        if not code:
            invalid_codes.append(index)
            continue
        quote_codes.add(code)
        codes_seen[code] = codes_seen.get(code, 0) + 1
        if codes_seen[code] == 2:
            duplicates.append(code)
        current_nav = _to_float(row.get("current_nav"))
        current_price = _to_float(row.get("current_price"))
        if current_nav is None and current_price is None:
            invalid_values.append({"code": code, "row": index, "reason": "missing_price_or_nav"})
        if current_nav is not None and current_nav <= 0:
            invalid_values.append({"code": code, "row": index, "reason": "non_positive_nav"})
        if current_price is not None and current_price <= 0:
            invalid_values.append({"code": code, "row": index, "reason": "non_positive_price"})
        if not row.get("as_of"):
            missing_dates.append(code)
            continue
        holding = holding_map.get(code)
        is_qdii = _is_qdii_holding(holding)
        freshness = build_quote_freshness(
            str(row.get("as_of")),
            is_qdii=is_qdii,
            normal_threshold_days=config.preflight.max_normal_stale_days,
            qdii_threshold_days=config.preflight.max_qdii_stale_days,
        )
        status = freshness.get("status")
        if status == "future_date":
            future_dates.append(code)
        elif status == "stale":
            stale_codes.append(code)
        elif status == "unknown":
            unknown_dates.append(code)

    checks.append(
        _check(
            "manual_quotes_values",
            not invalid_codes and not invalid_values,
            "critical",
            "手工净值字段通过基本校验。"
            if not invalid_codes and not invalid_values
            else "手工净值字段存在非法值或缺失。",
            {"invalid_code_rows": invalid_codes, "invalid_values": invalid_values},
        )
    )
    checks.append(
        _check(
            "manual_quotes_duplicate_codes",
            not duplicates,
            "warning",
            "未发现重复净值代码。" if not duplicates else f"发现重复净值代码：{', '.join(duplicates)}",
            {"duplicates": duplicates},
        )
    )
    checks.append(
        _check(
            "manual_quotes_dates_present",
            not missing_dates,
            "warning",
            "手工净值都带有日期。" if not missing_dates else "部分手工净值缺少 as_of 日期。",
            {"codes": missing_dates},
        )
    )
    checks.append(
        _check(
            "manual_quotes_future_dates",
            not future_dates,
            "warning",
            "未发现未来日期的手工净值。" if not future_dates else "存在晚于今天的手工净值日期，请检查录入。",
            {"codes": future_dates},
        )
    )
    stale_severity = "critical" if config.preflight.fail_on_stale_quotes else "warning"
    checks.append(
        _check(
            "manual_quotes_stale",
            not stale_codes,
            stale_severity,
            "手工净值日期在允许时效内。" if not stale_codes else "存在已过期的手工净值数据。",
            {"codes": stale_codes},
        )
    )
    checks.append(
        _check(
            "manual_quotes_unknown_dates",
            not unknown_dates,
            "warning",
            "净值日期格式可识别。" if not unknown_dates else "部分净值日期格式无法识别。",
            {"codes": unknown_dates},
        )
    )

    missing_holdings = sorted(code for code in holding_map if code not in quote_codes)
    missing_severity = "critical" if config.preflight.strict_quotes else "warning"
    checks.append(
        _check(
            "manual_quotes_missing_for_holdings",
            not missing_holdings,
            missing_severity,
            "所有持仓都能匹配到手工净值。" if not missing_holdings else "部分持仓缺少对应手工净值。",
            {"codes": missing_holdings},
        )
    )
    unused_quotes = sorted(code for code in quote_codes if code not in holding_map)
    checks.append(
        _check(
            "manual_quotes_unused_codes",
            not unused_quotes,
            "warning",
            "手工净值代码与当前持仓完全对齐。" if not unused_quotes else "存在未被当前持仓使用的手工净值代码。",
            {"codes": unused_quotes},
        )
    )
    return checks


def _load_raw_quotes(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".yaml", ".yml", ".json"}:
        payload = _load_yaml_like(path.read_text(encoding="utf-8"))
        items = payload.get("quotes", []) or []
        if not isinstance(items, list):
            raise ValueError("Manual quote file must contain a 'quotes' list.")
        return [item for item in items if isinstance(item, dict)]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _to_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def _is_qdii_holding(holding: AssetHolding | None) -> bool:
    if holding is None:
        return False
    metadata = holding.metadata or {}
    tags = metadata.get("tags", []) if isinstance(metadata.get("tags"), list) else []
    haystack = " ".join([holding.name, *(str(item) for item in tags), str(metadata.get("group", ""))]).lower()
    keywords = ["qdii", "海外", "全球", "纳斯达克", "标普", "美元"]
    return any(keyword.lower() in haystack for keyword in keywords)


def _check(name: str, ok: bool, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": ok, "severity": severity, "message": message, "details": details or {}}
