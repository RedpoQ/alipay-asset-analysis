from __future__ import annotations

import re

CANONICAL_FIELDS = (
    "code",
    "name",
    "market_value",
    "shares",
    "cost_nav",
    "current_nav",
    "profit_rate",
    "target_position",
    "amount",
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "code": (
        "基金代码",
        "代码",
        "产品代码",
        "基金编号",
        "fund_code",
        "code",
    ),
    "name": (
        "基金名称",
        "名称",
        "产品名称",
        "基金",
        "fund_name",
        "name",
    ),
    "market_value": (
        "持有金额",
        "持有市值",
        "当前市值",
        "当前金额",
        "持仓金额",
        "市值",
        "金额",
        "market_value",
        "amount",
    ),
    "shares": (
        "持有份额",
        "持仓份额",
        "份额",
        "shares",
    ),
    "cost_nav": (
        "持仓成本价",
        "持仓成本",
        "成本价",
        "成本净值",
        "持有成本价",
        "买入净值",
        "cost_nav",
        "cost_price",
    ),
    "current_nav": (
        "最新净值",
        "当前净值",
        "单位净值",
        "净值",
        "current_nav",
        "latest_nav",
    ),
    "profit_rate": (
        "收益率",
        "持有收益率",
        "盈亏率",
        "profit_rate",
        "return_rate",
    ),
    "target_position": (
        "目标仓位",
        "目标占比",
        "target_position",
        "target_weight",
    ),
    "amount": (
        "amount",
    ),
}

_FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "\ufeff": "",
        "\u3000": " ",
        "（": "(",
        "）": ")",
        "，": ",",
        "：": ":",
        "＿": "_",
        "－": "-",
        "％": "%",
        "￥": "¥",
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
    }
)

HEADER_ALIAS_MAP: dict[str, str] = {}
for canonical_field, aliases in FIELD_ALIASES.items():
    HEADER_ALIAS_MAP[canonical_field] = canonical_field
    for alias in aliases:
        HEADER_ALIAS_MAP[alias] = canonical_field

NORMALIZED_HEADER_ALIAS_MAP = {
    canonical_field: canonical_field for canonical_field in CANONICAL_FIELDS
}
for alias, canonical_field in HEADER_ALIAS_MAP.items():
    NORMALIZED_HEADER_ALIAS_MAP[alias] = canonical_field
NORMALIZED_HEADER_ALIAS_MAP = {
    (re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", re.sub(r"\([^)]*\)", "", str(alias).translate(_FULLWIDTH_TRANSLATION).strip()).lower())): canonical_field
    for alias, canonical_field in NORMALIZED_HEADER_ALIAS_MAP.items()
}


def normalize_header_name(header: str | None) -> str:
    if header is None:
        return ""
    text = str(header).translate(_FULLWIDTH_TRANSLATION).strip()
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text


def resolve_canonical_field(header: str | None) -> str | None:
    normalized = normalize_header_name(header)
    if not normalized:
        return None
    return NORMALIZED_HEADER_ALIAS_MAP.get(normalized)
