from __future__ import annotations

from datetime import date, datetime
from typing import Any


def build_quote_freshness(
    as_of: str | None,
    *,
    is_qdii: bool = False,
    today: date | None = None,
    normal_threshold_days: int = 3,
    qdii_threshold_days: int = 5,
) -> dict[str, Any]:
    current_day = today or date.today()
    threshold_days = qdii_threshold_days if is_qdii else normal_threshold_days
    if not as_of:
        return {
            "status": "missing_date",
            "as_of": as_of,
            "age_days": None,
            "threshold_days": threshold_days,
            "warnings": ["缺少净值日期，无法判断数据新鲜度。"],
        }
    try:
        as_of_date = datetime.fromisoformat(str(as_of)).date()
    except ValueError:
        try:
            as_of_date = date.fromisoformat(str(as_of))
        except ValueError:
            return {
                "status": "unknown",
                "as_of": as_of,
                "age_days": None,
                "threshold_days": threshold_days,
                "warnings": ["净值日期格式无法识别。"],
            }
    age_days = (current_day - as_of_date).days
    if age_days < 0:
        return {
            "status": "future_date",
            "as_of": as_of_date.isoformat(),
            "age_days": age_days,
            "threshold_days": threshold_days,
            "warnings": ["净值日期晚于今天，请检查手工录入数据。"],
        }
    if age_days > threshold_days:
        return {
            "status": "stale",
            "as_of": as_of_date.isoformat(),
            "age_days": age_days,
            "threshold_days": threshold_days,
            "warnings": ["净值日期已超过建议时效，更适合做结构检查。"],
        }
    return {
        "status": "fresh",
        "as_of": as_of_date.isoformat(),
        "age_days": age_days,
        "threshold_days": threshold_days,
        "warnings": [],
    }
