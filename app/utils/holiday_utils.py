# -*- coding: utf-8 -*-
"""
节假日工具模块

提供中国法定节假日检查功能
"""

from datetime import date
from typing import Dict, Optional, Set

# 中国法定节假日配置（按年份）
# 格式: {年份: {日期: 节假日名称}}
CHINESE_HOLIDAYS: Dict[int, Dict[date, str]] = {
    2025: {
        # 元旦
        date(2025, 1, 1): "元旦",
        # 春节
        date(2025, 1, 28): "春节",
        date(2025, 1, 29): "春节",
        date(2025, 1, 30): "春节",
        date(2025, 1, 31): "春节",
        date(2025, 2, 1): "春节",
        date(2025, 2, 2): "春节",
        date(2025, 2, 3): "春节",
        date(2025, 2, 4): "春节",
        # 清明节
        date(2025, 4, 4): "清明节",
        date(2025, 4, 5): "清明节",
        date(2025, 4, 6): "清明节",
        # 劳动节
        date(2025, 5, 1): "劳动节",
        date(2025, 5, 2): "劳动节",
        date(2025, 5, 3): "劳动节",
        date(2025, 5, 4): "劳动节",
        date(2025, 5, 5): "劳动节",
        # 端午节
        date(2025, 5, 31): "端午节",
        date(2025, 6, 1): "端午节",
        date(2025, 6, 2): "端午节",
        # 中秋节+国庆节
        date(2025, 10, 1): "国庆节",
        date(2025, 10, 2): "国庆节",
        date(2025, 10, 3): "国庆节",
        date(2025, 10, 4): "中秋节",
        date(2025, 10, 5): "国庆节",
        date(2025, 10, 6): "国庆节",
        date(2025, 10, 7): "国庆节",
        date(2025, 10, 8): "国庆节",
    },
    2026: {
        # 元旦
        date(2026, 1, 1): "元旦",
        date(2026, 1, 2): "元旦",
        date(2026, 1, 3): "元旦",
        # 春节（农历正月初一：2026年2月17日）
        date(2026, 2, 15): "春节",
        date(2026, 2, 16): "春节",
        date(2026, 2, 17): "春节",
        date(2026, 2, 18): "春节",
        date(2026, 2, 19): "春节",
        date(2026, 2, 20): "春节",
        date(2026, 2, 21): "春节",
        # 清明节
        date(2026, 4, 4): "清明节",
        date(2026, 4, 5): "清明节",
        date(2026, 4, 6): "清明节",
        # 劳动节
        date(2026, 5, 1): "劳动节",
        date(2026, 5, 2): "劳动节",
        date(2026, 5, 3): "劳动节",
        # 端午节
        date(2026, 6, 19): "端午节",
        date(2026, 6, 20): "端午节",
        date(2026, 6, 21): "端午节",
        # 中秋节
        date(2026, 9, 25): "中秋节",
        date(2026, 9, 26): "中秋节",
        date(2026, 9, 27): "中秋节",
        # 国庆节
        date(2026, 10, 1): "国庆节",
        date(2026, 10, 2): "国庆节",
        date(2026, 10, 3): "国庆节",
        date(2026, 10, 4): "国庆节",
        date(2026, 10, 5): "国庆节",
        date(2026, 10, 6): "国庆节",
        date(2026, 10, 7): "国庆节",
    },
}

# 调休工作日（原本是周末但需要上班的日子）
WORKDAY_ADJUSTMENTS: Dict[int, Set[date]] = {
    2025: {
        date(2025, 1, 26),  # 春节调休
        date(2025, 2, 8),   # 春节调休
        date(2025, 4, 27),  # 劳动节调休
        date(2025, 9, 28),  # 国庆调休
        date(2025, 10, 11), # 国庆调休
    },
    2026: {
        date(2026, 2, 14),  # 春节调休
        date(2026, 2, 28),  # 春节调休
    },
}


def is_holiday(check_date: date) -> bool:
    """
    检查指定日期是否为法定节假日

    Args:
        check_date: 要检查的日期

    Returns:
        bool: 如果是节假日返回 True，否则返回 False
    """
    year = check_date.year
    year_holidays = CHINESE_HOLIDAYS.get(year, {})
    return check_date in year_holidays


def get_holiday_name(check_date: date) -> Optional[str]:
    """
    获取指定日期的节假日名称

    Args:
        check_date: 要检查的日期

    Returns:
        Optional[str]: 节假日名称，如果不是节假日返回 None
    """
    year = check_date.year
    year_holidays = CHINESE_HOLIDAYS.get(year, {})
    return year_holidays.get(check_date)


def is_workday_adjustment(check_date: date) -> bool:
    """
    检查指定日期是否为调休工作日（周末需要上班）

    Args:
        check_date: 要检查的日期

    Returns:
        bool: 如果是调休工作日返回 True，否则返回 False
    """
    year = check_date.year
    year_adjustments = WORKDAY_ADJUSTMENTS.get(year, set())
    return check_date in year_adjustments


def get_work_type(check_date: date) -> str:
    """
    获取指定日期的工作类型

    Args:
        check_date: 要检查的日期

    Returns:
        str: 工作类型 - "NORMAL"（正常工作日）, "WEEKEND"（周末）, "HOLIDAY"（节假日）
    """
    # 先检查是否是法定节假日
    if is_holiday(check_date):
        return "HOLIDAY"

    # 检查是否是调休工作日（周末但需要上班）
    if is_workday_adjustment(check_date):
        return "NORMAL"

    # 检查是否是周末
    if check_date.weekday() >= 5:  # 5=周六, 6=周日
        return "WEEKEND"

    return "NORMAL"


def get_working_days(start_date: date, end_date: date) -> int:
    """
    计算两个日期之间的工作日数量（不含节假日和周末）。
    
    Args:
        start_date: 开始日期（含）
        end_date: 结束日期（含）
    
    Returns:
        工作日天数
    """
    from datetime import timedelta
    count = 0
    current = start_date
    while current <= end_date:
        if not is_holiday(current):
            count += 1
        current += timedelta(days=1)
    return count


def add_working_days(start_date: date, working_days: int) -> date:
    """
    从 start_date 起，往后加指定工作日数，返回目标日期。
    
    Args:
        start_date: 起始日期
        working_days: 要增加的工作日数
    
    Returns:
        目标日期
    """
    from datetime import timedelta
    current = start_date
    added = 0
    while added < working_days:
        current += timedelta(days=1)
        if not is_holiday(current):
            added += 1
    return current
