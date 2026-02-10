# -*- coding: utf-8 -*-
"""
内置格式化器

提供报表框架常用的数据格式化函数：
- format_status_badge: 状态徽章格式化
- format_percentage: 百分比格式化
- format_currency: 货币格式化
- format_date: 日期格式化
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Union


# 状态到颜色/标签的映射
_STATUS_BADGES = {
    "COMPLETED": {"label": "已完成", "color": "green"},
    "IN_PROGRESS": {"label": "进行中", "color": "blue"},
    "PENDING": {"label": "待处理", "color": "orange"},
    "CANCELLED": {"label": "已取消", "color": "gray"},
    "FAILED": {"label": "失败", "color": "red"},
    "APPROVED": {"label": "已批准", "color": "green"},
    "REJECTED": {"label": "已拒绝", "color": "red"},
    "DRAFT": {"label": "草稿", "color": "gray"},
}


def format_status_badge(status: str) -> dict:
    """格式化状态为徽章样式

    Args:
        status: 状态字符串

    Returns:
        包含 label、color、value 的字典
    """
    badge = _STATUS_BADGES.get(status, {"label": status, "color": "default"})
    return {
        "value": status,
        "label": badge["label"],
        "color": badge["color"],
    }


def format_percentage(
    value: Union[float, int, Decimal, None],
    decimals: int = 1,
) -> Optional[str]:
    """格式化为百分比字符串

    Args:
        value: 数值（0-1 范围的小数或 0-100 的百分比值）
        decimals: 小数位数，默认 1

    Returns:
        百分比字符串，如 "75.0%"
    """
    if value is None:
        return None
    num = float(value)
    # 假定输入值是 0-1 范围的小数
    pct = num * 100
    return f"{pct:.{decimals}f}%"


def format_currency(
    value: Union[float, int, Decimal, None],
    symbol: str = "¥",
    decimals: int = 2,
) -> Optional[str]:
    """格式化为货币字符串

    Args:
        value: 金额数值
        symbol: 货币符号，默认 "¥"
        decimals: 小数位数，默认 2

    Returns:
        货币字符串，如 "¥10,000.00"
    """
    if value is None:
        return None
    num = float(value)
    formatted = f"{num:,.{decimals}f}"
    return f"{symbol}{formatted}"


def format_date(
    value: Union[date, datetime, None],
    fmt: str = "%Y-%m-%d",
) -> Optional[str]:
    """格式化日期

    Args:
        value: 日期或日期时间对象
        fmt: 格式化字符串，默认 "%Y-%m-%d"

    Returns:
        格式化后的日期字符串，输入为 None 时返回 None
    """
    if value is None:
        return None
    return value.strftime(fmt)
