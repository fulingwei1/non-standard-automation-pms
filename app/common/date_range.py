# -*- coding: utf-8 -*-
"""
通用时间范围工具

统一月初/月末、当月/上月等计算，替代各处手写
replace(day=1)、date(year, month+1, 1) - timedelta(days=1) 的重复代码。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple


def get_month_range(target_date: date) -> Tuple[date, date]:
    """
    获取指定日期所在月的起止日期（月初、月末）。

    Args:
        target_date: 任意日期。

    Returns:
        (月初 date, 月末 date)，均为 date 类型（不含时间）。

    示例:
        get_month_range(date(2025, 1, 15))  -> (date(2025,1,1), date(2025,1,31))
    """
    start = target_date.replace(day=1)
    if target_date.month == 12:
        end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
    return start, end


def get_last_month_range(target_date: date) -> Tuple[date, date]:
    """
    获取指定日期所在月的上一个月的起止日期。

    Args:
        target_date: 任意日期。

    Returns:
        (上月月初, 上月月末)。
    """
    first_of_this_month = target_date.replace(day=1)
    last_day_of_last_month = first_of_this_month - timedelta(days=1)
    return get_month_range(last_day_of_last_month)


def get_month_range_by_ym(year: int, month: int) -> Tuple[date, date]:
    """
    根据年份、月份（1–12）返回该月的起止日期。

    Args:
        year: 年。
        month: 月，1–12。

    Returns:
        (该月月初, 该月月末)。
    """
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def month_start(target_date: date) -> date:
    """指定日期所在月的第一天。"""
    return target_date.replace(day=1)


def month_end(target_date: date) -> date:
    """指定日期所在月的最后一天。"""
    _, end = get_month_range(target_date)
    return end


def get_week_range(target_date: date) -> Tuple[date, date]:
    """
    获取指定日期所在周的起止日期（周一到周日）。

    Args:
        target_date: 任意日期。

    Returns:
        (周一, 周日)。
    """
    weekday = target_date.weekday()
    start = target_date - timedelta(days=weekday)
    end = start + timedelta(days=6)
    return start, end
