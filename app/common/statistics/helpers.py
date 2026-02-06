# -*- coding: utf-8 -*-
"""
统计工具函数

提供统一的格式化和统计卡片构建功能，减少代码重复。
"""

from decimal import Decimal
from typing import Any, Optional, Union


def format_currency(amount: Union[Decimal, float, int, None]) -> str:
    """
    格式化货币金额

    Args:
        amount: 金额（支持 Decimal, float, int, None）

    Returns:
        格式化后的字符串（例如：¥1.5万、¥500）

    Examples:
        >>> format_currency(15000)
        '¥1.5万'
        >>> format_currency(500)
        '¥500'
        >>> format_currency(None)
        '¥0'
    """
    if amount is None:
        return '¥0'
    amount = float(amount)
    if amount >= 10000:
        return f'¥{amount / 10000:.1f}万'
    return f'¥{amount:,.0f}'


def format_hours(hours: Union[Decimal, float, int, None], precision: int = 1) -> str:
    """
    格式化工时

    Args:
        hours: 工时数
        precision: 小数点精度（默认1位）

    Returns:
        格式化后的字符串（例如：8.5h）

    Examples:
        >>> format_hours(8.5)
        '8.5h'
        >>> format_hours(Decimal('10.25'))
        '10.2h'
        >>> format_hours(None)
        '0.0h'
    """
    if hours is None:
        hours = 0
    return f'{float(hours):.{precision}f}h'


def format_percentage(value: Union[float, int, None], precision: int = 1) -> str:
    """
    格式化百分比

    Args:
        value: 百分比值（0-100）
        precision: 小数点精度（默认1位）

    Returns:
        格式化后的字符串（例如：95.5%）

    Examples:
        >>> format_percentage(95.5)
        '95.5%'
        >>> format_percentage(100)
        '100.0%'
        >>> format_percentage(None)
        '-'
    """
    if value is None:
        return '-'
    return f'{value:.{precision}f}%'


def create_stat_card(
    key: str,
    label: str,
    value: Any,
    trend: Union[int, float] = 0,
    unit: Optional[str] = None,
    icon: Optional[str] = None
) -> dict:
    """
    创建统计卡片

    Args:
        key: 统计项唯一键
        label: 显示标签
        value: 统计值（可以是数字或已格式化的字符串）
        trend: 趋势值（正数表示上升，负数表示下降，0表示无变化）
        unit: 单位（可选）
        icon: 图标（可选）

    Returns:
        统计卡片字典

    Examples:
        >>> create_stat_card('total', '总数', 100, trend=5)
        {'key': 'total', 'label': '总数', 'value': 100, 'trend': 5}

        >>> create_stat_card('revenue', '收入', '¥1.5万', trend=2000, unit='元', icon='money')
        {'key': 'revenue', 'label': '收入', 'value': '¥1.5万', 'trend': 2000, 'unit': '元', 'icon': 'money'}
    """
    card = {
        'key': key,
        'label': label,
        'value': value,
        'trend': trend
    }

    if unit is not None:
        card['unit'] = unit
    if icon is not None:
        card['icon'] = icon

    return card


def create_stats_response(stats: list) -> dict:
    """
    创建标准的统计响应

    Args:
        stats: 统计卡片列表

    Returns:
        标准响应字典 {'stats': [...]}

    Examples:
        >>> stats = [create_stat_card('total', '总数', 100)]
        >>> create_stats_response(stats)
        {'stats': [{'key': 'total', 'label': '总数', 'value': 100, 'trend': 0}]}
    """
    return {'stats': stats}


def calculate_trend(current: Union[int, float, Decimal], previous: Union[int, float, Decimal]) -> Union[int, float]:
    """
    计算趋势值（当前值 - 上期值）

    Args:
        current: 当前值
        previous: 上期值

    Returns:
        趋势值（差值）

    Examples:
        >>> calculate_trend(100, 80)
        20
        >>> calculate_trend(50, 70)
        -20
        >>> calculate_trend(100, 0)
        0
    """
    if not previous or previous == 0:
        return 0

    # 保持原始类型（int 或 float）
    diff = current - previous
    if isinstance(current, int) and isinstance(previous, int):
        return int(diff)
    return float(diff)
