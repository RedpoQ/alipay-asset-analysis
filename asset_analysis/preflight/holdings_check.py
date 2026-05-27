from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..alipay_parser import parse_alipay_file
from ..holdings_parser import parse_holdings_file, parse_holdings_text
from ..models import AssetHolding
from ..workflow.config import DailyWorkflowConfig


def run_holdings_checks(config: DailyWorkflowConfig) -> tuple[list[dict[str, Any]], list[AssetHolding]]:
    checks: list[dict[str, Any]] = []
    holdings: list[AssetHolding] = []
    input_path = Path(config.input.alipay_csv if config.input.mode == "alipay_csv" else config.input.holdings_yaml)
    checks.append(
        _check(
            "holdings_file_exists",
            input_path.exists(),
            "critical",
            f"持仓输入文件存在：{input_path}" if input_path.exists() else f"持仓输入文件不存在：{input_path}",
            {"path": str(input_path)},
        )
    )
    if not input_path.exists():
        return checks, holdings

    try:
        if config.input.mode == "alipay_csv":
            result = parse_alipay_file(input_path)
            holdings = parse_holdings_text(json.dumps(result.holdings, ensure_ascii=False), suffix=".json")
            checks.append(
                _check(
                    "holdings_parse",
                    result.valid_count > 0,
                    "critical",
                    "Alipay 输入已成功转换为标准持仓。"
                    if result.valid_count > 0
                    else "Alipay 输入未能转换出有效持仓。",
                    {"valid_count": result.valid_count, "warnings": [item.to_dict() for item in result.warnings], "errors": [item.to_dict() for item in result.errors]},
                )
            )
        else:
            holdings = parse_holdings_file(input_path)
            checks.append(_check("holdings_parse", True, "critical", "标准持仓文件解析成功。", {"path": str(input_path)}))
    except Exception as exc:
        checks.append(_check("holdings_parse", False, "critical", f"持仓文件解析失败：{exc}", {"path": str(input_path)}))
        return checks, holdings

    checks.append(
        _check(
            "holdings_not_empty",
            bool(holdings),
            "critical",
            "持仓列表非空。" if holdings else "未解析到任何持仓。",
            {"count": len(holdings)},
        )
    )
    if not holdings:
        return checks, holdings

    seen: dict[str, int] = {}
    total_target = 0.0
    non_zero_target_count = 0
    duplicate_codes: list[str] = []
    invalid_amounts: list[str] = []
    invalid_costs: list[str] = []
    invalid_targets: list[str] = []
    empty_names: list[str] = []
    for item in holdings:
        seen[item.code] = seen.get(item.code, 0) + 1
        if seen[item.code] == 2:
            duplicate_codes.append(item.code)
        if item.amount < 0:
            invalid_amounts.append(item.code)
        if item.cost_nav is not None and item.cost_nav < 0:
            invalid_costs.append(item.code)
        if item.cost_price is not None and item.cost_price < 0:
            invalid_costs.append(item.code)
        if not 0 <= float(item.target_position) <= 1:
            invalid_targets.append(item.code)
        total_target += float(item.target_position)
        if float(item.target_position) > 0:
            non_zero_target_count += 1
        if not str(item.name).strip():
            empty_names.append(item.code)

    checks.append(
        _check(
            "holdings_numeric_values",
            not invalid_amounts and not invalid_costs and not invalid_targets,
            "critical",
            "持仓数值字段通过基本校验。"
            if not invalid_amounts and not invalid_costs and not invalid_targets
            else "持仓数值字段存在非法值。",
            {
                "invalid_amounts": invalid_amounts,
                "invalid_costs": invalid_costs,
                "invalid_targets": invalid_targets,
            },
        )
    )
    duplicate_severity = "critical" if config.preflight.fail_on_duplicate_codes else "warning"
    checks.append(
        _check(
            "holdings_duplicate_codes",
            not duplicate_codes,
            duplicate_severity,
            "未发现重复持仓代码。"
            if not duplicate_codes
            else f"发现重复持仓代码：{', '.join(duplicate_codes)}",
            {"duplicates": duplicate_codes},
        )
    )
    target_warning = False
    target_message = "目标仓位汇总正常。"
    if total_target > 1.2:
        target_warning = True
        target_message = f"目标仓位合计 {total_target:.2f}，明显高于 1.2。"
    elif non_zero_target_count == 0:
        target_warning = True
        target_message = "所有持仓的 target_position 都为 0 或缺失。"
    checks.append(
        _check(
            "holdings_target_position_sum",
            not target_warning,
            "warning",
            target_message,
            {"total_target_position": round(total_target, 6), "non_zero_target_count": non_zero_target_count},
        )
    )
    checks.append(
        _check(
            "holdings_empty_name",
            not empty_names,
            "warning",
            "持仓名称字段正常。" if not empty_names else "发现名称为空的持仓。",
            {"codes": empty_names},
        )
    )
    return checks, holdings


def _check(name: str, ok: bool, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": ok, "severity": severity, "message": message, "details": details or {}}
