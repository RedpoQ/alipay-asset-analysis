from __future__ import annotations

import json


def build_report_prompt(result) -> str:
    context = {
        "summary": result.summary.to_dict(),
        "positions": [position.to_dict() for position in result.positions],
        "signals": [signal.to_dict() for signal in result.signals],
        "portfolio_warnings": list(result.portfolio_warnings),
        "rules": dict(result.rules),
        "data_source": result.data_source,
        "quote_warnings": _collect_quote_warnings(result),
    }
    instructions = [
        "你是一个投资分析报告解释助手。",
        "你只能解释用户已经提供的结构化数据和既有信号。",
        "不要预测未来价格、净值、涨跌或市场走势。",
        "不要发明缺失数据，不要补充未提供的事实。",
        "不要修改 add/reduce/hold 信号，不要覆盖规则引擎结论。",
        "不要推荐自动交易、程序化下单或自动执行。",
        "请明确提及数据源与限制。",
        "输出必须是 Markdown。",
        "请使用以下章节：今日概览、持仓信号、风险提醒、数据与规则限制、后续观察点。",
    ]
    return "\n".join(instructions) + "\n\n结构化上下文如下：\n```json\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n```"


def _collect_quote_warnings(result) -> list[str]:
    warnings: list[str] = []
    for position in result.positions:
        quote = position.quote or {}
        if position.error:
            warnings.append(f"{position.code}: {position.error['message']}")
        elif quote.get("source") == "fallback":
            warnings.append(f"{position.code}: fallback quote used after primary source failure")
    return warnings
