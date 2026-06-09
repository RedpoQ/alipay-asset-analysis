from __future__ import annotations

from typing import Any


def format_chat_summary(summary: dict[str, Any], format: str = "text") -> str:
    if format == "markdown":
        return _format_markdown(summary)
    if format == "wechat":
        return _format_wechat(summary)
    return _format_text(summary)


def _format_text(summary: dict[str, Any]) -> str:
    lines = [str(summary.get("title", "每日基金分析")), str(summary.get("one_line", ""))]
    for section in summary.get("sections", []):
        lines.append(section.get("title", ""))
        for item in section.get("items", []):
            lines.append(f"- {item}")
    return "\n".join(line for line in lines if line).strip() + "\n"


def _format_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# {summary.get('title', '每日基金分析')}", "", summary.get("one_line", "")]
    for section in summary.get("sections", []):
        lines.extend(["", f"## {section.get('title', '')}"])
        for item in section.get("items", []):
            lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def _format_wechat(summary: dict[str, Any]) -> str:
    """微信格式：简洁列表，适合快速阅读"""
    lines = []
    
    # 标题
    lines.append("每日基金分析")
    lines.append("")
    
    # 摘要 - 简化版
    signals_summary = summary.get("signals_summary", {})
    add_count = signals_summary.get("add", 0)
    reduce_count = signals_summary.get("reduce", 0)
    hold_count = signals_summary.get("hold", 0)
    
    # 从 warnings 提取主要风险
    warnings = summary.get("warnings_localized", [])
    main_risk = _extract_main_risk(warnings)
    
    # 从 summary 提取收益率
    overview = _get_section(summary, "总览")
    total_return = ""
    for item in overview:
        if "总收益率" in item:
            total_return = item.split("：")[-1].strip() if "：" in item else ""
            break
    
    if total_return:
        lines.append(f"收益率 {total_return}，补仓观察 {add_count} 个 / 减仓观察 {reduce_count} 个 / 持有观察 {hold_count} 个。")
    if main_risk:
        lines.append(f"主要风险：{main_risk}")
    lines.append("")
    
    # 重点动作 - 从 top_signals 提取
    top_signals = summary.get("top_signals", [])
    if top_signals:
        lines.append("重点动作")
        for signal in top_signals:
            code = signal.get("code", "")
            name = signal.get("name", "")
            signal_type = signal.get("signal", "hold")
            
            if signal_type == "add":
                label = "补仓观察"
            elif signal_type == "reduce":
                label = "减仓观察"
            else:
                label = "持有观察"
            
            # 简化基金名称
            short_name = _simplify_fund_name(name)
            lines.append(f"- {short_name}（{code}）：{label}")
        lines.append("")
    
    # 风险提醒 - 从 warnings 和 sections 提取
    lines.append("风险提醒")
    risk_items = _extract_risk_items(summary, warnings)
    for item in risk_items:
        lines.append(f"- {item}")
    lines.append("")
    
    # 数据状态
    data_status = summary.get("data_status", {})
    data_source = data_status.get("data_source", "unknown")
    lines.append("数据状态")
    if data_source == "manual":
        lines.append("- 使用手工净值，不代表实时行情")
    elif data_source == "mock":
        lines.append("- 使用模拟数据，仅做结构检查")
    else:
        lines.append(f"- 数据源：{data_source}")
    lines.append("- 规则驱动，不预测价格")
    lines.append("")
    
    # 补充说明 - 从 top_signals 和 sections 提取关键信息
    lines.append("补充说明")
    
    # 从 top_signals 提取仓位信息
    for signal in top_signals:
        code = signal.get("code", "")
        current_position = signal.get("current_position", 0)
        target_position = signal.get("target_position", 0)
        
        if current_position and target_position:
            current_pct = float(current_position) * 100
            target_pct = float(target_position) * 100
            
            if current_pct > target_pct * 1.2:  # 超过目标20%
                lines.append(f"- {code} 当前仓位 {current_pct:.2f}%，明显高于目标仓位 {target_pct:.0f}%")
            elif current_pct < target_pct * 0.8:  # 低于目标20%
                lines.append(f"- {code} 当前仓位 {current_pct:.2f}%，低于目标仓位 {target_pct:.0f}%")
    
    # 从 sections 的 "海外 / QDII 曝险" 提取卫星仓和QDII信息
    exposure_section = _get_section(summary, "海外 / QDII 曝险")
    qdii_warning_added = False
    for item in exposure_section:
        if "卫星仓" in item and "占比" in item:
            import re
            match = re.search(r'(\d+\.?\d*)%', item)
            if match:
                pct = match.group(1)
                lines.append(f"- 卫星仓占比 {pct}%，高于建议上限 30.00%")
        elif "QDII" in item and ("滞后" in item or "汇率" in item) and not qdii_warning_added:
            lines.append(f"- QDII 可能存在净值滞后和汇率波动影响")
            qdii_warning_added = True
    
    return "\n".join(lines).strip() + "\n"


def _extract_main_risk(warnings: list[dict[str, str]]) -> str:
    """提取主要风险描述"""
    for warning in warnings:
        text = warning.get("text", "")
        if "单只" in text and ("仓位" in text or "超过" in text):
            # 提取基金名称和仓位
            import re
            # 匹配 "XXX 当前仓位 XX.XX%，超过单只资产上限"
            match = re.search(r'(.+?)\s*当前仓位\s*(\d+\.?\d*)%.*超过单只', text)
            if match:
                fund_name = match.group(1).strip()
                pct = match.group(2)
                return f"{fund_name} 仓位 {pct}%，超过单只上限"
    return ""


def _extract_risk_items(summary: dict, warnings: list[dict[str, str]]) -> list[str]:
    """从多个来源提取风险提醒"""
    risk_items = []
    
    # 从 warnings_localized 提取
    for warning in warnings:
        text = warning.get("text", "")
        
        if "单只" in text and ("仓位" in text or "超过" in text):
            risk_items.append("单只仓位过高")
        elif "美股" in text or "QDII" in text or "纳斯达克" in text:
            if "暴露" in text or "集中" in text or "占比" in text:
                risk_items.append("美股 / QDII 暴露偏高")
        elif "卫星仓" in text and "占比" in text:
            risk_items.append("卫星仓占比偏高")
        elif "基金总仓位" in text and "超过" in text:
            risk_items.append("基金总仓位过高")
    
    # 从 sections 的 "海外 / QDII 曝险" 提取
    exposure_section = _get_section(summary, "海外 / QDII 曝险")
    for item in exposure_section:
        if "卫星仓" in item and "占比" in item and "卫星仓占比偏高" not in risk_items:
            risk_items.append("卫星仓占比偏高")
    
    # 去重
    seen = set()
    unique_items = []
    for item in risk_items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    
    return unique_items if unique_items else ["暂无明显风险"]


def _get_section(summary: dict, title: str) -> list:
    """获取指定标题的 section 内容"""
    for section in summary.get("sections", []):
        if section.get("title", "").startswith(title):
            return section.get("items", [])
    return []


def _simplify_fund_name(name: str) -> str:
    """简化基金名称"""
    if not name:
        return ""
    
    # 移除常见的后缀
    suffixes_to_remove = [
        "ETF联接(QDII)A", "ETF联接(QDII)C", "ETF联接A", "ETF联接C",
        "(QDII)A", "(QDII)C", "(QDII)", "LOF)A", "LOF)C",
        "股票", "混合", "指数", "债券"
    ]
    
    result = name
    for suffix in suffixes_to_remove:
        if result.endswith(suffix):
            result = result[:-len(suffix)]
            break
    
    # 如果还是太长，截断
    if len(result) > 15:
        result = result[:12] + "..."
    
    return result if result else name[:12] + "..."
