from __future__ import annotations


GROUP_LABELS = {
    "broad_index": "宽基指数",
    "sector_theme": "行业主题",
    "active_equity": "主动权益",
    "bond": "债券",
    "money_market": "货币/现金类",
    "overseas": "海外资产",
    "cash": "现金",
    "other": "其他",
    "core": "核心仓",
    "satellite": "卫星仓",
    "diversifier": "分散补充仓",
    "qdii": "QDII基金",
    "nasdaq100": "纳斯达克100",
    "sp500": "标普500",
    "global_equity": "全球权益",
    "us_equity": "美股权益",
}


def localize_group_name(group: str) -> str:
    return GROUP_LABELS.get(str(group), str(group) or "其他")
