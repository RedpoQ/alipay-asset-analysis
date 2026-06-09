"""基金申购状态检查模块"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import urlopen
from urllib.error import URLError


@dataclass
class FundPurchaseStatus:
    """基金申购状态"""
    code: str
    name: str
    purchase_status: str  # 开放申购, 暂停申购, 限制大额申购, 限制申购
    redeem_status: str    # 开放赎回, 暂停赎回
    is_purchase_allowed: bool
    is_redeem_allowed: bool
    limit_info: str | None  # 限制信息（如限制金额）
    error: str | None = None


def check_fund_purchase_status(code: str, timeout: float = 5.0) -> FundPurchaseStatus:
    """
    检查基金申购状态
    
    Args:
        code: 基金代码
        timeout: 超时时间（秒）
    
    Returns:
        FundPurchaseStatus 对象
    """
    url = f'https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=1'
    
    try:
        req = __import__('urllib.request', fromlist=['Request']).Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://fund.eastmoney.com/'
        })
        with urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8', errors='replace'))
        
        items = data.get('Data', {}).get('LSJZList', [])
        if not items:
            return FundPurchaseStatus(
                code=code,
                name='未知',
                purchase_status='未知',
                redeem_status='未知',
                is_purchase_allowed=False,
                is_redeem_allowed=False,
                limit_info=None,
                error='无数据'
            )
        
        item = items[0]
        purchase_status = item.get('SGZT', '未知')
        redeem_status = item.get('SHZT', '未知')
        
        # 判断是否可以申购
        is_purchase_allowed = purchase_status in ['开放申购', '限制大额申购', '限制申购']
        
        # 判断是否可以赎回
        is_redeem_allowed = redeem_status in ['开放赎回']
        
        # 获取限制信息
        limit_info = None
        if '限制' in purchase_status:
            limit_info = purchase_status
        
        return FundPurchaseStatus(
            code=code,
            name=item.get('FSRQ', '未知'),  # 使用日期作为临时名称
            purchase_status=purchase_status,
            redeem_status=redeem_status,
            is_purchase_allowed=is_purchase_allowed,
            is_redeem_allowed=is_redeem_allowed,
            limit_info=limit_info
        )
        
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return FundPurchaseStatus(
            code=code,
            name='未知',
            purchase_status='未知',
            redeem_status='未知',
            is_purchase_allowed=False,
            is_redeem_allowed=False,
            limit_info=None,
            error=str(exc)
        )


def batch_check_purchase_status(codes: list[str], timeout: float = 5.0) -> dict[str, FundPurchaseStatus]:
    """
    批量检查基金申购状态
    
    Args:
        codes: 基金代码列表
        timeout: 超时时间（秒）
    
    Returns:
        字典，key为基金代码，value为FundPurchaseStatus
    """
    results = {}
    for code in codes:
        results[code] = check_fund_purchase_status(code, timeout)
    return results


def get_purchase_status_summary(statuses: dict[str, FundPurchaseStatus]) -> str:
    """
    获取申购状态摘要
    
    Args:
        statuses: 基金申购状态字典
    
    Returns:
        格式化的状态摘要
    """
    lines = []
    for code, status in statuses.items():
        if status.error:
            lines.append(f"{code}: 查询失败 ({status.error})")
        else:
            purchase_icon = "✅" if status.is_purchase_allowed else "❌"
            redeem_icon = "✅" if status.is_redeem_allowed else "❌"
            lines.append(f"{code}: 申购{purchase_icon} {status.purchase_status} | 赎回{redeem_icon} {status.redeem_status}")
            if status.limit_info:
                lines.append(f"  限制: {status.limit_info}")
    return "\n".join(lines)
